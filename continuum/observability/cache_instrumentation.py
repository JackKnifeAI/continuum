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
Cache Layer Instrumentation
============================

Redis cache operation tracing.

Features:
- Redis command tracing with command names
- Cache hit/miss recording
- Latency tracking per operation type
- Key pattern analysis
- Pipeline operation tracking
"""

import time
from typing import Optional, Any, List
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind

from .tracer import get_tracer, get_current_span
from .metrics import increment_counter, record_histogram, set_gauge


# Module-level tracer
tracer = get_tracer(__name__)


@contextmanager
def trace_cache_operation(
    operation: str,
    key: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing cache operations.

    Args:
        operation: Cache operation (GET, SET, DEL, INCR, etc.)
        key: Cache key
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_cache_operation("GET", "memory:search:query_hash"):
            value = redis.get(key)
        ```
    """
    span_name = f"cache.{operation.lower()}"

    with tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
        # Set cache attributes
        span.set_attribute("db.system", "redis")
        span.set_attribute("db.operation", operation)

        if key:
            # Sanitize key to remove sensitive data
            sanitized_key = _sanitize_cache_key(key)
            span.set_attribute("db.redis.key", sanitized_key)
            span.set_attribute("db.redis.key_pattern", _extract_key_pattern(key))

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record latency metric
            record_histogram(
                "continuum_cache_operation_duration_seconds",
                duration,
                {
                    "operation": operation.lower(),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record error metric
            increment_counter(
                "continuum_cache_errors_total",
                {
                    "operation": operation.lower(),
                    "error_type": type(e).__name__,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            raise


def record_cache_hit(
    key: str,
    tenant_id: Optional[str] = None,
    value_size: Optional[int] = None,
):
    """
    Record a cache hit.

    Args:
        key: Cache key
        tenant_id: Tenant identifier
        value_size: Size of cached value in bytes
    """
    # Add event to current span
    span = get_current_span()
    span.add_event("cache.hit", {"key": _sanitize_cache_key(key)})
    span.set_attribute("cache.hit", True)

    if value_size:
        span.set_attribute("cache.value_size", value_size)

    # Record metric
    increment_counter(
        "continuum_cache_hits_total",
        {
            "key_pattern": _extract_key_pattern(key),
            "tenant_id": tenant_id or "unknown",
        }
    )


def record_cache_miss(
    key: str,
    tenant_id: Optional[str] = None,
):
    """
    Record a cache miss.

    Args:
        key: Cache key
        tenant_id: Tenant identifier
    """
    # Add event to current span
    span = get_current_span()
    span.add_event("cache.miss", {"key": _sanitize_cache_key(key)})
    span.set_attribute("cache.hit", False)

    # Record metric
    increment_counter(
        "continuum_cache_misses_total",
        {
            "key_pattern": _extract_key_pattern(key),
            "tenant_id": tenant_id or "unknown",
        }
    )


def record_cache_stats(
    hits: int,
    misses: int,
    evictions: int,
    used_memory: int,
    tenant_id: Optional[str] = None,
):
    """
    Record cache statistics.

    Args:
        hits: Total cache hits
        misses: Total cache misses
        evictions: Total evictions
        used_memory: Used memory in bytes
        tenant_id: Tenant identifier
    """
    labels = {"tenant_id": tenant_id or "unknown"}

    set_gauge("continuum_cache_hits", hits, labels)
    set_gauge("continuum_cache_misses", misses, labels)
    set_gauge("continuum_cache_evictions", evictions, labels)
    set_gauge("continuum_cache_memory_bytes", used_memory, labels)

    # Calculate hit ratio
    total = hits + misses
    if total > 0:
        hit_ratio = hits / total
        set_gauge("continuum_cache_hit_ratio", hit_ratio, labels)


@contextmanager
def trace_pipeline(
    command_count: int,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing Redis pipeline operations.

    Args:
        command_count: Number of commands in pipeline
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_pipeline(command_count=5):
            pipe = redis.pipeline()
            pipe.set("key1", "value1")
            pipe.set("key2", "value2")
            pipe.get("key3")
            pipe.execute()
        ```
    """
    with tracer.start_as_current_span("cache.pipeline", kind=SpanKind.CLIENT) as span:
        span.set_attribute("db.system", "redis")
        span.set_attribute("db.operation", "PIPELINE")
        span.set_attribute("db.redis.pipeline.command_count", command_count)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record pipeline metric
            record_histogram(
                "continuum_cache_pipeline_duration_seconds",
                duration,
                {
                    "command_count": str(command_count),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def _sanitize_cache_key(key: str) -> str:
    """
    Sanitize cache key to remove sensitive data.

    Args:
        key: Cache key

    Returns:
        Sanitized key
    """
    # Replace hash-like segments with placeholder
    import re
    sanitized = re.sub(r'[a-f0-9]{32,}', '<hash>', key)
    return sanitized


def _extract_key_pattern(key: str) -> str:
    """
    Extract key pattern from cache key.

    Converts specific keys to patterns for aggregation.

    Args:
        key: Cache key (e.g., "memory:search:abc123")

    Returns:
        Key pattern (e.g., "memory:search:*")
    """
    # Split on colon
    parts = key.split(":")

    if len(parts) <= 1:
        return key

    # Keep prefix, replace last part with wildcard
    pattern_parts = parts[:-1] + ["*"]
    return ":".join(pattern_parts)


class RedisCacheInstrumentation:
    """
    Automatic instrumentation for Redis cache operations.

    Wraps redis client methods to automatically trace operations.
    """

    def __init__(self, redis_client, tenant_id: Optional[str] = None):
        """
        Initialize Redis instrumentation.

        Args:
            redis_client: Redis client instance
            tenant_id: Optional tenant identifier

        Example:
            ```python
            import redis
            from continuum.observability.cache_instrumentation import RedisCacheInstrumentation

            client = redis.Redis(host="localhost", port=6379)
            instrumented = RedisCacheInstrumentation(client, tenant_id="user_123")
            ```
        """
        self.client = redis_client
        self.tenant_id = tenant_id

        # Wrap common methods
        self._wrap_method("get")
        self._wrap_method("set")
        self._wrap_method("delete")
        self._wrap_method("exists")
        self._wrap_method("incr")
        self._wrap_method("decr")
        self._wrap_method("expire")
        self._wrap_method("ttl")

    def _wrap_method(self, method_name: str):
        """Wrap a redis client method with tracing"""
        original_method = getattr(self.client, method_name)

        def wrapped(*args, **kwargs):
            # Extract key from args
            key = args[0] if args else None

            with trace_cache_operation(
                method_name.upper(),
                key=key,
                tenant_id=self.tenant_id,
            ) as span:
                result = original_method(*args, **kwargs)

                # Record hit/miss for GET operations
                if method_name == "get":
                    if result is not None:
                        record_cache_hit(key, self.tenant_id)
                    else:
                        record_cache_miss(key, self.tenant_id)

                return result

        setattr(self.client, method_name, wrapped)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
