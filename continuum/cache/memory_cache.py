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
Memory-Specific Caching

Caches hot memories, search results, and graph traversals
with write-through strategy for updates.

Cache Types:
    - Hot memories: Frequently accessed concepts/entities
    - Search results: Query -> results mapping
    - Graph traversals: Relationship queries
    - Tenant stats: Aggregate statistics

Features:
    - LRU eviction for hot memories
    - Query result caching with intelligent invalidation
    - Write-through updates (cache + DB)
    - Tenant isolation
"""

import time
import hashlib
from typing import Any, Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .redis_cache import RedisCache, RedisCacheConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics for monitoring"""

    tenant_id: str
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def total_operations(self) -> int:
        """Total cache operations"""
        return self.hits + self.misses + self.sets + self.deletes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'hit_rate': self.hit_rate,
            'total_operations': self.total_operations,
        }


class MemoryCache:
    """
    Memory-specific caching layer.

    Provides high-level caching for memory operations:
    - Hot memories (frequently accessed)
    - Search results
    - Graph traversals
    - Aggregate statistics

    All operations are tenant-isolated.
    """

    def __init__(self, tenant_id: str, redis_config: Optional[RedisCacheConfig] = None):
        """
        Initialize memory cache for a tenant.

        Args:
            tenant_id: Tenant identifier
            redis_config: Optional Redis configuration
        """
        self.tenant_id = tenant_id
        self.redis = RedisCache(redis_config)

        # Key prefixes
        self.prefix = "continuum"
        self.tenant_prefix = self._make_tenant_key()

        # Stats tracking
        self._stats = CacheStats(tenant_id=tenant_id)
        self._load_stats()

    def _make_tenant_key(self, *parts: str) -> str:
        """
        Create tenant-namespaced key.

        Args:
            *parts: Additional key components

        Returns:
            Full cache key
        """
        # Hash tenant ID for security (no PII in cache keys)
        tenant_hash = hashlib.sha256(self.tenant_id.encode()).hexdigest()[:12]
        components = [self.prefix, tenant_hash] + list(parts)
        return ":".join(components)

    def _hash_query(self, query: str) -> str:
        """
        Hash a query string for use as cache key.

        Args:
            query: Query string

        Returns:
            Hashed query (16 chars)
        """
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    # =========================================================================
    # HOT MEMORY CACHING (Frequently accessed concepts/entities)
    # =========================================================================

    def get_memory(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached memory/concept.

        Args:
            concept_name: Name of concept to retrieve

        Returns:
            Cached memory dict or None if not found
        """
        key = self._make_tenant_key("memory", concept_name.lower())
        result = self.redis.get(key)

        if result:
            self._stats.hits += 1
            self._save_stats()
            logger.debug(f"Cache HIT: memory:{concept_name}")
        else:
            self._stats.misses += 1
            self._save_stats()
            logger.debug(f"Cache MISS: memory:{concept_name}")

        return result

    def set_memory(self, concept_name: str, memory: Dict[str, Any], ttl: int = 3600):
        """
        Cache a memory/concept.

        Args:
            concept_name: Name of concept
            memory: Memory dictionary to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        key = self._make_tenant_key("memory", concept_name.lower())
        success = self.redis.set(key, memory, ttl=ttl)

        if success:
            self._stats.sets += 1
            self._save_stats()
            logger.debug(f"Cache SET: memory:{concept_name}")

    def delete_memory(self, concept_name: str):
        """
        Delete cached memory.

        Args:
            concept_name: Name of concept to delete
        """
        key = self._make_tenant_key("memory", concept_name.lower())
        success = self.redis.delete(key)

        if success:
            self._stats.deletes += 1
            self._save_stats()
            logger.debug(f"Cache DELETE: memory:{concept_name}")

    def get_memories_batch(self, concept_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple memories at once.

        Args:
            concept_names: List of concept names

        Returns:
            Dictionary of concept_name -> memory (only includes found items)
        """
        if not concept_names:
            return {}

        keys = [self._make_tenant_key("memory", name.lower()) for name in concept_names]
        results = self.redis.get_many(keys)

        # Map back to original concept names
        concept_map = {self._make_tenant_key("memory", name.lower()): name
                      for name in concept_names}

        output = {}
        for key, value in results.items():
            original_name = concept_map.get(key)
            if original_name:
                output[original_name] = value
                self._stats.hits += 1

        # Count misses
        self._stats.misses += len(concept_names) - len(output)
        self._save_stats()

        return output

    # =========================================================================
    # SEARCH RESULT CACHING
    # =========================================================================

    def get_search(self, query: str, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results.

        Args:
            query: Search query string
            max_results: Maximum results requested

        Returns:
            Cached search results or None if not found
        """
        query_hash = self._hash_query(query)
        key = self._make_tenant_key("search", query_hash, str(max_results))
        result = self.redis.get(key)

        if result:
            self._stats.hits += 1
            self._save_stats()
            logger.debug(f"Cache HIT: search:{query_hash}")
        else:
            self._stats.misses += 1
            self._save_stats()
            logger.debug(f"Cache MISS: search:{query_hash}")

        return result

    def set_search(self, query: str, results: List[Dict[str, Any]],
                   max_results: int = 10, ttl: int = 300):
        """
        Cache search results.

        Args:
            query: Search query string
            results: Search results to cache
            max_results: Maximum results used
            ttl: Time to live in seconds (default: 5 minutes)
        """
        query_hash = self._hash_query(query)
        key = self._make_tenant_key("search", query_hash, str(max_results))
        success = self.redis.set(key, results, ttl=ttl)

        if success:
            self._stats.sets += 1
            self._save_stats()
            logger.debug(f"Cache SET: search:{query_hash}")

    def invalidate_search(self):
        """
        Invalidate all search caches for this tenant.

        Call this when new concepts are added or updated.
        """
        pattern = self._make_tenant_key("search", "*")
        deleted = self.redis.delete_pattern(pattern)

        if deleted > 0:
            self._stats.evictions += deleted
            self._save_stats()
            logger.info(f"Invalidated {deleted} search cache entries")

    # =========================================================================
    # GRAPH TRAVERSAL CACHING
    # =========================================================================

    def get_graph_links(self, concept_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached graph links for a concept.

        Args:
            concept_name: Concept to get links for

        Returns:
            Cached links or None if not found
        """
        key = self._make_tenant_key("graph", concept_name.lower())
        result = self.redis.get(key)

        if result:
            self._stats.hits += 1
            self._save_stats()
            logger.debug(f"Cache HIT: graph:{concept_name}")
        else:
            self._stats.misses += 1
            self._save_stats()
            logger.debug(f"Cache MISS: graph:{concept_name}")

        return result

    def set_graph_links(self, concept_name: str, links: List[Dict[str, Any]], ttl: int = 1800):
        """
        Cache graph links for a concept.

        Args:
            concept_name: Concept name
            links: List of link dictionaries
            ttl: Time to live in seconds (default: 30 minutes)
        """
        key = self._make_tenant_key("graph", concept_name.lower())
        success = self.redis.set(key, links, ttl=ttl)

        if success:
            self._stats.sets += 1
            self._save_stats()
            logger.debug(f"Cache SET: graph:{concept_name}")

    def invalidate_graph(self, concept_name: Optional[str] = None):
        """
        Invalidate graph caches.

        Args:
            concept_name: Optional specific concept to invalidate (or all if None)
        """
        if concept_name:
            key = self._make_tenant_key("graph", concept_name.lower())
            deleted = 1 if self.redis.delete(key) else 0
        else:
            pattern = self._make_tenant_key("graph", "*")
            deleted = self.redis.delete_pattern(pattern)

        if deleted > 0:
            self._stats.evictions += deleted
            self._save_stats()
            logger.info(f"Invalidated {deleted} graph cache entries")

    # =========================================================================
    # AGGREGATE STATS CACHING
    # =========================================================================

    def get_stats_cache(self) -> Optional[Dict[str, Any]]:
        """
        Get cached aggregate statistics.

        Returns:
            Cached stats or None if not found
        """
        key = self._make_tenant_key("stats")
        result = self.redis.get(key)

        if result:
            self._stats.hits += 1
            self._save_stats()
            logger.debug("Cache HIT: stats")
        else:
            self._stats.misses += 1
            self._save_stats()
            logger.debug("Cache MISS: stats")

        return result

    def set_stats_cache(self, stats: Dict[str, Any], ttl: int = 60):
        """
        Cache aggregate statistics.

        Args:
            stats: Statistics dictionary
            ttl: Time to live in seconds (default: 1 minute)
        """
        key = self._make_tenant_key("stats")
        success = self.redis.set(key, stats, ttl=ttl)

        if success:
            self._stats.sets += 1
            self._save_stats()
            logger.debug("Cache SET: stats")

    def invalidate_stats(self):
        """Invalidate cached statistics"""
        key = self._make_tenant_key("stats")
        success = self.redis.delete(key)

        if success:
            self._stats.deletes += 1
            self._save_stats()
            logger.debug("Cache DELETE: stats")

    # =========================================================================
    # WRITE-THROUGH PATTERN
    # =========================================================================

    def write_through_memory(self, concept_name: str, memory: Dict[str, Any],
                            db_writer: callable, ttl: int = 3600) -> bool:
        """
        Write-through pattern: Update both cache and database.

        Args:
            concept_name: Concept name
            memory: Memory to write
            db_writer: Function to write to database (takes memory dict)
            ttl: Cache TTL

        Returns:
            True if successful, False otherwise
        """
        # Write to database first
        try:
            db_writer(memory)
        except Exception as e:
            logger.error(f"Write-through DB error: {e}")
            return False

        # Then update cache
        self.set_memory(concept_name, memory, ttl=ttl)

        # Invalidate related caches
        self.invalidate_search()
        self.invalidate_graph(concept_name)
        self.invalidate_stats()

        return True

    # =========================================================================
    # CACHE STATS MANAGEMENT
    # =========================================================================

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats object
        """
        return self._stats

    def _save_stats(self):
        """Save stats to Redis"""
        key = self._make_tenant_key("cache_stats")
        self.redis.set(key, asdict(self._stats), ttl=86400)  # 24 hours

    def _load_stats(self):
        """Load stats from Redis"""
        key = self._make_tenant_key("cache_stats")
        stats_dict = self.redis.get(key)

        if stats_dict:
            self._stats = CacheStats(**stats_dict)

    def reset_stats(self):
        """Reset cache statistics"""
        self._stats = CacheStats(tenant_id=self.tenant_id)
        self._save_stats()

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    def clear_all(self):
        """
        Clear all caches for this tenant.

        Use with caution!
        """
        pattern = self._make_tenant_key("*")
        deleted = self.redis.delete_pattern(pattern)
        logger.warning(f"Cleared {deleted} cache entries for tenant {self.tenant_id}")
        self.reset_stats()

    def ping(self) -> bool:
        """
        Check if cache is available.

        Returns:
            True if available, False otherwise
        """
        return self.redis.ping()

    def close(self):
        """Close cache connections"""
        self.redis.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
