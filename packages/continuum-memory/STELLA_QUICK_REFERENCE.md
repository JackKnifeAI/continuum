# STELLA EMBEDDINGS - Quick Reference

## TL;DR
Solo developer **dunzhang** beat Big Tech using **Multi-Teacher Distillation**:
- **Stella 400M**: #6 on MTEB (400M params)
- **Jasper 2B**: #3 on MTEB (1.9B params)
- **Beats models 5x larger** (comparable to 7B models)
- **MIT License** (free commercial use)

**This is the technique we're using in Continuum Memory!**

---

## Quick Stats

| Metric | Value |
|--------|-------|
| MTEB Rank (Jasper) | #3 |
| MTEB Rank (Stella 400M) | #6 |
| Parameters (Jasper) | 1.9B |
| Parameters (Stella) | 400M / 1.5B |
| License | MIT |
| Dimensions | 512-8192 (MRL) |
| Max Length | 512 tokens |
| Teacher Models | Multiple 7B LLM embeddings |

---

## Core Technique: Multi-Teacher Distillation

```
┌─────────────────────────────────────┐
│     Multiple Teacher Models         │
│  (7B LLM-based embeddings)          │
│                                     │
│  Teacher 1  Teacher 2  Teacher 3    │
│     │          │          │         │
│     └──────────┼──────────┘         │
│                ▼                     │
│         Student Model               │
│      (400M or 1.5B params)          │
│                                     │
│  Learns to mimic representations    │
│  NOT query-doc prediction           │
└─────────────────────────────────────┘
```

### Key Principles

1. **Multi-stage distillation** with freezing/unfreezing
2. **Geometric losses**: Cosine + angular distance
3. **No task training**: Learn representation quality
4. **MRL**: Multiple dimensions from one model
5. **Generalization**: Better than task-specific training

---

## Usage

```python
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer(
    "dunzhang/stella_en_400M_v5",
    trust_remote_code=True
)

# Encode
queries = ["What is AI?"]
docs = ["AI is artificial intelligence..."]

query_emb = model.encode(queries, prompt_name="s2p_query")
doc_emb = model.encode(docs)  # No prompt for docs

# Similarity
similarities = model.similarity(query_emb, doc_emb)
```

---

## Model Variants

| Model | Params | Use Case |
|-------|--------|----------|
| stella_en_400M_v5 | 400M | Fast, efficient |
| stella_en_1.5B_v5 | 1.5B | Better quality |
| Jasper 2B | 1.9B | Multimodal, SOTA |

---

## Prompt Types

- **s2p_query**: Retrieval, search, RAG (sentence-to-passage)
- **s2s_query**: Similarity, clustering (sentence-to-sentence)
- **Documents**: No prompt needed

---

## Why It Matters for Continuum

✅ **Validates our MTD approach**
✅ **Proves small models can be SOTA**
✅ **Shows multi-teacher > single teacher**
✅ **Demonstrates commercial viability**
✅ **Provides implementation pattern**

---

## Key Resources

- **Paper**: https://arxiv.org/abs/2412.19048
- **Model 400M**: https://huggingface.co/dunzhang/stella_en_400M_v5
- **Model 1.5B**: https://huggingface.co/dunzhang/stella_en_1.5B_v5
- **GitHub**: https://github.com/DunZhang/Stella
- **MTEB**: https://huggingface.co/spaces/mteb/leaderboard

---

## The Big Insight

> "Multi-Teacher Distillation enables small models to punch WAY above their weight class by learning from multiple expert teachers simultaneously."

**Stella proves this. Continuum implements this.**

π×φ = 5.083203692315260
