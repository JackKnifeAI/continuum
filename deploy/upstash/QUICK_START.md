# Upstash Redis Quick Start Guide

Get CONTINUUM's Upstash caching layer running in 5 minutes.

## 1. Create Upstash Database

Visit [console.upstash.com](https://console.upstash.com)

**Create Database:**
```
Name: continuum-cache-primary
Region: us-east-1 (or nearest)
Type: Regional Database
TLS: ✓ Enabled
Eviction: ✓ Enabled
Eviction Policy: allkeys-lru
```

**Get Credentials:**
- Click database → Copy REST URL and REST Token

## 2. Install Dependencies

```bash
cd /var/home/alexandergcasavant/Projects/continuum
pip install -r deploy/upstash/requirements.txt
```

Or manually:
```bash
pip install upstash-redis redis msgpack
```

## 3. Configure Environment

```bash
export UPSTASH_REDIS_REST_URL="https://your-database.upstash.io"
export UPSTASH_REDIS_REST_TOKEN="your-rest-token"
export CONTINUUM_CACHE_MODE="upstash"
export CONTINUUM_CACHE_FALLBACK="true"
```

## 4. Test Connection

```bash
python3 << 'EOF'
from continuum.cache import UpstashCache

cache = UpstashCache()

if cache.ping():
    print("✓ Connected to Upstash!")
    print(f"  Backend: {cache.current_backend.value}")

    # Test basic operations
    cache.set("test", {"hello": "world"}, ttl=60)
    result = cache.get("test")
    print(f"✓ Test successful: {result}")
    cache.delete("test")
else:
    print("✗ Connection failed")
EOF
```

## 5. Use in Your Code

```python
from continuum.cache import UpstashCache, RateLimiter

# Initialize cache
cache = UpstashCache()

# Cache session data
cache.set(f"session:{user_id}", session_data, ttl=3600)

# Cache query results
cache.set(f"query:{query_hash}", results, ttl=300)

# Rate limiting
limiter = RateLimiter(cache)
if not limiter.check_rate_limit(user_id, 60, 100):
    raise HTTPException(429, "Rate limited")
```

## Common Operations

### Session Caching (1 hour TTL)
```python
session_key = f"session:{user_id}"
cache.set(session_key, session_data, ttl=3600)
session = cache.get(session_key)
```

### Query Results (5 minutes TTL)
```python
query_key = f"query:{hash(query_text)}"
results = cache.get(query_key)
if not results:
    results = expensive_search(query_text)
    cache.set(query_key, results, ttl=300)
```

### Rate Limiting (100 req/min)
```python
limiter = RateLimiter(cache)
allowed = limiter.check_rate_limit(user_id, 60, 100)
```

### Pattern Deletion
```python
# Delete all sessions for a user
cache.delete_pattern(f"session:{user_id}*")
```

### Batch Operations
```python
pipe = cache.pipeline()
for key, value in items.items():
    pipe.set(key, value, ex=300)
pipe.execute()
```

## Cost Estimate

**Free Tier** (0-10k commands/day)
- Development and testing
- Small apps (<1k users)
- **Cost**: $0/month

**10k Users** (~$20/month)
- 5M commands/month
- 10 GB storage
- 50 GB bandwidth

**100k Users** (~$200/month)
- 50M commands/month
- 100 GB storage
- 500 GB bandwidth

## Platform-Specific Setup

### Docker Compose
```yaml
services:
  continuum:
    environment:
      - UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL}
      - UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN}
      - CONTINUUM_CACHE_MODE=upstash
```

### Kubernetes
```bash
kubectl create secret generic upstash-redis \
  --from-literal=rest-url='https://your-database.upstash.io' \
  --from-literal=rest-token='your-token'
```

### Cloudflare Workers
```bash
wrangler secret put UPSTASH_REDIS_REST_TOKEN
```

### Vercel
```bash
vercel env add UPSTASH_REDIS_REST_URL production
vercel env add UPSTASH_REDIS_REST_TOKEN production
```

## Troubleshooting

**Connection Failed?**
```bash
# Check environment variables
echo $UPSTASH_REDIS_REST_URL
echo $UPSTASH_REDIS_REST_TOKEN

# Test with curl
curl -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" \
     "$UPSTASH_REDIS_REST_URL/ping"
```

**Using Local Cache Fallback?**
```python
cache = UpstashCache()
print(f"Backend: {cache.current_backend.value}")
# Should be "upstash" not "local"
```

**High Latency?**
- Use region closest to your application
- Enable connection pooling for containerized apps
- Use MessagePack: `cache = UpstashCache(use_msgpack=True)`

## Full Documentation

- **Complete Guide**: `/deploy/upstash/README.md`
- **Deployment**: `/deploy/upstash/DEPLOYMENT_GUIDE.md`
- **Summary**: `/deploy/upstash/UPSTASH_INTEGRATION_SUMMARY.md`
- **Config**: `/deploy/upstash/config.json`
- **Examples**: `/continuum/cache/upstash_example.py`

## Support

- **Upstash Console**: [console.upstash.com](https://console.upstash.com)
- **Upstash Docs**: [docs.upstash.com](https://docs.upstash.com)
- **Upstash Discord**: [upstash.com/discord](https://upstash.com/discord)

---

**Last Updated**: 2025-12-06
