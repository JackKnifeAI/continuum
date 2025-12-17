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
Prometheus metrics middleware for FastAPI.

Tracks API requests, latencies, errors, and custom application metrics.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    REGISTRY,
    CONTENT_TYPE_LATEST,
)


# =============================================================================
# METRIC DEFINITIONS
# =============================================================================

# API Metrics
api_requests_total = Counter(
    'continuum_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

api_errors_total = Counter(
    'continuum_api_errors_total',
    'Total API errors (4xx, 5xx)',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

api_request_duration_seconds = Histogram(
    'continuum_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

api_request_size_bytes = Histogram(
    'continuum_api_request_size_bytes',
    'API request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000, 10000000)
)

api_response_size_bytes = Histogram(
    'continuum_api_response_size_bytes',
    'API response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000, 10000000)
)

api_active_connections = Gauge(
    'continuum_api_active_connections',
    'Number of active API connections'
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Prometheus metrics collection.

    Tracks:
    - Request count by method, endpoint, status, tenant
    - Request duration (latency)
    - Request/response sizes
    - Error rates
    - Active connections
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""

        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track active connections
        api_active_connections.inc()

        # Extract metadata
        method = request.method
        endpoint = self._normalize_path(request.url.path)
        tenant_id = request.headers.get('x-tenant-id', 'unknown')

        # Track request size
        request_size = int(request.headers.get('content-length', 0))
        if request_size > 0:
            api_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

        # Time the request
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Track response size
            response_size = int(response.headers.get('content-length', 0))
            if response_size > 0:
                api_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)

            # Record metrics
            status_code = response.status_code

            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                tenant_id=tenant_id
            ).inc()

            api_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Track errors (4xx, 5xx)
            if status_code >= 400:
                api_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    tenant_id=tenant_id
                ).inc()

            return response

        except Exception as e:
            # Track unhandled exceptions
            duration = time.time() - start_time

            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500,
                tenant_id=tenant_id
            ).inc()

            api_errors_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500,
                tenant_id=tenant_id
            ).inc()

            api_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            raise

        finally:
            # Decrement active connections
            api_active_connections.dec()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize URL path to prevent cardinality explosion.

        Replaces UUIDs and numeric IDs with placeholders.

        Examples:
            /api/v1/memories/123 -> /api/v1/memories/{id}
            /api/v1/tenants/abc-123-def -> /api/v1/tenants/{id}
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )

        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)

        # Replace alphanumeric IDs (common pattern)
        path = re.sub(r'/[a-z0-9]{20,}', '/{id}', path, flags=re.IGNORECASE)

        return path


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint handler.

    Returns metrics in Prometheus exposition format.

    Usage:
        @app.get("/metrics")
        async def metrics():
            return metrics_endpoint()
    """
    from fastapi.responses import Response

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

__all__ = [
    'PrometheusMiddleware',
    'metrics_endpoint',
    # Metric objects (for custom instrumentation)
    'api_requests_total',
    'api_errors_total',
    'api_request_duration_seconds',
    'api_request_size_bytes',
    'api_response_size_bytes',
    'api_active_connections',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
