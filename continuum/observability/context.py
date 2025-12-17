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
Trace Context Propagation
==========================

Utilities for propagating trace context across service boundaries.

Supports:
- W3C TraceContext propagation
- Baggage propagation for user context
- Cross-service correlation
- Async context preservation
"""

from typing import Dict, Optional, Any
from opentelemetry import trace, baggage, context
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import SpanContext


def extract_trace_context(carrier: Dict[str, str]) -> Optional[context.Context]:
    """
    Extract trace context from a carrier (e.g., HTTP headers).

    Args:
        carrier: Dictionary containing trace context (e.g., HTTP headers)

    Returns:
        Extracted context or None

    Example:
        ```python
        # Extract from HTTP headers
        ctx = extract_trace_context(request.headers)

        # Use as parent context for new span
        with tracer.start_as_current_span("operation", context=ctx):
            # This span will be a child of the remote span
            pass
        ```
    """
    if not carrier:
        return None

    try:
        return extract(carrier)
    except Exception:
        return None


def inject_trace_context(carrier: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Inject current trace context into a carrier (e.g., HTTP headers).

    Args:
        carrier: Optional carrier dictionary to inject into (creates new if None)

    Returns:
        Carrier with trace context injected

    Example:
        ```python
        # Inject into HTTP headers for outgoing request
        headers = inject_trace_context()
        response = httpx.get(url, headers=headers)
        ```
    """
    carrier = carrier or {}
    inject(carrier)
    return carrier


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID as a hex string.

    Returns:
        Trace ID or None if no active span

    Example:
        ```python
        trace_id = get_trace_id()
        logger.info(f"Processing request", extra={"trace_id": trace_id})
        ```
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, '032x')
    return None


def get_span_id() -> Optional[str]:
    """
    Get the current span ID as a hex string.

    Returns:
        Span ID or None if no active span

    Example:
        ```python
        span_id = get_span_id()
        logger.info(f"Processing operation", extra={"span_id": span_id})
        ```
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, '016x')
    return None


def get_trace_context() -> Optional[SpanContext]:
    """
    Get the current span context.

    Returns:
        SpanContext or None
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return span.get_span_context()
    return None


def set_baggage(key: str, value: str):
    """
    Set a baggage item in the current context.

    Baggage is propagated across service boundaries and can be used
    to carry user context, tenant IDs, etc.

    Args:
        key: Baggage key
        value: Baggage value

    Example:
        ```python
        set_baggage("tenant_id", "user_123")
        set_baggage("user_id", "alex")

        # Baggage is automatically propagated to downstream services
        response = httpx.get(url)
        ```
    """
    ctx = baggage.set_baggage(key, value)
    context.attach(ctx)


def get_baggage(key: str) -> Optional[str]:
    """
    Get a baggage item from the current context.

    Args:
        key: Baggage key

    Returns:
        Baggage value or None

    Example:
        ```python
        tenant_id = get_baggage("tenant_id")
        if tenant_id:
            logger.info(f"Processing for tenant: {tenant_id}")
        ```
    """
    return baggage.get_baggage(key)


def get_all_baggage() -> Dict[str, str]:
    """
    Get all baggage items from the current context.

    Returns:
        Dictionary of all baggage items
    """
    return baggage.get_all()


def clear_baggage():
    """
    Clear all baggage from the current context.
    """
    ctx = baggage.clear()
    context.attach(ctx)


def with_trace_context(carrier: Dict[str, str]):
    """
    Context manager to temporarily attach trace context.

    Args:
        carrier: Carrier with trace context

    Example:
        ```python
        # Receive message from queue with trace context
        message = queue.receive()

        # Process with parent trace context
        with with_trace_context(message.headers):
            # Spans created here will be children of the remote span
            process_message(message)
        ```
    """
    ctx = extract_trace_context(carrier)
    if ctx:
        token = context.attach(ctx)
        try:
            yield
        finally:
            context.detach(token)
    else:
        yield


def create_carrier_from_span(span: trace.Span) -> Dict[str, str]:
    """
    Create a carrier from a span for manual propagation.

    Args:
        span: Span to extract context from

    Returns:
        Carrier dictionary with trace context

    Example:
        ```python
        with tracer.start_as_current_span("parent") as span:
            # Create carrier for async task
            carrier = create_carrier_from_span(span)

            # Send to background worker
            queue.send({
                "data": data,
                "trace_context": carrier
            })
        ```
    """
    carrier = {}

    # Set current span as active and inject
    ctx = trace.set_span_in_context(span)
    token = context.attach(ctx)
    try:
        inject(carrier)
    finally:
        context.detach(token)

    return carrier


def link_spans(parent_carrier: Dict[str, str]) -> Optional[trace.Link]:
    """
    Create a span link from a carrier.

    Links allow connecting spans that aren't in a parent-child relationship,
    useful for async processing, batch operations, etc.

    Args:
        parent_carrier: Carrier containing parent trace context

    Returns:
        Span link or None

    Example:
        ```python
        # Receive batch of messages with trace contexts
        messages = queue.receive_batch()

        # Create span that links to all parent spans
        links = [link_spans(msg.headers) for msg in messages]

        with tracer.start_as_current_span("batch_process", links=links):
            # Process all messages
            for msg in messages:
                process(msg)
        ```
    """
    ctx = extract_trace_context(parent_carrier)
    if ctx:
        span_ctx = trace.get_current_span(ctx).get_span_context()
        if span_ctx.is_valid:
            return trace.Link(span_ctx)
    return None


def propagate_context_to_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propagate current trace context into a dictionary.

    Useful for message queues, events, etc.

    Args:
        data: Dictionary to add trace context to

    Returns:
        Dictionary with trace context added

    Example:
        ```python
        event = {
            "event_type": "memory_added",
            "data": {...}
        }

        # Add trace context for propagation
        event = propagate_context_to_dict(event)

        # Send event
        event_bus.publish(event)
        ```
    """
    carrier = inject_trace_context()
    if carrier:
        data["_trace_context"] = carrier
    return data


def extract_context_from_dict(data: Dict[str, Any]) -> Optional[context.Context]:
    """
    Extract trace context from a dictionary.

    Args:
        data: Dictionary containing trace context

    Returns:
        Extracted context or None

    Example:
        ```python
        # Receive event
        event = event_bus.receive()

        # Extract and use trace context
        ctx = extract_context_from_dict(event)
        if ctx:
            with with_trace_context(event.get("_trace_context", {})):
                process_event(event)
        ```
    """
    carrier = data.get("_trace_context")
    if carrier:
        return extract_trace_context(carrier)
    return None


def get_traceparent() -> Optional[str]:
    """
    Get the W3C traceparent header value for the current span.

    Returns:
        Traceparent string or None

    Example:
        ```python
        traceparent = get_traceparent()
        # Returns: "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        ```
    """
    carrier = inject_trace_context()
    return carrier.get("traceparent")


def get_tracestate() -> Optional[str]:
    """
    Get the W3C tracestate header value for the current span.

    Returns:
        Tracestate string or None
    """
    carrier = inject_trace_context()
    return carrier.get("tracestate")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
