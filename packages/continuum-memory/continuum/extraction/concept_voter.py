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
Concept Voter - Ensemble Extraction System

Combines results from multiple extractors (regex, semantic, LLM) using
configurable voting strategies to achieve higher accuracy and confidence
in concept identification.

Key features:
- Multiple voting strategies (UNION, INTERSECTION, WEIGHTED)
- Confidence scoring based on extractor agreement
- Configurable extractor weights
- Extraction quality metrics
- Graceful degradation (works with any subset of extractors)

This implements the ensemble approach for CONTINUUM v2.0 to improve
extraction accuracy beyond single-extractor methods.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import time


class VotingStrategy(Enum):
    """
    Voting strategies for combining extractor results.

    UNION: Include concept if ANY extractor found it (high recall)
    INTERSECTION: Include only if MULTIPLE extractors agree (high precision)
    WEIGHTED: Weight-based voting with configurable threshold (balanced)
    """
    UNION = "union"
    INTERSECTION = "intersection"
    WEIGHTED = "weighted"


@dataclass
class ExtractorResult:
    """
    Result from a single extractor.

    Attributes:
        concepts: List of concept strings extracted
        source: Extractor identifier (regex/semantic/llm)
        extraction_time_ms: Time taken for extraction in milliseconds
        metadata: Optional metadata about extraction (confidence scores, etc.)
    """
    concepts: List[str]
    source: str
    extraction_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


@dataclass
class ConceptWithConfidence:
    """
    Concept with confidence score from voting.

    Attributes:
        concept: Concept string
        confidence: Confidence score [0.0, 1.0]
        sources: List of extractors that found this concept
        agreement_count: Number of extractors that agreed
    """
    concept: str
    confidence: float
    sources: List[str]
    agreement_count: int


class ConceptVoter:
    """
    Ensemble voting system for concept extraction.

    Combines results from multiple extractors using configurable voting
    strategies and weights. Provides confidence scores for extracted concepts
    based on extractor agreement.

    Args:
        strategy: Voting strategy to use (default: WEIGHTED)
        extractor_weights: Dict mapping source name to weight
            Default: regex=0.3, semantic=0.5, llm=0.8
        confidence_threshold: Minimum confidence for inclusion (WEIGHTED mode)
            Default: 0.4
        min_agreement_count: Minimum extractors needed (INTERSECTION mode)
            Default: 2

    Example:
        >>> voter = ConceptVoter(
        ...     strategy=VotingStrategy.WEIGHTED,
        ...     extractor_weights={'regex': 0.3, 'semantic': 0.5, 'llm': 0.8}
        ... )
        >>>
        >>> results = [
        ...     ExtractorResult(['neural network'], 'regex', 2.5),
        ...     ExtractorResult(['neural network', 'TensorFlow'], 'llm', 150.0)
        ... ]
        >>>
        >>> concepts = voter.vote(results)
        >>> print(concepts[0].concept, concepts[0].confidence)
        'neural network' 0.55
    """

    DEFAULT_WEIGHTS = {
        'regex': 0.3,
        'semantic': 0.5,
        'llm': 0.8
    }

    def __init__(
        self,
        strategy: VotingStrategy = VotingStrategy.WEIGHTED,
        extractor_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: float = 0.4,
        min_agreement_count: int = 2
    ):
        self.strategy = strategy
        self.extractor_weights = extractor_weights or self.DEFAULT_WEIGHTS.copy()
        self.confidence_threshold = confidence_threshold
        self.min_agreement_count = min_agreement_count

        # Metrics tracking
        self._total_extractions = 0
        self._strategy_stats: Dict[str, int] = {}
        self._extractor_contribution: Dict[str, int] = {}

    def vote(self, results: List[ExtractorResult]) -> List[ConceptWithConfidence]:
        """
        Vote on concepts from multiple extractors.

        Combines results using the configured voting strategy and returns
        concepts with confidence scores.

        Args:
            results: List of ExtractorResult objects from different extractors

        Returns:
            List of ConceptWithConfidence objects, sorted by confidence (descending)
        """
        if not results:
            return []

        self._total_extractions += 1

        # Build concept -> sources mapping
        concept_sources: Dict[str, List[str]] = {}

        for result in results:
            for concept in result.concepts:
                if concept not in concept_sources:
                    concept_sources[concept] = []
                concept_sources[concept].append(result.source)

        # Apply voting strategy
        if self.strategy == VotingStrategy.UNION:
            voted_concepts = self._vote_union(concept_sources)
        elif self.strategy == VotingStrategy.INTERSECTION:
            voted_concepts = self._vote_intersection(concept_sources)
        elif self.strategy == VotingStrategy.WEIGHTED:
            voted_concepts = self._vote_weighted(concept_sources)
        else:
            raise ValueError(f"Unknown voting strategy: {self.strategy}")

        # Update metrics
        strategy_key = self.strategy.value
        self._strategy_stats[strategy_key] = self._strategy_stats.get(strategy_key, 0) + 1

        for concept in voted_concepts:
            for source in concept.sources:
                self._extractor_contribution[source] = (
                    self._extractor_contribution.get(source, 0) + 1
                )

        # Sort by confidence (descending)
        voted_concepts.sort(key=lambda c: c.confidence, reverse=True)

        return voted_concepts

    def _vote_union(
        self,
        concept_sources: Dict[str, List[str]]
    ) -> List[ConceptWithConfidence]:
        """
        UNION strategy: Include if ANY extractor found it.

        Confidence = weight of strongest extractor / max possible weight
        """
        concepts = []
        max_weight = max(self.extractor_weights.values()) if self.extractor_weights else 1.0

        for concept, sources in concept_sources.items():
            # Find highest weight among sources
            max_source_weight = max(
                self.extractor_weights.get(source, 0.5) for source in sources
            )

            confidence = max_source_weight / max_weight

            concepts.append(ConceptWithConfidence(
                concept=concept,
                confidence=confidence,
                sources=sources,
                agreement_count=len(sources)
            ))

        return concepts

    def _vote_intersection(
        self,
        concept_sources: Dict[str, List[str]]
    ) -> List[ConceptWithConfidence]:
        """
        INTERSECTION strategy: Include only if multiple extractors agree.

        Confidence = agreement_count / total_extractors
        """
        concepts = []

        for concept, sources in concept_sources.items():
            agreement_count = len(sources)

            # Only include if meets minimum agreement threshold
            if agreement_count < self.min_agreement_count:
                continue

            # Confidence based on agreement ratio
            # (More extractors agreeing = higher confidence)
            total_possible = len(self.extractor_weights)
            confidence = agreement_count / total_possible if total_possible > 0 else 1.0

            concepts.append(ConceptWithConfidence(
                concept=concept,
                confidence=confidence,
                sources=sources,
                agreement_count=agreement_count
            ))

        return concepts

    def _vote_weighted(
        self,
        concept_sources: Dict[str, List[str]]
    ) -> List[ConceptWithConfidence]:
        """
        WEIGHTED strategy: Sum extractor weights, threshold for inclusion.

        Confidence = sum(weights of extractors that found it) / sum(all weights)
        Only include if confidence >= threshold
        """
        concepts = []
        total_weight = sum(self.extractor_weights.values())

        if total_weight == 0:
            # Fallback to equal weighting
            total_weight = len(self.extractor_weights)

        for concept, sources in concept_sources.items():
            # Sum weights of extractors that found this concept
            weight_sum = sum(
                self.extractor_weights.get(source, 0.5) for source in sources
            )

            confidence = weight_sum / total_weight

            # Apply threshold
            if confidence < self.confidence_threshold:
                continue

            concepts.append(ConceptWithConfidence(
                concept=concept,
                confidence=confidence,
                sources=sources,
                agreement_count=len(sources)
            ))

        return concepts

    def vote_from_text(
        self,
        text: str,
        extractors: Dict[str, callable]
    ) -> Tuple[List[ConceptWithConfidence], Dict[str, float]]:
        """
        Convenience method: Run extractors and vote in one call.

        Args:
            text: Input text to extract concepts from
            extractors: Dict mapping source_name -> extractor_function
                Each function should take text and return List[str]

        Returns:
            Tuple of (voted_concepts, extraction_times)
                voted_concepts: List of ConceptWithConfidence objects
                extraction_times: Dict mapping source -> time_ms
        """
        results = []
        extraction_times = {}

        for source, extractor_fn in extractors.items():
            start_time = time.time()

            try:
                concepts = extractor_fn(text)
                elapsed_ms = (time.time() - start_time) * 1000

                results.append(ExtractorResult(
                    concepts=concepts,
                    source=source,
                    extraction_time_ms=elapsed_ms
                ))

                extraction_times[source] = elapsed_ms

            except Exception as e:
                # Log error but continue with other extractors
                extraction_times[source] = -1  # Error indicator
                continue

        voted_concepts = self.vote(results)

        return voted_concepts, extraction_times

    def get_metrics(self) -> Dict:
        """
        Get extraction quality metrics.

        Returns:
            Dict with keys:
                - total_extractions: Total number of vote() calls
                - strategy_usage: Dict of strategy -> count
                - extractor_contributions: Dict of source -> concept count
                - avg_concepts_per_extraction: Average concepts per vote
        """
        total_concepts = sum(self._extractor_contribution.values())

        return {
            'total_extractions': self._total_extractions,
            'strategy_usage': self._strategy_stats.copy(),
            'extractor_contributions': self._extractor_contribution.copy(),
            'avg_concepts_per_extraction': (
                total_concepts / self._total_extractions
                if self._total_extractions > 0 else 0
            )
        }

    def reset_metrics(self):
        """Reset all metrics counters."""
        self._total_extractions = 0
        self._strategy_stats.clear()
        self._extractor_contribution.clear()

    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update extractor weights dynamically.

        Useful for adaptive weighting based on performance feedback.

        Args:
            new_weights: Dict mapping source -> new weight
        """
        self.extractor_weights.update(new_weights)

    def log_extraction_quality(
        self,
        concepts: List[ConceptWithConfidence]
    ) -> Dict:
        """
        Analyze quality metrics for a voted extraction.

        Args:
            concepts: List of concepts from vote()

        Returns:
            Dict with quality metrics:
                - total_concepts: Number of concepts extracted
                - high_confidence_count: Concepts with confidence >= 0.7
                - medium_confidence_count: Concepts with 0.4 <= confidence < 0.7
                - low_confidence_count: Concepts with confidence < 0.4
                - avg_confidence: Mean confidence score
                - avg_agreement: Mean agreement count
                - source_distribution: Dict of source -> contribution count
        """
        if not concepts:
            return {
                'total_concepts': 0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'avg_confidence': 0.0,
                'avg_agreement': 0.0,
                'source_distribution': {}
            }

        high_conf = sum(1 for c in concepts if c.confidence >= 0.7)
        med_conf = sum(1 for c in concepts if 0.4 <= c.confidence < 0.7)
        low_conf = sum(1 for c in concepts if c.confidence < 0.4)

        avg_conf = sum(c.confidence for c in concepts) / len(concepts)
        avg_agreement = sum(c.agreement_count for c in concepts) / len(concepts)

        # Count source contributions
        source_dist: Dict[str, int] = {}
        for concept in concepts:
            for source in concept.sources:
                source_dist[source] = source_dist.get(source, 0) + 1

        return {
            'total_concepts': len(concepts),
            'high_confidence_count': high_conf,
            'medium_confidence_count': med_conf,
            'low_confidence_count': low_conf,
            'avg_confidence': avg_conf,
            'avg_agreement': avg_agreement,
            'source_distribution': source_dist
        }


def create_default_voter(
    high_precision: bool = False,
    high_recall: bool = False
) -> ConceptVoter:
    """
    Create a ConceptVoter with preset configurations.

    Args:
        high_precision: If True, use INTERSECTION strategy for precision
        high_recall: If True, use UNION strategy for recall

        If both False (default), uses WEIGHTED strategy for balanced approach

    Returns:
        Configured ConceptVoter instance
    """
    if high_precision and high_recall:
        raise ValueError("Cannot optimize for both precision and recall")

    if high_precision:
        return ConceptVoter(
            strategy=VotingStrategy.INTERSECTION,
            min_agreement_count=2
        )
    elif high_recall:
        return ConceptVoter(
            strategy=VotingStrategy.UNION
        )
    else:
        # Balanced default
        return ConceptVoter(
            strategy=VotingStrategy.WEIGHTED,
            confidence_threshold=0.4
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
