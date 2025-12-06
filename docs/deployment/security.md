# Production Deployment Security Guide

This guide provides step-by-step instructions for securely deploying CONTINUUM in production.

## Prerequisites

- Linux server (Ubuntu 22.04 LTS recommended)
- Docker (optional but recommended)
- Domain with SSL certificate
- Reverse proxy (nginx or Caddy)

## 1. Pre-Deployment Security Checklist

### Environment Configuration

```bash
# Generate secure secrets
python3 -c "import secrets; print(f'CONTINUUM_SECRET_KEY={secrets.token_hex(32)}')" >> .env
python3 -c "import secrets; print(f'CONTINUUM_DB_KEY={secrets.token_hex(32)}')" >> .env

# Set production environment
echo "CONTINUUM_ENV=production" >> .env
echo "CONTINUUM_DEBUG=false" >> .env
echo "CONTINUUM_REQUIRE_API_KEY=true" >> .env

# Configure CORS for your domain
echo "CONTINUUM_CORS_ORIGINS=https://yourdomain.com" >> .env

# Enable encryption
echo "CONTINUUM_ENCRYPT_DB=true" >> .env

# Secure file permissions
chmod 600 .env
```

### Database Security

```bash
# PostgreSQL recommended for production
echo "POSTGRES_HOST=localhost" >> .env
echo "POSTGRES_PORT=5432" >> .env
echo "POSTGRES_DB=continuum_prod" >> .env
echo "POSTGRES_USER=continuum_prod" >> .env

# Generate strong database password
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env
echo "POSTGRES_SSL_MODE=require" >> .env
```

### API Security

```bash
# Rate limiting with Redis
echo "CONTINUUM_RATE_LIMIT_ENABLED=true" >> .env
echo "CONTINUUM_REDIS_URL=redis://localhost:6379/0" >> .env

# Log configuration
echo "CONTINUUM_LOG_LEVEL=WARNING" >> .env
echo "CONTINUUM_AUDIT_LOG_ENABLED=true" >> .env
```

## 2. PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE continuum_prod;
CREATE USER continuum_prod WITH ENCRYPTED PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE continuum_prod TO continuum_prod;
ALTER DATABASE continuum_prod OWNER TO continuum_prod;
\q
EOF

# Enable SSL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: ssl = on

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## 3. Redis Setup (for Rate Limiting)

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis for security
sudo nano /etc/redis/redis.conf

# Set:
# bind 127.0.0.1 ::1  (localhost only)
# requirepass <strong-password>
# maxmemory 256mb
# maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server

# Update .env
echo "CONTINUUM_REDIS_URL=redis://:your-redis-password@localhost:6379/0" >> .env
```

## 4. Application Deployment

### Option A: Docker (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY continuum/ ./continuum/

# Security: Run as non-root
RUN useradd -m -u 1000 continuum && chown -R continuum:continuum /app
USER continuum

# Expose port
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8420/v1/health')"

# Run application
CMD ["uvicorn", "continuum.api.server:app", "--host", "127.0.0.1", "--port", "8420", "--no-access-log"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  continuum:
    build: .
    restart: unless-stopped
    environment:
      - CONTINUUM_ENV=production
    env_file:
      - .env
    volumes:
      - continuum_data:/app/continuum_data
    ports:
      - "127.0.0.1:8420:8420"
    depends_on:
      - postgres
      - redis
    networks:
      - continuum_network

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=continuum_prod
      - POSTGRES_USER=continuum_prod
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - continuum_network
    command: postgres -c ssl=on -c ssl_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem -c ssl_key_file=/etc/ssl/private/ssl-cert-snakeoil.key

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - continuum_network

volumes:
  continuum_data:
  postgres_data:
  redis_data:

networks:
  continuum_network:
    driver: bridge
```

Deploy with:
```bash
docker-compose up -d
```

### Option B: Systemd Service

```ini
# /etc/systemd/system/continuum.service
[Unit]
Description=CONTINUUM Memory API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=continuum
Group=continuum
WorkingDirectory=/opt/continuum
EnvironmentFile=/opt/continuum/.env
ExecStart=/opt/continuum/venv/bin/uvicorn continuum.api.server:app \
    --host 127.0.0.1 \
    --port 8420 \
    --no-access-log \
    --workers 4

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/continuum/continuum_data

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable continuum
sudo systemctl start continuum
sudo systemctl status continuum
```

## 5. Reverse Proxy (nginx)

```nginx
# /etc/nginx/sites-available/continuum
upstream continuum_backend {
    server 127.0.0.1:8420 fail_timeout=10s max_fails=3;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=continuum_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=continuum_conn:10m;

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; object-src 'none'" always;

    # Rate limiting
    limit_req zone=continuum_limit burst=20 nodelay;
    limit_conn continuum_conn 10;

    # Logging
    access_log /var/log/nginx/continuum-access.log;
    error_log /var/log/nginx/continuum-error.log;

    # Request size limit
    client_max_body_size 1M;

    location / {
        proxy_pass http://continuum_backend;
        proxy_http_version 1.1;

        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://continuum_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Enable configuration:
```bash
sudo ln -s /etc/nginx/sites-available/continuum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 6. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Restrict PostgreSQL to localhost
sudo ufw deny 5432/tcp

# Restrict Redis to localhost
sudo ufw deny 6379/tcp
```

## 7. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## 8. Monitoring & Logging

### Log Rotation

```bash
# /etc/logrotate.d/continuum
/var/log/nginx/continuum-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

/opt/continuum/continuum_data/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 continuum continuum
}
```

### Health Monitoring

```bash
# Cron job for health checks
# /etc/cron.d/continuum-health
*/5 * * * * continuum /opt/continuum/scripts/health_check.sh
```

```bash
# /opt/continuum/scripts/health_check.sh
#!/bin/bash
HEALTH_URL="http://127.0.0.1:8420/v1/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "Health check failed: HTTP $RESPONSE" | logger -t continuum
    # Optional: Send alert
    # mail -s "CONTINUUM health check failed" admin@yourdomain.com
fi
```

## 9. Backup Strategy

```bash
# Daily database backup
# /opt/continuum/scripts/backup.sh
#!/bin/bash
BACKUP_DIR="/opt/continuum/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h localhost -U continuum_prod continuum_prod | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Encrypt backup
gpg --encrypt --recipient admin@yourdomain.com $BACKUP_DIR/db_$DATE.sql.gz
rm $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz.gpg s3://your-backup-bucket/continuum/

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz.gpg" -mtime +30 -delete
```

Cron:
```bash
# Daily at 2 AM
0 2 * * * /opt/continuum/scripts/backup.sh
```

## 10. Security Monitoring

### Fail2Ban (Protect against brute force)

```ini
# /etc/fail2ban/filter.d/continuum.conf
[Definition]
failregex = .*"status_code":401.*"client_ip":"<HOST>"
ignoreregex =
```

```ini
# /etc/fail2ban/jail.d/continuum.conf
[continuum]
enabled = true
filter = continuum
logpath = /var/log/nginx/continuum-access.log
maxretry = 5
findtime = 300
bantime = 3600
action = iptables-multiport[name=continuum, port="http,https"]
```

### Intrusion Detection (OSSEC)

```bash
# Install OSSEC
wget https://github.com/ossec/ossec-hiera/archive/master.zip
# Follow OSSEC installation guide

# Monitor continuum logs
echo "/opt/continuum/continuum_data/logs/continuum.log" >> /var/ossec/etc/ossec.conf
```

## 11. API Key Management

### Initial Admin Key

```bash
# Generate first admin API key
python3 -c "
from continuum.api.routes import create_key
from continuum.api.schemas import CreateKeyRequest

request = CreateKeyRequest(
    tenant_id='admin',
    name='Initial Admin Key'
)
# Follow API documentation to create key
"
```

### Key Rotation Script

```bash
# /opt/continuum/scripts/rotate_keys.sh
#!/bin/bash
# Monthly key rotation reminder
echo "Monthly API key rotation reminder" | mail -s "CONTINUUM: Rotate API Keys" admin@yourdomain.com
```

## 12. Post-Deployment Verification

```bash
# 1. Check service status
sudo systemctl status continuum
sudo systemctl status postgresql
sudo systemctl status redis

# 2. Check logs
tail -f /opt/continuum/continuum_data/logs/continuum.log
tail -f /var/log/nginx/continuum-error.log

# 3. Test endpoints
curl https://api.yourdomain.com/v1/health

# 4. Security headers check
curl -I https://api.yourdomain.com

# 5. SSL check
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# 6. Run security scan
nikto -h https://api.yourdomain.com
nmap -sV --script ssl-enum-ciphers api.yourdomain.com
```

## 13. Incident Response Plan

### Security Incident Checklist

1. **Detection**
   - Review logs: `/opt/continuum/continuum_data/logs/`
   - Check monitoring alerts
   - Analyze traffic patterns

2. **Containment**
   - Isolate affected system
   - Block malicious IPs
   - Rotate compromised credentials

3. **Eradication**
   - Remove malware/backdoors
   - Patch vulnerabilities
   - Update firewall rules

4. **Recovery**
   - Restore from backup
   - Verify integrity
   - Resume services

5. **Post-Incident**
   - Document incident
   - Update procedures
   - Communicate with stakeholders

## 14. Maintenance Schedule

### Daily
- Monitor health checks
- Review error logs
- Check disk space

### Weekly
- Review security logs
- Check for failed login attempts
- Verify backups

### Monthly
- Update dependencies
- Rotate API keys
- Security scan
- Review access logs

### Quarterly
- Full security audit
- Penetration testing
- Disaster recovery drill
- Update SSL certificates (if needed)

---

## Support

For security issues, see [SECURITY.md](../SECURITY.md)

For deployment support: [GitHub Issues](https://github.com/yourusername/continuum/issues)

**Last Updated**: 2025-12-06
