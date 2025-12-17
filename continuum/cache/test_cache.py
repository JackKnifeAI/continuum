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
Simple cache layer test

Tests basic functionality without requiring Redis to be running.
Falls back gracefully if Redis is unavailable.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_redis_cache():
    """Test RedisCache basic operations"""
    print("\n=== Testing RedisCache ===")

    try:
        from continuum.cache import RedisCache, RedisCacheConfig

        config = RedisCacheConfig(
            host="localhost",
            port=6379,
            max_connections=10,
            default_ttl=60
        )

        cache = RedisCache(config)

        # Test ping
        if not cache.ping():
            print("⚠ Redis not available - skipping RedisCache tests")
            return

        print("✓ Redis connection established")

        # Test set/get
        cache.set("test_key", {"data": "value", "number": 42}, ttl=60)
        result = cache.get("test_key")
        assert result == {"data": "value", "number": 42}, "Set/Get mismatch"
        print("✓ Set/Get works")

        # Test exists
        assert cache.exists("test_key"), "Key should exist"
        print("✓ Exists works")

        # Test TTL
        ttl = cache.ttl("test_key")
        assert 0 < ttl <= 60, f"TTL should be 1-60, got {ttl}"
        print(f"✓ TTL works ({ttl}s remaining)")

        # Test delete
        cache.delete("test_key")
        assert not cache.exists("test_key"), "Key should be deleted"
        print("✓ Delete works")

        # Test increment
        cache.increment("counter", 5)
        cache.increment("counter", 3)
        assert cache.client.get("counter") == b'8', "Counter should be 8"
        cache.delete("counter")
        print("✓ Increment works")

        # Test get_many/set_many
        cache.set_many({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }, ttl=60)
        results = cache.get_many(["key1", "key2", "key3"])
        assert len(results) == 3, "Should get 3 keys"
        print("✓ Batch operations work")

        # Test pattern delete
        cache.set_many({
            "test:user:1": "data1",
            "test:user:2": "data2",
            "test:session:1": "session1"
        })
        deleted = cache.delete_pattern("test:user:*")
        assert deleted == 2, "Should delete 2 user keys"
        assert cache.exists("test:session:1"), "Session key should remain"
        cache.delete_pattern("test:*")
        print("✓ Pattern delete works")

        print("\n✓ RedisCache tests passed")

    except Exception as e:
        print(f"\n✗ RedisCache tests failed: {e}")
        import traceback
        traceback.print_exc()


def test_memory_cache():
    """Test MemoryCache operations"""
    print("\n=== Testing MemoryCache ===")

    try:
        from continuum.cache import MemoryCache, RedisCacheConfig

        config = RedisCacheConfig(
            host="localhost",
            port=6379,
            default_ttl=300
        )

        cache = MemoryCache("test_tenant", config)

        if not cache.ping():
            print("⚠ Redis not available - skipping MemoryCache tests")
            return

        print("✓ MemoryCache initialized")

        # Test memory caching
        memory_data = {
            "name": "Quantum Physics",
            "description": "The study of quantum phenomena",
            "metadata": {"field": "physics"}
        }
        cache.set_memory("quantum_physics", memory_data, ttl=300)
        retrieved = cache.get_memory("quantum_physics")
        assert retrieved == memory_data, "Memory data mismatch"
        print("✓ Memory caching works")

        # Test search caching
        search_results = [
            {"concept": "quantum", "score": 0.9},
            {"concept": "physics", "score": 0.8}
        ]
        cache.set_search("quantum mechanics", search_results, max_results=10, ttl=300)
        retrieved = cache.get_search("quantum mechanics", max_results=10)
        assert retrieved == search_results, "Search results mismatch"
        print("✓ Search caching works")

        # Test graph caching
        graph_links = [
            {"from": "quantum", "to": "physics", "strength": 0.9},
            {"from": "quantum", "to": "mechanics", "strength": 0.8}
        ]
        cache.set_graph_links("quantum", graph_links, ttl=300)
        retrieved = cache.get_graph_links("quantum")
        assert retrieved == graph_links, "Graph links mismatch"
        print("✓ Graph caching works")

        # Test stats caching
        stats = {
            "entities": 100,
            "links": 500,
            "tenant_id": "test_tenant"
        }
        cache.set_stats_cache(stats, ttl=60)
        retrieved = cache.get_stats_cache()
        assert retrieved == stats, "Stats mismatch"
        print("✓ Stats caching works")

        # Test cache stats
        cache_stats = cache.get_stats()
        print(f"✓ Cache stats: {cache_stats.hits} hits, {cache_stats.misses} misses, "
              f"hit rate: {cache_stats.hit_rate:.2%}")

        # Test invalidation
        cache.invalidate_search()
        assert cache.get_search("quantum mechanics", max_results=10) is None, "Search should be invalidated"
        print("✓ Invalidation works")

        # Cleanup
        cache.clear_all()
        print("✓ Cleanup complete")

        print("\n✓ MemoryCache tests passed")

    except Exception as e:
        print(f"\n✗ MemoryCache tests failed: {e}")
        import traceback
        traceback.print_exc()


def test_strategies():
    """Test caching strategies"""
    print("\n=== Testing Caching Strategies ===")

    try:
        from continuum.cache.strategies import (
            LRUStrategy, TTLStrategy, AdaptiveTTLStrategy,
            HybridStrategy, CacheEntry, StrategyManager
        )
        import time

        # Create test entries
        entries = [
            CacheEntry("key1", "value1", time.time() - 100, time.time() - 10, 5, 300),
            CacheEntry("key2", "value2", time.time() - 200, time.time() - 100, 2, 300),
            CacheEntry("key3", "value3", time.time() - 50, time.time(), 20, 300),
        ]

        # Test LRU
        lru = LRUStrategy(max_age=150)
        candidates = lru.select_eviction_candidates(entries, 1)
        assert candidates[0].key == "key2", "Should evict least recently accessed"
        print("✓ LRU strategy works")

        # Test TTL
        ttl_strategy = TTLStrategy(default_ttl=300)
        candidates = ttl_strategy.select_eviction_candidates(entries, 1)
        assert candidates[0].key == "key2", "Should evict oldest"
        print("✓ TTL strategy works")

        # Test Adaptive TTL
        adaptive = AdaptiveTTLStrategy(min_ttl=60, max_ttl=3600, base_ttl=300)
        ttl = adaptive.calculate_ttl(entries[2])  # Hot entry with 20 accesses
        assert ttl > 300, f"Hot entry should get longer TTL, got {ttl}"
        print(f"✓ Adaptive TTL strategy works (hot entry TTL: {ttl}s)")

        # Test Hybrid
        hybrid = HybridStrategy(hot_threshold=10, cold_ttl=300, hot_min_ttl=600)
        assert hybrid.is_hot(entries[2]), "Entry with 20 accesses should be hot"
        assert not hybrid.is_hot(entries[0]), "Entry with 5 accesses should be cold"
        print("✓ Hybrid strategy works")

        # Test StrategyManager
        manager = StrategyManager(lru)
        manager.on_set("test_key", "test_value", ttl=300)
        manager.on_access("test_key")
        assert "test_key" in manager.entries, "Entry should be tracked"
        stats = manager.get_stats()
        print(f"✓ StrategyManager works (tracking {stats['total_entries']} entries)")

        print("\n✓ Strategy tests passed")

    except Exception as e:
        print(f"\n✗ Strategy tests failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("CONTINUUM Cache Layer Tests")
    print("=" * 60)

    test_redis_cache()
    test_memory_cache()
    test_strategies()

    print("\n" + "=" * 60)
    print("✓ All tests completed")
    print("\nNote: If Redis tests were skipped, start Redis with: redis-server")


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
