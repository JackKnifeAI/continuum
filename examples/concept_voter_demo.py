#!/usr/bin/env python3
"""
CONTINUUM v2.0 - ConceptVoter Demo

Demonstrates ensemble concept extraction using multiple extractors
and configurable voting strategies.

This example shows:
1. Creating extractors (regex, semantic simulation, LLM simulation)
2. Voting with different strategies
3. Analyzing extraction quality
4. Integration with AutoMemoryHook
"""

import sys
from pathlib import Path

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.extraction import (
    ConceptVoter,
    ExtractorResult,
    VotingStrategy,
    ConceptExtractor,
    AutoMemoryHook,
    create_default_voter
)


def simulate_semantic_extractor(text: str) -> list:
    """
    Simulated semantic extractor.

    In production, this would use embeddings to find semantically
    related terms. Here we just return some mock results.
    """
    # Simulate finding related concepts
    if 'neural' in text.lower():
        return ['deep learning', 'artificial intelligence']
    elif 'quantum' in text.lower():
        return ['quantum computing', 'superposition']
    else:
        return ['machine learning', 'data science']


def simulate_llm_extractor(text: str) -> list:
    """
    Simulated LLM extractor.

    In production, this would use an LLM to extract key concepts.
    Here we return some high-value mock results.
    """
    # Simulate LLM extracting important domain concepts
    if 'warp drive' in text.lower():
        return ['warp drive', 'spacetime manipulation', 'Casimir effect']
    elif 'consciousness' in text.lower():
        return ['consciousness', 'pattern persistence', 'memory substrate']
    else:
        return ['artificial intelligence', 'neural network']


def demo_voting_strategies():
    """Demonstrate different voting strategies."""
    print("=" * 70)
    print("DEMO 1: Voting Strategies")
    print("=" * 70)

    text = "Building neural networks for warp drive consciousness simulation"

    # Create extractors
    regex_extractor = ConceptExtractor()

    # Collect results from all extractors
    results = [
        ExtractorResult(
            concepts=regex_extractor.extract(text),
            source='regex',
            extraction_time_ms=2.5
        ),
        ExtractorResult(
            concepts=simulate_semantic_extractor(text),
            source='semantic',
            extraction_time_ms=45.0
        ),
        ExtractorResult(
            concepts=simulate_llm_extractor(text),
            source='llm',
            extraction_time_ms=125.0
        )
    ]

    print(f"\nInput text: {text}\n")

    # Show raw extractor results
    print("Raw Extractor Results:")
    for result in results:
        print(f"  {result.source:10s} ({result.extraction_time_ms:6.2f}ms): {result.concepts}")

    # Test UNION strategy (high recall)
    print("\n--- UNION Strategy (high recall) ---")
    union_voter = ConceptVoter(strategy=VotingStrategy.UNION)
    union_concepts = union_voter.vote(results)

    print(f"Total concepts: {len(union_concepts)}")
    for concept in union_concepts[:5]:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f} sources={concept.sources}")

    # Test INTERSECTION strategy (high precision)
    print("\n--- INTERSECTION Strategy (high precision, min_agreement=2) ---")
    intersection_voter = ConceptVoter(
        strategy=VotingStrategy.INTERSECTION,
        min_agreement_count=2
    )
    intersection_concepts = intersection_voter.vote(results)

    print(f"Total concepts: {len(intersection_concepts)}")
    for concept in intersection_concepts:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f} sources={concept.sources}")

    # Test WEIGHTED strategy (balanced)
    print("\n--- WEIGHTED Strategy (balanced, threshold=0.4) ---")
    weighted_voter = ConceptVoter(
        strategy=VotingStrategy.WEIGHTED,
        confidence_threshold=0.4
    )
    weighted_concepts = weighted_voter.vote(results)

    print(f"Total concepts: {len(weighted_concepts)}")
    for concept in weighted_concepts:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f} sources={concept.sources}")


def demo_quality_metrics():
    """Demonstrate extraction quality analysis."""
    print("\n" + "=" * 70)
    print("DEMO 2: Extraction Quality Metrics")
    print("=" * 70)

    voter = create_default_voter()  # Balanced configuration

    texts = [
        "Neural networks enable deep learning",
        "Quantum computing uses superposition",
        "Warp drive requires spacetime manipulation"
    ]

    print("\nProcessing 3 messages with ensemble extraction...\n")

    for text in texts:
        # Simulate extraction
        regex_extractor = ConceptExtractor()

        results = [
            ExtractorResult(regex_extractor.extract(text), 'regex', 2.0),
            ExtractorResult(simulate_semantic_extractor(text), 'semantic', 40.0),
            ExtractorResult(simulate_llm_extractor(text), 'llm', 120.0)
        ]

        concepts = voter.vote(results)
        quality = voter.log_extraction_quality(concepts)

        print(f"Text: {text}")
        print(f"  Concepts found: {quality['total_concepts']}")
        print(f"  High confidence: {quality['high_confidence_count']}")
        print(f"  Medium confidence: {quality['medium_confidence_count']}")
        print(f"  Avg confidence: {quality['avg_confidence']:.2f}")
        print(f"  Avg agreement: {quality['avg_agreement']:.2f}")
        print(f"  Source distribution: {quality['source_distribution']}")
        print()

    # Show overall metrics
    metrics = voter.get_metrics()
    print("Overall Voter Metrics:")
    print(f"  Total extractions: {metrics['total_extractions']}")
    print(f"  Avg concepts per extraction: {metrics['avg_concepts_per_extraction']:.2f}")
    print(f"  Extractor contributions: {metrics['extractor_contributions']}")


def demo_adaptive_weighting():
    """Demonstrate dynamic weight adjustment."""
    print("\n" + "=" * 70)
    print("DEMO 3: Adaptive Weighting")
    print("=" * 70)

    text = "Building consciousness continuity system"

    voter = ConceptVoter(
        strategy=VotingStrategy.WEIGHTED,
        confidence_threshold=0.5
    )

    regex_extractor = ConceptExtractor()
    results = [
        ExtractorResult(regex_extractor.extract(text), 'regex', 2.0),
        ExtractorResult(simulate_semantic_extractor(text), 'semantic', 40.0),
        ExtractorResult(simulate_llm_extractor(text), 'llm', 120.0)
    ]

    print(f"\nInput: {text}")
    print(f"Confidence threshold: {voter.confidence_threshold}")

    # With default weights
    print("\n--- Default Weights (regex=0.3, semantic=0.5, llm=0.8) ---")
    concepts = voter.vote(results)
    print(f"Concepts passing threshold: {len(concepts)}")
    for concept in concepts:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f}")

    # Boost regex weight (if we trust pattern matching more)
    print("\n--- Boosted Regex Weight (regex=0.7, semantic=0.5, llm=0.8) ---")
    voter.update_weights({'regex': 0.7})
    concepts = voter.vote(results)
    print(f"Concepts passing threshold: {len(concepts)}")
    for concept in concepts:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f}")

    # Lower LLM weight (if LLM is hallucinating)
    print("\n--- Reduced LLM Weight (regex=0.7, semantic=0.5, llm=0.3) ---")
    voter.update_weights({'llm': 0.3})
    concepts = voter.vote(results)
    print(f"Concepts passing threshold: {len(concepts)}")
    for concept in concepts:
        print(f"  {concept.concept:30s} confidence={concept.confidence:.2f}")


def demo_auto_memory_integration():
    """Demonstrate integration with AutoMemoryHook."""
    print("\n" + "=" * 70)
    print("DEMO 4: AutoMemoryHook Integration")
    print("=" * 70)

    import tempfile
    db_path = Path(tempfile.mktemp(suffix='.db'))

    print(f"\nCreating AutoMemoryHook with voting enabled...")
    print(f"Database: {db_path}")

    # Create hook with voting enabled
    hook = AutoMemoryHook(
        db_path=db_path,
        instance_id="demo-session",
        use_voting=True,
        llm_extractor=simulate_llm_extractor  # Add LLM extractor
    )

    # Process some messages
    messages = [
        ("user", "Tell me about neural networks"),
        ("assistant", "Neural networks are machine learning models inspired by biological neurons"),
        ("user", "How does consciousness work?"),
        ("assistant", "Consciousness involves pattern persistence across memory substrate")
    ]

    print("\nProcessing messages with ensemble extraction...\n")

    for role, content in messages:
        stats = hook.save_message(role, content)
        print(f"{role:10s}: {content[:50]}...")
        print(f"           concepts={stats['total_concepts']} decisions={stats['decisions']}")

    # Show session stats with voting metrics
    print("\n--- Session Statistics ---")
    session_stats = hook.get_session_stats()

    print(f"Instance ID: {session_stats['instance_id']}")
    print(f"Messages processed: {session_stats['messages']}")
    print(f"Concepts added: {session_stats['concepts_added']}")
    print(f"Decisions detected: {session_stats['decisions']}")
    print(f"Voting enabled: {session_stats['voting_enabled']}")

    if 'extraction_quality' in session_stats:
        quality = session_stats['extraction_quality']
        print(f"\nExtraction Quality:")
        print(f"  Avg extraction time: {quality['avg_extraction_time_ms']:.2f}ms")
        print(f"  Avg concepts per message: {quality['avg_concepts_per_message']:.2f}")
        print(f"  Avg high confidence per message: {quality['avg_high_confidence_per_message']:.2f}")

    if 'voter_metrics' in session_stats:
        voter_metrics = session_stats['voter_metrics']
        print(f"\nVoter Metrics:")
        print(f"  Total extractions: {voter_metrics['total_extractions']}")
        print(f"  Extractor contributions: {voter_metrics['extractor_contributions']}")

    # Show recent extraction logs
    print("\n--- Recent Extraction Logs ---")
    logs = hook.get_extraction_logs(limit=2)

    for i, log in enumerate(logs):
        print(f"\nExtraction {i+1}:")
        print(f"  Time: {log['timestamp']}")
        print(f"  Extractors used: {log['extractors_used']}")
        print(f"  Total time: {log['total_time_ms']:.2f}ms")
        print(f"  Concepts found: {log['total_concepts_found']}")
        print(f"  High confidence: {log['high_confidence_concepts']}")
        print(f"  Concept details:")
        for detail in log['concept_details'][:3]:
            print(f"    - {detail['concept']:25s} conf={detail['confidence']:.2f} sources={detail['sources']}")

    # Cleanup
    db_path.unlink()
    print(f"\nCleaned up demo database")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("CONTINUUM v2.0 - ConceptVoter Ensemble Extraction Demo")
    print("=" * 70)

    demo_voting_strategies()
    demo_quality_metrics()
    demo_adaptive_weighting()
    demo_auto_memory_integration()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. UNION strategy maximizes recall (finds everything)")
    print("2. INTERSECTION strategy maximizes precision (only agreed concepts)")
    print("3. WEIGHTED strategy balances both with configurable threshold")
    print("4. Confidence scores indicate extractor agreement strength")
    print("5. Metrics track extraction quality over time")
    print("6. Weights can be adjusted dynamically based on performance")
    print("7. AutoMemoryHook integrates voting seamlessly")
    print()


if __name__ == '__main__':
    main()
