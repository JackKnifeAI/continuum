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
OpenTelemetry Configuration
===========================

Environment-based configuration for OpenTelemetry tracing, metrics, and logging.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OTelConfig:
    """
    OpenTelemetry configuration.

    All settings can be overridden via environment variables prefixed with OTEL_.
    """

    # Service identification
    service_name: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "continuum"))
    service_namespace: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAMESPACE", "ai-memory"))
    service_version: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_VERSION", "0.1.0"))
    deployment_environment: str = field(default_factory=lambda: os.getenv("CONTINUUM_ENV", "development"))

    # Exporter configuration
    exporter_type: str = field(default_factory=lambda: os.getenv("OTEL_EXPORTER_TYPE", "console"))
    exporter_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("OTEL_ENDPOINT"))

    # Jaeger-specific
    jaeger_agent_host: str = field(default_factory=lambda: os.getenv("JAEGER_AGENT_HOST", "localhost"))
    jaeger_agent_port: int = field(default_factory=lambda: int(os.getenv("JAEGER_AGENT_PORT", "6831")))

    # Zipkin-specific
    zipkin_endpoint: str = field(default_factory=lambda: os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans"))

    # OTLP-specific
    otlp_endpoint: str = field(default_factory=lambda: os.getenv("OTLP_ENDPOINT", "http://localhost:4317"))
    otlp_protocol: str = field(default_factory=lambda: os.getenv("OTLP_PROTOCOL", "grpc"))  # grpc or http
    otlp_headers: Dict[str, str] = field(default_factory=dict)

    # Datadog-specific
    datadog_agent_url: str = field(default_factory=lambda: os.getenv("DD_AGENT_URL", "http://localhost:8126"))

    # Sampling configuration
    sampling_rate: float = field(default_factory=lambda: float(os.getenv("OTEL_SAMPLING_RATE", "1.0")))
    sample_errors_always: bool = field(default_factory=lambda: os.getenv("OTEL_SAMPLE_ERRORS_ALWAYS", "true").lower() == "true")

    # Propagators
    propagators: List[str] = field(default_factory=lambda: os.getenv("OTEL_PROPAGATORS", "tracecontext,baggage").split(","))

    # Resource attributes
    resource_attributes: Dict[str, str] = field(default_factory=dict)

    # Instrumentation settings
    auto_instrument_fastapi: bool = field(default_factory=lambda: os.getenv("OTEL_AUTO_INSTRUMENT_FASTAPI", "true").lower() == "true")
    auto_instrument_sqlalchemy: bool = field(default_factory=lambda: os.getenv("OTEL_AUTO_INSTRUMENT_SQLALCHEMY", "true").lower() == "true")
    auto_instrument_redis: bool = field(default_factory=lambda: os.getenv("OTEL_AUTO_INSTRUMENT_REDIS", "true").lower() == "true")
    auto_instrument_httpx: bool = field(default_factory=lambda: os.getenv("OTEL_AUTO_INSTRUMENT_HTTPX", "true").lower() == "true")

    # Performance tuning
    max_attributes_per_span: int = field(default_factory=lambda: int(os.getenv("OTEL_MAX_ATTRIBUTES_PER_SPAN", "128")))
    max_events_per_span: int = field(default_factory=lambda: int(os.getenv("OTEL_MAX_EVENTS_PER_SPAN", "128")))
    max_links_per_span: int = field(default_factory=lambda: int(os.getenv("OTEL_MAX_LINKS_PER_SPAN", "128")))

    # Batch processing
    batch_export_delay_millis: int = field(default_factory=lambda: int(os.getenv("OTEL_BSP_SCHEDULE_DELAY", "5000")))
    batch_max_queue_size: int = field(default_factory=lambda: int(os.getenv("OTEL_BSP_MAX_QUEUE_SIZE", "2048")))
    batch_max_export_batch_size: int = field(default_factory=lambda: int(os.getenv("OTEL_BSP_MAX_EXPORT_BATCH_SIZE", "512")))
    batch_export_timeout_millis: int = field(default_factory=lambda: int(os.getenv("OTEL_BSP_EXPORT_TIMEOUT", "30000")))

    # Metrics
    metrics_enabled: bool = field(default_factory=lambda: os.getenv("OTEL_METRICS_ENABLED", "true").lower() == "true")
    metrics_export_interval_millis: int = field(default_factory=lambda: int(os.getenv("OTEL_METRICS_EXPORT_INTERVAL", "60000")))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("OTEL_LOG_LEVEL", "INFO"))
    log_correlation: bool = field(default_factory=lambda: os.getenv("OTEL_LOG_CORRELATION", "true").lower() == "true")

    def __post_init__(self):
        """Post-initialization processing"""
        # Parse resource attributes from environment
        resource_attrs_str = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")
        if resource_attrs_str:
            for pair in resource_attrs_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    self.resource_attributes[key.strip()] = value.strip()

        # Parse OTLP headers from environment
        otlp_headers_str = os.getenv("OTLP_HEADERS", "")
        if otlp_headers_str:
            for pair in otlp_headers_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    self.otlp_headers[key.strip()] = value.strip()

        # Validate sampling rate
        if not 0.0 <= self.sampling_rate <= 1.0:
            raise ValueError(f"OTEL_SAMPLING_RATE must be between 0.0 and 1.0, got {self.sampling_rate}")

        # Validate exporter type
        valid_exporters = ["jaeger", "zipkin", "otlp", "datadog", "console"]
        if self.exporter_type not in valid_exporters:
            raise ValueError(f"OTEL_EXPORTER_TYPE must be one of {valid_exporters}, got {self.exporter_type}")

    def get_resource_attributes(self) -> Dict[str, str]:
        """
        Get all resource attributes including defaults and environment overrides.

        Returns:
            Dictionary of resource attributes
        """
        attrs = {
            "service.name": self.service_name,
            "service.namespace": self.service_namespace,
            "service.version": self.service_version,
            "deployment.environment": self.deployment_environment,
        }

        # Add custom resource attributes
        attrs.update(self.resource_attributes)

        # Add host information
        import socket
        attrs["host.name"] = socket.gethostname()

        # Add process information
        import os
        attrs["process.pid"] = str(os.getpid())

        return attrs

    def is_dev_environment(self) -> bool:
        """Check if running in development environment"""
        return self.deployment_environment in ["development", "dev", "local"]

    def is_prod_environment(self) -> bool:
        """Check if running in production environment"""
        return self.deployment_environment in ["production", "prod"]

    def should_sample_trace(self) -> bool:
        """
        Determine if a trace should be sampled based on configuration.

        Returns:
            True if trace should be sampled
        """
        # Always sample in development
        if self.is_dev_environment():
            return True

        # Use configured sampling rate
        import random
        return random.random() < self.sampling_rate


# Singleton config instance
_config: Optional[OTelConfig] = None


def get_otel_config() -> OTelConfig:
    """
    Get the global OpenTelemetry configuration instance.

    Returns:
        OTelConfig instance
    """
    global _config
    if _config is None:
        _config = OTelConfig()
    return _config


def set_otel_config(config: OTelConfig):
    """
    Set the global OpenTelemetry configuration.

    Args:
        config: OTelConfig instance
    """
    global _config
    _config = config

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
