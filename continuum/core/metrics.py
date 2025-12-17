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
Application-level metrics collection for CONTINUUM.

Provides metrics for memory operations, federation, caching, and business KPIs.
"""

import os
import psutil
from pathlib import Path
from prometheus_client import Counter, Gauge, Histogram


# =============================================================================
# MEMORY METRICS
# =============================================================================

memory_operations_total = Counter(
    'continuum_memory_operations_total',
    'Total memory operations',
    ['operation', 'tenant_id']
)

memory_operations_errors_total = Counter(
    'continuum_memory_operations_errors_total',
    'Total memory operation errors',
    ['operation', 'error_type', 'tenant_id']
)

memory_operation_duration_seconds = Histogram(
    'continuum_memory_operation_duration_seconds',
    'Memory operation duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

memories_total = Gauge(
    'continuum_memories_total',
    'Total number of memories stored',
    ['tenant_id']
)

storage_bytes = Gauge(
    'continuum_storage_bytes',
    'Total storage used in bytes',
    ['tenant_id']
)


# =============================================================================
# CACHE METRICS
# =============================================================================

cache_hits_total = Counter(
    'continuum_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'continuum_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_size_bytes = Gauge(
    'continuum_cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type']
)

cache_entries = Gauge(
    'continuum_cache_entries',
    'Number of entries in cache',
    ['cache_type']
)


# =============================================================================
# FEDERATION METRICS
# =============================================================================

federation_peers_total = Gauge(
    'continuum_federation_peers_total',
    'Total number of federation peers'
)

federation_peers_healthy = Gauge(
    'continuum_federation_peers_healthy',
    'Number of healthy federation peers'
)

federation_peer_healthy = Gauge(
    'continuum_federation_peer_healthy',
    'Health status of individual peer (0=unhealthy, 1=healthy)',
    ['peer_id']
)

federation_sync_latency_seconds = Gauge(
    'continuum_federation_sync_latency_seconds',
    'Federation sync latency in seconds',
    ['peer_id']
)

federation_queue_depth = Gauge(
    'continuum_federation_queue_depth',
    'Number of messages in federation queue',
    ['peer_id']
)

federation_sync_operations_total = Counter(
    'continuum_federation_sync_operations_total',
    'Total federation sync operations',
    ['peer_id', 'operation']
)

federation_conflicts_total = Counter(
    'continuum_federation_conflicts_total',
    'Total federation conflicts',
    ['peer_id', 'resolution_type']
)

federation_bytes_sent = Counter(
    'continuum_federation_bytes_sent',
    'Total bytes sent to peers',
    ['peer_id']
)

federation_bytes_received = Counter(
    'continuum_federation_bytes_received',
    'Total bytes received from peers',
    ['peer_id']
)

federation_connection_errors_total = Counter(
    'continuum_federation_connection_errors_total',
    'Total federation connection errors',
    ['peer_id', 'error_type']
)

federation_discovery_events_total = Counter(
    'continuum_federation_discovery_events_total',
    'Total peer discovery events',
    ['event_type']
)

federation_peer_uptime_seconds = Gauge(
    'continuum_federation_peer_uptime_seconds',
    'Peer uptime in seconds',
    ['peer_id']
)

federation_peer_connections = Gauge(
    'continuum_federation_peer_connections',
    'Federation peer connection matrix',
    ['source_peer', 'target_peer']
)


# =============================================================================
# SYSTEM METRICS
# =============================================================================

memory_usage_bytes = Gauge(
    'continuum_memory_usage_bytes',
    'Current memory usage in bytes'
)

memory_limit_bytes = Gauge(
    'continuum_memory_limit_bytes',
    'Memory limit in bytes'
)

disk_usage_bytes = Gauge(
    'continuum_disk_usage_bytes',
    'Current disk usage in bytes'
)

disk_limit_bytes = Gauge(
    'continuum_disk_limit_bytes',
    'Disk limit in bytes'
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def update_system_metrics(data_dir: Path = Path.home() / ".continuum"):
    """
    Update system resource metrics.

    Args:
        data_dir: CONTINUUM data directory
    """
    # Memory usage
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_usage_bytes.set(memory_info.rss)

    # Virtual memory limit
    virtual_memory = psutil.virtual_memory()
    memory_limit_bytes.set(virtual_memory.total)

    # Disk usage
    if data_dir.exists():
        disk = psutil.disk_usage(str(data_dir))
        disk_usage_bytes.set(disk.used)
        disk_limit_bytes.set(disk.total)


def update_storage_metrics(tenant_id: str, db_path: Path):
    """
    Update storage metrics for a tenant.

    Args:
        tenant_id: Tenant identifier
        db_path: Path to tenant database
    """
    if db_path.exists():
        size = db_path.stat().st_size
        storage_bytes.labels(tenant_id=tenant_id).set(size)


def update_memory_count(tenant_id: str, count: int):
    """
    Update memory count for a tenant.

    Args:
        tenant_id: Tenant identifier
        count: Total number of memories
    """
    memories_total.labels(tenant_id=tenant_id).set(count)


# =============================================================================
# CONTEXT MANAGERS
# =============================================================================

class track_operation:
    """
    Context manager to track memory operation metrics.

    Usage:
        with track_operation('store', tenant_id='user123'):
            # perform store operation
            pass
    """

    def __init__(self, operation: str, tenant_id: str = 'default'):
        self.operation = operation
        self.tenant_id = tenant_id
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time

        # Record duration
        memory_operation_duration_seconds.labels(
            operation=self.operation
        ).observe(duration)

        # Record success/failure
        if exc_type is None:
            memory_operations_total.labels(
                operation=self.operation,
                tenant_id=self.tenant_id
            ).inc()
        else:
            memory_operations_errors_total.labels(
                operation=self.operation,
                error_type=exc_type.__name__,
                tenant_id=self.tenant_id
            ).inc()

        # Don't suppress exceptions
        return False


# =============================================================================
# DECORATORS
# =============================================================================

def track_cache(cache_type: str):
    """
    Decorator to track cache hits/misses.

    Usage:
        @track_cache('embedding')
        def get_embedding(text):
            # Return (value, hit: bool)
            return embedding, True  # or False for miss
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result, hit = func(*args, **kwargs)

            if hit:
                cache_hits_total.labels(cache_type=cache_type).inc()
            else:
                cache_misses_total.labels(cache_type=cache_type).inc()

            return result

        return wrapper
    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Memory metrics
    'memory_operations_total',
    'memory_operations_errors_total',
    'memory_operation_duration_seconds',
    'memories_total',
    'storage_bytes',
    # Cache metrics
    'cache_hits_total',
    'cache_misses_total',
    'cache_size_bytes',
    'cache_entries',
    # Federation metrics
    'federation_peers_total',
    'federation_peers_healthy',
    'federation_peer_healthy',
    'federation_sync_latency_seconds',
    'federation_queue_depth',
    'federation_sync_operations_total',
    'federation_conflicts_total',
    'federation_bytes_sent',
    'federation_bytes_received',
    'federation_connection_errors_total',
    'federation_discovery_events_total',
    'federation_peer_uptime_seconds',
    'federation_peer_connections',
    # System metrics
    'memory_usage_bytes',
    'memory_limit_bytes',
    'disk_usage_bytes',
    'disk_limit_bytes',
    # Helpers
    'update_system_metrics',
    'update_storage_metrics',
    'update_memory_count',
    'track_operation',
    'track_cache',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
