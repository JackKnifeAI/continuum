# Upstash Redis Deployment Guide for CONTINUUM

Complete deployment guide for integrating Upstash serverless Redis with CONTINUUM's caching layer.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Upstash Setup](#upstash-setup)
3. [Environment Configuration](#environment-configuration)
4. [Deployment by Platform](#deployment-by-platform)
5. [Testing](#testing)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Cost Management](#cost-management)

## Prerequisites

### Required Accounts
- **Upstash account**: [Sign up](https://console.upstash.com)
- **GitHub account**: For CI/CD secrets

### Required Tools
```bash
# Python 3.9+
python --version

# pip for package installation
pip --version

# (Optional) Upstash CLI
npm install -g @upstash/cli
```

## Upstash Setup

### Step 1: Create Primary Cache Database

1. Visit [console.upstash.com](https://console.upstash.com)
2. Click "Create Database"
3. Configure:
   ```
   Name: continuum-cache-primary
   Type: Regional Database
   Region: us-east-1 (or your preferred region)
   TLS: ✓ Enabled
   Eviction: ✓ Enabled
   Eviction Policy: allkeys-lru
   ```
4. Click "Create"

### Step 2: Create Sessions Database

1. Click "Create Database"
2. Configure:
   ```
   Name: continuum-sessions
   Type: Regional Database
   Region: us-east-1 (same as primary)
   TLS: ✓ Enabled
   Eviction: ✗ Disabled (persistence required)
   Eviction Policy: noeviction
   ```
3. Click "Create"

### Step 3: (Optional) Create Global Federation Database

For multi-region deployments:

1. Click "Create Database"
2. Configure:
   ```
   Name: continuum-federation-sync
   Type: Global Database
   Primary Region: us-east-1
   Read Regions: eu-west-1, ap-southeast-1
   TLS: ✓ Enabled
   Eviction: ✗ Disabled
   ```
3. Click "Create"

### Step 4: Get Connection Credentials

For each database:

1. Click on database name
2. Copy credentials:
   - **REST API** tab: `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
   - **Redis** tab: `UPSTASH_REDIS_URL`

## Environment Configuration

### Local Development

Create `.env` file:
```bash
# Upstash REST API (for serverless mode)
UPSTASH_REDIS_REST_URL=https://your-database.upstash.io
UPSTASH_REDIS_REST_TOKEN=AYg...your-token...Z6Q==

# Upstash Redis URL (for traditional mode)
UPSTASH_REDIS_URL=redis://default:token@your-database.upstash.io:6379

# Cache configuration
CONTINUUM_CACHE_MODE=upstash
CONTINUUM_CACHE_FALLBACK=true
UPSTASH_ENABLE_TELEMETRY=false
```

Load environment:
```bash
source .env
# or
export $(cat .env | xargs)
```

### Production

**Never commit credentials to git!**

Use platform-specific secret management:

- **Kubernetes**: Sealed Secrets / External Secrets
- **Cloudflare Workers**: Wrangler secrets
- **Vercel**: Environment Variables
- **AWS**: Secrets Manager / Parameter Store
- **Docker**: Docker Secrets

## Deployment by Platform

### Docker / Docker Compose

**docker-compose.yml**
```yaml
version: '3.8'

services:
  continuum:
    image: continuum:latest
    environment:
      - UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL}
      - UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN}
      - CONTINUUM_CACHE_MODE=upstash
      - CONTINUUM_CACHE_FALLBACK=true
    env_file:
      - .env.production
    ports:
      - "8000:8000"
```

Deploy:
```bash
docker-compose up -d
```

### Kubernetes

**1. Create Secret**

```bash
kubectl create secret generic upstash-redis \
  --from-literal=rest-url='https://your-database.upstash.io' \
  --from-literal=rest-token='your-rest-token' \
  --namespace continuum
```

**2. Update Deployment**

```yaml
# deploy/kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: continuum
spec:
  template:
    spec:
      containers:
      - name: continuum
        env:
        - name: UPSTASH_REDIS_REST_URL
          valueFrom:
            secretKeyRef:
              name: upstash-redis
              key: rest-url
        - name: UPSTASH_REDIS_REST_TOKEN
          valueFrom:
            secretKeyRef:
              name: upstash-redis
              key: rest-token
        - name: CONTINUUM_CACHE_MODE
          value: "upstash"
        - name: CONTINUUM_CACHE_FALLBACK
          value: "true"
```

**3. Deploy**

```bash
kubectl apply -f deploy/kubernetes/
```

### Cloudflare Workers

**1. Configure Wrangler**

```toml
# wrangler.toml
name = "continuum-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[vars]
UPSTASH_REDIS_REST_URL = "https://your-database.upstash.io"
```

**2. Add Secret**

```bash
wrangler secret put UPSTASH_REDIS_REST_TOKEN
# Paste your token when prompted
```

**3. Deploy**

```bash
wrangler deploy
```

**4. Worker Code**

```typescript
import { Redis } from '@upstash/redis/cloudflare'

export default {
  async fetch(request: Request, env: Env) {
    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    })

    // Use cache
    const cached = await redis.get('key')
    if (cached) {
      return new Response(JSON.stringify(cached))
    }

    // Set cache
    await redis.set('key', { data: 'value' }, { ex: 300 })

    return new Response('OK')
  }
}
```

### Vercel / Next.js

**1. Add Environment Variables**

```bash
vercel env add UPSTASH_REDIS_REST_URL production
vercel env add UPSTASH_REDIS_REST_TOKEN production
```

Or via Vercel dashboard:
- Settings → Environment Variables
- Add `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`

**2. Use in API Routes**

```typescript
// app/api/cache/route.ts
import { UpstashCache } from '@/continuum/cache'

export async function GET() {
  const cache = new UpstashCache({
    restUrl: process.env.UPSTASH_REDIS_REST_URL!,
    restToken: process.env.UPSTASH_REDIS_REST_TOKEN!,
  })

  const data = await cache.get('key')
  return Response.json(data)
}
```

**3. Deploy**

```bash
vercel deploy --prod
```

### AWS Lambda

**1. Create Secrets in Secrets Manager**

```bash
aws secretsmanager create-secret \
  --name continuum/upstash-redis \
  --secret-string '{
    "rest_url":"https://your-database.upstash.io",
    "rest_token":"your-rest-token"
  }'
```

**2. Update Lambda Function**

```python
# lambda_function.py
import json
import boto3
from continuum.cache import UpstashCache

# Get secrets
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='continuum/upstash-redis')
creds = json.loads(secret['SecretString'])

# Initialize cache
cache = UpstashCache(
    rest_url=creds['rest_url'],
    rest_token=creds['rest_token'],
    mode='rest'
)

def lambda_handler(event, context):
    # Use cache
    cached = cache.get('key')
    if cached:
        return {'statusCode': 200, 'body': json.dumps(cached)}

    # Set cache
    cache.set('key', {'data': 'value'}, ttl=300)
    return {'statusCode': 200, 'body': 'OK'}
```

**3. Update IAM Role**

Add permission to read secrets:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:*:*:secret:continuum/upstash-redis-*"
    }
  ]
}
```

**4. Deploy**

```bash
zip -r function.zip lambda_function.py continuum/
aws lambda update-function-code \
  --function-name continuum \
  --zip-file fileb://function.zip
```

## Testing

### 1. Test Connection

```bash
python3 << 'EOF'
from continuum.cache import UpstashCache

cache = UpstashCache()
if cache.ping():
    print("✓ Connected to Upstash Redis")
    print(f"  Backend: {cache.current_backend.value}")
else:
    print("✗ Connection failed")
EOF
```

### 2. Test Basic Operations

```bash
python3 << 'EOF'
from continuum.cache import UpstashCache

cache = UpstashCache()

# Set
cache.set("test:key", {"hello": "world"}, ttl=60)
print("✓ SET test:key")

# Get
result = cache.get("test:key")
print(f"✓ GET test:key = {result}")

# Delete
cache.delete("test:key")
print("✓ DELETE test:key")
EOF
```

### 3. Run Full Example Suite

```bash
cd /var/home/alexandergcasavant/Projects/continuum
python continuum/cache/upstash_example.py
```

### 4. Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run cache tests
pytest continuum/cache/test_cache.py -v
```

## Monitoring

### Upstash Console

Monitor in [console.upstash.com](https://console.upstash.com):

**Key Metrics:**
- Commands per second
- Storage usage (MB)
- Bandwidth usage (MB)
- Hit rate (%)
- Latency (p50, p95, p99)

**Set Up Alerts:**
1. Click database → Alerts
2. Configure:
   - Memory usage > 85%
   - Daily commands > 80% of limit
   - Error rate > 5%

### Application Monitoring

Add to your application:

```python
from continuum.cache import UpstashCache

cache = UpstashCache()

# Log cache statistics
stats = cache.info()
print(f"Cache keys: {stats.get('keys', 0)}")
print(f"Memory used: {stats.get('used_memory_human', 'unknown')}")

# Monitor hit rate
hits = cache.get("stats:cache_hits") or 0
misses = cache.get("stats:cache_misses") or 0
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
print(f"Cache hit rate: {hit_rate:.2%}")
```

### Prometheus / Grafana

Export metrics for Prometheus:

```python
from prometheus_client import Counter, Gauge

cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')
cache_latency = Gauge('cache_latency_seconds', 'Cache operation latency')

# In your cache wrapper
def get_with_metrics(key):
    start = time.time()
    result = cache.get(key)
    latency = time.time() - start

    cache_latency.set(latency)
    if result:
        cache_hits.inc()
    else:
        cache_misses.inc()

    return result
```

## Troubleshooting

### Connection Errors

**Error**: `Failed to connect to Upstash Redis`

**Solutions**:
1. Verify environment variables are set:
   ```bash
   echo $UPSTASH_REDIS_REST_URL
   echo $UPSTASH_REDIS_REST_TOKEN
   ```

2. Check IP allowlist in Upstash console:
   - Database → Security → IP Allowlist
   - Add your application's IP or use `0.0.0.0/0` for development

3. Verify TLS is enabled:
   - URLs should start with `https://` (REST) or `rediss://` (Redis)

4. Test with curl:
   ```bash
   curl -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" \
        "$UPSTASH_REDIS_REST_URL/ping"
   ```

### Rate Limiting Errors

**Error**: `Daily command limit exceeded`

**Solutions**:
1. Check current usage in Upstash console
2. Reduce cache churn by increasing TTLs
3. Use pipelines for batch operations
4. Upgrade to higher tier if needed

### Memory Errors

**Error**: `OOM command not allowed`

**Solutions**:
1. Enable eviction policy:
   - Database → Configuration → Eviction Policy
   - Set to `allkeys-lru` for cache, `noeviction` for sessions

2. Reduce TTLs to expire data faster

3. Delete unused keys:
   ```python
   cache.delete_pattern("old:pattern:*")
   ```

4. Increase database size in Upstash console

### Latency Issues

**High latency** (>500ms):

**Solutions**:
1. Use global database for multi-region reads
2. Move to region closer to application
3. Reduce payload sizes (use MessagePack)
4. Enable connection pooling (Redis mode)

### Fallback Mode Stuck

**Issue**: Cache stuck in local mode

**Solutions**:
1. Check health check interval (default 30s)
2. Verify Upstash is reachable
3. Check logs for connection errors
4. Manually test connection:
   ```python
   cache = UpstashCache()
   print(f"Backend: {cache.current_backend.value}")
   cache._connect()  # Force reconnection attempt
   ```

## Cost Management

### Monitor Costs

**Upstash Console:**
- Billing → Usage
- View current period usage and projected costs

**Estimated Monthly Costs:**

| Users | Commands/mo | Storage | Bandwidth | Cost |
|-------|-------------|---------|-----------|------|
| 1k    | 500k        | 1 GB    | 5 GB      | ~$2  |
| 10k   | 5M          | 10 GB   | 50 GB     | ~$20 |
| 100k  | 50M         | 100 GB  | 500 GB    | ~$200|
| 1M    | 500M        | 1 TB    | 5 TB      | ~$2k |

### Optimization Strategies

**1. Reduce Command Count**
```python
# Bad: 10 commands
for key, value in items.items():
    cache.set(key, value)

# Good: 1 command (pipeline)
pipe = cache.pipeline()
for key, value in items.items():
    pipe.set(key, value, ex=300)
pipe.execute()
```

**2. Reduce Storage**
```python
# Use MessagePack (30-50% smaller)
cache = UpstashCache(use_msgpack=True)

# Set aggressive TTLs
cache.set("key", value, ttl=300)  # 5 minutes
```

**3. Reduce Bandwidth**
```python
# Don't cache large blobs
MAX_CACHE_SIZE = 100 * 1024  # 100 KB
if len(data) > MAX_CACHE_SIZE:
    # Store in database instead
    pass
```

**4. Use Free Tier Efficiently**
- 10k commands/day = ~300k/month (free)
- Cache only frequently accessed data
- Use longer TTLs to reduce churn

### Cost Alerts

Set up billing alerts in Upstash console:
1. Billing → Alerts
2. Set threshold (e.g., $50/month)
3. Add email for notifications

## Migration from Traditional Redis

### Step 1: Parallel Run

Run both Redis and Upstash simultaneously:

```python
from continuum.cache import RedisCache, UpstashCache

# Traditional Redis
redis_cache = RedisCache()

# Upstash Redis
upstash_cache = UpstashCache()

# Write to both
redis_cache.set("key", value, ttl=300)
upstash_cache.set("key", value, ttl=300)

# Read from Upstash (with Redis fallback)
result = upstash_cache.get("key") or redis_cache.get("key")
```

### Step 2: Monitor Performance

Compare metrics:
- Latency
- Hit rate
- Error rate

### Step 3: Gradual Rollout

Use feature flags:
```python
import os

USE_UPSTASH = os.environ.get("USE_UPSTASH", "false") == "true"

if USE_UPSTASH:
    cache = UpstashCache()
else:
    cache = RedisCache()
```

Increase rollout percentage:
```python
import random

UPSTASH_ROLLOUT_PERCENT = int(os.environ.get("UPSTASH_ROLLOUT", "0"))

if random.randint(0, 100) < UPSTASH_ROLLOUT_PERCENT:
    cache = UpstashCache()
else:
    cache = RedisCache()
```

### Step 4: Full Migration

Once stable:
1. Update environment: `CONTINUUM_CACHE_MODE=upstash`
2. Deploy to all instances
3. Decommission traditional Redis
4. Remove old code paths

## Support

- **Upstash Docs**: [docs.upstash.com](https://docs.upstash.com)
- **Upstash Discord**: [upstash.com/discord](https://upstash.com/discord)
- **CONTINUUM Issues**: GitHub Issues
- **Email**: support@upstash.com

## Appendix: Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UPSTASH_REDIS_REST_URL` | Yes (REST) | - | Upstash REST API URL |
| `UPSTASH_REDIS_REST_TOKEN` | Yes (REST) | - | Upstash REST API token |
| `UPSTASH_REDIS_URL` | Yes (Redis) | - | Traditional Redis URL |
| `CONTINUUM_CACHE_MODE` | No | auto | Connection mode (rest/redis/auto) |
| `CONTINUUM_CACHE_FALLBACK` | No | true | Enable local cache fallback |
| `UPSTASH_POOL_SIZE` | No | 10 | Connection pool size (Redis mode) |
| `UPSTASH_ENABLE_TELEMETRY` | No | false | Enable Upstash telemetry |

### Cache Key Patterns

| Pattern | Description | TTL |
|---------|-------------|-----|
| `session:{user_id}` | User sessions | 1 hour |
| `query:{hash}` | Query results | 5 minutes |
| `memory:{concept_id}` | Hot memories | 30 minutes |
| `ratelimit:api:{user_id}:{window}` | API rate limits | 1 minute |
| `ratelimit:search:{user_id}:{window}` | Search rate limits | 1 minute |
| `fed:queue:{priority}` | Federation queue | 24 hours |
| `ws:{channel}` | WebSocket pub/sub | 5 minutes |

### Eviction Policies

| Policy | Use Case | Eviction Behavior |
|--------|----------|-------------------|
| `allkeys-lru` | Cache (primary) | Evict least recently used keys |
| `noeviction` | Sessions | Return error when memory full |
| `volatile-lru` | Mixed | Evict LRU keys with TTL set |
| `allkeys-lfu` | Access patterns | Evict least frequently used keys |

---

**Last Updated**: 2025-12-06
**Version**: 1.0.0
