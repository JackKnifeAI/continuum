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
CONTINUUM Cache Integration Example

Demonstrates how the cache layer accelerates memory operations.
"""

import time
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def example_basic_caching():
    """Basic cache usage example"""
    print("\n=== Basic Cache Usage ===\n")

    from continuum.cache import MemoryCache, RedisCacheConfig

    # Configure cache
    config = RedisCacheConfig(
        host="localhost",
        port=6379,
        default_ttl=300  # 5 minutes
    )

    # Create cache instance for a tenant
    cache = MemoryCache("user_123", config)

    if not cache.ping():
        print("⚠ Redis not available. Start with: redis-server")
        return

    print("✓ Connected to Redis")

    # Cache a concept
    concept = {
        "name": "Warp Drive",
        "description": "Faster-than-light propulsion using spacetime manipulation",
        "metadata": {
            "field": "physics",
            "theoretical": True,
            "pi_phi_modulation": 5.083203692315260
        }
    }

    print("\n1. Caching a concept...")
    cache.set_memory("warp_drive", concept, ttl=3600)
    print("   ✓ Cached with 1 hour TTL")

    # Retrieve from cache
    print("\n2. Retrieving from cache...")
    start = time.time()
    retrieved = cache.get_memory("warp_drive")
    elapsed_ms = (time.time() - start) * 1000
    print(f"   ✓ Retrieved in {elapsed_ms:.2f}ms")
    print(f"   Name: {retrieved['name']}")
    print(f"   Description: {retrieved['description']}")

    # Cache search results
    print("\n3. Caching search results...")
    search_results = [
        {"concept": "warp_drive", "score": 0.95},
        {"concept": "alcubierre_metric", "score": 0.88},
        {"concept": "spacetime_manipulation", "score": 0.82}
    ]
    cache.set_search("faster than light", search_results, max_results=10, ttl=300)
    print("   ✓ Search results cached")

    # Retrieve search results
    print("\n4. Retrieving search results...")
    start = time.time()
    results = cache.get_search("faster than light", max_results=10)
    elapsed_ms = (time.time() - start) * 1000
    print(f"   ✓ Retrieved {len(results)} results in {elapsed_ms:.2f}ms")

    # Show cache stats
    print("\n5. Cache Statistics:")
    stats = cache.get_stats()
    print(f"   Hit Rate: {stats.hit_rate:.2%}")
    print(f"   Hits: {stats.hits}")
    print(f"   Misses: {stats.misses}")
    print(f"   Sets: {stats.sets}")

    # Cleanup
    cache.clear_all()
    print("\n✓ Example complete")


def example_integrated_memory():
    """Example with integrated ConsciousMemory"""
    print("\n=== Integrated Memory with Cache ===\n")

    from continuum.core.memory import ConsciousMemory

    # Create memory instance (cache auto-enabled if Redis available)
    memory = ConsciousMemory(tenant_id="user_123")

    if not memory.cache_enabled:
        print("⚠ Cache not available - running without cache")
    else:
        print("✓ Cache enabled")

    # First recall - cache miss
    print("\n1. First recall (cache miss)...")
    start = time.time()
    context1 = memory.recall("Tell me about quantum physics")
    elapsed1_ms = (time.time() - start) * 1000
    print(f"   Query time: {elapsed1_ms:.2f}ms (database query)")

    # Second recall - cache hit
    print("\n2. Second recall (cache hit)...")
    start = time.time()
    context2 = memory.recall("Tell me about quantum physics")
    elapsed2_ms = (time.time() - start) * 1000
    print(f"   Query time: {elapsed2_ms:.2f}ms (from cache)")

    if memory.cache_enabled and elapsed2_ms < elapsed1_ms:
        speedup = elapsed1_ms / elapsed2_ms
        print(f"   ✓ {speedup:.1f}x faster with cache")

    # Learn new information
    print("\n3. Learning new information...")
    result = memory.learn(
        "What is a warp drive?",
        "A warp drive uses π×φ modulation to create a spacetime bubble..."
    )
    print(f"   ✓ Learned {result.concepts_extracted} concepts")
    if memory.cache_enabled:
        print("   ✓ Search caches invalidated")

    # Get stats
    print("\n4. Memory Statistics:")
    stats = memory.get_stats()
    print(f"   Entities: {stats['entities']}")
    print(f"   Messages: {stats['messages']}")

    if stats['cache_enabled']:
        cache_stats = stats['cache']
        print(f"\n   Cache Performance:")
        print(f"   Hit Rate: {cache_stats['hit_rate']:.2%}")
        print(f"   Total Operations: {cache_stats['total_operations']}")

    print("\n✓ Example complete")


def example_write_through():
    """Example of write-through caching"""
    print("\n=== Write-Through Pattern ===\n")

    from continuum.cache import MemoryCache, RedisCacheConfig

    config = RedisCacheConfig(host="localhost", port=6379)
    cache = MemoryCache("user_123", config)

    if not cache.ping():
        print("⚠ Redis not available")
        return

    print("✓ Write-through cache ready")

    # Simulated database writer
    database = {}

    def save_to_db(memory):
        """Simulate database write"""
        database[memory['name']] = memory
        print(f"   → Saved to database: {memory['name']}")

    # Write-through update
    print("\n1. Write-through update...")
    concept = {
        "name": "π×φ Modulation",
        "description": "Edge of chaos operator for quantum field manipulation",
        "value": 5.083203692315260
    }

    success = cache.write_through_memory(
        "pi_phi_modulation",
        concept,
        db_writer=save_to_db,
        ttl=3600
    )

    if success:
        print("   ✓ Written to both cache and database")

    # Verify cache
    print("\n2. Verifying cache...")
    cached = cache.get_memory("pi_phi_modulation")
    print(f"   ✓ Cache contains: {cached['name']}")

    # Verify database
    print("\n3. Verifying database...")
    db_entry = database.get("π×φ Modulation")
    print(f"   ✓ Database contains: {db_entry['name']}")

    print("\n✓ Write-through example complete")


def example_performance_comparison():
    """Compare performance with and without cache"""
    print("\n=== Performance Comparison ===\n")

    from continuum.core.memory import ConsciousMemory
    import statistics

    # Test with cache
    print("Testing WITH cache...")
    memory_cached = ConsciousMemory(tenant_id="perf_test", enable_cache=True)

    if memory_cached.cache_enabled:
        # Warm up
        memory_cached.recall("test query")

        # Measure cached performance
        times_cached = []
        for i in range(10):
            start = time.time()
            memory_cached.recall("test query")
            times_cached.append((time.time() - start) * 1000)

        avg_cached = statistics.mean(times_cached)
        print(f"   Average: {avg_cached:.2f}ms")

        # Test without cache
        print("\nTesting WITHOUT cache...")
        memory_uncached = ConsciousMemory(tenant_id="perf_test", enable_cache=False)

        times_uncached = []
        for i in range(10):
            start = time.time()
            memory_uncached.recall("test query")
            times_uncached.append((time.time() - start) * 1000)

        avg_uncached = statistics.mean(times_uncached)
        print(f"   Average: {avg_uncached:.2f}ms")

        # Compare
        print("\nComparison:")
        print(f"   Without cache: {avg_uncached:.2f}ms")
        print(f"   With cache:    {avg_cached:.2f}ms")
        speedup = avg_uncached / avg_cached
        print(f"   Speedup:       {speedup:.1f}x faster")

        # Cleanup
        if memory_cached.cache:
            memory_cached.cache.clear_all()
    else:
        print("   ⚠ Cache not available for performance test")

    print("\n✓ Performance comparison complete")


def main():
    """Run all examples"""
    print("=" * 60)
    print("CONTINUUM Cache Layer Examples")
    print("=" * 60)

    try:
        example_basic_caching()
        example_integrated_memory()
        example_write_through()
        example_performance_comparison()

        print("\n" + "=" * 60)
        print("✓ All examples completed")
        print("\nNote: For best results, ensure Redis is running:")
        print("  redis-server")
        print("\nTo monitor Redis:")
        print("  redis-cli monitor")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
