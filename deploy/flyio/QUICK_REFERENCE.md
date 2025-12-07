# CONTINUUM Fly.io - Quick Reference

One-page cheatsheet for common operations.

## Setup (One-Time)

```bash
# 1. Install & login
curl -L https://fly.io/install.sh | sh
fly auth login

# 2. Create app & database
fly apps create continuum-memory
fly postgres create --name continuum-memory-db
fly postgres attach continuum-memory-db -a continuum-memory

# 3. Set secrets
fly secrets set CONTINUUM_CORS_ORIGINS=https://app.example.com -a continuum-memory

# 4. Deploy
cd deploy/flyio
./scripts/deploy.sh
./scripts/migrate.sh
```

## Deployment

```bash
./scripts/deploy.sh                # Deploy production
./scripts/deploy.sh --staging      # Deploy staging
./scripts/deploy.sh --check        # Pre-flight check
./scripts/deploy.sh --rollback     # Rollback
```

## Scaling

```bash
./scripts/scale.sh status          # Show current scale
./scripts/scale.sh up 3            # Scale to 3 instances
./scripts/scale.sh up 3 iad,lhr    # Scale across regions
./scripts/scale.sh down 1          # Scale down
./scripts/scale.sh vm dedicated-cpu-2x  # Upgrade VM
```

## Database

```bash
./scripts/migrate.sh               # Run migrations
./scripts/migrate.sh --status      # Check status
./scripts/migrate.sh --backup      # Create backup
./scripts/migrate.sh --rollback    # Rollback migration
./scripts/migrate.sh --connect     # Connect to DB
```

## Monitoring

```bash
fly status -a continuum-memory     # App status
fly logs -a continuum-memory       # Live logs
fly dashboard -a continuum-memory  # Web dashboard
fly ssh console -a continuum-memory # SSH into instance
```

## Secrets

```bash
fly secrets list -a continuum-memory           # List secrets
fly secrets set KEY=value -a continuum-memory  # Set secret
fly secrets unset KEY -a continuum-memory      # Remove secret
```

## Health & Debug

```bash
# Health check
curl https://continuum-memory.fly.dev/v1/health

# API stats (requires key)
curl -H "X-API-Key: cm_..." https://continuum-memory.fly.dev/v1/stats

# SSH debug
fly ssh console -a continuum-memory
> curl http://localhost:8420/v1/health
> env | grep DATABASE_URL
> python -c "from continuum import __version__; print(__version__)"
```

## Regions

| Code | Location              | Use Case        |
|------|-----------------------|-----------------|
| iad  | Ashburn, VA           | US East         |
| lax  | Los Angeles, CA       | US West         |
| lhr  | London, UK            | Europe          |
| fra  | Frankfurt, Germany    | Europe          |
| sin  | Singapore             | Asia Pacific    |
| syd  | Sydney, Australia     | Oceania         |
| gru  | São Paulo, Brazil     | South America   |

## VM Sizes

| Size             | RAM   | CPUs      | $/mo* |
|------------------|-------|-----------|-------|
| shared-cpu-1x    | 256MB | 1 shared  | $2    |
| shared-cpu-2x    | 512MB | 1 shared  | $4    |
| shared-cpu-4x    | 1GB   | 1 shared  | $8    |
| dedicated-cpu-1x | 2GB   | 1 dedicated | $30   |
| dedicated-cpu-2x | 4GB   | 2 dedicated | $60   |

*Approximate

## Common Issues

**Health check failing:**
```bash
fly logs -a continuum-memory
fly ssh console -a continuum-memory
curl http://localhost:8420/v1/health
```

**Database connection:**
```bash
fly postgres status -a continuum-memory-db
fly postgres connect -a continuum-memory-db
./scripts/migrate.sh --status
```

**Out of memory:**
```bash
fly scale memory 1024 -a continuum-memory
# Or upgrade VM
./scripts/scale.sh vm shared-cpu-4x
```

**Slow performance:**
```bash
# Add regions
./scripts/scale.sh up 3 iad,lhr,sin
# Or upgrade CPU
./scripts/scale.sh vm dedicated-cpu-2x
```

## Files

```
deploy/flyio/
├── fly.toml              # App config
├── Dockerfile            # Container build
├── .dockerignore         # Build exclusions
├── README.md             # Full guide
├── DEPLOYMENT_SUMMARY.md # Overview
├── QUICK_REFERENCE.md    # This file
└── scripts/
    ├── deploy.sh         # Deployment
    ├── migrate.sh        # Database
    └── scale.sh          # Scaling
```

## Environment Variables

```bash
# In fly.toml [env] section
CONTINUUM_ENV=production
CONTINUUM_PORT=8420
LOG_LEVEL=info
UVICORN_WORKERS=2

# Via secrets
DATABASE_URL              # Auto-set by Postgres attach
CONTINUUM_CORS_ORIGINS    # Required
REDIS_URL                 # Optional
STRIPE_SECRET_KEY         # Optional
STRIPE_WEBHOOK_SECRET     # Optional
```

## API Endpoints

```
GET  /                    # Service info
GET  /v1/health          # Health check
POST /v1/recall          # Query memory
POST /v1/learn           # Store learning
POST /v1/turn            # Recall + Learn
GET  /v1/stats           # Statistics
GET  /v1/entities        # List entities
GET  /docs               # API docs
WS   /ws/sync            # WebSocket sync
```

## Support

- Docs: https://fly.io/docs
- Forum: https://community.fly.io
- Status: https://status.fly.io
- Email: contact@jackknifeai.com

---

**Keep this file handy for quick operations!**
