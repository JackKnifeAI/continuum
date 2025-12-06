#!/usr/bin/env python3
"""
Test suite for extraction module.

Verifies that concept extraction, decision detection, and attention
graph construction work correctly in the cleaned continuum module.
"""

import tempfile
from pathlib import Path

from continuum.extraction import (
    ConceptExtractor,
    DecisionExtractor,
    AttentionGraphExtractor,
    CanonicalMapper,
    AutoMemoryHook
)


def test_concept_extraction():
    """Test basic concept extraction."""
    extractor = ConceptExtractor()

    # Test with capitalized phrases and technical terms
    text = "Building a WorkingMemory system with neural_networks and machine-learning"
    concepts = extractor.extract(text)

    print("Test: Concept Extraction")
    print(f"  Input: {text}")
    print(f"  Extracted: {concepts}")
    assert 'WorkingMemory' in concepts
    assert 'neural_networks' in concepts
    assert 'machine-learning' in concepts
    print("  ✓ Passed\n")


def test_concept_extraction_with_counts():
    """Test concept extraction with occurrence counts."""
    extractor = ConceptExtractor()

    text = "Python and JavaScript are popular. Python is great for ML."
    counts = extractor.extract_with_counts(text)

    print("Test: Concept Extraction with Counts")
    print(f"  Input: {text}")
    print(f"  Counts: {counts}")
    assert counts.get('Python', 0) == 2
    assert counts.get('JavaScript', 0) == 1
    print("  ✓ Passed\n")


def test_decision_extraction():
    """Test decision detection."""
    extractor = DecisionExtractor()

    # Test with assistant role
    text = "I am going to create the API module. My decision is to use FastAPI."
    decisions = extractor.extract(text, role="assistant")

    print("Test: Decision Extraction")
    print(f"  Input: {text}")
    print(f"  Decisions: {decisions}")
    assert len(decisions) >= 1
    assert any('API' in d for d in decisions)
    print("  ✓ Passed\n")

    # Test with user role (should return empty)
    decisions = extractor.extract(text, role="user")
    assert len(decisions) == 0
    print("  ✓ User role filtering works\n")


def test_canonical_mapper():
    """Test concept canonicalization."""
    mapper = CanonicalMapper({
        'machine learning': ['machine_learning', 'machinelearning', 'ML']
    })

    print("Test: Canonical Mapper")
    assert mapper.canonicalize('machine_learning') == 'machine learning'
    assert mapper.canonicalize('ML') == 'machine learning'
    assert mapper.canonicalize('deep_learning') == 'deep_learning'  # No mapping
    print("  ✓ Passed\n")


def test_attention_graph_extraction():
    """Test attention graph extraction."""
    extractor = AttentionGraphExtractor()

    text = "Building neural networks with TensorFlow and PyTorch for machine learning."
    results = extractor.extract_from_message(text)

    print("Test: Attention Graph Extraction")
    print(f"  Input: {text}")
    print(f"  Pairs found: {len(results['pairs'])}")
    print(f"  Compounds found: {len(results['compounds'])}")

    # Should find pairs of concepts
    assert len(results['pairs']) > 0
    print("  ✓ Passed\n")


def test_auto_memory_hook():
    """Test full auto-memory hook integration."""
    # Use temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"

        hook = AutoMemoryHook(
            db_path=db_path,
            instance_id="test-session",
            save_messages=True,
            occurrence_threshold=1  # Lower threshold for testing
        )

        print("Test: Auto Memory Hook Integration")

        # Save user message
        stats1 = hook.save_message(
            "user",
            "Let's build a neural_network with machine-learning"
        )
        print(f"  User message stats: {stats1}")

        # Save assistant message with decision
        stats2 = hook.save_message(
            "assistant",
            "I am going to create the neural network module using TensorFlow"
        )
        print(f"  Assistant message stats: {stats2}")

        # Get session stats
        session_stats = hook.get_session_stats()
        print(f"  Session stats: {session_stats}")

        assert session_stats['messages'] == 2
        assert session_stats['decisions'] >= 1
        assert session_stats['concepts_added'] >= 2

        print("  ✓ Passed\n")


def test_attention_graph_with_database():
    """Test attention graph with database persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_graph.db"

        extractor = AttentionGraphExtractor(db_path=db_path)

        print("Test: Attention Graph with Database")

        # Analyze message
        message = "Deep learning networks using neural architecture"
        stats = extractor.analyze_message(message, instance_id="test")

        print(f"  Message: {message}")
        print(f"  Stats: {stats}")

        # Try to get neighbors (should work even if empty)
        neighbors = extractor.get_concept_neighbors("Deep", min_strength=0.1)
        print(f"  Neighbors of 'Deep': {len(neighbors)}")

        print("  ✓ Passed\n")


if __name__ == "__main__":
    print("="*70)
    print("CONTINUUM EXTRACTION MODULE - Test Suite")
    print("="*70)
    print()

    test_concept_extraction()
    test_concept_extraction_with_counts()
    test_decision_extraction()
    test_canonical_mapper()
    test_attention_graph_extraction()
    test_auto_memory_hook()
    test_attention_graph_with_database()

    print("="*70)
    print("All tests passed!")
    print("="*70)
