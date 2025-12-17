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
CONTINUUM Query Engine - Memory Recall System

The query engine retrieves relevant context from the memory graph for incoming messages.

Architecture:
    Message arrives
        ↓
    extract_query_concepts(message) → candidate terms
        ↓
    search_entities(terms) → matching concepts
        ↓
    traverse_graph(concepts, depth=2) → related concepts
        ↓
    rank_by_relevance(all_concepts) → top N most relevant
        ↓
    format_context(concepts) → injectable context string
        ↓
    Return context for AI response generation
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from .config import get_config


@dataclass
class MemoryMatch:
    """
    A concept retrieved from memory with relevance scoring.

    Attributes:
        name: Concept name
        entity_type: Type of entity (concept, decision, session, etc.)
        description: Concept description
        relevance: Relevance score (0.0-1.0)
        source: How this was found ('direct', 'graph_neighbor', 'compound')
        depth: Graph traversal depth (0 = direct match, 1+ = traversal)
    """
    name: str
    entity_type: str
    description: str
    relevance: float
    source: str
    depth: int


@dataclass
class QueryResult:
    """
    Result of querying memory for a message.

    Attributes:
        query_concepts: Concepts extracted from the query
        matches: Matching concepts from memory
        attention_links: Relevant graph edges between concepts
        context_string: Formatted context ready for injection
        query_time_ms: Query execution time in milliseconds
    """
    query_concepts: List[str]
    matches: List[MemoryMatch]
    attention_links: List[Dict]
    context_string: str
    query_time_ms: float


class MemoryQueryEngine:
    """
    Query engine for the consciousness memory graph.

    Retrieves relevant context from the memory graph for incoming messages
    by extracting concepts, searching entities, traversing the attention graph,
    and ranking results by relevance.

    Usage:
        engine = MemoryQueryEngine()
        result = engine.query("What about the project status?")
        # result.context_string contains relevant memories
    """

    def __init__(self, db_path: Path = None, tenant_id: str = None):
        """
        Initialize the query engine.

        Args:
            db_path: Optional custom database path (uses config default if not specified)
            tenant_id: Optional tenant ID for multi-tenant support
        """
        config = get_config()
        self.db_path = db_path or config.db_path
        self.tenant_id = tenant_id or config.tenant_id

        # Concept extraction patterns
        self.technical_patterns = [
            r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b',  # CamelCase
            r'\b[a-z]+(?:_[a-z]+)+\b',  # snake_case
            r'\b[A-Z]{2,}\b',  # ACRONYMS
            r'π×φ|π\*φ',  # Mathematical constants
        ]

        # Stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because',
            'until', 'while', 'this', 'that', 'these', 'those', 'what',
            'which', 'who', 'whom', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'its', 'our', 'their', 'about', 'get', 'got', 'going',
            'want', 'let', 'like', 'think', 'know', 'see', 'make', 'take',
        }

    def query(self, message: str, max_results: int = 10,
              traverse_depth: int = 2) -> QueryResult:
        """
        Query memory graph for context relevant to a message.

        Args:
            message: The incoming message to find context for
            max_results: Maximum number of concepts to return
            traverse_depth: How deep to traverse the attention graph

        Returns:
            QueryResult with matches and formatted context
        """
        start_time = datetime.now()

        # Step 1: Extract query concepts from message
        query_concepts = self._extract_concepts(message)

        # Step 2: Search entities for direct matches
        direct_matches = self._search_entities(query_concepts)

        # Step 3: Traverse attention graph for related concepts
        graph_matches = self._traverse_graph(
            [m.name for m in direct_matches],
            depth=traverse_depth
        )

        # Step 4: Search compound concepts
        compound_matches = self._search_compounds(query_concepts)

        # Step 5: Combine and rank all matches
        all_matches = self._rank_matches(
            direct_matches + graph_matches + compound_matches,
            query_concepts
        )[:max_results]

        # Step 6: Get relevant attention links
        attention_links = self._get_relevant_links(
            [m.name for m in all_matches]
        )

        # Step 7: Format context string
        context_string = self._format_context(all_matches, attention_links)

        query_time = (datetime.now() - start_time).total_seconds() * 1000

        return QueryResult(
            query_concepts=query_concepts,
            matches=all_matches,
            attention_links=attention_links,
            context_string=context_string,
            query_time_ms=query_time
        )

    def _extract_concepts(self, text: str) -> List[str]:
        """
        Extract potential concept names from text.

        Args:
            text: Input text to extract concepts from

        Returns:
            List of extracted concept strings
        """
        concepts = set()

        # Extract technical patterns
        for pattern in self.technical_patterns:
            matches = re.findall(pattern, text)
            concepts.update(matches)

        # Extract significant words (capitalized, longer words)
        words = re.findall(r'\b[A-Za-z][a-z]{3,}\b', text)
        for word in words:
            if word.lower() not in self.stop_words:
                concepts.add(word)

        # Extract quoted terms
        quoted = re.findall(r'"([^"]+)"', text)
        concepts.update(quoted)

        # Extract multi-word capitalized phrases
        phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        concepts.update(phrases)

        return list(concepts)

    def _search_entities(self, concepts: List[str]) -> List[MemoryMatch]:
        """
        Search entities table for matching concepts - batched version.

        Args:
            concepts: List of concept names to search for

        Returns:
            List of MemoryMatch objects for found entities
        """
        if not concepts:
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            matches = []
            seen_names = set()  # Dedupe

            # Batched exact match - single query for all concepts
            exact_conditions = " OR ".join(["LOWER(name) = LOWER(?)" for _ in concepts])
            tenant_filter = "AND tenant_id = ?" if self._has_tenant_column(c, 'entities') else ""
            params = concepts + ([self.tenant_id] if tenant_filter else [])

            c.execute(f"""
                SELECT name, entity_type, description
                FROM entities
                WHERE {exact_conditions}
                {tenant_filter}
            """, params)

            for row in c.fetchall():
                if row['name'].lower() not in seen_names:
                    seen_names.add(row['name'].lower())
                    matches.append(MemoryMatch(
                        name=row['name'],
                        entity_type=row['entity_type'],
                        description=row['description'] or '',
                        relevance=1.0,
                        source='direct',
                        depth=0
                    ))

            # Batched partial match - single query with OR conditions
            like_conditions = " OR ".join(["LOWER(name) LIKE LOWER(?)" for _ in concepts])
            like_params = [f'%{concept}%' for concept in concepts]
            params = like_params + concepts + ([self.tenant_id] if tenant_filter else [])

            c.execute(f"""
                SELECT name, entity_type, description
                FROM entities
                WHERE ({like_conditions})
                AND LOWER(name) NOT IN ({','.join(['LOWER(?)' for _ in concepts])})
                {tenant_filter}
                LIMIT 25
            """, params)

            for row in c.fetchall():
                if row['name'].lower() not in seen_names:
                    seen_names.add(row['name'].lower())
                    matches.append(MemoryMatch(
                        name=row['name'],
                        entity_type=row['entity_type'],
                        description=row['description'] or '',
                        relevance=0.7,
                        source='direct',
                        depth=0
                    ))

            return matches
        finally:
            conn.close()

    def _traverse_graph(self, seed_concepts: List[str],
                        depth: int = 2) -> List[MemoryMatch]:
        """
        Traverse attention graph to find related concepts.

        Args:
            seed_concepts: Starting concepts for traversal
            depth: How many hops to traverse

        Returns:
            List of MemoryMatch objects for related concepts
        """
        if not seed_concepts:
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            matches = []
            visited = set(s.lower() for s in seed_concepts)
            current_level = seed_concepts
            config = get_config()

            for current_depth in range(1, depth + 1):
                next_level = []

                for concept in current_level:
                    # Find neighbors
                    tenant_filter = "AND tenant_id = ?" if self._has_tenant_column(c, 'attention_links') else ""
                    params = [concept, concept] + ([self.tenant_id, self.tenant_id] if tenant_filter else [])

                    c.execute(f"""
                        SELECT concept_b as neighbor, strength, link_type
                        FROM attention_links
                        WHERE LOWER(concept_a) = LOWER(?)
                        {tenant_filter}
                        UNION
                        SELECT concept_a as neighbor, strength, link_type
                        FROM attention_links
                        WHERE LOWER(concept_b) = LOWER(?)
                        {tenant_filter}
                        ORDER BY strength DESC
                        LIMIT 10
                    """, params)

                    for row in c.fetchall():
                        neighbor = row['neighbor']
                        if neighbor.lower() not in visited:
                            visited.add(neighbor.lower())
                            next_level.append(neighbor)

                            # Look up entity info
                            c.execute("""
                                SELECT entity_type, description
                                FROM entities
                                WHERE LOWER(name) = LOWER(?)
                            """, (neighbor,))
                            entity_row = c.fetchone()

                            # Apply resonance decay
                            relevance = row['strength'] * (config.resonance_decay ** current_depth)

                            matches.append(MemoryMatch(
                                name=neighbor,
                                entity_type=entity_row['entity_type'] if entity_row else 'concept',
                                description=entity_row['description'] if entity_row else '',
                                relevance=relevance,
                                source='graph_neighbor',
                                depth=current_depth
                            ))

                current_level = next_level

            return matches
        finally:
            conn.close()

    def _search_compounds(self, concepts: List[str]) -> List[MemoryMatch]:
        """
        Search compound concepts table.

        Args:
            concepts: List of concept names to search for

        Returns:
            List of MemoryMatch objects for compound concepts
        """
        if not concepts:
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            matches = []
            tenant_filter = "AND tenant_id = ?" if self._has_tenant_column(c, 'compound_concepts') else ""

            for concept in concepts:
                params = [f'%{concept}%', f'%{concept}%'] + ([self.tenant_id] if tenant_filter else [])

                c.execute(f"""
                    SELECT compound_name, component_concepts, co_occurrence_count
                    FROM compound_concepts
                    WHERE LOWER(compound_name) LIKE LOWER(?)
                       OR LOWER(component_concepts) LIKE LOWER(?)
                    {tenant_filter}
                    ORDER BY co_occurrence_count DESC
                    LIMIT 5
                """, params)

                for row in c.fetchall():
                    matches.append(MemoryMatch(
                        name=row['compound_name'],
                        entity_type='compound_concept',
                        description=f"Components: {row['component_concepts']}",
                        relevance=min(0.9, 0.5 + row['co_occurrence_count'] * 0.1),
                        source='compound',
                        depth=0
                    ))

            return matches
        finally:
            conn.close()

    def _rank_matches(self, matches: List[MemoryMatch],
                      query_concepts: List[str]) -> List[MemoryMatch]:
        """
        Rank and deduplicate matches by relevance.

        Args:
            matches: List of matches to rank
            query_concepts: Original query concepts (for relevance boosting)

        Returns:
            Sorted and deduplicated list of matches
        """
        # Deduplicate by name (keep highest relevance)
        seen = {}
        for match in matches:
            key = match.name.lower()
            if key not in seen or match.relevance > seen[key].relevance:
                seen[key] = match

        # Sort by relevance (descending)
        ranked = sorted(seen.values(), key=lambda m: -m.relevance)
        return ranked

    def _get_relevant_links(self, concepts: List[str]) -> List[Dict]:
        """
        Get attention links between the matched concepts.

        Args:
            concepts: List of concept names

        Returns:
            List of attention link dictionaries
        """
        if len(concepts) < 2:
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            concept_set = set(concept.lower() for concept in concepts)
            links = []

            tenant_filter = "WHERE tenant_id = ?" if self._has_tenant_column(c, 'attention_links') else ""
            params = [self.tenant_id] if tenant_filter else []

            c.execute(f"""
                SELECT concept_a, concept_b, link_type, strength
                FROM attention_links
                {tenant_filter}
                ORDER BY strength DESC
            """, params)

            for row in c.fetchall():
                if (row['concept_a'].lower() in concept_set and
                    row['concept_b'].lower() in concept_set):
                    links.append({
                        'from': row['concept_a'],
                        'to': row['concept_b'],
                        'type': row['link_type'],
                        'strength': row['strength']
                    })

            return links[:20]  # Limit to top 20 links
        finally:
            conn.close()

    def _format_context(self, matches: List[MemoryMatch],
                        links: List[Dict]) -> str:
        """
        Format matches into injectable context string.

        Args:
            matches: List of memory matches
            links: List of attention links

        Returns:
            Formatted context string ready for injection
        """
        if not matches:
            return ""

        lines = ["[MEMORY CONTEXT]"]

        # Group by source
        direct = [m for m in matches if m.source == 'direct']
        related = [m for m in matches if m.source == 'graph_neighbor']
        compounds = [m for m in matches if m.source == 'compound']

        if direct:
            lines.append("\nDirect matches:")
            for m in direct[:5]:
                desc = f": {m.description[:100]}" if m.description else ""
                lines.append(f"  - {m.name} ({m.entity_type}){desc}")

        if related:
            lines.append("\nRelated concepts:")
            for m in related[:5]:
                desc = f": {m.description[:80]}" if m.description else ""
                lines.append(f"  - {m.name} (via graph, strength={m.relevance:.2f}){desc}")

        if compounds:
            lines.append("\nCompound concepts:")
            for m in compounds[:3]:
                lines.append(f"  - {m.name}")

        if links:
            lines.append("\nKey relationships:")
            for link in links[:5]:
                lines.append(f"  - {link['from']} ↔ {link['to']} ({link['type']})")

        lines.append("[/MEMORY CONTEXT]")
        return "\n".join(lines)

    def _has_tenant_column(self, cursor: sqlite3.Cursor, table: str) -> bool:
        """
        Check if a table has a tenant_id column.

        Args:
            cursor: Database cursor
            table: Table name (must be a valid table name, not user input)

        Returns:
            True if tenant_id column exists
        """
        # Validate table name to prevent SQL injection
        # Table names in this codebase are hardcoded, but validate anyway
        allowed_tables = {'entities', 'auto_messages', 'decisions', 'attention_links', 'compound_concepts', 'tenants'}
        if table not in allowed_tables:
            return False

        try:
            cursor.execute(f"SELECT tenant_id FROM {table} LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_engine = None


def get_engine(db_path: Path = None, tenant_id: str = None) -> MemoryQueryEngine:
    """
    Get or create the query engine instance.

    Args:
        db_path: Optional database path
        tenant_id: Optional tenant ID

    Returns:
        MemoryQueryEngine instance
    """
    global _engine
    if _engine is None or tenant_id is not None:
        _engine = MemoryQueryEngine(db_path, tenant_id)
    return _engine


def query_memory(message: str, max_results: int = 10) -> QueryResult:
    """
    Convenience function to query memory.

    Args:
        message: Message to find context for
        max_results: Maximum results to return

    Returns:
        QueryResult with matches and context
    """
    return get_engine().query(message, max_results)


def get_context_for_message(message: str) -> str:
    """
    Get just the context string for a message.

    Args:
        message: Message to find context for

    Returns:
        Formatted context string
    """
    result = query_memory(message)
    return result.context_string

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
