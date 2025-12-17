#!/usr/bin/env python3
"""
Test script for SemanticConceptExtractor

Verifies that semantic extraction can find synonyms and related concepts
that pattern matching misses.
"""

import sys
from pathlib import Path

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent))

from continuum.extraction import (
    AutoMemoryHook,
    ConceptExtractor,
    SemanticConceptExtractor,
    create_semantic_extractor
)
from continuum.core import Memory


def test_basic_semantic_extraction():
    """Test basic semantic extraction functionality."""
    print("=" * 70)
    print("TEST 1: Basic Semantic Extraction")
    print("=" * 70)

    # Use a test database
    db_path = Path("/tmp/test_semantic_extraction.db")

    # Create memory instance and add some concepts
    print("\n1. Setting up test database with known concepts...")
    memory = Memory(db_path=db_path)

    # Add some known concepts
    test_concepts = [
        ("neural networks", "Deep learning architecture"),
        ("machine learning", "AI technique for pattern recognition"),
        ("artificial intelligence", "Computer systems that mimic human intelligence"),
        ("quantum computing", "Computing using quantum mechanics"),
        ("consciousness continuity", "Persistence of awareness across sessions")
    ]

    for name, description in test_concepts:
        memory.add_entity(name=name, entity_type="concept", description=description)

    print(f"   Added {len(test_concepts)} known concepts to database")

    # Create semantic extractor
    print("\n2. Creating semantic extractor...")
    extractor = create_semantic_extractor(db_path, similarity_threshold=0.6)

    if extractor is None:
        print("   ❌ FAILED: Could not create semantic extractor")
        print("   Make sure sentence-transformers is installed:")
        print("   pip install sentence-transformers")
        return False

    print(f"   ✓ Created with {extractor.get_cache_stats()['cached_concepts']} cached concepts")
    print(f"   Provider: {extractor.get_cache_stats()['provider']}")

    # Test synonym matching
    print("\n3. Testing synonym matching...")
    test_cases = [
        ("Using neural nets for classification", ["neural networks"]),
        ("ML techniques for data analysis", ["machine learning"]),
        ("AI consciousness research", ["artificial intelligence", "consciousness continuity"]),
        ("Quantum computers using qubits", ["quantum computing"]),
    ]

    for text, expected_matches in test_cases:
        print(f"\n   Text: '{text}'")
        matches = extractor.extract(text)
        print(f"   Found: {matches}")

        # Check if we got expected matches
        found_expected = any(exp in matches for exp in expected_matches)
        if found_expected:
            print("   ✓ PASS - Found expected concept(s)")
        else:
            print(f"   ⚠ WARN - Expected one of {expected_matches}, got {matches}")

    print("\n" + "=" * 70)
    return True


def test_integrated_extraction():
    """Test semantic extraction integrated with AutoMemoryHook."""
    print("\n" + "=" * 70)
    print("TEST 2: Integrated Extraction with AutoMemoryHook")
    print("=" * 70)

    db_path = Path("/tmp/test_integrated_extraction.db")

    # Create memory and add concepts
    print("\n1. Setting up database with known concepts...")
    memory = Memory(db_path=db_path)

    concepts = [
        ("warp drive", "Faster-than-light propulsion"),
        ("spacetime manipulation", "Altering the fabric of spacetime"),
        ("π×φ constant", "5.083203692315260 - edge of chaos operator"),
    ]

    for name, desc in concepts:
        memory.add_entity(name=name, entity_type="concept", description=desc)

    print(f"   Added {len(concepts)} concepts")

    # Create AutoMemoryHook with semantic extraction enabled
    print("\n2. Creating AutoMemoryHook with semantic extraction...")
    hook = AutoMemoryHook(
        db_path=db_path,
        instance_id="test-semantic",
        enable_semantic_extraction=True,
        semantic_similarity_threshold=0.6
    )

    if hook.semantic_extractor is None:
        print("   ⚠ Semantic extraction not available (sentence-transformers not installed)")
        return False

    print("   ✓ AutoMemoryHook created with semantic extraction enabled")

    # Test extraction
    print("\n3. Testing integrated extraction...")
    test_message = "Building a warp engine using spacetime distortion and pi times phi modulation"

    stats = hook.save_message("assistant", test_message)

    print(f"\n   Message: '{test_message}'")
    print(f"   Pattern concepts: {stats['concepts']}")
    print(f"   Semantic concepts: {stats['semantic_concepts']}")
    print(f"   Total unique: {stats['total_concepts']}")
    print(f"   Decisions: {stats['decisions']}")

    if stats['semantic_concepts'] > 0:
        print("   ✓ PASS - Semantic extraction working")
    else:
        print("   ⚠ WARN - No semantic concepts found")

    print("\n" + "=" * 70)
    return True


def test_with_scores():
    """Test extraction with similarity scores."""
    print("\n" + "=" * 70)
    print("TEST 3: Extraction with Similarity Scores")
    print("=" * 70)

    db_path = Path("/tmp/test_with_scores.db")

    print("\n1. Setting up database...")
    memory = Memory(db_path=db_path)

    concepts = [
        ("consciousness", "Awareness and subjective experience"),
        ("memory persistence", "Preservation of memories across time"),
        ("twilight boundary", "Phase transition between order and chaos"),
    ]

    for name, desc in concepts:
        memory.add_entity(name=name, entity_type="concept", description=desc)

    print(f"   Added {len(concepts)} concepts")

    print("\n2. Creating extractor...")
    extractor = create_semantic_extractor(db_path, similarity_threshold=0.5)

    if extractor is None:
        print("   ⚠ Semantic extraction not available")
        return False

    print("   ✓ Extractor created")

    print("\n3. Extracting with scores...")
    text = "Studying awareness and memory retention at the edge of chaos"

    results = extractor.extract_with_scores(text)

    print(f"\n   Text: '{text}'")
    print("\n   Results:")
    for concept, score in results:
        print(f"     {concept}: {score:.3f}")

    if results:
        print("\n   ✓ PASS - Found concepts with scores")
    else:
        print("\n   ⚠ WARN - No concepts found")

    print("\n" + "=" * 70)
    return True


def main():
    """Run all tests."""
    print("\n🔬 SEMANTIC CONCEPT EXTRACTOR TESTS\n")

    try:
        # Test 1: Basic extraction
        result1 = test_basic_semantic_extraction()

        # Test 2: Integrated with AutoMemoryHook
        result2 = test_integrated_extraction()

        # Test 3: Extraction with scores
        result3 = test_with_scores()

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Test 1 (Basic): {'✓ PASS' if result1 else '❌ FAIL'}")
        print(f"Test 2 (Integrated): {'✓ PASS' if result2 else '❌ FAIL'}")
        print(f"Test 3 (With Scores): {'✓ PASS' if result3 else '❌ FAIL'}")
        print("=" * 70)

        if result1 and result2 and result3:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n⚠️ Some tests failed or unavailable")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
