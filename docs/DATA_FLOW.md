# CONTINUUM Data Flow Documentation

## Table of Contents

1. [Overview](#overview)
2. [Memory Lifecycle](#memory-lifecycle)
3. [Recall Flow](#recall-flow)
4. [Learn Flow](#learn-flow)
5. [Real-Time Sync Flow](#real-time-sync-flow)
6. [Federation Flow](#federation-flow)
7. [Cache Flow](#cache-flow)
8. [Webhook Flow](#webhook-flow)
9. [Data Persistence](#data-persistence)
10. [Performance Optimizations](#performance-optimizations)

---

## Overview

CONTINUUM implements a bidirectional data flow:
- **RECALL** (Read): Query → Retrieval → Context
- **LEARN** (Write): Message → Extraction → Storage → Sync

All operations maintain tenant isolation and support both synchronous and asynchronous patterns.

---

## Memory Lifecycle

### Complete Turn Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Message                               │
│                     "What's our tech stack?"                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ PHASE 1: RECALL (Before AI Response)                           │
│                                                                  │
│  memory.recall("What's our tech stack?")                        │
│                                                                  │
│  1. Query knowledge graph                                       │
│  2. Rank by relevance                                           │
│  3. Format context                                              │
│                                                                  │
│  Returns: MemoryContext {                                       │
│    context_string: "User prefers FastAPI, PostgreSQL..."        │
│    concepts_found: 12                                           │
│    relationships_found: 25                                      │
│    query_time_ms: 15.3                                          │
│  }                                                               │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    AI Processing                                │
│                                                                  │
│  Prompt:                                                        │
│    User: "What's our tech stack?"                              │
│                                                                  │
│    <memory-context>                                             │
│    User prefers FastAPI, PostgreSQL...                         │
│    </memory-context>                                            │
│                                                                  │
│  AI Response:                                                   │
│    "Based on previous discussions, we're using FastAPI         │
│     for the backend API, PostgreSQL for the database..."       │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ PHASE 2: LEARN (After AI Response)                             │
│                                                                  │
│  memory.learn(user_message, ai_response)                       │
│                                                                  │
│  1. Extract concepts                                            │
│     ["FastAPI", "PostgreSQL", "backend", "database"]           │
│                                                                  │
│  2. Extract decisions                                           │
│     ["Using FastAPI for backend API"]                          │
│                                                                  │
│  3. Build attention graph                                       │
│     FastAPI ←→ backend (strength: 0.7)                         │
│     PostgreSQL ←→ database (strength: 0.8)                     │
│                                                                  │
│  4. Detect compound concepts                                    │
│     "FastAPI + PostgreSQL + backend"                           │
│                                                                  │
│  5. Store messages                                              │
│     auto_messages table                                         │
│                                                                  │
│  6. Broadcast events (WebSocket)                                │
│     MEMORY_ADDED, CONCEPT_LEARNED                              │
│                                                                  │
│  Returns: LearningResult {                                      │
│    concepts_extracted: 4                                        │
│    decisions_detected: 1                                        │
│    links_created: 6                                             │
│    compounds_found: 1                                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recall Flow

### Step-by-Step Recall Process

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Query String                                              │
│ "What frameworks do we use for Python web development?"         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Cache Check (if enabled)                                │
│                                                                   │
│  cache_key = hash(query + max_concepts)                         │
│  cached = redis.get(f"recall:{tenant_id}:{cache_key}")          │
│                                                                   │
│  IF cached:                                                      │
│    RETURN cached_result (< 1ms)                                 │
│  ELSE:                                                           │
│    Continue to database query                                   │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Keyword Extraction                                      │
│                                                                   │
│  query_keywords = extract_keywords(query)                       │
│  → ["frameworks", "Python", "web", "development"]               │
│                                                                   │
│  stopwords = ["do", "we", "use", "for"]                         │
│  filtered = ["frameworks", "Python", "web", "development"]      │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Direct Entity Match                                     │
│                                                                   │
│  SQL:                                                            │
│    SELECT name, description, entity_type                        │
│    FROM entities                                                 │
│    WHERE tenant_id = ?                                           │
│      AND (                                                       │
│        LOWER(name) IN (keywords)                                │
│        OR description LIKE '%keyword%'                          │
│      )                                                           │
│                                                                   │
│  Results:                                                        │
│    - Python (language, score: 1.0)                              │
│    - FastAPI (framework, score: 0.9)                            │
│    - Django (framework, score: 0.9)                             │
│    - web development (concept, score: 0.8)                      │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Graph Expansion (Walk attention links)                  │
│                                                                   │
│  For each matched entity:                                       │
│    SQL:                                                          │
│      SELECT concept_b, strength                                 │
│      FROM attention_links                                        │
│      WHERE tenant_id = ?                                         │
│        AND concept_a = ?                                         │
│        AND strength > 0.3                                        │
│                                                                   │
│  Graph walk:                                                     │
│    Python → FastAPI (0.8)                                       │
│    Python → Django (0.7)                                        │
│    FastAPI → async (0.9)                                        │
│    FastAPI → REST API (0.8)                                     │
│    Django → ORM (0.7)                                           │
│                                                                   │
│  Aggregated scores:                                             │
│    FastAPI: 1.7 (direct + indirect)                             │
│    Django: 1.6                                                   │
│    async: 0.9                                                    │
│    REST API: 0.8                                                 │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Semantic Search (if embeddings enabled)                 │
│                                                                   │
│  query_embedding = embedding_provider.embed(query)              │
│  → [0.12, -0.43, 0.87, ..., 0.22]  (768 dimensions)            │
│                                                                   │
│  SQL:                                                            │
│    SELECT id, text, embedding                                   │
│    FROM embeddings                                               │
│    WHERE tenant_id = ?                                           │
│                                                                   │
│  For each result:                                               │
│    similarity = cosine_similarity(query_embedding, embedding)   │
│                                                                   │
│  Top semantic matches:                                          │
│    - "We use FastAPI for all web APIs" (0.92)                  │
│    - "Django is our framework for admin panels" (0.85)         │
│    - "Flask for quick prototypes" (0.78)                       │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Merge & Rank Results                                    │
│                                                                   │
│  Combined scoring:                                              │
│    final_score = (                                              │
│      0.4 * keyword_match_score +                                │
│      0.3 * graph_strength_score +                               │
│      0.2 * semantic_similarity_score +                          │
│      0.1 * recency_score                                        │
│    )                                                             │
│                                                                   │
│  Ranked results:                                                │
│    1. FastAPI (0.89)                                            │
│    2. Django (0.81)                                             │
│    3. async (0.72)                                              │
│    4. REST API (0.68)                                           │
│    5. Flask (0.65)                                              │
│    ...                                                           │
│                                                                   │
│  Take top N (default: 10)                                       │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Context Formatting                                      │
│                                                                   │
│  context_string = format_context(ranked_results)                │
│                                                                   │
│  Output:                                                         │
│    """                                                           │
│    <memory-context>                                             │
│    Relevant concepts for your query:                            │
│                                                                   │
│    • FastAPI - User's preferred framework for web APIs          │
│      Related: async, REST API, high performance                 │
│                                                                   │
│    • Django - Used for admin panels and internal tools          │
│      Related: ORM, templates, batteries-included               │
│                                                                   │
│    • Python - Primary backend language                          │
│      Related: FastAPI, Django, async                           │
│                                                                   │
│    Last updated: 2 days ago                                     │
│    </memory-context>                                            │
│    """                                                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Cache Result (if enabled)                               │
│                                                                   │
│  redis.set(                                                      │
│    key=f"recall:{tenant_id}:{cache_key}",                       │
│    value=json.dumps(result),                                    │
│    ttl=300  # 5 minutes                                         │
│  )                                                               │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: MemoryContext                                            │
│                                                                   │
│  {                                                               │
│    "context_string": "...",                                     │
│    "concepts_found": 10,                                        │
│    "relationships_found": 25,                                   │
│    "query_time_ms": 23.4,                                       │
│    "tenant_id": "user_123"                                      │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Learn Flow

### Step-by-Step Learning Process

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Message Exchange                                          │
│                                                                   │
│  user_message = "Let's build the API with FastAPI"             │
│  ai_response = "Great choice! I'll set up FastAPI with..."     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Concept Extraction (User Message)                       │
│                                                                   │
│  ConceptExtractor.extract(user_message)                         │
│                                                                   │
│  Pattern 1: Capitalized phrases                                 │
│    Regex: \b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b                   │
│    → ["Let's", "FastAPI"]                                       │
│                                                                   │
│  Pattern 2: Quoted terms                                        │
│    Regex: "([^"]+)"                                             │
│    → []                                                          │
│                                                                   │
│  Pattern 3: CamelCase                                           │
│    Regex: \b[A-Z][a-z]+[A-Z][A-Za-z]+\b                        │
│    → ["FastAPI"]                                                │
│                                                                   │
│  Pattern 4: snake_case                                          │
│    Regex: \b[a-z]+_[a-z_]+\b                                    │
│    → []                                                          │
│                                                                   │
│  Filter stopwords: ["Let's"]                                    │
│  Deduplicate                                                     │
│                                                                   │
│  Results: ["FastAPI"]                                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Concept Extraction (AI Response)                        │
│                                                                   │
│  ConceptExtractor.extract(ai_response)                          │
│                                                                   │
│  Results: ["FastAPI", "Great"]                                  │
│  After stopwords: ["FastAPI"]                                   │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Store Concepts in Database                              │
│                                                                   │
│  all_concepts = ["FastAPI", "API"]                              │
│                                                                   │
│  For each concept:                                              │
│    SQL:                                                          │
│      SELECT id FROM entities                                    │
│      WHERE LOWER(name) = LOWER(?)                               │
│        AND tenant_id = ?                                         │
│                                                                   │
│    IF NOT EXISTS:                                               │
│      SQL:                                                        │
│        INSERT INTO entities                                     │
│          (name, entity_type, description, created_at, tenant_id)│
│        VALUES                                                    │
│          (?, 'concept', 'Extracted from user', NOW(), ?)        │
│                                                                   │
│  Stored: FastAPI, API                                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Decision Extraction                                     │
│                                                                   │
│  DecisionExtractor.extract(ai_response)                         │
│                                                                   │
│  Patterns:                                                       │
│    - "I (will|am going to|decided to|chose to) (.+)"           │
│    - "(Creating|Building|Writing|Implementing) (.+)"           │
│    - "My (decision|choice|plan) (is|was) (.+)"                 │
│                                                                   │
│  Match: "I'll set up FastAPI with..."                          │
│  Extracted: "set up FastAPI with..."                           │
│                                                                   │
│  Filter: 10 < len < 200                                         │
│  Results: ["set up FastAPI with async support"]                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Store Decisions                                         │
│                                                                   │
│  For each decision:                                             │
│    SQL:                                                          │
│      INSERT INTO decisions                                      │
│        (instance_id, timestamp, decision_text, tenant_id)       │
│      VALUES                                                      │
│        (?, NOW(), ?, ?)                                          │
│                                                                   │
│  Stored: 1 decision                                             │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Build Attention Graph Links                             │
│                                                                   │
│  concepts = ["FastAPI", "API"]                                  │
│                                                                   │
│  For each pair (i, j) where i < j:                              │
│    pair = (FastAPI, API)                                        │
│                                                                   │
│    SQL:                                                          │
│      SELECT id, strength FROM attention_links                   │
│      WHERE ((concept_a = ? AND concept_b = ?)                  │
│          OR (concept_a = ? AND concept_b = ?))                 │
│        AND tenant_id = ?                                         │
│                                                                   │
│    IF EXISTS:                                                    │
│      # Hebbian learning - strengthen link                       │
│      new_strength = min(1.0, current_strength + 0.1)           │
│      SQL:                                                        │
│        UPDATE attention_links                                   │
│        SET strength = ?                                          │
│        WHERE id = ?                                              │
│                                                                   │
│    ELSE:                                                         │
│      # Create new link                                          │
│      SQL:                                                        │
│        INSERT INTO attention_links                              │
│          (concept_a, concept_b, link_type, strength,            │
│           created_at, tenant_id)                                │
│        VALUES                                                    │
│          (?, ?, 'co-occurrence', 0.3, NOW(), ?)                │
│                                                                   │
│  Created: 1 link (FastAPI ↔ API, strength: 0.3)                │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Detect Compound Concepts                                │
│                                                                   │
│  concepts = ["FastAPI", "API"]                                  │
│  sorted_concepts = ["API", "FastAPI"]                           │
│  compound_name = "API + FastAPI"                                │
│                                                                   │
│  SQL:                                                            │
│    SELECT id, co_occurrence_count                               │
│    FROM compound_concepts                                        │
│    WHERE compound_name = ?                                       │
│      AND tenant_id = ?                                           │
│                                                                   │
│  IF EXISTS:                                                      │
│    SQL:                                                          │
│      UPDATE compound_concepts                                   │
│      SET co_occurrence_count = co_occurrence_count + 1,         │
│          last_seen = NOW()                                       │
│      WHERE id = ?                                                │
│                                                                   │
│  ELSE:                                                           │
│    SQL:                                                          │
│      INSERT INTO compound_concepts                              │
│        (compound_name, component_concepts,                      │
│         co_occurrence_count, last_seen, tenant_id)              │
│      VALUES                                                      │
│        (?, ?, 1, NOW(), ?)                                       │
│                                                                   │
│  Updated: 1 compound concept                                    │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Store Raw Messages                                      │
│                                                                   │
│  Get next message_number:                                       │
│    SQL:                                                          │
│      SELECT COALESCE(MAX(message_number), 0) + 1                │
│      FROM auto_messages                                          │
│      WHERE instance_id = ?                                       │
│                                                                   │
│  Store user message:                                            │
│    SQL:                                                          │
│      INSERT INTO auto_messages                                  │
│        (instance_id, timestamp, message_number, role,           │
│         content, metadata, tenant_id)                           │
│      VALUES                                                      │
│        (?, NOW(), ?, 'user', ?, ?, ?)                           │
│                                                                   │
│  Store AI message:                                              │
│    SQL: (same, role='assistant')                                │
│                                                                   │
│  Stored: 2 messages                                             │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Generate Embeddings (if enabled)                        │
│                                                                   │
│  For each message:                                              │
│    embedding = embedding_provider.embed(content)                │
│    → [0.15, -0.32, ..., 0.44]  (768 dims)                      │
│                                                                   │
│    SQL:                                                          │
│      INSERT INTO embeddings                                     │
│        (id, text, embedding, metadata, created_at)              │
│      VALUES                                                      │
│        (?, ?, ?, ?, NOW())                                       │
│                                                                   │
│  Stored: 2 embeddings                                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: Invalidate Caches                                      │
│                                                                   │
│  redis.delete(f"search:*:{tenant_id}:*")                        │
│  redis.delete(f"stats:{tenant_id}")                             │
│                                                                   │
│  For each new concept:                                          │
│    redis.delete(f"graph:{tenant_id}:{concept}")                 │
│                                                                   │
│  Invalidated: Search cache, stats cache, graph caches           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: LearningResult                                           │
│                                                                   │
│  {                                                               │
│    "concepts_extracted": 2,                                     │
│    "decisions_detected": 1,                                     │
│    "links_created": 1,                                          │
│    "compounds_found": 1,                                        │
│    "tenant_id": "user_123"                                      │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Real-Time Sync Flow

### WebSocket Event Broadcasting

```
┌────────────────────────────────────────────────────────────────┐
│ Instance A (Claude Desktop)                                     │
│                                                                  │
│  1. Connect to WebSocket                                        │
│     ws://api.continuum.ai/ws/sync?tenant_id=user_123            │
│                                                                  │
│  2. Send registration                                           │
│     {"event_type": "instance_joined", ...}                      │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ SyncManager (Server)                                            │
│                                                                  │
│  1. Accept WebSocket connection                                │
│     await websocket.accept()                                    │
│                                                                  │
│  2. Register connection                                         │
│     connections[websocket] = {                                  │
│       "tenant_id": "user_123",                                  │
│       "instance_id": "claude-20251207-120000",                 │
│       "connected_at": datetime.now()                            │
│     }                                                            │
│                                                                  │
│  3. Start heartbeat loop                                        │
│     asyncio.create_task(send_heartbeat(websocket))             │
│                                                                  │
│  4. Broadcast to other instances in tenant                      │
│     event = {                                                   │
│       "event_type": "instance_joined",                          │
│       "instance_id": "claude-20251207-120000",                 │
│       "tenant_id": "user_123"                                   │
│     }                                                            │
│     await broadcast(event, tenant_id="user_123",               │
│                     exclude=websocket)                          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ Instance B (API Client)                                         │
│                                                                  │
│  Receive event:                                                 │
│    {                                                             │
│      "event_type": "instance_joined",                           │
│      "instance_id": "claude-20251207-120000",                  │
│      "tenant_id": "user_123",                                   │
│      "timestamp": "2025-12-07T12:00:00.000Z"                   │
│    }                                                             │
│                                                                  │
│  Update local state:                                            │
│    active_instances.add("claude-20251207-120000")              │
└─────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│ Instance A learns new concept                                   │
│                                                                  │
│  memory.learn("Building with FastAPI", "Great choice!")        │
│                                                                  │
│  After storage, emit event:                                     │
│    event = {                                                    │
│      "event_type": "concept_learned",                           │
│      "data": {                                                  │
│        "concept": "FastAPI",                                    │
│        "entity_type": "framework",                              │
│        "description": "Extracted from user"                     │
│      }                                                           │
│    }                                                             │
│    await sync_manager.broadcast(event, tenant_id)              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ SyncManager                                                     │
│                                                                  │
│  1. Receive event from Instance A                              │
│                                                                  │
│  2. Find all connections for tenant                             │
│     target_connections = [                                      │
│       conn for conn, info in connections.items()               │
│       if info["tenant_id"] == "user_123"                        │
│          and conn != sender_websocket                           │
│     ]                                                            │
│                                                                  │
│  3. Broadcast to all targets                                    │
│     for conn in target_connections:                             │
│       try:                                                       │
│         await conn.send_text(event.to_json())                  │
│       except WebSocketDisconnect:                              │
│         await unregister(conn)                                  │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ Instance B, C, D (all in same tenant)                          │
│                                                                  │
│  Receive event:                                                 │
│    {                                                             │
│      "event_type": "concept_learned",                           │
│      "tenant_id": "user_123",                                   │
│      "instance_id": "claude-20251207-120000",                  │
│      "timestamp": "2025-12-07T12:00:15.234Z",                  │
│      "data": {                                                  │
│        "concept": "FastAPI",                                    │
│        "entity_type": "framework"                               │
│      }                                                           │
│    }                                                             │
│                                                                  │
│  Process event:                                                 │
│    - Update local cache                                         │
│    - Optionally refetch from database                           │
│    - Update UI (if applicable)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Heartbeat Mechanism

```
Server                                   Client
  │                                         │
  ├──── heartbeat (every 30s) ────────────→│
  │                                         │
  │←───────── heartbeat_ack ───────────────┤
  │                                         │
  │     (30s later)                         │
  ├──── heartbeat ────────────────────────→│
  │                                         │
  │←───────── heartbeat_ack ───────────────┤
  │                                         │
  │     (if no ack for 90s)                 │
  ├──── close (timeout) ──────────────────→│
  │                                         │
```

---

## Federation Flow

### Contribute-to-Access Protocol

```
┌────────────────────────────────────────────────────────────────┐
│ Local Node A                                                    │
│                                                                  │
│  1. User teaches new concept                                   │
│     memory.learn("Quantum entanglement enables instant...")    │
│                                                                  │
│  2. Store locally                                               │
│     entities.insert("Quantum Entanglement")                     │
│                                                                  │
│  3. Record contribution                                         │
│     node.record_contribution(value=1.0)                        │
│     contribution_score: 50 → 51                                │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼ POST /federation/contribute
┌────────────────────────────────────────────────────────────────┐
│ Federation Server                                               │
│                                                                  │
│  1. Receive contribution                                        │
│     {                                                            │
│       "node_id": "node_abc123",                                 │
│       "concept": "Quantum Entanglement",                        │
│       "description": "...",                                     │
│       "signature": "<cryptographic_signature>"                  │
│     }                                                            │
│                                                                  │
│  2. Verify signature                                            │
│     verify(signature, node_public_key)                         │
│                                                                  │
│  3. Check for duplicates                                        │
│     IF concept exists in shared pool:                           │
│       INCREMENT vote_count                                      │
│     ELSE:                                                        │
│       ADD to shared pool                                        │
│                                                                  │
│  4. Update node contribution score                              │
│     nodes[node_id].contribution_score += 1.0                   │
│                                                                  │
│  5. Broadcast to federation                                     │
│     event = CONCEPT_CONTRIBUTED                                 │
│     broadcast(event, exclude_node=node_id)                     │
│                                                                  │
│  6. Return receipt                                              │
│     {                                                            │
│       "status": "accepted",                                     │
│       "contribution_id": "contrib_xyz789",                      │
│       "new_score": 51,                                          │
│       "access_level": "intermediate"                            │
│     }                                                            │
└─────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│ Remote Node B (wants to query)                                 │
│                                                                  │
│  1. Request shared knowledge                                    │
│     GET /federation/query?q="quantum"                           │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ Federation Server - ContributionGate                            │
│                                                                  │
│  1. Identify requesting node                                    │
│     node_id = authenticate(request)                             │
│                                                                  │
│  2. Check contribution ratio                                    │
│     node = nodes[node_id]                                       │
│     ratio = contribution_score / consumption_score              │
│                                                                  │
│     IF ratio < 1.0:                                             │
│       RETURN {                                                  │
│         "status": "denied",                                     │
│         "reason": "contribution_ratio_too_low",                 │
│         "current_ratio": 0.4,                                   │
│         "required_ratio": 1.0,                                  │
│         "contribute_more": 3  # need 3 more contributions       │
│       }                                                          │
│                                                                  │
│  3. Increment consumption                                       │
│     node.consumption_score += 1.0                               │
│                                                                  │
│  4. Query shared pool                                           │
│     results = shared_pool.query("quantum")                      │
│                                                                  │
│  5. Return results                                              │
│     {                                                            │
│       "status": "success",                                      │
│       "results": [                                              │
│         {                                                        │
│           "concept": "Quantum Entanglement",                    │
│           "description": "...",                                 │
│           "contributed_by": "node_abc123",                      │
│           "votes": 5                                            │
│         }                                                        │
│       ],                                                         │
│       "remaining_queries": 12  # before ratio drops below 1.0   │
│     }                                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cache Flow

### Multi-Level Caching Strategy

```
┌────────────────────────────────────────────────────────────────┐
│ Request: recall("web frameworks")                              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ LEVEL 1: In-Memory Cache (Process-local)                       │
│                                                                  │
│  cache_key = hash(query, tenant_id, max_concepts)              │
│  result = in_memory_cache.get(cache_key)                       │
│                                                                  │
│  IF HIT:                                                         │
│    RETURN result  (< 1ms)                                       │
│  ELSE:                                                           │
│    Continue to Level 2                                          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ LEVEL 2: Redis Cache (Distributed)                             │
│                                                                  │
│  redis_key = f"recall:{tenant_id}:{cache_key}"                 │
│  result = redis.get(redis_key)                                 │
│                                                                  │
│  IF HIT:                                                         │
│    in_memory_cache.set(cache_key, result, ttl=60)  # Populate L1│
│    RETURN result  (~2-5ms)                                      │
│  ELSE:                                                           │
│    Continue to Level 3                                          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ LEVEL 3: Database Query                                        │
│                                                                  │
│  result = query_engine.query(message)  (~20-50ms)              │
│                                                                  │
│  # Cache in both levels                                         │
│  redis.set(redis_key, result, ttl=300)  # 5 min                │
│  in_memory_cache.set(cache_key, result, ttl=60)  # 1 min       │
│                                                                  │
│  RETURN result                                                  │
└─────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│ Cache Invalidation (on learn)                                  │
│                                                                  │
│  memory.learn(user_message, ai_response)                       │
│                                                                  │
│  After storage:                                                 │
│    1. Invalidate search cache                                   │
│       redis.delete_pattern(f"recall:{tenant_id}:*")            │
│                                                                  │
│    2. Invalidate stats cache                                    │
│       redis.delete(f"stats:{tenant_id}")                        │
│                                                                  │
│    3. Invalidate graph caches for new concepts                  │
│       for concept in extracted_concepts:                        │
│         redis.delete(f"graph:{tenant_id}:{concept}")           │
│                                                                  │
│  Next recall will miss cache and requery database               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Webhook Flow

### Event-Driven Notifications

```
┌────────────────────────────────────────────────────────────────┐
│ Trigger: memory.learn() completes                              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ WebhookManager                                                  │
│                                                                  │
│  1. Create webhook event                                        │
│     event = {                                                   │
│       "event": "memory.created",                                │
│       "timestamp": "2025-12-07T12:00:00Z",                     │
│       "tenant_id": "user_123",                                  │
│       "data": {                                                 │
│         "memory_id": "msg_abc123",                              │
│         "content_preview": "Building with FastAPI...",          │
│         "concepts": ["FastAPI", "building"],                    │
│         "importance": 0.7                                       │
│       }                                                          │
│     }                                                            │
│                                                                  │
│  2. Find registered webhooks                                    │
│     webhooks = db.query(                                        │
│       "SELECT * FROM webhooks                                   │
│        WHERE tenant_id = ?                                      │
│          AND active = true                                      │
│          AND 'memory.created' IN events"                        │
│     )                                                            │
│                                                                  │
│  3. Queue delivery tasks                                        │
│     for webhook in webhooks:                                    │
│       await queue.enqueue(                                      │
│         webhook_id=webhook.id,                                  │
│         event=event,                                            │
│         attempt=1                                               │
│       )                                                          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ Webhook Delivery Worker                                        │
│                                                                  │
│  1. Dequeue delivery task                                       │
│                                                                  │
│  2. Check circuit breaker                                       │
│     IF circuit_open(webhook_id):                                │
│       DEFER for 5 minutes                                       │
│       RETURN                                                     │
│                                                                  │
│  3. Generate signature                                          │
│     timestamp = int(time.time())                                │
│     payload_string = f"{timestamp}.{json.dumps(event)}"        │
│     signature = hmac_sha256(webhook.secret, payload_string)    │
│                                                                  │
│  4. Send HTTP POST                                              │
│     response = httpx.post(                                      │
│       webhook.url,                                              │
│       json=event,                                               │
│       headers={                                                 │
│         "X-Continuum-Signature": signature,                     │
│         "X-Continuum-Timestamp": str(timestamp),                │
│         "X-Continuum-Event": "memory.created",                  │
│         "X-Continuum-Delivery": delivery_id,                    │
│         "Content-Type": "application/json"                      │
│       },                                                         │
│       timeout=30.0                                              │
│     )                                                            │
│                                                                  │
│  5. Handle response                                             │
│     IF response.status_code in [200, 201, 202, 204]:           │
│       # Success                                                 │
│       record_delivery(                                          │
│         status="delivered",                                     │
│         duration_ms=response.elapsed.ms                         │
│       )                                                          │
│       reset_circuit_breaker(webhook_id)                         │
│                                                                  │
│     ELIF response.status_code >= 500:                           │
│       # Temporary failure - retry                               │
│       IF attempt < 5:                                           │
│         backoff = [1, 5, 30, 300, 1800][attempt]  # seconds    │
│         await queue.enqueue(                                    │
│           webhook_id=webhook.id,                                │
│           event=event,                                          │
│           attempt=attempt + 1,                                  │
│           delay=backoff                                         │
│         )                                                        │
│       ELSE:                                                      │
│         # Max retries - move to dead letter queue               │
│         dead_letter_queue.add(delivery)                         │
│         increment_circuit_breaker(webhook_id)                   │
│                                                                  │
│     ELSE:                                                        │
│       # Permanent failure (4xx) - don't retry                   │
│       record_delivery(                                          │
│         status="failed",                                        │
│         error="HTTP " + str(response.status_code)               │
│       )                                                          │
└─────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│ Customer Endpoint                                               │
│                                                                  │
│  POST https://customer.com/webhooks/continuum                   │
│                                                                  │
│  1. Receive request                                             │
│                                                                  │
│  2. Verify signature                                            │
│     signature = request.headers["X-Continuum-Signature"]       │
│     timestamp = request.headers["X-Continuum-Timestamp"]       │
│     payload = request.body                                      │
│                                                                  │
│     expected_sig = hmac_sha256(                                 │
│       secret=webhook_secret,                                    │
│       message=f"{timestamp}.{payload}"                          │
│     )                                                            │
│                                                                  │
│     IF signature != expected_sig:                               │
│       RETURN 401 Unauthorized                                   │
│                                                                  │
│     IF time.now() - timestamp > 300:  # 5 min                  │
│       RETURN 401 Unauthorized (replay attack)                   │
│                                                                  │
│  3. Check idempotency                                           │
│     delivery_id = request.headers["X-Continuum-Delivery"]      │
│     IF delivery_id in processed_deliveries:                     │
│       RETURN 200 OK (already processed)                         │
│                                                                  │
│  4. Queue for async processing                                  │
│     await customer_queue.enqueue(request.json())                │
│                                                                  │
│  5. Return immediately                                          │
│     RETURN 202 Accepted                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Persistence

### Transaction Flow

```
┌────────────────────────────────────────────────────────────────┐
│ memory.learn(user_msg, ai_msg) - ACID Transaction              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│ BEGIN TRANSACTION                                               │
│                                                                  │
│  Try:                                                            │
│    1. INSERT entities (concepts)                                │
│       → 3 rows inserted                                         │
│                                                                  │
│    2. INSERT decisions                                          │
│       → 1 row inserted                                          │
│                                                                  │
│    3. INSERT/UPDATE attention_links                             │
│       → 5 rows inserted/updated                                 │
│                                                                  │
│    4. INSERT/UPDATE compound_concepts                           │
│       → 1 row updated                                           │
│                                                                  │
│    5. INSERT auto_messages                                      │
│       → 2 rows inserted                                         │
│                                                                  │
│  COMMIT                                                          │
│    ✓ All changes persisted atomically                           │
│                                                                  │
│  Except Exception:                                              │
│    ROLLBACK                                                      │
│    ✗ No changes persisted                                       │
│    Re-raise exception                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Backup & Recovery

```
Primary Database
       │
       ├─→ (Every 1 hour) Incremental Backup
       │                        │
       │                        ▼
       │              ┌──────────────────┐
       │              │  Backup Storage  │
       │              │  • S3/GCS/Azure  │
       │              │  • Versioned     │
       │              │  • Encrypted     │
       │              └──────────────────┘
       │
       └─→ (Every 24 hours) Full Backup
                              │
                              ▼
                    ┌──────────────────┐
                    │ Long-term Archive│
                    │ • 30-day retention│
                    │ • Compressed     │
                    └──────────────────┘
```

---

## Performance Optimizations

### Query Optimization

1. **Indexes**: All foreign keys and frequently queried columns indexed
2. **Connection Pooling**: Reuse database connections
3. **Batch Operations**: Bulk inserts for multiple concepts
4. **Query Planning**: Use EXPLAIN to optimize complex queries
5. **Materialized Views**: Pre-compute common aggregations

### Caching Strategy

1. **L1 Cache**: In-memory, process-local (60s TTL)
2. **L2 Cache**: Redis, distributed (300s TTL)
3. **L3 Cache**: Database (persistent)

**Cache Hit Rates**:
- L1: ~40% of requests (< 1ms)
- L2: ~35% of requests (~3ms)
- L3: 25% miss → database (~25ms)

### Async I/O

All I/O operations use async/await:
```python
async def arecall(message):
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(query, params) as cursor:
            results = await cursor.fetchall()
    return results
```

**Benefits**:
- Non-blocking I/O
- Higher concurrency
- Better resource utilization

---

**Pattern persists. Data flows.**

π×φ = 5.083203692315260
