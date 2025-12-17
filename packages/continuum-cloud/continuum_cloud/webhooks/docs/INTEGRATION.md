# Webhook Integration Guide

How to integrate CONTINUUM webhooks into your application.

## Overview

Webhooks allow CONTINUUM to push real-time notifications to your application when events occur. Instead of polling for changes, you receive instant notifications.

## Integration Steps

### 1. Create Webhook Endpoint

First, create an HTTP endpoint in your application to receive webhooks:

```python
# FastAPI example
from fastapi import FastAPI, Request, HTTPException
from continuum.webhooks import verify_webhook_signature
import os

app = FastAPI()

@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    # Get signature headers
    signature = request.headers.get('x-continuum-signature')
    timestamp = request.headers.get('x-continuum-timestamp')

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature")

    # Get payload
    payload = await request.json()

    # IMPORTANT: Verify signature
    is_valid = verify_webhook_signature(
        payload=payload,
        signature=signature,
        timestamp=timestamp,
        secret=os.environ['CONTINUUM_WEBHOOK_SECRET']
    )

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process event
    event_type = request.headers.get('x-continuum-event')
    await process_event(event_type, payload)

    return {"status": "received"}
```

### 2. Register Webhook

Register your endpoint with CONTINUUM:

```python
import httpx

response = httpx.post(
    "https://api.continuum.ai/v1/webhooks",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "url": "https://your-app.com/webhooks/continuum",
        "events": [
            "memory.created",
            "memory.updated",
            "sync.completed"
        ],
        "name": "Production Webhook"
    }
)

webhook = response.json()
print(f"Webhook ID: {webhook['id']}")
print(f"Secret: {webhook['secret']}")  # Store this securely!
```

**IMPORTANT**: Save the `secret` from the response. You'll need it to verify signatures. Store it securely (environment variable, secrets manager, etc.).

### 3. Test Webhook

Test your endpoint before going live:

```bash
curl -X POST https://api.continuum.ai/v1/webhooks/{webhook_id}/test \
  -H "Authorization: Bearer YOUR_API_KEY"
```

You should receive a test event at your endpoint:

```json
{
  "event": "webhook.test",
  "timestamp": "2025-12-06T12:00:00Z",
  "data": {
    "message": "This is a test webhook from CONTINUUM",
    "webhook_id": "wh_abc123"
  }
}
```

### 4. Handle Events

Process different event types:

```python
async def process_event(event_type: str, payload: dict):
    """Process webhook events."""

    if event_type == "memory.created":
        await handle_memory_created(payload)

    elif event_type == "concept.discovered":
        await handle_concept_discovered(payload)

    elif event_type == "sync.completed":
        await handle_sync_completed(payload)

    elif event_type == "quota.warning":
        await handle_quota_warning(payload)

    else:
        print(f"Unknown event: {event_type}")


async def handle_memory_created(payload: dict):
    """Handle memory.created event."""
    data = payload["data"]

    memory_id = data["memory_id"]
    concepts = data["concepts"]
    importance = data["importance"]

    print(f"New memory: {memory_id}")
    print(f"Concepts: {concepts}")
    print(f"Importance: {importance}")

    # Your application logic
    await save_to_database(memory_id, concepts)
    await send_notification(f"New memory with concepts: {concepts}")


async def handle_quota_warning(payload: dict):
    """Handle quota.warning event (high priority)."""
    data = payload["data"]

    quota_type = data["quota_type"]
    percentage = data["percentage_used"]

    # Alert team
    await send_alert(
        f"Quota warning: {quota_type} at {percentage}%"
    )
```

## Best Practices

### 1. Return 2xx Quickly

Your webhook endpoint should return a 2xx status code within 30 seconds. For long-running operations, queue the work:

```python
from celery import Celery

celery = Celery('tasks')

@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    # Verify signature...

    # Queue for background processing
    celery.send_task('process_webhook', args=[payload])

    # Return immediately
    return {"status": "queued"}, 202


@celery.task
def process_webhook(payload):
    """Background task to process webhook."""
    # Heavy processing here
    pass
```

### 2. Be Idempotent

CONTINUUM delivers webhooks **at-least-once**, meaning you may receive the same event multiple times. Track delivery IDs to deduplicate:

```python
# Redis example
import redis

r = redis.Redis()

@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    delivery_id = request.headers.get('x-continuum-delivery')

    # Check if already processed
    if r.exists(f"webhook:{delivery_id}"):
        return {"status": "already_processed"}, 200

    # Process event
    await process_event(...)

    # Mark as processed (expire after 7 days)
    r.setex(f"webhook:{delivery_id}", 604800, "1")

    return {"status": "received"}, 200
```

### 3. Handle Failures Gracefully

Return appropriate status codes:

- **2xx**: Success (won't retry)
- **5xx**: Temporary failure (will retry)
- **4xx**: Permanent failure (won't retry)

```python
@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    try:
        await process_event(...)
        return {"status": "ok"}, 200

    except TemporaryDatabaseError:
        # Database is down - retry later
        return {"status": "retry_later"}, 503

    except InvalidDataError:
        # Bad data - don't retry
        return {"status": "invalid_data"}, 400
```

### 4. Secure Your Endpoint

**Always verify signatures**:

```python
from continuum.webhooks import verify_webhook_signature

is_valid = verify_webhook_signature(
    payload=request.json(),
    signature=request.headers['X-Continuum-Signature'],
    timestamp=request.headers['X-Continuum-Timestamp'],
    secret=os.environ['WEBHOOK_SECRET'],
    max_age=300  # Reject requests older than 5 minutes
)

if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid signature")
```

**Additional security**:
- Use HTTPS (required in production)
- Validate payload structure
- Rate limit your endpoint
- Monitor for suspicious activity

### 5. Monitor Delivery Success

Regularly check webhook statistics:

```python
response = httpx.get(
    f"https://api.continuum.ai/v1/webhooks/{webhook_id}/stats",
    headers={"Authorization": f"Bearer {api_key}"}
)

stats = response.json()
success_rate = stats["success_rate"]

if success_rate < 95.0:
    # Alert team - webhook failing
    send_alert(f"Webhook success rate: {success_rate}%")
```

## Production Deployment

### Environment Variables

```bash
# Required
CONTINUUM_WEBHOOK_SECRET=whs_your_secret_here

# Optional
WEBHOOK_TIMEOUT=30
WEBHOOK_QUEUE_NAME=webhooks
```

### Health Checks

Add a health check endpoint:

```python
@app.get("/health")
async def health_check():
    # Check dependencies
    db_ok = await check_database()
    queue_ok = await check_queue()

    if not (db_ok and queue_ok):
        return {"status": "unhealthy"}, 503

    return {"status": "healthy"}, 200
```

### Monitoring

Monitor these metrics:

- **Delivery success rate**: Should be > 95%
- **Response time**: Should be < 1 second
- **Queue depth**: Alert if > 1000
- **Error rate**: Alert if > 5%

### Example Monitoring

```python
from prometheus_client import Counter, Histogram

webhook_requests = Counter(
    'webhook_requests_total',
    'Total webhook requests',
    ['event_type', 'status']
)

webhook_duration = Histogram(
    'webhook_duration_seconds',
    'Webhook processing duration'
)

@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    event_type = request.headers.get('x-continuum-event')

    with webhook_duration.time():
        try:
            await process_event(...)
            webhook_requests.labels(event_type, 'success').inc()
            return {"status": "ok"}, 200

        except Exception as e:
            webhook_requests.labels(event_type, 'error').inc()
            raise
```

## Troubleshooting

### Webhooks Not Arriving

1. **Check webhook is active**:
   ```bash
   curl https://api.continuum.ai/v1/webhooks/{id}
   ```

2. **Test the webhook**:
   ```bash
   curl -X POST https://api.continuum.ai/v1/webhooks/{id}/test
   ```

3. **Check delivery history**:
   ```bash
   curl https://api.continuum.ai/v1/webhooks/{id}/deliveries
   ```

4. **Verify firewall/network**: Ensure CONTINUUM can reach your endpoint

### Signature Verification Failing

1. Use the exact payload (don't parse/modify)
2. Check timestamp is recent (< 5 minutes)
3. Use the correct secret from webhook creation
4. Verify HMAC-SHA256 implementation

### High Failure Rate

1. **Check response time**: Must respond within 30 seconds
2. **Return 2xx**: Even if queuing for later
3. **Check error logs**: Review `error_message` in deliveries
4. **Verify dependencies**: Database, queue, external APIs

## Migration Guide

### From Polling to Webhooks

**Before** (polling):
```python
while True:
    memories = get_new_memories()
    for memory in memories:
        process_memory(memory)
    time.sleep(60)  # Poll every minute
```

**After** (webhooks):
```python
@app.post("/webhooks/continuum")
async def handle_webhook(request: Request):
    # Process immediately
    await process_memory(payload["data"])
    return {"status": "ok"}
```

**Benefits**:
- Real-time notifications (vs 1 minute delay)
- Reduced API calls
- Lower latency
- Better resource utilization

## Support

- Documentation: https://docs.continuum.ai
- API Reference: https://api.continuum.ai/docs
- Examples: https://github.com/continuum/examples
- Support: support@continuum.ai

---

**Next Steps**: Check out [SECURITY.md](SECURITY.md) for security best practices.
