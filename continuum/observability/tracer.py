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
OpenTelemetry Tracer
====================

Core tracing functionality for CONTINUUM using OpenTelemetry.

Provides:
- Tracer initialization with multiple exporter backends
- Auto-instrumentation for common libraries
- Manual span creation and decoration
- Context propagation
- Sampling strategies
"""

import functools
import logging
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Tracer, Span, Status, StatusCode
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)

from .config import get_otel_config, OTelConfig
from .sampling import get_sampler

logger = logging.getLogger(__name__)

# Global state
_initialized = False
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def init_telemetry(
    service_name: Optional[str] = None,
    exporter_type: Optional[str] = None,
    sampling_rate: Optional[float] = None,
    config: Optional[OTelConfig] = None,
) -> bool:
    """
    Initialize OpenTelemetry tracing and metrics.

    This should be called once at application startup, before any requests are processed.

    Args:
        service_name: Override service name from config
        exporter_type: Override exporter type (jaeger|zipkin|otlp|datadog|console)
        sampling_rate: Override sampling rate (0.0-1.0)
        config: Optional OTelConfig instance (uses global config if not provided)

    Returns:
        True if initialization successful, False otherwise

    Example:
        ```python
        from continuum.observability import init_telemetry

        # Initialize with defaults from environment
        init_telemetry()

        # Or override specific settings
        init_telemetry(
            service_name="continuum-api",
            exporter_type="jaeger",
            sampling_rate=0.1
        )
        ```
    """
    global _initialized, _tracer_provider, _meter_provider

    if _initialized:
        logger.warning("Telemetry already initialized, skipping")
        return True

    try:
        # Get configuration
        cfg = config or get_otel_config()

        # Apply overrides
        if service_name:
            cfg.service_name = service_name
        if exporter_type:
            cfg.exporter_type = exporter_type
        if sampling_rate is not None:
            cfg.sampling_rate = sampling_rate

        logger.info(f"Initializing OpenTelemetry for service: {cfg.service_name}")
        logger.info(f"Exporter: {cfg.exporter_type}, Sampling: {cfg.sampling_rate}")

        # Create resource with service information
        resource = Resource.create(cfg.get_resource_attributes())

        # Initialize tracing
        _tracer_provider = _init_tracing(cfg, resource)

        # Initialize metrics
        if cfg.metrics_enabled:
            _meter_provider = _init_metrics(cfg, resource)

        # Setup auto-instrumentation
        _setup_auto_instrumentation(cfg)

        # Setup propagators
        _setup_propagators(cfg)

        _initialized = True
        logger.info("OpenTelemetry initialization complete")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        return False


def _init_tracing(config: OTelConfig, resource: Resource) -> TracerProvider:
    """
    Initialize tracing with configured exporter.

    Args:
        config: OTel configuration
        resource: Resource attributes

    Returns:
        TracerProvider instance
    """
    # Create tracer provider with sampler
    sampler = get_sampler(config)
    provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Get exporter based on configuration
    exporter = _get_trace_exporter(config)

    # Add batch span processor
    processor = BatchSpanProcessor(
        exporter,
        max_queue_size=config.batch_max_queue_size,
        schedule_delay_millis=config.batch_export_delay_millis,
        max_export_batch_size=config.batch_max_export_batch_size,
        export_timeout_millis=config.batch_export_timeout_millis,
    )
    provider.add_span_processor(processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(f"Tracing initialized with {config.exporter_type} exporter")
    return provider


def _init_metrics(config: OTelConfig, resource: Resource) -> MeterProvider:
    """
    Initialize metrics with configured exporter.

    Args:
        config: OTel configuration
        resource: Resource attributes

    Returns:
        MeterProvider instance
    """
    # Get metrics exporter
    exporter = _get_metrics_exporter(config)

    # Create periodic reader
    reader = PeriodicExportingMetricReader(
        exporter,
        export_interval_millis=config.metrics_export_interval_millis,
    )

    # Create meter provider
    provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )

    # Set as global meter provider
    metrics.set_meter_provider(provider)

    logger.info("Metrics initialized")
    return provider


def _get_trace_exporter(config: OTelConfig) -> SpanExporter:
    """
    Get trace exporter based on configuration.

    Args:
        config: OTel configuration

    Returns:
        SpanExporter instance
    """
    if config.exporter_type == "console":
        return ConsoleSpanExporter()

    elif config.exporter_type == "jaeger":
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        return JaegerExporter(
            agent_host_name=config.jaeger_agent_host,
            agent_port=config.jaeger_agent_port,
        )

    elif config.exporter_type == "zipkin":
        from opentelemetry.exporter.zipkin.json import ZipkinExporter
        return ZipkinExporter(
            endpoint=config.zipkin_endpoint,
        )

    elif config.exporter_type == "otlp":
        if config.otlp_protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            return OTLPSpanExporter(
                endpoint=config.otlp_endpoint,
                headers=config.otlp_headers,
            )
        else:  # http
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            return OTLPSpanExporter(
                endpoint=config.otlp_endpoint,
                headers=config.otlp_headers,
            )

    elif config.exporter_type == "datadog":
        # Datadog uses OTLP exporter with specific configuration
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        return OTLPSpanExporter(
            endpoint=f"{config.datadog_agent_url}/v0.7/traces",
        )

    else:
        raise ValueError(f"Unknown exporter type: {config.exporter_type}")


def _get_metrics_exporter(config: OTelConfig):
    """
    Get metrics exporter based on configuration.

    Args:
        config: OTel configuration

    Returns:
        MetricExporter instance
    """
    if config.exporter_type == "console":
        return ConsoleMetricExporter()

    elif config.exporter_type in ["otlp"]:
        if config.otlp_protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            return OTLPMetricExporter(
                endpoint=config.otlp_endpoint,
                headers=config.otlp_headers,
            )
        else:  # http
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            return OTLPMetricExporter(
                endpoint=config.otlp_endpoint,
                headers=config.otlp_headers,
            )

    else:
        # Default to console for unsupported exporters
        logger.warning(f"Metrics exporter not supported for {config.exporter_type}, using console")
        return ConsoleMetricExporter()


def _setup_auto_instrumentation(config: OTelConfig):
    """
    Setup auto-instrumentation for common libraries.

    Args:
        config: OTel configuration
    """
    try:
        # FastAPI instrumentation
        if config.auto_instrument_fastapi:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor().instrument()
                logger.info("FastAPI auto-instrumentation enabled")
            except ImportError:
                logger.debug("FastAPI instrumentation not available")

        # SQLAlchemy instrumentation
        if config.auto_instrument_sqlalchemy:
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                SQLAlchemyInstrumentor().instrument()
                logger.info("SQLAlchemy auto-instrumentation enabled")
            except ImportError:
                logger.debug("SQLAlchemy instrumentation not available")

        # Redis instrumentation
        if config.auto_instrument_redis:
            try:
                from opentelemetry.instrumentation.redis import RedisInstrumentor
                RedisInstrumentor().instrument()
                logger.info("Redis auto-instrumentation enabled")
            except ImportError:
                logger.debug("Redis instrumentation not available")

        # httpx instrumentation
        if config.auto_instrument_httpx:
            try:
                from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
                HTTPXClientInstrumentor().instrument()
                logger.info("httpx auto-instrumentation enabled")
            except ImportError:
                logger.debug("httpx instrumentation not available")

    except Exception as e:
        logger.warning(f"Error setting up auto-instrumentation: {e}")


def _setup_propagators(config: OTelConfig):
    """
    Setup trace context propagators.

    Args:
        config: OTel configuration
    """
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.composite import CompositePropagator

    propagators = []

    for prop_name in config.propagators:
        prop_name = prop_name.strip().lower()

        if prop_name == "tracecontext":
            from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
            propagators.append(TraceContextTextMapPropagator())

        elif prop_name == "baggage":
            from opentelemetry.baggage.propagation import W3CBaggagePropagator
            propagators.append(W3CBaggagePropagator())

        elif prop_name == "b3":
            from opentelemetry.propagators.b3 import B3MultiFormat
            propagators.append(B3MultiFormat())

        elif prop_name == "jaeger":
            from opentelemetry.propagators.jaeger import JaegerPropagator
            propagators.append(JaegerPropagator())

    if propagators:
        set_global_textmap(CompositePropagator(propagators))
        logger.info(f"Propagators configured: {config.propagators}")


def shutdown_telemetry(timeout_millis: int = 30000):
    """
    Shutdown telemetry and flush remaining spans/metrics.

    Should be called on application shutdown.

    Args:
        timeout_millis: Maximum time to wait for export in milliseconds
    """
    global _initialized, _tracer_provider, _meter_provider

    if not _initialized:
        return

    logger.info("Shutting down OpenTelemetry")

    # Shutdown tracer provider
    if _tracer_provider:
        _tracer_provider.shutdown()

    # Shutdown meter provider
    if _meter_provider:
        _meter_provider.shutdown()

    _initialized = False
    logger.info("OpenTelemetry shutdown complete")


def get_tracer(name: str = __name__) -> Tracer:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (typically __name__ of the module)

    Returns:
        Tracer instance

    Example:
        ```python
        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("my_operation"):
            # Your code here
            pass
        ```
    """
    return trace.get_tracer(name)


def get_meter(name: str = __name__):
    """
    Get a meter instance for metrics.

    Args:
        name: Meter name (typically __name__ of the module)

    Returns:
        Meter instance

    Example:
        ```python
        meter = get_meter(__name__)
        counter = meter.create_counter("requests_total")
        counter.add(1, {"endpoint": "/api/recall"})
        ```
    """
    return metrics.get_meter(name)


def get_current_span() -> Span:
    """
    Get the current active span.

    Returns:
        Current span or a non-recording span if none active

    Example:
        ```python
        span = get_current_span()
        span.set_attribute("user_id", "12345")
        span.add_event("Processing started")
        ```
    """
    return trace.get_current_span()


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True,
):
    """
    Decorator to trace a function.

    Args:
        name: Span name (defaults to function name)
        attributes: Static attributes to add to span
        record_exception: Whether to record exceptions as span events

    Example:
        ```python
        @trace_function(name="process_memory", attributes={"component": "memory"})
        def process_memory(data):
            # Function is automatically traced
            return result
        ```
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        tracer = get_tracer(func.__module__)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Add static attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    if record_exception:
                        span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Add static attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    if record_exception:
                        span.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def traced_operation(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    tracer_name: str = __name__,
):
    """
    Context manager for tracing an operation.

    Args:
        name: Span name
        attributes: Attributes to add to span
        tracer_name: Name of tracer to use

    Example:
        ```python
        with traced_operation("database_query", {"query_type": "select"}):
            result = db.query(...)
        ```
    """
    tracer = get_tracer(tracer_name)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
