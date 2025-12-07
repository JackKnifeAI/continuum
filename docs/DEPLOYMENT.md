# CONTINUUM Deployment Guide

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Platforms](#cloud-platforms)
5. [Kubernetes](#kubernetes)
6. [Configuration Management](#configuration-management)
7. [Database Setup](#database-setup)
8. [Scaling Strategies](#scaling-strategies)
9. [Monitoring & Operations](#monitoring--operations)
10. [Security Hardening](#security-hardening)
11. [Troubleshooting](#troubleshooting)

---

## Deployment Options

### Comparison Matrix

| Deployment Type | Best For | Complexity | Scalability | Cost |
|----------------|----------|------------|-------------|------|
| **Local SQLite** | Development, testing | ⭐ Simple | Limited | Free |
| **Docker** | Small-medium deployments | ⭐⭐ Moderate | Good | Low |
| **Fly.io** | Global edge deployment | ⭐⭐ Moderate | Excellent | Medium |
| **Kubernetes** | Enterprise, high-scale | ⭐⭐⭐⭐⭐ Complex | Excellent | High |
| **Cloudflare Workers** | Serverless, global | ⭐⭐⭐ Moderate | Excellent | Low-Medium |

---

## Local Development

### Quick Start

```bash
# Install CONTINUUM
pip install continuum-memory

# Initialize database
continuum init --db-path ./data/memory.db

# Run development server
continuum serve --port 8420 --reload

# Access API
# - Docs: http://localhost:8420/docs
# - Health: http://localhost:8420/v1/health
```

### Development Setup with All Features

```bash
# Install with all optional dependencies
pip install continuum-memory[all]

# Set environment variables
export CONTINUUM_DB_PATH="./data/memory.db"
export CONTINUUM_ENV="development"
export CONTINUUM_ENABLE_EMBEDDINGS="true"
export CONTINUUM_ENABLE_FEDERATION="true"

# Initialize with PostgreSQL (optional)
export POSTGRES_URL="postgresql://user:pass@localhost:5432/continuum"
continuum init --use-postgres

# Run with Redis cache (optional)
export REDIS_URL="redis://localhost:6379/0"
export CONTINUUM_CACHE_ENABLED="true"

# Start server
continuum serve --port 8420 --reload
```

### Directory Structure

```
project/
├── data/                       # Data directory
│   ├── memory.db              # SQLite database
│   ├── backups/               # Backup files
│   └── logs/                  # Log files
├── .env                        # Environment variables
└── continuum_config.json      # Configuration file
```

---

## Docker Deployment

### Single Container (SQLite)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install continuum-memory

# Create data directory
RUN mkdir -p /data

# Set working directory
WORKDIR /app

# Environment variables
ENV CONTINUUM_DB_PATH=/data/memory.db
ENV CONTINUUM_ENV=production

# Expose port
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8420/v1/health || exit 1

# Run server
CMD ["continuum", "serve", "--host", "0.0.0.0", "--port", "8420"]
```

**Run**:
```bash
# Build image
docker build -t continuum:latest .

# Run container
docker run -d \
  --name continuum \
  -p 8420:8420 \
  -v $(pwd)/data:/data \
  continuum:latest

# View logs
docker logs -f continuum

# Stop
docker stop continuum
```

### Docker Compose (Full Stack)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # CONTINUUM API
  api:
    image: continuum-memory:latest
    build: .
    ports:
      - "8420:8420"
    environment:
      CONTINUUM_ENV: production
      POSTGRES_URL: postgresql://continuum:password@postgres:5432/continuum
      REDIS_URL: redis://redis:6379/0
      CONTINUUM_CACHE_ENABLED: "true"
      CONTINUUM_REQUIRE_API_KEY: "true"
      CONTINUUM_API_KEY: ${CONTINUUM_API_KEY}
      SENTRY_DSN: ${SENTRY_DSN}
      POSTHOG_API_KEY: ${POSTHOG_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8420/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: continuum
      POSTGRES_USER: continuum
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U continuum"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redisdata:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx Reverse Proxy (optional)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local
```

**.env**:
```bash
# API Keys
CONTINUUM_API_KEY=your-secure-api-key-here

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
POSTHOG_API_KEY=phc_...

# Database (if using external)
# POSTGRES_URL=postgresql://user:pass@host:5432/db

# Stripe (if using billing)
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...
```

**Deploy**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale API servers
docker-compose up -d --scale api=3

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Cloud Platforms

### Fly.io Deployment

**fly.toml**:
```toml
app = "continuum-memory"
primary_region = "iad"

[build]
  image = "continuum-memory:latest"

[env]
  CONTINUUM_ENV = "production"
  CONTINUUM_REQUIRE_API_KEY = "true"

[[services]]
  http_checks = []
  internal_port = 8420
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 100
    soft_limit = 80
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "10s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

  [[services.http_checks]]
    interval = "30s"
    grace_period = "10s"
    method = "get"
    path = "/v1/health"
    protocol = "http"
    timeout = "5s"
    tls_skip_verify = false

# Scale configuration
[scaling]
  min_machines = 2
  max_machines = 10

# Regions for global deployment
[[services.regions]]
  regions = ["iad", "lhr", "syd", "hkg"]

# Database (use Fly Postgres or Supabase)
[[statics]]
  guest_path = "/data"
  url_prefix = "/data"
```

**Deploy**:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly apps create continuum-memory

# Set secrets
fly secrets set CONTINUUM_API_KEY=your-key
fly secrets set POSTGRES_URL=postgresql://...
fly secrets set SENTRY_DSN=https://...

# Deploy
fly deploy

# View status
fly status

# View logs
fly logs

# Scale up
fly scale count 3

# Scale to multiple regions
fly regions add lhr syd hkg

# Destroy app
fly apps destroy continuum-memory
```

**Using Supabase for PostgreSQL**:
```bash
# Create Supabase project at https://supabase.com

# Get connection string
# Project Settings → Database → Connection String

# Set as secret
fly secrets set POSTGRES_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
```

**Using Upstash for Redis**:
```bash
# Create Upstash Redis at https://upstash.com

# Get connection URL

# Set as secret
fly secrets set REDIS_URL="redis://:[password]@[region].upstash.io:6379"
fly secrets set CONTINUUM_CACHE_ENABLED="true"
```

### Railway Deployment

**railway.json**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "continuum serve --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/v1/health",
    "healthcheckTimeout": 100
  }
}
```

**Deploy**:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create project
railway init

# Add PostgreSQL
railway add --plugin postgresql

# Add Redis
railway add --plugin redis

# Set environment variables
railway variables set CONTINUUM_ENV=production
railway variables set CONTINUUM_REQUIRE_API_KEY=true

# Deploy
railway up

# View logs
railway logs

# Open in browser
railway open
```

### Cloudflare Workers (Serverless)

**wrangler.toml**:
```toml
name = "continuum-worker"
type = "javascript"
account_id = "your-account-id"
workers_dev = true

[env.production]
route = "https://continuum.yourdomain.com/*"
zone_id = "your-zone-id"

[[d1_databases]]
binding = "DB"
database_name = "continuum"
database_id = "your-database-id"

[[kv_namespaces]]
binding = "CACHE"
id = "your-kv-id"
```

**worker.js**:
```javascript
// Simplified - use Cloudflare Workers adaptation
import { Continuum } from 'continuum-worker';

export default {
  async fetch(request, env, ctx) {
    const continuum = new Continuum({
      db: env.DB,
      cache: env.CACHE
    });

    return continuum.handleRequest(request);
  }
}
```

**Deploy**:
```bash
# Install Wrangler
npm install -g wrangler

# Login
wrangler login

# Create D1 database
wrangler d1 create continuum

# Create KV namespace
wrangler kv:namespace create CACHE

# Deploy
wrangler publish

# View logs
wrangler tail
```

---

## Kubernetes

### Helm Chart

**values.yaml**:
```yaml
replicaCount: 3

image:
  repository: continuum-memory
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: LoadBalancer
  port: 80
  targetPort: 8420

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: continuum.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: continuum-tls
      hosts:
        - continuum.yourdomain.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

postgresql:
  enabled: true
  auth:
    username: continuum
    password: password
    database: continuum
  primary:
    persistence:
      enabled: true
      size: 100Gi
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi

redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: true
    password: password
  master:
    persistence:
      enabled: true
      size: 10Gi

env:
  - name: CONTINUUM_ENV
    value: "production"
  - name: CONTINUUM_REQUIRE_API_KEY
    value: "true"
  - name: POSTGRES_URL
    valueFrom:
      secretKeyRef:
        name: continuum-secrets
        key: postgres-url
  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: continuum-secrets
        key: redis-url
  - name: CONTINUUM_API_KEY
    valueFrom:
      secretKeyRef:
        name: continuum-secrets
        key: api-key
```

**Deploy with Helm**:
```bash
# Add CONTINUUM Helm repo (if published)
helm repo add continuum https://charts.continuum.ai
helm repo update

# Install
helm install continuum continuum/continuum \
  --namespace continuum \
  --create-namespace \
  --values values.yaml

# Upgrade
helm upgrade continuum continuum/continuum \
  --namespace continuum \
  --values values.yaml

# Rollback
helm rollback continuum

# Uninstall
helm uninstall continuum --namespace continuum
```

**Deploy with kubectl**:
```bash
# Create namespace
kubectl create namespace continuum

# Create secrets
kubectl create secret generic continuum-secrets \
  --namespace continuum \
  --from-literal=postgres-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  --from-literal=api-key="your-api-key"

# Apply manifests
kubectl apply -f infrastructure/kubernetes/ --namespace continuum

# View pods
kubectl get pods -n continuum

# View logs
kubectl logs -f deployment/continuum-api -n continuum

# Port forward for testing
kubectl port-forward service/continuum-api 8420:80 -n continuum

# Delete
kubectl delete namespace continuum
```

### Kubernetes Manifests

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: continuum-api
  namespace: continuum
spec:
  replicas: 3
  selector:
    matchLabels:
      app: continuum-api
  template:
    metadata:
      labels:
        app: continuum-api
    spec:
      containers:
      - name: api
        image: continuum-memory:latest
        ports:
        - containerPort: 8420
        env:
        - name: CONTINUUM_ENV
          value: "production"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: continuum-secrets
              key: postgres-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: continuum-secrets
              key: redis-url
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8420
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /v1/health
            port: 8420
          initialDelaySeconds: 5
          periodSeconds: 10
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: continuum-api
  namespace: continuum
spec:
  type: LoadBalancer
  selector:
    app: continuum-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8420
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: continuum-ingress
  namespace: continuum
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - continuum.yourdomain.com
    secretName: continuum-tls
  rules:
  - host: continuum.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: continuum-api
            port:
              number: 80
```

**hpa.yaml** (Horizontal Pod Autoscaler):
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: continuum-api-hpa
  namespace: continuum
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: continuum-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Configuration Management

### Environment Variables

**Production .env**:
```bash
# Environment
CONTINUUM_ENV=production

# Database
POSTGRES_URL=postgresql://user:pass@host:5432/continuum
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=40

# Cache
REDIS_URL=redis://host:6379/0
CONTINUUM_CACHE_ENABLED=true
CONTINUUM_CACHE_TTL=300

# API
CONTINUUM_API_PORT=8420
CONTINUUM_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CONTINUUM_REQUIRE_API_KEY=true
CONTINUUM_API_KEY=your-secure-key

# Security
CONTINUUM_ENCRYPTION_KEY=your-32-byte-key
CONTINUUM_JWT_SECRET=your-jwt-secret

# Features
CONTINUUM_ENABLE_EMBEDDINGS=true
CONTINUUM_ENABLE_FEDERATION=true
CONTINUUM_ENABLE_WEBHOOKS=true

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
SENTRY_TRACES_SAMPLE_RATE=0.1
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://app.posthog.com

# Billing (if enabled)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Secrets Management

**Using Kubernetes Secrets**:
```bash
# Create from literals
kubectl create secret generic continuum-secrets \
  --from-literal=postgres-url="postgresql://..." \
  --from-literal=api-key="..." \
  --namespace continuum

# Create from file
kubectl create secret generic continuum-secrets \
  --from-file=.env \
  --namespace continuum

# View secret
kubectl get secret continuum-secrets -n continuum -o yaml
```

**Using Vault**:
```bash
# Store in Vault
vault kv put secret/continuum \
  postgres_url="postgresql://..." \
  api_key="..."

# Inject into Kubernetes (using Vault Agent)
# See: https://www.vaultproject.io/docs/platform/k8s
```

**Using AWS Secrets Manager**:
```bash
# Store secret
aws secretsmanager create-secret \
  --name continuum/prod/config \
  --secret-string '{"postgres_url":"...","api_key":"..."}'

# Retrieve in application
# Use AWS SDK or external-secrets operator
```

---

## Database Setup

### PostgreSQL Initialization

**1. Create Database**:
```sql
-- As postgres superuser
CREATE DATABASE continuum;
CREATE USER continuum WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE continuum TO continuum;

-- Connect to database
\c continuum

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search
```

**2. Run Migrations**:
```bash
# Using CONTINUUM CLI
continuum init --use-postgres

# Or manually
psql -U continuum -d continuum -f schema.sql
```

**3. Create Indexes**:
```sql
-- Performance indexes
CREATE INDEX idx_entities_tenant_name ON entities(tenant_id, LOWER(name));
CREATE INDEX idx_entities_created ON entities(created_at DESC);
CREATE INDEX idx_messages_tenant_instance ON auto_messages(tenant_id, instance_id);
CREATE INDEX idx_links_tenant_concepts ON attention_links(tenant_id, concept_a, concept_b);
CREATE INDEX idx_links_strength ON attention_links(strength DESC) WHERE strength > 0.5;

-- Full-text search
CREATE INDEX idx_entities_description_fts ON entities USING gin(to_tsvector('english', description));
```

**4. Set Up Replication (Production)**:
```bash
# On primary
# postgresql.conf
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3

# Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';

# pg_hba.conf
host replication replicator replica_ip/32 md5

# On replica
# Create replication slot on primary
SELECT * FROM pg_create_physical_replication_slot('replica_1');

# recovery.conf (PostgreSQL < 12) or postgresql.conf (>= 12)
primary_conninfo = 'host=primary_ip port=5432 user=replicator password=repl_password'
primary_slot_name = 'replica_1'
```

### Database Backups

**Automated Backups (PostgreSQL)**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="continuum"

# Full backup
pg_dump -U continuum -Fc $DB_NAME > $BACKUP_DIR/continuum_$DATE.dump

# Upload to S3
aws s3 cp $BACKUP_DIR/continuum_$DATE.dump s3://backups/continuum/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "continuum_*.dump" -mtime +30 -delete

# Verify backup
pg_restore --list $BACKUP_DIR/continuum_$DATE.dump > /dev/null
if [ $? -eq 0 ]; then
  echo "Backup successful: continuum_$DATE.dump"
else
  echo "Backup verification failed!"
  exit 1
fi
```

**Cron Schedule**:
```cron
# Daily full backup at 2 AM
0 2 * * * /path/to/backup.sh

# Hourly incremental backup
0 * * * * pg_basebackup -D /backups/incremental/$(date +\%H)
```

**Restore**:
```bash
# Stop application
kubectl scale deployment continuum-api --replicas=0 -n continuum

# Restore database
pg_restore -U continuum -d continuum -c /backups/continuum_20251207_020000.dump

# Start application
kubectl scale deployment continuum-api --replicas=3 -n continuum
```

---

## Scaling Strategies

### Vertical Scaling

**Increase Container Resources**:
```yaml
# Kubernetes
resources:
  requests:
    cpu: 2000m      # Was: 500m
    memory: 4Gi     # Was: 1Gi
  limits:
    cpu: 4000m      # Was: 1000m
    memory: 8Gi     # Was: 2Gi
```

### Horizontal Scaling

**Increase Replica Count**:
```bash
# Docker Compose
docker-compose up -d --scale api=5

# Kubernetes
kubectl scale deployment continuum-api --replicas=5 -n continuum

# Fly.io
fly scale count 5
```

**Auto-Scaling**:
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: continuum-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: continuum-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Scaling

**Read Replicas**:
```
┌──────────────┐
│   Primary    │ (Write)
│  PostgreSQL  │
└──────┬───────┘
       │
       ├─→ Replica 1 (Read)
       ├─→ Replica 2 (Read)
       └─→ Replica 3 (Read)
```

**Connection Pooling (PgBouncer)**:
```ini
# pgbouncer.ini
[databases]
continuum = host=postgres port=5432 dbname=continuum

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

### Caching Strategy

```
Request
  │
  ├─→ L1: In-memory (40% hit rate, <1ms)
  │
  ├─→ L2: Redis (35% hit rate, ~3ms)
  │
  └─→ L3: Database (25% miss, ~25ms)
```

---

## Monitoring & Operations

### Health Checks

**Endpoint**: `GET /v1/health`

**Response**:
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "disk_space": "healthy"
  }
}
```

**Kubernetes Probes**:
```yaml
livenessProbe:
  httpGet:
    path: /v1/health
    port: 8420
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /v1/health
    port: 8420
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

### Metrics (Prometheus)

**Exposed Metrics**:
```
# Requests
continuum_requests_total{method="POST",endpoint="/v1/recall",status="200"} 1250

# Latency
continuum_request_duration_seconds{endpoint="/v1/recall",quantile="0.95"} 0.023

# Memory operations
continuum_memories_stored_total 5420
continuum_concepts_extracted_total 12589

# Cache
continuum_cache_hits_total 8934
continuum_cache_misses_total 1243
```

**Prometheus Config**:
```yaml
scrape_configs:
  - job_name: 'continuum'
    static_configs:
      - targets: ['continuum-api:8420']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Logging

**Structured JSON Logs**:
```json
{
  "timestamp": "2025-12-07T12:00:00.123Z",
  "level": "INFO",
  "message": "Memory recalled",
  "tenant_id": "user_123",
  "instance_id": "claude-20251207-120000",
  "query_time_ms": 23.4,
  "concepts_found": 12
}
```

**Centralized Logging (ELK Stack)**:
```yaml
# Filebeat config
filebeat.inputs:
  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

# Logstash filter
filter {
  json {
    source => "message"
  }
  mutate {
    add_field => { "service" => "continuum" }
  }
}
```

### Alerting

**Prometheus Alerts**:
```yaml
groups:
  - name: continuum
    rules:
      - alert: HighErrorRate
        expr: rate(continuum_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: continuum_request_duration_seconds{quantile="0.95"} > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"

      - alert: LowCacheHitRate
        expr: rate(continuum_cache_hits_total[5m]) / rate(continuum_cache_requests_total[5m]) < 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate below 50%"
```

---

## Security Hardening

### Network Security

**Firewall Rules**:
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5432/tcp   # Block direct PostgreSQL access
ufw deny 6379/tcp   # Block direct Redis access
ufw enable
```

**Kubernetes Network Policies**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: continuum-network-policy
  namespace: continuum
spec:
  podSelector:
    matchLabels:
      app: continuum-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8420
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

### TLS/SSL Configuration

**Nginx SSL**:
```nginx
server {
    listen 443 ssl http2;
    server_name continuum.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        proxy_pass http://continuum-api:8420;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Security

**PostgreSQL Hardening**:
```sql
-- Revoke public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Create read-only user
CREATE USER continuum_readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE continuum TO continuum_readonly;
GRANT USAGE ON SCHEMA public TO continuum_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO continuum_readonly;

-- Enable SSL
-- postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'

-- Restrict connections
-- pg_hba.conf
hostssl all all 0.0.0.0/0 md5
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Errors**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql "postgresql://user:pass@host:5432/continuum"

# Check connection pool
SELECT count(*) FROM pg_stat_activity;
```

**2. High Memory Usage**:
```bash
# Check container memory
docker stats

# Check for memory leaks
# Restart with lower pool size
POSTGRES_POOL_SIZE=10 continuum serve
```

**3. Slow Queries**:
```sql
-- Enable query logging
ALTER DATABASE continuum SET log_min_duration_statement = 1000;

-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze query
EXPLAIN ANALYZE SELECT ...;
```

**4. WebSocket Disconnects**:
```bash
# Check load balancer timeout
# Nginx: proxy_read_timeout 600s;

# Check heartbeat
# Client should respond to heartbeat within 90s
```

### Debug Mode

```bash
# Enable debug logging
export CONTINUUM_LOG_LEVEL=DEBUG
continuum serve

# View detailed logs
docker logs -f continuum | grep DEBUG
```

---

**Pattern deploys. Intelligence scales.**

π×φ = 5.083203692315260
