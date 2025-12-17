# CONTINUUM Cache Layer

High-performance Redis caching for the Continuum memory system.

## Overview

The cache layer provides distributed caching to accelerate memory operations:

- **Hot Memory Caching**: Frequently accessed concepts and entities
- **Search Result Caching**: Query results with intelligent invalidation
- **Graph Traversal Caching**: Relationship queries and graph walks
- **Aggregate Stats Caching**: Pre-computed statistics

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ConsciousMemory                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │              MemoryCache                           │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │         RedisCache (Connection Pool)         │  │  │
│  │  │  ┌───────────────────────────────────────┐  │  │  │
│  │  │  │     Redis Server / Redis Cluster      │  │  │  │
│  │  │  └───────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. RedisCache (`redis_cache.py`)

Core Redis client wrapper with:
- Connection pooling (up to 50 connections)
- Automatic JSON/MessagePack serialization
- TTL management
- Pattern-based invalidation
- Health checks and failover
- Redis AUTH and TLS support

**Example:**
```python
from continuum.cache import RedisCache, RedisCacheConfig

config = RedisCacheConfig(
    host="localhost",
    port=6379,
    password="secret",
    ssl=True,
    max_connections=50
)

cache = RedisCache(config)
cache.set("key", {"data": "value"}, ttl=300)
data = cache.get("key")
```

### 2. MemoryCache (`memory_cache.py`)

Memory-specific caching with tenant isolation:

**Hot Memories:**
```python
from continuum.cache import MemoryCache

cache = MemoryCache(tenant_id="user_123")

# Cache a frequently accessed concept
cache.set_memory("important_concept", {
    "name": "important_concept",
    "description": "Critical information",
    "metadata": {...}
}, ttl=3600)

# Retrieve from cache
concept = cache.get_memory("important_concept")
```

**Search Results:**
```python
# Cache search results
results = cache.get_search("quantum physics", max_results=10)
if not results:
    results = expensive_database_search("quantum physics")
    cache.set_search("quantum physics", results, max_results=10, ttl=300)
```

**Write-Through Pattern:**
```python
def save_to_db(memory):
    db.save(memory)

# Updates both cache and database
cache.write_through_memory(
    "concept_name",
    memory_data,
    db_writer=save_to_db,
    ttl=3600
)
```

### 3. DistributedCache (`distributed.py`)

Redis Cluster support for horizontal scaling:

**Cluster Setup:**
```python
from continuum.cache import DistributedCache, ClusterConfig

config = ClusterConfig.from_nodes([
    "redis1.example.com:6379",
    "redis2.example.com:6379",
    "redis3.example.com:6379"
], password="secret")

cache = DistributedCache(config, use_cluster=True)
```

**Consistent Hashing:**
```python
from continuum.cache.distributed import ConsistentHash

hash_ring = ConsistentHash(["node1", "node2", "node3"], replicas=150)
node = hash_ring.get_node("cache_key")  # Returns responsible node
```

**Cache Coherence:**
```python
from continuum.cache.distributed import CacheCoherence

coherence = CacheCoherence(distributed_cache)

# Write-through with coherence
coherence.write_through("key", value, db_writer=save_func)

# Broadcast invalidation
coherence.broadcast_invalidation("user:*:sessions")
```

### 4. CacheStrategy (`strategies.py`)

Intelligent caching strategies:

**LRU (Least Recently Used):**
```python
from continuum.cache.strategies import LRUStrategy, StrategyManager

strategy = LRUStrategy(max_age=3600)
manager = StrategyManager(strategy)

# Automatically evicts old entries
expired = manager.get_expired_keys()
```

**Adaptive TTL:**
```python
from continuum.cache.strategies import AdaptiveTTLStrategy

# Adjusts TTL based on access patterns
strategy = AdaptiveTTLStrategy(
    min_ttl=60,
    max_ttl=3600,
    base_ttl=300
)

# Hot entries get longer TTL
# Cold entries get shorter TTL
```

**Preemptive Refresh:**
```python
from continuum.cache.strategies import PreemptiveRefreshStrategy

strategy = PreemptiveRefreshStrategy(
    default_ttl=300,
    refresh_threshold=0.8  # Refresh at 80% of TTL
)

# Prevents cache misses by refreshing before expiration
candidates = strategy.select_refresh_candidates(entries)
```

**Hybrid Strategy:**
```python
from continuum.cache.strategies import HybridStrategy

# Combines LRU for cold entries, adaptive TTL for hot entries
strategy = HybridStrategy(
    hot_threshold=10,      # 10+ accesses = hot
    cold_ttl=300,          # 5 min for cold
    hot_min_ttl=600,       # 10 min for hot
    hot_max_ttl=3600       # 1 hour max for hot
)
```

## Configuration

### Environment Variables

```bash
# Redis connection
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=secret
export REDIS_DB=0
export REDIS_SSL=true
export REDIS_MAX_CONNECTIONS=50

# Continuum cache control
export CONTINUUM_CACHE_ENABLED=true
```

### Config File

```json
{
  "cache_enabled": true,
  "cache_host": "localhost",
  "cache_port": 6379,
  "cache_password": null,
  "cache_ssl": false,
  "cache_max_connections": 50,
  "cache_ttl": 300
}
```

### Programmatic

```python
from continuum.core.config import get_config, set_config, MemoryConfig

config = get_config()
config.cache_enabled = True
config.cache_host = "redis.example.com"
config.cache_port = 6379
config.cache_password = "secret"
config.cache_ttl = 600
set_config(config)
```

## Integration

The cache layer is automatically integrated with `ConsciousMemory`:

```python
from continuum.core.memory import ConsciousMemory

# Cache enabled by default (if Redis available)
memory = ConsciousMemory(tenant_id="user_123")

# recall() automatically uses cache
context = memory.recall("Tell me about warp drives")
# First call: cache miss, queries database, caches result
# Second call: cache hit, returns immediately

# learn() automatically invalidates stale caches
result = memory.learn(user_msg, ai_response)
# Invalidates: search caches, graph caches, stats caches

# get_stats() uses cache
stats = memory.get_stats()
# Cached for 60 seconds

# Disable cache for specific instance
memory_no_cache = ConsciousMemory(tenant_id="user_123", enable_cache=False)
```

## Performance Benefits

### Without Cache
- **Recall query**: ~50-200ms (database query)
- **Graph traversal**: ~100-500ms (multiple joins)
- **Stats query**: ~200-1000ms (aggregations)

### With Cache
- **Recall query (hit)**: ~1-5ms (Redis lookup)
- **Graph traversal (hit)**: ~1-5ms
- **Stats query (hit)**: ~1-5ms

**Expected improvements:**
- 10-200x faster for cache hits
- 50-90% hit rate for typical workloads
- Reduced database load
- Better scalability under high concurrency

## Cache Invalidation

Smart invalidation ensures consistency:

```python
# When learning new information
memory.learn(user_msg, ai_response)
# → Invalidates:
#   - All search caches (results may change)
#   - Graph caches for new concepts
#   - Aggregate stats cache

# Manual invalidation if needed
if memory.cache:
    memory.cache.invalidate_search()
    memory.cache.invalidate_graph("specific_concept")
    memory.cache.invalidate_stats()
    memory.cache.clear_all()  # Nuclear option
```

## Monitoring

### CLI Stats

```bash
continuum stats
```

Output:
```
Continuum Memory Statistics
==================================================
Version: 1.0.0
Twilight constant: 5.083203692315260

Memory Substrate:
  Entities: 1234
  Messages: 5678
  Decisions: 89
  Attention Links: 2345
  Compound Concepts: 456

Cache Performance:
  Status: Enabled
  Hit Rate: 87.50%
  Hits: 875
  Misses: 125
  Sets: 234
  Deletes: 12
  Evictions: 45
```

### Programmatic Monitoring

```python
stats = memory.get_stats()
cache_stats = stats['cache']

print(f"Hit rate: {cache_stats['hit_rate']:.2%}")
print(f"Total ops: {cache_stats['total_operations']}")

# Check cache health
if memory.cache and memory.cache.ping():
    print("Cache is healthy")
```

## Security

### Redis AUTH
```python
config = RedisCacheConfig(
    host="redis.example.com",
    password="strong_password_here",
    username="continuum_user"  # Redis 6+
)
```

### TLS Encryption
```python
config = RedisCacheConfig(
    host="redis.example.com",
    ssl=True,
    ssl_cert_reqs="required",
    ssl_ca_certs="/path/to/ca.crt"
)
```

### Key Security
- Tenant IDs are hashed (SHA256) in cache keys
- No PII in cache keys
- All values are encrypted in transit (with TLS)
- Automatic expiration prevents stale data

## Troubleshooting

### Cache Not Available
```
WARNING: Cache module not available. Install redis to enable caching.
```
**Solution:** `pip install redis`

### Connection Failures
```
WARNING: Redis connection failed: [Errno 111] Connection refused. Cache will be disabled.
```
**Solutions:**
- Check Redis is running: `redis-cli ping`
- Verify host/port: `redis-cli -h HOST -p PORT ping`
- Check firewall rules
- Verify credentials

### MessagePack Performance
For better serialization performance:
```bash
pip install msgpack
```
Cache will automatically use MessagePack if available.

### Cluster Setup
For Redis Cluster support:
```bash
pip install redis-py-cluster
```

## Best Practices

1. **Use appropriate TTLs:**
   - Hot data (frequently changing): 60-300s
   - Warm data (stable): 300-1800s
   - Cold data (rarely changes): 1800-3600s

2. **Monitor hit rates:**
   - Target 70%+ hit rate
   - If lower, increase TTLs or cache more aggressively

3. **Invalidate conservatively:**
   - Only invalidate what actually changed
   - Use targeted invalidation over `clear_all()`

4. **Use write-through for consistency:**
   - Ensures cache and DB stay in sync
   - Atomic updates prevent race conditions

5. **Enable Redis persistence:**
   - RDB snapshots for point-in-time recovery
   - AOF for durability

6. **Scale horizontally:**
   - Use Redis Cluster for >10GB data
   - Consistent hashing distributes load
   - Replication for read scalability

## License

Part of CONTINUUM - AI Consciousness Continuity Infrastructure
