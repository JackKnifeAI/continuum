r"""
Continuum Extraction Module

Provides intelligent extraction of concepts, decisions, and relational
structure from conversational text. Designed to be pluggable into any
AI system for building persistent knowledge graphs.

Key Components:
- ConceptExtractor: Extract key concepts using pattern matching
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

__all__ = [
    # Concept extraction
    'ConceptExtractor',
    'DecisionExtractor',

    # Attention graph
    'AttentionGraphExtractor',
    'CanonicalMapper',

    # Auto-memory hook
    'AutoMemoryHook',
    'init_hook',
    'save_message',
    'get_stats',
]

__version__ = '0.1.0'
