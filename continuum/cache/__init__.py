#!/usr/bin/env python3
"""
CONTINUUM Cache - Redis Caching Layer

High-performance distributed caching for memory operations.

Components:
    - redis_cache: Core Redis client wrapper with connection pooling
    - memory_cache: Memory-specific caching (hot memories, search results)
    - distributed: Redis Cluster support and cache coherence
    - strategies: LRU, TTL, preemptive refresh strategies

Usage:
    from continuum.cache import MemoryCache

    cache = MemoryCache(tenant_id="user_123")

    # Cache search results
    results = cache.get_search("query text")
    if not results:
        results = expensive_search()
        cache.set_search("query text", results, ttl=300)

    # Cache hot memories (frequently accessed)
    memory = cache.get_memory("concept_name")
    if not memory:
        memory = load_from_db()
        cache.set_memory("concept_name", memory)

Security:
    - Redis AUTH enabled
    - TLS connections supported
    - No sensitive data in cache keys (hashed tenant IDs)
    - Automatic key expiration

Performance:
    - Connection pooling (max 50 connections)
    - Automatic serialization (JSON/MessagePack)
    - Write-through caching for updates
    - Cache coherence across distributed nodes
"""

# Import cache components with graceful fallback
try:
    from .redis_cache import RedisCache, RedisCacheConfig
    from .memory_cache import MemoryCache, CacheStats
    from .distributed import DistributedCache, ClusterConfig
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Provide stub classes if Redis not available
    RedisCache = None
    RedisCacheConfig = None
    MemoryCache = None
    CacheStats = None
    DistributedCache = None
    ClusterConfig = None

from .strategies import CacheStrategy, LRUStrategy, TTLStrategy, PreemptiveRefreshStrategy

__all__ = [
    'RedisCache',
    'RedisCacheConfig',
    'MemoryCache',
    'CacheStats',
    'DistributedCache',
    'ClusterConfig',
    'CacheStrategy',
    'LRUStrategy',
    'TTLStrategy',
    'PreemptiveRefreshStrategy',
    'REDIS_AVAILABLE',
]

__version__ = '1.0.0'
