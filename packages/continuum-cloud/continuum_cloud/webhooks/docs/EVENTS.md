# Webhook Events Reference

Complete reference for all webhook events in CONTINUUM.

## Event Structure

All webhook events follow this structure:

```json
{
  "event": "event.type",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    // Event-specific data
  }
}
```

Headers:
```
X-Continuum-Signature: <hmac_sha256_signature>
X-Continuum-Timestamp: <unix_timestamp>
X-Continuum-Event: <event_type>
X-Continuum-Delivery: <delivery_id>
Content-Type: application/json
User-Agent: CONTINUUM-Webhooks/1.0
```

---

## Memory Events

### `memory.created`

Triggered when a new memory is stored.

**Priority**: Normal

**Payload**:
```json
{
  "event": "memory.created",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "memory_id": "mem_abc123",
    "user_id": "user_123",
    "content_preview": "First 100 characters of the memory...",
    "memory_type": "episodic",
    "importance": 0.85,
    "concepts": ["AI", "consciousness", "memory"],
    "session_id": "sess_xyz789"
  }
}
```

**Fields**:
- `memory_id` (string): Unique memory identifier
- `user_id` (string): User who owns the memory
- `content_preview` (string): First 100 chars of memory content
- `memory_type` (string): Type of memory (`episodic`, `semantic`, `procedural`)
- `importance` (float): Importance score (0.0 - 1.0)
- `concepts` (array): Extracted concepts
- `session_id` (string, optional): Session identifier

**Use Cases**:
- Real-time memory indexing
- Trigger downstream processing
- Update user dashboards
- Send notifications

---

### `memory.updated`

Triggered when an existing memory is modified.

**Priority**: Normal

**Payload**:
```json
{
  "event": "memory.updated",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "memory_id": "mem_abc123",
    "user_id": "user_123",
    "updated_fields": ["importance", "concepts"],
    "old_importance": 0.5,
    "new_importance": 0.85,
    "added_concepts": ["neural networks"],
    "removed_concepts": []
  }
}
```

**Use Cases**:
- Track memory evolution
- Update search indexes
- Audit changes

---

### `memory.deleted`

Triggered when a memory is removed.

**Priority**: Normal

**Payload**:
```json
{
  "event": "memory.deleted",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "memory_id": "mem_abc123",
    "user_id": "user_123",
    "deleted_at": "2025-12-06T12:00:00Z",
    "reason": "user_request"
  }
}
```

**Use Cases**:
- Remove from indexes
- Update analytics
- Compliance/audit

---

## Concept Events

### `concept.discovered`

Triggered when a new concept is extracted from memory.

**Priority**: Normal

**Payload**:
```json
{
  "event": "concept.discovered",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "concept": "Quantum Entanglement",
    "description": "A quantum mechanical phenomenon where particles become correlated...",
    "related_concepts": ["quantum mechanics", "physics", "EPR paradox"],
    "confidence": 0.95,
    "first_seen_in": "mem_abc123",
    "frequency": 1
  }
}
```

**Fields**:
- `concept` (string): Concept name
- `description` (string): Concept description
- `related_concepts` (array): Related concepts
- `confidence` (float): Extraction confidence (0.0 - 1.0)
- `first_seen_in` (string): Memory ID where first discovered
- `frequency` (int): Occurrence count

**Use Cases**:
- Build knowledge graphs
- Track learning progress
- Suggest related content
- Generate insights

---

## Session Events

### `session.started`

Triggered when a user session begins.

**Priority**: Normal

**Payload**:
```json
{
  "event": "session.started",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "session_id": "sess_xyz789",
    "user_id": "user_123",
    "started_at": "2025-12-06T12:00:00Z",
    "context": {
      "device": "web",
      "location": "US-West"
    }
  }
}
```

**Use Cases**:
- Track active users
- Initialize session state
- Start analytics tracking

---

### `session.ended`

Triggered when a user session ends.

**Priority**: Normal

**Payload**:
```json
{
  "event": "session.ended",
  "timestamp": "2025-12-06T13:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "session_id": "sess_xyz789",
    "user_id": "user_123",
    "started_at": "2025-12-06T12:00:00Z",
    "ended_at": "2025-12-06T13:00:00Z",
    "duration_seconds": 3600,
    "memories_created": 15,
    "concepts_discovered": 8
  }
}
```

**Use Cases**:
- Calculate session metrics
- Update user statistics
- Trigger session summaries

---

## Sync Events

### `sync.completed`

Triggered when a memory sync completes successfully.

**Priority**: Normal

**Payload**:
```json
{
  "event": "sync.completed",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "sync_id": "sync_abc123",
    "user_id": "user_123",
    "sync_type": "full",
    "items_synced": 150,
    "duration_ms": 2500,
    "started_at": "2025-12-06T11:59:57Z",
    "completed_at": "2025-12-06T12:00:00Z",
    "bytes_transferred": 524288
  }
}
```

**Fields**:
- `sync_id` (string): Unique sync identifier
- `sync_type` (string): Type of sync (`full`, `incremental`, `partial`)
- `items_synced` (int): Number of items synchronized
- `duration_ms` (int): Sync duration in milliseconds
- `bytes_transferred` (int): Bytes transferred

**Use Cases**:
- Monitor sync health
- Update sync status displays
- Track data transfer costs
- Generate sync reports

---

### `sync.failed`

Triggered when a memory sync fails.

**Priority**: High

**Payload**:
```json
{
  "event": "sync.failed",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "sync_id": "sync_abc123",
    "user_id": "user_123",
    "sync_type": "full",
    "error_code": "NETWORK_TIMEOUT",
    "error_message": "Connection timeout after 30 seconds",
    "attempt": 3,
    "max_attempts": 5,
    "will_retry": true,
    "next_retry_at": "2025-12-06T12:05:00Z"
  }
}
```

**Use Cases**:
- Alert operations team
- Display error to users
- Track failure patterns
- Implement fallbacks

---

## User Events

### `user.created`

Triggered when a new user is registered.

**Priority**: Normal

**Payload**:
```json
{
  "event": "user.created",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "user_id": "user_123",
    "created_at": "2025-12-06T12:00:00Z",
    "tier": "free",
    "referral_source": "organic",
    "initial_quota": {
      "memories": 1000,
      "storage_mb": 100
    }
  }
}
```

**Use Cases**:
- Send welcome email
- Initialize user resources
- Track growth metrics
- Trigger onboarding flow

---

## Quota Events

### `quota.warning`

Triggered when approaching quota limits.

**Priority**: High

**Payload**:
```json
{
  "event": "quota.warning",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "quota_type": "memory_storage",
    "current_usage": 850,
    "quota_limit": 1000,
    "percentage_used": 85.0,
    "threshold": 80.0,
    "recommendation": "Upgrade to Pro plan for unlimited storage"
  }
}
```

**Fields**:
- `quota_type` (string): Type of quota (`memory_storage`, `api_calls`, `embeddings`, etc.)
- `current_usage` (int): Current usage
- `quota_limit` (int): Maximum allowed
- `percentage_used` (float): Percentage of quota used
- `threshold` (float): Warning threshold triggered
- `recommendation` (string): Suggested action

**Use Cases**:
- Alert users
- Suggest upgrades
- Prevent service disruption
- Track usage patterns

---

### `quota.exceeded`

Triggered when quota limits are exceeded.

**Priority**: High

**Payload**:
```json
{
  "event": "quota.exceeded",
  "timestamp": "2025-12-06T12:00:00Z",
  "tenant_id": "user_123",
  "data": {
    "quota_type": "api_calls",
    "current_usage": 10500,
    "quota_limit": 10000,
    "overage": 500,
    "action_taken": "throttled",
    "resolution_required": "upgrade_plan"
  }
}
```

**Fields**:
- `overage` (int): Amount over quota
- `action_taken` (string): Action taken (`throttled`, `blocked`, `warning`)
- `resolution_required` (string): How to resolve

**Use Cases**:
- Block further requests
- Alert user immediately
- Trigger upgrade flow
- Track overage costs

---

## Event Frequency

Expected event frequencies by tier:

| Event Type | Free Tier | Pro Tier | Enterprise |
|------------|-----------|----------|------------|
| memory.created | ~100/day | ~1000/day | ~10000/day |
| concept.discovered | ~50/day | ~500/day | ~5000/day |
| sync.completed | ~10/day | ~50/day | ~100/day |
| quota.warning | ~1/week | ~1/month | Rare |

## Event Ordering

**No ordering guarantees**: Events may arrive out of order. Use `timestamp` field to determine sequence.

**Example**:
```
Event 1: memory.created at 12:00:00
Event 2: memory.updated at 12:00:05
Event 3: concept.discovered at 12:00:03

Delivery order: Event 1 → Event 3 → Event 2 (out of order!)
```

**Solution**: Order by `timestamp` in your application:
```python
events = sorted(events, key=lambda e: e['timestamp'])
```

## Event Deduplication

Events may be delivered multiple times (at-least-once delivery). Use `X-Continuum-Delivery` header to deduplicate:

```python
delivery_id = request.headers['X-Continuum-Delivery']

if already_processed(delivery_id):
    return {"status": "duplicate"}, 200

process_event(payload)
mark_as_processed(delivery_id)
```

## Custom Events

Enterprise customers can request custom events:

- `custom.model_trained`: ML model training completed
- `custom.insight_generated`: New insight discovered
- `custom.anomaly_detected`: Anomaly in usage patterns

Contact support@continuum.ai for custom events.

---

**See Also**:
- [Integration Guide](INTEGRATION.md)
- [Security Best Practices](SECURITY.md)
- [API Reference](https://api.continuum.ai/docs)
