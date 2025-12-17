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
CONTINUUM Observability Module
===============================

OpenTelemetry-based distributed tracing, metrics, and logging for CONTINUUM.

This module provides comprehensive observability for the distributed AI memory system,
enabling end-to-end request tracing, performance monitoring, and debugging across:
- API layer (FastAPI)
- Database layer (SQLAlchemy/SQLite/PostgreSQL)
- Cache layer (Redis)
- Federation layer (peer-to-peer sync)
- Memory operations (recall, learn, graph traversal)

Quick Start:
-----------
```python
from continuum.observability import init_telemetry, get_tracer

# Initialize telemetry on application startup
init_telemetry(
    service_name="continuum-api",
    exporter_type="jaeger",
    sampling_rate=0.1
)

# Get tracer for manual instrumentation
tracer = get_tracer(__name__)

# Create custom spans
with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("user_id", "12345")
    # ... your code ...
```

Environment Variables:
---------------------
- OTEL_EXPORTER_TYPE: Exporter type (jaeger|zipkin|otlp|datadog|console) [default: console]
- OTEL_SERVICE_NAME: Service name for traces [default: continuum]
- OTEL_SAMPLING_RATE: Sampling rate 0.0-1.0 [default: 1.0]
- OTEL_ENDPOINT: Exporter endpoint URL
- OTEL_PROPAGATORS: Comma-separated propagators [default: tracecontext,baggage]
- OTEL_RESOURCE_ATTRIBUTES: Key-value pairs for resource attributes

Auto-Instrumentation:
--------------------
The following libraries are automatically instrumented when telemetry is initialized:
- FastAPI (requests, responses, errors)
- SQLAlchemy (queries, transactions)
- Redis (commands, pipelines)
- httpx (HTTP client calls)

Exporters:
---------
- Jaeger: Full-featured distributed tracing UI
- Zipkin: Lightweight distributed tracing
- OTLP: OpenTelemetry Protocol (Grafana Tempo, etc.)
- Datadog: Datadog APM integration
- Console: Development console output
"""

from .tracer import (
    init_telemetry,
    shutdown_telemetry,
    get_tracer,
    get_meter,
    get_current_span,
    trace_function,
)

from .config import OTelConfig

from .metrics import (
    record_request,
    record_memory_operation,
    record_cache_operation,
    record_federation_operation,
    increment_counter,
    record_histogram,
    set_gauge,
)

from .context import (
    extract_trace_context,
    inject_trace_context,
    get_trace_id,
    get_span_id,
    set_baggage,
    get_baggage,
)

from .logging_integration import (
    setup_logging,
    get_logger,
)

__all__ = [
    # Initialization
    "init_telemetry",
    "shutdown_telemetry",

    # Tracers and meters
    "get_tracer",
    "get_meter",
    "get_current_span",
    "trace_function",

    # Configuration
    "OTelConfig",

    # Metrics
    "record_request",
    "record_memory_operation",
    "record_cache_operation",
    "record_federation_operation",
    "increment_counter",
    "record_histogram",
    "set_gauge",

    # Context propagation
    "extract_trace_context",
    "inject_trace_context",
    "get_trace_id",
    "get_span_id",
    "set_baggage",
    "get_baggage",

    # Logging
    "setup_logging",
    "get_logger",
]

__version__ = "0.1.0"

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
