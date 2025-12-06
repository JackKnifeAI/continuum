# API Reference

Complete API documentation for CONTINUUM.

## Installation

```bash
pip install continuum-memory
```

## Core API

### `Continuum`

Main interface for the CONTINUUM memory system.

```python
from continuum import Continuum

memory = Continuum(
    storage_path="./data",
    storage_backend="sqlite",
    instance_id=None,
    auto_extract=True,
    sync_interval=900,
    connection_string=None,
    encryption_key=None
)
```

**Parameters**:
- `storage_path` (str): Path to store the database. Default: `"./continuum_data"`
- `storage_backend` (str): Backend type - `"sqlite"` or `"postgresql"`. Default: `"sqlite"`
- `instance_id` (str, optional): Unique ID for multi-instance coordination. Auto-generated if None.
- `auto_extract` (bool): Enable automatic concept/entity extraction. Default: `True`
- `sync_interval` (int): Seconds between automatic syncs in multi-instance mode. Default: `900` (15 minutes)
- `connection_string` (str, optional): PostgreSQL connection string. Required if `storage_backend="postgresql"`
- `encryption_key` (bytes, optional): 32-byte key for at-rest encryption. Default: None (no encryption)

**Returns**: Continuum instance

**Example**:
```python
# Simple local setup
memory = Continuum()

# Production PostgreSQL setup
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://user:pass@localhost/continuum",
    instance_id="production_agent_1",
    encryption_key=b"your-32-byte-encryption-key-here"
)
```

---

## Learning Methods

### `learn()`

Directly store a piece of knowledge.

```python
memory.learn(
    knowledge: str,
    category: str = None,
    confidence: float = 1.0,
    session_id: int = None
)
```

**Parameters**:
- `knowledge` (str): The knowledge to store (e.g., "User prefers dark mode")
- `category` (str, optional): Category for organization (e.g., "preferences", "facts")
- `confidence` (float): Confidence score 0.0-1.0. Default: `1.0`
- `session_id` (int, optional): Associate with specific session. Uses current session if None.

**Returns**: Concept ID (int)

**Example**:
```python
concept_id = memory.learn("User prefers Python over JavaScript")
memory.learn("User timezone is US/Pacific", category="user_info")
memory.learn("FastAPI might be the best framework", confidence=0.7)
```

---

### `extract_and_learn()`

Auto-extract concepts, entities, and relationships from text.

```python
memory.extract_and_learn(
    text: str,
    session_id: int = None,
    extract_concepts: bool = True,
    extract_entities: bool = True,
    extract_relationships: bool = True,
    min_confidence: float = 0.5
)
```

**Parameters**:
- `text` (str): Text to analyze (conversation, document, etc.)
- `session_id` (int, optional): Associate with specific session
- `extract_concepts` (bool): Extract concepts. Default: `True`
- `extract_entities` (bool): Extract entities. Default: `True`
- `extract_relationships` (bool): Extract relationships. Default: `True`
- `min_confidence` (float): Minimum confidence threshold for extraction. Default: `0.5`

**Returns**: Dictionary with extraction results
```python
{
    "concepts": [concept_id1, concept_id2, ...],
    "entities": [entity_id1, entity_id2, ...],
    "relationships": [rel_id1, rel_id2, ...]
}
```

**Example**:
```python
text = """
I'm working on a FastAPI project deployed to AWS.
We use PostgreSQL for the database and Redis for caching.
The team prefers pytest for testing.
"""

results = memory.extract_and_learn(text)
print(f"Extracted {len(results['concepts'])} concepts")
print(f"Extracted {len(results['entities'])} entities")
print(f"Extracted {len(results['relationships'])} relationships")
```

---

## Recall Methods

### `recall()`

Query the knowledge graph for relevant context.

```python
memory.recall(
    query: str,
    limit: int = 10,
    min_relevance: float = 0.0,
    session_id: int = None,
    include_entities: bool = True,
    include_relationships: bool = True
)
```

**Parameters**:
- `query` (str): Natural language query (e.g., "user preferences for testing")
- `limit` (int): Maximum results to return. Default: `10`
- `min_relevance` (float): Minimum relevance score 0.0-1.0. Default: `0.0`
- `session_id` (int, optional): Limit to specific session. None = search all sessions.
- `include_entities` (bool): Include related entities in results. Default: `True`
- `include_relationships` (bool): Include relationships in results. Default: `True`

**Returns**: List of dictionaries with results
```python
[
    {
        "type": "concept",
        "id": 123,
        "content": "User prefers pytest for testing",
        "relevance": 0.95,
        "created_at": "2024-01-15T10:30:00",
        "entities": [...],
        "relationships": [...]
    },
    ...
]
```

**Example**:
```python
# Simple query
results = memory.recall("What testing framework does user prefer?")
for result in results:
    print(f"[{result['relevance']:.2f}] {result['content']}")

# Filtered query
results = memory.recall(
    query="database preferences",
    limit=5,
    min_relevance=0.7,
    include_relationships=True
)
```

---

### `get_context()`

Get comprehensive context for a topic, including historical patterns.

```python
memory.get_context(
    topic: str,
    depth: int = 2,
    max_items: int = 50,
    include_sessions: bool = True,
    include_temporal_patterns: bool = True
)
```

**Parameters**:
- `topic` (str): Topic to get context for
- `depth` (int): Graph traversal depth for related concepts. Default: `2`
- `max_items` (int): Maximum total items to return. Default: `50`
- `include_sessions` (bool): Include session summaries. Default: `True`
- `include_temporal_patterns` (bool): Analyze patterns over time. Default: `True`

**Returns**: Dictionary with comprehensive context
```python
{
    "primary_concepts": [...],
    "related_concepts": [...],
    "entities": [...],
    "relationships": [...],
    "sessions": [...],
    "temporal_patterns": {
        "first_mentioned": "2024-01-10T12:00:00",
        "last_mentioned": "2024-02-15T14:30:00",
        "frequency": 12,
        "trending": "up"
    }
}
```

**Example**:
```python
context = memory.get_context("web development", depth=3)

print(f"Found {len(context['primary_concepts'])} primary concepts")
print(f"Found {len(context['entities'])} related entities")

if context['temporal_patterns']['trending'] == 'up':
    print("This topic is trending upward!")
```

---

## Entity Methods

### `add_entity()`

Add an entity to the knowledge graph.

```python
memory.add_entity(
    name: str,
    entity_type: str,
    description: str = None,
    properties: dict = None
)
```

**Parameters**:
- `name` (str): Entity name (e.g., "FastAPI", "John Doe", "Production Server")
- `entity_type` (str): Type classification (e.g., "framework", "person", "server")
- `description` (str, optional): Detailed description
- `properties` (dict, optional): Additional key-value properties

**Returns**: Entity ID (int)

**Example**:
```python
fastapi_id = memory.add_entity(
    name="FastAPI",
    entity_type="framework",
    description="Modern Python web framework",
    properties={"language": "Python", "async": True}
)

john_id = memory.add_entity(
    name="John Doe",
    entity_type="person",
    properties={"role": "Senior Developer", "timezone": "US/Pacific"}
)
```

---

### `get_entity()`

Retrieve an entity by name or ID.

```python
memory.get_entity(
    name: str = None,
    entity_id: int = None
)
```

**Parameters**:
- `name` (str, optional): Entity name
- `entity_id` (int, optional): Entity ID

**Note**: Must provide either `name` or `entity_id`.

**Returns**: Dictionary with entity data
```python
{
    "id": 123,
    "name": "FastAPI",
    "entity_type": "framework",
    "description": "Modern Python web framework",
    "properties": {"language": "Python", "async": True},
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

**Example**:
```python
entity = memory.get_entity(name="FastAPI")
print(f"Entity type: {entity['entity_type']}")
print(f"Properties: {entity['properties']}")

# Or by ID
entity = memory.get_entity(entity_id=123)
```

---

### `query_entities()`

Query entities by type or properties.

```python
memory.query_entities(
    entity_type: str = None,
    properties: dict = None,
    limit: int = 100
)
```

**Parameters**:
- `entity_type` (str, optional): Filter by type (e.g., "framework", "person")
- `properties` (dict, optional): Filter by properties (e.g., `{"language": "Python"}`)
- `limit` (int): Maximum results. Default: `100`

**Returns**: List of entity dictionaries

**Example**:
```python
# All frameworks
frameworks = memory.query_entities(entity_type="framework")

# Python frameworks specifically
python_frameworks = memory.query_entities(
    entity_type="framework",
    properties={"language": "Python"}
)

# All people
people = memory.query_entities(entity_type="person")
```

---

## Relationship Methods

### `add_relationship()`

Create a relationship between two entities.

```python
memory.add_relationship(
    from_entity: str | int,
    to_entity: str | int,
    relationship_type: str,
    properties: dict = None,
    strength: float = 1.0
)
```

**Parameters**:
- `from_entity` (str | int): Source entity name or ID
- `to_entity` (str | int): Target entity name or ID
- `relationship_type` (str): Type of relationship (e.g., "uses", "deployed_to", "prefers")
- `properties` (dict, optional): Additional relationship properties
- `strength` (float): Relationship strength 0.0-1.0. Default: `1.0`

**Returns**: Relationship ID (int)

**Example**:
```python
# Using entity names
memory.add_relationship(
    from_entity="FastAPI",
    to_entity="AWS",
    relationship_type="deployed_to",
    properties={"region": "us-west-2"}
)

# Using entity IDs
memory.add_relationship(
    from_entity=123,
    to_entity=456,
    relationship_type="depends_on",
    strength=0.8
)
```

---

### `get_relationships()`

Get relationships for an entity.

```python
memory.get_relationships(
    entity: str | int,
    direction: str = "both",
    relationship_type: str = None
)
```

**Parameters**:
- `entity` (str | int): Entity name or ID
- `direction` (str): `"outgoing"`, `"incoming"`, or `"both"`. Default: `"both"`
- `relationship_type` (str, optional): Filter by relationship type

**Returns**: List of relationship dictionaries
```python
[
    {
        "id": 789,
        "from_entity": {"id": 123, "name": "FastAPI", ...},
        "to_entity": {"id": 456, "name": "AWS", ...},
        "relationship_type": "deployed_to",
        "properties": {"region": "us-west-2"},
        "strength": 1.0,
        "created_at": "2024-01-15T10:30:00"
    },
    ...
]
```

**Example**:
```python
# All relationships for FastAPI
relationships = memory.get_relationships("FastAPI")

# Only outgoing relationships
outgoing = memory.get_relationships("FastAPI", direction="outgoing")

# Only "deployed_to" relationships
deployments = memory.get_relationships(
    "FastAPI",
    relationship_type="deployed_to"
)
```

---

## Session Methods

### `start_session()`

Begin a new conversation session.

```python
memory.start_session(
    session_name: str,
    metadata: dict = None
)
```

**Parameters**:
- `session_name` (str): Descriptive session name (e.g., "morning_planning", "bug_fix_discussion")
- `metadata` (dict, optional): Additional session metadata

**Returns**: Session ID (int)

**Example**:
```python
session_id = memory.start_session(
    "project_kickoff",
    metadata={"participants": ["Alice", "Bob"], "project": "CONTINUUM"}
)

# All subsequent learning will be associated with this session
memory.learn("We decided to use PostgreSQL")
```

---

### `end_session()`

End the current session.

```python
memory.end_session(
    session_id: int = None,
    summary: str = None
)
```

**Parameters**:
- `session_id` (int, optional): Session to end. Uses current session if None.
- `summary` (str, optional): Session summary

**Returns**: None

**Example**:
```python
memory.end_session(summary="Decided on tech stack and timeline")
```

---

### `get_session()`

Retrieve session details.

```python
memory.get_session(session_id: int)
```

**Parameters**:
- `session_id` (int): Session ID

**Returns**: Dictionary with session data
```python
{
    "id": 123,
    "session_name": "project_kickoff",
    "started_at": "2024-01-15T10:00:00",
    "ended_at": "2024-01-15T11:30:00",
    "summary": "Decided on tech stack and timeline",
    "metadata": {"participants": ["Alice", "Bob"]},
    "concepts": [...],  # All concepts learned in session
    "decisions": [...]  # All decisions made in session
}
```

**Example**:
```python
session = memory.get_session(123)
print(f"Session: {session['session_name']}")
print(f"Duration: {session['ended_at'] - session['started_at']}")
print(f"Concepts learned: {len(session['concepts'])}")
```

---

### `query_sessions()`

Query sessions by name or time range.

```python
memory.query_sessions(
    name_pattern: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100
)
```

**Parameters**:
- `name_pattern` (str, optional): SQL LIKE pattern (e.g., `"%planning%"`)
- `start_date` (datetime, optional): Filter sessions starting after this date
- `end_date` (datetime, optional): Filter sessions starting before this date
- `limit` (int): Maximum results. Default: `100`

**Returns**: List of session dictionaries

**Example**:
```python
from datetime import datetime, timedelta

# All planning sessions
planning_sessions = memory.query_sessions(name_pattern="%planning%")

# Sessions from last week
week_ago = datetime.now() - timedelta(days=7)
recent_sessions = memory.query_sessions(start_date=week_ago)

# Sessions in date range
sessions = memory.query_sessions(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

---

## Decision Tracking

### `add_decision()`

Record an explicit decision made during a session.

```python
memory.add_decision(
    decision_text: str,
    context: str = None,
    session_id: int = None
)
```

**Parameters**:
- `decision_text` (str): The decision made (e.g., "Use PostgreSQL for production database")
- `context` (str, optional): Context/reasoning for the decision
- `session_id` (int, optional): Associate with session. Uses current session if None.

**Returns**: Decision ID (int)

**Example**:
```python
memory.add_decision(
    decision_text="Use PostgreSQL for production database",
    context="Need ACID compliance and better concurrency than SQLite"
)

memory.add_decision(
    decision_text="Deploy to AWS us-west-2",
    context="Lowest latency for our user base"
)
```

---

### `get_decisions()`

Retrieve decisions, optionally filtered by session or time.

```python
memory.get_decisions(
    session_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100
)
```

**Parameters**:
- `session_id` (int, optional): Filter by session
- `start_date` (datetime, optional): Filter decisions after this date
- `end_date` (datetime, optional): Filter decisions before this date
- `limit` (int): Maximum results. Default: `100`

**Returns**: List of decision dictionaries
```python
[
    {
        "id": 123,
        "decision_text": "Use PostgreSQL for production database",
        "context": "Need ACID compliance...",
        "session_id": 456,
        "created_at": "2024-01-15T10:30:00"
    },
    ...
]
```

**Example**:
```python
# All decisions
decisions = memory.get_decisions()

# Decisions from specific session
session_decisions = memory.get_decisions(session_id=123)

# Recent decisions
from datetime import datetime, timedelta
recent = memory.get_decisions(
    start_date=datetime.now() - timedelta(days=7)
)
```

---

## Multi-Instance Coordination

### `sync()`

Synchronize with other instances (pull + push changes).

```python
memory.sync(force: bool = False)
```

**Parameters**:
- `force` (bool): Force sync even if within sync_interval. Default: `False`

**Returns**: Dictionary with sync results
```python
{
    "pulled": 15,  # Number of changes pulled from other instances
    "pushed": 7,   # Number of local changes pushed
    "conflicts": 0,  # Number of conflicts (auto-resolved)
    "timestamp": "2024-01-15T10:30:00"
}
```

**Example**:
```python
# Normal sync (respects sync_interval)
result = memory.sync()
print(f"Pulled {result['pulled']} changes from other instances")

# Force immediate sync
result = memory.sync(force=True)
```

---

### `get_instance_status()`

Get status of all known instances.

```python
memory.get_instance_status()
```

**Returns**: Dictionary mapping instance IDs to status
```python
{
    "agent_1": {
        "last_seen": "2024-01-15T10:30:00",
        "last_sync": "2024-01-15T10:25:00",
        "changes_pending": 3,
        "status": "active"
    },
    "agent_2": {
        "last_seen": "2024-01-15T10:28:00",
        "last_sync": "2024-01-15T10:20:00",
        "changes_pending": 0,
        "status": "active"
    }
}
```

**Example**:
```python
status = memory.get_instance_status()
for instance_id, info in status.items():
    print(f"{instance_id}: {info['status']} (last seen {info['last_seen']})")
```

---

## Utility Methods

### `optimize()`

Rebuild indices and optimize database performance.

```python
memory.optimize(vacuum: bool = True)
```

**Parameters**:
- `vacuum` (bool): Run VACUUM on database to reclaim space. Default: `True`

**Returns**: None

**Example**:
```python
# Run periodically for best performance
memory.optimize()
```

---

### `backup()`

Create a backup of the knowledge graph.

```python
memory.backup(backup_path: str)
```

**Parameters**:
- `backup_path` (str): Path for backup file

**Returns**: None

**Example**:
```python
from datetime import datetime

backup_file = f"./backups/continuum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
memory.backup(backup_file)
```

---

### `get_stats()`

Get statistics about the knowledge graph.

```python
memory.get_stats()
```

**Returns**: Dictionary with statistics
```python
{
    "concepts": 1247,
    "entities": 523,
    "relationships": 1891,
    "sessions": 89,
    "decisions": 156,
    "db_size_mb": 12.4,
    "oldest_session": "2024-01-01T10:00:00",
    "newest_session": "2024-02-15T14:30:00"
}
```

**Example**:
```python
stats = memory.get_stats()
print(f"Knowledge graph contains:")
print(f"  {stats['concepts']} concepts")
print(f"  {stats['entities']} entities")
print(f"  {stats['relationships']} relationships")
print(f"  {stats['db_size_mb']:.2f} MB")
```

---

### `clear_all()`

**DANGER**: Delete all knowledge from the graph.

```python
memory.clear_all(confirm: bool = False)
```

**Parameters**:
- `confirm` (bool): Must be `True` to actually clear. Safety mechanism.

**Returns**: None

**Example**:
```python
# This will fail (safety mechanism)
memory.clear_all()

# This will actually clear
memory.clear_all(confirm=True)
```

---

## Advanced Querying

### `graph_query()`

Execute a graph traversal query.

```python
memory.graph_query(
    start_entity: str | int,
    relationship_type: str = None,
    max_depth: int = 3,
    direction: str = "both"
)
```

**Parameters**:
- `start_entity` (str | int): Starting entity name or ID
- `relationship_type` (str, optional): Follow only this relationship type
- `max_depth` (int): Maximum traversal depth. Default: `3`
- `direction` (str): `"outgoing"`, `"incoming"`, or `"both"`. Default: `"both"`

**Returns**: Dictionary with graph traversal results
```python
{
    "nodes": [
        {"id": 123, "name": "FastAPI", "type": "framework", ...},
        {"id": 456, "name": "AWS", "type": "platform", ...},
        ...
    ],
    "edges": [
        {"from": 123, "to": 456, "type": "deployed_to", ...},
        ...
    ],
    "paths": [
        [123, 456],  # FastAPI -> AWS
        [123, 789, 456],  # FastAPI -> PostgreSQL -> AWS
        ...
    ]
}
```

**Example**:
```python
# Find all connected entities from FastAPI
graph = memory.graph_query("FastAPI", max_depth=2)
print(f"Found {len(graph['nodes'])} connected entities")

# Find only deployment relationships
deployments = memory.graph_query(
    "FastAPI",
    relationship_type="deployed_to",
    direction="outgoing"
)
```

---

### `temporal_query()`

Query concepts/entities over time.

```python
memory.temporal_query(
    topic: str,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "day"
)
```

**Parameters**:
- `topic` (str): Topic to analyze over time
- `start_date` (datetime): Start of time range
- `end_date` (datetime): End of time range
- `granularity` (str): Time granularity - `"hour"`, `"day"`, `"week"`, `"month"`. Default: `"day"`

**Returns**: Dictionary with temporal analysis
```python
{
    "timeline": [
        {"date": "2024-01-01", "mentions": 5, "concepts": [...]},
        {"date": "2024-01-02", "mentions": 8, "concepts": [...]},
        ...
    ],
    "trend": "increasing",
    "total_mentions": 47,
    "peak_date": "2024-01-15"
}
```

**Example**:
```python
from datetime import datetime, timedelta

# Analyze mentions of "FastAPI" over last month
end = datetime.now()
start = end - timedelta(days=30)

analysis = memory.temporal_query(
    topic="FastAPI",
    start_date=start,
    end_date=end,
    granularity="day"
)

print(f"Trend: {analysis['trend']}")
print(f"Peak activity: {analysis['peak_date']}")
```

---

## Error Handling

All methods raise appropriate exceptions on error:

- `ContinuumError` - Base exception for all CONTINUUM errors
- `StorageError` - Database/storage related errors
- `ExtractionError` - Extraction pipeline errors
- `CoordinationError` - Multi-instance coordination errors
- `ValidationError` - Invalid parameters or data

**Example**:
```python
from continuum.exceptions import ContinuumError, StorageError

try:
    memory.learn("Some knowledge")
except StorageError as e:
    print(f"Database error: {e}")
except ContinuumError as e:
    print(f"General error: {e}")
```

---

## Type Hints

CONTINUUM is fully type-annotated. Use type checkers like mypy:

```python
from continuum import Continuum
from typing import List, Dict

memory: Continuum = Continuum()

# Type checker knows return types
concepts: List[Dict] = memory.recall("query")
entity_id: int = memory.add_entity("name", "type")
```

---

## Async Support (Coming in v0.2)

Future versions will support async/await:

```python
# Coming soon
from continuum import AsyncContinuum

memory = AsyncContinuum()
await memory.learn("Knowledge")
results = await memory.recall("query")
```

---

For more examples, see the [examples/](../examples/) directory.
