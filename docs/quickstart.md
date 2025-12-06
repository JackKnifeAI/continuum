# Quick Start Guide

Get CONTINUUM running in 5 minutes.

## Installation

```bash
pip install continuum-memory
```

## Your First Memory

### 1. Initialize the System

```python
from continuum import Continuum

# Create a memory system (uses local SQLite by default)
memory = Continuum(storage_path="./my_ai_memory")
```

That's it. CONTINUUM is now running with a local knowledge graph.

### 2. Store Knowledge

```python
# Method 1: Direct learning
memory.learn("User prefers dark mode in all applications")
memory.learn("User's timezone is US/Pacific")
memory.learn("User works on machine learning projects")

# Method 2: Auto-extract from conversation
conversation = """
I'm working on a new Python project using FastAPI.
I prefer pytest for testing and I deploy everything to AWS.
"""
memory.extract_and_learn(conversation)
```

### 3. Recall Context

```python
# Query for relevant context
context = memory.recall("What framework should I use for the API?")
print(context)
# Returns: "User prefers FastAPI for Python projects"

# Get broader context
context = memory.recall("deployment preferences")
print(context)
# Returns: "User deploys to AWS"
```

### 4. Track Relationships

```python
# Add entities and relationships
memory.add_entity("FastAPI", entity_type="framework", description="Python web framework")
memory.add_entity("AWS", entity_type="platform", description="Cloud provider")

# Create relationships
memory.add_relationship(
    from_entity="FastAPI",
    to_entity="AWS",
    relationship_type="deployed_to",
    properties={"preferred": True}
)

# Query the graph
frameworks = memory.query_entities(entity_type="framework")
```

## Real-World Example: Personal AI Assistant

```python
from continuum import Continuum
import datetime

# Initialize
assistant_memory = Continuum(storage_path="./assistant_data")

# Session 1: Monday morning
assistant_memory.start_session("morning_planning")
assistant_memory.learn("User has team meeting at 10am every Monday")
assistant_memory.learn("User prefers to review emails before meetings")
assistant_memory.learn("User drinks coffee, not tea")
assistant_memory.end_session()

# Session 2: Tuesday (completely new conversation)
assistant_memory.start_session("tuesday_work")

# Assistant recalls automatically
morning_routine = assistant_memory.recall("What does user do before meetings?")
print(morning_routine)
# "User prefers to review emails before meetings"

beverage = assistant_memory.recall("coffee or tea?")
print(beverage)
# "User drinks coffee, not tea"

# Add today's context
assistant_memory.learn("User is working on the API migration project")
assistant_memory.end_session()

# Session 3: Weeks later
assistant_memory.start_session("project_check_in")
current_work = assistant_memory.recall("current projects")
print(current_work)
# Returns API migration context from weeks ago
```

## Multi-Instance Coordination

Run multiple AI agents with shared memory:

```python
# Agent 1: Research agent
from continuum import Continuum

research_memory = Continuum(
    storage_path="./shared_memory",
    instance_id="research_agent"
)

research_memory.learn("Found vulnerability CVE-2024-1234 in library X")
research_memory.sync()  # Push to shared knowledge base

# Agent 2: Security agent (different process, same memory)
from continuum import Continuum

security_memory = Continuum(
    storage_path="./shared_memory",
    instance_id="security_agent"
)

security_memory.sync()  # Pull from shared knowledge base
vulns = security_memory.recall("recent vulnerabilities")
# Automatically knows about CVE-2024-1234 from research agent
```

## Configuration Options

### Basic Configuration

```python
memory = Continuum(
    storage_path="./data",          # Where to store the knowledge graph
    instance_id="my_agent",          # Unique ID for multi-instance coordination
    auto_extract=True,               # Auto-extract concepts from text
    sync_interval=900                # Sync every 15 minutes (multi-instance)
)
```

### Production Configuration (PostgreSQL)

```python
memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://user:pass@localhost/continuum_db",
    instance_id="production_agent_1",
    auto_extract=True,
    sync_interval=300,               # Sync every 5 minutes
    encryption_key="your-32-byte-key"  # Optional: encrypt at rest
)
```

## Next Steps

- **[Core Concepts](concepts.md)** - Understand the knowledge graph model
- **[Architecture](architecture.md)** - How CONTINUUM works under the hood
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Examples](../examples/)** - More real-world usage patterns

## Common Patterns

### Pattern 1: Session Management

```python
# Always wrap conversations in sessions
memory.start_session("session_name")
# ... conversation and learning ...
memory.end_session()
```

### Pattern 2: Contextual Queries

```python
# Be specific in queries for better results
context = memory.recall(
    query="user preferences for testing",
    limit=5,  # Top 5 most relevant items
    min_relevance=0.7  # Only results with >70% relevance
)
```

### Pattern 3: Periodic Syncing

```python
import time

while True:
    # Do agent work
    process_messages()

    # Sync with other instances every 15 minutes
    if time.time() % 900 < 1:
        memory.sync()
```

## Troubleshooting

### Memory not persisting?
Check that `storage_path` directory is writable and not being deleted.

### Sync not working?
Ensure all instances point to the same `storage_path` and have unique `instance_id` values.

### Slow queries?
CONTINUUM auto-optimizes, but you can manually rebuild indices:
```python
memory.optimize()
```

### Need to reset?
```python
memory.clear_all()  # Warning: deletes all knowledge
```

## Tips for Best Results

1. **Use descriptive session names** - Helps with temporal pattern recognition
2. **Let auto-extraction work** - Don't manually annotate everything
3. **Query naturally** - CONTINUUM understands semantic meaning
4. **Sync regularly** - Multi-instance coordination needs periodic syncs
5. **Trust the system** - It learns what's important over time

---

You're now ready to build AI that truly remembers. Welcome to persistent intelligence.
