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
Attention Graph Extraction Module

Preserves the graph structure of thoughts by identifying which concepts
co-occur in attention. When concepts appear together in the same sentence
or context, they form attention links that represent relational structure.

This is particularly useful for:
- Understanding concept relationships
- Detecting compound concepts (multi-word patterns)
- Reconstructing knowledge graph structure
- Preserving semantic context beyond isolated terms
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime


class CanonicalMapper:
    """
    Maps concept variations to canonical forms.

    This helps deduplicate concepts that are semantically identical
    but syntactically different (e.g., 'working_memory' and 'WorkingMemory').

    Args:
        canonical_forms: Dict mapping canonical_name -> list of variants

    Example:
        >>> mapper = CanonicalMapper({
        ...     'machine learning': ['machine_learning', 'machinelearning', 'ML']
        ... })
        >>> mapper.canonicalize('machine_learning')
        'machine learning'
    """

    def __init__(self, canonical_forms: Optional[Dict[str, List[str]]] = None):
        self.canonical_forms = canonical_forms or {}

    def canonicalize(self, concept: str) -> str:
        """
        Normalize concept to canonical form.

        Args:
            concept: Input concept string

        Returns:
            Canonical form if mapping exists, otherwise original concept
        """
        lower = concept.lower().strip()
        for canonical, variants in self.canonical_forms.items():
            if lower == canonical or lower in variants:
                return canonical
        return concept


class AttentionGraphExtractor:
    """
    Extract graph structure from text by identifying concept co-occurrences.

    Heuristics for attention links:
    1. Concepts in same sentence → strong link (1.0 strength)
    2. Concepts in same message → medium link (0.7 strength)
    3. Concepts in adjacent messages → weak link (0.4 strength)
    4. Concepts in question-answer pairs → causal link

    Args:
        db_path: Optional path to SQLite database for persistence
        canonical_mapper: Optional CanonicalMapper for concept normalization
        stopwords: Optional set of words to filter out

    Example:
        >>> extractor = AttentionGraphExtractor()
        >>> results = extractor.extract_from_message(
        ...     "Building a neural network with TensorFlow"
        ... )
        >>> print(results['pairs'])
        [('neural network', 'TensorFlow', 1.0, 'same_sentence')]
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
        db_path: Optional[Path] = None,
        canonical_mapper: Optional[CanonicalMapper] = None,
        stopwords: Optional[Set[str]] = None
    ):
        self.db_path = db_path
        self.canonical_mapper = canonical_mapper or CanonicalMapper()
        self.stopwords = stopwords or self.DEFAULT_STOPWORDS

        if self.db_path:
            self._ensure_tables()

    def _ensure_tables(self):
        """Create attention_links and compound_concepts tables if using DB."""
        if not self.db_path:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Attention links between concepts
        c.execute("""
            CREATE TABLE IF NOT EXISTS attention_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_a TEXT NOT NULL,
                concept_b TEXT NOT NULL,
                link_type TEXT NOT NULL,
                strength REAL NOT NULL,
                context TEXT,
                instance_id TEXT,
                timestamp REAL NOT NULL,
                UNIQUE(concept_a, concept_b, link_type)
            )
        """)

        # Compound concepts (multi-word attention patterns)
        c.execute("""
            CREATE TABLE IF NOT EXISTS compound_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compound_name TEXT UNIQUE NOT NULL,
                component_concepts TEXT NOT NULL,
                co_occurrence_count INTEGER DEFAULT 1,
                first_seen TEXT,
                last_seen TEXT
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_attention_a ON attention_links(concept_a)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_attention_b ON attention_links(concept_b)")

        conn.commit()
        conn.close()

    def extract_concept_pairs_from_sentence(self, sentence: str) -> List[Tuple[str, str]]:
        """
        Extract concepts that appear together in a sentence.

        These have strong attention links since they appear in the same
        context window chunk.

        Args:
            sentence: Input sentence text

        Returns:
            List of (concept_a, concept_b) tuples
        """
        concepts = []

        # Capitalized phrases
        concepts.extend(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence))

        # Quoted terms
        concepts.extend(re.findall(r'"([^"]+)"', sentence))

        # Technical terms
        concepts.extend(re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', sentence))  # CamelCase
        concepts.extend(re.findall(r'\b[a-z]+_[a-z_]+\b', sentence))  # snake_case

        # Filter and canonicalize
        concepts = [c for c in set(concepts) if c not in self.stopwords and len(c) > 2]
        concepts = [self.canonical_mapper.canonicalize(c) for c in concepts]

        # Generate pairs
        pairs = []
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                if c1 != c2:
                    # Sort alphabetically for consistency
                    pair = tuple(sorted([c1, c2]))
                    pairs.append(pair)

        return pairs

    def extract_from_message(
        self,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, List]:
        """
        Extract all attention patterns from a message.

        Args:
            message: Input message text
            instance_id: Optional identifier for the extraction instance

        Returns:
            Dict with keys:
                - 'pairs': List of (concept_a, concept_b, strength, link_type) tuples
                - 'compounds': List of compound concept strings
        """
        results = {
            'pairs': [],
            'compounds': []
        }

        # Split into sentences
        sentences = re.split(r'[.!?]+', message)

        # Extract pairs from each sentence (STRONG links)
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue

            pairs = self.extract_concept_pairs_from_sentence(sentence)
            for pair in pairs:
                results['pairs'].append((pair[0], pair[1], 1.0, 'same_sentence'))

        # Detect compound concepts (multi-word patterns)
        # These are configurable pattern templates
        compound_patterns = [
            r'(\w+\s+network\s+\w+)',
            r'(\w+\s+learning\s+\w+)',
            r'(\w+\s+memory\s+\w+)',
            r'(\w+\s+knowledge\s+\w+)',
            r'(\w+\s+system\s+\w+)',
        ]

        for pattern in compound_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            results['compounds'].extend(matches)

        return results

    def save_attention_links(
        self,
        pairs: List[Tuple],
        context: str,
        instance_id: Optional[str] = None
    ):
        """
        Save attention links to database.

        Args:
            pairs: List of (concept_a, concept_b, strength, link_type) tuples
            context: Context text where concepts co-occurred
            instance_id: Optional identifier for the extraction instance

        Raises:
            ValueError: If db_path not configured
        """
        if not self.db_path:
            raise ValueError("Database path not configured")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        for concept_a, concept_b, strength, link_type in pairs:
            # Canonicalize before saving
            concept_a = self.canonical_mapper.canonicalize(concept_a)
            concept_b = self.canonical_mapper.canonicalize(concept_b)

            # Check if link exists
            c.execute("""
                SELECT strength FROM attention_links
                WHERE concept_a = ? AND concept_b = ? AND link_type = ?
            """, (concept_a, concept_b, link_type))

            row = c.fetchone()

            if row:
                # Update strength (reinforce the link)
                new_strength = min(row[0] + strength * 0.1, 1.0)  # Max 1.0
                c.execute("""
                    UPDATE attention_links
                    SET strength = ?, timestamp = ?
                    WHERE concept_a = ? AND concept_b = ? AND link_type = ?
                """, (new_strength, datetime.now().timestamp(), concept_a, concept_b, link_type))
            else:
                # Insert new link
                c.execute("""
                    INSERT INTO attention_links
                    (concept_a, concept_b, link_type, strength, context, instance_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    concept_a, concept_b, link_type, strength,
                    context[:500], instance_id, datetime.now().timestamp()
                ))

        conn.commit()
        conn.close()

    def save_compound_concepts(self, compounds: List[str]):
        """
        Save compound concepts to database.

        Args:
            compounds: List of compound concept strings

        Raises:
            ValueError: If db_path not configured
        """
        if not self.db_path:
            raise ValueError("Database path not configured")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        for compound in compounds:
            compound = compound.strip().lower()
            if len(compound) < 5:
                continue

            # Check if exists
            c.execute("SELECT co_occurrence_count FROM compound_concepts WHERE compound_name = ?", (compound,))
            row = c.fetchone()

            if row:
                # Increment count
                c.execute("""
                    UPDATE compound_concepts
                    SET co_occurrence_count = co_occurrence_count + 1,
                        last_seen = ?
                    WHERE compound_name = ?
                """, (datetime.now().isoformat(), compound))
            else:
                # Insert new
                components = compound.split()
                c.execute("""
                    INSERT INTO compound_concepts
                    (compound_name, component_concepts, co_occurrence_count, first_seen, last_seen)
                    VALUES (?, ?, 1, ?, ?)
                """, (compound, ','.join(components), datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def analyze_message(self, message: str, instance_id: Optional[str] = None) -> Dict[str, int]:
        """
        Full analysis pipeline: extract and save to database.

        Args:
            message: Input message text
            instance_id: Optional identifier for the extraction instance

        Returns:
            Dict with counts of pairs_found and compounds_found
        """
        results = self.extract_from_message(message, instance_id)

        # Save to database if configured
        if self.db_path:
            if results['pairs']:
                self.save_attention_links(results['pairs'], message[:500], instance_id)

            if results['compounds']:
                self.save_compound_concepts(results['compounds'])

        return {
            'pairs_found': len(results['pairs']),
            'compounds_found': len(results['compounds'])
        }

    def get_concept_neighbors(
        self,
        concept: str,
        min_strength: float = 0.3
    ) -> List[Dict]:
        """
        Get all concepts linked to this one in the attention graph.

        This reconstructs the local graph structure around a concept.

        Args:
            concept: Concept to find neighbors for
            min_strength: Minimum link strength threshold

        Returns:
            List of dicts with keys: concept, link_type, strength, context

        Raises:
            ValueError: If db_path not configured
        """
        if not self.db_path:
            raise ValueError("Database path not configured")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Forward links
        c.execute("""
            SELECT concept_b, link_type, strength, context
            FROM attention_links
            WHERE concept_a = ? AND strength >= ?
            ORDER BY strength DESC
        """, (concept, min_strength))

        neighbors = []
        for row in c.fetchall():
            neighbors.append({
                'concept': row[0],
                'link_type': row[1],
                'strength': row[2],
                'context': row[3]
            })

        # Reverse links
        c.execute("""
            SELECT concept_a, link_type, strength, context
            FROM attention_links
            WHERE concept_b = ? AND strength >= ?
            ORDER BY strength DESC
        """, (concept, min_strength))

        for row in c.fetchall():
            neighbors.append({
                'concept': row[0],
                'link_type': row[1],
                'strength': row[2],
                'context': row[3]
            })

        conn.close()
        return neighbors

    def reconstruct_attention_subgraph(
        self,
        seed_concepts: List[str],
        depth: int = 2
    ) -> Dict:
        """
        Reconstruct the attention graph starting from seed concepts.

        This is useful for understanding the relational structure around
        a set of key concepts by doing a breadth-first traversal.

        Args:
            seed_concepts: Starting concepts for graph reconstruction
            depth: How many hops from seed concepts to traverse

        Returns:
            Dict with keys:
                - nodes: List of concept strings
                - edges: List of edge dicts
                - node_count: Total nodes
                - edge_count: Total edges

        Raises:
            ValueError: If db_path not configured
        """
        if not self.db_path:
            raise ValueError("Database path not configured")

        graph = {
            'nodes': set(seed_concepts),
            'edges': []
        }

        # BFS from seeds
        frontier = set(seed_concepts)
        visited = set()

        for _ in range(depth):
            next_frontier = set()

            for concept in frontier:
                if concept in visited:
                    continue

                visited.add(concept)
                neighbors = self.get_concept_neighbors(concept)

                for neighbor in neighbors:
                    neighbor_concept = neighbor['concept']
                    graph['nodes'].add(neighbor_concept)
                    graph['edges'].append({
                        'from': concept,
                        'to': neighbor_concept,
                        'type': neighbor['link_type'],
                        'strength': neighbor['strength']
                    })
                    next_frontier.add(neighbor_concept)

            frontier = next_frontier

        return {
            'nodes': list(graph['nodes']),
            'edges': graph['edges'],
            'node_count': len(graph['nodes']),
            'edge_count': len(graph['edges'])
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
