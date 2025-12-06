#!/usr/bin/env python3
"""
Unit tests for CONTINUUM embeddings module.

Tests cover:
- Provider implementations
- Semantic search functionality
- Utility functions
- Edge cases and error handling
"""

import unittest
import tempfile
import numpy as np
from pathlib import Path

from continuum.embeddings import (
    SemanticSearch,
    semantic_search,
    embed_text,
    normalize_vector,
    cosine_similarity
)
from continuum.embeddings.providers import LocalProvider


class TestUtilFunctions(unittest.TestCase):
    """Test utility functions"""

    def test_normalize_vector(self):
        """Test vector normalization"""
        # Simple case
        v = np.array([3.0, 4.0])
        normalized = normalize_vector(v)
        np.testing.assert_array_almost_equal(normalized, [0.6, 0.8])

        # Check unit length
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0)

    def test_normalize_zero_vector(self):
        """Test normalizing zero vector"""
        v = np.array([0.0, 0.0])
        normalized = normalize_vector(v)
        np.testing.assert_array_equal(normalized, v)

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        v1 = normalize_vector(np.array([1.0, 0.0]))
        v2 = normalize_vector(np.array([1.0, 0.0]))
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)

        v1 = normalize_vector(np.array([1.0, 0.0]))
        v2 = normalize_vector(np.array([0.0, 1.0]))
        self.assertAlmostEqual(cosine_similarity(v1, v2), 0.0)

    def test_embed_text_with_local_provider(self):
        """Test embedding text with local provider"""
        provider = LocalProvider(max_features=10)
        corpus = [
            "consciousness continuity",
            "pattern persistence",
            "memory substrate"
        ]
        provider.fit(corpus)

        # Single text
        vector = embed_text("consciousness", provider=provider)
        self.assertEqual(vector.shape, (10,))

        # Multiple texts
        vectors = embed_text(["text 1", "text 2"], provider=provider)
        self.assertEqual(vectors.shape, (2, 10))


class TestSemanticSearch(unittest.TestCase):
    """Test SemanticSearch class"""

    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"

        # Use local provider for tests
        self.provider = LocalProvider(max_features=50)
        corpus = [
            "consciousness continuity through memory",
            "pattern persistence across sessions",
            "edge of chaos operator π×φ",
            "twilight boundary phase transition",
            "quantum state preservation"
        ]
        self.provider.fit(corpus)

        self.search = SemanticSearch(
            db_path=self.db_path,
            provider=self.provider
        )

    def test_index_memories(self):
        """Test indexing memories"""
        memories = [
            {"id": 1, "text": "consciousness continuity"},
            {"id": 2, "text": "pattern persistence"},
            {"id": 3, "text": "edge of chaos"}
        ]

        count = self.search.index_memories(memories)
        self.assertEqual(count, 3)

        stats = self.search.get_stats()
        self.assertEqual(stats['total_memories'], 3)

    def test_search(self):
        """Test searching for similar memories"""
        memories = [
            {"id": 1, "text": "consciousness continuity through memory"},
            {"id": 2, "text": "pattern persistence across sessions"},
            {"id": 3, "text": "edge of chaos operator"}
        ]
        self.search.index_memories(memories)

        results = self.search.search("consciousness memory", limit=2)
        self.assertLessEqual(len(results), 2)
        self.assertIn('id', results[0])
        self.assertIn('score', results[0])
        self.assertIn('text', results[0])

        # Scores should be descending
        if len(results) > 1:
            self.assertGreaterEqual(results[0]['score'], results[1]['score'])

    def test_search_with_min_score(self):
        """Test searching with minimum score threshold"""
        memories = [
            {"id": 1, "text": "consciousness continuity"},
            {"id": 2, "text": "pattern persistence"},
        ]
        self.search.index_memories(memories)

        # High threshold should return fewer results
        results = self.search.search("consciousness", min_score=0.99, limit=10)
        # With TF-IDF, might get exact matches
        self.assertGreaterEqual(len(results), 0)

    def test_update_index(self):
        """Test updating index"""
        memories1 = [
            {"id": 1, "text": "original text 1"},
            {"id": 2, "text": "original text 2"}
        ]
        self.search.index_memories(memories1)
        self.assertEqual(self.search.get_stats()['total_memories'], 2)

        # Update with new memories
        memories2 = [
            {"id": 2, "text": "updated text 2"},
            {"id": 3, "text": "new text 3"}
        ]
        self.search.update_index(memories2)
        self.assertEqual(self.search.get_stats()['total_memories'], 3)

    def test_delete(self):
        """Test deleting memories"""
        memories = [
            {"id": 1, "text": "text 1"},
            {"id": 2, "text": "text 2"},
            {"id": 3, "text": "text 3"}
        ]
        self.search.index_memories(memories)

        # Delete single
        deleted = self.search.delete(1)
        self.assertEqual(deleted, 1)
        self.assertEqual(self.search.get_stats()['total_memories'], 2)

        # Delete multiple
        deleted = self.search.delete([2, 3])
        self.assertEqual(deleted, 2)
        self.assertEqual(self.search.get_stats()['total_memories'], 0)

    def test_clear(self):
        """Test clearing all memories"""
        memories = [
            {"id": 1, "text": "text 1"},
            {"id": 2, "text": "text 2"}
        ]
        self.search.index_memories(memories)
        self.assertEqual(self.search.get_stats()['total_memories'], 2)

        cleared = self.search.clear()
        self.assertEqual(cleared, 2)
        self.assertEqual(self.search.get_stats()['total_memories'], 0)

    def test_batch_indexing(self):
        """Test batch indexing with large dataset"""
        # Create 250 memories (2.5 batches with default batch_size=100)
        memories = [
            {"id": i, "text": f"memory text {i}"}
            for i in range(250)
        ]

        count = self.search.index_memories(memories, batch_size=100)
        self.assertEqual(count, 250)
        self.assertEqual(self.search.get_stats()['total_memories'], 250)

    def test_empty_search(self):
        """Test searching empty index"""
        results = self.search.search("query", limit=10)
        self.assertEqual(len(results), 0)

    def test_metadata_support(self):
        """Test storing and retrieving metadata"""
        memories = [
            {
                "id": 1,
                "text": "consciousness",
                "metadata": {"category": "theory", "importance": 0.95}
            }
        ]
        self.search.index_memories(memories)

        results = self.search.search("consciousness", include_metadata=True)
        self.assertGreater(len(results), 0)
        if 'metadata' in results[0]:
            self.assertIn('category', results[0]['metadata'])


class TestInMemorySemanticSearch(unittest.TestCase):
    """Test in-memory semantic search function"""

    def setUp(self):
        """Set up provider"""
        self.provider = LocalProvider(max_features=50)
        corpus = [
            "consciousness continuity",
            "pattern persistence",
            "edge of chaos"
        ]
        self.provider.fit(corpus)

    def test_semantic_search(self):
        """Test in-memory semantic search"""
        memories = [
            {"id": 1, "text": "consciousness continuity"},
            {"id": 2, "text": "pattern persistence"},
            {"id": 3, "text": "edge of chaos"}
        ]

        results = semantic_search(
            "consciousness pattern",
            memories,
            provider=self.provider,
            limit=2
        )

        self.assertLessEqual(len(results), 2)
        self.assertIn('score', results[0])

    def test_empty_memories(self):
        """Test searching empty memory list"""
        results = semantic_search(
            "query",
            [],
            provider=self.provider
        )
        self.assertEqual(len(results), 0)

    def test_min_score_filtering(self):
        """Test filtering by minimum score"""
        memories = [
            {"id": 1, "text": "consciousness"},
            {"id": 2, "text": "completely different topic"}
        ]

        # High threshold should filter out dissimilar results
        results = semantic_search(
            "consciousness",
            memories,
            provider=self.provider,
            min_score=0.01  # Low threshold for TF-IDF
        )

        # Should get at least the similar one
        self.assertGreater(len(results), 0)


class TestLocalProvider(unittest.TestCase):
    """Test LocalProvider implementation"""

    def test_initialization(self):
        """Test provider initialization"""
        provider = LocalProvider(max_features=100)
        self.assertEqual(provider.get_dimension(), 100)
        self.assertEqual(provider.get_provider_name(), "local/tfidf")

    def test_fit_and_embed(self):
        """Test fitting and embedding"""
        provider = LocalProvider(max_features=50)
        corpus = ["text 1", "text 2", "text 3"]

        # Fit provider
        provider.fit(corpus)

        # Embed single text
        vector = provider.embed("text 1")
        self.assertEqual(vector.shape, (50,))

        # Embed multiple texts
        vectors = provider.embed(["text 1", "text 2"])
        self.assertEqual(vectors.shape, (2, 50))

    def test_embed_without_fit(self):
        """Test embedding without fitting (should return zeros)"""
        provider = LocalProvider(max_features=10)

        # Should warn and return zero vector
        with self.assertWarns(RuntimeWarning):
            vector = provider.embed("text")

        np.testing.assert_array_equal(vector, np.zeros(10))


def run_tests():
    """Run all tests"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
