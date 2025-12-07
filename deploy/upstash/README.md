# Upstash Redis Configuration for CONTINUUM

Serverless Redis configuration for CONTINUUM's distributed caching layer.

## Overview

CONTINUUM uses Upstash Redis for managed, serverless caching with:
- **REST API mode** for Cloudflare Workers and serverless deployments
- **Traditional Redis mode** for connection pooling in containerized environments
- **Global databases** for cross-region federation sync
- **Automatic failover** to local cache if Upstash unavailable

## Quick Start

### 1. Create Upstash Databases

Visit [console.upstash.com](https://console.upstash.com) and create:

**Primary Cache** (Regional)
```
Name: continuum-cache-primary
Region: us-east-1 (or your primary region)
Type: Regional
TLS: Enabled
Eviction: Enabled
Eviction Policy: allkeys-lru
```

**Sessions** (Regional)
```
Name: continuum-sessions
Region: us-east-1
Type: Regional
TLS: Enabled
Eviction: Disabled
Eviction Policy: noeviction
```

**Federation Sync** (Global - Optional)
```
Name: continuum-federation-sync
Type: Global Database
Primary Region: us-east-1
Read Regions: eu-west-1, ap-southeast-1
TLS: Enabled
```

### 2. Configure Environment Variables

Copy credentials from Upstash console:

```bash
# Required for REST mode (serverless)
export UPSTASH_REDIS_REST_URL="https://your-database.upstash.io"
export UPSTASH_REDIS_REST_TOKEN="your-rest-token"

# Optional for traditional Redis mode
export UPSTASH_REDIS_URL="redis://default:token@your-database.upstash.io:6379"

# Enable Upstash adapter
export CONTINUUM_CACHE_MODE="upstash"

# Enable local cache fallback
export CONTINUUM_CACHE_FALLBACK="true"
```

### 3. Install Dependencies

```bash
# For REST mode (serverless)
pip install upstash-redis

# For traditional Redis mode
pip install redis hiredis msgpack
```

### 4. Test Connection

```python
from continuum.cache import UpstashCache

# Automatically uses environment variables
cache = UpstashCache()

# Test connection
if cache.ping():
    print("Connected to Upstash!")

# Set and get
cache.set("test:key", {"hello": "world"}, ttl=60)
result = cache.get("test:key")
print(result)  # {'hello': 'world'}
```

## Architecture

### Cache Layers

**Session Caching** (1 hour TTL)
```python
from continuum.cache import UpstashCache

cache = UpstashCache()
session_key = f"session:{user_id}"
cache.set(session_key, session_data, ttl=3600)
```

**Query Result Caching** (5 minutes TTL)
```python
query_key = f"query:{hash(query_text)}"
results = cache.get(query_key)
if not results:
    results = expensive_search(query_text)
    cache.set(query_key, results, ttl=300)
```

**Hot Memories** (30 minutes TTL)
```python
memory_key = f"memory:{concept_id}"
memory = cache.get(memory_key)
if not memory:
    memory = db.load_memory(concept_id)
    cache.set(memory_key, memory, ttl=1800)
```

**Rate Limiting** (1 minute sliding window)
```python
from continuum.cache import RateLimiter

limiter = RateLimiter(cache)
allowed = limiter.check_rate_limit(
    user_id="user_123",
    window_seconds=60,
    max_requests=100
)
```

**Federation Sync Queue** (24 hours TTL)
```python
queue_key = "fed:queue:pending"
cache.lpush(queue_key, sync_event)
cache.expire(queue_key, 86400)
```

**WebSocket Pub/Sub**
```python
# Publish memory update
cache.publish("ws:memory:updates", {
    "type": "memory_updated",
    "memory_id": "concept_123",
    "timestamp": time.time()
})

# Subscribe to updates
pubsub = cache.pubsub()
pubsub.subscribe("ws:memory:updates")
for message in pubsub.listen():
    handle_update(message)
```

### Connection Modes

**REST Mode** (Recommended for Serverless)
```python
# Uses HTTP REST API - no persistent connections
# Perfect for Cloudflare Workers, AWS Lambda, Vercel
cache = UpstashCache(mode="rest")
```

**Redis Mode** (Traditional)
```python
# Uses redis-py with connection pooling
# Better for containerized apps with persistent connections
cache = UpstashCache(mode="redis", pool_size=10)
```

### Automatic Failover

If Upstash is unavailable, CONTINUUM automatically falls back to local in-memory cache:

```python
cache = UpstashCache(fallback=True)

# Transparently uses Upstash if available, local cache if not
cache.set("key", "value")
result = cache.get("key")

# Check current backend
print(cache.current_backend)  # "upstash" or "local"
```

## Rate Limiting

### API Rate Limiting

```python
from continuum.cache import UpstashCache, RateLimiter

cache = UpstashCache()
limiter = RateLimiter(cache)

# Check rate limit (100 requests per minute)
user_id = "user_123"
if not limiter.check_rate_limit(user_id, window_seconds=60, max_requests=100):
    raise HTTPException(429, "Rate limit exceeded")

# Get current usage
usage = limiter.get_usage(user_id, window_seconds=60)
print(f"Requests: {usage['current']}/{usage['limit']}")
```

### Search Query Rate Limiting

```python
# Stricter limits for expensive operations
if not limiter.check_rate_limit(
    f"search:{user_id}",
    window_seconds=60,
    max_requests=20
):
    raise HTTPException(429, "Search rate limit exceeded")
```

### Federation Sync Rate Limiting

```python
# Higher limits for federation traffic
instance_id = "instance_001"
if not limiter.check_rate_limit(
    f"fed:{instance_id}",
    window_seconds=60,
    max_requests=500
):
    logger.warning("Federation sync rate limited")
```

## Key Patterns

Use consistent key prefixes for pattern-based invalidation:

```python
# Session keys
session:{user_id}

# Query cache keys
query:{query_hash}

# Memory cache keys
memory:{concept_id}

# Rate limit keys
ratelimit:api:{user_id}:{window_timestamp}
ratelimit:search:{user_id}:{window_timestamp}

# Federation keys
fed:queue:{priority}
fed:sync:events

# WebSocket channels
ws:memory:updates
ws:session:events
```

### Pattern-Based Invalidation

```python
# Invalidate all sessions for a user
cache.delete_pattern(f"session:{user_id}:*")

# Invalidate all query cache
cache.delete_pattern("query:*")

# Invalidate all memories
cache.delete_pattern("memory:*")
```

## Regional Configuration

### Single Region (Simple)

```python
# All traffic goes to one region
cache = UpstashCache(
    rest_url=os.environ["UPSTASH_REDIS_REST_URL"],
    rest_token=os.environ["UPSTASH_REDIS_REST_TOKEN"]
)
```

### Multi-Region (Global Database)

For low-latency reads across multiple regions:

```python
# Create global database in Upstash console
# Primary: us-east-1
# Read replicas: eu-west-1, ap-southeast-1

# Application automatically uses nearest replica for reads
# Writes go to primary region
cache = UpstashCache(
    rest_url=os.environ["UPSTASH_REDIS_GLOBAL_REST_URL"],
    rest_token=os.environ["UPSTASH_REDIS_GLOBAL_REST_TOKEN"]
)
```

### Region Selection Strategy

| Use Case | Strategy | Database Type |
|----------|----------|---------------|
| Single-region app | Primary only | Regional |
| Multi-region read-heavy | Global database | Global |
| Multi-region write-heavy | Separate regional DBs | Regional per region |
| Federation sync | Global database | Global |

## Cost Estimation

### Free Tier
- **10,000 commands/day**
- **256 MB storage**
- **1000 concurrent connections**
- **Best for**: Development, testing, small apps

### Pay-As-You-Go Pricing

**10,000 Users** (~$20/month)
```
Commands: 5M/month @ $0.20/100k = $10
Storage: 10GB @ $0.25/GB = $2.50
Bandwidth: 50GB @ $0.15/GB = $7.50
Total: $20/month
```

**100,000 Users** (~$200/month)
```
Commands: 50M/month @ $0.20/100k = $100
Storage: 100GB @ $0.25/GB = $25
Bandwidth: 500GB @ $0.15/GB = $75
Total: $200/month
```

**1,000,000 Users** (~$2,000/month)
```
Commands: 500M/month @ $0.20/100k = $1,000
Storage: 1TB @ $0.25/GB = $250
Bandwidth: 5TB @ $0.15/GB = $750
Total: $2,000/month
```

### Pro Fixed Plan ($280/month)

Includes:
- **50M commands/month**
- **100 GB storage**
- **500 GB bandwidth**
- **Best for**: 100k+ users with predictable usage

### Cost Optimization

**Reduce Commands**
```python
# Use pipelines for batch operations
pipe = cache.pipeline()
for key, value in items.items():
    pipe.set(key, value, ttl=300)
pipe.execute()  # 1 command instead of N
```

**Reduce Storage**
```python
# Use MessagePack instead of JSON (30-50% smaller)
cache = UpstashCache(use_msgpack=True)

# Set aggressive TTLs
cache.set("key", value, ttl=300)  # 5 minutes
```

**Reduce Bandwidth**
```python
# Cache only essential data
# Avoid caching large blobs
MAX_CACHE_SIZE = 100 * 1024  # 100 KB
if len(serialized_data) > MAX_CACHE_SIZE:
    logger.warning("Skipping cache - payload too large")
```

## Monitoring

### Upstash Console

Monitor in [console.upstash.com](https://console.upstash.com):
- **Commands per second**
- **Storage usage**
- **Bandwidth usage**
- **Hit rate**
- **Latency (p50, p95, p99)**

### Application Metrics

```python
# Get cache statistics
stats = cache.info()
print(f"Used memory: {stats['used_memory_human']}")
print(f"Connected clients: {stats['connected_clients']}")
print(f"Total commands: {stats['total_commands_processed']}")

# Monitor hit rate
hits = cache.get("stats:cache_hits") or 0
misses = cache.get("stats:cache_misses") or 0
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
print(f"Cache hit rate: {hit_rate:.2%}")
```

### Alerts

Configure alerts in Upstash dashboard:
- **Memory usage > 85%** - Scale up or increase eviction
- **Commands > daily limit** - Risk of overage charges
- **Error rate > 5%** - Connection or configuration issue

## Security

### TLS Encryption
All Upstash databases use TLS by default:
```python
# Automatic TLS for REST mode
cache = UpstashCache(mode="rest")

# TLS for Redis mode
cache = UpstashCache(
    mode="redis",
    url="rediss://..."  # Note the 'rediss://' scheme
)
```

### Token Rotation
```bash
# Rotate REST tokens quarterly
# 1. Generate new token in Upstash console
# 2. Update environment variable
# 3. Restart application
# 4. Revoke old token after 24 hours
```

### IP Allowlist
```
# Configure in Upstash console -> Database -> Security
# Production: Restrict to application server IPs
# Development: Allow all (0.0.0.0/0)
```

### Data Residency
```
# Select region matching compliance requirements
US: us-east-1, us-west-1
EU: eu-west-1, eu-central-1
Asia: ap-southeast-1, ap-northeast-1
```

## Deployment

### Cloudflare Workers

```typescript
// wrangler.toml
[vars]
UPSTASH_REDIS_REST_URL = "https://your-database.upstash.io"

[secrets]
UPSTASH_REDIS_REST_TOKEN = "your-rest-token"
```

```typescript
// worker.ts
import { Redis } from '@upstash/redis/cloudflare'

export default {
  async fetch(request: Request, env: Env) {
    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    })

    await redis.set('key', 'value')
    const value = await redis.get('key')

    return new Response(value)
  }
}
```

### Docker / Kubernetes

```yaml
# k8s secret
apiVersion: v1
kind: Secret
metadata:
  name: upstash-redis
type: Opaque
stringData:
  rest-url: "https://your-database.upstash.io"
  rest-token: "your-rest-token"
```

```yaml
# deployment
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
```

### Vercel / Next.js

```bash
# .env.local
UPSTASH_REDIS_REST_URL=https://your-database.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-rest-token
CONTINUUM_CACHE_MODE=upstash
```

```typescript
// lib/cache.ts
import { UpstashCache } from '@/continuum/cache'

export const cache = new UpstashCache({
  restUrl: process.env.UPSTASH_REDIS_REST_URL!,
  restToken: process.env.UPSTASH_REDIS_REST_TOKEN!,
})
```

## Troubleshooting

### Connection Errors

```
Error: Failed to connect to Upstash Redis
```

**Solutions:**
- Verify `UPSTASH_REDIS_REST_URL` is correct
- Verify `UPSTASH_REDIS_REST_TOKEN` is valid
- Check IP allowlist in Upstash console
- Enable fallback mode for graceful degradation

### Rate Limiting Errors

```
Error: Daily command limit exceeded
```

**Solutions:**
- Reduce cache TTLs (less storage churn)
- Use pipelines for batch operations
- Increase TTLs to reduce refetch rate
- Upgrade to higher tier or Pro plan

### Memory Errors

```
Error: OOM command not allowed when used memory > 'maxmemory'
```

**Solutions:**
- Enable eviction with `allkeys-lru` policy
- Reduce TTLs to expire data faster
- Increase database size
- Delete unused keys

### Latency Issues

```
Warning: High latency detected (>500ms)
```

**Solutions:**
- Use global database for multi-region reads
- Enable connection pooling (Redis mode)
- Reduce payload sizes (use MessagePack)
- Move to region closer to application

## Best Practices

1. **Always Set TTL** - Prevent unbounded growth
2. **Use Consistent Key Prefixes** - Enable pattern-based invalidation
3. **Enable Fallback** - Graceful degradation if Upstash unavailable
4. **Monitor Costs** - Set up alerts for usage spikes
5. **Use Pipelines** - Batch operations to reduce command count
6. **Cache Smartly** - Only cache frequently accessed data
7. **Test Failover** - Verify local cache fallback works
8. **Rotate Tokens** - Regular security hygiene
9. **Choose Right Mode** - REST for serverless, Redis for containers
10. **Regional Strategy** - Single region unless global reads needed

## Support

- **Upstash Docs**: [docs.upstash.com](https://docs.upstash.com)
- **Upstash Discord**: [upstash.com/discord](https://upstash.com/discord)
- **CONTINUUM Issues**: [github.com/continuum/issues](https://github.com/continuum/issues)

## License

CONTINUUM caching layer - see main project LICENSE
