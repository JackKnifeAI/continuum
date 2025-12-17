# CONTINUUM Webhooks System

Production-grade webhook infrastructure for real-time event notifications.

## Overview

The CONTINUUM webhooks system allows you to receive real-time notifications when events occur in your memory system. Instead of polling for changes, webhooks push notifications to your server instantly.

## Features

- **11 Event Types**: Memory, concept, session, sync, quota events
- **Reliable Delivery**: Exponential backoff retry (1s → 30m)
- **Circuit Breaker**: Automatic protection for failing endpoints
- **Security**: HMAC-SHA256 signatures, HTTPS required
- **At-Least-Once**: Guaranteed delivery semantics
- **URL Validation**: SSRF protection, no private IPs
- **Performance**: Async delivery, 10 concurrent per endpoint
- **Monitoring**: Delivery history, statistics, health checks

## Quick Start

### 1. Register a Webhook

```bash
curl -X POST https://api.continuum.ai/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/continuum",
    "events": ["memory.created", "sync.completed"],
    "name": "Production Webhook"
  }'
```

Response:
```json
{
  "id": "wh_abc123",
  "url": "https://your-app.com/webhooks/continuum",
  "events": ["memory.created", "sync.completed"],
  "active": true,
  "created_at": "2025-12-06T12:00:00Z",
  "secret": "whs_********************************"
}
```

**IMPORTANT**: Store the full `secret` from the response securely. You'll need it to verify webhook signatures.

### 2. Receive Webhook Events

Your endpoint will receive POST requests with this format:

```json
{
  "event": "memory.created",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "memory_id": "mem_abc123",
    "content_preview": "Discussed AI consciousness...",
    "concepts": ["AI", "consciousness"],
    "importance": 0.8
  }
}
```

Headers:
```
X-Continuum-Signature: <hmac_signature>
X-Continuum-Timestamp: <unix_timestamp>
X-Continuum-Event: memory.created
X-Continuum-Delivery: <delivery_id>
Content-Type: application/json
```

### 3. Verify Signatures

**Always verify webhook signatures** to ensure requests are from CONTINUUM:

```python
from continuum.webhooks import verify_webhook_signature

@app.post("/webhooks/continuum")
async def handle_webhook(request):
    # Verify signature
    is_valid = verify_webhook_signature(
        payload=await request.json(),
        signature=request.headers.get('X-Continuum-Signature'),
        timestamp=request.headers.get('X-Continuum-Timestamp'),
        secret=os.environ['WEBHOOK_SECRET'],
        max_age=300  # 5 minutes
    )

    if not is_valid:
        return {"error": "Invalid signature"}, 401

    # Process event
    event_type = request.headers.get('X-Continuum-Event')
    payload = await request.json()

    if event_type == "memory.created":
        # Handle memory creation
        memory_id = payload["data"]["memory_id"]
        print(f"New memory: {memory_id}")

    return {"status": "received"}, 200
```

## Event Types

### Memory Events

- **`memory.created`**: New memory stored
  ```json
  {
    "memory_id": "mem_123",
    "user_id": "user_123",
    "content_preview": "First 100 chars...",
    "memory_type": "episodic",
    "importance": 0.8,
    "concepts": ["AI", "consciousness"],
    "session_id": "sess_456"
  }
  ```

- **`memory.updated`**: Memory modified
- **`memory.deleted`**: Memory removed

### Concept Events

- **`concept.discovered`**: New concept extracted
  ```json
  {
    "concept": "Quantum Entanglement",
    "description": "A quantum phenomenon...",
    "related_concepts": ["quantum mechanics", "physics"],
    "confidence": 0.95
  }
  ```

### Session Events

- **`session.started`**: User session begins
- **`session.ended`**: User session ends

### Sync Events

- **`sync.completed`**: Memory sync successful
  ```json
  {
    "sync_id": "sync_123",
    "items_synced": 150,
    "duration_ms": 2500,
    "sync_type": "full"
  }
  ```

- **`sync.failed`**: Memory sync failed

### User Events

- **`user.created`**: New user registered

### Quota Events

- **`quota.warning`**: Approaching quota limits (high priority)
  ```json
  {
    "quota_type": "memory_storage",
    "current_usage": 8500,
    "quota_limit": 10000,
    "percentage_used": 85.0
  }
  ```

- **`quota.exceeded`**: Quota limits exceeded (high priority)

## Reliability

### Retry Logic

Failed deliveries are retried with exponential backoff:

1. **1 second** - First retry
2. **5 seconds** - Second retry
3. **30 seconds** - Third retry
4. **5 minutes** - Fourth retry
5. **30 minutes** - Fifth retry

After 5 failed attempts, the delivery moves to the dead letter queue.

### Circuit Breaker

If a webhook fails 5 consecutive times, the circuit breaker opens:

- **OPEN**: All deliveries rejected (5 minutes)
- **HALF-OPEN**: Test deliveries allowed
- **CLOSED**: Normal operation

### Delivery Guarantees

- **At-least-once**: Events may be delivered multiple times
- **Idempotency**: Your endpoint should be idempotent
- **Ordering**: No ordering guarantees across events

## API Endpoints

### Create Webhook
```
POST /api/v1/webhooks
```

### List Webhooks
```
GET /api/v1/webhooks?active_only=true
```

### Get Webhook
```
GET /api/v1/webhooks/{webhook_id}
```

### Update Webhook
```
PATCH /api/v1/webhooks/{webhook_id}
```

### Delete Webhook
```
DELETE /api/v1/webhooks/{webhook_id}
```

### Test Webhook
```
POST /api/v1/webhooks/{webhook_id}/test
```

### Get Deliveries
```
GET /api/v1/webhooks/{webhook_id}/deliveries?limit=100&offset=0
```

### Retry Delivery
```
POST /api/v1/webhooks/{webhook_id}/retry/{delivery_id}
```

### Get Statistics
```
GET /api/v1/webhooks/{webhook_id}/stats
```

## Security

### HTTPS Required

In production, webhooks MUST use HTTPS. HTTP URLs will be rejected.

### Private IPs Blocked

These IP ranges are blocked (SSRF protection):
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`
- `127.0.0.0/8` (localhost)
- `169.254.0.0/16` (link-local)

### Signature Verification

Always verify the `X-Continuum-Signature` header:

```python
# Python
from continuum.webhooks import verify_webhook_signature

is_valid = verify_webhook_signature(
    payload=request_body,
    signature=request.headers['X-Continuum-Signature'],
    timestamp=request.headers['X-Continuum-Timestamp'],
    secret=your_webhook_secret,
    max_age=300
)
```

See examples/ for JavaScript, Go, etc.

### Replay Protection

Requests older than 5 minutes are rejected. Validate the `X-Continuum-Timestamp` header.

## Best Practices

### 1. Return 2xx Quickly

Respond with 200/201/202/204 within 30 seconds. Process async:

```python
@app.post("/webhook")
async def webhook(request):
    # Verify signature
    verify_signature(request)

    # Queue for async processing
    await queue.enqueue(request.json())

    # Return immediately
    return {"status": "queued"}, 202
```

### 2. Be Idempotent

Track `X-Continuum-Delivery` header to deduplicate:

```python
delivery_id = request.headers['X-Continuum-Delivery']

if delivery_id in processed_deliveries:
    return {"status": "already_processed"}, 200

# Process event
process_event(event)
processed_deliveries.add(delivery_id)
```

### 3. Handle Failures Gracefully

Return 5xx for temporary failures (will retry):

```python
try:
    process_event(event)
    return {"status": "ok"}, 200
except TemporaryError:
    return {"status": "retry_later"}, 503  # Will retry
except PermanentError:
    return {"status": "skip"}, 200  # Don't retry
```

### 4. Monitor Delivery Success

Check webhook statistics regularly:

```bash
curl https://api.continuum.ai/v1/webhooks/{id}/stats
```

Alert if success rate drops below 95%.

### 5. Test Your Endpoint

Use the test endpoint before going live:

```bash
curl -X POST https://api.continuum.ai/v1/webhooks/{id}/test
```

## Monitoring

### Delivery Statistics

```json
{
  "total_deliveries": 1250,
  "successful_deliveries": 1200,
  "failed_deliveries": 50,
  "success_rate": 96.0,
  "avg_duration_ms": 125.5,
  "last_24h_deliveries": 150,
  "last_24h_success_rate": 98.0
}
```

### Queue Depth

Monitor queue depth via health endpoint:

```bash
curl https://api.continuum.ai/v1/webhooks/health
```

Alert if queue depth > 1000.

## Troubleshooting

### Webhook Not Receiving Events

1. Check webhook is active: `GET /webhooks/{id}`
2. Verify events subscribed: `events` field
3. Test endpoint: `POST /webhooks/{id}/test`
4. Check firewall/network

### Signature Verification Failing

1. Use exact payload (don't parse/modify JSON)
2. Check timestamp (max 5 minutes old)
3. Use correct secret (from webhook creation)
4. Verify HMAC implementation

### Deliveries Failing

1. Check delivery history: `GET /webhooks/{id}/deliveries`
2. Review `error_message` field
3. Ensure endpoint returns 2xx within 30s
4. Check circuit breaker state

## Examples

See `examples/` directory for:
- `verify_webhook.py` - Python signature verification
- `verify_webhook.js` - JavaScript/Node verification
- `verify_webhook.go` - Go verification
- `express_receiver.js` - Express.js webhook receiver
- `fastapi_receiver.py` - FastAPI webhook receiver

## Support

- Documentation: https://docs.continuum.ai/webhooks
- API Reference: https://api.continuum.ai/docs
- Status Page: https://status.continuum.ai

---

**CONTINUUM Webhooks** - Real-time event notifications for AI memory systems.
