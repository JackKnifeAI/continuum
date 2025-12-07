## CONTINUUM Observability

Comprehensive OpenTelemetry-based distributed tracing, metrics, and logging for CONTINUUM AI memory infrastructure.

## Features

### Distributed Tracing
- **End-to-end request tracing** across API, database, cache, federation, and memory layers
- **Auto-instrumentation** for FastAPI, SQLAlchemy, Redis, httpx
- **Custom spans** for business logic with semantic attributes
- **Trace context propagation** across service boundaries using W3C TraceContext
- **Multiple exporters**: Jaeger, Zipkin, OTLP (Grafana Tempo), Datadog, Console

### Metrics
- **Request metrics**: Total requests, duration histograms, error counts
- **Memory metrics**: Recall/learn operations, entity counts, graph statistics
- **Cache metrics**: Hit/miss ratios, operation latencies
- **Federation metrics**: Sync operations, peer connections, conflicts
- **Database metrics**: Query duration, slow queries, connection pool stats

### Logging
- **Structured logging** with JSON output
- **Automatic trace context injection** (trace_id, span_id)
- **Log correlation** with traces
- **Span event integration** for timeline visualization

### Sampling Strategies
- **Always-on**: Development mode
- **Ratio-based**: Sample X% of traces
- **Error-always**: Always sample errors, probabilistically sample success
- **Rate-limited**: Cap traces per second
- **Adaptive**: Adjust sampling based on traffic

## Quick Start

### Installation

```bash
cd continuum
pip install -r continuum/observability/requirements.txt
```

### Initialize Telemetry

```python
from continuum.observability import init_telemetry

# Initialize with environment variables
init_telemetry()

# Or override settings
init_telemetry(
    service_name="continuum-api",
    exporter_type="jaeger",
    sampling_rate=0.1
)
```

### Environment Variables

```bash
# Service identification
export OTEL_SERVICE_NAME="continuum-api"
export OTEL_SERVICE_NAMESPACE="ai-memory"
export CONTINUUM_ENV="production"

# Exporter configuration
export OTEL_EXPORTER_TYPE="jaeger"  # jaeger|zipkin|otlp|datadog|console
export OTEL_ENDPOINT="http://localhost:4317"

# Sampling
export OTEL_SAMPLING_RATE="0.1"  # Sample 10% of traces
export OTEL_SAMPLE_ERRORS_ALWAYS="true"  # Always sample errors

# Propagators
export OTEL_PROPAGATORS="tracecontext,baggage"
```

### Instrument FastAPI Application

```python
from fastapi import FastAPI
from continuum.observability import init_telemetry
from continuum.observability.api_instrumentation import instrument_fastapi_app

# Initialize telemetry
init_telemetry()

# Create FastAPI app
app = FastAPI()

# Add tracing middleware
instrument_fastapi_app(app)

# Your routes automatically traced
@app.post("/v1/recall")
async def recall(request: RecallRequest):
    # Automatically traced with full context
    return response
```

### Manual Instrumentation

```python
from continuum.observability import get_tracer, trace_function

# Get a tracer
tracer = get_tracer(__name__)

# Decorator-based tracing
@trace_function(name="process_memory", attributes={"component": "memory"})
def process_memory(data):
    # Function automatically traced
    result = complex_operation(data)
    return result

# Context manager tracing
with tracer.start_as_current_span("database_query") as span:
    span.set_attribute("query_type", "select")
    span.set_attribute("table", "entities")
    results = db.query(sql)
    span.set_attribute("row_count", len(results))
```

### Memory Operations Tracing

```python
from continuum.observability.memory_instrumentation import (
    trace_recall,
    trace_learn,
    enrich_span_with_recall_results
)

# Trace recall operation
with trace_recall(query, max_concepts=10, tenant_id="user_123") as span:
    context = memory.recall(query)
    enrich_span_with_recall_results(
        concepts_found=context.concepts_found,
        relationships_found=context.relationships_found,
        query_time_ms=context.query_time_ms,
    )

# Trace learn operation
with trace_learn(len(user_msg), len(ai_msg), tenant_id="user_123") as span:
    result = memory.learn(user_msg, ai_msg)
    enrich_span_with_learn_results(
        concepts_extracted=result.concepts_extracted,
        decisions_detected=result.decisions_detected,
        links_created=result.links_created,
        compounds_found=result.compounds_found,
    )
```

### Database Instrumentation

```python
from continuum.observability.database_instrumentation import trace_query

# Trace SQL query
with trace_query(
    "SELECT * FROM entities WHERE tenant_id = ?",
    operation="SELECT",
    table="entities",
    tenant_id="user_123"
):
    cursor.execute(query, (tenant_id,))
    results = cursor.fetchall()
```

### Cache Instrumentation

```python
from continuum.observability.cache_instrumentation import (
    trace_cache_operation,
    record_cache_hit,
    record_cache_miss
)

# Trace cache operation
with trace_cache_operation("GET", key="memory:search:hash"):
    value = redis.get(key)
    if value:
        record_cache_hit(key, tenant_id="user_123")
    else:
        record_cache_miss(key, tenant_id="user_123")
```

### Context Propagation

```python
from continuum.observability.context import (
    inject_trace_context,
    extract_trace_context,
    set_baggage,
    get_baggage
)

# Inject context into HTTP headers
headers = inject_trace_context()
response = httpx.post(url, headers=headers)

# Extract context from incoming request
ctx = extract_trace_context(request.headers)

# Set baggage for cross-service context
set_baggage("tenant_id", "user_123")
set_baggage("user_type", "premium")

# Get baggage in downstream service
tenant_id = get_baggage("tenant_id")
```

### Structured Logging

```python
from continuum.observability import setup_logging, get_logger

# Setup logging with trace integration
setup_logging(level="INFO", json_output=True)

# Get logger
logger = get_logger(__name__)

# Logs automatically include trace_id and span_id
logger.info("Processing request", extra={
    "tenant_id": "user_123",
    "operation": "recall",
    "duration_ms": 123.45
})
```

## Deployment

### Run Observability Stack

```bash
cd deploy/otel
docker-compose -f docker-compose.otel.yml up -d
```

This starts:
- **Jaeger** (UI at http://localhost:16686)
- **Grafana Tempo** (alternative trace backend)
- **Grafana** (visualization at http://localhost:3000)
- **Prometheus** (metrics at http://localhost:9090)
- **OTEL Collector** (central collection point)

### Access UIs

- **Jaeger UI**: http://localhost:16686
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **OTEL Collector Health**: http://localhost:13133

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTINUUM Application                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │ Database │  │  Cache   │  │Federation│   │
│  │Instrumen-│  │Instrumen-│  │Instrumen-│  │Instrumen-│   │
│  │  tation  │  │  tation  │  │  tation  │  │  tation  │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
│        │             │              │             │         │
│        └─────────────┴──────────────┴─────────────┘         │
│                         │                                    │
│              ┌──────────▼──────────┐                        │
│              │  OpenTelemetry SDK  │                        │
│              │  - TracerProvider   │                        │
│              │  - MeterProvider    │                        │
│              │  - Propagators      │                        │
│              └──────────┬──────────┘                        │
└─────────────────────────┼─────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │   OpenTelemetry Collector      │
         │   - Receive OTLP               │
         │   - Process & Filter           │
         │   - Export to backends         │
         └────────┬──────────┬────────────┘
                  │          │
         ┌────────▼──┐   ┌───▼────────┐
         │  Jaeger   │   │   Tempo    │
         │ (Traces)  │   │ (Traces)   │
         └───────────┘   └────────────┘
                  │
         ┌────────▼──────────┐
         │    Prometheus     │
         │    (Metrics)      │
         └───────────────────┘
                  │
         ┌────────▼──────────┐
         │     Grafana       │
         │ (Visualization)   │
         └───────────────────┘
```

## Metrics Reference

### Request Metrics
- `continuum_requests_total`: Total HTTP requests (counter)
- `continuum_request_duration_seconds`: Request duration (histogram)
- `continuum_errors_total`: Total errors (counter)

### Memory Metrics
- `continuum_memory_operations_total`: Memory operations (counter)
- `continuum_memory_operation_duration_seconds`: Operation duration (histogram)
- `continuum_memory_entities_total`: Total entities (gauge)
- `continuum_memory_messages_total`: Total messages (gauge)
- `continuum_memory_decisions_total`: Total decisions (gauge)
- `continuum_memory_attention_links_total`: Total attention links (gauge)

### Cache Metrics
- `continuum_cache_hits_total`: Cache hits (counter)
- `continuum_cache_misses_total`: Cache misses (counter)
- `continuum_cache_hit_ratio`: Hit ratio 0-1 (gauge)
- `continuum_cache_operation_duration_seconds`: Operation duration (histogram)

### Federation Metrics
- `continuum_federation_active_peers`: Active peers (gauge)
- `continuum_federation_sync_success_total`: Successful syncs (counter)
- `continuum_federation_sync_errors_total`: Failed syncs (counter)
- `continuum_federation_sync_duration_seconds`: Sync duration (histogram)

### Database Metrics
- `continuum_db_query_duration_seconds`: Query duration (histogram)
- `continuum_db_slow_queries_total`: Slow queries (counter)
- `continuum_db_pool_size`: Connection pool size (gauge)
- `continuum_db_pool_active`: Active connections (gauge)

## Performance Tuning

### Sampling

For high-traffic production systems, use probabilistic sampling:

```python
init_telemetry(
    sampling_rate=0.01,  # Sample 1% of traces
    sample_errors_always=True  # But always sample errors
)
```

### Batch Export

Adjust batch settings for your throughput:

```bash
export OTEL_BSP_SCHEDULE_DELAY=5000  # 5 seconds
export OTEL_BSP_MAX_QUEUE_SIZE=2048
export OTEL_BSP_MAX_EXPORT_BATCH_SIZE=512
```

### Resource Limits

Set resource limits to prevent memory issues:

```bash
export OTEL_MAX_ATTRIBUTES_PER_SPAN=128
export OTEL_MAX_EVENTS_PER_SPAN=128
```

## Troubleshooting

### No traces appearing in Jaeger

1. Check OTEL Collector is running: `curl http://localhost:13133`
2. Check application is exporting: Look for OTLP export logs
3. Verify exporter endpoint: `echo $OTEL_ENDPOINT`
4. Check Jaeger UI: http://localhost:16686

### High memory usage

1. Reduce sampling rate: `OTEL_SAMPLING_RATE=0.01`
2. Increase batch delay: `OTEL_BSP_SCHEDULE_DELAY=10000`
3. Enable memory limiter in collector config

### Traces not propagating across services

1. Verify propagators are configured: `OTEL_PROPAGATORS=tracecontext,baggage`
2. Check headers are being injected/extracted
3. Verify both services use same propagators

## Examples

See `examples/` directory for complete examples:
- `api_tracing_example.py`: FastAPI with tracing
- `memory_tracing_example.py`: Memory operations
- `federation_tracing_example.py`: P2P sync tracing
- `custom_spans_example.py`: Manual instrumentation

## License

MIT
