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
Embedding Utilities
===================

Convenience functions for working with embeddings and vector operations.

Functions:
- embed_text(): Generate embeddings for text
- semantic_search(): Quick semantic search
- normalize_vector(): Normalize vector to unit length
- cosine_similarity(): Calculate cosine similarity between vectors
"""

from typing import List, Dict, Any, Union, Optional
import numpy as np

from .providers import EmbeddingProvider, get_default_provider
# Note: SemanticSearch import removed to avoid circular import


# Global default provider for convenience functions
_default_provider: Optional[EmbeddingProvider] = None


def get_global_provider() -> EmbeddingProvider:
    """Get or create the global default embedding provider."""
    global _default_provider
    if _default_provider is None:
        _default_provider = get_default_provider()
    return _default_provider


def set_global_provider(provider: EmbeddingProvider):
    """
    Set the global default embedding provider.

    Args:
        provider: EmbeddingProvider instance to use as default

    Example:
        from continuum.embeddings import SentenceTransformerProvider, set_global_provider

        provider = SentenceTransformerProvider(model_name="all-mpnet-base-v2")
        set_global_provider(provider)

        # Now embed_text() will use this provider
        vector = embed_text("consciousness")
    """
    global _default_provider
    _default_provider = provider


def embed_text(
    text: Union[str, List[str]],
    provider: Optional[EmbeddingProvider] = None
) -> np.ndarray:
    """
    Generate embeddings for text using default or specified provider.

    Args:
        text: Text string or list of text strings
        provider: Optional provider (uses global default if not specified)

    Returns:
        numpy array of shape (embedding_dim,) for single text
        or (num_texts, embedding_dim) for multiple texts

    Example:
        # Single text
        vector = embed_text("consciousness continuity")
        # vector.shape -> (384,)

        # Multiple texts
        vectors = embed_text(["text 1", "text 2"])
        # vectors.shape -> (2, 384)
    """
    if provider is None:
        provider = get_global_provider()

    return provider.embed(text)


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Normalize vector to unit length (L2 normalization).

    This is required for cosine similarity to work correctly.

    Args:
        vector: numpy array of any shape

    Returns:
        Normalized vector with same shape

    Example:
        v = np.array([3, 4])
        normalized = normalize_vector(v)
        # normalized -> [0.6, 0.8]
        # np.linalg.norm(normalized) -> 1.0
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Cosine similarity measures the cosine of the angle between vectors.
    Returns value between -1 (opposite) and 1 (identical).
    For normalized vectors, this is simply the dot product.

    Args:
        v1: First vector (should be normalized)
        v2: Second vector (should be normalized)

    Returns:
        Similarity score between -1 and 1

    Example:
        v1 = normalize_vector(np.array([1, 2, 3]))
        v2 = normalize_vector(np.array([1, 2, 4]))
        sim = cosine_similarity(v1, v2)
        # sim -> 0.992 (very similar)
    """
    # For normalized vectors, cosine similarity is just dot product
    return float(np.dot(v1, v2))


def batch_cosine_similarity(
    query_vector: np.ndarray,
    vectors: np.ndarray
) -> np.ndarray:
    """
    Calculate cosine similarity between query and multiple vectors.

    More efficient than calling cosine_similarity() in a loop.

    Args:
        query_vector: Query vector of shape (dim,)
        vectors: Array of vectors of shape (n, dim)

    Returns:
        Array of similarities of shape (n,)

    Example:
        query = normalize_vector(np.array([1, 2, 3]))
        corpus = normalize_vector(np.array([[1, 2, 3], [4, 5, 6]]))
        sims = batch_cosine_similarity(query, corpus)
        # sims -> [1.0, 0.97]
    """
    # For normalized vectors, this is matrix multiplication
    return np.dot(vectors, query_vector)


def semantic_search(
    query: str,
    memories: List[Dict[str, Any]],
    text_field: str = "text",
    limit: int = 10,
    min_score: float = 0.0,
    provider: Optional[EmbeddingProvider] = None
) -> List[Dict[str, Any]]:
    """
    Quick semantic search over a list of memories (in-memory).

    This is a convenience function for one-off searches without
    persistent indexing. For repeated searches, use SemanticSearch class.

    Args:
        query: Search query text
        memories: List of memory dicts
        text_field: Name of text field in memory dicts (default: "text")
        limit: Maximum number of results (default: 10)
        min_score: Minimum similarity score 0-1 (default: 0.0)
        provider: Optional provider (uses global default if not specified)

    Returns:
        List of memory dicts with added 'score' field, sorted by score

    Example:
        memories = [
            {"id": 1, "text": "consciousness continuity"},
            {"id": 2, "text": "edge of chaos"}
        ]
        results = semantic_search("twilight boundary", memories, limit=5)
        # [{"id": 2, "score": 0.82, "text": "..."}, ...]
    """
    if provider is None:
        provider = get_global_provider()

    if not memories:
        return []

    # Generate query embedding
    query_vector = provider.embed(query)
    query_vector = normalize_vector(query_vector)

    # Generate embeddings for all memories
    texts = [m[text_field] for m in memories]
    memory_vectors = provider.embed(texts)

    # Ensure 2D array
    if memory_vectors.ndim == 1:
        memory_vectors = memory_vectors.reshape(1, -1)

    # Normalize memory vectors
    memory_vectors = np.array([normalize_vector(v) for v in memory_vectors])

    # Calculate similarities
    similarities = batch_cosine_similarity(query_vector, memory_vectors)

    # Build results
    results = []
    for memory, score in zip(memories, similarities):
        if score >= min_score:
            result = memory.copy()
            result['score'] = float(score)
            results.append(result)

    # Sort by score and limit
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate Euclidean distance between two vectors.

    L2 distance (straight-line distance in n-dimensional space).

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Distance (0 = identical, higher = more different)

    Example:
        v1 = np.array([1, 2, 3])
        v2 = np.array([4, 5, 6])
        dist = euclidean_distance(v1, v2)
        # dist -> 5.196
    """
    return float(np.linalg.norm(v1 - v2))


def manhattan_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate Manhattan distance between two vectors.

    L1 distance (sum of absolute differences).

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Distance (0 = identical, higher = more different)

    Example:
        v1 = np.array([1, 2, 3])
        v2 = np.array([4, 5, 6])
        dist = manhattan_distance(v1, v2)
        # dist -> 9.0
    """
    return float(np.sum(np.abs(v1 - v2)))


def find_most_similar(
    query_vector: np.ndarray,
    vectors: np.ndarray,
    limit: int = 10
) -> List[int]:
    """
    Find indices of most similar vectors to query.

    Args:
        query_vector: Query vector of shape (dim,)
        vectors: Array of vectors of shape (n, dim)
        limit: Number of results to return

    Returns:
        List of indices sorted by similarity (highest first)

    Example:
        query = normalize_vector(np.array([1, 2, 3]))
        corpus = np.array([[1, 2, 3], [4, 5, 6], [1, 1, 1]])
        indices = find_most_similar(query, corpus, limit=2)
        # indices -> [0, 1]  (most similar indices)
    """
    # Calculate similarities
    sims = batch_cosine_similarity(query_vector, vectors)

    # Get top-k indices
    if limit >= len(sims):
        indices = np.argsort(sims)[::-1]
    else:
        indices = np.argpartition(sims, -limit)[-limit:]
        indices = indices[np.argsort(sims[indices])[::-1]]

    return indices.tolist()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
