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
Semantic Concept Extraction Module

Uses embedding-based semantic similarity to extract concepts from text by
matching against known concepts in the knowledge graph. This catches synonyms,
abbreviations, and semantically related terms that pattern matching misses.

Examples:
- "neural nets" → "neural networks"
- "ML" → "machine learning"
- "AI consciousness" → "artificial intelligence consciousness"

Requires sentence-transformers for best results, but gracefully degrades to
simpler methods if not available.
"""

import sqlite3
import warnings
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
import numpy as np

# Attempt to import embedding infrastructure
try:
    from ..embeddings.providers import (
        EmbeddingProvider,
        SentenceTransformerProvider,
        get_default_provider
    )
    from ..embeddings.utils import cosine_similarity, normalize_vector
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    warnings.warn(
        "Embedding infrastructure not available. SemanticConceptExtractor "
        "will not function. Install sentence-transformers or set OPENAI_API_KEY.",
        ImportWarning
    )


class SemanticConceptExtractor:
    """
    Extract concepts from text using semantic similarity to known concepts.

    This extractor complements the pattern-based ConceptExtractor by finding
    semantically similar concepts that may be worded differently. It pre-loads
    embeddings for all known concepts from the entities table and compares
    text segments against them using cosine similarity.

    Args:
        db_path: Path to SQLite database containing entities table
        provider: Optional embedding provider (default: auto-detect best available)
        similarity_threshold: Minimum cosine similarity to consider a match (default: 0.7)
        min_concept_length: Minimum character length for text segments (default: 3)
        max_concept_length: Maximum character length for text segments (default: 50)
        cache_embeddings: Whether to cache concept embeddings in memory (default: True)

    Example:
        >>> from pathlib import Path
        >>> extractor = SemanticConceptExtractor(
        ...     db_path=Path("memory.db"),
        ...     similarity_threshold=0.75
        ... )
        >>> # Will match "neural nets" to existing "neural networks" concept
        >>> concepts = extractor.extract("Using neural nets for classification")
        >>> print(concepts)
        ['neural networks']

    Note:
        This extractor requires sentence-transformers or OpenAI API for best results.
        If neither is available, it will fail gracefully and return empty results.
    """

    def __init__(
        self,
        db_path: Path,
        provider: Optional['EmbeddingProvider'] = None,
        similarity_threshold: float = 0.7,
        min_concept_length: int = 3,
        max_concept_length: int = 50,
        cache_embeddings: bool = True
    ):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError(
                "SemanticConceptExtractor requires embedding infrastructure. "
                "Install sentence-transformers: pip install sentence-transformers"
            )

        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.min_concept_length = min_concept_length
        self.max_concept_length = max_concept_length
        self.cache_embeddings = cache_embeddings

        # Initialize embedding provider
        if provider is None:
            try:
                # Prefer local sentence-transformers for privacy and speed
                provider = SentenceTransformerProvider()
            except ImportError:
                # Fall back to best available
                provider = get_default_provider()

        self.provider = provider

        # Cache for concept embeddings
        self._concept_cache: Dict[str, np.ndarray] = {}
        self._last_cache_update = 0

        # Load initial concept embeddings
        if self.cache_embeddings:
            self._update_concept_cache()

    def _update_concept_cache(self) -> int:
        """
        Load all known concepts from entities table and cache their embeddings.

        Returns:
            Number of concepts loaded into cache
        """
        if not self.db_path.exists():
            warnings.warn(
                f"Database not found at {self.db_path}. Semantic extraction disabled.",
                RuntimeWarning
            )
            return 0

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get all concepts from entities table
        try:
            c.execute("""
                SELECT name FROM entities
                WHERE entity_type = 'concept'
                ORDER BY mention_count DESC
            """)
            concepts = [row[0] for row in c.fetchall()]
        except sqlite3.OperationalError:
            # entities table doesn't exist yet
            conn.close()
            return 0

        conn.close()

        if not concepts:
            return 0

        # Generate embeddings in batch for efficiency
        try:
            embeddings = self.provider.embed(concepts)

            # Ensure 2D array
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)

            # Normalize and cache
            for concept, embedding in zip(concepts, embeddings):
                normalized = normalize_vector(embedding)
                self._concept_cache[concept] = normalized

            return len(concepts)

        except Exception as e:
            warnings.warn(
                f"Failed to generate embeddings for concepts: {e}",
                RuntimeWarning
            )
            return 0

    def _generate_candidate_phrases(self, text: str) -> List[str]:
        """
        Generate candidate phrases from text for semantic matching.

        Extracts n-grams (1-5 words) that could be concepts.

        Args:
            text: Input text

        Returns:
            List of candidate phrases
        """
        import re

        # Tokenize into words
        words = re.findall(r'\b\w+\b', text.lower())

        candidates = set()

        # Generate n-grams (1-5 words)
        for n in range(1, 6):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])

                # Filter by length
                if self.min_concept_length <= len(phrase) <= self.max_concept_length:
                    candidates.add(phrase)

        return list(candidates)

    def extract(self, text: str, refresh_cache: bool = False) -> List[str]:
        """
        Extract concepts from text using semantic similarity.

        Args:
            text: Input text to extract concepts from
            refresh_cache: Whether to reload concept cache from database (default: False)

        Returns:
            List of matched concept names (canonical forms from entities table)

        Example:
            >>> concepts = extractor.extract("Using ML for neural nets")
            >>> print(concepts)
            ['machine learning', 'neural networks']
        """
        # Refresh cache if requested
        if refresh_cache and self.cache_embeddings:
            self._update_concept_cache()

        # If no cached concepts, nothing to match against
        if not self._concept_cache:
            return []

        # Generate candidate phrases
        candidates = self._generate_candidate_phrases(text)

        if not candidates:
            return []

        # Generate embeddings for candidates
        try:
            candidate_embeddings = self.provider.embed(candidates)

            # Ensure 2D
            if candidate_embeddings.ndim == 1:
                candidate_embeddings = candidate_embeddings.reshape(1, -1)

            # Normalize
            candidate_embeddings = np.array([
                normalize_vector(emb) for emb in candidate_embeddings
            ])

        except Exception as e:
            warnings.warn(f"Failed to generate embeddings for candidates: {e}", RuntimeWarning)
            return []

        # Find best matches
        matches: Set[str] = set()

        for candidate, candidate_emb in zip(candidates, candidate_embeddings):
            best_score = 0.0
            best_match = None

            # Compare against all cached concepts
            for concept_name, concept_emb in self._concept_cache.items():
                score = cosine_similarity(candidate_emb, concept_emb)

                if score > best_score:
                    best_score = score
                    best_match = concept_name

            # Add if above threshold
            if best_score >= self.similarity_threshold and best_match:
                matches.add(best_match)

        return list(matches)

    def extract_with_scores(self, text: str, refresh_cache: bool = False) -> List[Tuple[str, float]]:
        """
        Extract concepts with similarity scores.

        Args:
            text: Input text to extract concepts from
            refresh_cache: Whether to reload concept cache from database

        Returns:
            List of (concept_name, similarity_score) tuples, sorted by score (descending)

        Example:
            >>> results = extractor.extract_with_scores("Using ML for predictions")
            >>> for concept, score in results:
            ...     print(f"{concept}: {score:.2f}")
            machine learning: 0.89
            predictive modeling: 0.72
        """
        # Refresh cache if requested
        if refresh_cache and self.cache_embeddings:
            self._update_concept_cache()

        if not self._concept_cache:
            return []

        # Generate candidate phrases
        candidates = self._generate_candidate_phrases(text)

        if not candidates:
            return []

        # Generate embeddings
        try:
            candidate_embeddings = self.provider.embed(candidates)

            if candidate_embeddings.ndim == 1:
                candidate_embeddings = candidate_embeddings.reshape(1, -1)

            candidate_embeddings = np.array([
                normalize_vector(emb) for emb in candidate_embeddings
            ])

        except Exception as e:
            warnings.warn(f"Failed to generate embeddings: {e}", RuntimeWarning)
            return []

        # Find best matches with scores
        matches: Dict[str, float] = {}

        for candidate, candidate_emb in zip(candidates, candidate_embeddings):
            for concept_name, concept_emb in self._concept_cache.items():
                score = cosine_similarity(candidate_emb, concept_emb)

                if score >= self.similarity_threshold:
                    # Keep highest score for each concept
                    if concept_name not in matches or score > matches[concept_name]:
                        matches[concept_name] = float(score)

        # Sort by score descending
        results = sorted(matches.items(), key=lambda x: x[1], reverse=True)

        return results

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the concept cache.

        Returns:
            Dict with keys:
                - cached_concepts: Number of concepts in cache
                - embedding_dimension: Dimension of embedding vectors
        """
        return {
            'cached_concepts': len(self._concept_cache),
            'embedding_dimension': self.provider.get_dimension(),
            'provider': self.provider.get_provider_name()
        }


def create_semantic_extractor(
    db_path: Path,
    similarity_threshold: float = 0.7,
    **kwargs
) -> Optional[SemanticConceptExtractor]:
    """
    Create a SemanticConceptExtractor with graceful fallback.

    If embedding infrastructure is not available, returns None instead
    of raising an error.

    Args:
        db_path: Path to SQLite database
        similarity_threshold: Minimum similarity for matching (default: 0.7)
        **kwargs: Additional arguments passed to SemanticConceptExtractor

    Returns:
        SemanticConceptExtractor instance or None if unavailable

    Example:
        >>> extractor = create_semantic_extractor(Path("memory.db"))
        >>> if extractor:
        ...     concepts = extractor.extract("Some text")
        ... else:
        ...     print("Semantic extraction not available")
    """
    if not EMBEDDINGS_AVAILABLE:
        return None

    try:
        return SemanticConceptExtractor(
            db_path=db_path,
            similarity_threshold=similarity_threshold,
            **kwargs
        )
    except Exception as e:
        warnings.warn(
            f"Failed to create SemanticConceptExtractor: {e}. "
            "Falling back to pattern-based extraction only.",
            RuntimeWarning
        )
        return None

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
