# Sentry Integration Guide for CONTINUUM

Quick reference for adding Sentry monitoring to CONTINUUM components.

## Basic Error Capture

### In API Routes

```python
from continuum.core.sentry_integration import (
    capture_exception,
    set_user_context,
    set_operation_context,
    add_breadcrumb,
)

@router.post("/v1/recall")
async def recall(request: RecallRequest):
    # Set context
    set_user_context(tenant_id=request.tenant_id)
    set_operation_context(operation="recall")

    try:
        # Add breadcrumb
        add_breadcrumb(
            message="Starting recall operation",
            category="memory",
            level="info",
            data={"query_length": len(request.query)},
        )

        # Your logic here
        result = await perform_recall(request)

        return result

    except Exception as e:
        # Capture error (automatically sent to Sentry)
        capture_exception(
            e,
            level="error",
            extra={
                "query": request.query[:100],  # Truncated
                "tenant_id": request.tenant_id,
            },
            tags={
                "operation": "recall",
                "model_type": request.model_type,
            },
        )
        raise
```

### In CLI Commands

```python
from continuum.core.sentry_integration import capture_exception, is_enabled

def search_command(query, config, use_color):
    try:
        # Your logic
        results = search(query)
        return results

    except Exception as e:
        if is_enabled():
            capture_exception(
                e,
                level="error",
                tags={"cli_command": "search"},
            )

        # Still raise for CLI error handling
        raise
```

### In Background Tasks

```python
from continuum.core.sentry_integration import capture_exception

async def sync_task(tenant_id):
    try:
        # Background work
        await sync_with_federation(tenant_id)

    except Exception as e:
        # Capture but don't raise (background task)
        capture_exception(
            e,
            level="error",
            tags={
                "background_task": "sync",
                "tenant_id": tenant_id,
            },
        )
```

## Performance Monitoring

### Using Context Manager

```python
from continuum.core.sentry_integration import PerformanceTransaction

async def recall(query: str):
    with PerformanceTransaction("memory.recall", "Semantic search recall") as txn:
        # Main operation
        with txn.start_span("database.query", "Query embeddings"):
            embeddings = await db.query_embeddings(query)

        with txn.start_span("graph.traverse", "Traverse knowledge graph"):
            results = await graph.traverse(embeddings)

        with txn.start_span("format.response", "Format response"):
            return format_results(results)
```

### Using Decorator

```python
from continuum.core.sentry_integration import monitor_performance

@monitor_performance("memory.learn", "Extract concepts from conversation")
async def learn(conversation):
    # Your logic here
    concepts = extract_concepts(conversation)
    await store_concepts(concepts)
    return concepts
```

## Breadcrumbs for Debugging

Add breadcrumbs throughout your code to create a debug trail:

```python
from continuum.core.sentry_integration import add_breadcrumb

async def complex_operation(data):
    add_breadcrumb("Starting complex operation", category="app", level="info")

    # Step 1
    add_breadcrumb("Validating input", category="validation", level="info",
                   data={"size": len(data)})
    validate(data)

    # Step 2
    add_breadcrumb("Processing data", category="processing", level="info")
    processed = process(data)

    # Step 3
    add_breadcrumb("Storing results", category="storage", level="info",
                   data={"count": len(processed)})
    await store(processed)

    add_breadcrumb("Operation completed", category="app", level="info")
```

## User Context

Set user context at the beginning of requests:

```python
from continuum.core.sentry_integration import set_user_context

# In middleware or request handler
set_user_context(
    tenant_id="user_123",        # Automatically hashed for privacy
    instance_id="claude-001",
    anonymize=True,              # Default: True
)
```

## Custom Tags

Use custom tags for filtering in Sentry:

```python
from continuum.core.sentry_integration import set_operation_context

set_operation_context(
    operation="sync",
    model_type="claude-opus-4.5",
    memory_operation="concept_extraction",
    federation_peer="peer-alpha",
    # Add any custom tags
    region="us-east-1",
    shard_id="shard-42",
)
```

## Memory Operation Errors

For memory-specific errors, use the dedicated helper:

```python
from continuum.core.sentry_integration import capture_memory_error

try:
    result = await recall(query)
except Exception as e:
    capture_memory_error(
        e,
        operation="recall",
        tenant_id=tenant_id,
        instance_id=instance_id,
        query=query[:100],      # Truncated
        num_results=0,
    )
    raise
```

## Checking if Sentry is Enabled

Before adding expensive operations:

```python
from continuum.core.sentry_integration import is_enabled

if is_enabled():
    # Only compute if Sentry is active
    detailed_context = compute_expensive_context()
    capture_exception(e, extra={"context": detailed_context})
else:
    # Fallback
    capture_exception(e)
```

## Flushing Events

Before shutdown, flush pending events:

```python
from continuum.core.sentry_integration import flush, close

# At shutdown
flush(timeout=5.0)
close()
```

## Common Patterns

### API Endpoint Pattern

```python
from continuum.core.sentry_integration import (
    set_user_context,
    set_operation_context,
    add_breadcrumb,
    capture_exception,
    PerformanceTransaction,
)

@router.post("/v1/operation")
async def operation_endpoint(request: OperationRequest):
    # Set context
    set_user_context(tenant_id=request.tenant_id)
    set_operation_context(operation="operation_name")

    # Monitor performance
    with PerformanceTransaction("api.operation", request.tenant_id):
        try:
            # Add breadcrumbs
            add_breadcrumb("Validating request", category="validation")
            validate_request(request)

            add_breadcrumb("Processing", category="business_logic")
            result = await process(request)

            add_breadcrumb("Success", category="response")
            return result

        except ValidationError as e:
            add_breadcrumb("Validation failed", category="error", level="error")
            capture_exception(e, level="warning")  # Lower severity
            raise HTTPException(400, str(e))

        except Exception as e:
            add_breadcrumb("Operation failed", category="error", level="error")
            capture_exception(e, level="error")
            raise HTTPException(500, "Internal error")
```

### Database Operation Pattern

```python
from continuum.core.sentry_integration import (
    add_breadcrumb,
    capture_exception,
    monitor_performance,
)

@monitor_performance("database.insert_concepts")
async def insert_concepts(concepts, session):
    try:
        add_breadcrumb(
            "Inserting concepts",
            category="database",
            data={"count": len(concepts)},
        )

        # Your DB logic
        result = await session.execute(...)

        return result

    except OperationalError as e:
        # Database-specific error
        capture_exception(
            e,
            level="error",
            tags={
                "database_operation": "insert_concepts",
                "error_type": "operational",
            },
        )
        raise
```

### Background Job Pattern

```python
from continuum.core.sentry_integration import (
    set_user_context,
    add_breadcrumb,
    capture_exception,
    PerformanceTransaction,
)

async def background_sync_job(tenant_id):
    set_user_context(tenant_id=tenant_id)

    with PerformanceTransaction("background.sync", tenant_id):
        try:
            add_breadcrumb("Starting sync", category="background")

            # Your logic
            await sync_data(tenant_id)

            add_breadcrumb("Sync complete", category="background")

        except Exception as e:
            add_breadcrumb("Sync failed", category="error", level="error")

            # Don't raise (background job)
            capture_exception(
                e,
                level="error",
                tags={"background_job": "sync"},
            )
```

## Best Practices

1. **Set context early**: Call `set_user_context()` and `set_operation_context()` at the start of operations

2. **Use breadcrumbs liberally**: They help debug issues - add them at key points

3. **Capture with appropriate severity**:
   - `level="fatal"`: System-critical errors
   - `level="error"`: Unexpected errors (default)
   - `level="warning"`: Expected but notable errors (validation, etc.)
   - `level="info"`: Important events (not errors)

4. **Tag strategically**: Use tags for filtering, not for unique values
   - Good: `operation="recall"`, `model_type="claude"`
   - Bad: `query="user's exact query"` (use extra instead)

5. **Truncate sensitive data**: Always truncate or hash before sending
   ```python
   capture_exception(e, extra={
       "query": query[:100],  # Truncate
       "tenant_id_hash": hash_tenant_id(tenant_id),  # Hash
   })
   ```

6. **Don't over-capture**: Avoid capturing expected errors repeatedly
   ```python
   # Bad: Captures on every cache miss
   try:
       return cache.get(key)
   except CacheMiss as e:
       capture_exception(e)  # DON'T DO THIS
       return None

   # Good: Only capture unexpected errors
   try:
       return cache.get(key)
   except CacheMiss:
       return None  # Expected
   except RedisError as e:
       capture_exception(e)  # Unexpected
       return None
   ```

7. **Use performance monitoring selectively**: Track key operations, not everything
   - Track: API endpoints, database queries, external calls
   - Don't track: Internal helpers, getters/setters

8. **Flush on shutdown**: Always flush before process exit
   ```python
   from continuum.core.sentry_integration import close

   # At shutdown
   close()  # Flushes with 5s timeout
   ```

## Testing

### Disable Sentry in Tests

```python
# In test setup
import os
os.environ.pop("SENTRY_DSN", None)  # Disable Sentry

# Or mock it
from unittest.mock import patch

@patch('continuum.core.sentry_integration.capture_exception')
def test_error_handling(mock_capture):
    # Your test
    trigger_error()

    # Verify capture was called
    mock_capture.assert_called_once()
```

### Test Sentry Integration

```python
from continuum.core.sentry_integration import init_sentry, is_enabled

def test_sentry_integration():
    # Initialize with test DSN
    os.environ["SENTRY_DSN"] = "https://test@o123.ingest.sentry.io/456"

    success = init_sentry()
    assert success
    assert is_enabled()
```

## Troubleshooting

### Events Not Appearing

1. Check DSN is set: `echo $SENTRY_DSN`
2. Check SDK installed: `pip show sentry-sdk`
3. Check initialization: Look for "Sentry initialized" in logs
4. Check sampling: Set `sample_rate=1.0`
5. Flush before exit: Call `close()` or `flush()`

### Too Many Events

1. Reduce sampling: `sample_rate=0.1` (10%)
2. Ignore expected errors: Add to `should_ignore_error()`
3. Use rate limiting in Sentry UI

### Missing Context

1. Call `set_user_context()` early
2. Call `set_operation_context()` early
3. Add breadcrumbs throughout code
4. Include `extra` data in `capture_exception()`

---

For more details, see:
- Main documentation: `deploy/sentry/README.md`
- Integration code: `continuum/core/sentry_integration.py`
- Sentry docs: https://docs.sentry.io/platforms/python/
