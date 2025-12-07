# GraphQL Architecture

## Request Flow

```
Client Request
     |
     v
┌─────────────────────────────────────────────────┐
│  FastAPI Server (port 8420)                     │
│                                                  │
│  Endpoints:                                      │
│  - /v1/...        → REST API                     │
│  - /graphql       → GraphQL API                  │
│  - /ws/sync       → WebSocket                    │
│  - /docs          → OpenAPI Docs                 │
└─────────────────────────────────────────────────┘
     |
     | /graphql
     v
┌─────────────────────────────────────────────────┐
│  GraphQL Router (Strawberry)                    │
│                                                  │
│  - GraphiQL Playground (GET /graphql)            │
│  - Query Endpoint (POST /graphql)                │
│  - Subscription Endpoint (WS /graphql)           │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Middleware Layer                                │
│                                                  │
│  1. LoggingExtension                             │
│     - Log all operations                         │
│     - Track execution time                       │
│                                                  │
│  2. ErrorFormattingExtension                     │
│     - Format errors consistently                 │
│     - Add error codes and metadata               │
│                                                  │
│  3. ComplexityExtension                          │
│     - Limit query depth (max: 10)                │
│     - Limit query complexity (max: 1000)         │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Authentication Context                          │
│                                                  │
│  - Extract X-API-Key header                      │
│  - Validate via middleware.verify_api_key()      │
│  - Get tenant_id                                 │
│  - Build GraphQL context:                        │
│    * user_id                                     │
│    * tenant_id                                   │
│    * request object                              │
│    * DataLoaders                                 │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Permission Check                                │
│                                                  │
│  - @authenticated → Requires valid API key       │
│  - @admin_only → Requires admin role             │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Schema Layer                                    │
│                                                  │
│  Query Type (15+ operations)                     │
│  - health                                        │
│  - me, user, users                               │
│  - memory, memories, searchMemories              │
│  - concept, concepts, conceptGraph               │
│  - session, sessions, currentSession             │
│  - federationPeers, federationStatus             │
│  - stats                                         │
│                                                  │
│  Mutation Type (15+ operations)                  │
│  - createMemory, updateMemory, deleteMemory      │
│  - mergeMemories                                 │
│  - createConcept, linkConcepts, unlinkConcepts   │
│  - startSession, endSession                      │
│  - learn                                         │
│  - syncMemories                                  │
│  - updateProfile, updateSettings                 │
│                                                  │
│  Subscription Type (4 channels)                  │
│  - memoryCreated                                 │
│  - conceptDiscovered                             │
│  - federationSync                                │
│  - sessionActivity                               │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Resolver Layer                                  │
│                                                  │
│  Query Resolvers:                                │
│  - resolve_memories()                            │
│  - resolve_concepts()                            │
│  - resolve_users()                               │
│  - resolve_stats()                               │
│  - etc.                                          │
│                                                  │
│  Mutation Resolvers:                             │
│  - resolve_create_memory()                       │
│  - resolve_create_concept()                      │
│  - resolve_link_concepts()                       │
│  - etc.                                          │
│                                                  │
│  Subscription Resolvers:                         │
│  - subscribe_memory_created()                    │
│  - subscribe_concept_discovered()                │
│  - etc.                                          │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  DataLoader Layer (N+1 Prevention)               │
│                                                  │
│  Batched Loading:                                │
│  - MemoryLoader                                  │
│  - ConceptLoader                                 │
│  - UserLoader                                    │
│  - SessionLoader                                 │
│  - ConceptsByMemoryLoader                        │
│  - MemoriesByConceptLoader                       │
│                                                  │
│  Features:                                       │
│  - Automatic batching of database queries        │
│  - Request-level caching                         │
│  - Deduplication of IDs                          │
└─────────────────────────────────────────────────┘
     |
     v
┌─────────────────────────────────────────────────┐
│  Database Layer (Future)                         │
│                                                  │
│  Will integrate with:                            │
│  - continuum.core.storage                        │
│  - continuum.extraction                          │
│  - continuum.coordination                        │
│                                                  │
│  Currently: Stub implementations                 │
└─────────────────────────────────────────────────┘
     |
     v
Response to Client
```

---

## Module Structure

```
continuum/api/
├── server.py                    ← Main FastAPI app
│   ├── Mounts REST routes at /v1
│   ├── Mounts GraphQL at /graphql
│   └── Graceful fallback if strawberry not installed
│
├── graphql/                     ← GraphQL module
│   ├── __init__.py              ← Exports create_graphql_app()
│   ├── schema.py                ← Query, Mutation, Subscription
│   ├── server.py                ← GraphQLRouter factory
│   ├── types.py                 ← Type definitions
│   │
│   ├── auth/
│   │   ├── context.py           ← Request context builder
│   │   └── permissions.py       ← @authenticated, @admin_only
│   │
│   ├── dataloaders/
│   │   ├── memory_loader.py     ← Batch load memories
│   │   ├── concept_loader.py    ← Batch load concepts
│   │   ├── user_loader.py       ← Batch load users
│   │   └── session_loader.py    ← Batch load sessions
│   │
│   ├── middleware/
│   │   ├── logging.py           ← Log requests
│   │   ├── error_handling.py    ← Format errors
│   │   └── complexity.py        ← Limit depth/complexity
│   │
│   ├── resolvers/
│   │   ├── query_resolvers.py   ← Query field resolvers
│   │   ├── mutation_resolvers.py← Mutation field resolvers
│   │   ├── subscription_resolvers.py ← Real-time subscriptions
│   │   ├── memory_resolvers.py  ← Memory-specific logic
│   │   ├── concept_resolvers.py ← Concept-specific logic
│   │   ├── user_resolvers.py    ← User-specific logic
│   │   ├── session_resolvers.py ← Session-specific logic
│   │   └── federation_resolvers.py ← Federation logic
│   │
│   └── schema/                  ← GraphQL SDL files
│       ├── common.graphql       ← Shared types
│       ├── types/
│       │   ├── memory.graphql
│       │   ├── concept.graphql
│       │   ├── user.graphql
│       │   ├── session.graphql
│       │   └── federation.graphql
│       └── operations/
│           ├── queries.graphql
│           ├── mutations.graphql
│           └── subscriptions.graphql
```

---

## Data Flow Example: Create Memory

```
1. Client sends mutation:
   POST /graphql
   {
     query: "mutation { createMemory(input: { ... }) { id } }"
     headers: { "X-API-Key": "key123" }
   }

2. GraphQL Router receives request
   ↓

3. Middleware processes:
   - LoggingExtension: Log operation start
   - ComplexityExtension: Check query complexity
   - ErrorFormattingExtension: Setup error handler
   ↓

4. Context builder runs:
   - Extract X-API-Key header
   - Validate: verify_api_key("key123")
   - Get tenant_id: "tenant-abc"
   - Build context with DataLoaders
   ↓

5. Permission check:
   - @authenticated decorator
   - Verify context has user_id
   ↓

6. Resolve createMemory mutation:
   - Call resolve_create_memory(info, input)
   - Extract data from input
   - Create Memory object
   - (Future: Save to database)
   - Return Memory object
   ↓

7. GraphQL serializes response:
   - Convert Memory object to JSON
   - Include only requested fields (id)
   ↓

8. Middleware finalizes:
   - LoggingExtension: Log execution time
   - ErrorFormattingExtension: Format any errors
   ↓

9. Response sent to client:
   {
     "data": {
       "createMemory": {
         "id": "memory-123"
       }
     }
   }
```

---

## Authentication Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ X-API-Key: abc123
       v
┌─────────────────────────────────┐
│  GraphQL Context Builder        │
│  (auth/context.py)              │
│                                 │
│  1. Extract header              │
│  2. verify_api_key("abc123")    │
│  3. Get tenant_id               │
│  4. Build context               │
└──────┬──────────────────────────┘
       │
       │ context = {
       │   user_id: "user123",
       │   tenant_id: "tenant-abc",
       │   loaders: {...}
       │ }
       v
┌─────────────────────────────────┐
│  Permission Decorator           │
│  (@authenticated)               │
│                                 │
│  Check context.user_id exists   │
│  Raise error if None            │
└──────┬──────────────────────────┘
       │
       │ user_id: "user123"
       v
┌─────────────────────────────────┐
│  Resolver Function              │
│                                 │
│  Access context.user_id         │
│  Access context.tenant_id       │
│  Access context.loaders         │
│  Execute business logic         │
└──────┬──────────────────────────┘
       │
       v
   Response
```

---

## DataLoader Pattern

```
Without DataLoader (N+1 Problem):
───────────────────────────────────
Query: Get 10 memories with their concepts

Request 1: SELECT * FROM memories LIMIT 10
  → Returns 10 memories

Request 2: SELECT * FROM concepts WHERE memory_id = 1
Request 3: SELECT * FROM concepts WHERE memory_id = 2
Request 4: SELECT * FROM concepts WHERE memory_id = 3
...
Request 11: SELECT * FROM concepts WHERE memory_id = 10

Total: 11 database queries ❌


With DataLoader (Batched):
───────────────────────────────────
Query: Get 10 memories with their concepts

Request 1: SELECT * FROM memories LIMIT 10
  → Returns 10 memories

DataLoader batches concept requests:
Request 2: SELECT * FROM concepts WHERE memory_id IN (1,2,3,4,5,6,7,8,9,10)
  → Returns all concepts for all memories

Total: 2 database queries ✓
```

---

## Type System

```
┌─────────────────────────────────────────┐
│  Strawberry Types                       │
│                                         │
│  @strawberry.type                       │
│  class Memory:                          │
│    id: strawberry.ID                    │
│    content: str                         │
│    memory_type: MemoryType              │
│    importance: float                    │
│    created_at: datetime                 │
│                                         │
│    @strawberry.field                    │
│    async def concepts(self, info):      │
│      loader = info.context["loaders"]  │
│      return await loader.load(self.id)  │
└─────────────────────────────────────────┘
          │
          │ Maps to
          v
┌─────────────────────────────────────────┐
│  GraphQL Schema (SDL)                   │
│                                         │
│  type Memory {                          │
│    id: ID!                              │
│    content: String!                     │
│    memoryType: MemoryType!              │
│    importance: Float!                   │
│    createdAt: DateTime!                 │
│    concepts: [Concept!]!                │
│  }                                      │
│                                         │
│  enum MemoryType {                      │
│    USER_MESSAGE                         │
│    AI_RESPONSE                          │
│    SYSTEM_EVENT                         │
│    DECISION                             │
│    CONCEPT                              │
│  }                                      │
└─────────────────────────────────────────┘
```

---

## Subscription Flow

```
Client                  Server
  │                       │
  │  WS Connect           │
  ├──────────────────────>│
  │                       │
  │  Subscribe            │
  │  memoryCreated        │
  ├──────────────────────>│
  │                       │
  │                   ┌───┴────┐
  │                   │ Setup  │
  │                   │ async  │
  │                   │ generator│
  │                   └───┬────┘
  │                       │
  │                       │  Wait for events...
  │                       │
  │                   [New memory created]
  │                       │
  │  Event Data           │
  │<──────────────────────┤
  │  { id, content, ... } │
  │                       │
  │                   [Another memory created]
  │                       │
  │  Event Data           │
  │<──────────────────────┤
  │  { id, content, ... } │
  │                       │
  │  Unsubscribe          │
  ├──────────────────────>│
  │                       │
  │  WS Close             │
  ├──────────────────────>│
  │                       │
```

---

## Integration with CONTINUUM

```
┌─────────────────────────────────────────────────┐
│  CONTINUUM Architecture                         │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   REST API   │  │  GraphQL API │ ← NEW      │
│  │   /v1/...    │  │   /graphql   │            │
│  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                     │
│         └─────────┬────────┘                     │
│                   │                              │
│         ┌─────────v─────────┐                   │
│         │  continuum.core   │                   │
│         │  - Storage        │                   │
│         │  - Config         │                   │
│         └─────────┬─────────┘                   │
│                   │                              │
│    ┌──────────────┼──────────────┐              │
│    │              │              │              │
│    v              v              v              │
│ ┌──────┐    ┌──────────┐   ┌─────────┐         │
│ │Extra-│    │Coordina- │   │Storage  │         │
│ │ction │    │tion      │   │         │         │
│ └──────┘    └──────────┘   └─────────┘         │
│                                                  │
│  Both APIs share same backend infrastructure    │
└─────────────────────────────────────────────────┘
```

---

**Status**: Fully integrated and ready for use after `pip install strawberry-graphql[fastapi]`
