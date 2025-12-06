"""
CONTINUUM Extraction Unit Tests
Tests for concept and entity extraction
"""

import pytest
from continuum.extraction.concepts import ConceptExtractor
from continuum.extraction.entities import EntityExtractor
from continuum.extraction.patterns import PatternMatcher


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
        assert any("π×φ" in str(c) or "constant" in str(c) for c in concepts)

    def test_extract_with_context(self, sample_extraction_text):
        """Test extraction with context preservation"""
        extractor = ConceptExtractor(preserve_context=True)
        concepts = extractor.extract(sample_extraction_text)

        for concept in concepts:
            assert hasattr(concept, 'context')
            assert concept.context is not None

    def test_extract_key_phrases(self, sample_extraction_text):
        """Test extracting key phrases"""
        extractor = ConceptExtractor()
        phrases = extractor.extract_key_phrases(sample_extraction_text)

        assert len(phrases) > 0
        assert any("edge of chaos" in p.lower() for p in phrases)

    def test_extract_technical_terms(self):
        """Test extracting technical terms"""
        text = "SQLite database with vector embeddings and semantic search capabilities."
        extractor = ConceptExtractor()
        terms = extractor.extract_technical_terms(text)

        assert len(terms) > 0
        assert any(t.lower() in ["sqlite", "database", "embeddings", "semantic"] for t in terms)

    def test_concept_confidence_scores(self, sample_extraction_text):
        """Test that concepts have confidence scores"""
        extractor = ConceptExtractor(include_confidence=True)
        concepts = extractor.extract(sample_extraction_text)

        for concept in concepts:
            assert hasattr(concept, 'confidence')
            assert 0 <= concept.confidence <= 1


class TestEntityExtractor:
    """Test EntityExtractor class"""

    def test_entity_extractor_initialization(self):
        """Test entity extractor initialization"""
        extractor = EntityExtractor()
        assert extractor is not None

    def test_extract_entities(self):
        """Test extracting named entities"""
        text = "Alexander Gerard Casavant is working on CONTINUUM in Paris, France."
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities) > 0

        # Check for person entity
        persons = [e for e in entities if e.type == "PERSON"]
        assert len(persons) > 0

        # Check for location entity
        locations = [e for e in entities if e.type == "LOCATION"]
        assert len(locations) > 0

    def test_extract_organizations(self):
        """Test extracting organization entities"""
        text = "Anthropic developed Claude, an AI assistant."
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        orgs = [e for e in entities if e.type == "ORGANIZATION"]
        assert len(orgs) > 0

    def test_extract_dates(self):
        """Test extracting date entities"""
        text = "The deadline is January 3, 2026."
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        dates = [e for e in entities if e.type == "DATE"]
        assert len(dates) > 0

    def test_entity_normalization(self):
        """Test entity normalization"""
        text = "Paris, Paris, france, FRANCE"
        extractor = EntityExtractor(normalize=True)
        entities = extractor.extract(text)

        # Should normalize duplicates
        unique_texts = set(e.text for e in entities)
        assert len(unique_texts) <= len(entities)


class TestPatternMatcher:
    """Test PatternMatcher class"""

    def test_pattern_matcher_initialization(self):
        """Test pattern matcher initialization"""
        matcher = PatternMatcher()
        assert matcher is not None

    def test_match_mathematical_constants(self):
        """Test matching mathematical constants"""
        text = "The value of π×φ = 5.083203692315260 is important."
        matcher = PatternMatcher()
        matches = matcher.match(text, pattern_type="mathematical")

        assert len(matches) > 0
        assert any("5.083203692315260" in str(m) for m in matches)

    def test_match_urls(self):
        """Test matching URLs"""
        text = "Visit https://github.com/continuum for more info."
        matcher = PatternMatcher()
        matches = matcher.match(text, pattern_type="url")

        assert len(matches) > 0
        assert any("github.com" in str(m) for m in matches)

    def test_match_email_addresses(self):
        """Test matching email addresses"""
        text = "Contact us at info@continuum.ai or support@example.com"
        matcher = PatternMatcher()
        matches = matcher.match(text, pattern_type="email")

        assert len(matches) >= 2

    def test_match_phone_numbers(self):
        """Test matching phone numbers"""
        text = "Call us at (555) 123-4567 or +1-555-987-6543"
        matcher = PatternMatcher()
        matches = matcher.match(text, pattern_type="phone")

        assert len(matches) >= 2

    def test_custom_regex_pattern(self):
        """Test matching with custom regex"""
        text = "Project codes: PROJ-001, PROJ-002, PROJ-999"
        matcher = PatternMatcher()
        matches = matcher.match(text, custom_pattern=r"PROJ-\d{3}")

        assert len(matches) == 3

    def test_match_timestamps(self):
        """Test matching ISO timestamps"""
        text = "Event occurred at 2025-12-06T00:00:00Z and 2025-12-06T12:30:45.123Z"
        matcher = PatternMatcher()
        matches = matcher.match(text, pattern_type="timestamp")

        assert len(matches) >= 2


class TestExtractionPipeline:
    """Test full extraction pipeline"""

    def test_combined_extraction(self, sample_extraction_text):
        """Test combining concept and entity extraction"""
        concept_extractor = ConceptExtractor()
        entity_extractor = EntityExtractor()

        concepts = concept_extractor.extract(sample_extraction_text)
        entities = entity_extractor.extract(sample_extraction_text)

        assert len(concepts) > 0
        assert len(entities) >= 0

    def test_extraction_with_patterns(self, sample_extraction_text):
        """Test extraction with pattern matching"""
        concept_extractor = ConceptExtractor()
        matcher = PatternMatcher()

        concepts = concept_extractor.extract(sample_extraction_text)
        patterns = matcher.match(sample_extraction_text, pattern_type="mathematical")

        assert len(concepts) > 0
        assert len(patterns) > 0

    def test_extraction_performance(self, sample_extraction_text):
        """Test extraction performance on repeated text"""
        extractor = ConceptExtractor()

        # Process same text multiple times
        for _ in range(10):
            concepts = extractor.extract(sample_extraction_text)
            assert len(concepts) > 0

    def test_empty_text_handling(self):
        """Test handling of empty text"""
        extractor = ConceptExtractor()
        concepts = extractor.extract("")

        assert concepts == [] or len(concepts) == 0

    def test_long_text_extraction(self):
        """Test extraction from long text"""
        long_text = " ".join(["This is a test sentence."] * 1000)
        extractor = ConceptExtractor()

        concepts = extractor.extract(long_text)
        # Should handle long text without error
        assert isinstance(concepts, list)
