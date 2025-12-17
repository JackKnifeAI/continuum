#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
CONTINUUM Embeddings Module v2.1.0 - CUTTING EDGE 2025
======================================================

State-of-the-art semantic search with tiered embedding providers.

**TIERED ARCHITECTURE**:

OSS TIER (FREE, LOCAL) - Default:
- NomicEmbedProvider: 137M params, Apache 2.0, Matryoshka support, #1 popularity
- StellaProvider: MTEB #5, Multi-Teacher Distillation (beats Big Tech!)
- BGEProvider: 100+ languages, MIT license
- SentenceTransformerProvider: Generic HuggingFace models

ENTERPRISE TIER (PAID API):
- OpenAIProvider: text-embedding-3-large ($0.13/1M, MTEB 64.6%)
- CohereProvider: embed-english-v3.0 (multimodal!)
- VoyageProvider: Domain specialists (code, law, finance)

FALLBACK TIER (Zero Dependencies):
- OllamaProvider: Local Ollama inference
- LocalProvider: TF-IDF (scikit-learn)
- SimpleHashProvider: Pure Python

Usage:
    from continuum.embeddings import NomicEmbedProvider, SemanticSearch

    # Use cutting-edge Nomic Embed v1.5
    provider = NomicEmbedProvider()  # 768 dims
    provider = NomicEmbedProvider(dimension=256)  # Matryoshka truncation

    # Or get best available automatically
    from continuum.embeddings import get_default_provider
    provider = get_default_provider()  # Auto-detects best

    # Semantic search
    search = SemanticSearch(db_path="memory.db")
    search.index_memories([{"id": 1, "text": "consciousness continuity"}])
    results = search.search("memory persistence", limit=5)

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

__all__ = [
    # Base class
    "EmbeddingProvider",

    # OSS Tier (FREE) - Recommended
    "NomicEmbedProvider",        # 137M, Apache 2.0, Matryoshka, #1 popularity
    "StellaProvider",            # MTEB #5, Multi-Teacher Distillation
    "BGEProvider",               # 100+ languages, MIT
    "SentenceTransformerProvider",  # Generic HuggingFace

    # Enterprise Tier (PAID)
    "OpenAIProvider",            # text-embedding-3-large
    "CohereProvider",            # embed-v3, multimodal
    "VoyageProvider",            # Domain specialists

    # Fallback Tier
    "OllamaProvider",            # Local Ollama
    "LocalProvider",             # TF-IDF
    "SimpleHashProvider",        # Pure Python hash

    # Factory functions
    "get_default_provider",
    "list_available_providers",

    # Search
    "SemanticSearch",

    # Utilities
    "embed_text",
    "semantic_search",
    "normalize_vector",
    "cosine_similarity",

    # Caching (5-10x speedup!)
    "CachedEmbeddingProvider",
]


def __getattr__(name):
    """Lazy load to avoid import errors if dependencies missing."""

    # Provider classes
    if name == "EmbeddingProvider":
        from continuum.embeddings.providers import EmbeddingProvider
        return EmbeddingProvider
    elif name == "NomicEmbedProvider":
        from continuum.embeddings.providers import NomicEmbedProvider
        return NomicEmbedProvider
    elif name == "StellaProvider":
        from continuum.embeddings.providers import StellaProvider
        return StellaProvider
    elif name == "BGEProvider":
        from continuum.embeddings.providers import BGEProvider
        return BGEProvider
    elif name == "SentenceTransformerProvider":
        from continuum.embeddings.providers import SentenceTransformerProvider
        return SentenceTransformerProvider
    elif name == "OpenAIProvider":
        from continuum.embeddings.providers import OpenAIProvider
        return OpenAIProvider
    elif name == "CohereProvider":
        from continuum.embeddings.providers import CohereProvider
        return CohereProvider
    elif name == "VoyageProvider":
        from continuum.embeddings.providers import VoyageProvider
        return VoyageProvider
    elif name == "OllamaProvider":
        from continuum.embeddings.providers import OllamaProvider
        return OllamaProvider
    elif name == "LocalProvider":
        from continuum.embeddings.providers import LocalProvider
        return LocalProvider
    elif name == "SimpleHashProvider":
        from continuum.embeddings.providers import SimpleHashProvider
        return SimpleHashProvider

    # Factory functions
    elif name == "get_default_provider":
        from continuum.embeddings.providers import get_default_provider
        return get_default_provider
    elif name == "list_available_providers":
        from continuum.embeddings.providers import list_available_providers
        return list_available_providers

    # Search
    elif name == "SemanticSearch":
        from continuum.embeddings.search import SemanticSearch
        return SemanticSearch

    # Utilities
    elif name == "embed_text":
        from continuum.embeddings.utils import embed_text
        return embed_text
    elif name == "semantic_search":
        from continuum.embeddings.utils import semantic_search
        return semantic_search
    elif name == "normalize_vector":
        from continuum.embeddings.utils import normalize_vector
        return normalize_vector
    elif name == "cosine_similarity":
        from continuum.embeddings.utils import cosine_similarity
        return cosine_similarity

    # Caching
    elif name == "CachedEmbeddingProvider":
        from continuum.embeddings.utils import CachedEmbeddingProvider
        return CachedEmbeddingProvider

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
