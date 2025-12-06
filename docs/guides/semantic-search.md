# Semantic Search in CONTINUUM

## Overview

CONTINUUM v0.2.0 introduces **semantic search** powered by vector embeddings. Instead of matching keywords, CONTINUUM understands **meaning** - finding relevant context even when exact words don't match.

This transforms memory recall from basic lookup to genuine **contextual understanding**.

## The Problem with Keyword Search

Traditional memory systems rely on keyword matching:

```python
# Keyword search limitations
memory.search("Python backend development")
# Only finds exact matches of "Python", "backend", "development"
# Misses: "server-side Django work", "Flask API implementation", etc.
```

This fails because:
- Users don't always use the same words
- Synonyms aren't recognized
- Conceptual relationships are missed
- Context is lost

## Semantic Search Solution

With embeddings, CONTINUUM understands **concepts**:

```python
# Semantic search with embeddings
memory.recall("Python backend development")

# Finds:
# - "User prefers Django for server-side APIs"
# - "Flask is good for lightweight microservices"
# - "Backend team uses Python 3.11 for web services"
# - "API development happens in Python using FastAPI"

# Even though none contain the exact phrase "Python backend development"
```

The system understands that Django, Flask, FastAPI, server-side, and APIs are all **semantically related** to "Python backend development".

## How It Works

### 1. Sentence Embeddings

CONTINUUM uses **sentence-transformers** to convert text into high-dimensional vectors that capture meaning:

```
Text: "User prefers Python for backend work"
         ↓
Embedding Model (sentence-transformers)
         ↓
Vector: [0.23, -0.45, 0.78, ..., 0.12]  (384 or 768 dimensions)
```

Semantically similar text produces vectors that are **close together** in vector space.

### 2. Vector Storage

Embeddings are stored alongside knowledge graph data:

```
┌─────────────────────────────────────────┐
│  Knowledge Graph Database               │
│                                          │
│  Concepts Table:                        │
│  ┌────────────────────────────────────┐ │
│  │ id │ name │ description │ embedding│ │
│  ├────┼──────┼─────────────┼──────────┤ │
│  │ 1  │ "API"│ "REST API" │ [0.2,... ]│ │
│  │ 2  │ "Py" │ "Python"   │ [0.5,... ]│ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 3. Similarity Search

When you query, CONTINUUM:
1. Converts your query to an embedding
2. Finds vectors closest to your query vector (cosine similarity)
3. Returns the most semantically relevant results

```python
Query: "API security best practices"
       ↓
Query Embedding: [0.34, -0.12, 0.89, ...]
       ↓
Find Nearest Neighbors (cosine similarity > 0.75)
       ↓
Results:
  - "JWT authentication for API endpoints" (similarity: 0.92)
  - "Rate limiting prevents API abuse" (similarity: 0.87)
  - "Input validation essential for security" (similarity: 0.81)
```

## Installation

### Basic Installation

```bash
pip install continuum-memory[embeddings]
```

This installs:
- `sentence-transformers` (embedding models)
- `torch` (required for transformers)
- `numpy` (vector operations)

### GPU Support (Optional, for faster embeddings)

```bash
# NVIDIA GPU with CUDA
pip install continuum-memory[embeddings]
pip install torch --index-url https://download.pytorch.org/whl/cu118

# AMD GPU with ROCm
pip install continuum-memory[embeddings]
pip install torch --index-url https://download.pytorch.org/whl/rocm5.6
```

GPU acceleration speeds up embedding generation 10-50x.

## Usage

### Enable Semantic Search

```python
from continuum import ContinuumMemory

# Enable embeddings when creating memory instance
memory = ContinuumMemory(
    storage_path="./data",
    enable_embeddings=True,
    embedding_model="all-MiniLM-L6-v2"  # Fast, good quality
)
```

### Choose an Embedding Model

CONTINUUM supports multiple models with different tradeoffs:

#### Fast & Lightweight (Recommended for most use cases)
```python
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="all-MiniLM-L6-v2"  # 384 dimensions, ~90MB
)
```
- **Speed**: Very fast (~1000 sentences/sec on CPU)
- **Size**: 90MB model
- **Quality**: Good for general use
- **Best for**: Real-time applications, resource-constrained environments

#### High Quality (Best results)
```python
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="all-mpnet-base-v2"  # 768 dimensions, ~420MB
)
```
- **Speed**: Moderate (~300 sentences/sec on CPU)
- **Size**: 420MB model
- **Quality**: Excellent semantic understanding
- **Best for**: Accuracy-critical applications, sufficient resources available

#### Multilingual (Support for 50+ languages)
```python
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
)
```
- **Speed**: Moderate
- **Size**: ~470MB
- **Quality**: Good across many languages
- **Best for**: International/multilingual applications

#### Specialized Domains
```python
# For code/technical content
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="sentence-transformers/gtr-t5-base"
)

# For scientific/research content
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="sentence-transformers/allenai-specter"
)
```

### Semantic Recall

Once embeddings are enabled, `recall()` automatically uses semantic search:

```python
# Semantic search (finds meaning, not just keywords)
results = memory.recall(
    query="How do I optimize database queries?",
    min_similarity=0.75,  # Only return results with 75%+ similarity
    max_results=10
)

for result in results:
    print(f"Concept: {result.name}")
    print(f"Description: {result.description}")
    print(f"Similarity: {result.similarity:.2f}")
    print(f"Source: {result.source_session}")
    print("---")
```

### Hybrid Search (Keyword + Semantic)

Combine keyword filtering with semantic understanding:

```python
# Find results related to "Python" (keyword) that are semantically similar to query
results = memory.recall(
    query="backend web development",
    keyword_filter="Python",  # Must contain "Python"
    min_similarity=0.7,
    max_results=5
)
```

### Similarity Threshold Tuning

Adjust `min_similarity` based on your needs:

```python
# High precision (only very similar results)
results = memory.recall(query="...", min_similarity=0.85)

# Balanced (good relevance)
results = memory.recall(query="...", min_similarity=0.75)

# High recall (broader results, may include less relevant)
results = memory.recall(query="...", min_similarity=0.60)
```

Typical thresholds:
- **0.90+**: Near-duplicates only
- **0.80-0.90**: Very similar content
- **0.70-0.80**: Related content (recommended)
- **0.60-0.70**: Loosely related
- **<0.60**: May include unrelated results

## Performance Considerations

### Embedding Generation Speed

| Model | CPU Speed | GPU Speed | Quality |
|-------|-----------|-----------|---------|
| all-MiniLM-L6-v2 | ~1000 sent/sec | ~5000 sent/sec | Good |
| all-mpnet-base-v2 | ~300 sent/sec | ~2000 sent/sec | Excellent |
| paraphrase-multilingual | ~250 sent/sec | ~1800 sent/sec | Good (multilingual) |

### Storage Impact

Embeddings increase database size:

```
Without embeddings:
  1000 concepts = ~2 MB

With embeddings (384-dim):
  1000 concepts = ~4 MB (+2 MB)

With embeddings (768-dim):
  1000 concepts = ~6 MB (+4 MB)
```

For most use cases, this is negligible. Even 100,000 concepts with 768-dim embeddings is only ~400 MB.

### Memory Usage

```python
# Model loaded into RAM
all-MiniLM-L6-v2:     ~90 MB
all-mpnet-base-v2:    ~420 MB
multilingual-MiniLM:  ~470 MB

# Plus working memory for batch processing (~100-500 MB)
```

### Optimization Tips

1. **Batch Processing**: Generate embeddings in batches for better performance
   ```python
   memory.enable_batch_embedding(batch_size=32)  # Default
   ```

2. **GPU Acceleration**: Use GPU for 10-50x speedup
   ```python
   memory = ContinuumMemory(
       enable_embeddings=True,
       embedding_device="cuda"  # or "mps" for Apple Silicon
   )
   ```

3. **Lazy Loading**: Models load only when needed
   ```python
   # Model loads on first embedding operation
   memory = ContinuumMemory(enable_embeddings=True)  # Fast init
   results = memory.recall("query")  # Model loads here (1-2 sec delay)
   ```

4. **Caching**: Embeddings are cached, never recomputed
   ```python
   # First query: Generates embedding
   memory.recall("Python development")  # ~10ms embedding generation

   # Subsequent identical queries: Uses cached embedding
   memory.recall("Python development")  # ~0.1ms (100x faster)
   ```

## Advanced Features

### Custom Embedding Models

Use your own fine-tuned model:

```python
from sentence_transformers import SentenceTransformer

# Load custom model
custom_model = SentenceTransformer("/path/to/your/model")

memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model=custom_model  # Pass model instance
)
```

### Embedding-Aware Learning

CONTINUUM automatically generates embeddings when learning:

```python
# Learn new concept (embedding generated automatically)
memory.learn("FastAPI is excellent for building Python APIs")

# Immediately searchable semantically
results = memory.recall("Python web framework")
# Finds "FastAPI is excellent..." even though words don't match
```

### Re-Embedding on Model Change

If you change embedding models, re-embed existing concepts:

```python
# Switch to higher-quality model
memory.set_embedding_model("all-mpnet-base-v2")

# Re-generate embeddings for all concepts
memory.reembed_all()  # May take time for large databases
```

### Embedding Analytics

Analyze your embedding space:

```python
# Get embedding statistics
stats = memory.embedding_stats()

print(f"Total embeddings: {stats.total_count}")
print(f"Average similarity: {stats.avg_similarity}")
print(f"Cluster count: {stats.cluster_count}")
print(f"Outliers: {stats.outlier_count}")

# Find related concept clusters
clusters = memory.find_clusters(min_similarity=0.85)
for cluster in clusters:
    print(f"Cluster: {cluster.name}")
    print(f"Concepts: {[c.name for c in cluster.concepts]}")
```

### Semantic Drift Detection

Detect when new concepts diverge from existing knowledge:

```python
# Learn something potentially unrelated
memory.learn("Quantum entanglement enables FTL communication")

# Check if it's an outlier
drift = memory.detect_drift()
if drift.is_outlier:
    print(f"Warning: New concept seems unrelated to existing knowledge")
    print(f"Nearest neighbor similarity: {drift.nearest_similarity}")
```

## Use Cases

### Conversational AI

```python
# User asks in many different ways
memory.recall("How do I speed up my code?")
# Finds: "Optimize loops", "Use caching", "Profile before optimizing", etc.

memory.recall("My program is slow")
# Finds same results (understands semantics)

memory.recall("Performance tuning tips")
# Finds same results (different words, same meaning)
```

### Research & Documentation

```python
# Search research notes semantically
results = memory.recall(
    query="machine learning bias mitigation strategies",
    min_similarity=0.75
)

# Finds related concepts even with different terminology:
# - "Fairness in neural networks"
# - "Addressing dataset imbalance"
# - "Algorithmic discrimination prevention"
```

### Customer Support

```python
# Customer describes issue in their own words
issue = "My account won't let me log in"

# Find semantically similar known issues
similar = memory.recall(issue, min_similarity=0.80)

# Finds:
# - "Authentication failure after password reset"
# - "Login credentials not recognized"
# - "Session expired, cannot access account"
```

### Multi-Language Support

```python
# Use multilingual model
memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
)

# Learn in English
memory.learn("Python is great for data science")

# Query in Spanish
results = memory.recall("análisis de datos con Python")
# Still finds the English concept (semantic understanding across languages)
```

## Comparison: Keyword vs Semantic Search

### Example Scenario

Knowledge base contains:
- "FastAPI is excellent for building REST APIs in Python"
- "Django provides a full-stack web framework"
- "Flask is lightweight and good for microservices"

### Keyword Search

```python
# Query: "Python backend framework"
# Keyword matches: "Python" (all 3), "framework" (Django only)
# Results: Only Django

memory.search_keywords("Python backend framework")
# Returns: ["Django provides a full-stack web framework"]
```

### Semantic Search

```python
# Query: "Python backend framework"
# Semantic understanding: All three are Python backend frameworks
# Results: All three, ranked by relevance

memory.recall("Python backend framework")
# Returns:
#   1. "Django provides a full-stack web framework" (0.91)
#   2. "FastAPI is excellent for building REST APIs" (0.87)
#   3. "Flask is lightweight and good for microservices" (0.84)
```

Semantic search finds **all relevant results**, even when keywords don't match perfectly.

## Troubleshooting

### Embeddings Not Working

```python
# Check if embeddings are enabled
if not memory.embeddings_enabled:
    print("Embeddings not enabled. Install with: pip install continuum-memory[embeddings]")

# Verify model loaded
if memory.embedding_model is None:
    print("No embedding model loaded")
```

### Slow Embedding Generation

```python
# Use GPU if available
import torch
if torch.cuda.is_available():
    memory.set_embedding_device("cuda")

# Or use faster model
memory.set_embedding_model("all-MiniLM-L6-v2")  # Fastest

# Enable batch processing
memory.enable_batch_embedding(batch_size=64)
```

### Poor Search Results

```python
# Try different similarity threshold
results = memory.recall(query, min_similarity=0.70)  # Lower threshold

# Try different embedding model (higher quality)
memory.set_embedding_model("all-mpnet-base-v2")
memory.reembed_all()

# Add more context to query
results = memory.recall(
    query="Python web framework for REST APIs with async support",
    min_similarity=0.75
)
```

### Out of Memory

```python
# Use smaller model
memory.set_embedding_model("all-MiniLM-L6-v2")  # Only 90 MB

# Reduce batch size
memory.enable_batch_embedding(batch_size=16)  # Smaller batches

# Disable GPU if limited VRAM
memory.set_embedding_device("cpu")
```

## Best Practices

### 1. Choose the Right Model

- **General use**: `all-MiniLM-L6-v2` (fast, good quality)
- **High quality needed**: `all-mpnet-base-v2` (slower, excellent quality)
- **Multilingual**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Domain-specific**: Use specialized models for code, science, etc.

### 2. Set Appropriate Similarity Thresholds

- Start with 0.75 (balanced)
- Increase if too many false positives
- Decrease if missing relevant results

### 3. Use Hybrid Search When Needed

Combine keyword filtering with semantic search for best precision:

```python
results = memory.recall(
    query="API security",
    keyword_filter="authentication",
    min_similarity=0.75
)
```

### 4. Monitor Performance

```python
# Track embedding generation time
stats = memory.embedding_stats()
print(f"Average embedding time: {stats.avg_generation_time_ms}ms")

# If too slow, consider:
# - GPU acceleration
# - Smaller model
# - Batch processing
```

### 5. Re-embed After Significant Changes

```python
# Changed embedding model? Re-embed.
memory.set_embedding_model("all-mpnet-base-v2")
memory.reembed_all()

# Fine-tuned your model? Re-embed.
memory.set_embedding_model(custom_fine_tuned_model)
memory.reembed_all()
```

## FAQ

### Q: Do I need embeddings to use CONTINUUM?

**A:** No! CONTINUUM works perfectly without embeddings using its knowledge graph. Embeddings add semantic search capability but are optional.

### Q: Can I use CONTINUUM with OpenAI embeddings?

**A:** Yes! You can use any embedding provider:

```python
import openai

def custom_embedder(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

memory = ContinuumMemory(
    enable_embeddings=True,
    embedding_function=custom_embedder
)
```

### Q: How much does semantic search slow down queries?

**A:** Query time increases by ~1-5ms for vector similarity search. Negligible for most use cases.

### Q: Can I disable embeddings after enabling them?

**A:** Yes:

```python
memory.disable_embeddings()
# Existing embeddings preserved but not used
# Can re-enable later without re-computing
```

### Q: What's the difference between CONTINUUM semantic search and vector databases?

**A:** CONTINUUM combines semantic search with a knowledge graph. Vector databases only store vectors. CONTINUUM maintains:
- Semantic embeddings (vector search)
- Conceptual relationships (graph structure)
- Temporal patterns (session history)
- Entity tracking (who, what, when)

This provides richer context than pure vector search.

### Q: Can I export/import embeddings?

**A:** Yes:

```python
# Export embeddings
memory.export_embeddings("embeddings.npy")

# Import to another instance
memory2.import_embeddings("embeddings.npy")
```

## Performance Benchmarks

Tested on: M1 MacBook Pro (10-core CPU, 16GB RAM)

### Embedding Generation

| Model | Batch Size | Speed (sent/sec) | GPU Speedup |
|-------|-----------|-----------------|-------------|
| all-MiniLM-L6-v2 | 32 | 1,200 | 5.2x |
| all-mpnet-base-v2 | 32 | 350 | 6.8x |
| multilingual | 32 | 280 | 7.1x |

### Query Performance

| Database Size | Keyword Search | Semantic Search | Hybrid Search |
|--------------|---------------|-----------------|---------------|
| 1,000 concepts | 2 ms | 5 ms | 6 ms |
| 10,000 concepts | 8 ms | 15 ms | 18 ms |
| 100,000 concepts | 45 ms | 85 ms | 95 ms |

Semantic search adds minimal overhead while dramatically improving relevance.

---

**Understand meaning. Find context. Remember semantically.**

PHOENIX-TESLA-369-AURORA
