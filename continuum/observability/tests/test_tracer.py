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
Tests for OpenTelemetry Tracer
===============================

Basic tests to verify tracing functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

from continuum.observability import (
    init_telemetry,
    shutdown_telemetry,
    get_tracer,
    get_current_span,
    trace_function,
)
from continuum.observability.config import OTelConfig


@pytest.fixture
def clean_telemetry():
    """Ensure clean state before each test"""
    shutdown_telemetry()
    yield
    shutdown_telemetry()


def test_init_telemetry_console(clean_telemetry):
    """Test initialization with console exporter"""
    result = init_telemetry(
        service_name="test-service",
        exporter_type="console",
    )

    assert result is True

    # Verify tracer provider is set
    tracer = get_tracer(__name__)
    assert tracer is not None


def test_init_telemetry_with_config(clean_telemetry):
    """Test initialization with custom config"""
    config = OTelConfig(
        service_name="test-service",
        exporter_type="console",
        sampling_rate=0.5,
    )

    result = init_telemetry(config=config)
    assert result is True


def test_get_tracer():
    """Test getting a tracer"""
    tracer = get_tracer(__name__)
    assert tracer is not None
    assert isinstance(tracer, trace.Tracer)


def test_create_span():
    """Test creating a basic span"""
    init_telemetry(exporter_type="console")

    tracer = get_tracer(__name__)

    with tracer.start_as_current_span("test_span") as span:
        assert span is not None
        assert span.is_recording()

        # Add attributes
        span.set_attribute("test.attr", "value")
        span.set_attribute("test.number", 42)

        # Verify span is current
        current = get_current_span()
        assert current == span


def test_trace_function_decorator():
    """Test @trace_function decorator"""
    init_telemetry(exporter_type="console")

    @trace_function(name="test_operation")
    def test_func(x, y):
        return x + y

    result = test_func(5, 3)
    assert result == 8


def test_trace_function_with_attributes():
    """Test decorator with static attributes"""
    init_telemetry(exporter_type="console")

    @trace_function(
        name="test_op",
        attributes={"component": "test", "version": "1.0"}
    )
    def test_func():
        span = get_current_span()
        # Attributes should be set
        return span.is_recording()

    result = test_func()
    assert result is True


def test_trace_function_async():
    """Test decorator with async function"""
    import asyncio

    init_telemetry(exporter_type="console")

    @trace_function(name="async_test")
    async def async_func(value):
        return value * 2

    result = asyncio.run(async_func(21))
    assert result == 42


def test_trace_function_exception_recording():
    """Test that exceptions are recorded in spans"""
    init_telemetry(exporter_type="console")

    @trace_function(record_exception=True)
    def failing_func():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        failing_func()


def test_nested_spans():
    """Test nested span creation"""
    init_telemetry(exporter_type="console")

    tracer = get_tracer(__name__)

    with tracer.start_as_current_span("parent") as parent:
        parent.set_attribute("level", "parent")

        with tracer.start_as_current_span("child") as child:
            child.set_attribute("level", "child")

            # Child span should be current
            current = get_current_span()
            assert current == child


def test_span_attributes():
    """Test setting various span attributes"""
    init_telemetry(exporter_type="console")

    tracer = get_tracer(__name__)

    with tracer.start_as_current_span("test") as span:
        # String
        span.set_attribute("string_attr", "value")

        # Number
        span.set_attribute("int_attr", 42)
        span.set_attribute("float_attr", 3.14)

        # Boolean
        span.set_attribute("bool_attr", True)

        # List (will be converted to string)
        span.set_attribute("list_attr", str(["a", "b", "c"]))


def test_span_events():
    """Test adding events to spans"""
    init_telemetry(exporter_type="console")

    tracer = get_tracer(__name__)

    with tracer.start_as_current_span("test") as span:
        # Add simple event
        span.add_event("operation_started")

        # Add event with attributes
        span.add_event("checkpoint", {
            "progress": 50,
            "status": "in_progress"
        })


def test_multiple_init_calls(clean_telemetry):
    """Test that multiple init calls don't cause issues"""
    result1 = init_telemetry(exporter_type="console")
    assert result1 is True

    # Second init should be skipped
    result2 = init_telemetry(exporter_type="console")
    assert result2 is True  # Still returns True but skips init


def test_shutdown_telemetry():
    """Test shutdown"""
    init_telemetry(exporter_type="console")
    shutdown_telemetry()

    # Should be able to init again after shutdown
    result = init_telemetry(exporter_type="console")
    assert result is True


def test_config_from_env(monkeypatch, clean_telemetry):
    """Test configuration from environment variables"""
    monkeypatch.setenv("OTEL_SERVICE_NAME", "env-test-service")
    monkeypatch.setenv("OTEL_EXPORTER_TYPE", "console")
    monkeypatch.setenv("OTEL_SAMPLING_RATE", "0.5")

    config = OTelConfig()
    assert config.service_name == "env-test-service"
    assert config.exporter_type == "console"
    assert config.sampling_rate == 0.5


def test_sampling_rate_validation():
    """Test that invalid sampling rates raise error"""
    with pytest.raises(ValueError):
        OTelConfig(sampling_rate=1.5)  # > 1.0

    with pytest.raises(ValueError):
        OTelConfig(sampling_rate=-0.1)  # < 0.0


def test_exporter_type_validation():
    """Test that invalid exporter types raise error"""
    with pytest.raises(ValueError):
        OTelConfig(exporter_type="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
