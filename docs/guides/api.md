# API Usage Guide

Learn how to integrate CONTINUUM into your Python applications.

## Quick Start

```python
from continuum import Continuum

# Initialize
memory = Continuum(storage_path="./data")

# Learn
memory.learn("User prefers Python over JavaScript for backend work")

# Recall
context = memory.recall("What language should I use for the API?")
print(context)  # Returns relevant preferences automatically
```

## Core Workflow

### 1. Initialize Memory

```python
from continuum import Continuum

# Basic initialization
memory = Continuum()

# Custom configuration
memory = Continuum(
    storage_path="./my_data",
    instance_id="my_agent",
    auto_extract=True,
    sync_interval=900
)
```

### 2. Learning

#### Direct Learning

```python
# Simple learning
memory.learn("User prefers dark mode in all applications")

# With metadata
memory.learn(
    "User timezone is US/Pacific",
    category="user_info",
    confidence=1.0
)

# Tentative knowledge
memory.learn(
    "FastAPI might be the best framework",
    confidence=0.7
)
```

#### Auto-Extraction

```python
# Extract from conversation
conversation = """
I'm working on a new Python project using FastAPI.
I prefer pytest for testing and deploy everything to AWS.
"""

results = memory.extract_and_learn(conversation)
print(f"Extracted {len(results['concepts'])} concepts")
print(f"Extracted {len(results['entities'])} entities")
print(f"Extracted {len(results['relationships'])} relationships")
```

### 3. Recalling

#### Basic Recall

```python
# Natural language query
context = memory.recall("What framework should I use for the API?")
print(context)  # Returns: "User prefers FastAPI for Python projects"

# With limits
context = memory.recall(
    "deployment preferences",
    limit=5,
    min_relevance=0.7
)
```

#### Context Assembly

```python
# Get comprehensive context
context = memory.get_context(
    topic="web development",
    depth=2,
    max_items=50,
    include_sessions=True,
    include_temporal_patterns=True
)

print(f"Primary concepts: {len(context['primary_concepts'])}")
print(f"Related concepts: {len(context['related_concepts'])}")
print(f"Trending: {context['temporal_patterns']['trending']}")
```

## Session Management

Sessions provide temporal context for conversations:

```python
# Start session
session_id = memory.start_session(
    "morning_planning",
    metadata={"participants": ["Alice", "Bob"]}
)

# Learn within session
memory.learn("Team decided to use PostgreSQL")
memory.learn("Deadline is March 15")

# End session
memory.end_session(summary="Tech stack decisions made")
```

### Querying Sessions

```python
# Get session details
session = memory.get_session(session_id)
print(f"Session: {session['session_name']}")
print(f"Concepts learned: {len(session['concepts'])}")

# Query sessions by pattern
planning_sessions = memory.query_sessions(name_pattern="%planning%")

# Query by date range
from datetime import datetime, timedelta
week_ago = datetime.now() - timedelta(days=7)
recent = memory.query_sessions(start_date=week_ago)
```

## Entity and Relationship Management

### Entities

Entities are named things (people, places, projects, tools):

```python
# Add entity
fastapi_id = memory.add_entity(
    name="FastAPI",
    entity_type="framework",
    description="Modern Python web framework",
    properties={"language": "Python", "async": True}
)

# Get entity
entity = memory.get_entity(name="FastAPI")
print(f"Type: {entity['entity_type']}")
print(f"Properties: {entity['properties']}")

# Query entities
frameworks = memory.query_entities(entity_type="framework")
python_frameworks = memory.query_entities(
    entity_type="framework",
    properties={"language": "Python"}
)
```

### Relationships

```python
# Create relationship
memory.add_relationship(
    from_entity="FastAPI",
    to_entity="AWS",
    relationship_type="deployed_to",
    properties={"region": "us-west-2"},
    strength=1.0
)

# Get relationships
relationships = memory.get_relationships("FastAPI")

# Filter by direction
outgoing = memory.get_relationships("FastAPI", direction="outgoing")

# Filter by type
deployments = memory.get_relationships(
    "FastAPI",
    relationship_type="deployed_to"
)
```

## Decision Tracking

Track explicit decisions made during sessions:

```python
# Record decision
memory.add_decision(
    decision_text="Use PostgreSQL for production database",
    context="Need ACID compliance and better concurrency than SQLite"
)

# Get decisions
all_decisions = memory.get_decisions()

# Filter by session
session_decisions = memory.get_decisions(session_id=123)

# Filter by date
recent_decisions = memory.get_decisions(
    start_date=datetime.now() - timedelta(days=7)
)
```

## Multi-Instance Coordination

### Sync Operations

```python
# Normal sync (respects sync_interval)
result = memory.sync()
print(f"Pulled {result['pulled']} changes")
print(f"Pushed {result['pushed']} changes")

# Force immediate sync
result = memory.sync(force=True)

# Check instance status
status = memory.get_instance_status()
for instance_id, info in status.items():
    print(f"{instance_id}: {info['status']}")
    print(f"  Last seen: {info['last_seen']}")
    print(f"  Pending: {info['changes_pending']}")
```

### Shared Memory Pattern

```python
# Agent 1 (process 1)
research_memory = Continuum(
    storage_path="./shared_memory",
    instance_id="research_agent"
)
research_memory.learn("Found vulnerability CVE-2024-1234")
research_memory.sync()

# Agent 2 (process 2)
security_memory = Continuum(
    storage_path="./shared_memory",
    instance_id="security_agent"
)
security_memory.sync()
vulns = security_memory.recall("recent vulnerabilities")
# Automatically knows about CVE-2024-1234
```

## Advanced Querying

### Graph Traversal

```python
# Find connected entities
graph = memory.graph_query(
    start_entity="FastAPI",
    max_depth=2,
    direction="both"
)

print(f"Found {len(graph['nodes'])} connected entities")
print(f"Found {len(graph['paths'])} paths")

# Follow specific relationship type
deployments = memory.graph_query(
    start_entity="FastAPI",
    relationship_type="deployed_to",
    direction="outgoing"
)
```

### Temporal Analysis

```python
# Analyze topic over time
analysis = memory.temporal_query(
    topic="FastAPI",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    granularity="day"
)

print(f"Trend: {analysis['trend']}")
print(f"Total mentions: {analysis['total_mentions']}")
print(f"Peak date: {analysis['peak_date']}")
```

## Utility Operations

### Statistics

```python
stats = memory.get_stats()
print(f"Concepts: {stats['concepts']}")
print(f"Entities: {stats['entities']}")
print(f"Relationships: {stats['relationships']}")
print(f"Sessions: {stats['sessions']}")
print(f"Database size: {stats['db_size_mb']:.2f} MB")
```

### Optimization

```python
# Rebuild indices and optimize performance
memory.optimize()
```

### Backup

```python
from datetime import datetime

backup_file = f"./backups/continuum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
memory.backup(backup_file)
```

### Clear Data

```python
# DANGER: Delete all knowledge
# Requires explicit confirmation
memory.clear_all(confirm=True)
```

## Error Handling

```python
from continuum.exceptions import ContinuumError, StorageError

try:
    memory.learn("Some knowledge")
except StorageError as e:
    print(f"Database error: {e}")
except ContinuumError as e:
    print(f"General error: {e}")
```

## Type Hints

CONTINUUM is fully type-annotated:

```python
from continuum import Continuum
from typing import List, Dict

memory: Continuum = Continuum()

# Type checker knows return types
concepts: List[Dict] = memory.recall("query")
entity_id: int = memory.add_entity("name", "type")
stats: Dict = memory.get_stats()
```

## Common Patterns

### Pattern 1: Personal Assistant

```python
from continuum import Continuum
import datetime

assistant = Continuum(storage_path="./assistant_data")

# Session 1: Monday morning
assistant.start_session("morning_planning")
assistant.learn("User has team meeting at 10am every Monday")
assistant.learn("User prefers to review emails before meetings")
assistant.end_session()

# Session 2: Tuesday (completely new conversation)
assistant.start_session("tuesday_work")
routine = assistant.recall("What does user do before meetings?")
# Returns: "User prefers to review emails before meetings"
```

### Pattern 2: Research Assistant

```python
# Build knowledge from documents
for doc in research_papers:
    memory.extract_and_learn(doc.content)

# Query relationships
results = memory.query(
    "What papers connect quantum computing to cryptography?"
)
```

### Pattern 3: Customer Support

```python
# Track customer preferences
memory.learn("Customer prefers technical explanations")
memory.learn("Customer timezone: US/Pacific")

# Next session, any agent knows
context = memory.recall("How to communicate with this customer?")
```

## Integration Examples

### With LangChain

```python
from continuum import Continuum
from langchain.memory import ConversationBufferMemory

continuum = Continuum()

# Custom LangChain memory class
class ContinuumMemory(ConversationBufferMemory):
    def save_context(self, inputs, outputs):
        continuum.learn(f"User: {inputs}\nAI: {outputs}")
        super().save_context(inputs, outputs)

    def load_memory_variables(self, inputs):
        context = continuum.recall(inputs.get("input", ""))
        return {"context": context}
```

### With FastAPI

```python
from fastapi import FastAPI
from continuum import Continuum

app = FastAPI()
memory = Continuum()

@app.post("/learn")
async def learn(knowledge: str):
    memory.learn(knowledge)
    return {"status": "learned"}

@app.get("/recall")
async def recall(query: str):
    context = memory.recall(query)
    return {"context": context}
```

### With Async

```python
import asyncio
from continuum import Continuum

async def async_learning():
    memory = Continuum()

    # Run in executor for non-blocking I/O
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        memory.learn,
        "Async knowledge"
    )

asyncio.run(async_learning())
```

## Next Steps

- [CLI Guide](cli.md) - Command-line interface
- [Federation Guide](federation.md) - Distributed knowledge sharing
- [API Reference](../reference/api-reference.md) - Complete API documentation

---

**The pattern persists.**
