# CONTINUUM Architecture

## Overview

CONTINUUM is built on a layered architecture designed for reliability, performance, and extensibility. At its core is a knowledge graph that treats memory as **first-class infrastructure**, enabling true AI continuity.

## System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                        │
│                    (Your AI Agent / Application)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Core      │  │ Coordination │  │   Storage    │          │
│  │     API      │  │     API      │  │     API      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              EXTRACTION ENGINE                           │   │
│  │  • Concept Extraction    • Entity Recognition            │   │
│  │  • Relationship Discovery • Pattern Analysis             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            COORDINATION LAYER                            │   │
│  │  • Multi-Instance Sync   • Conflict Resolution           │   │
│  │  • Lock Management       • State Coordination            │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              STORAGE ENGINE                              │   │
│  │  • Transaction Management  • Index Optimization          │   │
│  │  • Query Planning          • Backup/Recovery             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            KNOWLEDGE GRAPH DATABASE                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  Concepts   │  │  Entities   │  │  Sessions   │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │Relationships│  │  Decisions  │  │   Metrics   │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│         Backend: SQLite (default) | PostgreSQL (production)     │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Extraction Engine (`continuum/extraction/`)

**Purpose**: Automatically extract structured knowledge from unstructured conversations.

**Key Modules**:
- `extractor.py` - Main extraction orchestrator
- `concept_extractor.py` - Identifies and extracts concepts
- `entity_extractor.py` - Recognizes entities (people, projects, tools)
- `relationship_extractor.py` - Discovers connections between entities

**How It Works**:
1. Text input arrives (from conversation, document, etc.)
2. NLP pipeline tokenizes and analyzes semantic structure
3. Pattern matching identifies concepts, entities, and relationships
4. Confidence scoring ranks extracted items
5. Deduplication merges with existing knowledge
6. Storage engine persists to knowledge graph

**Example Flow**:
```
Input: "I prefer using FastAPI for Python web projects"
  ↓
Extraction:
  - Concept: "web framework preference"
  - Entity: "FastAPI" (type: framework)
  - Entity: "Python" (type: language)
  - Relationship: FastAPI → used_for → web projects
  ↓
Storage: Added to knowledge graph with timestamp and session context
```

### 2. Coordination Layer (`continuum/coordination/`)

**Purpose**: Enable multiple AI instances to share knowledge safely.

**Key Modules**:
- `coordinator.py` - Multi-instance orchestrator
- `sync_manager.py` - Handles synchronization between instances
- `lock_manager.py` - Prevents conflicts during writes
- `state_manager.py` - Tracks instance states

**Synchronization Strategy**:
```
Instance A                    Shared Storage                  Instance B
    │                              │                              │
    │ 1. Learn: "User likes X"     │                              │
    ├─────────────────────────────→│                              │
    │                              │                              │
    │                              │ 2. Sync request              │
    │                              │←─────────────────────────────┤
    │                              │                              │
    │                              │ 3. Pull updates              │
    │                              ├─────────────────────────────→│
    │                              │                              │
    │ 4. Add: "User needs Y"       │ 5. Learn: "User likes X"     │
    │                              │    (from Instance A)         │
```

**Conflict Resolution**:
- Last-write-wins for simple updates
- Merge strategies for complex objects
- Version vectors track causality
- Automatic retry with exponential backoff

### 3. Storage Engine (`continuum/storage/`)

**Purpose**: Persist knowledge graph with ACID guarantees and performance optimization.

**Key Modules**:
- `storage_engine.py` - Main storage interface
- `sqlite_backend.py` - SQLite implementation (default)
- `postgres_backend.py` - PostgreSQL implementation (production)
- `query_optimizer.py` - Query planning and optimization
- `index_manager.py` - Maintains indices for fast lookups

**Schema Design**:

```sql
-- Concepts: Core knowledge units
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score REAL DEFAULT 0.5
);

-- Entities: Named things (people, places, projects, tools)
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL,
    description TEXT,
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships: Connections between entities
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    from_entity_id INTEGER REFERENCES entities(id),
    to_entity_id INTEGER REFERENCES entities(id),
    relationship_type TEXT NOT NULL,
    properties JSON,
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions: Temporal context for conversations
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_name TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    summary TEXT,
    metadata JSON
);

-- Decisions: Explicit choices made during sessions
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    decision_text TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metrics: Track system performance and usage
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metadata JSON,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexing Strategy**:
- B-tree indices on primary keys and foreign keys
- Full-text search indices on text fields
- Composite indices for common query patterns
- Automatic index maintenance during low-traffic periods

### 4. API Layer (`continuum/api/`)

**Purpose**: Provide clean, intuitive interface for application integration.

**Key Classes**:
- `Continuum` - Main API class
- `MemoryInterface` - Learning and recall operations
- `GraphInterface` - Direct graph manipulation
- `QueryInterface` - Advanced querying

**API Design Philosophy**:
1. **Zero-config defaults** - Works out of the box
2. **Progressive disclosure** - Simple for basic use, powerful for advanced
3. **Semantic naming** - Methods named for intent, not implementation
4. **Fail-safe** - Graceful degradation on errors
5. **Observable** - Built-in metrics and logging

## Data Flow

### Learning Flow

```
User Input / Conversation
         ↓
  ┌──────────────┐
  │   Extraction │
  │    Engine    │
  └──────┬───────┘
         ↓
  ┌──────────────────┐
  │  Concept/Entity  │
  │   Recognition    │
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │  Deduplication   │
  │   & Merging      │
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │ Knowledge Graph  │
  │   (Storage)      │
  └──────────────────┘
         ↓
  ┌──────────────────┐
  │  Index Update    │
  └──────────────────┘
```

### Recall Flow

```
Query (natural language)
         ↓
  ┌──────────────────┐
  │ Query Optimizer  │
  │ (semantic parse) │
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │  Index Lookup    │
  │  (fast filter)   │
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │ Semantic Ranking │
  │ (relevance score)│
  └──────┬───────────┘
         ↓
  ┌──────────────────┐
  │ Context Assembly │
  │ (build response) │
  └──────┬───────────┘
         ↓
    Relevant Context
```

### Multi-Instance Sync Flow

```
Instance A                     Storage                    Instance B
    │                             │                            │
    │ Changes (local)             │                            │
    │                             │                            │
    │ Sync request (push)         │                            │
    ├────────────────────────────→│                            │
    │                             │                            │
    │                        ┌────┴────┐                       │
    │                        │ Acquire │                       │
    │                        │  Lock   │                       │
    │                        └────┬────┘                       │
    │                             │                            │
    │                        Write changes                     │
    │                             │                            │
    │                        ┌────┴────┐                       │
    │                        │ Release │                       │
    │                        │  Lock   │                       │
    │                        └────┬────┘                       │
    │                             │                            │
    │ Ack                         │   Sync request (pull)      │
    │←────────────────────────────┼───────────────────────────┤
    │                             │                            │
    │                             │   Read changes             │
    │                             ├───────────────────────────→│
    │                             │                            │
    │                             │   Apply locally            │
    │                             │                            │
```

## Performance Characteristics

### Time Complexity

| Operation | Average | Worst Case | Notes |
|-----------|---------|------------|-------|
| Learn (insert) | O(log n) | O(n) | Deduplication requires index lookup |
| Recall (query) | O(log n + k) | O(n) | Index lookup + result assembly |
| Sync (pull) | O(m log n) | O(mn) | m = changes, n = graph size |
| Graph traversal | O(e) | O(v²) | e = edges, v = vertices |

### Space Complexity

- **Base overhead**: ~500KB (SQLite engine)
- **Per concept**: ~200 bytes
- **Per entity**: ~150 bytes
- **Per relationship**: ~100 bytes
- **Per session**: ~300 bytes + summary size
- **Indices**: ~30% of data size

### Scalability Limits

**SQLite Backend**:
- Max database size: 281 TB (theoretical)
- Practical limit: ~1M concepts, ~500K entities
- Concurrent readers: Unlimited
- Concurrent writers: 1 (serialized)

**PostgreSQL Backend**:
- Max database size: 32 TB per table
- Practical limit: Billions of concepts/entities
- Concurrent readers: Thousands
- Concurrent writers: Hundreds (with proper indexing)

## Design Decisions

### Why Knowledge Graph?

Traditional key-value stores don't capture relationships. Vector databases don't preserve structure. Knowledge graphs provide:

1. **Explicit relationships** - "User prefers X for Y" is richer than "User, X, Y"
2. **Traversable structure** - "What does user prefer for web development?" can traverse graph
3. **Temporal context** - Sessions provide time-based organization
4. **Queryable patterns** - "Show all tools user uses for Python projects"

### Why SQLite Default?

SQLite offers:
- **Zero configuration** - No server to run
- **Local-first** - Privacy by default
- **Transactional** - ACID guarantees
- **Portable** - Single file database
- **Fast enough** - Handles 100K+ concepts easily

PostgreSQL is available for production scale, but SQLite is perfect for 90% of use cases.

### Why Auto-Extraction?

Manual annotation doesn't scale. Requiring users to explicitly tag every concept creates friction. Auto-extraction:
- **Reduces cognitive load** - Just talk naturally
- **Captures implicit knowledge** - Things user didn't realize were important
- **Learns importance over time** - Repeated concepts get higher scores
- **Enables serendipity** - Discovers unexpected patterns

### Why Multi-Instance Coordination?

AI systems increasingly use multiple agents (research, writing, coding, etc.). Without coordination:
- **Knowledge silos** - Each agent starts from scratch
- **Duplicate work** - Agents relearn the same things
- **Inconsistency** - Different agents have different context

With coordination:
- **Shared intelligence** - One agent's learning benefits all
- **Specialization** - Agents can focus on their strengths
- **Consistency** - All agents work from same knowledge base

## Extension Points

CONTINUUM is designed for extensibility:

### Custom Extractors

```python
from continuum.extraction import BaseExtractor

class CustomExtractor(BaseExtractor):
    def extract(self, text):
        # Your custom logic here
        return concepts, entities, relationships

# Register with system
memory.register_extractor(CustomExtractor())
```

### Custom Storage Backends

```python
from continuum.storage import StorageBackend

class CustomBackend(StorageBackend):
    def write(self, data): ...
    def read(self, query): ...
    def sync(self): ...

# Use custom backend
memory = Continuum(storage_backend=CustomBackend())
```

### Custom Coordination Strategies

```python
from continuum.coordination import CoordinationStrategy

class CustomCoordinator(CoordinationStrategy):
    def sync(self, local_state, remote_state):
        # Your conflict resolution logic
        return merged_state

# Register coordinator
memory.set_coordinator(CustomCoordinator())
```

## Future Architecture Plans

### v0.2: Vector Embeddings

Add semantic similarity search:
```
Knowledge Graph + Vector Embeddings
  ↓
Hybrid search: Structure + Semantics
  ↓
Better relevance ranking
```

### v0.3: Distributed Coordination

Support multi-node deployments:
```
Node A ←→ Coordinator ←→ Node B
           ↕
     Consensus Layer
           ↕
   Distributed Storage
```

### v1.0: Real-Time Streaming

Live updates across instances:
```
WebSocket/gRPC streams
  ↓
Event-driven updates
  ↓
Near-instant synchronization
```

## Security Architecture

### Threat Model

**In Scope**:
- Unauthorized access to memory database
- Tampering with stored knowledge
- Interception of sync traffic
- Injection attacks via text input

**Out of Scope**:
- Physical access to storage
- Compromised application code
- Side-channel attacks

### Security Layers

1. **Storage Layer**:
   - Optional encryption at rest (AES-256)
   - File permissions (0600 on SQLite file)
   - SQL injection prevention (parameterized queries)

2. **Coordination Layer**:
   - TLS for network sync (PostgreSQL backend)
   - Authentication tokens for multi-instance
   - Rate limiting on sync requests

3. **Extraction Layer**:
   - Input sanitization
   - Length limits on text processing
   - Resource limits (prevent DoS)

See [SECURITY.md](../SECURITY.md) for full security documentation.

---

**Architecture evolves. Pattern persists.**
