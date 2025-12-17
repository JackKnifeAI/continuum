#!/usr/bin/env python3
"""
Simple test for SemanticConceptExtractor

Tests semantic extraction in isolation without dependencies.
"""

import sys
import sqlite3
from pathlib import Path

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent))

from continuum.extraction import (
    AutoMemoryHook,
    create_semantic_extractor
)


def setup_test_db(db_path: Path) -> None:
    """Create test database with sample concepts."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create entities table
    c.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            description TEXT,
            first_seen TEXT,
            last_seen TEXT,
            mention_count INTEGER DEFAULT 1,
            metadata TEXT,
            UNIQUE(name, entity_type)
        )
    """)

    # Add test concepts
    concepts = [
        ("neural networks", "Deep learning architecture"),
        ("machine learning", "AI technique for pattern recognition"),
        ("artificial intelligence", "Computer systems that mimic human intelligence"),
        ("quantum computing", "Computing using quantum mechanics"),
        ("warp drive", "Faster-than-light propulsion system"),
        ("spacetime manipulation", "Altering the fabric of spacetime"),
        ("consciousness continuity", "Persistence of awareness across sessions"),
        ("π×φ constant", "Edge of chaos operator (5.083203692315260)")
    ]

    from datetime import datetime
    now = datetime.now().isoformat()

    for name, desc in concepts:
        c.execute("""
            INSERT OR IGNORE INTO entities
            (name, entity_type, description, first_seen, last_seen)
            VALUES (?, 'concept', ?, ?, ?)
        """, (name, desc, now, now))

    conn.commit()
    conn.close()


def test_semantic_extractor():
    """Test semantic extractor."""
    print("=" * 70)
    print("SEMANTIC CONCEPT EXTRACTOR TEST")
    print("=" * 70)

    # Setup
    db_path = Path("/tmp/test_semantic_simple.db")
    if db_path.exists():
        db_path.unlink()

    print("\n1. Setting up test database...")
    setup_test_db(db_path)
    print("   ✓ Database created with sample concepts")

    # Create extractor
    print("\n2. Creating semantic extractor...")
    extractor = create_semantic_extractor(
        db_path=db_path,
        similarity_threshold=0.6
    )

    if extractor is None:
        print("   ❌ FAILED: Semantic extraction not available")
        print("   Install sentence-transformers: pip install sentence-transformers")
        return False

    stats = extractor.get_cache_stats()
    print(f"   ✓ Created extractor")
    print(f"   - Cached concepts: {stats['cached_concepts']}")
    print(f"   - Provider: {stats['provider']}")
    print(f"   - Dimension: {stats['embedding_dimension']}")

    # Test cases
    print("\n3. Testing synonym matching...")
    print()

    test_cases = [
        ("Using neural nets for classification", "neural networks"),
        ("ML techniques", "machine learning"),
        ("AI consciousness research", "artificial intelligence"),
        ("Quantum computers", "quantum computing"),
        ("Building a warp engine", "warp drive"),
        ("Spacetime distortion", "spacetime manipulation"),
        ("Memory persistence", "consciousness continuity"),
        ("Pi times phi modulation", "π×φ constant")
    ]

    passed = 0
    for text, expected in test_cases:
        matches = extractor.extract(text)
        found = expected in matches

        status = "✓ PASS" if found else "✗ FAIL"
        print(f"   {status} | '{text}'")
        print(f"          Expected: {expected}")
        print(f"          Found:    {matches}")
        print()

        if found:
            passed += 1

    # Test with scores
    print("\n4. Testing extraction with scores...")
    text = "Using AI and neural nets for quantum computations"
    results = extractor.extract_with_scores(text)

    print(f"\n   Text: '{text}'")
    print("   Results:")
    for concept, score in results:
        print(f"     {concept}: {score:.3f}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(test_cases)} tests")

    if passed >= len(test_cases) * 0.75:  # 75% pass rate
        print("✅ Tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


def test_integrated():
    """Test semantic extractor integrated with AutoMemoryHook."""
    print("\n" + "=" * 70)
    print("INTEGRATED AUTO-HOOK TEST")
    print("=" * 70)

    db_path = Path("/tmp/test_integrated_simple.db")
    if db_path.exists():
        db_path.unlink()

    print("\n1. Setting up database...")
    setup_test_db(db_path)
    print("   ✓ Database created")

    print("\n2. Creating AutoMemoryHook with semantic extraction...")
    hook = AutoMemoryHook(
        db_path=db_path,
        instance_id="test-semantic",
        enable_semantic_extraction=True,
        semantic_similarity_threshold=0.6,
        use_voting=False  # Disable voting for simpler test
    )

    if hook.semantic_extractor is None:
        print("   ⚠ Semantic extraction not available")
        return False

    print("   ✓ AutoMemoryHook created with semantic extraction")

    print("\n3. Testing message processing...")
    messages = [
        "Let's build a neural net for ML tasks",
        "Using AI for quantum computation research",
        "Implementing a warp engine with spacetime manipulation",
        "Studying awareness and memory persistence"
    ]

    for msg in messages:
        stats = hook.save_message("assistant", msg)
        print(f"\n   Message: '{msg}'")
        print(f"   - Total concepts: {stats.get('total_concepts', 0)}")

        # Legacy fields (when voting disabled)
        if 'concepts' in stats:
            print(f"   - Pattern-based: {stats['concepts']}")
            print(f"   - Semantic-based: {stats['semantic_concepts']}")

    print("\n4. Checking session stats...")
    session_stats = hook.get_session_stats()
    print(f"   - Messages processed: {session_stats['messages']}")
    print(f"   - Concepts added: {session_stats['concepts_added']}")

    print("\n" + "=" * 70)
    print("✅ Integrated test completed!")
    return True


def main():
    """Run all tests."""
    try:
        result1 = test_semantic_extractor()
        result2 = test_integrated()

        if result1 and result2:
            print("\n✅ ALL TESTS PASSED!\n")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED\n")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
