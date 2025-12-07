#!/usr/bin/env python3
"""
CONTINUUM Observability Quick Start
====================================

Complete example showing how to add distributed tracing to CONTINUUM.

Run this example:
    python examples/observability_quickstart.py

Then view traces at:
    http://localhost:16686 (Jaeger UI)
"""

import time
import random
from pathlib import Path

# Initialize CONTINUUM observability
from continuum.observability import (
    init_telemetry,
    shutdown_telemetry,
    get_tracer,
    setup_logging,
    get_logger,
)

from continuum.observability.memory_instrumentation import (
    trace_recall,
    trace_learn,
    enrich_span_with_recall_results,
    enrich_span_with_learn_results,
)

from continuum.observability.database_instrumentation import trace_query
from continuum.observability.cache_instrumentation import (
    trace_cache_operation,
    record_cache_hit,
    record_cache_miss,
)

from continuum.observability.context import set_baggage, get_baggage


def main():
    """Main example"""

    print("=" * 70)
    print("CONTINUUM Observability Quick Start")
    print("=" * 70)

    # 1. Initialize telemetry
    print("\n1. Initializing OpenTelemetry...")
    init_telemetry(
        service_name="continuum-quickstart",
        exporter_type="console",  # Use console for this demo
        sampling_rate=1.0,        # Sample everything for demo
    )

    # 2. Setup structured logging with trace context
    print("2. Setting up structured logging...")
    setup_logging(level="INFO", json_output=False)
    logger = get_logger(__name__)

    # 3. Get a tracer
    tracer = get_tracer(__name__)

    print("3. Running example operations...\n")

    # 4. Simulate a user request
    with tracer.start_as_current_span("user_request") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.route", "/v1/recall")
        span.set_attribute("http.status_code", 200)

        # Set baggage for tenant context
        set_baggage("tenant_id", "demo_user_123")
        set_baggage("user_tier", "premium")

        logger.info("Processing user request")

        # Simulate memory recall
        simulate_memory_recall(logger)

        # Simulate memory learning
        simulate_memory_learn(logger)

        logger.info("Request completed successfully")

    # 5. Shutdown telemetry
    print("\n4. Shutting down telemetry...")
    shutdown_telemetry()

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    print("\nIn production, you would see these traces in Jaeger UI:")
    print("  http://localhost:16686")
    print("\nTo run with Jaeger:")
    print("  1. Start observability stack: cd deploy/otel && docker-compose up -d")
    print("  2. Set exporter: export OTEL_EXPORTER_TYPE=jaeger")
    print("  3. Run this script again")
    print("=" * 70)


def simulate_memory_recall(logger):
    """Simulate a memory recall operation"""
    query = "Tell me about distributed tracing in CONTINUUM"
    tenant_id = get_baggage("tenant_id")

    with trace_recall(query, max_concepts=10, tenant_id=tenant_id) as span:
        logger.info("Starting memory recall", extra={"query_length": len(query)})

        # Simulate cache check
        cache_key = f"search:{hash(query)}"
        with trace_cache_operation("GET", cache_key, tenant_id):
            time.sleep(0.01)  # Simulate cache lookup
            # Simulate cache miss
            record_cache_miss(cache_key, tenant_id)

        # Simulate database query
        with trace_query(
            "SELECT * FROM entities WHERE tenant_id = ?",
            "SELECT",
            "entities",
            tenant_id
        ):
            time.sleep(0.05)  # Simulate query
            concepts_found = random.randint(3, 10)
            logger.info(f"Database query returned {concepts_found} concepts")

        # Simulate context building
        time.sleep(0.02)

        # Enrich span with results
        enrich_span_with_recall_results(
            concepts_found=concepts_found,
            relationships_found=random.randint(5, 20),
            query_time_ms=70.0,
        )

        # Simulate caching result
        with trace_cache_operation("SET", cache_key, tenant_id):
            time.sleep(0.005)

        logger.info("Memory recall completed", extra={
            "concepts_found": concepts_found,
        })


def simulate_memory_learn(logger):
    """Simulate a memory learning operation"""
    user_msg = "How does distributed tracing work?"
    ai_msg = "Distributed tracing tracks requests across services using trace context propagation..."
    tenant_id = get_baggage("tenant_id")

    with trace_learn(len(user_msg), len(ai_msg), tenant_id) as span:
        logger.info("Starting memory learn")

        # Simulate concept extraction
        time.sleep(0.03)
        concepts_extracted = random.randint(3, 8)
        logger.info(f"Extracted {concepts_extracted} concepts")

        # Simulate decision detection
        time.sleep(0.02)
        decisions_detected = random.randint(0, 2)

        # Simulate graph link creation
        with trace_query(
            "INSERT INTO attention_links ...",
            "INSERT",
            "attention_links",
            tenant_id
        ):
            time.sleep(0.04)
            links_created = random.randint(5, 15)

        # Enrich span with results
        enrich_span_with_learn_results(
            concepts_extracted=concepts_extracted,
            decisions_detected=decisions_detected,
            links_created=links_created,
            compounds_found=random.randint(0, 3),
        )

        logger.info("Memory learn completed", extra={
            "concepts": concepts_extracted,
            "links": links_created,
        })


if __name__ == "__main__":
    main()
