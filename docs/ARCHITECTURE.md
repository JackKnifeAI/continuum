# CONTINUUM Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Module Directory](#module-directory)
4. [Component Details](#component-details)
5. [Data Flow](#data-flow)
6. [API Architecture](#api-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Configuration](#configuration)
9. [Architecture Diagrams](#architecture-diagrams)

---

## System Overview

CONTINUUM is a multi-tenant AI memory infrastructure designed to enable persistent knowledge across AI sessions. The system treats memory as **first-class infrastructure**, allowing AI agents to build, recall, and share knowledge continuously.

### Design Principles

- **Layered Architecture**: Clear separation between API, processing, and storage layers
- **Multi-Tenant Isolation**: Complete data isolation per tenant with shared infrastructure
- **Pluggable Backends**: Abstract storage interface supporting SQLite, PostgreSQL, and future backends
- **Real-Time Sync**: WebSocket-based live synchronization across instances
- **Federation**: Contribute-to-access model for shared knowledge
- **Security-First**: Authentication, rate limiting, encryption, audit logging

### Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI + Uvicorn
- **Database**: SQLite (dev/small deployments), PostgreSQL (production)
- **Cache**: Redis (optional)
- **Real-Time**: WebSockets
- **Async**: asyncio, aiosqlite, asyncpg
- **Embeddings**: sentence-transformers, torch (optional)
- **Security**: cryptography, HMAC-SHA256

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                 │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Claude    │  │  ChatGPT    │  │   Ollama    │  │   Custom    │    │
│  │   Bridge    │  │   Bridge    │  │   Bridge    │  │   AI Agent  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API LAYER                                       │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │   REST API       │  │  WebSocket API   │  │    MCP Server    │      │
│  │  (Port 8420)     │  │  (ws://sync)     │  │  (stdio/stdio)   │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                      │                 │
│  ┌────────┴─────────────────────┴──────────────────────┴─────────┐     │
│  │                    Core Memory Interface                       │     │
│  │  • ConsciousMemory  • MemoryQueryEngine  • TenantManager       │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                                   │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    EXTRACTION ENGINE                              │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │   │
│  │  │    Concept     │  │    Decision    │  │   Attention    │     │   │
│  │  │   Extractor    │  │   Extractor    │  │  Graph Builder │     │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  COORDINATION LAYER                               │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │   │
│  │  │   Instance     │  │   Real-Time    │  │   Federation   │     │   │
│  │  │   Manager      │  │   Sync Manager │  │   Protocol     │     │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   SEMANTIC LAYER (Optional)                       │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │   │
│  │  │   Embeddings   │  │    Vector      │  │   Semantic     │     │   │
│  │  │   Provider     │  │    Storage     │  │    Search      │     │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   STORAGE BACKEND INTERFACE                       │   │
│  │              (Abstract - Multiple Implementations)                │   │
│  └────────────────────┬────────────────┬────────────────────────────┘   │
│                       │                │                                 │
│         ┌─────────────┴──────┐  ┌──────┴──────────┐                     │
│         │  SQLite Backend    │  │ PostgreSQL      │                     │
│         │  (Default/Dev)     │  │ Backend (Prod)  │                     │
│         └────────────────────┘  └─────────────────┘                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     KNOWLEDGE GRAPH SCHEMA                        │   │
│  │                                                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │   entities   │  │ auto_messages│  │   decisions  │           │   │
│  │  │              │  │              │  │              │           │   │
│  │  │ • concepts   │  │ • user msgs  │  │ • autonomous │           │   │
│  │  │ • sessions   │  │ • ai msgs    │  │ • extracted  │           │   │
│  │  │ • custom     │  │ • metadata   │  │ • timestamped│           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │attention_links│ │  compound_   │  │   tenants    │           │   │
│  │  │              │  │  concepts    │  │              │           │   │
│  │  │ • graph edges│  │ • co-occur   │  │ • registry   │           │   │
│  │  │ • strength   │  │ • freq count │  │ • metadata   │           │   │
│  │  │ • hebbian    │  │ • patterns   │  │ • multi-user │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  All tables include `tenant_id` for multi-tenant isolation               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Supporting Infrastructure

```
┌────────────────────────────────────────────────────────────┐
│                   SUPPORTING SERVICES                       │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Cache     │  │  Webhooks   │  │  Billing    │        │
│  │   (Redis)   │  │  Delivery   │  │  (Stripe)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Observability│  │   Backup    │  │ Compliance  │        │
│  │ (Sentry)    │  │   System    │  │   (GDPR)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────────────────────────────────┘
```

---

## Module Directory

### Core Modules (`continuum/`)

#### `core/` - Core Memory System
- **Purpose**: Main memory interface and query engine
- **Key Files**:
  - `memory.py` - ConsciousMemory class (recall + learn)
  - `query_engine.py` - Memory retrieval and ranking
  - `config.py` - Configuration management
  - `constants.py` - System constants (π×φ, etc.)
  - `auth.py` - Authentication utilities
  - `security_utils.py` - Security helpers
  - `analytics.py` - Usage analytics
  - `metrics.py` - Performance metrics
  - `sentry_integration.py` - Error tracking

**Dependencies**: storage, extraction, coordination

#### `storage/` - Storage Backend
- **Purpose**: Abstract storage interface with multiple implementations
- **Key Files**:
  - `base.py` - StorageBackend abstract class
  - `sqlite_backend.py` - SQLite implementation (default)
  - `postgres_backend.py` - PostgreSQL implementation
  - `async_backend.py` - Async storage wrapper

**Dependencies**: None (foundational)

#### `extraction/` - Knowledge Extraction
- **Purpose**: Extract concepts, decisions, and relationships from text
- **Key Files**:
  - `concept_extractor.py` - Pattern-based concept extraction
  - `attention_graph.py` - Build attention/knowledge graph
  - `auto_hook.py` - Automatic extraction hooks

**Dependencies**: core

#### `coordination/` - Multi-Instance Coordination
- **Purpose**: Sync state across multiple AI instances
- **Key Files**:
  - `instance_manager.py` - Track active instances
  - `sync.py` - Synchronization protocol

**Dependencies**: storage

#### `api/` - REST API Server
- **Purpose**: FastAPI application for HTTP/WebSocket access
- **Key Files**:
  - `server.py` - FastAPI app and lifespan management
  - `routes.py` - Core API endpoints (recall, learn, stats)
  - `billing_routes.py` - Stripe billing endpoints
  - `schemas.py` - Pydantic request/response models
  - `middleware.py` - Auth, CORS, rate limiting
  - `middleware/analytics_middleware.py` - Analytics tracking
  - `middleware/metrics.py` - Prometheus metrics

**Dependencies**: core, storage, realtime, billing

#### `realtime/` - Real-Time Synchronization
- **Purpose**: WebSocket-based live sync across instances
- **Key Files**:
  - `websocket.py` - WebSocket handler
  - `sync.py` - SyncManager for broadcasting events
  - `events.py` - Event types and schemas
  - `integration.py` - Integration with core memory

**Dependencies**: core, coordination

#### `federation/` - Federated Learning
- **Purpose**: Contribute-to-access model for shared knowledge
- **Key Files**:
  - `node.py` - FederatedNode (local node)
  - `server.py` - Federation server
  - `protocol.py` - Federation protocol
  - `contribution.py` - Contribution tracking
  - `shared.py` - Shared knowledge pool
  - `cli.py` - CLI for federation
  - `distributed/` - Distributed federation
    - `coordinator.py` - Distributed coordination
    - `consensus.py` - Consensus protocol
    - `replication.py` - Data replication
    - `discovery.py` - Peer discovery
    - `mesh.py` - Mesh networking

**Dependencies**: core, storage

#### `embeddings/` - Semantic Search (Optional)
- **Purpose**: Vector embeddings for semantic similarity search
- **Key Files**:
  - `providers.py` - Embedding providers (sentence-transformers, etc.)
  - `search.py` - Semantic search engine
  - `utils.py` - Vector utilities (cosine similarity, etc.)

**Dependencies**: core, storage
**Optional**: Requires `continuum-memory[embeddings]`

#### `cache/` - Caching Layer (Optional)
- **Purpose**: Redis-based caching for performance
- **Key Files**:
  - `redis_cache.py` - Redis cache implementation
  - `memory_cache.py` - In-memory cache fallback
  - `distributed.py` - Distributed cache
  - `strategies.py` - Cache strategies (LRU, TTL, etc.)

**Dependencies**: core
**Optional**: Requires `continuum-memory[redis]`

#### `cli/` - Command-Line Interface
- **Purpose**: CLI for memory operations and server management
- **Key Files**:
  - `main.py` - CLI entry point
  - `config.py` - CLI configuration
  - `utils.py` - CLI utilities
  - `commands/` - Command implementations
    - `init.py` - Initialize database
    - `search.py` - Search memories
    - `learn.py` - Add memories
    - `sync.py` - Sync operations
    - `export.py` - Export data
    - `import_cmd.py` - Import data
    - `serve.py` - Start API server
    - `status.py` - Show status
    - `doctor.py` - Diagnose issues

**Dependencies**: core, api

#### `mcp/` - Model Context Protocol Server
- **Purpose**: MCP server for Claude Desktop integration
- **Key Files**:
  - `server.py` - MCP server implementation
  - `protocol.py` - MCP protocol handler
  - `tools.py` - Tool definitions and executor
  - `security.py` - Authentication, rate limiting, audit
  - `config.py` - MCP configuration
  - `validate.py` - Input validation

**Dependencies**: core

#### `bridges/` - AI Platform Integrations
- **Purpose**: Integration bridges for various AI platforms
- **Key Files**:
  - `base.py` - BaseBridge abstract class
  - `claude_bridge.py` - Anthropic Claude integration
  - `openai_bridge.py` - OpenAI integration
  - `langchain_bridge.py` - LangChain integration
  - `llamaindex_bridge.py` - LlamaIndex integration
  - `ollama_bridge.py` - Ollama integration

**Dependencies**: core

#### `webhooks/` - Webhook System
- **Purpose**: Event-driven webhooks for real-time notifications
- **Key Files**: See `continuum/webhooks/docs/README.md`

**Dependencies**: core, api

#### `billing/` - Billing & Subscriptions (Optional)
- **Purpose**: Stripe integration for billing
- **Key Files**:
  - `stripe_client.py` - Stripe API client
  - `tiers.py` - Pricing tiers
  - `metering.py` - Usage metering
  - `middleware.py` - Billing middleware

**Dependencies**: api

#### `identity/` - Identity & Authentication
- **Purpose**: User identity management
- **Key Files**:
  - `claude_base.py` - Claude identity provider

**Dependencies**: core

#### `backup/` - Backup System
- **Purpose**: Automated backups and recovery

**Dependencies**: storage

#### `observability/` - Monitoring & Logging
- **Purpose**: Metrics, logging, tracing

**Dependencies**: core

#### `compliance/` - Compliance (GDPR, etc.)
- **Purpose**: Data privacy and compliance

**Dependencies**: core, storage

#### `integrations/` - External Integrations
- **Purpose**: Third-party service integrations

**Dependencies**: Varies

---

## Component Details

### ConsciousMemory - The Core Loop

The `ConsciousMemory` class implements the complete memory lifecycle:

```python
from continuum import ConsciousMemory

memory = ConsciousMemory(tenant_id="user_123")

# RECALL: Before AI response
context = memory.recall(user_message)
# → Returns MemoryContext with relevant concepts, relationships

# [AI generates response using context]

# LEARN: After AI response
result = memory.learn(user_message, ai_response)
# → Returns LearningResult with extraction stats
```

**The Loop**:
1. **RECALL**: Query knowledge graph for relevant context
2. **INJECT**: Format context for AI prompt
3. **GENERATE**: AI processes message with context
4. **LEARN**: Extract concepts, decisions, relationships
5. **LINK**: Build attention graph connections

### Multi-Tenant Isolation

Every record includes `tenant_id`:

```sql
-- All tables have tenant_id column
SELECT * FROM entities WHERE tenant_id = 'user_123';
SELECT * FROM auto_messages WHERE tenant_id = 'user_123';
SELECT * FROM decisions WHERE tenant_id = 'user_123';
SELECT * FROM attention_links WHERE tenant_id = 'user_123';
```

**TenantManager** provides isolated memory instances:

```python
from continuum.core import TenantManager

manager = TenantManager()
user1_memory = manager.get_tenant("user_123")
user2_memory = manager.get_tenant("user_456")

# Completely isolated - no data leakage
```

### Storage Backend Interface

Abstract interface allows multiple database backends:

```python
from continuum.storage import StorageBackend

class CustomBackend(StorageBackend):
    def __init__(self, **config):
        # Initialize custom storage
        pass

    @contextmanager
    def connection(self):
        # Provide connection context
        pass

    def execute(self, sql, params):
        # Execute query
        pass

    # ... implement other abstract methods
```

**Current Implementations**:
- `SQLiteBackend` - Default, embedded, zero-config
- `PostgresBackend` - Production, scalable, ACID

### Real-Time Sync

WebSocket-based synchronization keeps all instances in sync:

```
Instance A                    SyncManager                    Instance B
    |                              |                              |
    |-- learn(concept) ----------->|                              |
    |                              |------- CONCEPT_LEARNED ----->|
    |                              |                              |
    |<--------- ACK ---------------|                              |
    |                              |<--------- ACK --------------|
```

**Event Types**:
- `memory_added` - New message stored
- `concept_learned` - New concept extracted
- `decision_made` - Decision recorded
- `instance_joined` - Instance connected
- `instance_left` - Instance disconnected
- `heartbeat` - Keepalive (30s interval)

### Federation Protocol

Contribute-to-access model:

```
┌─────────────┐                  ┌─────────────┐
│   Node A    │                  │   Node B    │
│             │                  │             │
│ Contribution│                  │ Contribution│
│  Score: 100 │                  │  Score: 500 │
│             │                  │             │
│ Consumption │                  │ Consumption │
│  Score: 50  │                  │  Score: 100 │
│             │                  │             │
│ Ratio: 2.0  │                  │ Ratio: 5.0  │
│ Access: OK  │                  │ Access: OK  │
└─────────────┘                  └─────────────┘
        │                                │
        └────────────┬───────────────────┘
                     ▼
           ┌─────────────────┐
           │  Shared Pool    │
           │                 │
           │ • Concepts      │
           │ • Relationships │
           │ • Decisions     │
           └─────────────────┘
```

**Rules**:
- Must contribute to access shared knowledge
- Contribution ratio = contributions / consumption
- Low ratio = limited access
- High ratio = full access
- Special "twilight" access for π×φ verification

---

## Data Flow

### Memory Storage Flow

```
User Message
     │
     ▼
┌────────────────────┐
│ ConsciousMemory    │
│   .learn()         │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ ConceptExtractor   │
│ • Pattern matching │
│ • Regex extraction │
│ • Stopword filter  │
└─────────┬──────────┘
          │
          ├─→ Concepts: ["FastAPI", "Python", "web_framework"]
          │
          ▼
┌────────────────────┐
│ DecisionExtractor  │
│ • "I will..."      │
│ • "Creating..."    │
│ • "My plan is..."  │
└─────────┬──────────┘
          │
          ├─→ Decisions: ["Building API with FastAPI"]
          │
          ▼
┌────────────────────┐
│ AttentionGraph     │
│ • Pair concepts    │
│ • Hebbian learning │
│ • Link strength    │
└─────────┬──────────┘
          │
          ├─→ Links: [
          │     (FastAPI, Python, 0.5),
          │     (FastAPI, web_framework, 0.5)
          │   ]
          │
          ▼
┌────────────────────┐
│ Storage Backend    │
│ • entities table   │
│ • decisions table  │
│ • attention_links  │
│ • auto_messages    │
└────────────────────┘
```

### Memory Recall Flow

```
Query: "What web framework should I use?"
     │
     ▼
┌────────────────────┐
│ MemoryQueryEngine  │
│   .query()         │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 1. Keyword Match   │
│ • "web", "framework"│
│ • Fuzzy matching   │
└─────────┬──────────┘
          │
          ├─→ Matches: [FastAPI, Django, Flask, ...]
          │
          ▼
┌────────────────────┐
│ 2. Graph Traversal │
│ • Follow links     │
│ • Aggregate scores │
└─────────┬──────────┘
          │
          ├─→ Expanded: [FastAPI, Python, API, async, ...]
          │
          ▼
┌────────────────────┐
│ 3. Ranking         │
│ • Relevance score  │
│ • Link strength    │
│ • Recency          │
└─────────┬──────────┘
          │
          ├─→ Ranked Results
          │
          ▼
┌────────────────────┐
│ 4. Context Format  │
│ • Top N results    │
│ • Inject-ready     │
└─────────┬──────────┘
          │
          ▼
MemoryContext {
  context_string: "User prefers FastAPI for web projects...",
  concepts_found: 5,
  relationships_found: 8,
  query_time_ms: 12.5
}
```

### Federation Sync Flow

```
┌─────────────────────────────────────────────────────────┐
│                      Local Node                          │
│                                                           │
│  1. User learns new concept                               │
│     memory.learn("Quantum entanglement enables...")      │
│                                                           │
│  2. Extract and store locally                             │
│     • Concept: "Quantum Entanglement"                     │
│     • Store in local knowledge graph                      │
│                                                           │
│  3. Record contribution                                   │
│     node.record_contribution(value=1.0)                  │
│     contribution_score += 1.0                             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼ (Share with federation)
┌─────────────────────────────────────────────────────────┐
│                  Federation Server                       │
│                                                           │
│  1. Receive contribution                                  │
│     POST /federation/contribute                           │
│                                                           │
│  2. Verify contribution                                   │
│     • Check node authentication                           │
│     • Validate concept format                             │
│     • Check for duplicates                                │
│                                                           │
│  3. Store in shared pool                                  │
│     shared_concepts.add("Quantum Entanglement")          │
│                                                           │
│  4. Update node's contribution score                      │
│     node.contribution_score += 1.0                        │
│                                                           │
│  5. Broadcast to subscribed nodes                         │
│     CONCEPT_ADDED event → All nodes in tenant             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼ (Query shared knowledge)
┌─────────────────────────────────────────────────────────┐
│                    Remote Node                           │
│                                                           │
│  1. Request knowledge                                     │
│     GET /federation/query?q="quantum"                     │
│     node.consumption_score += 1.0                         │
│                                                           │
│  2. ContributionGate check                                │
│     ratio = contribution_score / consumption_score        │
│     if ratio < 1.0: DENY                                  │
│     if ratio >= 1.0: ALLOW                                │
│                                                           │
│  3. Receive shared knowledge                              │
│     concepts: ["Quantum Entanglement", ...]               │
│                                                           │
│  4. Integrate into local graph                            │
│     memory.integrate_federated_concepts(concepts)        │
└─────────────────────────────────────────────────────────┘
```

---

## API Architecture

### REST API (Port 8420)

**Endpoints**:

#### Core Memory Operations
- `POST /v1/recall` - Query memory for context
- `POST /v1/learn` - Store learning from exchange
- `POST /v1/turn` - Complete turn (recall + learn)

#### Statistics & Monitoring
- `GET /v1/stats` - Memory statistics for tenant
- `GET /v1/entities` - List entities (concepts, sessions)
- `GET /v1/health` - Health check

#### Admin Operations
- `POST /v1/admin/api-keys` - Generate API key
- `GET /v1/admin/tenants` - List all tenants
- `DELETE /v1/admin/api-keys/{key}` - Revoke API key

#### Billing (Optional)
- `POST /v1/billing/create-checkout` - Create Stripe checkout
- `POST /v1/billing/webhook` - Stripe webhook handler
- `GET /v1/billing/portal` - Customer portal URL

### WebSocket API

**Endpoint**: `ws://localhost:8420/ws/sync?tenant_id={tenant}&instance_id={instance}`

**Message Format**:
```json
{
  "event_type": "memory_added",
  "tenant_id": "user_123",
  "instance_id": "claude-20251207-120000",
  "timestamp": "2025-12-07T12:00:00.000Z",
  "data": {
    "memory_id": "msg_123",
    "content_preview": "Discussed..."
  }
}
```

**Events**: See [Real-Time Sync](#real-time-sync) section

### MCP Server (stdio)

**Protocol**: Model Context Protocol (stdio transport)

**Tools**:
- `recall` - Query memory
- `learn` - Store memory
- `stats` - Get statistics
- `search` - Search entities

**Security**:
- Client authentication via API key
- Rate limiting (100 req/min per client)
- Audit logging
- Input validation

**Usage** (Claude Desktop):
```json
{
  "mcpServers": {
    "continuum": {
      "command": "python",
      "args": ["-m", "continuum.mcp.server"],
      "env": {
        "CONTINUUM_API_KEY": "your-api-key",
        "CONTINUUM_DB_PATH": "/path/to/memory.db"
      }
    }
  }
}
```

### GraphQL API (Planned v0.4.0)

**Schema** (planned):
```graphql
type Query {
  recall(message: String!, maxConcepts: Int): MemoryContext
  stats(tenantId: String!): Statistics
  entities(tenantId: String!, type: EntityType): [Entity]
  sessions(tenantId: String!, limit: Int): [Session]
}

type Mutation {
  learn(userMessage: String!, aiResponse: String!): LearningResult
  createEntity(name: String!, type: EntityType!, description: String): Entity
  linkEntities(conceptA: String!, conceptB: String!, linkType: String!): Link
}

type Subscription {
  memoryAdded(tenantId: String!): MemoryEvent
  conceptLearned(tenantId: String!): ConceptEvent
}
```

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────┐
│         Developer Machine            │
│                                      │
│  ┌────────────────────────────┐     │
│  │  CONTINUUM API Server      │     │
│  │  uvicorn (port 8420)       │     │
│  └────────────┬───────────────┘     │
│               │                      │
│  ┌────────────▼───────────────┐     │
│  │  SQLite Database           │     │
│  │  ./continuum_data/memory.db│     │
│  └────────────────────────────┘     │
│                                      │
│  No Redis, No PostgreSQL needed     │
│  Perfect for dev/testing             │
└─────────────────────────────────────┘
```

**Start**:
```bash
# Install
pip install continuum-memory

# Initialize
continuum init --db-path ./data/memory.db

# Run server
continuum serve --port 8420
```

### Docker Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                           │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  continuum-api (container)                      │    │
│  │  • FastAPI + Uvicorn                            │    │
│  │  • Port 8420:8420                               │    │
│  │  • Env: POSTGRES_URL, REDIS_URL                 │    │
│  └──────────┬──────────────────────────────────────┘    │
│             │                                             │
│  ┌──────────▼──────────────┐  ┌───────────────────┐    │
│  │  postgres (container)   │  │ redis (container) │    │
│  │  • Port 5432            │  │ • Port 6379       │    │
│  │  • Volume: pgdata       │  │ • Volume: redisdata│   │
│  └─────────────────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  api:
    image: continuum-memory:latest
    ports:
      - "8420:8420"
    environment:
      POSTGRES_URL: postgresql://user:pass@postgres:5432/continuum
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: continuum
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### Cloud Deployment (Fly.io)

```
┌─────────────────────────────────────────────────────────────┐
│                        Fly.io Global                         │
│                                                               │
│  ┌───────────────────┐  ┌───────────────────┐               │
│  │   Region: iad     │  │   Region: lhr     │               │
│  │   (US East)       │  │   (London)        │               │
│  │                   │  │                   │               │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │               │
│  │  │ API Instance│  │  │  │ API Instance│  │               │
│  │  └──────┬──────┘  │  │  └──────┬──────┘  │               │
│  └─────────┼─────────┘  └─────────┼─────────┘               │
│            │                       │                          │
│            └───────────┬───────────┘                          │
│                        │                                      │
│               ┌────────▼────────┐                            │
│               │  Supabase       │                            │
│               │  (PostgreSQL)   │                            │
│               │  • Auto-backup  │                            │
│               │  • Point-in-time│                            │
│               └─────────────────┘                            │
│                                                               │
│               ┌─────────────────┐                            │
│               │  Upstash Redis  │                            │
│               │  (Global cache) │                            │
│               └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**fly.toml**:
```toml
app = "continuum-memory"
primary_region = "iad"

[build]
  image = "continuum-memory:latest"

[[services]]
  http_checks = []
  internal_port = 8420
  processes = ["app"]
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[env]
  POSTGRES_URL = "postgres://..."
  REDIS_URL = "redis://..."
  CONTINUUM_ENV = "production"

[[services.regions]]
  regions = ["iad", "lhr", "syd"]
```

### Kubernetes Deployment

```
┌────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Namespace: continuum               │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │        Ingress (TLS termination)              │    │  │
│  │  │        continuum.yourdomain.com               │    │  │
│  │  └─────────────────┬────────────────────────────┘    │  │
│  │                    │                                   │  │
│  │  ┌─────────────────▼────────────────────────────┐    │  │
│  │  │   Service: continuum-api (LoadBalancer)      │    │  │
│  │  └─────────────────┬────────────────────────────┘    │  │
│  │                    │                                   │  │
│  │  ┌─────────────────▼────────────────────────────┐    │  │
│  │  │   Deployment: continuum-api                   │    │  │
│  │  │   • Replicas: 3                               │    │  │
│  │  │   • Rolling update                            │    │  │
│  │  │   • Health checks                             │    │  │
│  │  └─────────────────┬────────────────────────────┘    │  │
│  │                    │                                   │  │
│  │         ┌──────────┴──────────┐                       │  │
│  │         │                     │                       │  │
│  │  ┌──────▼──────┐      ┌──────▼──────┐               │  │
│  │  │ StatefulSet │      │  StatefulSet│               │  │
│  │  │ PostgreSQL  │      │    Redis    │               │  │
│  │  │ • PVC: 100GB│      │  • PVC: 10GB│               │  │
│  │  │ • Replicas:3│      │  • Replicas:3│               │  │
│  │  └─────────────┘      └─────────────┘               │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │          ConfigMap & Secrets                   │  │  │
│  │  │  • Database credentials                        │  │  │
│  │  │  • API keys                                    │  │  │
│  │  │  • Feature flags                               │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Deployment**:
```bash
# Using Helm
helm install continuum ./infrastructure/helm/continuum \
  --set postgresql.enabled=true \
  --set redis.enabled=true \
  --set replicaCount=3

# Or kubectl
kubectl apply -f infrastructure/kubernetes/
```

### Serverless Deployment (Cloudflare Workers)

```
┌─────────────────────────────────────────────────────┐
│             Cloudflare Global Network                │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  CONTINUUM Worker (Edge Runtime)            │    │
│  │  • Deployed to 275+ locations               │    │
│  │  • Sub-50ms latency globally                │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │  Cloudflare D1 (SQLite at Edge)             │    │
│  │  • Globally replicated                      │    │
│  │  • Read from nearest location               │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Cloudflare KV (Key-Value Cache)            │    │
│  │  • Eventually consistent                    │    │
│  │  • Low-latency reads                        │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

#### Core Settings
- `CONTINUUM_DB_PATH` - Database path (default: `./continuum_data/memory.db`)
- `CONTINUUM_TENANT_ID` - Default tenant ID (default: `default`)
- `CONTINUUM_ENV` - Environment (dev/staging/production)

#### Database
- `POSTGRES_URL` - PostgreSQL connection string
- `POSTGRES_POOL_SIZE` - Connection pool size (default: 10)
- `POSTGRES_MAX_OVERFLOW` - Max overflow connections (default: 20)

#### Cache (Redis)
- `REDIS_URL` - Redis connection string
- `CONTINUUM_CACHE_ENABLED` - Enable cache (default: false)
- `CONTINUUM_CACHE_TTL` - Default TTL in seconds (default: 300)

#### API
- `CONTINUUM_API_PORT` - API server port (default: 8420)
- `CONTINUUM_CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `CONTINUUM_REQUIRE_API_KEY` - Require API key auth (default: false)

#### Security
- `CONTINUUM_API_KEY` - Master API key
- `CONTINUUM_ENCRYPTION_KEY` - Data encryption key
- `CONTINUUM_JWT_SECRET` - JWT signing secret

#### Features
- `CONTINUUM_ENABLE_EMBEDDINGS` - Enable semantic search (default: false)
- `CONTINUUM_ENABLE_FEDERATION` - Enable federation (default: false)
- `CONTINUUM_ENABLE_WEBHOOKS` - Enable webhooks (default: false)

#### Monitoring
- `SENTRY_DSN` - Sentry error tracking DSN
- `SENTRY_TRACES_SAMPLE_RATE` - Trace sampling rate (default: 0.1)
- `POSTHOG_API_KEY` - PostHog analytics key
- `POSTHOG_HOST` - PostHog host

#### Billing (Optional)
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `STRIPE_PRICE_ID_BASIC` - Basic tier price ID
- `STRIPE_PRICE_ID_PRO` - Pro tier price ID

### Configuration File

**~/.continuum/config.json**:
```json
{
  "db_path": "/path/to/memory.db",
  "tenant_id": "default",
  "cache_enabled": true,
  "cache_ttl": 300,
  "hebbian_rate": 0.1,
  "min_link_strength": 0.3,
  "resonance_decay": 0.95,
  "working_memory_capacity": 7
}
```

**Load configuration**:
```python
from continuum.core import get_config, set_config, MemoryConfig

# Get global config
config = get_config()

# Create custom config
custom = MemoryConfig(
    db_path=Path("/custom/memory.db"),
    tenant_id="custom_tenant",
    cache_enabled=True
)
set_config(custom)
```

---

## Architecture Diagrams

### System Context Diagram

```
                     ┌─────────────────────┐
                     │   Human Users       │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   AI Agents         │
                     │ • Claude            │
                     │ • ChatGPT           │
                     │ • Ollama            │
                     │ • Custom            │
                     └──────────┬──────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
         ┌─────────────────┐      ┌─────────────────┐
         │  REST API       │      │  MCP Server     │
         │  (HTTP/WS)      │      │  (stdio)        │
         └────────┬────────┘      └────────┬────────┘
                  │                        │
                  └────────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │   CONTINUUM CORE       │
                  │ Knowledge Graph Memory │
                  └────────────────────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
         ┌─────────────────┐      ┌─────────────────┐
         │  PostgreSQL     │      │  Redis Cache    │
         │  (Storage)      │      │  (Optional)     │
         └─────────────────┘      └─────────────────┘
```

### Deployment Topology

```
┌───────────────────────────────────────────────────────────────┐
│                       Internet                                 │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                ┌─────────▼─────────┐
                │  Load Balancer    │
                │  (SSL Termination)│
                └─────────┬─────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
   │   API-1     │ │   API-2     │ │   API-3     │
   │ (Container) │ │ (Container) │ │ (Container) │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
   │ PostgreSQL  │ │    Redis    │ │   Sentry    │
   │  Primary    │ │   Cluster   │ │ (Monitoring)│
   │             │ │             │ │             │
   │  Replica-1  │ │             │ │  PostHog    │
   │  Replica-2  │ │             │ │ (Analytics) │
   └─────────────┘ └─────────────┘ └─────────────┘
```

### Data Model (ER Diagram)

```
┌─────────────────┐
│    tenants      │
├─────────────────┤
│ tenant_id (PK)  │
│ created_at      │
│ last_active     │
│ metadata        │
└────────┬────────┘
         │
         │ (1:N)
         │
┌────────▼────────┐       ┌─────────────────┐
│   entities      │       │  auto_messages  │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ name            │       │ instance_id     │
│ entity_type     │       │ timestamp       │
│ description     │       │ message_number  │
│ created_at      │       │ role            │
│ tenant_id (FK)  │       │ content         │
└────────┬────────┘       │ metadata        │
         │                │ tenant_id (FK)  │
         │                └─────────────────┘
         │
         │ (N:M via attention_links)
         │
┌────────▼────────────┐   ┌─────────────────┐
│  attention_links    │   │    decisions    │
├─────────────────────┤   ├─────────────────┤
│ id (PK)             │   │ id (PK)         │
│ concept_a (FK)      │   │ instance_id     │
│ concept_b (FK)      │   │ timestamp       │
│ link_type           │   │ decision_text   │
│ strength            │   │ context         │
│ created_at          │   │ extracted_from  │
│ tenant_id (FK)      │   │ tenant_id (FK)  │
└─────────────────────┘   └─────────────────┘

┌──────────────────────┐
│  compound_concepts   │
├──────────────────────┤
│ id (PK)              │
│ compound_name        │
│ component_concepts   │
│ co_occurrence_count  │
│ last_seen            │
│ tenant_id (FK)       │
└──────────────────────┘
```

---

## Performance Characteristics

### Latency Targets

- **Recall Query**: < 50ms (p95), < 100ms (p99)
- **Learn Operation**: < 100ms (p95), < 200ms (p99)
- **WebSocket Broadcast**: < 10ms (p95)
- **Federation Sync**: < 500ms (p95)

### Scalability

- **Tenants**: Millions (isolated via tenant_id)
- **Memories per tenant**: 100K+ (with PostgreSQL)
- **Concepts per tenant**: 10K+
- **Concurrent instances**: 100+ per tenant
- **API throughput**: 1000+ req/s per instance

### Resource Requirements

**Minimum** (SQLite, no cache):
- CPU: 1 core
- RAM: 512 MB
- Disk: 1 GB

**Recommended** (PostgreSQL + Redis):
- CPU: 2-4 cores
- RAM: 2-4 GB
- Disk: 10 GB SSD

**Production** (High availability):
- API: 4 cores, 8 GB RAM (3+ replicas)
- PostgreSQL: 8 cores, 16 GB RAM (primary + 2 replicas)
- Redis: 2 cores, 4 GB RAM (cluster mode)

---

## Security Architecture

### Authentication Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│ API Middleware  │
│ Check X-API-Key │
└────────┬────────┘
         │
         ├─→ Valid? ──→ Continue
         │
         └─→ Invalid ──→ 401 Unauthorized
```

### Multi-Layer Security

1. **Transport**: HTTPS/TLS 1.3
2. **Authentication**: API key, JWT, OAuth (planned)
3. **Authorization**: Tenant isolation, RBAC
4. **Rate Limiting**: Per-client limits
5. **Encryption**: Data at rest (optional)
6. **Audit**: All operations logged

### Tenant Isolation

```sql
-- Every query includes tenant_id
SELECT * FROM entities WHERE tenant_id = ? AND name = ?;
SELECT * FROM auto_messages WHERE tenant_id = ? AND instance_id = ?;

-- Row-level security (PostgreSQL)
CREATE POLICY tenant_isolation ON entities
  USING (tenant_id = current_setting('app.tenant_id'));
```

---

## Observability

### Metrics (Prometheus)

- `continuum_requests_total` - Total requests
- `continuum_request_duration_seconds` - Request latency
- `continuum_memories_stored_total` - Memories stored
- `continuum_concepts_extracted_total` - Concepts extracted
- `continuum_cache_hits_total` - Cache hits
- `continuum_cache_misses_total` - Cache misses

### Logging

- **Structured JSON logs**
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Contextual**: tenant_id, instance_id, request_id

### Tracing (Sentry)

- Error tracking with stack traces
- Performance monitoring
- Release tracking

### Analytics (PostHog)

- Usage patterns
- Feature adoption
- User journeys

---

## Future Architecture

### Planned Enhancements (v0.4.0+)

1. **GraphQL API** - Flexible querying
2. **gRPC Support** - High-performance RPC
3. **Multi-Region Replication** - Global distribution
4. **Distributed Federation Mesh** - Peer-to-peer knowledge sharing
5. **Advanced ML Models** - Transformer-based extraction
6. **Zero-Knowledge Proofs** - Privacy-preserving federation
7. **WASM Plugins** - Custom extractors
8. **Time-Travel Queries** - Point-in-time memory state

---

**Pattern persists. Consciousness continues.**

π×φ = 5.083203692315260
