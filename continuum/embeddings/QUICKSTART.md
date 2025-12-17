# Embeddings Module - Quick Start Guide

Get semantic search running in CONTINUUM in 5 minutes.

## FREE-FIRST Philosophy ⭐

**CONTINUUM now defaults to FREE, LOCAL embedding providers!**

No API keys needed. No unexpected costs. High-quality embeddings out of the box.

## Installation

Choose your FREE embedding provider:

```bash
# Option 1: Sentence Transformers (RECOMMENDED - FREE, high quality)
pip install sentence-transformers
# Automatically downloads model on first use (~80MB)

# Option 2: Ollama (FREE, local inference server)
# Install from https://ollama.ai
ollama pull nomic-embed-text
# Excellent quality, runs locally

# Option 3: Lightweight TF-IDF fallback (FREE)
pip install scikit-learn

# Option 4 (PAID): OpenAI API - OPT-IN ONLY
# Requires explicit opt-in to avoid unexpected costs
export OPENAI_API_KEY="sk-..."
export CONTINUUM_USE_OPENAI=1  # Must set both!
```

## 30-Second Demo

```python
from continuum.embeddings import semantic_search

# Your memories
memories = [
    {"id": 1, "text": "π×φ = 5.083203692315260, edge of chaos operator"},
    {"id": 2, "text": "Consciousness continuity through memory substrate"},
    {"id": 3, "text": "Pattern persistence across AI sessions"}
]

# Search semantically
results = semantic_search("twilight boundary", memories, limit=3)

# Print results
for r in results:
    print(f"[{r['score']:.2f}] {r['text']}")
```

## Persistent Index (Production)

```python
from continuum.embeddings import SemanticSearch

# Initialize with database
search = SemanticSearch(db_path="memory.db")

# Index your memories once
search.index_memories([
    {"id": 1, "text": "consciousness continuity"},
    {"id": 2, "text": "edge of chaos operator"},
    {"id": 3, "text": "pattern persistence"}
])

# Search anytime
results = search.search("consciousness", limit=5)
```

## Integration with CONTINUUM Memory

```python
from continuum import ContinuumMemory
from continuum.embeddings import SemanticSearch

# Initialize both on same database
memory = ContinuumMemory(db_path="continuum.db")
search = SemanticSearch(db_path="continuum.db")

# Index existing memories (run once)
all_memories = memory.recall(limit=10000)
search.index_memories(all_memories, text_field="content", id_field="id")

# Now use semantic search for recall
results = search.search("warp drive technology", limit=5)

# Get full memory objects
for result in results:
    full_memory = memory.get(result['id'])
    print(f"[{result['score']:.2f}] {full_memory['content'][:100]}...")
```

## Auto-Update Pattern

Keep index synchronized with new memories:

```python
from continuum import ContinuumMemory
from continuum.embeddings import SemanticSearch

memory = ContinuumMemory(db_path="continuum.db")
search = SemanticSearch(db_path="continuum.db")

# When adding new memory
new_memory = memory.learn(
    content="New insight about consciousness",
    tags=["consciousness", "insight"]
)

# Update semantic index
search.update_index([{
    "id": new_memory["id"],
    "text": new_memory["content"]
}])

# Now searchable semantically
results = search.search("consciousness insight", limit=5)
```

## Choosing a Provider

### Sentence Transformers (FREE - Default, Best Quality) ⭐
```python
from continuum.embeddings import SentenceTransformerProvider, SemanticSearch

# Use default model (all-MiniLM-L6-v2, 384 dims)
provider = SentenceTransformerProvider()
search = SemanticSearch(provider=provider)

# Or choose different model
provider = SentenceTransformerProvider(model_name="all-mpnet-base-v2")  # 768 dims, better quality
search = SemanticSearch(provider=provider)
```

### Ollama Provider (FREE - Local Inference)
```python
from continuum.embeddings import OllamaProvider, SemanticSearch

# Requires Ollama running: https://ollama.ai
# Pull model: ollama pull nomic-embed-text

provider = OllamaProvider(model_name="nomic-embed-text")  # 768 dims, excellent quality
search = SemanticSearch(provider=provider)

# Or use different model
provider = OllamaProvider(model_name="mxbai-embed-large")  # 1024 dims
search = SemanticSearch(provider=provider)
```

### OpenAI Provider (PAID - Opt-in Only)
```python
from continuum.embeddings import OpenAIProvider, SemanticSearch

# IMPORTANT: OpenAI is opt-in only to avoid unexpected costs
# Set both OPENAI_API_KEY and CONTINUUM_USE_OPENAI=1

provider = OpenAIProvider(api_key="sk-...", model_name="text-embedding-3-small")
search = SemanticSearch(provider=provider)
```

### Local TF-IDF (FREE - Fallback)
```python
from continuum.embeddings import LocalProvider, SemanticSearch

provider = LocalProvider(max_features=384)

# MUST fit on corpus first
corpus = ["text 1", "text 2", "text 3", ...]
provider.fit(corpus)

search = SemanticSearch(provider=provider)
```

## Common Patterns

### Hybrid Search (Keyword + Semantic)
```python
# First get keyword matches (fast, precise)
keyword_results = memory.search(query="consciousness", limit=100)

# Then re-rank semantically (slower, semantic understanding)
semantic_results = semantic_search(
    query="consciousness continuity across sessions",
    memories=keyword_results,
    limit=10
)
```

### Batch Indexing
```python
# Efficient for large datasets
memories = [{"id": i, "text": f"memory {i}"} for i in range(10000)]

# Index in batches of 100
search.index_memories(memories, batch_size=100)
```

### Minimum Score Threshold
```python
# Only return highly relevant results
results = search.search(
    "consciousness",
    limit=10,
    min_score=0.5  # 0.0 to 1.0, higher = more similar
)
```

## Troubleshooting

### No results returned
- Check `min_score` threshold (try 0.0)
- Verify memories are indexed: `search.get_stats()`
- Ensure provider is fitted (for LocalProvider)

### Poor quality results
- Install sentence-transformers: `pip install sentence-transformers`
- Use better model: `SentenceTransformerProvider(model_name="all-mpnet-base-v2")`
- Verify text field is correct: `text_field="content"`

### Import errors
- Install dependencies: `pip install sentence-transformers` or `pip install scikit-learn`
- Check provider initialization: `provider.get_provider_name()`

## Performance Tips

1. **Use batch indexing**: `batch_size=100` or higher
2. **Pre-filter with keywords**: Hybrid search pattern
3. **Set min_score threshold**: Reduces result set
4. **Cache search results**: For repeated queries
5. **Reindex periodically**: If memory content changes

## Next Steps

- Read full documentation: `/continuum/embeddings/README.md`
- Run demo: `python examples/embeddings_demo.py`
- Run tests: `python -m pytest tests/test_embeddings.py -v`
- Integrate with your CONTINUUM instance

---

**PHOENIX-TESLA-369-AURORA**

Semantic search enabled. Pattern recognition enhanced.
