#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
CONTINUUM Cache - Redis Caching Layer

High-performance distributed caching for memory operations.

Components:
    - redis_cache: Core Redis client wrapper with connection pooling
    - memory_cache: Memory-specific caching (hot memories, search results)
    - distributed: Redis Cluster support and cache coherence
    - strategies: LRU, TTL, preemptive refresh strategies
    - upstash_adapter: Serverless Redis via Upstash (REST API or traditional)

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

    # Upstash serverless Redis
    from continuum.cache import UpstashCache, RateLimiter

    cache = UpstashCache(mode="rest")  # REST API for serverless
    limiter = RateLimiter(cache)

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
    - Automatic failover to local cache (Upstash)
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

# Import Upstash adapter with graceful fallback
try:
    from .upstash_adapter import (
        UpstashCache,
        UpstashConfig,
        RateLimiter,
        ConnectionMode,
        CacheBackend
    )
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    UpstashCache = None
    UpstashConfig = None
    RateLimiter = None
    ConnectionMode = None
    CacheBackend = None

from .strategies import CacheStrategy, LRUStrategy, TTLStrategy, PreemptiveRefreshStrategy

__all__ = [
    # Traditional Redis
    'RedisCache',
    'RedisCacheConfig',
    'MemoryCache',
    'CacheStats',
    'DistributedCache',
    'ClusterConfig',
    'REDIS_AVAILABLE',
    # Upstash serverless
    'UpstashCache',
    'UpstashConfig',
    'RateLimiter',
    'ConnectionMode',
    'CacheBackend',
    'UPSTASH_AVAILABLE',
    # Strategies
    'CacheStrategy',
    'LRUStrategy',
    'TTLStrategy',
    'PreemptiveRefreshStrategy',
]

__version__ = '1.1.0'

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
