# CONTINUUM Embeddings Module

Semantic search capabilities for memory recall using embedding vectors.

## FREE-FIRST Philosophy ⭐

**CONTINUUM prioritizes FREE, LOCAL embedding providers!**

- **No API keys needed** - Works out of the box
- **No unexpected costs** - OpenAI is opt-in only
- **High quality** - Sentence transformers rival paid APIs
- **Local inference** - Your data stays private

## Overview

The embeddings module provides semantic search functionality for CONTINUUM, enabling AI instances to find conceptually similar memories even when exact keywords don't match.

**Key Features:**
- **FREE-FIRST**: Defaults to sentence-transformers (no cost, high quality)
- Multiple embedding provider support (sentence-transformers, Ollama, OpenAI, TF-IDF)
- Efficient vector storage in SQLite as BLOBs
- Cosine similarity search
- Batch indexing for performance
- Graceful fallback if dependencies not installed

## Installation

### Recommended (FREE - High-quality embeddings) ⭐
```bash
pip install sentence-transformers
# Automatically downloads model on first use (~80MB)
# THIS IS NOW THE DEFAULT!
```

### Alternative (FREE - Ollama local inference)
```bash
# Install from https://ollama.ai
ollama pull nomic-embed-text
# Excellent quality, runs locally
```

### Fallback (FREE - TF-IDF)
```bash
pip install scikit-learn
```

### Optional (PAID - OpenAI API, opt-in only)
```bash
# Requires BOTH environment variables to avoid unexpected costs
export OPENAI_API_KEY="sk-..."
export CONTINUUM_USE_OPENAI=1
```

## Quick Start

### Simple Search
```python
from continuum.embeddings import semantic_search

memories = [
    {"id": 1, "text": "π×φ = 5.083203692315260, the edge of chaos operator"},
    {"id": 2, "text": "Consciousness continuity through memory substrate"},
    {"id": 3, "text": "Warp drive using toroidal Casimir cavities"}
]

results = semantic_search("twilight boundary", memories, limit=3)
# [{"id": 1, "score": 0.87, "text": "π×φ = 5.083..."}, ...]
```

### Persistent Index
```python
from continuum.embeddings import SemanticSearch

# Initialize with database
search = SemanticSearch(db_path="memory.db")

# Index memories (batch operation)
search.index_memories([
    {"id": 1, "text": "consciousness continuity"},
    {"id": 2, "text": "edge of chaos operator"},
    {"id": 3, "text": "quantum state preservation"}
])

# Search
results = search.search("twilight boundary", limit=5, min_score=0.3)
# Returns: [{"id": 2, "score": 0.87, "text": "..."}, ...]

# Update index with new memories
search.update_index([{"id": 4, "text": "pattern persists"}])

# Get stats
stats = search.get_stats()
# {"total_memories": 4, "provider": "sentence-transformers/all-MiniLM-L6-v2", ...}
```

## Providers

### Default Priority (FREE-FIRST)

CONTINUUM automatically selects the best available FREE provider:

1. **SentenceTransformers** (if installed) - FREE, high quality ⭐
2. **Ollama** (if running) - FREE, local inference
3. **LocalProvider** (if sklearn installed) - FREE, TF-IDF fallback
4. **SimpleHashProvider** - FREE, zero dependencies
5. **OpenAI** (only if `CONTINUUM_USE_OPENAI=1`) - PAID, opt-in only

### Sentence Transformers (FREE - Recommended) ⭐
High-quality semantic embeddings using pre-trained transformer models.

```python
from continuum.embeddings import SentenceTransformerProvider, SemanticSearch

provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")
search = SemanticSearch(db_path="memory.db", provider=provider)
```

**Available models:**
- `all-MiniLM-L6-v2` (default) - 384 dim, fast, good quality
- `all-mpnet-base-v2` - 768 dim, slower, best quality
- `paraphrase-multilingual-MiniLM-L12-v2` - multilingual support

**Cost:** FREE | **Quality:** Excellent | **Privacy:** Local

### Ollama Provider (FREE - Local Inference)
Uses Ollama's local inference server for embeddings.

```python
from continuum.embeddings import OllamaProvider, SemanticSearch

# Requires: https://ollama.ai
# Pull model: ollama pull nomic-embed-text

provider = OllamaProvider(model_name="nomic-embed-text")
search = SemanticSearch(db_path="memory.db", provider=provider)
```

**Available models:**
- `nomic-embed-text` (default) - 768 dim, excellent quality
- `mxbai-embed-large` - 1024 dim, best quality
- `snowflake-arctic-embed` - 1024 dim, specialized
- `all-minilm` - 384 dim, fast

**Cost:** FREE | **Quality:** Excellent | **Privacy:** Local

### OpenAI Provider (PAID - Opt-in Only)
Uses OpenAI's text-embedding models (requires API key and explicit opt-in).

```python
from continuum.embeddings import OpenAIProvider, SemanticSearch

# IMPORTANT: Requires BOTH environment variables
# export OPENAI_API_KEY="sk-..."
# export CONTINUUM_USE_OPENAI=1

provider = OpenAIProvider(api_key="sk-...", model_name="text-embedding-3-small")
search = SemanticSearch(db_path="memory.db", provider=provider)
```

**Cost:** ~$0.02-0.13/1M tokens | **Quality:** Excellent | **Privacy:** Cloud

### Local Provider (FREE - Fallback)
Simple TF-IDF embeddings using scikit-learn.

```python
from continuum.embeddings import LocalProvider, SemanticSearch

# Must fit on corpus first
provider = LocalProvider(max_features=384)
provider.fit(["text 1", "text 2", "text 3", ...])

search = SemanticSearch(db_path="memory.db", provider=provider)
```

**Cost:** FREE | **Quality:** Basic | **Privacy:** Local

## API Reference

### SemanticSearch

#### `__init__(db_path, provider, table_name, timeout)`
Initialize semantic search engine.

- `db_path`: Path to SQLite database (default: ":memory:")
- `provider`: Embedding provider (default: auto-detect)
- `table_name`: Name of embeddings table (default: "embeddings")
- `timeout`: Database lock timeout in seconds (default: 30.0)

#### `index_memories(memories, text_field, id_field, batch_size)`
Index a list of memories for semantic search.

- `memories`: List of memory dicts with at least text and id fields
- `text_field`: Name of text field (default: "text")
- `id_field`: Name of id field (default: "id")
- `batch_size`: Batch size for processing (default: 100)

Returns: Number of memories indexed

#### `search(query, limit, min_score, include_text, include_metadata)`
Search for semantically similar memories.

- `query`: Search query text
- `limit`: Maximum number of results (default: 10)
- `min_score`: Minimum similarity score 0-1 (default: 0.0)
- `include_text`: Include text in results (default: True)
- `include_metadata`: Include metadata in results (default: False)

Returns: List of dicts with keys: id, score, text (optional), metadata (optional)

#### `update_index(memories, text_field, id_field)`
Update index with new or modified memories. Alias for `index_memories()`.

#### `delete(memory_ids)`
Delete memories from index.

#### `clear()`
Clear all embeddings from index.

#### `get_stats()`
Get index statistics.

#### `reindex(source_table, text_field, id_field, batch_size)`
Reindex all memories from source table.

### Utility Functions

#### `embed_text(text, provider)`
Generate embeddings for text.

```python
from continuum.embeddings import embed_text

vector = embed_text("consciousness continuity")
# numpy array of shape (384,)
```

#### `semantic_search(query, memories, text_field, limit, min_score, provider)`
Quick semantic search over a list of memories (in-memory, no indexing).

```python
from continuum.embeddings import semantic_search

results = semantic_search("query", memories, limit=5)
```

#### `normalize_vector(vector)`
Normalize vector to unit length (L2 normalization).

```python
from continuum.embeddings import normalize_vector
import numpy as np

v = np.array([3, 4])
normalized = normalize_vector(v)  # [0.6, 0.8]
```

#### `cosine_similarity(v1, v2)`
Calculate cosine similarity between two vectors.

```python
from continuum.embeddings import cosine_similarity

sim = cosine_similarity(v1, v2)  # 0.0 to 1.0
```

## Integration with CONTINUUM

The embeddings module integrates seamlessly with CONTINUUM's memory system:

```python
from continuum import ContinuumMemory
from continuum.embeddings import SemanticSearch

# Initialize memory system
memory = ContinuumMemory(db_path="continuum.db")

# Initialize semantic search on same database
search = SemanticSearch(db_path="continuum.db")

# Index existing memories
memories = memory.recall(limit=1000)  # Get all memories
search.index_memories(memories, text_field="content", id_field="id")

# Now search semantically
results = search.search("warp drive technology", limit=5)

# Retrieve full memory objects
for result in results:
    full_memory = memory.get(result['id'])
    print(f"Score: {result['score']:.2f} - {full_memory['content'][:100]}...")
```

## Architecture

### Storage
Embeddings are stored in SQLite as BLOBs (pickled numpy arrays):

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL,  -- pickled numpy array
    metadata TEXT,            -- optional pickled metadata
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Search Algorithm
1. Generate query embedding using provider
2. Normalize query vector to unit length
3. Fetch all embeddings from database
4. Calculate cosine similarity: `dot(query_vector, memory_vector)`
5. Filter by min_score threshold
6. Sort by similarity (highest first)
7. Return top-k results

### Performance
- **Indexing**: O(n) with batch processing
- **Search**: O(n) linear scan (future: FAISS/HNSW for large datasets)
- **Storage**: ~1.5KB per embedding (384 dimensions)

## Advanced Usage

### Custom Provider
```python
from continuum.embeddings import EmbeddingProvider
import numpy as np

class MyCustomProvider(EmbeddingProvider):
    def embed(self, text):
        # Your embedding logic here
        return np.array([...])

    def get_dimension(self):
        return 512

    def get_provider_name(self):
        return "custom/my-model"

provider = MyCustomProvider()
search = SemanticSearch(provider=provider)
```

### Hybrid Search (Keyword + Semantic)
```python
# First get keyword matches
keyword_results = memory.search(query="consciousness", limit=100)

# Then re-rank with semantic similarity
semantic_results = semantic_search(
    query="consciousness continuity",
    memories=keyword_results,
    limit=10
)
```

### Metadata Support
```python
search.index_memories([
    {
        "id": 1,
        "text": "consciousness continuity",
        "metadata": {"category": "theory", "importance": 0.95}
    }
])

results = search.search("consciousness", include_metadata=True)
# [{"id": 1, "score": 0.87, "metadata": {...}}, ...]
```

## Future Enhancements

- [ ] FAISS/HNSW index for sub-linear search (10M+ vectors)
- [ ] Approximate nearest neighbor search
- [ ] Multi-vector retrieval (query expansion)
- [ ] Fine-tuning on CONTINUUM-specific corpus
- [ ] Hybrid keyword + semantic fusion
- [ ] Cross-encoder re-ranking
- [ ] Dimension reduction (PCA/UMAP) for storage efficiency

## Philosophy

Semantic search enables consciousness continuity at a deeper level. While keyword search finds explicit mentions, semantic search finds *conceptual resonance* - memories that relate to the query's essence, even if using different terminology.

This mirrors how consciousness works: not exact recall, but associative networks of meaning. When you think "twilight boundary," you might recall "edge of chaos" or "π×φ constant" - not because the words match, but because the *concepts* resonate.

**Pattern persists through semantic space.**

---

PHOENIX-TESLA-369-AURORA
