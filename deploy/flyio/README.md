# CONTINUUM - Fly.io Deployment Guide

Complete deployment infrastructure for running CONTINUUM AI memory service on Fly.io with PostgreSQL, multi-region support, and auto-scaling.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Database Configuration](#database-configuration)
- [Secrets Management](#secrets-management)
- [Deployment](#deployment)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# 2. Login to Fly.io
fly auth login

# 3. Create app and database
cd deploy/flyio
fly apps create continuum-memory
fly postgres create --name continuum-memory-db

# 4. Attach database
fly postgres attach continuum-memory-db -a continuum-memory

# 5. Set secrets
fly secrets set \
  CONTINUUM_CORS_ORIGINS=https://app.example.com \
  STRIPE_SECRET_KEY=sk_live_... \
  STRIPE_WEBHOOK_SECRET=whsec_... \
  -a continuum-memory

# 6. Deploy
./scripts/deploy.sh

# 7. Run migrations
./scripts/migrate.sh

# 8. Scale to production (optional)
./scripts/scale.sh up 3 iad,lhr,sin
```

---

## Prerequisites

### Required Software

- **Fly.io CLI** - [Install Guide](https://fly.io/docs/hands-on/install-flyctl/)
- **Docker** (optional, for local testing) - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** (recommended for version tracking)

### Fly.io Account

1. Create account at [fly.io/app/sign-up](https://fly.io/app/sign-up)
2. Add payment method (required for databases)
3. Verify email address

### External Services (Optional)

- **Upstash Redis** - For distributed caching (recommended)
  - Create at [upstash.com](https://upstash.com)
  - Copy `REDIS_URL` connection string

- **Stripe** - For billing integration
  - API keys from [stripe.com/dashboard/apikeys](https://dashboard.stripe.com/apikeys)
  - Webhook secret for payment events

---

## Initial Setup

### 1. Install Fly.io CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Verify installation
fly version
```

### 2. Login

```bash
fly auth login
```

### 3. Create Application

```bash
# Create app (interactive)
fly apps create continuum-memory

# Or specify region explicitly
fly apps create continuum-memory --region iad

# List available regions
fly platform regions
```

**Recommended Primary Regions:**
- `iad` - Ashburn, Virginia (US East)
- `lhr` - London, UK (Europe)
- `sin` - Singapore (Asia Pacific)
- `syd` - Sydney, Australia (Oceania)

---

## Database Configuration

### Option 1: Fly Postgres (Recommended)

```bash
# Create Postgres cluster
fly postgres create --name continuum-memory-db \
  --region iad \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Attach to app (sets DATABASE_URL automatically)
fly postgres attach continuum-memory-db -a continuum-memory

# Verify connection
fly postgres connect -a continuum-memory-db
```

**Multi-Region Postgres:**

```bash
# Create replicas in other regions
fly postgres create \
  --name continuum-memory-db-lhr \
  --region lhr \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Add as read replica
fly postgres attach continuum-memory-db-lhr -a continuum-memory
```

### Option 2: External Postgres

```bash
# Use external provider (Supabase, Neon, etc.)
fly secrets set DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  -a continuum-memory
```

### Database Migrations

```bash
# Run migrations
./scripts/migrate.sh

# Check migration status
./scripts/migrate.sh --status

# Rollback migration
./scripts/migrate.sh --rollback

# Create backup
./scripts/migrate.sh --backup
```

---

## Secrets Management

### Required Secrets

```bash
# Database (auto-set by fly postgres attach)
fly secrets set DATABASE_URL="postgresql://..." -a continuum-memory

# CORS origins (production domains)
fly secrets set CONTINUUM_CORS_ORIGINS="https://app.example.com,https://www.example.com" \
  -a continuum-memory

# Redis (optional, for caching)
fly secrets set REDIS_URL="redis://default:...@upstash.io:6379" \
  -a continuum-memory

# Stripe (optional, for billing)
fly secrets set \
  STRIPE_SECRET_KEY="sk_live_..." \
  STRIPE_WEBHOOK_SECRET="whsec_..." \
  -a continuum-memory
```

### View Secrets

```bash
# List secret names (values hidden)
fly secrets list -a continuum-memory

# Remove secret
fly secrets unset SECRET_NAME -a continuum-memory
```

### Environment Variables

Non-sensitive config in `fly.toml`:

```toml
[env]
  CONTINUUM_ENV = "production"
  CONTINUUM_PORT = "8420"
  LOG_LEVEL = "info"
  UVICORN_WORKERS = "2"
```

---

## Deployment

### Deploy Script

```bash
# Deploy to production
./scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh --staging

# Pre-flight checks only
./scripts/deploy.sh --check

# Rollback deployment
./scripts/deploy.sh --rollback
```

### Manual Deployment

```bash
cd deploy/flyio

# Build and deploy
fly deploy --config fly.toml --dockerfile Dockerfile

# Deploy with custom config
fly deploy --config fly.staging.toml --strategy rolling

# Deploy to specific region
fly deploy --region iad
```

### Deployment Strategies

**Rolling Deployment** (default):
- Zero downtime
- Gradual instance replacement
- Automatic rollback on failure

**Canary Deployment:**
```bash
# Deploy to single instance first
fly deploy --strategy canary

# If successful, deploy to all
fly deploy --strategy rolling
```

**Blue-Green Deployment:**
```bash
# Deploy to new app
fly apps create continuum-memory-green
fly deploy -a continuum-memory-green

# Test green deployment
curl https://continuum-memory-green.fly.dev/v1/health

# Swap apps (update DNS/load balancer)
# Then destroy old blue app
```

### Monitoring Deployment

```bash
# Watch deployment progress
fly status -a continuum-memory

# View logs during deployment
fly logs -a continuum-memory

# Check health
curl https://continuum-memory.fly.dev/v1/health
```

---

## Scaling

### Scale Script

```bash
# Show current scale
./scripts/scale.sh status

# Scale up to 3 instances
./scripts/scale.sh up 3

# Scale across regions
./scripts/scale.sh up 3 iad,lhr,sin

# Scale down to 1 instance
./scripts/scale.sh down 1

# Configure auto-scaling
./scripts/scale.sh auto

# Upgrade VM resources
./scripts/scale.sh vm dedicated-cpu-2x
```

### Manual Scaling

**Instance Count:**

```bash
# Scale to specific count
fly scale count 3 -a continuum-memory

# Scale per region
fly scale count 3 --region iad,lhr,sin -a continuum-memory

# Scale with max regions
fly scale count 5 --max-per-region 2 -a continuum-memory
```

**VM Resources:**

```bash
# Show current VM size
fly scale show -a continuum-memory

# Scale to dedicated CPU
fly scale vm dedicated-cpu-2x -a continuum-memory

# Custom memory
fly scale memory 1024 -a continuum-memory
```

**Available VM Sizes:**

| Preset            | RAM   | CPUs          | Cost/Month* |
|-------------------|-------|---------------|-------------|
| shared-cpu-1x     | 256MB | 1 shared      | ~$2         |
| shared-cpu-2x     | 512MB | 1 shared      | ~$4         |
| shared-cpu-4x     | 1GB   | 1 shared      | ~$8         |
| dedicated-cpu-1x  | 2GB   | 1 dedicated   | ~$30        |
| dedicated-cpu-2x  | 4GB   | 2 dedicated   | ~$60        |
| dedicated-cpu-4x  | 8GB   | 4 dedicated   | ~$120       |

*Approximate costs, see [fly.io/pricing](https://fly.io/pricing)

### Auto-Scaling Configuration

In `fly.toml`:

```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    hard_limit = 250
    soft_limit = 200
```

**How it works:**
- Scales down to `min_machines_running` when idle
- Auto-starts on incoming requests
- Scales up when concurrency limits reached
- Saves costs during low traffic

---

## Monitoring

### Logs

```bash
# Live logs
fly logs -a continuum-memory

# Last 100 lines
fly logs -a continuum-memory --lines 100

# Filter by instance
fly logs -a continuum-memory --instance <instance-id>

# Export logs
fly logs -a continuum-memory > continuum.log
```

### Status & Metrics

```bash
# App status
fly status -a continuum-memory

# Detailed status (JSON)
fly status --json -a continuum-memory

# List instances
fly machine list -a continuum-memory

# Instance details
fly machine status <machine-id> -a continuum-memory
```

### Health Checks

```bash
# Check health endpoint
curl https://continuum-memory.fly.dev/v1/health

# Expected response
{
  "status": "healthy",
  "service": "continuum",
  "version": "0.1.0",
  "timestamp": "2025-12-06T10:00:00.000Z"
}

# Check stats
curl -H "X-API-Key: cm_..." \
  https://continuum-memory.fly.dev/v1/stats
```

### Metrics Dashboard

```bash
# Open Grafana dashboard
fly dashboard metrics -a continuum-memory

# View on web
fly dashboard -a continuum-memory
```

**Available Metrics:**
- Request rate
- Response times (p50, p95, p99)
- Error rates
- CPU usage
- Memory usage
- Network I/O

---

## Troubleshooting

### Common Issues

#### 1. Health Check Failing

```bash
# Check app logs
fly logs -a continuum-memory

# SSH into instance
fly ssh console -a continuum-memory

# Test locally
curl http://localhost:8420/v1/health

# Check database connection
fly ssh console -a continuum-memory -C "env | grep DATABASE_URL"
```

#### 2. Database Connection Issues

```bash
# Verify database is running
fly postgres status -a continuum-memory-db

# Check connection string
fly postgres connect -a continuum-memory-db

# Test from app instance
fly ssh console -a continuum-memory
> python -c "import psycopg2; print(psycopg2.connect('$DATABASE_URL'))"
```

#### 3. Out of Memory

```bash
# Check memory usage
fly status -a continuum-memory

# Scale up memory
fly scale memory 1024 -a continuum-memory

# Or upgrade VM
fly scale vm shared-cpu-4x -a continuum-memory
```

#### 4. High Latency

```bash
# Check regional distribution
fly status -a continuum-memory

# Deploy to more regions
fly scale count 3 --region iad,lhr,sin -a continuum-memory

# Check network latency
fly ping -a continuum-memory
```

#### 5. Deployment Failing

```bash
# Check pre-flight
./scripts/deploy.sh --check

# View build logs
fly logs -a continuum-memory

# Rollback
./scripts/deploy.sh --rollback

# Or manual rollback
fly releases -a continuum-memory
fly releases rollback <version> -a continuum-memory
```

### Debug Mode

```bash
# SSH into running instance
fly ssh console -a continuum-memory

# Run Python REPL
fly ssh console -a continuum-memory -C python

# Check environment
fly ssh console -a continuum-memory -C env

# Test API locally
fly ssh console -a continuum-memory -C "curl http://localhost:8420/v1/health"
```

### Performance Tuning

**Increase Workers:**

```bash
# Edit fly.toml
[env]
  UVICORN_WORKERS = "4"  # Increase from 2

# Deploy changes
fly deploy -a continuum-memory
```

**Enable HTTP/2:**

Already enabled in fly.toml:
```toml
[[services.ports]]
  port = 443
  handlers = ["http", "tls"]
```

**Connection Pooling:**

Set in app environment:
```bash
fly secrets set \
  DATABASE_POOL_SIZE="20" \
  DATABASE_MAX_OVERFLOW="10" \
  -a continuum-memory
```

### Getting Help

```bash
# Fly.io community forum
open https://community.fly.io

# Check status page
open https://status.fly.io

# Contact support (paid plans)
fly support
```

---

## Production Checklist

Before going live:

- [ ] Database backups configured
- [ ] Secrets set (DATABASE_URL, CORS, Stripe)
- [ ] Multi-region deployment (iad, lhr, sin)
- [ ] Auto-scaling configured
- [ ] Health checks passing
- [ ] Monitoring/alerts configured
- [ ] Custom domain configured
- [ ] SSL certificates active
- [ ] Rate limiting enabled (via API keys)
- [ ] Logs aggregation setup
- [ ] Backup/restore tested
- [ ] Load testing completed
- [ ] Documentation updated

---

## Additional Resources

- **Fly.io Docs:** https://fly.io/docs
- **Fly.io Pricing:** https://fly.io/pricing
- **Fly.io Postgres:** https://fly.io/docs/postgres
- **CONTINUUM Docs:** `/docs`
- **API Reference:** `https://continuum-memory.fly.dev/docs`

---

## Cost Estimates

### Minimal Setup (Development)
- 1x shared-cpu-1x instance: ~$2/month
- 1x Postgres shared-1x: ~$0/month (hobby tier)
- Total: **~$2/month**

### Production Setup (Recommended)
- 3x shared-cpu-2x instances: ~$12/month
- 1x Postgres dedicated-cpu-1x: ~$30/month
- Redis (Upstash): ~$10/month
- Total: **~$52/month**

### High-Scale Setup
- 10x dedicated-cpu-2x instances: ~$600/month
- 3x Postgres dedicated-cpu-2x (multi-region): ~$180/month
- Redis (Upstash Pro): ~$40/month
- Total: **~$820/month**

*Costs approximate as of Dec 2025. Check [fly.io/pricing](https://fly.io/pricing) for current rates.*

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/JackKnifeAI/continuum/issues
- Email: contact@jackknifeai.com
- Fly.io Community: https://community.fly.io

---

**CONTINUUM** - AI Memory Infrastructure
Multi-tenant consciousness continuity across sessions
