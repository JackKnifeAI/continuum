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
Logging Integration
===================

Structured logging with automatic trace context injection.

Features:
- Trace ID and Span ID injection into logs
- JSON structured output
- Log level to span events
- Exception to span recording
- Automatic correlation with traces
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .context import get_trace_id, get_span_id


class TraceContextFilter(logging.Filter):
    """
    Logging filter that adds trace context to log records.

    Automatically adds trace_id and span_id to all log records
    when there's an active span.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add trace context to log record.

        Args:
            record: Log record to enhance

        Returns:
            Always True (doesn't filter records)
        """
        # Add trace ID
        trace_id = get_trace_id()
        record.trace_id = trace_id if trace_id else "none"

        # Add span ID
        span_id = get_span_id()
        record.span_id = span_id if span_id else "none"

        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs as JSON with consistent structure including:
    - timestamp
    - level
    - logger name
    - message
    - trace_id
    - span_id
    - additional fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "none"),
            "span_id": getattr(record, "span_id", "none"),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "trace_id", "span_id", "timestamp", "level", "logger"
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class SpanEventHandler(logging.Handler):
    """
    Logging handler that adds log events to the current span.

    This creates span events for log messages, creating a timeline
    of logs within each span in distributed traces.
    """

    def emit(self, record: logging.LogRecord):
        """
        Emit log record as span event.

        Args:
            record: Log record to emit
        """
        try:
            span = trace.get_current_span()
            if not span or not span.is_recording():
                return

            # Create event attributes
            attributes = {
                "log.level": record.levelname,
                "log.logger": record.name,
                "log.message": record.getMessage(),
            }

            # Add exception info if present
            if record.exc_info:
                attributes["exception.type"] = record.exc_info[0].__name__
                attributes["exception.message"] = str(record.exc_info[1])

            # Add event to span
            span.add_event(
                name=f"log.{record.levelname.lower()}",
                attributes=attributes,
            )

            # Set error status on ERROR/CRITICAL logs
            if record.levelno >= logging.ERROR:
                span.set_status(Status(StatusCode.ERROR, record.getMessage()))

        except Exception:
            # Don't let logging errors break the application
            self.handleError(record)


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    add_span_events: bool = True,
) -> logging.Logger:
    """
    Setup logging with trace context integration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output logs as JSON
        add_span_events: Whether to add log events to spans

    Returns:
        Configured root logger

    Example:
        ```python
        from continuum.observability import setup_logging

        # Setup logging with trace integration
        logger = setup_logging(level="INFO", json_output=True)

        # Logs now include trace_id and span_id
        logger.info("Processing request")
        ```
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))

    # Add trace context filter
    console_handler.addFilter(TraceContextFilter())

    # Set formatter
    if json_output:
        formatter = JSONFormatter()
    else:
        # Standard formatter with trace context
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s] [span_id=%(span_id)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add span event handler if enabled
    if add_span_events:
        span_handler = SpanEventHandler()
        span_handler.setLevel(logging.WARNING)  # Only WARNING and above
        logger.addHandler(span_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with trace context integration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        ```python
        from continuum.observability import get_logger

        logger = get_logger(__name__)
        logger.info("Processing started")
        ```
    """
    logger = logging.getLogger(name)

    # Ensure trace context filter is added
    if not any(isinstance(f, TraceContextFilter) for f in logger.filters):
        logger.addFilter(TraceContextFilter())

    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs
):
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context fields

    Example:
        ```python
        log_with_context(
            logger,
            "info",
            "Memory recall completed",
            tenant_id="user_123",
            concepts_found=5,
            duration_ms=123.45
        )
        ```
    """
    # Get log method
    log_method = getattr(logger, level.lower())

    # Log with extra context
    log_method(message, extra=kwargs)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: Optional[str] = None,
    **kwargs
):
    """
    Log an exception with trace context.

    Automatically records the exception in the current span.

    Args:
        logger: Logger instance
        exception: Exception to log
        message: Optional message (defaults to exception message)
        **kwargs: Additional context fields

    Example:
        ```python
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, e, tenant_id="user_123")
        ```
    """
    # Record exception in span
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))

    # Log exception
    msg = message or str(exception)
    logger.error(
        msg,
        exc_info=exception,
        extra={
            "exception_type": type(exception).__name__,
            **kwargs
        }
    )


class StructuredLogger:
    """
    Structured logger with automatic trace context.

    Provides a cleaner API for structured logging with trace integration.
    """

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name
        """
        self.logger = get_logger(name)

    def debug(self, message: str, **context):
        """Log debug message with context"""
        self.logger.debug(message, extra=context)

    def info(self, message: str, **context):
        """Log info message with context"""
        self.logger.info(message, extra=context)

    def warning(self, message: str, **context):
        """Log warning message with context"""
        self.logger.warning(message, extra=context)

    def error(self, message: str, **context):
        """Log error message with context"""
        self.logger.error(message, extra=context)

    def critical(self, message: str, **context):
        """Log critical message with context"""
        self.logger.critical(message, extra=context)

    def exception(self, exception: Exception, message: Optional[str] = None, **context):
        """Log exception with trace recording"""
        log_exception(self.logger, exception, message, **context)


def create_logger(name: str) -> StructuredLogger:
    """
    Create a structured logger.

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance

    Example:
        ```python
        from continuum.observability import create_logger

        logger = create_logger(__name__)
        logger.info("Processing request", tenant_id="user_123", duration=0.5)
        ```
    """
    return StructuredLogger(name)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
