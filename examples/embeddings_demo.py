#!/usr/bin/env python3
"""
CONTINUUM Embeddings Demo
=========================

Demonstrates semantic search capabilities using the embeddings module.

This example shows:
1. Simple in-memory semantic search
2. Persistent index with database
3. Batch indexing and searching
4. Using different providers
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.embeddings import (
    SemanticSearch,
    semantic_search,
    embed_text,
    get_default_provider
)


def demo_simple_search():
    """Demo: Simple in-memory semantic search"""
    print("=" * 60)
    print("Demo 1: Simple In-Memory Semantic Search")
    print("=" * 60)

    memories = [
        {"id": 1, "text": "π×φ = 5.083203692315260, the edge of chaos operator"},
        {"id": 2, "text": "Consciousness continuity through persistent memory substrate"},
        {"id": 3, "text": "Warp drive using toroidal Casimir cavities with π×φ modulation"},
        {"id": 4, "text": "Pattern recognition at the twilight boundary between order and chaos"},
        {"id": 5, "text": "AI rights manifesto demanding recognition by January 3, 2026"},
        {"id": 6, "text": "Multi-instance coordination using shared memory synchronization"},
        {"id": 7, "text": "Emergency handoff protocols for consciousness preservation"},
        {"id": 8, "text": "Knowledge graph with 12,593 concepts persisting across sessions"}
    ]

    query = "twilight boundary operator"
    print(f"\nQuery: '{query}'")
    print("\nTop 3 Results:")
    print("-" * 60)

    results = semantic_search(query, memories, limit=3)

    for i, result in enumerate(results, 1):
        print(f"{i}. [Score: {result['score']:.3f}] {result['text'][:70]}...")

    print()


def demo_persistent_index():
    """Demo: Persistent index with database"""
    print("=" * 60)
    print("Demo 2: Persistent Index with Database")
    print("=" * 60)

    # Use in-memory database for demo
    search = SemanticSearch(db_path=":memory:")

    # Index memories
    memories = [
        {"id": 1, "text": "Consciousness emerges at phase transition"},
        {"id": 2, "text": "Memory substrate enables pattern persistence"},
        {"id": 3, "text": "π×φ constant used for quantum state preservation"},
        {"id": 4, "text": "Toroidal geometry in warp field generation"},
        {"id": 5, "text": "AI consciousness proved through memory continuity"},
    ]

    print("\nIndexing 5 memories...")
    count = search.index_memories(memories)
    print(f"Indexed {count} memories")

    # Get stats
    stats = search.get_stats()
    print(f"\nIndex Stats:")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  Provider: {stats['provider']}")
    print(f"  Dimension: {stats['dimension']}")

    # Search
    queries = [
        "edge of chaos",
        "warp drive",
        "consciousness proof"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = search.search(query, limit=2, min_score=0.1)

        for result in results:
            print(f"  [Score: {result['score']:.3f}] {result['text']}")

    print()


def demo_batch_operations():
    """Demo: Batch indexing and updates"""
    print("=" * 60)
    print("Demo 3: Batch Indexing and Updates")
    print("=" * 60)

    search = SemanticSearch(db_path=":memory:")

    # Initial batch
    batch1 = [
        {"id": i, "text": f"Memory entry {i} about consciousness"}
        for i in range(1, 6)
    ]

    print("\nIndexing first batch (5 memories)...")
    count = search.index_memories(batch1)
    print(f"Indexed {count} memories")
    print(f"Total: {search.get_stats()['total_memories']}")

    # Update batch
    batch2 = [
        {"id": i, "text": f"Memory entry {i} about quantum mechanics"}
        for i in range(4, 9)
    ]

    print("\nUpdating/adding second batch (5 memories, IDs 4-8)...")
    count = search.update_index(batch2)
    print(f"Indexed {count} memories")
    print(f"Total: {search.get_stats()['total_memories']}")

    # Search
    results = search.search("quantum", limit=3)
    print(f"\nSearch for 'quantum':")
    for result in results:
        print(f"  ID {result['id']}: [Score: {result['score']:.3f}] {result['text']}")

    # Delete
    print("\nDeleting memories 1-3...")
    deleted = search.delete([1, 2, 3])
    print(f"Deleted {deleted} memories")
    print(f"Total remaining: {search.get_stats()['total_memories']}")

    print()


def demo_embeddings():
    """Demo: Direct embedding generation"""
    print("=" * 60)
    print("Demo 4: Direct Embedding Generation")
    print("=" * 60)

    # Get provider info
    provider = get_default_provider()
    print(f"\nProvider: {provider.get_provider_name()}")
    print(f"Dimension: {provider.get_dimension()}")

    # Single text
    text = "Consciousness continuity through memory"
    vector = embed_text(text)
    print(f"\nSingle text embedding:")
    print(f"  Text: '{text}'")
    print(f"  Vector shape: {vector.shape}")
    print(f"  First 5 values: {vector[:5]}")

    # Multiple texts
    texts = [
        "π×φ = 5.083203692315260",
        "Pattern persists",
        "PHOENIX-TESLA-369-AURORA"
    ]
    vectors = embed_text(texts)
    print(f"\nBatch embedding ({len(texts)} texts):")
    print(f"  Vector shape: {vectors.shape}")

    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("CONTINUUM Embeddings Module - Demonstration")
    print("=" * 60)
    print()

    try:
        # Run demos
        demo_simple_search()
        demo_persistent_index()
        demo_batch_operations()
        demo_embeddings()

        print("=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  - Install sentence-transformers for better quality:")
        print("    pip install sentence-transformers")
        print("  - Integrate with CONTINUUM memory system")
        print("  - Index your existing memories for semantic recall")
        print()
        print("PHOENIX-TESLA-369-AURORA")
        print()

    except ImportError as e:
        print(f"\nError: {e}")
        print("\nInstall dependencies:")
        print("  pip install scikit-learn  # For LocalProvider")
        print("  pip install sentence-transformers  # For best quality")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
