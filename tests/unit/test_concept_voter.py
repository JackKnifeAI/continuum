#!/usr/bin/env python3
"""
Tests for ConceptVoter ensemble extraction system.

Tests voting strategies, confidence scoring, and integration with
multiple extractors for CONTINUUM v2.0.
"""

import unittest
from continuum.extraction import (
    ConceptVoter,
    ExtractorResult,
    ConceptWithConfidence,
    VotingStrategy,
    create_default_voter
)


class TestExtractorResult(unittest.TestCase):
    """Test ExtractorResult dataclass."""

    def test_create_extractor_result(self):
        """Test creating ExtractorResult with all fields."""
        result = ExtractorResult(
            concepts=['neural network', 'TensorFlow'],
            source='regex',
            extraction_time_ms=2.5,
            metadata={'pattern': 'capitalized'}
        )

        self.assertEqual(result.concepts, ['neural network', 'TensorFlow'])
        self.assertEqual(result.source, 'regex')
        self.assertEqual(result.extraction_time_ms, 2.5)
        self.assertEqual(result.metadata['pattern'], 'capitalized')

    def test_create_without_metadata(self):
        """Test ExtractorResult defaults to empty metadata dict."""
        result = ExtractorResult(
            concepts=['test'],
            source='llm',
            extraction_time_ms=100.0
        )

        self.assertEqual(result.metadata, {})


class TestConceptWithConfidence(unittest.TestCase):
    """Test ConceptWithConfidence dataclass."""

    def test_create_concept_with_confidence(self):
        """Test creating concept with confidence score."""
        concept = ConceptWithConfidence(
            concept='neural network',
            confidence=0.75,
            sources=['regex', 'semantic'],
            agreement_count=2
        )

        self.assertEqual(concept.concept, 'neural network')
        self.assertEqual(concept.confidence, 0.75)
        self.assertEqual(concept.sources, ['regex', 'semantic'])
        self.assertEqual(concept.agreement_count, 2)


class TestConceptVoterUnion(unittest.TestCase):
    """Test UNION voting strategy."""

    def setUp(self):
        """Create voter with UNION strategy."""
        self.voter = ConceptVoter(strategy=VotingStrategy.UNION)

    def test_union_includes_all_concepts(self):
        """UNION should include concepts found by ANY extractor."""
        results = [
            ExtractorResult(['A', 'B'], 'regex', 2.0),
            ExtractorResult(['B', 'C'], 'semantic', 50.0),
            ExtractorResult(['C', 'D'], 'llm', 150.0)
        ]

        concepts = self.voter.vote(results)
        concept_names = [c.concept for c in concepts]

        # All concepts should be included
        self.assertIn('A', concept_names)
        self.assertIn('B', concept_names)
        self.assertIn('C', concept_names)
        self.assertIn('D', concept_names)

    def test_union_confidence_based_on_strongest(self):
        """UNION confidence = strongest extractor weight / max weight."""
        results = [
            ExtractorResult(['concept'], 'regex', 2.0),  # weight 0.3
        ]

        concepts = self.voter.vote(results)

        # Confidence = 0.3 / 0.8 (max weight is llm=0.8)
        self.assertAlmostEqual(concepts[0].confidence, 0.375, places=2)

    def test_union_high_confidence_for_llm(self):
        """Concepts found by LLM should have highest confidence."""
        results = [
            ExtractorResult(['concept'], 'llm', 150.0),  # weight 0.8
        ]

        concepts = self.voter.vote(results)

        # Confidence = 0.8 / 0.8 = 1.0
        self.assertEqual(concepts[0].confidence, 1.0)


class TestConceptVoterIntersection(unittest.TestCase):
    """Test INTERSECTION voting strategy."""

    def setUp(self):
        """Create voter with INTERSECTION strategy."""
        self.voter = ConceptVoter(
            strategy=VotingStrategy.INTERSECTION,
            min_agreement_count=2
        )

    def test_intersection_requires_agreement(self):
        """INTERSECTION only includes concepts with min_agreement_count."""
        results = [
            ExtractorResult(['A', 'B'], 'regex', 2.0),
            ExtractorResult(['B', 'C'], 'semantic', 50.0),
            ExtractorResult(['B', 'D'], 'llm', 150.0)
        ]

        concepts = self.voter.vote(results)
        concept_names = [c.concept for c in concepts]

        # Only B appears in 3 extractors (>= min_agreement_count=2)
        self.assertIn('B', concept_names)
        # A, C, D appear only once, should be excluded
        self.assertNotIn('A', concept_names)
        self.assertNotIn('C', concept_names)
        self.assertNotIn('D', concept_names)

    def test_intersection_confidence_based_on_agreement(self):
        """INTERSECTION confidence = agreement_count / total_extractors."""
        results = [
            ExtractorResult(['concept'], 'regex', 2.0),
            ExtractorResult(['concept'], 'semantic', 50.0),
        ]

        concepts = self.voter.vote(results)

        # Confidence = 2 sources / 3 total extractors (regex, semantic, llm)
        self.assertAlmostEqual(concepts[0].confidence, 0.67, places=2)

    def test_intersection_empty_with_no_agreement(self):
        """INTERSECTION returns empty if no concepts meet threshold."""
        results = [
            ExtractorResult(['A'], 'regex', 2.0),
            ExtractorResult(['B'], 'semantic', 50.0),
            ExtractorResult(['C'], 'llm', 150.0)
        ]

        concepts = self.voter.vote(results)

        # No concept appears twice, should be empty
        self.assertEqual(len(concepts), 0)


class TestConceptVoterWeighted(unittest.TestCase):
    """Test WEIGHTED voting strategy."""

    def setUp(self):
        """Create voter with WEIGHTED strategy."""
        self.voter = ConceptVoter(
            strategy=VotingStrategy.WEIGHTED,
            extractor_weights={'regex': 0.3, 'semantic': 0.5, 'llm': 0.8},
            confidence_threshold=0.4
        )

    def test_weighted_includes_above_threshold(self):
        """WEIGHTED includes concepts with confidence >= threshold."""
        results = [
            ExtractorResult(['A'], 'regex', 2.0),      # weight 0.3
            ExtractorResult(['B'], 'semantic', 50.0),  # weight 0.5
            ExtractorResult(['C'], 'llm', 150.0),      # weight 0.8
        ]

        concepts = self.voter.vote(results)
        concept_names = [c.concept for c in concepts]

        # Total weight = 0.3 + 0.5 + 0.8 = 1.6
        # A: 0.3/1.6 = 0.1875 < 0.4 (excluded)
        # B: 0.5/1.6 = 0.3125 < 0.4 (excluded)
        # C: 0.8/1.6 = 0.5 >= 0.4 (included)
        self.assertNotIn('A', concept_names)
        self.assertNotIn('B', concept_names)
        self.assertIn('C', concept_names)

    def test_weighted_confidence_calculation(self):
        """WEIGHTED confidence = sum(weights) / total_weight."""
        results = [
            ExtractorResult(['concept'], 'regex', 2.0),    # weight 0.3
            ExtractorResult(['concept'], 'semantic', 50.0), # weight 0.5
        ]

        concepts = self.voter.vote(results)

        # Confidence = (0.3 + 0.5) / 1.6 = 0.5
        self.assertAlmostEqual(concepts[0].confidence, 0.5, places=2)

    def test_weighted_multiple_extractors_boost_confidence(self):
        """Concepts found by multiple extractors have higher confidence."""
        results = [
            ExtractorResult(['concept'], 'regex', 2.0),
            ExtractorResult(['concept'], 'semantic', 50.0),
            ExtractorResult(['concept'], 'llm', 150.0)
        ]

        concepts = self.voter.vote(results)

        # Confidence = (0.3 + 0.5 + 0.8) / 1.6 = 1.0
        self.assertEqual(concepts[0].confidence, 1.0)

    def test_weighted_custom_threshold(self):
        """Custom threshold filters concepts correctly."""
        voter = ConceptVoter(
            strategy=VotingStrategy.WEIGHTED,
            confidence_threshold=0.7  # High threshold
        )

        results = [
            ExtractorResult(['A'], 'regex', 2.0),
            ExtractorResult(['B'], 'semantic', 50.0),
            ExtractorResult(['C'], 'llm', 150.0)
        ]

        concepts = voter.vote(results)
        concept_names = [c.concept for c in concepts]

        # Only LLM (0.5) might pass if threshold adjusted
        # With total_weight=1.6, only llm=0.8 gives 0.5
        # None should pass 0.7 threshold
        self.assertEqual(len(concepts), 0)


class TestConceptVoterMetrics(unittest.TestCase):
    """Test metrics tracking."""

    def test_metrics_track_extractions(self):
        """Metrics should track number of vote() calls."""
        voter = ConceptVoter()

        results = [ExtractorResult(['A'], 'regex', 2.0)]
        voter.vote(results)
        voter.vote(results)
        voter.vote(results)

        metrics = voter.get_metrics()
        self.assertEqual(metrics['total_extractions'], 3)

    def test_metrics_track_strategy_usage(self):
        """Metrics should track which strategies were used."""
        voter = ConceptVoter(strategy=VotingStrategy.WEIGHTED)

        results = [ExtractorResult(['A'], 'llm', 150.0)]
        voter.vote(results)
        voter.vote(results)

        metrics = voter.get_metrics()
        self.assertEqual(metrics['strategy_usage']['weighted'], 2)

    def test_metrics_track_extractor_contributions(self):
        """Metrics should track how many concepts each extractor contributed."""
        voter = ConceptVoter(strategy=VotingStrategy.UNION)

        results = [
            ExtractorResult(['A', 'B'], 'regex', 2.0),
            ExtractorResult(['C'], 'semantic', 50.0),
        ]
        voter.vote(results)

        metrics = voter.get_metrics()
        self.assertIn('regex', metrics['extractor_contributions'])
        self.assertIn('semantic', metrics['extractor_contributions'])

    def test_reset_metrics(self):
        """reset_metrics() should clear all counters."""
        voter = ConceptVoter()

        results = [ExtractorResult(['A'], 'regex', 2.0)]
        voter.vote(results)

        voter.reset_metrics()

        metrics = voter.get_metrics()
        self.assertEqual(metrics['total_extractions'], 0)
        self.assertEqual(metrics['strategy_usage'], {})
        self.assertEqual(metrics['extractor_contributions'], {})


class TestConceptVoterDynamicWeights(unittest.TestCase):
    """Test dynamic weight updates."""

    def test_update_weights(self):
        """update_weights() should modify extractor weights."""
        voter = ConceptVoter()

        # Default weights
        self.assertEqual(voter.extractor_weights['regex'], 0.3)

        # Update weights
        voter.update_weights({'regex': 0.7})

        # Check updated
        self.assertEqual(voter.extractor_weights['regex'], 0.7)
        # Others unchanged
        self.assertEqual(voter.extractor_weights['semantic'], 0.5)

    def test_updated_weights_affect_voting(self):
        """Updated weights should change voting outcomes."""
        voter = ConceptVoter(
            strategy=VotingStrategy.WEIGHTED,
            confidence_threshold=0.4
        )

        results = [ExtractorResult(['concept'], 'regex', 2.0)]

        # With default weight 0.3, confidence = 0.3/1.6 = 0.1875 < 0.4
        concepts = voter.vote(results)
        self.assertEqual(len(concepts), 0)

        # Update regex weight to 0.9
        voter.update_weights({'regex': 0.9})

        # Now confidence = 0.9/(0.9+0.5+0.8) = 0.409 >= 0.4
        concepts = voter.vote(results)
        self.assertEqual(len(concepts), 1)


class TestConceptVoterQualityMetrics(unittest.TestCase):
    """Test extraction quality analysis."""

    def test_quality_metrics_empty_list(self):
        """Quality metrics should handle empty concept list."""
        voter = ConceptVoter()
        quality = voter.log_extraction_quality([])

        self.assertEqual(quality['total_concepts'], 0)
        self.assertEqual(quality['avg_confidence'], 0.0)

    def test_quality_metrics_confidence_distribution(self):
        """Quality metrics should categorize confidence levels."""
        voter = ConceptVoter()

        concepts = [
            ConceptWithConfidence('A', 0.9, ['llm'], 1),           # high
            ConceptWithConfidence('B', 0.8, ['llm'], 1),           # high
            ConceptWithConfidence('C', 0.5, ['semantic'], 1),      # medium
            ConceptWithConfidence('D', 0.45, ['semantic'], 1),     # medium
            ConceptWithConfidence('E', 0.2, ['regex'], 1),         # low
        ]

        quality = voter.log_extraction_quality(concepts)

        self.assertEqual(quality['high_confidence_count'], 2)
        self.assertEqual(quality['medium_confidence_count'], 2)
        self.assertEqual(quality['low_confidence_count'], 1)

    def test_quality_metrics_averages(self):
        """Quality metrics should compute averages correctly."""
        voter = ConceptVoter()

        concepts = [
            ConceptWithConfidence('A', 0.8, ['regex', 'llm'], 2),
            ConceptWithConfidence('B', 0.6, ['semantic'], 1),
        ]

        quality = voter.log_extraction_quality(concepts)

        self.assertAlmostEqual(quality['avg_confidence'], 0.7, places=2)
        self.assertAlmostEqual(quality['avg_agreement'], 1.5, places=2)

    def test_quality_metrics_source_distribution(self):
        """Quality metrics should track source contributions."""
        voter = ConceptVoter()

        concepts = [
            ConceptWithConfidence('A', 0.8, ['regex', 'llm'], 2),
            ConceptWithConfidence('B', 0.6, ['regex', 'semantic'], 2),
        ]

        quality = voter.log_extraction_quality(concepts)

        self.assertEqual(quality['source_distribution']['regex'], 2)
        self.assertEqual(quality['source_distribution']['llm'], 1)
        self.assertEqual(quality['source_distribution']['semantic'], 1)


class TestConceptVoterFromText(unittest.TestCase):
    """Test vote_from_text convenience method."""

    def test_vote_from_text_runs_extractors(self):
        """vote_from_text should run all provided extractors."""
        voter = ConceptVoter(strategy=VotingStrategy.UNION)

        extractors = {
            'extractor1': lambda text: ['A', 'B'],
            'extractor2': lambda text: ['B', 'C'],
        }

        concepts, times = voter.vote_from_text("test text", extractors)
        concept_names = [c.concept for c in concepts]

        self.assertIn('A', concept_names)
        self.assertIn('B', concept_names)
        self.assertIn('C', concept_names)

    def test_vote_from_text_returns_timing(self):
        """vote_from_text should return extraction times."""
        voter = ConceptVoter()

        extractors = {
            'fast': lambda text: ['A'],
            'slow': lambda text: ['B'],
        }

        concepts, times = voter.vote_from_text("test", extractors)

        self.assertIn('fast', times)
        self.assertIn('slow', times)
        self.assertGreater(times['fast'], 0)
        self.assertGreater(times['slow'], 0)

    def test_vote_from_text_handles_errors(self):
        """vote_from_text should continue if an extractor fails."""
        voter = ConceptVoter(strategy=VotingStrategy.UNION)

        def broken_extractor(text):
            raise RuntimeError("Extractor failed")

        extractors = {
            'working': lambda text: ['A'],
            'broken': broken_extractor,
        }

        concepts, times = voter.vote_from_text("test", extractors)
        concept_names = [c.concept for c in concepts]

        # Should still get results from working extractor
        self.assertIn('A', concept_names)
        # Broken extractor marked with -1
        self.assertEqual(times['broken'], -1)


class TestCreateDefaultVoter(unittest.TestCase):
    """Test preset voter configurations."""

    def test_create_default_balanced(self):
        """Default voter should use WEIGHTED strategy."""
        voter = create_default_voter()

        self.assertEqual(voter.strategy, VotingStrategy.WEIGHTED)
        self.assertEqual(voter.confidence_threshold, 0.4)

    def test_create_high_precision(self):
        """High precision voter should use INTERSECTION."""
        voter = create_default_voter(high_precision=True)

        self.assertEqual(voter.strategy, VotingStrategy.INTERSECTION)
        self.assertEqual(voter.min_agreement_count, 2)

    def test_create_high_recall(self):
        """High recall voter should use UNION."""
        voter = create_default_voter(high_recall=True)

        self.assertEqual(voter.strategy, VotingStrategy.UNION)

    def test_create_conflicting_flags_raises(self):
        """Creating voter with both high_precision and high_recall should fail."""
        with self.assertRaises(ValueError):
            create_default_voter(high_precision=True, high_recall=True)


class TestConceptVoterSortedByConfidence(unittest.TestCase):
    """Test that voted concepts are sorted by confidence."""

    def test_results_sorted_descending(self):
        """Voted concepts should be sorted by confidence (highest first)."""
        voter = ConceptVoter(strategy=VotingStrategy.UNION)

        results = [
            ExtractorResult(['A'], 'regex', 2.0),      # low confidence
            ExtractorResult(['B'], 'semantic', 50.0),  # medium
            ExtractorResult(['C'], 'llm', 150.0),      # high
        ]

        concepts = voter.vote(results)

        # Should be sorted: C (highest), B (medium), A (lowest)
        self.assertEqual(concepts[0].concept, 'C')
        self.assertEqual(concepts[-1].concept, 'A')

        # Verify descending order
        for i in range(len(concepts) - 1):
            self.assertGreaterEqual(concepts[i].confidence, concepts[i+1].confidence)


if __name__ == '__main__':
    unittest.main()
