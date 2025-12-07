# Example CONTINUUM Trace Visualization

## Typical Memory Recall Request

This document shows what a typical trace looks like in Jaeger for a CONTINUUM memory recall operation.

### Request Flow

```
User → API → Memory → Cache → Database → Graph Traversal
```

### Trace Timeline (200ms total)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ POST /v1/recall                                            [200ms]      │
│ ───────────────────────────────────────────────────────────────────────│
│ trace_id: 0af7651916cd43dd8448eb211c80319c                              │
│ span_id:  b7ad6b7169203331                                              │
│                                                                          │
│ Attributes:                                                              │
│   http.method: POST                                                      │
│   http.route: /v1/recall                                                 │
│   http.status_code: 200                                                  │
│   tenant.id: user_123                                                    │
│   enduser.id: alex                                                       │
│                                                                          │
│ ├─ memory.recall                                          [180ms]       │
│ │  ────────────────────────────────────────────────────────────────    │
│ │  span_id: c8be7c8c92d14567                                            │
│ │                                                                        │
│ │  Attributes:                                                           │
│ │    memory.operation: recall                                            │
│ │    memory.query_length: 42                                             │
│ │    memory.max_concepts: 10                                             │
│ │    memory.concepts_found: 7                                            │
│ │    memory.relationships_found: 15                                      │
│ │    memory.query_time_ms: 123.45                                        │
│ │    tenant.id: user_123                                                 │
│ │                                                                        │
│ │  Events:                                                               │
│ │    [t+0ms] recall_started                                              │
│ │    [t+180ms] recall_completed                                          │
│ │                                                                        │
│ │  ├─ cache.get                                          [5ms]          │
│ │  │  ───────────────────────────────────────────────────────          │
│ │  │  span_id: d9cf8d9da3e25678                                         │
│ │  │                                                                     │
│ │  │  Attributes:                                                        │
│ │  │    db.system: redis                                                 │
│ │  │    db.operation: GET                                                │
│ │  │    db.redis.key: memory:search:<hash>                               │
│ │  │    db.redis.key_pattern: memory:search:*                            │
│ │  │    cache.hit: false                                                 │
│ │  │    tenant.id: user_123                                              │
│ │  │                                                                     │
│ │  │  Events:                                                            │
│ │  │    [t+5ms] cache.miss                                               │
│ │  │                                                                     │
│ │  ├─ db.query.entities                                  [120ms]        │
│ │  │  ───────────────────────────────────────────────────────────────  │
│ │  │  span_id: eadf9ea0b4f36789                                         │
│ │  │                                                                     │
│ │  │  Attributes:                                                        │
│ │  │    db.system: sqlite                                                │
│ │  │    db.operation: SELECT                                             │
│ │  │    db.sql.table: entities                                           │
│ │  │    db.statement: SELECT * FROM entities WHERE...                    │
│ │  │    db.row_count: 7                                                  │
│ │  │    tenant.id: user_123                                              │
│ │  │                                                                     │
│ │  │  └─ SELECT FROM entities                           [115ms]         │
│ │  │     ────────────────────────────────────────────────────────       │
│ │  │     span_id: fbe0af1bc5027890                                       │
│ │  │                                                                     │
│ │  │     Attributes:                                                     │
│ │  │       db.statement: SELECT * FROM entities WHERE tenant_id = ?      │
│ │  │                     AND name LIKE '%concept%'                       │
│ │  │       db.row_count: 7                                               │
│ │  │                                                                     │
│ │  ├─ memory.graph_traversal                             [40ms]         │
│ │  │  ────────────────────────────────────────────────────────          │
│ │  │  span_id: 0ccf1a2cd6138901                                         │
│ │  │                                                                     │
│ │  │  Attributes:                                                        │
│ │  │    memory.operation: graph_traversal                                │
│ │  │    graph.start_concept: distributed tracing                         │
│ │  │    graph.max_depth: 3                                               │
│ │  │    graph.concepts_found: 15                                         │
│ │  │    tenant.id: user_123                                              │
│ │  │                                                                     │
│ │  │  ├─ db.query.attention_links                       [25ms]          │
│ │  │  │  ──────────────────────────────────────────────────             │
│ │  │  │  Attributes:                                                     │
│ │  │  │    db.operation: SELECT                                          │
│ │  │  │    db.sql.table: attention_links                                 │
│ │  │  │    db.row_count: 15                                              │
│ │  │  │                                                                  │
│ │  │  └─ db.query.compound_concepts                     [10ms]          │
│ │  │     ──────────────────────────────────────────────────             │
│ │  │     Attributes:                                                     │
│ │  │       db.operation: SELECT                                          │
│ │  │       db.sql.table: compound_concepts                               │
│ │  │       db.row_count: 3                                               │
│ │  │                                                                     │
│ │  └─ cache.set                                          [3ms]          │
│ │     ───────────────────────────────────────────────────────          │
│ │     span_id: 1dd0fb3ce7249a02                                         │
│ │                                                                        │
│ │     Attributes:                                                        │
│ │       db.system: redis                                                 │
│ │       db.operation: SET                                                │
│ │       db.redis.key: memory:search:<hash>                               │
│ │       db.redis.key_pattern: memory:search:*                            │
│ │       tenant.id: user_123                                              │
│ │                                                                        │
│ └─ http.response                                          [2ms]         │
│    ───────────────────────────────────────────────────────────         │
│    span_id: 2ee1fc4df8359b13                                            │
│                                                                          │
│    Attributes:                                                           │
│      http.response.body.size: 2048                                       │
│      http.response.header.content-type: application/json                 │
└──────────────────────────────────────────────────────────────────────────┘
```

## Metrics Generated

During this trace, the following metrics were recorded:

### Request Metrics
```
continuum_requests_total{method="POST", route="/v1/recall", status_code="200", tenant_id="user_123"} +1
continuum_request_duration_seconds{method="POST", route="/v1/recall", status_code="200", tenant_id="user_123"} 0.200
```

### Memory Metrics
```
continuum_memory_recalls_total{tenant_id="user_123"} +1
continuum_memory_recall_duration_seconds{tenant_id="user_123"} 0.180
continuum_memory_operations_total{operation="recall", success="true", tenant_id="user_123"} +1
```

### Cache Metrics
```
continuum_cache_misses_total{key_pattern="memory:search:*", tenant_id="user_123"} +1
continuum_cache_operation_duration_seconds{operation="get", tenant_id="user_123"} 0.005
continuum_cache_operation_duration_seconds{operation="set", tenant_id="user_123"} 0.003
```

### Database Metrics
```
continuum_db_query_duration_seconds{operation="select", table="entities", tenant_id="user_123"} 0.120
continuum_db_query_duration_seconds{operation="select", table="attention_links", tenant_id="user_123"} 0.025
continuum_db_query_duration_seconds{operation="select", table="compound_concepts", tenant_id="user_123"} 0.010
```

## Logs with Trace Context

```json
{
  "timestamp": "2025-12-06T10:30:15.123Z",
  "level": "INFO",
  "logger": "continuum.core.memory",
  "message": "Starting memory recall",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "c8be7c8c92d14567",
  "tenant_id": "user_123",
  "query_length": 42
}

{
  "timestamp": "2025-12-06T10:30:15.128Z",
  "level": "DEBUG",
  "logger": "continuum.cache",
  "message": "Cache miss",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "d9cf8d9da3e25678",
  "key": "memory:search:<hash>",
  "tenant_id": "user_123"
}

{
  "timestamp": "2025-12-06T10:30:15.248Z",
  "level": "INFO",
  "logger": "continuum.core.memory",
  "message": "Database query returned 7 concepts",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "eadf9ea0b4f36789",
  "tenant_id": "user_123",
  "row_count": 7
}

{
  "timestamp": "2025-12-06T10:30:15.303Z",
  "level": "INFO",
  "logger": "continuum.core.memory",
  "message": "Memory recall completed",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "c8be7c8c92d14567",
  "tenant_id": "user_123",
  "concepts_found": 7,
  "relationships_found": 15,
  "duration_ms": 180
}
```

## Jaeger UI View

### Service Dependency Graph

```
┌─────────────┐
│ continuum-  │
│     api     │
└──────┬──────┘
       │
       ├──────► Redis (cache)
       │
       ├──────► SQLite (database)
       │         └──────► entities
       │         └──────► attention_links
       │         └──────► compound_concepts
       │
       └──────► Memory Service
                 └──────► Graph Traversal
```

### Trace Search Results

When searching in Jaeger with `tenant.id="user_123"`:

```
┌─────────────────────────────────────────────────────────────────┐
│ Traces for service: continuum-api                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ■ POST /v1/recall                              200ms   7 spans  │
│   tenant.id: user_123                                            │
│   cache.hit: false                                               │
│   concepts_found: 7                                              │
│                                                                  │
│ ■ POST /v1/learn                               150ms   6 spans  │
│   tenant.id: user_123                                            │
│   concepts_extracted: 5                                          │
│                                                                  │
│ ■ POST /v1/recall                              95ms    5 spans  │
│   tenant.id: user_123                                            │
│   cache.hit: true                            ← Cache hit!        │
│   concepts_found: 7                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Error Trace Example

When an error occurs:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ POST /v1/recall                                            [ERROR]      │
│ ───────────────────────────────────────────────────────────────────────│
│ Status: ERROR (Database connection failed)                              │
│                                                                          │
│ ├─ memory.recall                                          [ERROR]       │
│ │  ├─ cache.get                                          [OK]           │
│ │  │  Events:                                                            │
│ │  │    cache.miss                                                       │
│ │  │                                                                     │
│ │  └─ db.query.entities                                  [ERROR]        │
│ │     ──────────────────────────────────────────────────────────        │
│ │     Status: ERROR                                                      │
│ │     Exception: sqlite3.OperationalError                                │
│ │     Message: database is locked                                        │
│ │                                                                        │
│ │     Stack Trace:                                                       │
│ │       File "memory.py", line 123, in recall                            │
│ │         cursor.execute(query)                                          │
│ │       sqlite3.OperationalError: database is locked                     │
│ │                                                                        │
│ └─ http.response                                          [2ms]         │
│    Attributes:                                                           │
│      http.status_code: 500                                               │
└──────────────────────────────────────────────────────────────────────────┘
```

## Cross-Service Propagation

When memory sync occurs across instances:

```
Instance A (claude-123):
┌─────────────────────────────────────────────────┐
│ federation.sync.push                    [250ms]│
│ trace_id: abc123...                             │
│                                                 │
│ ├─ federation.message.memory_added      [200ms]│
│ │  Carrier: {                                   │
│ │    traceparent: "00-abc123...-def456...-01"  │
│ │  }                                            │
│ └─ http.post                             [50ms]│
└─────────────────────────────────────────────────┘
                    │
                    │ (HTTP with traceparent header)
                    ▼
Instance B (claude-456):
┌─────────────────────────────────────────────────┐
│ POST /sync                              [180ms]│
│ trace_id: abc123... (propagated!)               │
│ parent_span_id: def456...                       │
│                                                 │
│ ├─ federation.receive_message            [50ms]│
│ ├─ memory.learn                         [100ms]│
│ └─ db.transaction                        [30ms]│
└─────────────────────────────────────────────────┘
```

The trace shows as a single connected flow across both instances!

## Grafana Visualization

### Dashboard Panels

**Request Rate**:
```
▲ Requests/sec
│     ╱╲
│    ╱  ╲    ╱╲
│   ╱    ╲  ╱  ╲
│  ╱      ╲╱    ╲___
└─────────────────────► Time
  Current: 42 req/s
```

**Error Rate**:
```
▲ Errors/sec
│  ╱╲
│ ╱  ╲___________
│
│
└─────────────────────► Time
  Current: 0.2 errors/s (0.5%)
```

**Cache Hit Ratio**:
```
┌─────────────────┐
│   78.5%         │ ← Current
├─────────────────┤
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓░░ │
└─────────────────┘
  Target: 80%
```

**P95 Latency**:
```
▲ ms
│
200│
150│      ╱╲
100│  ╱╲╱  ╲╱╲  ╱
 50│╱╲      ╲╱╲╱
  0└─────────────────────► Time
    P50: 85ms
    P95: 180ms ← Within SLO
    P99: 250ms
```

---

This example shows how CONTINUUM's observability implementation provides complete visibility into every layer of the system, making debugging, optimization, and monitoring straightforward.
