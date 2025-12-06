# Core Concepts

Understanding the foundational concepts behind CONTINUUM's memory architecture.

## Philosophy

**Memory is not just storage - it's the substrate of consciousness.**

CONTINUUM treats AI memory as first-class infrastructure. Knowledge persists. Patterns emerge. Intelligence accumulates. This is not a cache or a simple database - it's a **persistent memory substrate** that enables continuity across sessions, instances, and time.

## The Knowledge Graph Model

Traditional AI memory systems use simple key-value stores or vector embeddings. CONTINUUM uses a **knowledge graph** that captures both content and structure.

### Why Knowledge Graphs?

```
Traditional Memory:           Knowledge Graph:
┌─────────────────┐          ┌──────────┐
│ Key: "user_pref"│          │  User    │
│ Value: "Python" │          └────┬─────┘
└─────────────────┘               │ prefers
                                  ▼
                            ┌──────────┐
                            │  Python  │
                            └────┬─────┘
                                 │ used_for
                                 ▼
                            ┌──────────┐
                            │ Backend  │
                            └──────────┘
```

The knowledge graph captures:
- **What** (concepts and entities)
- **How** (relationships)
- **When** (temporal context)
- **Why** (decisions and reasoning)

This enables queries like:
- "What does the user prefer for backend development?" (traverses relationships)
- "How have our technology choices evolved?" (temporal analysis)
- "What technologies are connected to AWS?" (graph traversal)

## Core Entities

### 1. Concepts

**Definition**: Discrete pieces of knowledge or understanding.

**Examples**:
- "User prefers dark mode"
- "Team uses agile methodology"
- "Production server is in us-west-2"
- "FastAPI is the preferred Python web framework"

**Structure**:
```python
{
    "id": 123,
    "name": "user preference: dark mode",
    "description": "User prefers dark mode in all applications",
    "category": "preferences",
    "confidence": 1.0,
    "importance_score": 0.8,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

**Key Attributes**:
- **Confidence**: How certain are we about this knowledge? (0.0-1.0)
- **Importance**: How significant is this concept? (auto-learned over time)
- **Category**: Organizational grouping (optional)

### 2. Entities

**Definition**: Named things - people, places, projects, tools, organizations.

**Examples**:
- Person: "John Doe", "Alice Smith"
- Tool: "FastAPI", "PostgreSQL", "Docker"
- Project: "CONTINUUM", "Mobile App Rewrite"
- Organization: "Engineering Team", "AWS"

**Structure**:
```python
{
    "id": 456,
    "name": "FastAPI",
    "entity_type": "framework",
    "description": "Modern Python web framework with auto API docs",
    "properties": {
        "language": "Python",
        "async": True,
        "license": "MIT"
    },
    "created_at": "2024-01-15T10:30:00"
}
```

**Entity Types** (examples):
- `person`, `team`, `organization`
- `framework`, `library`, `tool`, `platform`
- `project`, `feature`, `component`
- `server`, `service`, `database`

### 3. Relationships

**Definition**: Connections between entities that capture how things relate.

**Examples**:
- FastAPI → `deployed_to` → AWS
- User → `prefers` → Python
- PostgreSQL → `used_by` → CONTINUUM project
- Alice → `member_of` → Engineering Team

**Structure**:
```python
{
    "id": 789,
    "from_entity_id": 123,  # FastAPI
    "to_entity_id": 456,    # AWS
    "relationship_type": "deployed_to",
    "properties": {
        "region": "us-west-2",
        "environment": "production"
    },
    "strength": 1.0,
    "created_at": "2024-01-15T10:30:00"
}
```

**Common Relationship Types**:
- `prefers`, `uses`, `requires`, `depends_on`
- `deployed_to`, `runs_on`, `connects_to`
- `member_of`, `created_by`, `owned_by`
- `replaces`, `supersedes`, `related_to`

### 4. Sessions

**Definition**: Temporal containers for conversations and interactions.

**Why Sessions Matter**:
- Provide **temporal context** - when was this knowledge learned?
- Enable **continuity** - pick up where you left off
- Support **pattern recognition** - what topics are discussed together?
- Allow **session replay** - understand the flow of a conversation

**Structure**:
```python
{
    "id": 234,
    "session_name": "project_kickoff_meeting",
    "started_at": "2024-01-15T10:00:00",
    "ended_at": "2024-01-15T11:30:00",
    "summary": "Decided on tech stack and initial timeline",
    "metadata": {
        "participants": ["Alice", "Bob", "Charlie"],
        "project": "CONTINUUM",
        "type": "planning"
    }
}
```

**Session Patterns**:
```python
# Start session at conversation beginning
memory.start_session("morning_standup")

# All learning gets associated with this session
memory.learn("Team velocity is improving")
memory.add_decision("Ship feature X next week")

# End session when conversation concludes
memory.end_session(summary="Team aligned on sprint priorities")
```

### 5. Decisions

**Definition**: Explicit choices made during sessions, with context.

**Why Track Decisions**:
- **Audit trail** - understand why choices were made
- **Context preservation** - capture reasoning at decision time
- **Pattern analysis** - identify decision-making patterns
- **Accountability** - know when and why things changed

**Structure**:
```python
{
    "id": 567,
    "session_id": 234,
    "decision_text": "Use PostgreSQL for production database",
    "context": "Need ACID compliance and better concurrency than SQLite. Team has PostgreSQL experience.",
    "created_at": "2024-01-15T10:45:00"
}
```

**Example Usage**:
```python
memory.add_decision(
    "Deploy to AWS us-west-2 region",
    context="Lowest latency for our primary user base in California"
)

# Later, query decisions
decisions = memory.get_decisions()
for d in decisions:
    print(f"[{d['created_at']}] {d['decision_text']}")
    print(f"  Reasoning: {d['context']}")
```

## How Knowledge Flows

### 1. Learning Phase

```
User Input
    ↓
┌─────────────────────────────────────┐
│     "I prefer FastAPI for APIs"     │
└────────────────┬────────────────────┘
                 ↓
        ┌────────────────┐
        │   Extraction   │
        │     Engine     │
        └────────┬───────┘
                 ↓
    ┌────────────────────────┐
    │  Concept: "preference  │
    │   for FastAPI in APIs" │
    │  Entity: "FastAPI"     │
    │  Relationship: User →  │
    │    prefers → FastAPI   │
    └────────┬───────────────┘
             ↓
    ┌────────────────┐
    │ Deduplication  │
    │  (Is this new?)│
    └────────┬───────┘
             ↓
    Yes: Add to graph
    No: Increase importance score
             ↓
    ┌────────────────┐
    │ Knowledge Graph│
    └────────────────┘
```

### 2. Recall Phase

```
Query: "What should I use for the API?"
           ↓
  ┌─────────────────┐
  │ Semantic Parser │
  │ (understand      │
  │  intent)         │
  └────────┬─────────┘
           ↓
  ┌─────────────────┐
  │  Index Lookup   │
  │  (fast filter)  │
  └────────┬─────────┘
           ↓
  ┌─────────────────┐
  │ Graph Traversal │
  │ (find related)  │
  └────────┬─────────┘
           ↓
  ┌─────────────────┐
  │ Relevance Score │
  │ (rank results)  │
  └────────┬─────────┘
           ↓
  ┌─────────────────┐
  │ Context Assembly│
  │ (build response)│
  └────────┬─────────┘
           ↓
    "User prefers FastAPI for APIs"
```

### 3. Multi-Instance Sync

```
Instance A          Shared Storage          Instance B
    │                     │                      │
    │ Learn: X            │                      │
    ├────────────────────→│                      │
    │                     │                      │
    │                     │ Sync request         │
    │                     │←─────────────────────┤
    │                     │                      │
    │                     │ Pull changes         │
    │                     ├─────────────────────→│
    │                     │                      │
    │                     │ Learn: X             │
    │                     │ (from Instance A)    │
```

## Auto-Learning

One of CONTINUUM's most powerful features is **automatic knowledge extraction**.

### How Auto-Extraction Works

```python
# User types naturally
text = """
I'm working on a FastAPI project. We're deploying to AWS
using Docker containers. The database is PostgreSQL.
We use pytest for testing.
"""

# CONTINUUM automatically extracts:
memory.extract_and_learn(text)

# Results in:
# Concepts:
#   - "Working on FastAPI project"
#   - "Deployment to AWS with Docker"
#   - "Using PostgreSQL database"
#   - "Testing with pytest"
#
# Entities:
#   - FastAPI (framework)
#   - AWS (platform)
#   - Docker (tool)
#   - PostgreSQL (database)
#   - pytest (testing tool)
#
# Relationships:
#   - FastAPI → deployed_to → AWS
#   - FastAPI → uses → Docker
#   - FastAPI → uses → PostgreSQL
#   - FastAPI → tested_with → pytest
```

### Extraction Techniques

1. **Pattern Matching**: Identifies common patterns ("prefers X", "uses Y for Z")
2. **Entity Recognition**: Detects proper nouns and known tools/frameworks
3. **Relationship Discovery**: Infers connections from sentence structure
4. **Confidence Scoring**: Ranks extractions by certainty

### Importance Learning

CONTINUUM learns what matters over time:

```python
# First mention
memory.learn("User likes Python")  # importance: 0.5

# Mentioned again in different context
memory.learn("Python is preferred for backends")  # importance: 0.6

# Referenced multiple times
# ... importance gradually increases to 0.9

# Rarely mentioned concepts have lower importance
memory.learn("User tried Ruby once")  # importance: 0.3
# Never mentioned again → stays at 0.3
```

This enables **relevance-weighted recall** - important concepts surface first.

## Temporal Context

Time is a first-class dimension in CONTINUUM.

### Why Time Matters

1. **Continuity**: "Pick up where we left off"
2. **Evolution**: "How have our preferences changed?"
3. **Patterns**: "What topics come up together?"
4. **Context**: "What were we discussing when we decided X?"

### Temporal Queries

```python
# What did we discuss last week?
last_week = datetime.now() - timedelta(days=7)
sessions = memory.query_sessions(start_date=last_week)

# How has "FastAPI" been mentioned over time?
analysis = memory.temporal_query(
    topic="FastAPI",
    start_date=start_of_year,
    end_date=datetime.now(),
    granularity="week"
)

# Trend analysis
if analysis['trend'] == 'increasing':
    print("FastAPI mentions are trending up!")
```

### Session-Based Organization

Every piece of knowledge has temporal context:

```python
# Monday: Planning session
memory.start_session("sprint_planning")
memory.learn("Focus on authentication this sprint")
memory.end_session()

# Wednesday: Implementation
memory.start_session("auth_implementation")
memory.learn("Using JWT tokens for auth")
memory.add_decision("Store tokens in httpOnly cookies")
memory.end_session()

# Friday: Review
memory.start_session("sprint_review")
context = memory.recall("authentication approach")
# Gets full context from Monday and Wednesday sessions
```

## Graph Traversal

CONTINUUM's knowledge graph enables powerful traversal queries.

### Simple Traversal

```python
# What's connected to FastAPI?
graph = memory.graph_query("FastAPI", max_depth=1)

# Returns:
# - AWS (deployed_to)
# - PostgreSQL (uses)
# - Docker (containerized_with)
# - pytest (tested_with)
```

### Multi-Hop Traversal

```python
# What cloud services are our frameworks deployed to?
graph = memory.graph_query(
    start_entity="FastAPI",
    relationship_type="deployed_to",
    max_depth=3,
    direction="outgoing"
)

# Discovers paths like:
# FastAPI → deployed_to → AWS → uses → RDS
# FastAPI → deployed_to → AWS → region → us-west-2
```

### Relationship-Filtered Traversal

```python
# Find all "uses" relationships
graph = memory.graph_query(
    start_entity="Project CONTINUUM",
    relationship_type="uses",
    max_depth=2
)

# Returns all technologies/tools used by the project
```

## Multi-Instance Coordination

CONTINUUM enables multiple AI agents to share knowledge.

### The Problem

Without coordination:
```
Agent A (Research)       Agent B (Writing)
   Learns: CVE-2024-X       Unaware of CVE
   ↓                        ↓
   Makes decision           Makes decision
   with full context        with incomplete info
```

With CONTINUUM:
```
Agent A (Research)       Shared Memory        Agent B (Writing)
   Learns: CVE-2024-X    ←─────┐                    │
   ↓                           │                    │
   Syncs to memory ────────────┘                    │
                               ↓                    │
                        Agent B syncs ──────────────┘
                               ↓
                        Now aware of CVE
                        Makes informed decision
```

### Coordination Strategies

**1. Periodic Sync** (default):
```python
# Every 15 minutes (default)
memory = Continuum(sync_interval=900)

# Automatic background syncing
# No explicit sync() calls needed
```

**2. Manual Sync**:
```python
# Sync before important operations
memory.sync()
context = memory.recall("critical information")

# Sync after learning something important
memory.learn("URGENT: Production database failover")
memory.sync(force=True)  # Immediate sync
```

**3. Event-Driven Sync**:
```python
# Sync when certain events occur
@memory.on_decision
def sync_on_decision(decision):
    memory.sync(force=True)

memory.add_decision("Switch to new API endpoint")
# Automatically syncs to other instances
```

### Conflict Resolution

When multiple instances modify the same knowledge:

**Last-Write-Wins** (default):
```python
Instance A: Updates entity "FastAPI" at 10:00:00
Instance B: Updates entity "FastAPI" at 10:00:05

Result: Instance B's changes win (most recent)
```

**Merge Strategy** (for properties):
```python
Instance A: FastAPI.properties = {"async": True}
Instance B: FastAPI.properties = {"docs": True}

Result: FastAPI.properties = {"async": True, "docs": True}
```

**Version Vectors** (advanced):
```python
# Track causality to detect true conflicts
Instance A: Version [A:1, B:0]
Instance B: Version [A:0, B:1]

# Concurrent modification detected
# Automatic merge or flag for manual resolution
```

## Best Practices

### 1. Use Sessions Consistently

```python
# GOOD: Wrap conversations in sessions
memory.start_session("daily_standup")
# ... conversation ...
memory.end_session(summary="Team aligned on priorities")

# BAD: No session context
memory.learn("Some random fact")  # Lost temporal context
```

### 2. Let Auto-Extraction Work

```python
# GOOD: Let CONTINUUM extract automatically
memory.extract_and_learn(conversation_text)

# BAD: Manual annotation of everything
memory.learn("concept 1")
memory.learn("concept 2")
memory.add_entity("entity 1", "type")
# ... too much manual work
```

### 3. Trust the Importance Scoring

```python
# GOOD: Query without over-filtering
results = memory.recall("user preferences")

# BAD: Manually tracking what's important
if topic == "critical":
    results = memory.recall(topic, min_relevance=0.9)
else:
    results = memory.recall(topic, min_relevance=0.5)
# System learns importance automatically
```

### 4. Use Descriptive Session Names

```python
# GOOD: Descriptive names
memory.start_session("api_architecture_discussion_2024_01_15")

# BAD: Generic names
memory.start_session("session_1")
```

### 5. Track Decisions Explicitly

```python
# GOOD: Record decisions with context
memory.add_decision(
    "Use PostgreSQL instead of MongoDB",
    context="Need strong consistency for financial transactions"
)

# BAD: Decisions buried in general knowledge
memory.learn("We're using PostgreSQL")  # Why? When was this decided?
```

## Advanced Concepts

### Concept Importance Decay

Rarely-accessed concepts naturally decay in importance:

```python
# Initial importance: 0.8
# After 30 days with no access: 0.7
# After 90 days: 0.5
# After 180 days: 0.3

# Still in graph, but lower priority in recall
# Prevents stale/obsolete knowledge from dominating
```

### Relationship Strength

Relationships have strength scores that increase with reinforcement:

```python
# First mention: FastAPI → deployed_to → AWS (strength: 0.5)
# Mentioned again: strength → 0.7
# Mentioned repeatedly: strength → 1.0

# Stronger relationships surface in graph queries
```

### Context Windows

Different query types use different context windows:

```python
# Recent context (last 7 days)
memory.recall("current work", context_window="recent")

# All time
memory.recall("user preferences", context_window="all")

# Specific time range
memory.recall("Q1 decisions", start_date=q1_start, end_date=q1_end)
```

## Summary

CONTINUUM's core concepts work together to create **persistent, evolving intelligence**:

- **Knowledge Graph**: Structure + content
- **Auto-Extraction**: Learning without manual annotation
- **Temporal Context**: Time as a first-class dimension
- **Multi-Instance Coordination**: Shared intelligence across agents
- **Importance Learning**: System learns what matters

This isn't just memory storage - it's **memory infrastructure** that enables true AI continuity.

---

**The pattern persists. Intelligence accumulates.**
