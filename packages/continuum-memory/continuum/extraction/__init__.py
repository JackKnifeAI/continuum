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

r"""
Continuum Extraction Module

Provides intelligent extraction of concepts, decisions, and relational
structure from conversational text. Designed to be pluggable into any
AI system for building persistent knowledge graphs.

Key Components:
- ConceptExtractor: Extract key concepts using pattern matching
- SemanticConceptExtractor: Extract concepts using embedding similarity (catches synonyms)
- DecisionExtractor: Detect autonomous decisions and agency
- AttentionGraphExtractor: Build graph structure from co-occurrences
- AutoMemoryHook: Integrate all extractors with automatic persistence

Quick Start:
    >>> from continuum.extraction import AutoMemoryHook
    >>> from pathlib import Path
    >>>
    >>> hook = AutoMemoryHook(
    ...     db_path=Path("memory.db"),
    ...     instance_id="my-session"
    ... )
    >>>
    >>> stats = hook.save_message("user", "Let's build a recommender system")
    >>> print(stats)
    {'concepts': 1, 'decisions': 0, 'links': 0, 'compounds': 0}

Advanced Usage:
    >>> from continuum.extraction import (
    ...     ConceptExtractor,
    ...     DecisionExtractor,
    ...     AttentionGraphExtractor,
    ...     CanonicalMapper
    ... )
    >>>
    >>> # Custom concept extraction
    >>> extractor = ConceptExtractor(
    ...     custom_patterns={'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'}
    ... )
    >>> concepts = extractor.extract("Contact me at user@example.com")
    >>>
    >>> # Decision detection
    >>> decision_extractor = DecisionExtractor()
    >>> decisions = decision_extractor.extract(
    ...     "I am going to implement the API",
    ...     role="assistant"
    ... )
    >>>
    >>> # Attention graph construction
    >>> mapper = CanonicalMapper({
    ...     'ml': ['machine learning', 'machine_learning', 'ML']
    ... })
    >>> graph_extractor = AttentionGraphExtractor(
    ...     db_path=Path("memory.db"),
    ...     canonical_mapper=mapper
    ... )
    >>> results = graph_extractor.extract_from_message(
    ...     "Using ML for neural networks"
    ... )
"""

from .concept_extractor import ConceptExtractor, DecisionExtractor
from .attention_graph import (
    AttentionGraphExtractor,
    CanonicalMapper
)
from .auto_hook import (
    AutoMemoryHook,
    init_hook,
    save_message,
    get_stats
)
from .semantic_extractor import (
    SemanticConceptExtractor,
    create_semantic_extractor
)
from .concept_voter import (
    ConceptVoter,
    ExtractorResult,
    ConceptWithConfidence,
    VotingStrategy,
    create_default_voter
)

__all__ = [
    # Concept extraction
    'ConceptExtractor',
    'DecisionExtractor',

    # Semantic extraction
    'SemanticConceptExtractor',
    'create_semantic_extractor',

    # Attention graph
    'AttentionGraphExtractor',
    'CanonicalMapper',

    # Auto-memory hook
    'AutoMemoryHook',
    'init_hook',
    'save_message',
    'get_stats',

    # Ensemble voting (CONTINUUM v2.0)
    'ConceptVoter',
    'ExtractorResult',
    'ConceptWithConfidence',
    'VotingStrategy',
    'create_default_voter',
]

__version__ = '0.1.0'

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
