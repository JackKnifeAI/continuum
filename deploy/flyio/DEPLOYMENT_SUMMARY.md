# CONTINUUM Fly.io Deployment - Summary

Complete Fly.io deployment infrastructure created on 2025-12-06.

## Files Created

```
deploy/flyio/
├── fly.toml                    # Fly.io app configuration
├── Dockerfile                  # Multi-stage production container
├── .dockerignore              # Build exclusions
├── README.md                  # Complete deployment guide
├── DEPLOYMENT_SUMMARY.md      # This file
└── scripts/
    ├── deploy.sh              # Automated deployment
    ├── migrate.sh             # Database migrations
    └── scale.sh               # Instance scaling
```

## Configuration Highlights

### fly.toml
- **App name:** continuum-memory
- **Primary region:** iad (Ashburn, VA)
- **Port:** 8420
- **Auto-scaling:** Enabled (1-10 instances)
- **Health checks:** /v1/health endpoint
- **Rolling deployments:** Zero downtime
- **Multi-region ready:** iad, lhr, sin

### Dockerfile
- **Base:** Python 3.11 slim
- **Build:** Multi-stage for minimal size
- **User:** Non-root (continuum:1000)
- **Workers:** 2 uvicorn workers
- **Health check:** Built-in every 30s
- **Security:** Minimal attack surface

### Scripts

**deploy.sh**
- Pre-flight checks (git, docker, fly CLI)
- Automated deployment with rollback
- Health verification
- Git commit tracking

**migrate.sh**
- Database schema migrations
- Migration status checking
- Rollback capability
- Backup creation

**scale.sh**
- Instance scaling (up/down)
- Multi-region deployment
- VM resource scaling
- Auto-scaling configuration

## Quick Start

### 1. Initial Setup

```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
cd deploy/flyio
fly apps create continuum-memory

# Create and attach Postgres
fly postgres create --name continuum-memory-db
fly postgres attach continuum-memory-db -a continuum-memory
```

### 2. Configure Secrets

```bash
# Required secrets
fly secrets set \
  CONTINUUM_CORS_ORIGINS=https://app.example.com \
  -a continuum-memory

# Optional: Redis (Upstash)
fly secrets set REDIS_URL=redis://... -a continuum-memory

# Optional: Stripe
fly secrets set \
  STRIPE_SECRET_KEY=sk_live_... \
  STRIPE_WEBHOOK_SECRET=whsec_... \
  -a continuum-memory
```

### 3. Deploy

```bash
# Deploy application
./scripts/deploy.sh

# Run migrations
./scripts/migrate.sh

# Scale to production (optional)
./scripts/scale.sh up 3 iad,lhr,sin
```

### 4. Verify

```bash
# Check status
fly status -a continuum-memory

# Test health endpoint
curl https://continuum-memory.fly.dev/v1/health

# View logs
fly logs -a continuum-memory
```

## Architecture

### Multi-Region Setup

**Primary Region:** iad (US East)
- Lowest latency for US users
- Main database instance

**Secondary Regions:** lhr, sin
- lhr: Europe (London)
- sin: Asia Pacific (Singapore)
- Read replicas for low latency

### Database

**Fly Postgres** (recommended)
- Managed PostgreSQL cluster
- Automatic backups
- Multi-region replication
- Connection pooling

**Alternative:** External Postgres
- Supabase, Neon, AWS RDS
- Set via DATABASE_URL secret

### Caching

**Upstash Redis** (recommended)
- Global edge caching
- Serverless pricing
- Set via REDIS_URL secret

### Auto-Scaling

**Configuration:**
- Min instances: 1
- Max instances: 10
- Auto-stop when idle
- Auto-start on requests
- Soft limit: 200 requests
- Hard limit: 250 requests

## Deployment Strategies

### Rolling (Default)
- Zero downtime
- Gradual replacement
- Auto-rollback on failure

### Blue-Green
```bash
# Create green deployment
fly apps create continuum-memory-green
fly deploy -a continuum-memory-green

# Test and swap
```

### Canary
```bash
# Deploy to 1 instance
fly deploy --strategy canary

# If healthy, deploy all
fly deploy --strategy rolling
```

## Monitoring

### Health Checks

**Endpoint:** GET /v1/health
**Interval:** 30s
**Timeout:** 10s
**Grace period:** 30s

**Response:**
```json
{
  "status": "healthy",
  "service": "continuum",
  "version": "0.1.0",
  "timestamp": "2025-12-06T10:00:00Z"
}
```

### Logs

```bash
# Live logs
fly logs -a continuum-memory

# Filter by instance
fly logs -a continuum-memory --instance <id>

# Export
fly logs -a continuum-memory > logs.txt
```

### Metrics

```bash
# Status dashboard
fly dashboard -a continuum-memory

# Grafana metrics
fly dashboard metrics -a continuum-memory
```

## Cost Estimates

### Development
- 1x shared-cpu-1x: $2/month
- Postgres hobby tier: $0/month
- **Total: ~$2/month**

### Production (Recommended)
- 3x shared-cpu-2x: $12/month
- Postgres dedicated: $30/month
- Redis (Upstash): $10/month
- **Total: ~$52/month**

### High-Scale
- 10x dedicated-cpu-2x: $600/month
- 3x Postgres (multi-region): $180/month
- Redis Pro: $40/month
- **Total: ~$820/month**

## Security

### API Authentication
- X-API-Key header required
- Key management via /v1/keys
- Tenant isolation enforced

### Network Security
- HTTPS enforced (automatic certs)
- CORS configured via secrets
- Rate limiting via concurrency

### Database Security
- Encrypted connections (SSL)
- Private networking
- IP allowlisting available

### Container Security
- Non-root user (continuum:1000)
- Minimal base image
- No unnecessary packages

## Troubleshooting

### Deployment Fails

```bash
# Check logs
fly logs -a continuum-memory

# Rollback
./scripts/deploy.sh --rollback

# Or manual
fly releases rollback <version> -a continuum-memory
```

### Health Check Failing

```bash
# SSH into instance
fly ssh console -a continuum-memory

# Test locally
curl http://localhost:8420/v1/health

# Check environment
env | grep DATABASE_URL
```

### Database Issues

```bash
# Check Postgres status
fly postgres status -a continuum-memory-db

# Connect to database
fly postgres connect -a continuum-memory-db

# Run migration
./scripts/migrate.sh
```

### High Latency

```bash
# Deploy to more regions
./scripts/scale.sh regions iad,lhr,sin,syd 4

# Upgrade VM
./scripts/scale.sh vm dedicated-cpu-2x
```

## Maintenance

### Backups

```bash
# Create backup
./scripts/migrate.sh --backup

# Automated backups
fly postgres backups -a continuum-memory-db
```

### Updates

```bash
# Pull latest code
git pull

# Deploy update
./scripts/deploy.sh

# Run migrations
./scripts/migrate.sh
```

### Scaling

```bash
# Scale up
./scripts/scale.sh up 5

# Scale down
./scripts/scale.sh down 2

# Multi-region
./scripts/scale.sh regions iad,lhr,sin 3
```

## Next Steps

After deployment:

1. **Configure Custom Domain**
   ```bash
   fly certs add app.example.com -a continuum-memory
   ```

2. **Setup Monitoring**
   - Configure log aggregation
   - Setup alerts for errors
   - Monitor resource usage

3. **Load Testing**
   - Test with production load
   - Verify auto-scaling
   - Check regional latency

4. **Documentation**
   - Update API docs
   - Document integration
   - Create runbooks

5. **CI/CD Integration**
   - Automate deployments
   - Add testing pipeline
   - Setup staging environment

## Resources

- **Fly.io Docs:** https://fly.io/docs
- **Fly.io Pricing:** https://fly.io/pricing
- **CONTINUUM API:** https://continuum-memory.fly.dev/docs
- **Support:** contact@jackknifeai.com

---

**Deployment infrastructure ready!**

Run `./scripts/deploy.sh` to get started.
