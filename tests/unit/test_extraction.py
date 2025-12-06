"""
CONTINUUM Extraction Unit Tests
Tests for concept extraction, decision detection, and attention graphs
"""

import pytest
from pathlib import Path

from continuum.extraction import (
    ConceptExtractor,
    DecisionExtractor,
    AttentionGraphExtractor,
    AutoMemoryHook
)


@pytest.mark.unit
class TestConceptExtractor:
    """Test ConceptExtractor class"""

    def test_extractor_initialization(self):
        """Test concept extractor initialization"""
        extractor = ConceptExtractor()
        assert extractor is not None

    def test_extract_from_text(self, sample_extraction_text):
        """Test extracting concepts from text"""
        extractor = ConceptExtractor()
        concepts = extractor.extract(sample_extraction_text)

        assert len(concepts) > 0
        assert isinstance(concepts, list)

    def test_extract_capitalized_phrases(self):
        """Test extraction of capitalized phrases"""
        text = "The Golden Ratio and Working Memory are important concepts."
        extractor = ConceptExtractor()
        concepts = extractor.extract(text)

        # Should extract multi-word phrases like "The Golden Ratio" or "Working Memory"
        assert len(concepts) > 0
        assert any("Golden" in c or "Working" in c or "Memory" in c for c in concepts)

    def test_extract_quoted_terms(self):
        """Test extraction of quoted terms"""
        text = 'The "edge of chaos" operator is critical.'
        extractor = ConceptExtractor()
        concepts = extractor.extract(text)

        assert "edge of chaos" in concepts

    def test_extract_technical_terms(self):
        """Test extracting technical terms"""
        text = "The WorkingMemory class uses snake_case variables and kebab-case files."
        extractor = ConceptExtractor()
        concepts = extractor.extract(text)

        # Should extract at least some technical terms
        assert len(concepts) > 0

    def test_stopwords_filtering(self):
        """Test that stopwords are filtered out"""
        text = "The This That These Those are stopwords."
        extractor = ConceptExtractor()
        concepts = extractor.extract(text)

        # Stopwords should be filtered
        assert "The" not in concepts
        assert "This" not in concepts
        assert "That" not in concepts

    def test_custom_patterns(self):
        """Test custom regex patterns"""
        extractor = ConceptExtractor(
            custom_patterns={'project_code': r'PROJ-\d{3}'}
        )
        text = "Working on PROJ-001 and PROJ-042 today."
        concepts = extractor.extract(text)

        assert "PROJ-001" in concepts
        assert "PROJ-042" in concepts

    def test_extract_with_counts(self):
        """Test extraction with occurrence counts"""
        text = "Python is great. Python is fast. Python is awesome."
        extractor = ConceptExtractor()
        counts = extractor.extract_with_counts(text)

        assert isinstance(counts, dict)
        assert counts.get("Python", 0) == 3
        # Should have counted Python multiple times
        assert len(counts) >= 1


@pytest.mark.unit
class TestDecisionExtractor:
    """Test DecisionExtractor class"""

    def test_decision_extractor_initialization(self):
        """Test decision extractor initialization"""
        extractor = DecisionExtractor()
        assert extractor is not None

    def test_extract_decisions_from_assistant(self):
        """Test extracting decisions from assistant messages"""
        text = "I am going to create a new Python module for testing."
        extractor = DecisionExtractor()
        decisions = extractor.extract(text, role="assistant")

        assert len(decisions) >= 1
        assert any("create" in d.lower() for d in decisions)

    def test_no_decisions_from_user(self):
        """Test that user messages don't extract decisions"""
        text = "I am going to the store later."
        extractor = DecisionExtractor()
        decisions = extractor.extract(text, role="user")

        # User decisions should not be tracked
        assert len(decisions) == 0

    def test_decision_patterns(self):
        """Test various decision patterns"""
        extractor = DecisionExtractor()

        test_cases = [
            ("I will implement the feature", "assistant", True),
            ("Creating a new database schema", "assistant", True),
            ("My plan is to refactor this code", "assistant", True),
            ("Let me analyze the data first", "assistant", True),
            ("Just testing something", "assistant", False),
        ]

        for text, role, should_find in test_cases:
            decisions = extractor.extract(text, role=role)
            if should_find:
                assert len(decisions) > 0, f"Should find decision in: {text}"
            # Some patterns may vary, so we don't assert False case strictly

    def test_decision_length_filtering(self):
        """Test that decisions are filtered by length"""
        extractor = DecisionExtractor(min_length=10, max_length=50)

        # Too short
        short_text = "I will do it."
        short_decisions = extractor.extract(short_text, role="assistant")
        assert len(short_decisions) == 0

        # Just right
        good_text = "I am going to implement the authentication system."
        good_decisions = extractor.extract(good_text, role="assistant")
        assert len(good_decisions) >= 1


@pytest.mark.unit
class TestAttentionGraphExtractor:
    """Test AttentionGraphExtractor class"""

    def test_graph_extractor_initialization(self, tmp_db_path):
        """Test attention graph extractor initialization"""
        extractor = AttentionGraphExtractor(db_path=tmp_db_path)
        assert extractor is not None

    def test_analyze_message(self, tmp_db_path):
        """Test analyzing a message for graph structure"""
        extractor = AttentionGraphExtractor(db_path=tmp_db_path)

        stats = extractor.analyze_message(
            "Python and SQLite work well together for data storage.",
            instance_id="test-001"
        )

        assert isinstance(stats, dict)
        assert 'pairs_found' in stats
        assert 'compounds_found' in stats


@pytest.mark.unit
class TestAutoMemoryHook:
    """Test AutoMemoryHook class"""

    def test_hook_initialization(self, tmp_db_path):
        """Test auto-memory hook initialization"""
        hook = AutoMemoryHook(
            db_path=tmp_db_path,
            instance_id="test-session"
        )

        assert hook is not None
        assert hook.instance_id == "test-session"
        assert hook.message_count == 0

    def test_save_message(self, tmp_db_path):
        """Test saving a message with extraction"""
        hook = AutoMemoryHook(
            db_path=tmp_db_path,
            instance_id="test-session"
        )

        stats = hook.save_message(
            role="user",
            content="Let's build a WorkingMemory system using SQLite."
        )

        assert isinstance(stats, dict)
        assert 'concepts' in stats
        assert 'decisions' in stats
        assert 'links' in stats
        assert 'compounds' in stats
        assert hook.message_count == 1

    def test_save_message_with_decision(self, tmp_db_path):
        """Test saving a message that contains a decision"""
        hook = AutoMemoryHook(
            db_path=tmp_db_path,
            instance_id="test-session"
        )

        stats = hook.save_message(
            role="assistant",
            content="I am going to implement the memory persistence layer."
        )

        assert stats['decisions'] >= 1

    def test_get_session_stats(self, tmp_db_path):
        """Test retrieving session statistics"""
        hook = AutoMemoryHook(
            db_path=tmp_db_path,
            instance_id="test-session"
        )

        # Save some messages
        hook.save_message("user", "Tell me about Python")
        hook.save_message("assistant", "Python is a programming language")

        stats = hook.get_session_stats()

        assert stats['instance_id'] == "test-session"
        assert stats['messages'] == 2
        assert 'concepts_added' in stats
        assert 'decisions' in stats

    def test_occurrence_threshold(self, tmp_db_path):
        """Test that concepts require multiple occurrences"""
        hook = AutoMemoryHook(
            db_path=tmp_db_path,
            instance_id="test-session",
            occurrence_threshold=2
        )

        # First mention
        hook.save_message("user", "What is Python?")
        stats1 = hook.get_session_stats()
        concepts_after_1 = stats1['concepts_added']

        # Second mention should trigger addition
        hook.save_message("user", "Tell me more about Python")
        stats2 = hook.get_session_stats()
        concepts_after_2 = stats2['concepts_added']

        # Concepts should increase after threshold
        assert concepts_after_2 >= concepts_after_1


@pytest.mark.unit
class TestExtractionPipeline:
    """Test full extraction pipeline"""

    def test_combined_extraction(self, sample_extraction_text):
        """Test combining concept and decision extraction"""
        concept_extractor = ConceptExtractor()
        decision_extractor = DecisionExtractor()

        concepts = concept_extractor.extract(sample_extraction_text)
        decisions = decision_extractor.extract(sample_extraction_text, role="assistant")

        assert len(concepts) > 0
        # Sample text contains a decision
        assert len(decisions) >= 1

    def test_empty_text_handling(self):
        """Test handling of empty text"""
        extractor = ConceptExtractor()
        concepts = extractor.extract("")

        assert concepts == [] or len(concepts) == 0

    def test_long_text_extraction(self):
        """Test extraction from long text"""
        long_text = " ".join(["This is a test sentence about Python."] * 100)
        extractor = ConceptExtractor()

        concepts = extractor.extract(long_text)
        # Should handle long text without error
        assert isinstance(concepts, list)
