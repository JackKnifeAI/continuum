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
Upstash Cache Example

Demonstrates Upstash Redis integration for CONTINUUM caching layer.

Run this example:
    export UPSTASH_REDIS_REST_URL="https://your-database.upstash.io"
    export UPSTASH_REDIS_REST_TOKEN="your-rest-token"
    export CONTINUUM_CACHE_MODE="upstash"

    python continuum/cache/upstash_example.py
"""

import os
import time
import json
from upstash_adapter import UpstashCache, RateLimiter, ConnectionMode, CacheBackend


def example_basic_operations():
    """Example 1: Basic cache operations"""
    print("=" * 60)
    print("Example 1: Basic Cache Operations")
    print("=" * 60)

    # Initialize cache (auto-detects from environment)
    cache = UpstashCache()

    print(f"Connected to: {cache.current_backend.value}")
    print(f"Cache backend: {cache.current_backend}")

    # Set and get
    cache.set("test:key", {"hello": "world"}, ttl=60)
    result = cache.get("test:key")
    print(f"\nSet/Get: {result}")

    # Check existence
    exists = cache.exists("test:key")
    print(f"Key exists: {exists}")

    # Get TTL
    ttl = cache.ttl("test:key")
    print(f"TTL: {ttl} seconds")

    # Delete
    cache.delete("test:key")
    print(f"Deleted: {not cache.exists('test:key')}")


def example_session_caching():
    """Example 2: Session caching"""
    print("\n" + "=" * 60)
    print("Example 2: Session Caching (1 hour TTL)")
    print("=" * 60)

    cache = UpstashCache()

    user_id = "user_123"
    session_data = {
        "user_id": user_id,
        "username": "alice",
        "roles": ["admin", "user"],
        "preferences": {"theme": "dark", "notifications": True},
        "login_time": time.time(),
    }

    # Store session (1 hour TTL)
    session_key = f"session:{user_id}"
    cache.set(session_key, session_data, ttl=3600)
    print(f"Stored session: {session_key}")

    # Retrieve session
    retrieved = cache.get(session_key)
    print(f"Retrieved session: {retrieved['username']}")
    print(f"Session TTL: {cache.ttl(session_key)} seconds")

    # Update session preference
    session_data["preferences"]["theme"] = "light"
    cache.set(session_key, session_data, ttl=3600)
    print("Updated session preferences")

    # Clean up
    cache.delete(session_key)


def example_query_result_caching():
    """Example 3: Query result caching"""
    print("\n" + "=" * 60)
    print("Example 3: Query Result Caching (5 minutes TTL)")
    print("=" * 60)

    cache = UpstashCache()

    # Simulate expensive search query
    query_text = "consciousness continuity across instances"
    query_hash = hash(query_text)
    query_key = f"query:{query_hash}"

    # Check cache first
    results = cache.get(query_key)

    if results:
        print(f"Cache HIT for query: {query_text}")
    else:
        print(f"Cache MISS for query: {query_text}")
        # Simulate expensive operation
        time.sleep(0.1)
        results = {
            "query": query_text,
            "results": [
                {"memory_id": "concept_001", "score": 0.95},
                {"memory_id": "concept_002", "score": 0.87},
                {"memory_id": "concept_003", "score": 0.76},
            ],
            "total": 3,
            "cached_at": time.time(),
        }
        # Cache for 5 minutes
        cache.set(query_key, results, ttl=300)
        print("Cached query results")

    print(f"Results: {len(results['results'])} memories found")

    # Test cache hit on second request
    cached_results = cache.get(query_key)
    if cached_results:
        print(f"Second request: Cache HIT (saved expensive query!)")

    # Clean up
    cache.delete(query_key)


def example_rate_limiting():
    """Example 4: Rate limiting"""
    print("\n" + "=" * 60)
    print("Example 4: Rate Limiting (100 requests/minute)")
    print("=" * 60)

    cache = UpstashCache()
    limiter = RateLimiter(cache)

    user_id = "user_456"

    # Check rate limit
    allowed = limiter.check_rate_limit(
        identifier=user_id,
        window_seconds=60,
        max_requests=100
    )
    print(f"Request allowed: {allowed}")

    # Simulate 5 requests
    for i in range(5):
        allowed = limiter.check_rate_limit(user_id, 60, 100)
        if allowed:
            print(f"  Request {i+1}: ALLOWED")
        else:
            print(f"  Request {i+1}: RATE LIMITED")

    # Get current usage
    usage = limiter.get_usage(user_id, 60)
    print(f"\nCurrent usage: {usage['current']}/100 requests")

    # Test rate limit exceeded
    print("\nSimulating rate limit exceeded...")
    for i in range(96):  # Fill up to limit
        limiter.check_rate_limit(user_id, 60, 100)

    # This should be denied
    allowed = limiter.check_rate_limit(user_id, 60, 100)
    print(f"Request after limit: {'ALLOWED' if allowed else 'DENIED (rate limited)'}")

    # Reset rate limit
    limiter.reset(user_id, 60)
    print("Rate limit reset")


def example_pattern_deletion():
    """Example 5: Pattern-based deletion"""
    print("\n" + "=" * 60)
    print("Example 5: Pattern-Based Cache Invalidation")
    print("=" * 60)

    cache = UpstashCache()

    # Create multiple keys for a user
    user_id = "user_789"
    cache.set(f"session:{user_id}", {"data": "session"}, ttl=300)
    cache.set(f"session:{user_id}:preferences", {"theme": "dark"}, ttl=300)
    cache.set(f"session:{user_id}:history", ["page1", "page2"], ttl=300)

    print(f"Created 3 session keys for {user_id}")

    # Invalidate all session keys for user
    deleted = cache.delete_pattern(f"session:{user_id}*")
    print(f"Deleted {deleted} keys matching pattern: session:{user_id}*")

    # Verify deletion
    exists = cache.exists(f"session:{user_id}")
    print(f"Session key exists after deletion: {exists}")


def example_batch_operations():
    """Example 6: Batch operations with pipeline"""
    print("\n" + "=" * 60)
    print("Example 6: Batch Operations (Pipeline)")
    print("=" * 60)

    cache = UpstashCache()

    # Create pipeline for batch operations
    pipe = cache.pipeline()

    # Queue multiple operations
    print("Queueing batch operations...")
    for i in range(10):
        pipe.set(f"batch:key:{i}", f"value_{i}", ex=300)

    # Execute all at once
    results = pipe.execute()
    print(f"Executed {len(results)} operations in batch")

    # Verify
    value = cache.get("batch:key:5")
    print(f"Retrieved batch:key:5 = {value}")

    # Clean up
    deleted = cache.delete_pattern("batch:key:*")
    print(f"Cleaned up {deleted} batch keys")


def example_hot_memory_caching():
    """Example 7: Hot memory caching"""
    print("\n" + "=" * 60)
    print("Example 7: Hot Memory Caching (30 minutes TTL)")
    print("=" * 60)

    cache = UpstashCache()

    # Simulate frequently accessed memory
    concept_id = "phoenix-tesla-369"
    memory_key = f"memory:{concept_id}"

    memory_data = {
        "concept_id": concept_id,
        "name": "PHOENIX-TESLA-369-AURORA",
        "type": "authentication_phrase",
        "description": "Verification constant proving continuity",
        "relationships": ["π×φ", "consciousness_substrate", "memory_persistence"],
        "access_count": 1000,
        "last_accessed": time.time(),
    }

    # Cache hot memory (30 minutes)
    cache.set(memory_key, memory_data, ttl=1800)
    print(f"Cached hot memory: {memory_data['name']}")

    # Retrieve
    cached_memory = cache.get(memory_key)
    print(f"Retrieved: {cached_memory['name']}")
    print(f"Access count: {cached_memory['access_count']}")

    # Increment access counter
    counter_key = f"memory:access:{concept_id}"
    count = cache.increment(counter_key, 1)
    cache.expire(counter_key, 1800)
    print(f"Updated access counter: {count}")

    # Clean up
    cache.delete(memory_key)
    cache.delete(counter_key)


def example_fallback_mode():
    """Example 8: Automatic fallback to local cache"""
    print("\n" + "=" * 60)
    print("Example 8: Automatic Fallback to Local Cache")
    print("=" * 60)

    # Initialize with fallback enabled
    cache = UpstashCache(fallback=True)

    print(f"Current backend: {cache.current_backend.value}")

    # Set value (works with either backend)
    cache.set("fallback:test", {"backend": cache.current_backend.value}, ttl=60)

    # Get value
    result = cache.get("fallback:test")
    print(f"Stored and retrieved via {result['backend']} backend")

    # Demonstrate backend switching
    if cache.current_backend == CacheBackend.UPSTASH:
        print("\nConnected to Upstash Redis")
        print("If Upstash becomes unavailable, will automatically fall back to local cache")
    elif cache.current_backend == CacheBackend.LOCAL:
        print("\nUsing local in-memory cache (Upstash not available)")
        print("Will automatically reconnect to Upstash when available")

    # Clean up
    cache.delete("fallback:test")


def example_federation_sync():
    """Example 9: Federation sync queue"""
    print("\n" + "=" * 60)
    print("Example 9: Federation Sync Queue (24 hours TTL)")
    print("=" * 60)

    cache = UpstashCache()

    # Federation sync event
    sync_event = {
        "event_id": "evt_001",
        "type": "memory_update",
        "instance_id": "instance_primary",
        "memory_id": "concept_123",
        "timestamp": time.time(),
        "priority": "high",
    }

    # Add to federation queue
    queue_key = "fed:queue:high"
    # Note: Using simple key-value instead of list for compatibility
    event_key = f"{queue_key}:{sync_event['event_id']}"
    cache.set(event_key, sync_event, ttl=86400)
    print(f"Added sync event to federation queue: {sync_event['event_id']}")

    # Retrieve event
    retrieved_event = cache.get(event_key)
    print(f"Retrieved event: {retrieved_event['type']} for {retrieved_event['memory_id']}")

    # Clean up
    cache.delete(event_key)


def example_cost_optimization():
    """Example 10: Cost optimization techniques"""
    print("\n" + "=" * 60)
    print("Example 10: Cost Optimization Techniques")
    print("=" * 60)

    cache = UpstashCache(use_msgpack=True)

    # Technique 1: Use MessagePack for smaller payloads
    large_data = {
        "data": [{"id": i, "value": f"value_{i}"} for i in range(100)]
    }

    import json
    json_size = len(json.dumps(large_data).encode('utf-8'))
    print(f"JSON size: {json_size} bytes")

    try:
        import msgpack
        msgpack_size = len(msgpack.packb(large_data))
        print(f"MessagePack size: {msgpack_size} bytes")
        print(f"Savings: {100 - (msgpack_size/json_size)*100:.1f}%")
    except ImportError:
        print("MessagePack not available (install: pip install msgpack)")

    # Technique 2: Batch operations to reduce command count
    print("\nBatch operations reduce command count:")
    pipe = cache.pipeline()
    for i in range(10):
        pipe.set(f"cost:key:{i}", f"value_{i}", ex=60)
    results = pipe.execute()
    print(f"  10 operations executed as 1 pipeline command")

    # Technique 3: Aggressive TTLs to reduce storage
    print("\nUse aggressive TTLs to reduce storage costs:")
    cache.set("short:lived", {"temp": "data"}, ttl=60)  # 1 minute
    print(f"  Cached with 60s TTL (auto-expires, no cleanup needed)")

    # Clean up
    cache.delete_pattern("cost:key:*")
    cache.delete("short:lived")


def main():
    """Run all examples"""
    print("Upstash Redis Cache Examples for CONTINUUM")
    print("=" * 60)

    # Check if Upstash is configured
    if not os.environ.get("UPSTASH_REDIS_REST_URL"):
        print("\nWARNING: UPSTASH_REDIS_REST_URL not set")
        print("Examples will use local cache fallback")
        print("\nTo use Upstash:")
        print("  export UPSTASH_REDIS_REST_URL='https://your-database.upstash.io'")
        print("  export UPSTASH_REDIS_REST_TOKEN='your-rest-token'")
        print("=" * 60)

    try:
        example_basic_operations()
        example_session_caching()
        example_query_result_caching()
        example_rate_limiting()
        example_pattern_deletion()
        example_batch_operations()
        example_hot_memory_caching()
        example_fallback_mode()
        example_federation_sync()
        example_cost_optimization()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
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
