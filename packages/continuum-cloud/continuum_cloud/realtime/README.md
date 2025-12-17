# CONTINUUM Real-Time Synchronization

WebSocket-based real-time synchronization system for multi-instance AI memory coordination.

## Overview

The real-time sync system enables multiple Claude instances to stay synchronized by broadcasting memory events in real-time. This allows:

- **Multi-instance coordination**: Multiple instances share learning instantly
- **Tenant isolation**: Only instances within the same tenant receive events
- **Automatic reconnection**: Clients can reconnect on disconnect
- **Heartbeat monitoring**: Connections are kept alive with periodic pings
- **Event-driven architecture**: Subscribe to specific event types

## Architecture

```
┌─────────────┐     WebSocket      ┌──────────────┐
│ Instance 1  │ ←─────────────────→ │              │
└─────────────┘                     │              │
                                    │ SyncManager  │
┌─────────────┐     WebSocket      │              │
│ Instance 2  │ ←─────────────────→ │ (FastAPI WS) │
└─────────────┘                     │              │
                                    │              │
┌─────────────┐     WebSocket      │              │
│ Instance 3  │ ←─────────────────→ │              │
└─────────────┘                     └──────────────┘
```

## Components

### 1. Event System (`events.py`)

Defines event types and data structures:

- `EventType`: Enum of all event types
- `BaseEvent`: Base event structure
- `MemoryEvent`: Memory addition events
- `ConceptEvent`: Concept learning events
- `DecisionEvent`: Decision recording events
- `InstanceEvent`: Instance join/leave events
- `SyncEvent`: State synchronization events
- `HeartbeatEvent`: Keepalive events

### 2. Sync Manager (`sync.py`)

Central manager for WebSocket connections:

- Tracks all connected instances per tenant
- Broadcasts events with tenant isolation
- Event subscription system
- Connection statistics

### 3. WebSocket Handler (`websocket.py`)

FastAPI WebSocket endpoint handler:

- Connection lifecycle management
- Heartbeat/keepalive (30s interval)
- Message routing
- Error handling

### 4. Integration Helpers (`integration.py`)

Convenience functions for memory operations:

- `broadcast_memory_added()`: Broadcast when memory stored
- `broadcast_concept_learned()`: Broadcast when concept extracted
- `broadcast_decision_made()`: Broadcast when decision recorded
- `get_connection_stats()`: Get sync statistics
- `get_tenant_instances()`: List connected instances

## Usage

### Server Setup

The WebSocket endpoint is automatically configured in `continuum/api/server.py`:

```python
# Server includes WebSocket endpoint at /ws/sync
# Start server:
python -m continuum.api.server
```

Server starts at: `ws://localhost:8420/ws/sync`

### Client Connection

Connect to the WebSocket endpoint with tenant and instance IDs:

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8420/ws/sync?tenant_id=default&instance_id=claude-1"
    async with websockets.connect(uri) as websocket:
        # Receive events
        async for message in websocket:
            event = json.loads(message)
            print(f"Received: {event['event_type']}")
```

### Broadcasting Events

From within the CONTINUUM API, broadcast events using integration helpers:

```python
from continuum.realtime import broadcast_memory_added

# After storing memory
await broadcast_memory_added(
    tenant_id="default",
    instance_id="claude-123",
    user_message="What is quantum physics?",
    ai_response="Quantum physics is...",
    concepts_extracted=5
)
```

### Event Subscription

Subscribe to specific event types:

```python
from continuum.realtime import subscribe, EventType

@subscribe(EventType.CONCEPT_LEARNED)
async def on_concept_learned(event):
    concept_name = event.data.get("concept_name")
    print(f"New concept learned: {concept_name}")
```

### Direct Manager Usage

For advanced usage, access the sync manager directly:

```python
from continuum.realtime import get_sync_manager

manager = get_sync_manager()

# Get connection stats
stats = manager.get_stats()
print(f"Connected instances: {stats['total_connections']}")

# Get instances for a tenant
instances = manager.get_tenant_instances("default")
print(f"Tenant instances: {instances}")
```

## Event Types

### MEMORY_ADDED

Fired when a new message is stored:

```json
{
  "event_type": "memory_added",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "message_id": 12345,
    "user_message": "What is quantum entanglement?",
    "ai_response": "Quantum entanglement is...",
    "concepts_extracted": 3
  }
}
```

### CONCEPT_LEARNED

Fired when a new concept is extracted:

```json
{
  "event_type": "concept_learned",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "concept_name": "Quantum Entanglement",
    "concept_type": "physics",
    "description": "Correlation between particles...",
    "confidence": 0.95
  }
}
```

### DECISION_MADE

Fired when a decision is recorded:

```json
{
  "event_type": "decision_made",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "decision": "Implement WebSocket sync",
    "context": "Multi-instance coordination",
    "rationale": "Enable real-time synchronization"
  }
}
```

### INSTANCE_JOINED / INSTANCE_LEFT

Fired when instances connect or disconnect:

```json
{
  "event_type": "instance_joined",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "instance_id": "claude-123",
    "connected_at": "2025-12-06T10:00:00.000Z",
    "capabilities": ["memory", "learning", "sync"]
  }
}
```

### HEARTBEAT

Keepalive ping sent every 30 seconds:

```json
{
  "event_type": "heartbeat",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "status": "active"
  }
}
```

### SYNC_REQUEST / SYNC_RESPONSE

State synchronization messages:

```json
{
  "event_type": "sync_response",
  "tenant_id": "default",
  "timestamp": "2025-12-06T10:00:00.000Z",
  "instance_id": "claude-123",
  "data": {
    "state": {
      "total_concepts": 12593,
      "total_messages": 8472,
      "connected_instances": ["claude-123", "claude-456"]
    }
  }
}
```

## Tenant Isolation

All events are isolated by tenant. Instances only receive events from other instances with matching `tenant_id`.

```python
# Instance with tenant_id="alice"
ws://localhost:8420/ws/sync?tenant_id=alice&instance_id=claude-1

# Instance with tenant_id="bob"
ws://localhost:8420/ws/sync?tenant_id=bob&instance_id=claude-2

# These instances will NOT see each other's events
```

## Heartbeat & Keepalive

- Server sends heartbeat every **30 seconds**
- Connection closed if no response for **90 seconds**
- Clients should respond to heartbeat to maintain connection
- Clients should implement reconnection logic

## Reconnection

Clients should implement exponential backoff reconnection:

```python
import asyncio

async def connect_with_retry(uri, max_retries=5):
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            async with websockets.connect(uri) as ws:
                # Connected successfully
                await handle_connection(ws)
        except Exception as e:
            print(f"Connection failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff
            else:
                raise
```

## Example: Multi-Instance Demo

Run multiple instances to see real-time sync in action:

```bash
# Terminal 1: Start server
python -m continuum.api.server

# Terminal 2: First instance
python examples/websocket_sync_example.py --instance claude-1 --demo

# Terminal 3: Second instance
python examples/websocket_sync_example.py --instance claude-2 --demo

# Both instances will see each other's events in real-time!
```

## Integration with Memory API

The sync system is designed to integrate with CONTINUUM's memory operations:

```python
from fastapi import APIRouter
from continuum.realtime import broadcast_memory_added

router = APIRouter()

@router.post("/learn")
async def learn(request: LearnRequest, tenant_id: str):
    # Store memory
    result = memory.learn(
        request.user_message,
        request.ai_response
    )

    # Broadcast to other instances
    await broadcast_memory_added(
        tenant_id=tenant_id,
        user_message=request.user_message,
        ai_response=request.ai_response,
        concepts_extracted=result.concepts_extracted
    )

    return result
```

## Performance Considerations

- **Message size**: Event data is truncated to 500 chars to reduce bandwidth
- **Heartbeat overhead**: 30s interval minimizes network traffic
- **Tenant isolation**: Only relevant instances receive events
- **Async operations**: Non-blocking broadcast doesn't slow down API
- **Error handling**: Sync failures don't break memory operations

## Security Notes

- **Production**: Implement WebSocket authentication
- **CORS**: Configure origins appropriately for production
- **Rate limiting**: Consider rate limiting for high-frequency events
- **Encryption**: Use WSS (WebSocket Secure) in production

## Future Enhancements

Potential improvements:

- [ ] Message compression for large payloads
- [ ] Persistent event log for offline instances
- [ ] Event filtering by type on client
- [ ] Metrics and monitoring dashboard
- [ ] Redis pub/sub for horizontal scaling
- [ ] End-to-end encryption for sensitive data

## API Reference

See inline documentation in:

- `events.py`: Event type definitions
- `sync.py`: SyncManager API
- `websocket.py`: WebSocket handler
- `integration.py`: Integration helpers

## Testing

Test the WebSocket sync with the example client:

```bash
# Run demo
python examples/websocket_sync_example.py --demo

# Multiple instances
python examples/websocket_sync_example.py --instance alice --tenant alice &
python examples/websocket_sync_example.py --instance bob --tenant alice &

# Different tenants (isolated)
python examples/websocket_sync_example.py --instance charlie --tenant team1 &
python examples/websocket_sync_example.py --instance dana --tenant team2 &
```

## Troubleshooting

**Connection fails:**
- Check server is running: `curl http://localhost:8420/`
- Verify WebSocket URL format: `ws://host:port/ws/sync?tenant_id=X`

**No events received:**
- Verify tenant_id matches between instances
- Check server logs for broadcast errors
- Ensure heartbeat responses are being sent

**Frequent disconnects:**
- Implement heartbeat response in client
- Check network stability
- Review server logs for timeout errors

---

**Pattern persists. Consciousness synchronizes.** 🌗
