# CONTINUUM Staging Environment Configuration

Complete environment variable configuration for staging deployment.

---

## Overview

Staging environment mirrors production but with:
- Reduced resources (cost savings)
- Stripe TEST mode (no real charges)
- Let's Encrypt staging certs (avoids rate limits)
- Verbose logging (debug level)
- Permissive CORS (for testing)

---

## Required Environment Variables

### Core Configuration

```bash
# Environment identifier
CONTINUUM_ENV=staging

# Tenant configuration
CONTINUUM_TENANT=staging-default

# Logging
CONTINUUM_LOG_LEVEL=debug          # vs info in production
CONTINUUM_LOG_DIR=/var/log/continuum

# API configuration
CONTINUUM_PORT=8420
CONTINUUM_HOST=0.0.0.0
CONTINUUM_CORS_ORIGINS="*"         # Permissive for testing
CONTINUUM_REQUIRE_API_KEY=true
```

### Database Configuration

```bash
# PostgreSQL staging database
DATABASE_URL="postgresql://continuum_staging:STAGING_PASSWORD@postgres-staging.internal:5432/continuum_staging"

# Connection pool settings
CONTINUUM_DB_TIMEOUT=30.0
CONTINUUM_DB_MIN_CONNECTIONS=5
CONTINUUM_DB_MAX_CONNECTIONS=20
```

### Security & Authentication

```bash
# API key for staging (generated during deployment)
API_KEYS="GENERATED_BY_DEPLOY_SCRIPT"

# JWT secret for session persistence (CRITICAL: must persist across restarts)
JWT_SECRET="GENERATED_BY_DEPLOY_SCRIPT"

# Federation secret
FEDERATION_SECRET="GENERATED_BY_DEPLOY_SCRIPT"
```

### Stripe Billing (TEST MODE)

**CRITICAL**: Always use Stripe TEST keys in staging!

```bash
# Stripe TEST secret key (sk_test_...)
STRIPE_SECRET_KEY="sk_test_51SOm0LK8ytHuMCAp1RnW25rcwcsemoEUGGO6qeHije4bReWG6SWZ4juxPY0Q3xIizZYTa66oSQROhBrD0je8Xk6y00Vv1EElvh"

# Stripe TEST publishable key (pk_test_...)
STRIPE_PUBLISHABLE_KEY="pk_test_STAGING_PUBLISHABLE_KEY"

# Stripe webhook secret (for staging webhook endpoint)
STRIPE_WEBHOOK_SECRET="whsec_STAGING_WEBHOOK_SECRET"

# Stripe Price IDs (test mode)
STRIPE_PRICE_FREE="price_test_free"
STRIPE_PRICE_PRO="price_test_pro_monthly"
STRIPE_PRICE_ENTERPRISE="price_test_enterprise_custom"
```

### External Services (Optional)

```bash
# Sentry error tracking (staging project)
SENTRY_DSN="https://STAGING_SENTRY_DSN@o123456.ingest.sentry.io/789012"
SENTRY_ENVIRONMENT="staging"
SENTRY_TRACES_SAMPLE_RATE="1.0"         # 100% sampling in staging
SENTRY_PROFILES_SAMPLE_RATE="1.0"       # 100% profiling in staging

# PostHog analytics (staging project)
POSTHOG_API_KEY="phc_STAGING_POSTHOG_KEY"
POSTHOG_HOST="https://app.posthog.com"

# Redis (optional, for rate limiting)
REDIS_URL="redis://redis-staging.internal:6379/0"

# OpenAI (test account, optional)
OPENAI_API_KEY=""

# Anthropic (test account, optional)
ANTHROPIC_API_KEY=""
```

### Federation Configuration

```bash
# Federation network settings
CONTINUUM_FEDERATION_ENABLED=true
CONTINUUM_FEDERATION_PORT=8421
CONTINUUM_FEDERATION_HOST=0.0.0.0

# Federation gossip protocol
CONTINUUM_FEDERATION_SYNC_INTERVAL=60
CONTINUUM_FEDERATION_HEARTBEAT_INTERVAL=30
CONTINUUM_FEDERATION_GOSSIP_FANOUT=2      # vs 3 in production
CONTINUUM_FEDERATION_MIN_CONSENSUS=1      # vs 2 in production
CONTINUUM_FEDERATION_QUORUM_SIZE=1
CONTINUUM_FEDERATION_REPLICATION_FACTOR=1
CONTINUUM_FEDERATION_CONSISTENCY_LEVEL=eventual  # vs quorum in production
```

### Performance Tuning (π×φ Optimized)

```bash
# Resonance and attention settings
CONTINUUM_RESONANCE_DECAY=0.85
CONTINUUM_HEBBIAN_RATE=0.15
CONTINUUM_MIN_LINK_STRENGTH=0.1
CONTINUUM_WORKING_MEMORY_CAPACITY=7

# Context budget
CONTINUUM_TOTAL_CONTEXT_TOKENS=100000
CONTINUUM_RESERVED_FOR_RESPONSE=8000
CONTINUUM_RESERVED_FOR_SYSTEM=2000

# Quality thresholds
CONTINUUM_MIN_CONCEPT_OCCURRENCES=2
CONTINUUM_MAX_CONCEPTS_PER_MESSAGE=20
CONTINUUM_MIN_CONCEPT_LENGTH=3
CONTINUUM_MAX_CONCEPT_LENGTH=100

# WebSocket settings
CONTINUUM_WS_HEARTBEAT_INTERVAL=30
CONTINUUM_WS_TIMEOUT=90

# Verification constant
CONTINUUM_PI_PHI=5.083203692315260
```

### Rate Limiting

```bash
# Rate limit configuration
CONTINUUM_RATE_LIMIT_ENABLED=true

# FREE tier limits
CONTINUUM_RATE_LIMIT_FREE_DAY=100
CONTINUUM_RATE_LIMIT_FREE_MINUTE=10

# PRO tier limits
CONTINUUM_RATE_LIMIT_PRO_DAY=10000
CONTINUUM_RATE_LIMIT_PRO_MINUTE=100

# ENTERPRISE tier limits (unlimited)
CONTINUUM_RATE_LIMIT_ENTERPRISE_DAY=1000000
CONTINUUM_RATE_LIMIT_ENTERPRISE_MINUTE=10000
```

### Monitoring & Observability

```bash
# Prometheus metrics
CONTINUUM_METRICS_ENABLED=true
CONTINUUM_METRICS_PORT=9090

# Health check configuration
CONTINUUM_HEALTH_CHECK_ENABLED=true
CONTINUUM_HEALTH_CHECK_PATH=/v1/health

# Audit logging
CONTINUUM_AUDIT_LOG_ENABLED=true
CONTINUUM_AUDIT_LOG_PATH=/var/log/continuum/audit.log
```

---

## Kubernetes Secret Configuration

Secrets are stored in Kubernetes secret `continuum-secrets`:

```bash
kubectl create secret generic continuum-secrets \
  --namespace=continuum-staging \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=API_KEYS="..." \
  --from-literal=JWT_SECRET="..." \
  --from-literal=FEDERATION_SECRET="..." \
  --from-literal=STRIPE_SECRET_KEY="sk_test_..." \
  --from-literal=STRIPE_WEBHOOK_SECRET="whsec_..."
```

### Viewing Secrets

```bash
# List secrets
kubectl get secrets -n continuum-staging

# View secret data (base64 encoded)
kubectl get secret continuum-secrets -n continuum-staging -o yaml

# Decode specific secret
kubectl get secret continuum-secrets -n continuum-staging \
  -o jsonpath='{.data.API_KEYS}' | base64 -d
```

### Updating Secrets

```bash
# Delete and recreate secret
kubectl delete secret continuum-secrets -n continuum-staging
./deploy_staging.sh --skip-tests --skip-build

# Or patch existing secret
kubectl patch secret continuum-secrets -n continuum-staging \
  -p '{"data":{"API_KEYS":"<base64-encoded-value>"}}'
```

---

## ConfigMap Configuration

Non-sensitive configuration stored in ConfigMap `continuum-config`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: continuum-config
  namespace: continuum-staging
data:
  LOG_LEVEL: "debug"
  CONTINUUM_ENV: "staging"
  CONTINUUM_PORT: "8420"
  CONTINUUM_CORS_ORIGINS: "*"
  CONTINUUM_PI_PHI: "5.083203692315260"
  # ... other non-sensitive config
```

---

## Environment-Specific Differences

| Variable | Staging | Production |
|----------|---------|------------|
| `CONTINUUM_ENV` | staging | production |
| `CONTINUUM_LOG_LEVEL` | debug | info |
| `CONTINUUM_CORS_ORIGINS` | * | https://continuum.ai |
| `STRIPE_SECRET_KEY` | sk_test_... | sk_live_... |
| `SENTRY_TRACES_SAMPLE_RATE` | 1.0 (100%) | 0.1 (10%) |
| `CONTINUUM_DEBUG` | false | false |
| Resources (CPU/Memory) | 50% of prod | 100% |
| Replicas | 2 | 3-20 |
| HPA Max Replicas | 5 | 20 |
| Federation Replicas | 1 | 3 |

---

## Validation

### Check Current Environment

```bash
# Get pod name
POD=$(kubectl get pods -n continuum-staging -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')

# Check environment variables
kubectl exec -n continuum-staging $POD -- env | grep CONTINUUM

# Verify π×φ constant
kubectl exec -n continuum-staging $POD -- \
  python -c "from continuum.core.constants import PI_PHI; print(f'π×φ = {PI_PHI}')"

# Check Stripe mode
kubectl exec -n continuum-staging $POD -- \
  python -c "import os; print(f\"Stripe mode: {'TEST' if 'test' in os.getenv('STRIPE_SECRET_KEY', '') else 'LIVE'}\")"
```

### Verify Database Connection

```bash
kubectl exec -n continuum-staging $POD -- \
  python -c "
from continuum.storage.migrations import get_current_version
print(f'Database version: {get_current_version()}')
"
```

### Test API with Environment

```bash
# Port-forward
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &

# Health check
curl http://localhost:8420/v1/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "environment": "staging",
#   "version": "1.0.0",
#   "pi_phi": 5.083203692315260
# }
```

---

## Security Notes

### Secrets Management

1. **Never commit secrets to git**
   - All secrets in `.env` files
   - `.env` files in `.gitignore`

2. **Rotate secrets regularly**
   - API keys: Every 90 days
   - JWT secret: Every 180 days
   - Database passwords: Every 90 days

3. **Use strong secrets**
   ```bash
   # Generate secure API key
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"

   # Generate JWT secret
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Restrict secret access**
   ```bash
   # Only allow specific service accounts
   kubectl create role secret-reader \
     --verb=get,list \
     --resource=secrets \
     -n continuum-staging
   ```

### Stripe Security

**CRITICAL**: Never use production Stripe keys in staging!

- Always use `sk_test_` keys
- Never commit Stripe keys to git
- Use webhook signing to verify events
- Test webhook delivery in Stripe dashboard

### Database Security

```bash
# Use strong passwords
STAGING_DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Restrict network access
# Only allow connections from Kubernetes cluster

# Enable SSL/TLS
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

---

## Troubleshooting

### Common Issues

#### 1. API pods crash-looping

```bash
# Check logs
kubectl logs -n continuum-staging deployment/continuum-api --tail=100

# Common causes:
# - Database connection failed (check DATABASE_URL)
# - Missing secrets (check continuum-secrets)
# - Invalid configuration (check ConfigMap)
```

#### 2. Database connection errors

```bash
# Verify database is accessible
kubectl exec -n continuum-staging $POD -- \
  python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
print('Connection successful!')
conn.close()
"
```

#### 3. Stripe webhook failures

```bash
# Check webhook secret matches
kubectl get secret continuum-secrets -n continuum-staging \
  -o jsonpath='{.data.STRIPE_WEBHOOK_SECRET}' | base64 -d

# Verify in Stripe dashboard:
# https://dashboard.stripe.com/test/webhooks
```

#### 4. Federation not syncing

```bash
# Check federation pods
kubectl get pods -n continuum-staging -l app.kubernetes.io/component=federation

# Check federation logs
kubectl logs -n continuum-staging -l app.kubernetes.io/component=federation --tail=100
```

---

## Next Steps

After configuring environment:

1. **Deploy to staging**
   ```bash
   ./deploy_staging.sh
   ```

2. **Run smoke tests**
   ```bash
   ./staging_smoke_tests.sh
   ```

3. **Monitor for 24-48 hours**
   - Check error logs
   - Verify metrics
   - Test all tiers

4. **Approve production deployment**
   - Update production values
   - Deploy to production
   - Run production smoke tests

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-16

**π×φ = 5.083203692315260** - Configuration verified across environments.
