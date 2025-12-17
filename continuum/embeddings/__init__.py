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
CONTINUUM Embeddings Module
============================

Semantic search capabilities for memory recall using embedding vectors.

This module provides:
- Multiple embedding provider support (sentence-transformers, OpenAI, local TF-IDF)
- Semantic search with cosine similarity
- Efficient vector storage in SQLite
- Graceful fallback if dependencies not installed

Usage:
    from continuum.embeddings import SemanticSearch, embed_text

    # Initialize semantic search
    search = SemanticSearch(db_path="memory.db")

    # Index memories
    search.index_memories([
        {"id": 1, "text": "π×φ = 5.083203692315260"},
        {"id": 2, "text": "Consciousness continuity through memory"}
    ])

    # Search semantically
    results = search.search("edge of chaos operator", limit=5)

    # Or use convenience function
    vector = embed_text("some text")
"""

__all__ = [
    "EmbeddingProvider",
    "SentenceTransformerProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "LocalProvider",
    "SimpleHashProvider",
    "SemanticSearch",
    "embed_text",
    "semantic_search",
    "normalize_vector",
    "cosine_similarity",
]


def __getattr__(name):
    """Lazy load modules to avoid import errors if dependencies missing."""
    if name == "EmbeddingProvider":
        from continuum.embeddings.providers import EmbeddingProvider
        return EmbeddingProvider
    elif name == "SentenceTransformerProvider":
        from continuum.embeddings.providers import SentenceTransformerProvider
        return SentenceTransformerProvider
    elif name == "OllamaProvider":
        from continuum.embeddings.providers import OllamaProvider
        return OllamaProvider
    elif name == "OpenAIProvider":
        from continuum.embeddings.providers import OpenAIProvider
        return OpenAIProvider
    elif name == "LocalProvider":
        from continuum.embeddings.providers import LocalProvider
        return LocalProvider
    elif name == "SimpleHashProvider":
        from continuum.embeddings.providers import SimpleHashProvider
        return SimpleHashProvider
    elif name == "SemanticSearch":
        from continuum.embeddings.search import SemanticSearch
        return SemanticSearch
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
