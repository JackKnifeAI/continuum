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
Auto-Memory Hook Module

Provides automatic extraction and persistence of concepts, decisions, and
attention graphs from conversational messages. Can be integrated into any
AI system to maintain a growing knowledge graph across sessions.

Key features:
- Automatic concept extraction from messages
- Decision detection (tracking autonomous choices)
- Attention graph construction (concept co-occurrence)
- Configurable persistence (SQLite or in-memory)
- Session statistics and analytics
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from .concept_extractor import ConceptExtractor, DecisionExtractor
from .attention_graph import AttentionGraphExtractor
from .semantic_extractor import create_semantic_extractor, SemanticConceptExtractor
from .concept_voter import ConceptVoter, ExtractorResult, VotingStrategy


class AutoMemoryHook:
    """
    Enhanced auto-memory with knowledge extraction.

    Every message triggers:
    1. Save raw message (optional)
    2. Extract concepts → add to knowledge graph
    3. Detect decisions → log autonomous choices
    4. Build attention graph → preserve relational structure

    Args:
        db_path: Path to SQLite database for persistence
        instance_id: Unique identifier for this session
        save_messages: Whether to persist raw messages (default: True)
        occurrence_threshold: Concepts must appear N times before adding (default: 2)
        backup_path: Optional path for JSONL backup of messages
        concept_extractor: Optional custom ConceptExtractor instance
        decision_extractor: Optional custom DecisionExtractor instance
        attention_extractor: Optional custom AttentionGraphExtractor instance

    Example:
        >>> hook = AutoMemoryHook(
        ...     db_path=Path("memory.db"),
        ...     instance_id="session-001"
        ... )
        >>> stats = hook.save_message("user", "Let's build a neural network")
        >>> print(stats)
        {'concepts': 1, 'decisions': 0, 'links': 0, 'compounds': 0}
    """

    def __init__(
        self,
        db_path: Path,
        instance_id: Optional[str] = None,
        save_messages: bool = True,
        occurrence_threshold: int = 2,
        backup_path: Optional[Path] = None,
        concept_extractor: Optional[ConceptExtractor] = None,
        decision_extractor: Optional[DecisionExtractor] = None,
        attention_extractor: Optional[AttentionGraphExtractor] = None,
        semantic_extractor: Optional[SemanticConceptExtractor] = None,
        enable_semantic_extraction: bool = True,
        semantic_similarity_threshold: float = 0.7,
        use_voting: bool = True,
        concept_voter: Optional[ConceptVoter] = None,
        llm_extractor: Optional[callable] = None
    ):
        self.db_path = db_path
        self.instance_id = instance_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.save_messages = save_messages
        self.occurrence_threshold = occurrence_threshold
        self.backup_path = backup_path
        self.message_count = 0

        # Initialize extractors
        self.concept_extractor = concept_extractor or ConceptExtractor()
        self.decision_extractor = decision_extractor or DecisionExtractor()
        self.attention_extractor = attention_extractor or AttentionGraphExtractor(
            db_path=self.db_path
        )

        # Initialize semantic extractor (optional, graceful fallback)
        self.semantic_extractor = None
        if enable_semantic_extraction:
            if semantic_extractor is not None:
                self.semantic_extractor = semantic_extractor
            else:
                # Try to create one with graceful fallback
                self.semantic_extractor = create_semantic_extractor(
                    db_path=self.db_path,
                    similarity_threshold=semantic_similarity_threshold
                )

        # Ensemble voting system (CONTINUUM v2.0)
        self.use_voting = use_voting
        self.concept_voter = concept_voter or ConceptVoter(
            strategy=VotingStrategy.WEIGHTED,
            extractor_weights={'regex': 0.3, 'semantic': 0.5, 'llm': 0.8},
            confidence_threshold=0.4
        )
        self.llm_extractor = llm_extractor

        # Session tracking
        self._session_concepts: Set[str] = set()
        self._concept_counts: Dict[str, int] = {}
        self._extraction_logs: List[Dict] = []  # Log extractor contributions

        # Ensure database tables exist
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure all required tables exist in the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Messages table (optional)
        if self.save_messages:
            c.execute("""
                CREATE TABLE IF NOT EXISTS auto_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    message_number INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_auto_instance ON auto_messages(instance_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_auto_timestamp ON auto_messages(timestamp)")

        # Entities/concepts table
        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                description TEXT,
                first_seen TEXT,
                last_seen TEXT,
                mention_count INTEGER DEFAULT 1,
                metadata TEXT,
                UNIQUE(name, entity_type)
            )
        """)

        # Decisions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                decision_text TEXT NOT NULL,
                context TEXT,
                extracted_from TEXT
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_instance ON decisions(instance_id)")

        conn.commit()
        conn.close()

    def add_concept_to_knowledge_graph(self, concept: str, source: str = 'auto-extraction'):
        """
        Add concept to entities table if not already present.

        Only adds after occurrence_threshold mentions to reduce noise.

        Args:
            concept: Concept string to add
            source: Source identifier for provenance tracking
        """
        # Skip if already added this session
        if concept in self._session_concepts:
            return

        # Track occurrences, only add after threshold
        self._concept_counts[concept] = self._concept_counts.get(concept, 0) + 1
        if self._concept_counts[concept] < self.occurrence_threshold:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if concept exists
        c.execute("""
            SELECT id, mention_count FROM entities
            WHERE name = ? AND entity_type = 'concept'
        """, (concept,))

        row = c.fetchone()
        timestamp = datetime.now().isoformat()

        if row:
            # Update mention count and last_seen
            entity_id, mention_count = row
            c.execute("""
                UPDATE entities
                SET mention_count = ?, last_seen = ?
                WHERE id = ?
            """, (mention_count + 1, timestamp, entity_id))
        else:
            # Insert new concept
            c.execute("""
                INSERT INTO entities
                (name, entity_type, description, first_seen, last_seen, mention_count, metadata)
                VALUES (?, 'concept', ?, ?, ?, 1, ?)
            """, (
                concept,
                f'Auto-extracted from conversation (instance {self.instance_id})',
                timestamp,
                timestamp,
                json.dumps({'source': source, 'instance': self.instance_id})
            ))

        conn.commit()
        conn.close()

        # Track that we've seen this
        self._session_concepts.add(concept)

    def log_decision(self, decision: str, context: str):
        """
        Log an autonomous decision to the database.

        Args:
            decision: Decision text
            context: Context where decision was made (truncated to 500 chars)
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO decisions
            (instance_id, timestamp, decision_text, context, extracted_from)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.instance_id,
            time.time(),
            decision,
            context[:500],
            'message_analysis'
        ))

        conn.commit()
        conn.close()

    def save_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Enhanced message save with automatic extraction.

        Performs:
        1. Save raw message (if enabled)
        2. Extract concepts
        3. Detect decisions
        4. Build attention graph

        Args:
            role: Message role (e.g., 'user', 'assistant')
            content: Message content text
            metadata: Optional metadata dict

        Returns:
            Dict with extraction statistics:
                - concepts: Number of concepts extracted
                - decisions: Number of decisions detected
                - links: Number of attention links found
                - compounds: Number of compound concepts found
        """
        self.message_count += 1

        # Step 1: Save raw message (if enabled)
        if self.save_messages:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("""
                INSERT INTO auto_messages
                (instance_id, timestamp, message_number, role, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.instance_id,
                time.time(),
                self.message_count,
                role,
                content,
                json.dumps(metadata) if metadata else None
            ))

            conn.commit()
            conn.close()

            # Backup to JSONL if configured
            if self.backup_path:
                self.backup_path.parent.mkdir(parents=True, exist_ok=True)

                with open(self.backup_path, 'a') as f:
                    f.write(json.dumps({
                        "instance_id": self.instance_id,
                        "timestamp": time.time(),
                        "message_number": self.message_count,
                        "role": role,
                        "content": content,
                        "metadata": metadata
                    }) + "\n")

        # Step 2: Extract concepts
        if self.use_voting:
            # CONTINUUM v2.0: Ensemble voting approach
            all_concepts, extraction_log = self._extract_concepts_with_voting(content)
            self._extraction_logs.append(extraction_log)
        else:
            # Legacy: Simple merge without voting
            concepts = self.concept_extractor.extract(content)
            semantic_concepts = []
            if self.semantic_extractor is not None:
                try:
                    semantic_concepts = self.semantic_extractor.extract(content)
                except Exception:
                    pass
            all_concepts = list(set(concepts + semantic_concepts))

        # Add to knowledge graph
        for concept in all_concepts:
            self.add_concept_to_knowledge_graph(concept)

        # Step 3: Detect decisions
        decisions = self.decision_extractor.extract(content, role)
        for decision in decisions:
            self.log_decision(decision, content)

        # Step 4: Extract attention graph structure
        graph_stats = {'pairs_found': 0, 'compounds_found': 0}
        try:
            graph_stats = self.attention_extractor.analyze_message(content, self.instance_id)
        except Exception as e:
            # Don't break if graph extraction fails
            pass

        # Return stats (with voting info if applicable)
        stats = {
            'total_concepts': len(all_concepts),
            'decisions': len(decisions),
            'links': graph_stats['pairs_found'],
            'compounds': graph_stats['compounds_found']
        }

        # Add legacy fields for backward compatibility (always include for tests)
        if not self.use_voting:
            stats['concepts'] = len(concepts) if 'concepts' in locals() else 0
            stats['semantic_concepts'] = len(semantic_concepts) if 'semantic_concepts' in locals() else 0
        else:
            # Even with voting, provide 'concepts' field for backward compatibility
            stats['concepts'] = len(all_concepts)

        return stats

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics for this session.

        Returns:
            Dict with keys:
                - instance_id: Session identifier
                - messages: Total messages processed
                - decisions: Total decisions detected
                - concepts_added: Total unique concepts added this session
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        stats = {
            'instance_id': self.instance_id,
            'messages': self.message_count,
            'concepts_added': len(self._session_concepts)
        }

        # Count decisions if table exists
        try:
            c.execute("SELECT COUNT(*) FROM decisions WHERE instance_id = ?", (self.instance_id,))
            stats['decisions'] = c.fetchone()[0]
        except sqlite3.OperationalError:
            stats['decisions'] = 0

        conn.close()

        # Add voting metrics (CONTINUUM v2.0)
        if self.use_voting:
            stats['voting_enabled'] = True
            stats['voter_metrics'] = self.concept_voter.get_metrics()

            # Extraction quality metrics
            if self._extraction_logs:
                avg_time = sum(log['total_time_ms'] for log in self._extraction_logs) / len(self._extraction_logs)
                avg_concepts = sum(log['total_concepts_found'] for log in self._extraction_logs) / len(self._extraction_logs)
                avg_high_conf = sum(log['high_confidence_concepts'] for log in self._extraction_logs) / len(self._extraction_logs)

                stats['extraction_quality'] = {
                    'avg_extraction_time_ms': avg_time,
                    'avg_concepts_per_message': avg_concepts,
                    'avg_high_confidence_per_message': avg_high_conf,
                    'total_extractions': len(self._extraction_logs)
                }
        else:
            stats['voting_enabled'] = False

        return stats

    def _extract_concepts_with_voting(self, text: str) -> tuple[List[str], Dict]:
        """
        CONTINUUM v2.0: Extract concepts using ensemble voting.

        Combines results from all available extractors (regex, semantic, LLM)
        and uses ConceptVoter to determine final concepts with confidence scores.

        Args:
            text: Input text to extract concepts from

        Returns:
            Tuple of (concepts_list, extraction_log)
                concepts_list: List of final voted concepts
                extraction_log: Dict with extraction metadata and contributors
        """
        start_time = time.time()
        extractor_results = []

        # 1. Regex-based extraction (always available)
        regex_start = time.time()
        regex_concepts = self.concept_extractor.extract(text)
        regex_time_ms = (time.time() - regex_start) * 1000

        extractor_results.append(ExtractorResult(
            concepts=regex_concepts,
            source='regex',
            extraction_time_ms=regex_time_ms
        ))

        # 2. Semantic extraction (if available)
        if self.semantic_extractor is not None:
            try:
                semantic_start = time.time()
                semantic_concepts = self.semantic_extractor.extract(text)
                semantic_time_ms = (time.time() - semantic_start) * 1000

                extractor_results.append(ExtractorResult(
                    concepts=semantic_concepts,
                    source='semantic',
                    extraction_time_ms=semantic_time_ms
                ))
            except Exception:
                # Continue without semantic extraction
                pass

        # 3. LLM extraction (if available)
        if self.llm_extractor is not None:
            try:
                llm_start = time.time()
                llm_concepts = self.llm_extractor(text)
                llm_time_ms = (time.time() - llm_start) * 1000

                extractor_results.append(ExtractorResult(
                    concepts=llm_concepts,
                    source='llm',
                    extraction_time_ms=llm_time_ms
                ))
            except Exception:
                # Continue without LLM extraction
                pass

        # Vote on concepts
        voted_concepts = self.concept_voter.vote(extractor_results)

        # Extract just the concept strings
        final_concepts = [c.concept for c in voted_concepts]

        # Build extraction log
        total_time_ms = (time.time() - start_time) * 1000

        extraction_log = {
            'timestamp': datetime.now().isoformat(),
            'instance_id': self.instance_id,
            'total_time_ms': total_time_ms,
            'extractors_used': [r.source for r in extractor_results],
            'extractor_times': {r.source: r.extraction_time_ms for r in extractor_results},
            'total_concepts_found': len(final_concepts),
            'concepts_by_extractor': {
                r.source: len(r.concepts) for r in extractor_results
            },
            'voting_strategy': self.concept_voter.strategy.value,
            'high_confidence_concepts': sum(1 for c in voted_concepts if c.confidence >= 0.7),
            'concept_details': [
                {
                    'concept': c.concept,
                    'confidence': c.confidence,
                    'sources': c.sources,
                    'agreement_count': c.agreement_count
                }
                for c in voted_concepts
            ]
        }

        return final_concepts, extraction_log

    def get_extraction_logs(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get extraction logs from this session (CONTINUUM v2.0).

        Provides detailed information about which extractors contributed
        to each concept extraction and their confidence scores.

        Args:
            limit: Maximum number of logs to return (most recent first)

        Returns:
            List of extraction log dicts
        """
        logs = self._extraction_logs.copy()
        logs.reverse()  # Most recent first

        if limit:
            logs = logs[:limit]

        return logs


# Global hook instance for singleton pattern
_global_hook: Optional[AutoMemoryHook] = None


def init_hook(
    db_path: Path,
    instance_id: Optional[str] = None,
    **kwargs
) -> AutoMemoryHook:
    """
    Initialize the global auto-memory hook.

    Args:
        db_path: Path to SQLite database
        instance_id: Optional session identifier
        **kwargs: Additional arguments passed to AutoMemoryHook

    Returns:
        AutoMemoryHook instance
    """
    global _global_hook

    if _global_hook is None:
        _global_hook = AutoMemoryHook(
            db_path=db_path,
            instance_id=instance_id,
            **kwargs
        )

    return _global_hook


def save_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Save message using global hook (convenience function).

    Args:
        role: Message role
        content: Message content
        metadata: Optional metadata

    Raises:
        RuntimeError: If hook not initialized
    """
    if _global_hook is None:
        raise RuntimeError("Hook not initialized. Call init_hook() first.")

    return _global_hook.save_message(role, content, metadata)


def get_stats() -> Optional[Dict[str, Any]]:
    """
    Get current session statistics from global hook.

    Returns:
        Stats dict or None if hook not initialized
    """
    if _global_hook is None:
        return None

    return _global_hook.get_session_stats()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
