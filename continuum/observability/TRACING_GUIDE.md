# CONTINUUM Tracing Guide

Comprehensive guide for adding distributed tracing to CONTINUUM code.

## Table of Contents

1. [Adding Spans to Your Code](#adding-spans-to-your-code)
2. [Span Attributes](#span-attributes)
3. [Error Handling](#error-handling)
4. [Context Propagation](#context-propagation)
5. [Best Practices](#best-practices)
6. [Common Patterns](#common-patterns)

## Adding Spans to Your Code

### Method 1: Decorator-based (Recommended for Functions)

```python
from continuum.observability import trace_function

@trace_function(
    name="calculate_embedding",
    attributes={"component": "memory", "model": "text-embedding-ada-002"}
)
def calculate_embedding(text: str) -> List[float]:
    # Function automatically traced
    embedding = model.encode(text)
    return embedding
```

**When to use**: Regular functions that you want to trace consistently.

### Method 2: Context Manager (Recommended for Code Blocks)

```python
from continuum.observability import get_tracer

tracer = get_tracer(__name__)

def process_memory(data):
    with tracer.start_as_current_span("process_memory") as span:
        # Add attributes
        span.set_attribute("data_size", len(data))
        span.set_attribute("tenant_id", data.get("tenant_id"))

        # Your code
        result = complex_operation(data)

        # Add result attributes
        span.set_attribute("result_count", len(result))

        return result
```

**When to use**:
- Code blocks within larger functions
- When you need dynamic span attributes
- When you want fine-grained control

### Method 3: Layer-Specific Context Managers

```python
# Memory layer
from continuum.observability.memory_instrumentation import trace_recall, trace_learn

with trace_recall(query, max_concepts=10, tenant_id="user_123") as span:
    context = memory.recall(query)
    span.set_attribute("concepts_found", context.concepts_found)

# Database layer
from continuum.observability.database_instrumentation import trace_query

with trace_query("SELECT * FROM entities", "SELECT", "entities"):
    results = cursor.execute(query).fetchall()

# Cache layer
from continuum.observability.cache_instrumentation import trace_cache_operation

with trace_cache_operation("GET", key, tenant_id):
    value = redis.get(key)
```

**When to use**: Operations in specific layers (API, database, cache, memory, federation).

## Span Attributes

### Semantic Conventions

Use OpenTelemetry semantic conventions when possible:

```python
from opentelemetry.semconv.trace import SpanAttributes

span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
span.set_attribute(SpanAttributes.HTTP_URL, str(request.url))
span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
span.set_attribute(SpanAttributes.DB_SYSTEM, "sqlite")
span.set_attribute(SpanAttributes.DB_OPERATION, "SELECT")
```

### Custom Attributes

Add domain-specific attributes:

```python
# Memory operations
span.set_attribute("memory.operation", "recall")
span.set_attribute("memory.concepts_found", 5)
span.set_attribute("memory.query_time_ms", 123.45)

# Tenant context
span.set_attribute("tenant.id", "user_123")
span.set_attribute("tenant.tier", "premium")

# Business metrics
span.set_attribute("cost.tokens_used", 150)
span.set_attribute("cost.api_calls", 3)
```

### Attribute Guidelines

1. **Use dots for namespacing**: `memory.operation`, `cache.key_pattern`
2. **Use lowercase with underscores**: `concepts_found`, `query_time_ms`
3. **Be specific**: `http.request.body.size` not just `size`
4. **Sanitize sensitive data**: Never include passwords, API keys, PII
5. **Keep cardinality low**: Avoid high-cardinality values like UUIDs in tags

## Error Handling

### Recording Exceptions

```python
from opentelemetry.trace import Status, StatusCode

tracer = get_tracer(__name__)

with tracer.start_as_current_span("risky_operation") as span:
    try:
        result = might_fail()
        span.set_status(Status(StatusCode.OK))
    except ValueError as e:
        # Record exception in span
        span.record_exception(e)

        # Set error status
        span.set_status(Status(StatusCode.ERROR, str(e)))

        # Re-raise or handle
        raise
```

### Automatic Exception Recording

The `trace_function` decorator automatically records exceptions:

```python
@trace_function(record_exception=True)  # Default
def might_fail():
    if random.random() < 0.1:
        raise ValueError("Random failure!")
    return "success"
```

### Custom Error Attributes

```python
except CustomError as e:
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR, str(e)))

    # Add custom error attributes
    span.set_attribute("error.type", "business_logic_error")
    span.set_attribute("error.severity", "high")
    span.set_attribute("error.recoverable", False)
```

## Context Propagation

### HTTP Requests (Outgoing)

```python
from continuum.observability.context import inject_trace_context
import httpx

# Inject trace context into headers
headers = inject_trace_context()
response = httpx.post(
    "http://peer-service/sync",
    json=data,
    headers=headers
)
```

### HTTP Requests (Incoming)

```python
from continuum.observability.context import extract_trace_context
from fastapi import Request

@app.post("/sync")
async def sync_endpoint(request: Request):
    # Extract trace context from headers
    ctx = extract_trace_context(dict(request.headers))

    # New spans will be children of the remote span
    with tracer.start_as_current_span("sync_data", context=ctx):
        result = sync_data()

    return result
```

### Message Queues

```python
from continuum.observability.context import (
    propagate_context_to_dict,
    extract_context_from_dict
)

# Producer: Inject context into message
message = {
    "event_type": "memory_added",
    "data": {...}
}
message = propagate_context_to_dict(message)
queue.send(message)

# Consumer: Extract context from message
message = queue.receive()
ctx = extract_context_from_dict(message)

with tracer.start_as_current_span("process_message", context=ctx):
    process_message(message)
```

### Baggage (User Context)

```python
from continuum.observability.context import set_baggage, get_baggage

# Set baggage at entry point
set_baggage("tenant_id", "user_123")
set_baggage("user_tier", "premium")
set_baggage("request_id", str(uuid.uuid4()))

# Baggage automatically propagates to all child spans and downstream services

# Retrieve baggage anywhere in call stack
tenant_id = get_baggage("tenant_id")
logger.info(f"Processing for tenant: {tenant_id}")
```

## Best Practices

### 1. Span Naming

**Good**:
```python
# Descriptive, hierarchical
"memory.recall"
"db.query.entities"
"cache.get.search_results"
"federation.sync.push"
```

**Bad**:
```python
# Too generic
"operation"
"process"
"query"

# Too specific (high cardinality)
f"query_for_user_{user_id}"
f"recall_at_{timestamp}"
```

### 2. Span Granularity

**Too Coarse** (not useful):
```python
with tracer.start_as_current_span("process_request"):
    # Entire request handler - too much in one span
    authenticate()
    recall_memory()
    generate_response()
    learn_from_response()
    return response
```

**Too Fine** (too much overhead):
```python
with tracer.start_as_current_span("add_numbers"):
    result = a + b  # Don't trace trivial operations
```

**Just Right**:
```python
with tracer.start_as_current_span("recall_memory") as span:
    # Meaningful unit of work
    with tracer.start_as_current_span("query_database"):
        concepts = db.query()

    with tracer.start_as_current_span("build_context"):
        context = build_context(concepts)

    return context
```

### 3. Span Lifecycle

```python
# ✅ GOOD: Use context managers
with tracer.start_as_current_span("operation"):
    do_work()

# ❌ BAD: Manual span management (error-prone)
span = tracer.start_span("operation")
try:
    do_work()
finally:
    span.end()  # Easy to forget!
```

### 4. Async Code

```python
# Works automatically with async/await
@trace_function()
async def async_operation():
    result = await async_call()
    return result

# Or with context manager
async def process():
    with tracer.start_as_current_span("async_process"):
        result = await async_operation()
```

### 5. Sampling Awareness

```python
from continuum.observability import get_current_span

def expensive_to_compute():
    span = get_current_span()

    # Only compute expensive attributes if span is being sampled
    if span.is_recording():
        span.set_attribute("expensive_metric", compute_expensive_metric())
```

## Common Patterns

### Pattern 1: Database Query

```python
from continuum.observability.database_instrumentation import trace_query

def get_entities(tenant_id: str, limit: int = 100):
    query = "SELECT * FROM entities WHERE tenant_id = ? LIMIT ?"

    with trace_query(query, "SELECT", "entities", tenant_id) as span:
        cursor.execute(query, (tenant_id, limit))
        results = cursor.fetchall()

        # Enrich span with results
        span.set_attribute("row_count", len(results))

        return results
```

### Pattern 2: Cache Check with Fallback

```python
from continuum.observability.cache_instrumentation import (
    trace_cache_operation,
    record_cache_hit,
    record_cache_miss
)

def get_search_results(query: str, tenant_id: str):
    cache_key = f"search:{hash(query)}"

    # Try cache first
    with trace_cache_operation("GET", cache_key, tenant_id):
        cached = redis.get(cache_key)
        if cached:
            record_cache_hit(cache_key, tenant_id)
            return json.loads(cached)
        record_cache_miss(cache_key, tenant_id)

    # Cache miss - compute and cache
    with tracer.start_as_current_span("compute_search"):
        results = expensive_search(query)

    with trace_cache_operation("SET", cache_key, tenant_id):
        redis.setex(cache_key, 300, json.dumps(results))

    return results
```

### Pattern 3: Batch Processing

```python
from continuum.observability.context import link_spans

def process_batch(items: List[Dict]):
    # Create links to parent spans of all items
    links = []
    for item in items:
        if "trace_context" in item:
            link = link_spans(item["trace_context"])
            if link:
                links.append(link)

    # Create span with links to all parent contexts
    with tracer.start_as_current_span("batch_process", links=links) as span:
        span.set_attribute("batch_size", len(items))

        results = []
        for i, item in enumerate(items):
            with tracer.start_as_current_span(f"process_item_{i}"):
                result = process_item(item)
                results.append(result)

        return results
```

### Pattern 4: Retry with Tracing

```python
import time
from continuum.observability import get_current_span

def retry_with_tracing(func, max_attempts=3):
    span = get_current_span()

    for attempt in range(1, max_attempts + 1):
        try:
            span.add_event(f"attempt_{attempt}", {"attempt": attempt})
            result = func()
            span.set_attribute("attempts_used", attempt)
            return result
        except Exception as e:
            if attempt == max_attempts:
                span.record_exception(e)
                raise
            span.add_event(f"attempt_{attempt}_failed", {
                "error": str(e),
                "retry_after": 2 ** attempt
            })
            time.sleep(2 ** attempt)
```

### Pattern 5: Long-Running Background Task

```python
from continuum.observability.context import create_carrier_from_span
import asyncio

async def start_background_task(data):
    # Create span for initiating the task
    with tracer.start_as_current_span("initiate_background_task") as span:
        span.set_attribute("task_type", "memory_sync")

        # Capture trace context for background task
        carrier = create_carrier_from_span(span)

        # Pass carrier to background task
        asyncio.create_task(background_task(data, carrier))

async def background_task(data, trace_carrier):
    # Extract parent context
    ctx = extract_trace_context(trace_carrier)

    # Create child span in background task
    with tracer.start_as_current_span("background_task", context=ctx) as span:
        span.set_attribute("background", True)
        await process_async(data)
```

## Debugging Traces

### View Trace ID

```python
from continuum.observability.context import get_trace_id

trace_id = get_trace_id()
logger.info(f"Processing request", extra={"trace_id": trace_id})

# Include in API response for client-side debugging
return {
    "result": data,
    "trace_id": trace_id  # Client can search for this in Jaeger
}
```

### Force Sampling for Debugging

```python
from opentelemetry.sdk.trace.sampling import ALWAYS_ON

# Temporarily force sampling for debugging
init_telemetry(sampler=ALWAYS_ON)
```

### Console Exporter for Local Development

```bash
export OTEL_EXPORTER_TYPE=console
```

All spans will print to console - useful for debugging locally.

## Further Reading

- [OpenTelemetry Python Docs](https://opentelemetry-python.readthedocs.io/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [CONTINUUM README](./README.md)
