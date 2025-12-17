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
Federation Layer Instrumentation
=================================

Peer-to-peer communication and synchronization tracing.

Features:
- P2P communication tracing
- Sync operation spans with conflict tracking
- Cross-instance trace propagation
- Network latency measurement
- Sync success/failure metrics
"""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.propagate import inject, extract

from .tracer import get_tracer, get_current_span
from .metrics import increment_counter, record_histogram, set_gauge


# Module-level tracer
tracer = get_tracer(__name__)


@contextmanager
def trace_sync_operation(
    operation_type: str,
    peer_instance_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing federation sync operations.

    Args:
        operation_type: Type of sync operation (PUSH, PULL, FULL_SYNC)
        peer_instance_id: ID of peer instance
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_sync_operation("PUSH", peer_instance_id="claude-456"):
            sync_data_to_peer(peer, data)
        ```
    """
    span_name = f"federation.sync.{operation_type.lower()}"

    with tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
        # Set federation attributes
        span.set_attribute("federation.operation", operation_type)

        if peer_instance_id:
            span.set_attribute("federation.peer.instance_id", peer_instance_id)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record sync duration metric
            record_histogram(
                "continuum_federation_sync_duration_seconds",
                duration,
                {
                    "operation": operation_type.lower(),
                    "peer": peer_instance_id or "unknown",
                    "tenant_id": tenant_id or "unknown",
                }
            )

            # Record successful sync
            increment_counter(
                "continuum_federation_sync_success_total",
                {
                    "operation": operation_type.lower(),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record failed sync
            increment_counter(
                "continuum_federation_sync_errors_total",
                {
                    "operation": operation_type.lower(),
                    "error_type": type(e).__name__,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            raise


@contextmanager
def trace_peer_communication(
    peer_id: str,
    message_type: str,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing peer-to-peer communication.

    Args:
        peer_id: Peer instance ID
        message_type: Type of message (MEMORY_ADDED, CONCEPT_LEARNED, etc.)
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_peer_communication("claude-456", "MEMORY_ADDED"):
            send_message_to_peer(peer, message)
        ```
    """
    span_name = f"federation.message.{message_type.lower()}"

    with tracer.start_as_current_span(span_name, kind=SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "websocket")
        span.set_attribute("messaging.operation", "publish")
        span.set_attribute("messaging.destination", peer_id)
        span.set_attribute("messaging.message_type", message_type)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record message sent
            increment_counter(
                "continuum_federation_messages_sent_total",
                {
                    "message_type": message_type.lower(),
                    "peer": peer_id,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            # Record latency
            record_histogram(
                "continuum_federation_message_latency_seconds",
                duration,
                {
                    "message_type": message_type.lower(),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record error
            increment_counter(
                "continuum_federation_message_errors_total",
                {
                    "message_type": message_type.lower(),
                    "error_type": type(e).__name__,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            raise


def inject_trace_context_into_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject trace context into a federation message for cross-instance propagation.

    Args:
        message: Message dictionary

    Returns:
        Message with trace context injected

    Example:
        ```python
        message = {
            "event_type": "memory_added",
            "data": {...}
        }
        message = inject_trace_context_into_message(message)
        # message now has "trace_context" field
        ```
    """
    # Create carrier dict for context propagation
    carrier = {}
    inject(carrier)

    # Add trace context to message
    if carrier:
        message["trace_context"] = carrier

    return message


def extract_trace_context_from_message(message: Dict[str, Any]) -> Optional[trace.SpanContext]:
    """
    Extract trace context from a federation message.

    Args:
        message: Message dictionary with trace context

    Returns:
        Extracted span context or None

    Example:
        ```python
        # Receiving message from peer
        context = extract_trace_context_from_message(message)
        if context:
            # Use context as parent for new span
            with tracer.start_as_current_span("process_message", context=context):
                process_message(message)
        ```
    """
    trace_context = message.get("trace_context")
    if not trace_context:
        return None

    # Extract context from carrier
    return extract(trace_context)


def record_conflict_resolution(
    conflict_type: str,
    resolution_strategy: str,
    tenant_id: Optional[str] = None,
):
    """
    Record a conflict resolution event.

    Args:
        conflict_type: Type of conflict (MEMORY_CONFLICT, CONCEPT_CONFLICT, etc.)
        resolution_strategy: Strategy used (LATEST_WINS, MERGE, MANUAL)
        tenant_id: Tenant identifier
    """
    # Add event to current span
    span = get_current_span()
    span.add_event(
        "conflict_resolved",
        {
            "conflict_type": conflict_type,
            "resolution_strategy": resolution_strategy,
        }
    )

    # Record metric
    increment_counter(
        "continuum_federation_conflicts_total",
        {
            "conflict_type": conflict_type.lower(),
            "resolution": resolution_strategy.lower(),
            "tenant_id": tenant_id or "unknown",
        }
    )


def record_peer_connection(
    peer_id: str,
    connected: bool,
    tenant_id: Optional[str] = None,
):
    """
    Record peer connection state change.

    Args:
        peer_id: Peer instance ID
        connected: Whether peer is now connected
        tenant_id: Tenant identifier
    """
    # Add event to current span
    span = get_current_span()
    span.add_event(
        "peer_connection_changed",
        {
            "peer_id": peer_id,
            "connected": connected,
        }
    )

    # Record metric
    if connected:
        increment_counter(
            "continuum_federation_peer_connections_total",
            {"peer": peer_id, "tenant_id": tenant_id or "unknown"}
        )
    else:
        increment_counter(
            "continuum_federation_peer_disconnections_total",
            {"peer": peer_id, "tenant_id": tenant_id or "unknown"}
        )


def update_peer_count(count: int, tenant_id: Optional[str] = None):
    """
    Update active peer count gauge.

    Args:
        count: Number of active peers
        tenant_id: Tenant identifier
    """
    set_gauge(
        "continuum_federation_active_peers",
        count,
        {"tenant_id": tenant_id or "unknown"}
    )


@contextmanager
def trace_consensus_operation(
    operation: str,
    participant_count: int,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing consensus operations.

    Args:
        operation: Consensus operation type
        participant_count: Number of participants
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_consensus_operation("LEADER_ELECTION", participant_count=5):
            leader = elect_leader(participants)
        ```
    """
    span_name = f"federation.consensus.{operation.lower()}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("consensus.operation", operation)
        span.set_attribute("consensus.participant_count", participant_count)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record consensus duration
            record_histogram(
                "continuum_federation_consensus_duration_seconds",
                duration,
                {
                    "operation": operation.lower(),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def enrich_span_with_sync_stats(
    entities_synced: int,
    conflicts_resolved: int,
    bytes_transferred: int,
    span: Optional[trace.Span] = None,
):
    """
    Enrich span with sync operation statistics.

    Args:
        entities_synced: Number of entities synchronized
        conflicts_resolved: Number of conflicts resolved
        bytes_transferred: Bytes transferred
        span: Optional span to enrich
    """
    if span is None:
        span = get_current_span()

    span.set_attribute("sync.entities_count", entities_synced)
    span.set_attribute("sync.conflicts_count", conflicts_resolved)
    span.set_attribute("sync.bytes_transferred", bytes_transferred)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
