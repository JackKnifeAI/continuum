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
OpenTelemetry Metrics
=====================

Centralized metrics collection for CONTINUUM.

Provides convenience functions for recording:
- Counters (monotonically increasing values)
- Histograms (distributions of values)
- Gauges (point-in-time values)

All metrics are prefixed with "continuum_" for easy identification.
"""

from typing import Dict, Optional
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, UpDownCounter

from .tracer import get_meter


# Global metric instruments (lazily initialized)
_metrics_cache: Dict[str, any] = {}


def _get_or_create_counter(name: str, description: str = "", unit: str = "1") -> Counter:
    """Get or create a counter metric"""
    if name not in _metrics_cache:
        meter = get_meter(__name__)
        _metrics_cache[name] = meter.create_counter(
            name=name,
            description=description,
            unit=unit,
        )
    return _metrics_cache[name]


def _get_or_create_histogram(name: str, description: str = "", unit: str = "1") -> Histogram:
    """Get or create a histogram metric"""
    if name not in _metrics_cache:
        meter = get_meter(__name__)
        _metrics_cache[name] = meter.create_histogram(
            name=name,
            description=description,
            unit=unit,
        )
    return _metrics_cache[name]


def _get_or_create_gauge(name: str, description: str = "", unit: str = "1") -> UpDownCounter:
    """Get or create a gauge metric (using UpDownCounter)"""
    if name not in _metrics_cache:
        meter = get_meter(__name__)
        _metrics_cache[name] = meter.create_up_down_counter(
            name=name,
            description=description,
            unit=unit,
        )
    return _metrics_cache[name]


# =============================================================================
# REQUEST METRICS
# =============================================================================

def record_request(
    method: str,
    route: str,
    status_code: int,
    duration: float,
    tenant_id: str = "unknown",
):
    """
    Record an HTTP request.

    Args:
        method: HTTP method (GET, POST, etc.)
        route: Route path
        status_code: HTTP status code
        duration: Request duration in seconds
        tenant_id: Tenant identifier
    """
    # Request counter
    counter = _get_or_create_counter(
        "continuum_requests_total",
        description="Total number of HTTP requests",
    )
    counter.add(1, {
        "method": method,
        "route": route,
        "status_code": str(status_code),
        "tenant_id": tenant_id,
    })

    # Request duration histogram
    histogram = _get_or_create_histogram(
        "continuum_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s",
    )
    histogram.record(duration, {
        "method": method,
        "route": route,
        "status_code": str(status_code),
        "tenant_id": tenant_id,
    })


# =============================================================================
# MEMORY METRICS
# =============================================================================

def record_memory_operation(
    operation: str,
    duration: float,
    success: bool = True,
    tenant_id: str = "unknown",
):
    """
    Record a memory operation.

    Args:
        operation: Operation type (recall, learn, search)
        duration: Operation duration in seconds
        success: Whether operation succeeded
        tenant_id: Tenant identifier
    """
    # Operation counter
    counter = _get_or_create_counter(
        "continuum_memory_operations_total",
        description="Total number of memory operations",
    )
    counter.add(1, {
        "operation": operation,
        "success": str(success),
        "tenant_id": tenant_id,
    })

    # Operation duration histogram
    histogram = _get_or_create_histogram(
        "continuum_memory_operation_duration_seconds",
        description="Memory operation duration in seconds",
        unit="s",
    )
    histogram.record(duration, {
        "operation": operation,
        "tenant_id": tenant_id,
    })


# =============================================================================
# CACHE METRICS
# =============================================================================

def record_cache_operation(
    operation: str,
    hit: Optional[bool] = None,
    duration: float = 0.0,
    tenant_id: str = "unknown",
):
    """
    Record a cache operation.

    Args:
        operation: Cache operation (get, set, delete)
        hit: Whether cache hit occurred (for GET operations)
        duration: Operation duration in seconds
        tenant_id: Tenant identifier
    """
    # Cache operation counter
    counter = _get_or_create_counter(
        "continuum_cache_operations_total",
        description="Total number of cache operations",
    )
    counter.add(1, {
        "operation": operation,
        "tenant_id": tenant_id,
    })

    # Hit/miss counter
    if hit is not None:
        hit_counter = _get_or_create_counter(
            "continuum_cache_hits_total" if hit else "continuum_cache_misses_total",
            description="Cache hits" if hit else "Cache misses",
        )
        hit_counter.add(1, {"tenant_id": tenant_id})

    # Duration histogram
    if duration > 0:
        histogram = _get_or_create_histogram(
            "continuum_cache_operation_duration_seconds",
            description="Cache operation duration in seconds",
            unit="s",
        )
        histogram.record(duration, {
            "operation": operation,
            "tenant_id": tenant_id,
        })


# =============================================================================
# FEDERATION METRICS
# =============================================================================

def record_federation_operation(
    operation: str,
    duration: float,
    success: bool = True,
    peer_id: str = "unknown",
    tenant_id: str = "unknown",
):
    """
    Record a federation operation.

    Args:
        operation: Federation operation (sync, message)
        duration: Operation duration in seconds
        success: Whether operation succeeded
        peer_id: Peer instance ID
        tenant_id: Tenant identifier
    """
    # Federation operation counter
    counter = _get_or_create_counter(
        "continuum_federation_operations_total",
        description="Total number of federation operations",
    )
    counter.add(1, {
        "operation": operation,
        "success": str(success),
        "peer": peer_id,
        "tenant_id": tenant_id,
    })

    # Duration histogram
    histogram = _get_or_create_histogram(
        "continuum_federation_operation_duration_seconds",
        description="Federation operation duration in seconds",
        unit="s",
    )
    histogram.record(duration, {
        "operation": operation,
        "peer": peer_id,
        "tenant_id": tenant_id,
    })


# =============================================================================
# GENERIC METRICS
# =============================================================================

def increment_counter(
    name: str,
    attributes: Optional[Dict[str, str]] = None,
    value: int = 1,
):
    """
    Increment a counter metric.

    Args:
        name: Metric name
        attributes: Metric attributes/labels
        value: Value to add (default 1)
    """
    counter = _get_or_create_counter(name)
    counter.add(value, attributes or {})


def record_histogram(
    name: str,
    value: float,
    attributes: Optional[Dict[str, str]] = None,
):
    """
    Record a value in a histogram metric.

    Args:
        name: Metric name
        value: Value to record
        attributes: Metric attributes/labels
    """
    histogram = _get_or_create_histogram(name)
    histogram.record(value, attributes or {})


def set_gauge(
    name: str,
    value: int,
    attributes: Optional[Dict[str, str]] = None,
):
    """
    Set a gauge metric value.

    Note: OpenTelemetry doesn't have true gauges, so we use UpDownCounter.
    For actual gauge behavior, you may need to use asynchronous instruments.

    Args:
        name: Metric name
        value: Value to set
        attributes: Metric attributes/labels
    """
    gauge = _get_or_create_gauge(name)

    # For UpDownCounter, we need to track previous value and adjust
    # This is a simplified implementation
    # In production, consider using asynchronous gauge callbacks
    gauge.add(value, attributes or {})


# =============================================================================
# PREDEFINED METRICS
# =============================================================================

# These create the metrics at module load time for better performance

def init_metrics():
    """
    Initialize all predefined metrics.

    Call this during application startup to pre-create metric instruments.
    """
    # Request metrics
    _get_or_create_counter(
        "continuum_requests_total",
        "Total number of HTTP requests",
    )
    _get_or_create_histogram(
        "continuum_request_duration_seconds",
        "HTTP request duration in seconds",
        "s",
    )

    # Memory metrics
    _get_or_create_counter(
        "continuum_memory_operations_total",
        "Total number of memory operations",
    )
    _get_or_create_histogram(
        "continuum_memory_operation_duration_seconds",
        "Memory operation duration in seconds",
        "s",
    )
    _get_or_create_gauge(
        "continuum_memory_entities_total",
        "Total number of entities in memory",
    )
    _get_or_create_gauge(
        "continuum_memory_messages_total",
        "Total number of messages stored",
    )
    _get_or_create_gauge(
        "continuum_memory_decisions_total",
        "Total number of decisions recorded",
    )
    _get_or_create_gauge(
        "continuum_memory_attention_links_total",
        "Total number of attention links",
    )

    # Cache metrics
    _get_or_create_counter(
        "continuum_cache_hits_total",
        "Total number of cache hits",
    )
    _get_or_create_counter(
        "continuum_cache_misses_total",
        "Total number of cache misses",
    )
    _get_or_create_gauge(
        "continuum_cache_hit_ratio",
        "Cache hit ratio (0.0-1.0)",
    )

    # Federation metrics
    _get_or_create_gauge(
        "continuum_federation_active_peers",
        "Number of active federation peers",
    )
    _get_or_create_counter(
        "continuum_federation_sync_success_total",
        "Total number of successful sync operations",
    )
    _get_or_create_counter(
        "continuum_federation_sync_errors_total",
        "Total number of failed sync operations",
    )

    # Database metrics
    _get_or_create_histogram(
        "continuum_db_query_duration_seconds",
        "Database query duration in seconds",
        "s",
    )
    _get_or_create_counter(
        "continuum_db_slow_queries_total",
        "Total number of slow database queries",
    )

    # Error metrics
    _get_or_create_counter(
        "continuum_errors_total",
        "Total number of errors",
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
