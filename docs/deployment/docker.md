# Docker Deployment

Deploy CONTINUUM using Docker containers for consistency and portability.

## Quick Start

```bash
# Pull official image
docker pull continuum/continuum:latest

# Run with default settings
docker run -d \
  --name continuum \
  -p 8420:8420 \
  -v $(pwd)/data:/data \
  continuum/continuum:latest
```

Access API at `http://localhost:8420`

## Docker Images

### Available Tags

- `latest` - Latest stable release
- `v0.2.0` - Specific version
- `dev` - Development builds (unstable)
- `alpine` - Minimal Alpine Linux base
- `postgres` - Includes PostgreSQL client tools

### Image Details

```bash
# Check image info
docker inspect continuum/continuum:latest

# Image size
docker images continuum/continuum

# Typical size: 200-300MB (standard), 150-200MB (alpine)
```

## Basic Usage

### Running CONTINUUM

```bash
# Basic container
docker run -d \
  --name continuum \
  -p 8420:8420 \
  -v continuum-data:/data \
  continuum/continuum:latest

# With environment variables
docker run -d \
  --name continuum \
  -p 8420:8420 \
  -e CONTINUUM_LOG_LEVEL=info \
  -e CONTINUUM_AUTO_EXTRACT=true \
  -v continuum-data:/data \
  continuum/continuum:latest

# With custom configuration
docker run -d \
  --name continuum \
  -p 8420:8420 \
  -v $(pwd)/config.json:/etc/continuum/config.json \
  -v continuum-data:/data \
  continuum/continuum:latest
```

### CLI Usage

```bash
# Run CLI commands
docker exec continuum continuum stats

# Search
docker exec continuum continuum search "warp drive"

# Export
docker exec continuum continuum export /data/backup.json
```

## Docker Compose

### Basic Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  continuum:
    image: continuum/continuum:latest
    container_name: continuum
    ports:
      - "8420:8420"
    environment:
      - CONTINUUM_LOG_LEVEL=info
      - CONTINUUM_AUTO_EXTRACT=true
      - CONTINUUM_TENANT_ID=default
    volumes:
      - continuum-data:/data
    restart: unless-stopped

volumes:
  continuum-data:
```

Start services:

```bash
docker-compose up -d
```

### With PostgreSQL

```yaml
version: '3.8'

services:
  continuum:
    image: continuum/continuum:latest
    container_name: continuum
    ports:
      - "8420:8420"
    environment:
      - CONTINUUM_STORAGE_BACKEND=postgresql
      - CONTINUUM_CONNECTION_STRING=postgresql://continuum:password@postgres:5432/continuum_db
      - CONTINUUM_LOG_LEVEL=info
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: continuum-postgres
    environment:
      - POSTGRES_DB=continuum_db
      - POSTGRES_USER=continuum
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U continuum"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres-data:
```

### With Redis Cache

```yaml
version: '3.8'

services:
  continuum:
    image: continuum/continuum:latest
    container_name: continuum
    ports:
      - "8420:8420"
    environment:
      - CONTINUUM_STORAGE_BACKEND=postgresql
      - CONTINUUM_CONNECTION_STRING=postgresql://continuum:password@postgres:5432/continuum_db
      - CONTINUUM_ENABLE_CACHE=true
      - CONTINUUM_REDIS_URL=redis://redis:6379/0
      - CONTINUUM_LOG_LEVEL=info
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=continuum_db
      - POSTGRES_USER=continuum
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: continuum-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
```

### Full Stack (Production-Ready)

```yaml
version: '3.8'

services:
  continuum:
    image: continuum/continuum:latest
    container_name: continuum
    ports:
      - "8420:8420"
    environment:
      - CONTINUUM_STORAGE_BACKEND=postgresql
      - CONTINUUM_CONNECTION_STRING=postgresql://continuum:${POSTGRES_PASSWORD}@postgres:5432/continuum_db
      - CONTINUUM_ENABLE_CACHE=true
      - CONTINUUM_REDIS_URL=redis://redis:6379/0
      - CONTINUUM_ENABLE_FEDERATION=true
      - CONTINUUM_FEDERATION_URL=${FEDERATION_URL}
      - CONTINUUM_API_KEYS=${API_KEYS}
      - CONTINUUM_LOG_LEVEL=info
      - CONTINUUM_ENABLE_AUDIT_LOG=true
    volumes:
      - continuum-logs:/var/log/continuum
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8420/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=continuum_db
      - POSTGRES_USER=continuum
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U continuum"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    container_name: continuum-prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    restart: unless-stopped

  # Optional: Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: continuum-grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  continuum-logs:
  prometheus-data:
  grafana-data:
```

Create `.env` file:

```bash
POSTGRES_PASSWORD=secure_password_here
REDIS_PASSWORD=redis_password_here
API_KEYS=key1,key2,key3
FEDERATION_URL=https://federation.continuum.ai
GRAFANA_PASSWORD=grafana_password_here
```

Start:

```bash
docker-compose --env-file .env up -d
```

## Configuration

### Environment Variables

```bash
# Core
CONTINUUM_STORAGE_PATH=/data
CONTINUUM_STORAGE_BACKEND=sqlite  # or postgresql
CONTINUUM_CONNECTION_STRING=postgresql://...
CONTINUUM_INSTANCE_ID=docker-instance
CONTINUUM_TENANT_ID=default

# Logging
CONTINUUM_LOG_LEVEL=info  # debug, info, warning, error
CONTINUUM_LOG_FORMAT=json # or text

# API
CONTINUUM_API_HOST=0.0.0.0
CONTINUUM_API_PORT=8420
CONTINUUM_ENABLE_CORS=true
CONTINUUM_CORS_ORIGINS=*

# Security
CONTINUUM_REQUIRE_API_KEY=true
CONTINUUM_API_KEYS=key1,key2,key3
CONTINUUM_RATE_LIMIT=60

# Performance
CONTINUUM_ENABLE_CACHE=true
CONTINUUM_REDIS_URL=redis://redis:6379/0
CONTINUUM_MAX_RESULTS=100

# Federation
CONTINUUM_ENABLE_FEDERATION=true
CONTINUUM_FEDERATION_URL=https://federation.continuum.ai
CONTINUUM_FEDERATION_SECRET=your_secret

# Monitoring
CONTINUUM_ENABLE_METRICS=true
CONTINUUM_METRICS_PORT=9100
```

### Volume Mounts

```bash
# Data directory
-v continuum-data:/data

# Configuration file
-v $(pwd)/config.json:/etc/continuum/config.json

# Logs
-v $(pwd)/logs:/var/log/continuum

# Backups
-v $(pwd)/backups:/backups
```

## Networking

### Port Mapping

- `8420` - Main API port
- `8421` - Federation protocol port
- `8422` - Gossip protocol port (federation)
- `9100` - Prometheus metrics port (optional)

### Docker Networks

Create custom network for service isolation:

```bash
docker network create continuum-network

docker run -d \
  --name continuum \
  --network continuum-network \
  -p 8420:8420 \
  continuum/continuum:latest
```

## Health Checks

### Built-in Health Endpoint

```bash
curl http://localhost:8420/v1/health
```

Response:

```json
{
  "status": "healthy",
  "version": "0.2.0",
  "database": "connected",
  "cache": "connected",
  "federation": "connected"
}
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8420/v1/health || exit 1
```

## Persistence

### Named Volumes

```bash
# Create volume
docker volume create continuum-data

# Use volume
docker run -d \
  --name continuum \
  -v continuum-data:/data \
  continuum/continuum:latest

# Inspect volume
docker volume inspect continuum-data

# Backup volume
docker run --rm \
  -v continuum-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/continuum-data-backup.tar.gz /data
```

### Bind Mounts

```bash
# Use host directory
docker run -d \
  --name continuum \
  -v $(pwd)/data:/data \
  continuum/continuum:latest

# Ensure correct permissions
chmod 755 $(pwd)/data
```

## Security

### Running as Non-Root

```dockerfile
USER continuum:continuum
```

Container runs as UID/GID 1000:1000 by default.

### Secrets Management

Using Docker secrets (Swarm mode):

```yaml
version: '3.8'

services:
  continuum:
    image: continuum/continuum:latest
    secrets:
      - db_password
      - api_keys
    environment:
      - CONTINUUM_CONNECTION_STRING_FILE=/run/secrets/db_password
      - CONTINUUM_API_KEYS_FILE=/run/secrets/api_keys

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_keys:
    file: ./secrets/api_keys.txt
```

## Monitoring

### Logs

```bash
# View logs
docker logs continuum

# Follow logs
docker logs -f continuum

# Last 100 lines
docker logs --tail 100 continuum

# With timestamps
docker logs -t continuum
```

### Metrics

Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'continuum'
    static_configs:
      - targets: ['continuum:9100']
```

## Backup & Restore

### Database Backup

```bash
# SQLite
docker exec continuum continuum export /data/backup.json

# Copy to host
docker cp continuum:/data/backup.json ./backup.json

# PostgreSQL
docker exec continuum-postgres pg_dump -U continuum continuum_db > backup.sql
```

### Volume Backup

```bash
# Backup named volume
docker run --rm \
  -v continuum-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/continuum-$(date +%Y%m%d).tar.gz /data

# Restore named volume
docker run --rm \
  -v continuum-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/continuum-20251206.tar.gz --strip 1"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs continuum

# Inspect container
docker inspect continuum

# Check exit code
docker ps -a | grep continuum
```

### Permission Denied

```bash
# Fix volume permissions
docker run --rm \
  -v continuum-data:/data \
  alpine chown -R 1000:1000 /data
```

### Database Connection Failed

```bash
# Check network
docker network inspect bridge

# Test connection
docker exec continuum ping postgres

# Check credentials
docker exec continuum env | grep CONTINUUM_CONNECTION_STRING
```

### High Memory Usage

```bash
# Check resource usage
docker stats continuum

# Set memory limit
docker run -d \
  --name continuum \
  --memory=2g \
  --memory-swap=2g \
  continuum/continuum:latest
```

## Building Custom Images

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -r continuum && useradd -r -g continuum continuum

# Install CONTINUUM
RUN pip install --no-cache-dir continuum-memory[all]

# Set working directory
WORKDIR /app

# Create data directory
RUN mkdir -p /data && chown continuum:continuum /data

# Switch to non-root user
USER continuum

# Expose ports
EXPOSE 8420 8421 8422 9100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8420/v1/health').raise_for_status()"

# Start CONTINUUM
CMD ["continuum", "serve", "--host", "0.0.0.0", "--port", "8420"]
```

Build:

```bash
docker build -t my-continuum:latest .
```

## Next Steps

- [Kubernetes Deployment](kubernetes.md) - Production orchestration
- [Cloud Platforms](cloud.md) - Managed cloud deployments
- [Security Guide](security.md) - Security best practices

---

**The pattern persists.**
