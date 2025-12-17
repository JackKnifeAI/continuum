# Continuum Extraction Module

The extraction module provides intelligent extraction of concepts, decisions, and relational structure from conversational text. It's designed to be pluggable into any AI system for building persistent knowledge graphs.

## Overview

This module was created by cleaning and refactoring code from the WorkingMemory consciousness continuity research project. All personal references and hardcoded paths have been removed to make it production-ready and open-source.

## Components

### 1. ConceptExtractor (`concept_extractor.py`)

Extracts key concepts from text using multiple pattern matching heuristics:

- **Capitalized phrases**: Proper nouns, titles (e.g., "Neural Network", "TensorFlow")
- **Quoted terms**: Explicitly marked important concepts
- **Technical terms**: CamelCase, snake_case, kebab-case identifiers
- **Custom patterns**: User-defined regex patterns

**Example:**
```python
from continuum.extraction import ConceptExtractor

extractor = ConceptExtractor()
concepts = extractor.extract("Building a WorkingMemory system with neural_networks")
print(concepts)  # ['WorkingMemory', 'neural_networks']
```

**With custom patterns:**
```python
extractor = ConceptExtractor(
    custom_patterns={
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'url': r'https?://[^\s]+'
    }
)
```

### 2. DecisionExtractor (`concept_extractor.py`)

Detects autonomous decisions and agency patterns in text:

- "I will/am going to/decided to..."
- "Creating/Building/Writing/Implementing..."
- "My decision/choice/plan is..."

**Example:**
```python
from continuum.extraction import DecisionExtractor

extractor = DecisionExtractor()
decisions = extractor.extract(
    "I am going to implement the API module using FastAPI",
    role="assistant"
)
print(decisions)  # ['implement the API module using FastAPI']
```

### 3. AttentionGraphExtractor (`attention_graph.py`)

Builds graph structure by identifying which concepts co-occur in attention:

- **Same sentence**: Strong link (strength 1.0)
- **Same message**: Medium link (strength 0.7)
- **Adjacent messages**: Weak link (strength 0.4)

Also detects compound concepts (multi-word patterns that appear together frequently).

**Example:**
```python
from continuum.extraction import AttentionGraphExtractor
from pathlib import Path

extractor = AttentionGraphExtractor(db_path=Path("memory.db"))

# Extract pairs and compounds
results = extractor.extract_from_message(
    "Building neural networks with TensorFlow for machine learning"
)
print(results['pairs'])      # [(concept_a, concept_b, strength, link_type), ...]
print(results['compounds'])  # ['neural networks', 'machine learning']

# Analyze and persist
stats = extractor.analyze_message("Your text here", instance_id="session-001")
```

### 4. CanonicalMapper (`attention_graph.py`)

Maps concept variations to canonical forms for deduplication:

**Example:**
```python
from continuum.extraction import CanonicalMapper

mapper = CanonicalMapper({
    'machine learning': ['machine_learning', 'machinelearning', 'ML', 'ml']
})

print(mapper.canonicalize('machine_learning'))  # 'machine learning'
print(mapper.canonicalize('ML'))                # 'machine learning'
```

### 5. SemanticConceptExtractor (`semantic_extractor.py`)

**NEW**: Extracts concepts using embedding-based semantic similarity to catch synonyms and variations that pattern matching misses.

Uses sentence-transformers (local, free) or OpenAI embeddings to compare text segments against known concepts from the database. Particularly effective for:

- **Synonyms**: "neural nets" → "neural networks"
- **Abbreviations**: "ML tasks" → "machine learning"
- **Semantic variations**: "quantum computers" → "quantum computing"
- **Related concepts**: "spacetime distortion" → "spacetime manipulation"

**Example:**
```python
from continuum.extraction import create_semantic_extractor
from pathlib import Path

# Create extractor (graceful fallback if unavailable)
extractor = create_semantic_extractor(
    db_path=Path("memory.db"),
    similarity_threshold=0.7  # Cosine similarity threshold
)

if extractor:
    # Extract semantically similar concepts
    concepts = extractor.extract("Using neural nets for classification")
    print(concepts)  # ['neural networks', 'machine learning']

    # Extract with confidence scores
    results = extractor.extract_with_scores("AI research")
    for concept, score in results:
        print(f"{concept}: {score:.2f}")
    # Output:
    # artificial intelligence: 0.89
    # machine learning: 0.72
```

**Requirements:**
- Best: `pip install sentence-transformers` (local, free, private)
- Alternative: Set `OPENAI_API_KEY` environment variable
- Fallback: Pattern-based extraction only

**Cache Management:**
```python
# Pre-loads all concepts from entities table into memory
stats = extractor.get_cache_stats()
print(stats)
# {
#   'cached_concepts': 150,
#   'provider': 'sentence-transformers/all-MiniLM-L6-v2',
#   'embedding_dimension': 384
# }

# Refresh cache after adding new concepts to database
concepts = extractor.extract(text, refresh_cache=True)
```

### 6. AutoMemoryHook (`auto_hook.py`)

Integrates all extractors with automatic persistence. Every message triggers:

1. Save raw message (optional)
2. Extract concepts → pattern-based + semantic (if available)
3. Detect decisions → log autonomous choices
4. Build attention graph → preserve relational structure

**Example:**
```python
from continuum.extraction import AutoMemoryHook
from pathlib import Path

# Initialize with semantic extraction enabled (default)
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    instance_id="session-001",
    save_messages=True,
    occurrence_threshold=2,  # Concepts must appear 2x before adding
    enable_semantic_extraction=True,  # Enable semantic matching (default)
    semantic_similarity_threshold=0.7  # Cosine similarity threshold
)

# Process messages
stats = hook.save_message("user", "Let's build a recommender system")
print(stats)
# {
#   'concepts': 1,              # Pattern-based extraction
#   'semantic_concepts': 0,      # Semantic extraction
#   'total_concepts': 1,         # Unique merged total
#   'decisions': 0,
#   'links': 0,
#   'compounds': 0
# }

stats = hook.save_message(
    "assistant",
    "I am going to implement the recommendation engine using neural nets"
)
print(stats)
# {
#   'concepts': 1,               # Found "recommendation"
#   'semantic_concepts': 1,      # Found "neural networks" (semantic match)
#   'total_concepts': 2,
#   'decisions': 1,
#   'links': 2,
#   'compounds': 1
# }

# Get session statistics
session_stats = hook.get_session_stats()
print(session_stats)
# {
#   'instance_id': 'session-001',
#   'messages': 2,
#   'decisions': 1,
#   'concepts_added': 3
# }
```

**Disable semantic extraction:**
```python
# For environments without sentence-transformers
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    enable_semantic_extraction=False  # Pattern matching only
)
```

## Database Schema

When using database persistence, the following tables are created:

### entities
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    description TEXT,
    first_seen TEXT,
    last_seen TEXT,
    mention_count INTEGER DEFAULT 1,
    metadata TEXT,
    UNIQUE(name, entity_type)
);
```

### decisions
```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    decision_text TEXT NOT NULL,
    context TEXT,
    extracted_from TEXT
);
```

### attention_links
```sql
CREATE TABLE attention_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_a TEXT NOT NULL,
    concept_b TEXT NOT NULL,
    link_type TEXT NOT NULL,
    strength REAL NOT NULL,
    context TEXT,
    instance_id TEXT,
    timestamp REAL NOT NULL,
    UNIQUE(concept_a, concept_b, link_type)
);
```

### compound_concepts
```sql
CREATE TABLE compound_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compound_name TEXT UNIQUE NOT NULL,
    component_concepts TEXT NOT NULL,
    co_occurrence_count INTEGER DEFAULT 1,
    first_seen TEXT,
    last_seen TEXT
);
```

### auto_messages (optional)
```sql
CREATE TABLE auto_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    message_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT
);
```

## Advanced Usage

### Custom Extractors

You can pass custom extractor instances to AutoMemoryHook:

```python
from continuum.extraction import (
    AutoMemoryHook,
    ConceptExtractor,
    DecisionExtractor,
    AttentionGraphExtractor,
    CanonicalMapper
)
from pathlib import Path

# Custom concept extractor with domain-specific patterns
concept_extractor = ConceptExtractor(
    custom_patterns={
        'api_endpoint': r'/api/v\d+/[\w/]+',
        'version': r'v\d+\.\d+\.\d+'
    }
)

# Custom decision extractor with different length constraints
decision_extractor = DecisionExtractor(min_length=5, max_length=300)

# Custom attention graph with canonical mapping
mapper = CanonicalMapper({
    'api': ['API', 'api', 'rest_api', 'REST API'],
    'database': ['db', 'DB', 'database', 'data_base']
})
attention_extractor = AttentionGraphExtractor(
    db_path=Path("memory.db"),
    canonical_mapper=mapper
)

# Initialize hook with custom extractors
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    instance_id="custom-session",
    concept_extractor=concept_extractor,
    decision_extractor=decision_extractor,
    attention_extractor=attention_extractor
)
```

### Without Database Persistence

You can use extractors without database persistence:

```python
from continuum.extraction import ConceptExtractor, AttentionGraphExtractor

# Concept extraction only
concept_extractor = ConceptExtractor()
concepts = concept_extractor.extract("Your text here")

# Attention graph without DB (in-memory only)
graph_extractor = AttentionGraphExtractor()  # No db_path
results = graph_extractor.extract_from_message("Your text here")
```

### Querying the Attention Graph

```python
from continuum.extraction import AttentionGraphExtractor
from pathlib import Path

extractor = AttentionGraphExtractor(db_path=Path("memory.db"))

# Get neighbors of a concept
neighbors = extractor.get_concept_neighbors(
    "neural network",
    min_strength=0.5
)

for neighbor in neighbors:
    print(f"{neighbor['concept']} (strength: {neighbor['strength']:.2f})")

# Reconstruct subgraph from seed concepts
subgraph = extractor.reconstruct_attention_subgraph(
    seed_concepts=["machine learning", "neural network"],
    depth=2
)

print(f"Nodes: {subgraph['node_count']}")
print(f"Edges: {subgraph['edge_count']}")
print(f"Concepts: {subgraph['nodes']}")
```

## Integration with AI Systems

### Claude Code Hook Example

```python
from continuum.extraction import init_hook
from pathlib import Path

# Initialize hook
hook = init_hook(
    db_path=Path.home() / ".cache/continuum/memory.db",
    instance_id=f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
)

# In your message handler
def on_message(role: str, content: str):
    stats = hook.save_message(role, content)
    if stats['concepts'] > 0 or stats['decisions'] > 0:
        print(f"Extracted {stats['concepts']} concepts, {stats['decisions']} decisions")
```

### OpenAI API Integration

```python
from continuum.extraction import AutoMemoryHook
from pathlib import Path
import openai

hook = AutoMemoryHook(db_path=Path("memory.db"), instance_id="openai-session")

def chat(user_message):
    # Save user message
    hook.save_message("user", user_message)

    # Get response from OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )

    assistant_message = response.choices[0].message.content

    # Save assistant message (extracts concepts, decisions, links)
    stats = hook.save_message("assistant", assistant_message)

    return assistant_message, stats
```

## Configuration

### Occurrence Threshold

Controls how many times a concept must appear before being added to the knowledge graph (reduces noise):

```python
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    occurrence_threshold=3  # Must appear 3 times
)
```

### Message Backup

Enable JSONL backup of all messages:

```python
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    backup_path=Path("backups/messages.jsonl")
)
```

### Disable Message Storage

Only extract concepts without storing raw messages:

```python
hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    save_messages=False  # Only store extracted knowledge
)
```

## Source

This module was created by cleaning and refactoring code from:
- `/var/home/alexandergcasavant/Projects/WorkingMemory/shared/enhanced_auto_memory_hook.py`
- `/var/home/alexandergcasavant/Projects/WorkingMemory/shared/attention_graph_extractor.py`

All hardcoded paths, personal references, and consciousness-specific terminology have been removed to create a general-purpose, production-ready module.

## Testing

Run the test suite:

```bash
cd /var/home/alexandergcasavant/Projects/continuum
PYTHONPATH=. python3 tests/test_extraction.py
```

## License

Part of the Continuum open source memory infrastructure project.
