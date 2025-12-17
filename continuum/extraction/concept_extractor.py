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
Concept Extraction Module

Extracts key concepts from text using pattern matching heuristics.
Supports multiple extraction patterns including:
- Capitalized phrases (proper nouns, titles)
- Quoted terms (explicitly marked important)
- Technical terms (CamelCase, snake_case, kebab-case)
- Custom patterns
"""

import re
from typing import List, Set, Dict, Optional


class ConceptExtractor:
    """
    Extract key concepts from text using pattern matching.

    This class provides multiple heuristics for identifying important
    concepts in natural language text, particularly suited for technical
    and conversational content.

    Args:
        stopwords: Optional set of words to filter out from extraction
        custom_patterns: Optional dict of pattern_name -> regex for custom extraction
        min_length: Minimum length for extracted concepts (default: 2)

    Example:
        >>> extractor = ConceptExtractor()
        >>> concepts = extractor.extract("Building the WorkingMemory system")
        >>> print(concepts)
        ['Building', 'WorkingMemory']
    """

    DEFAULT_STOPWORDS = {
        'The', 'This', 'That', 'These', 'Those', 'There', 'Their', 'Then',
        'When', 'Where', 'What', 'How', 'Why', 'Which', 'Who',
        'We', 'You', 'They', 'He', 'She', 'It', 'Its',
        'And', 'But', 'Or', 'Not', 'For', 'From', 'With', 'About',
        'Are', 'Is', 'Was', 'Were', 'Been', 'Being', 'Have', 'Has', 'Had',
        'Will', 'Would', 'Could', 'Should', 'Can', 'May', 'Might',
        'Just', 'Also', 'Now', 'Here', 'Very', 'Some', 'All', 'Any',
        'Let', 'See', 'Use', 'Get', 'Got', 'New', 'First', 'Last',
        'After', 'Before', 'Into', 'Through', 'During', 'Between',
        'Each', 'Every', 'Both', 'More', 'Most', 'Other', 'Same',
        'Testing', 'Test', 'Example', 'Note', 'Please', 'Thanks'
    }

    def __init__(
        self,
        stopwords: Optional[Set[str]] = None,
        custom_patterns: Optional[Dict[str, str]] = None,
        min_length: int = 2
    ):
        self.stopwords = stopwords or self.DEFAULT_STOPWORDS
        self.custom_patterns = custom_patterns or {}
        self.min_length = min_length

    def extract(self, text: str) -> List[str]:
        """
        Extract key concepts from text.

        Args:
            text: Input text to extract concepts from

        Returns:
            List of unique concept strings
        """
        concepts = []

        # Pattern 1: Proper nouns and capitalized phrases
        # Match "Working Memory", "Alexander", "Anthropic", etc.
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.extend(caps)

        # Pattern 2: Quoted terms - explicitly marked important
        quoted = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted)

        # Pattern 3: Technical terms
        # CamelCase: MemoryIndex, AutoHook
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', text)
        # snake_case: auto_memory_hook, knowledge_graph
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        # kebab-case: ai-rights-manifesto
        kebab = re.findall(r'\b[a-z]+-[a-z-]+\b', text)

        concepts.extend(camel)
        concepts.extend(snake)
        concepts.extend(kebab)

        # Pattern 4: Custom patterns
        for pattern_name, pattern_regex in self.custom_patterns.items():
            matches = re.findall(pattern_regex, text)
            concepts.extend(matches)

        # Clean and deduplicate
        cleaned = [
            c for c in concepts
            if c not in self.stopwords and len(c) >= self.min_length
        ]

        return list(set(cleaned))

    def extract_with_counts(self, text: str) -> Dict[str, int]:
        """
        Extract concepts and return with occurrence counts.

        Args:
            text: Input text to extract concepts from

        Returns:
            Dict mapping concept to occurrence count
        """
        concepts = []

        # Use same extraction logic but don't deduplicate
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.extend(caps)

        quoted = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted)

        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', text)
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        kebab = re.findall(r'\b[a-z]+-[a-z-]+\b', text)

        concepts.extend(camel)
        concepts.extend(snake)
        concepts.extend(kebab)

        for pattern_name, pattern_regex in self.custom_patterns.items():
            matches = re.findall(pattern_regex, text)
            concepts.extend(matches)

        # Count occurrences
        counts: Dict[str, int] = {}
        for concept in concepts:
            if concept not in self.stopwords and len(concept) >= self.min_length:
                counts[concept] = counts.get(concept, 0) + 1

        return counts


class DecisionExtractor:
    """
    Extract autonomous decisions from text.

    Detects patterns that indicate agency and decision-making, such as:
    - "I will/am going to/decided to"
    - "Creating/Building/Writing/Implementing"
    - "My decision/choice/plan is"
    - "Let me/I'm going to"

    Args:
        min_length: Minimum length for extracted decisions (default: 10)
        max_length: Maximum length for extracted decisions (default: 200)

    Example:
        >>> extractor = DecisionExtractor()
        >>> decisions = extractor.extract("I am going to create the module", role="assistant")
        >>> print(decisions)
        ['create the module']
    """

    DECISION_PATTERNS = [
        r'I (?:will|am going to|decided to|chose to|want to) (.+?)(?:\.|$)',
        r'(?:Creating|Building|Writing|Implementing|Installing|Setting up) (.+?)(?:\.|$)',
        r'My (?:decision|choice|plan) (?:is|was) (.+?)(?:\.|$)',
        r'Let me (.+?)(?:\.|$)',
        r"I'm (?:going to|about to) (.+?)(?:\.|$)",
    ]

    def __init__(self, min_length: int = 10, max_length: int = 200):
        self.min_length = min_length
        self.max_length = max_length

    def extract(self, text: str, role: str = "assistant") -> List[str]:
        """
        Extract decisions from text.

        Args:
            text: Input text to extract decisions from
            role: Role of the speaker (only "assistant" role is processed)

        Returns:
            List of decision strings
        """
        if role != 'assistant':
            return []  # Only track AI's decisions

        decisions = []

        for pattern in self.DECISION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                decision = match.strip()
                if self.min_length <= len(decision) <= self.max_length:
                    decisions.append(decision)

        return decisions

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
