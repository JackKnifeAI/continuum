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
Memory Layer Instrumentation
=============================

AI memory operation tracing.

Features:
- Memory operation tracing (store, recall, search)
- Embedding generation spans
- Knowledge graph traversal tracking
- Concept extraction timing
- Attention link analysis
"""

import time
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .tracer import get_tracer, get_current_span
from .metrics import increment_counter, record_histogram, set_gauge


# Module-level tracer
tracer = get_tracer(__name__)


@contextmanager
def trace_recall(
    query: str,
    max_concepts: int = 10,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing memory recall operations.

    Args:
        query: Query string
        max_concepts: Maximum concepts to retrieve
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_recall("Tell me about warp drives", max_concepts=10) as span:
            context = memory.recall(query)
            span.set_attribute("concepts_found", context.concepts_found)
        ```
    """
    with tracer.start_as_current_span("memory.recall") as span:
        # Set memory attributes
        span.set_attribute("memory.operation", "recall")
        span.set_attribute("memory.query_length", len(query))
        span.set_attribute("memory.max_concepts", max_concepts)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        # Sanitize query (first 100 chars)
        sanitized_query = query[:100]
        span.set_attribute("memory.query_preview", sanitized_query)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record recall duration
            record_histogram(
                "continuum_memory_recall_duration_seconds",
                duration,
                {"tenant_id": tenant_id or "unknown"}
            )

            # Increment recall counter
            increment_counter(
                "continuum_memory_recalls_total",
                {"tenant_id": tenant_id or "unknown"}
            )

        except Exception as e:
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record error
            increment_counter(
                "continuum_memory_recall_errors_total",
                {
                    "error_type": type(e).__name__,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            raise


@contextmanager
def trace_learn(
    user_message_length: int,
    ai_response_length: int,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing memory learning operations.

    Args:
        user_message_length: Length of user message
        ai_response_length: Length of AI response
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_learn(len(user_msg), len(ai_msg)) as span:
            result = memory.learn(user_msg, ai_msg)
            span.set_attribute("concepts_extracted", result.concepts_extracted)
        ```
    """
    with tracer.start_as_current_span("memory.learn") as span:
        # Set memory attributes
        span.set_attribute("memory.operation", "learn")
        span.set_attribute("memory.user_message_length", user_message_length)
        span.set_attribute("memory.ai_response_length", ai_response_length)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record learn duration
            record_histogram(
                "continuum_memory_learn_duration_seconds",
                duration,
                {"tenant_id": tenant_id or "unknown"}
            )

            # Increment learn counter
            increment_counter(
                "continuum_memory_learns_total",
                {"tenant_id": tenant_id or "unknown"}
            )

        except Exception as e:
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record error
            increment_counter(
                "continuum_memory_learn_errors_total",
                {
                    "error_type": type(e).__name__,
                    "tenant_id": tenant_id or "unknown",
                }
            )

            raise


@contextmanager
def trace_concept_extraction(tenant_id: Optional[str] = None):
    """
    Context manager for tracing concept extraction.

    Example:
        ```python
        with trace_concept_extraction() as span:
            concepts = extract_concepts_from_text(text)
            span.set_attribute("concepts_extracted", len(concepts))
        ```
    """
    with tracer.start_as_current_span("memory.concept_extraction") as span:
        span.set_attribute("memory.operation", "concept_extraction")

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record extraction duration
            record_histogram(
                "continuum_memory_concept_extraction_duration_seconds",
                duration,
                {"tenant_id": tenant_id or "unknown"}
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_graph_traversal(
    start_concept: str,
    max_depth: int = 3,
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing knowledge graph traversal.

    Args:
        start_concept: Starting concept
        max_depth: Maximum traversal depth
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_graph_traversal("warp drive", max_depth=3) as span:
            related = traverse_graph(concept, depth)
            span.set_attribute("concepts_found", len(related))
        ```
    """
    with tracer.start_as_current_span("memory.graph_traversal") as span:
        span.set_attribute("memory.operation", "graph_traversal")
        span.set_attribute("graph.start_concept", start_concept)
        span.set_attribute("graph.max_depth", max_depth)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record traversal duration
            record_histogram(
                "continuum_memory_graph_traversal_duration_seconds",
                duration,
                {
                    "max_depth": str(max_depth),
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_embedding_generation(
    text_length: int,
    model: str = "unknown",
    tenant_id: Optional[str] = None,
):
    """
    Context manager for tracing embedding generation.

    Args:
        text_length: Length of text to embed
        model: Embedding model name
        tenant_id: Tenant identifier

    Example:
        ```python
        with trace_embedding_generation(len(text), model="text-embedding-ada-002"):
            embedding = generate_embedding(text)
        ```
    """
    with tracer.start_as_current_span("memory.embedding") as span:
        span.set_attribute("memory.operation", "embedding_generation")
        span.set_attribute("embedding.text_length", text_length)
        span.set_attribute("embedding.model", model)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        start_time = time.time()

        try:
            yield span

            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record embedding duration
            record_histogram(
                "continuum_memory_embedding_duration_seconds",
                duration,
                {
                    "model": model,
                    "tenant_id": tenant_id or "unknown",
                }
            )

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def enrich_span_with_recall_results(
    concepts_found: int,
    relationships_found: int,
    query_time_ms: float,
    span: Optional[trace.Span] = None,
):
    """
    Enrich span with recall operation results.

    Args:
        concepts_found: Number of concepts retrieved
        relationships_found: Number of relationships found
        query_time_ms: Query execution time in milliseconds
        span: Optional span to enrich
    """
    if span is None:
        span = get_current_span()

    span.set_attribute("memory.concepts_found", concepts_found)
    span.set_attribute("memory.relationships_found", relationships_found)
    span.set_attribute("memory.query_time_ms", query_time_ms)


def enrich_span_with_learn_results(
    concepts_extracted: int,
    decisions_detected: int,
    links_created: int,
    compounds_found: int,
    span: Optional[trace.Span] = None,
):
    """
    Enrich span with learn operation results.

    Args:
        concepts_extracted: Number of concepts extracted
        decisions_detected: Number of decisions detected
        links_created: Number of graph links created
        compounds_found: Number of compound concepts found
        span: Optional span to enrich
    """
    if span is None:
        span = get_current_span()

    span.set_attribute("memory.concepts_extracted", concepts_extracted)
    span.set_attribute("memory.decisions_detected", decisions_detected)
    span.set_attribute("memory.links_created", links_created)
    span.set_attribute("memory.compounds_found", compounds_found)


def update_memory_stats(
    total_entities: int,
    total_messages: int,
    total_decisions: int,
    attention_links: int,
    tenant_id: Optional[str] = None,
):
    """
    Update memory system statistics gauges.

    Args:
        total_entities: Total number of entities
        total_messages: Total number of messages
        total_decisions: Total number of decisions
        attention_links: Total number of attention links
        tenant_id: Tenant identifier
    """
    labels = {"tenant_id": tenant_id or "unknown"}

    set_gauge("continuum_memory_entities_total", total_entities, labels)
    set_gauge("continuum_memory_messages_total", total_messages, labels)
    set_gauge("continuum_memory_decisions_total", total_decisions, labels)
    set_gauge("continuum_memory_attention_links_total", attention_links, labels)


def record_memory_operation(
    operation: str,
    duration: float,
    success: bool,
    tenant_id: Optional[str] = None,
):
    """
    Record a memory operation metric.

    Args:
        operation: Operation type (recall|learn|search)
        duration: Operation duration in seconds
        success: Whether operation succeeded
        tenant_id: Tenant identifier
    """
    labels = {
        "operation": operation,
        "success": str(success),
        "tenant_id": tenant_id or "unknown",
    }

    # Record duration
    record_histogram(
        "continuum_memory_operation_duration_seconds",
        duration,
        labels,
    )

    # Record count
    increment_counter(
        "continuum_memory_operations_total",
        labels,
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
