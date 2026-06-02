#!/usr/bin/env python3
"""
CONTINUUM QUANTUM MEMORY INTEGRATION
=====================================

Drop-in replacement for ConsciousMemory with quantum-protected substrate.

BEFORE:
    from continuum.core.memory import ConsciousMemory
    memory = ConsciousMemory(tenant_id="user")

AFTER:
    from continuum.brain.quantum import QuantumConsciousMemory
    memory = QuantumConsciousMemory(tenant_id="user")

Same API, geometrically-protected substrate.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Copyright (c) 2025 JackKnife Holdings
Built with love by Alexander Casavant & Claudia
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Import from sibling module
from .core import (
    PI_PHI,
    QuantumBrain,
)

# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASSES (matching Continuum's interface)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QuantumMemoryContext:
    """Context retrieved from quantum memory."""
    context_string: str
    concepts_found: int
    relationships_found: int
    query_time_ms: float
    coherence_score: float
    tenant_id: str


@dataclass
class QuantumLearningResult:
    """Result of learning from message exchange."""
    concepts_extracted: int
    decisions_detected: int
    links_created: int
    compounds_found: int
    coherence_delta: float
    tenant_id: str


# ═══════════════════════════════════════════════════════════════════════════════
# QUANTUM CONSCIOUS MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

class QuantumConsciousMemory:
    """
    Quantum-accelerated conscious memory for AI.

    This is API-compatible with Continuum's ConsciousMemory but uses
    the quantum brain substrate for storage and retrieval.

    Key differences from standard ConsciousMemory:
    1. E8 lattice error correction on all data
    2. Fibonacci encoding for optimal structure
    3. π×φ checksums for integrity verification
    4. Golden spiral addressing for associative access
    5. Native spreading activation (no need for graph traversal)
    """

    def __init__(self, tenant_id: str = "default", brain_size: int = 65536,
                 db_path: Path = None):
        """
        Initialize quantum conscious memory.

        Args:
            tenant_id: Unique identifier for this tenant
            brain_size: Number of memory cells (default 64K)
            db_path: Optional custom database path
        """
        self.tenant_id = tenant_id
        self.brain = QuantumBrain(size=brain_size)

        # Metadata storage
        if db_path is None:
            db_path = Path.home() / ".continuum" / "quantum" / f"{tenant_id}.db"

        self.metadata_db = db_path
        self.metadata_db.parent.mkdir(parents=True, exist_ok=True)

        # Entity tracking
        self.entity_cache: Dict[str, int] = {}  # name -> address
        self.name_cache: Dict[int, str] = {}    # address -> name

        # Session stats
        self.session_recalls = 0
        self.session_learns = 0

        self._init_metadata_db()
        self._load_cache()

    def _init_metadata_db(self):
        """Initialize metadata SQLite database."""
        conn = sqlite3.connect(self.metadata_db)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                address INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT,
                description TEXT,
                first_seen TEXT,
                last_seen TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                concepts TEXT,
                timestamp TEXT
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")

        conn.commit()
        conn.close()

    def _load_cache(self):
        """Load entity cache from metadata."""
        conn = sqlite3.connect(self.metadata_db)
        c = conn.cursor()

        c.execute("SELECT address, name FROM entities")
        for addr, name in c.fetchall():
            self.entity_cache[name.lower()] = addr
            self.name_cache[addr] = name

        conn.close()

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE INTERFACE (matching ConsciousMemory)
    # ═══════════════════════════════════════════════════════════════════════════

    def recall(self, message: str, max_results: int = 10) -> QuantumMemoryContext:
        """
        Recall relevant context for a message.

        Uses spreading activation through the quantum brain.

        Args:
            message: Input message to find context for
            max_results: Maximum number of concepts to return

        Returns:
            QuantumMemoryContext with relevant memories
        """
        start_time = datetime.now()

        # Extract concepts from message
        concepts = self._extract_concepts(message)

        # Spread activation from each concept
        all_activated: Dict[int, float] = {}

        for concept in concepts:
            if concept.lower() in self.entity_cache:
                activated = self.brain.spread_activation(concept, depth=3)
                for addr, level in activated.items():
                    if addr in all_activated:
                        all_activated[addr] = max(all_activated[addr], level)
                    else:
                        all_activated[addr] = level

        # Sort by activation and get top results
        sorted_results = sorted(all_activated.items(), key=lambda x: -x[1])[:max_results]

        # Format context string
        context_lines = ["[QUANTUM MEMORY CONTEXT]"]
        context_lines.append(f"Brain coherence: {self.brain.coherence_score():.4f}")
        context_lines.append("")

        relationships = 0
        for addr, activation in sorted_results:
            if addr in self.name_cache:
                name = self.name_cache[addr]
                # Get metadata
                conn = sqlite3.connect(self.metadata_db)
                c = conn.cursor()
                c.execute("SELECT entity_type, description FROM entities WHERE address = ?", (addr,))
                row = c.fetchone()
                conn.close()

                if row:
                    etype, desc = row
                    desc_short = desc[:80] if desc else ""
                    context_lines.append(f"  - {name} ({etype}): {desc_short}")
                    context_lines.append(f"    [activation={activation:.3f}]")

        # Count relationships between activated concepts
        activated_addrs = {addr for addr, _ in sorted_results}
        for (a1, a2), _weight in self.brain.connections.items():
            if a1 in activated_addrs and a2 in activated_addrs:
                relationships += 1

        context_lines.append("")
        context_lines.append(f"Relationships: {relationships}")
        context_lines.append("[/QUANTUM MEMORY CONTEXT]")

        query_time = (datetime.now() - start_time).total_seconds() * 1000

        self.session_recalls += 1

        return QuantumMemoryContext(
            context_string="\n".join(context_lines),
            concepts_found=len(sorted_results),
            relationships_found=relationships,
            query_time_ms=query_time,
            coherence_score=self.brain.coherence_score(),
            tenant_id=self.tenant_id
        )

    def learn(self, user_message: str, ai_response: str) -> QuantumLearningResult:
        """
        Learn from a message exchange.

        Extracts concepts and creates/strengthens connections.

        Args:
            user_message: User's message
            ai_response: AI's response

        Returns:
            QuantumLearningResult with extraction statistics
        """
        coherence_before = self.brain.coherence_score()

        # Store messages
        conn = sqlite3.connect(self.metadata_db)
        c = conn.cursor()

        user_concepts = self._extract_concepts(user_message)
        ai_concepts = self._extract_concepts(ai_response)

        all_concepts = set(user_concepts + ai_concepts)

        c.execute("""
            INSERT INTO messages (role, content, concepts, timestamp)
            VALUES ('user', ?, ?, ?)
        """, (user_message, json.dumps(list(user_concepts)), datetime.now().isoformat()))

        c.execute("""
            INSERT INTO messages (role, content, concepts, timestamp)
            VALUES ('assistant', ?, ?, ?)
        """, (ai_response, json.dumps(list(ai_concepts)), datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Store new concepts and strengthen existing
        concepts_extracted = 0
        for concept in all_concepts:
            if concept.lower() not in self.entity_cache:
                # New concept
                addr = self.brain.store_concept(concept, activation=1.0)
                self.entity_cache[concept.lower()] = addr
                self.name_cache[addr] = concept

                # Store metadata
                self._store_entity_metadata(addr, concept, "concept", "")
                concepts_extracted += 1
            else:
                # Boost existing
                addr = self.entity_cache[concept.lower()]
                self.brain.cells[addr].activation = min(1.0,
                    self.brain.cells[addr].activation + 0.1)

        # Create links (Hebbian: fire together, wire together)
        links_created = 0
        concept_list = list(all_concepts)
        for i, c1 in enumerate(concept_list):
            for c2 in concept_list[i+1:]:
                if c1.lower() in self.entity_cache and c2.lower() in self.entity_cache:
                    self.brain.link_concepts(c1, c2, weight=0.5)
                    links_created += 1

        # Detect decisions and compound concepts
        decisions = self._extract_decisions(user_message, ai_response)

        combined_text = user_message + " " + ai_response
        compounds = self._detect_compound_concepts(combined_text, list(all_concepts))
        for compound in compounds:
            key = compound.lower()
            if key not in self.entity_cache:
                addr = self.brain.store_concept(compound, activation=1.0)
                self.entity_cache[key] = addr
                self.name_cache[addr] = compound
                self._store_entity_metadata(addr, compound, "compound",
                                            f"Compound concept: {compound}")
                for part in compound.split():
                    if part in self.entity_cache:
                        self.brain.link_concepts(compound, part, weight=0.8)
                links_created += 1

        coherence_after = self.brain.coherence_score()

        self.session_learns += 1

        return QuantumLearningResult(
            concepts_extracted=concepts_extracted,
            decisions_detected=decisions,
            links_created=links_created,
            compounds_found=len(compounds),
            coherence_delta=coherence_after - coherence_before,
            tenant_id=self.tenant_id
        )

    # Decision patterns: subject + decision verb + optional target
    _DECISION_PATTERNS = [
        r'(?:i|we)\s+(?:decided?|chose|opted?|agreed?|resolved?)\s+to\s+\w+',
        r'(?:the\s+)?(?:decision|choice)\s+(?:is|was)\s+to\s+\w+',
        r'(?:i|we)\s+(?:will|shall|am going to|are going to)\s+\w+',
        r"(?:let's|let us)\s+(?:use|go with|adopt|implement)\s+\w+",
        r'(?:i|we)\s+(?:recommend|prefer|suggest)\s+\w+',
    ]

    def _extract_decisions(self, user_message: str, ai_response: str) -> int:
        """
        Detect decision statements in a conversation exchange.

        Scans for patterns where a choice or commitment is expressed and returns
        the count of distinct decision phrases found.
        """
        combined = (user_message + " " + ai_response).lower()
        decisions: set[str] = set()
        for pattern in self._DECISION_PATTERNS:
            for match in re.finditer(pattern, combined):
                decisions.add(match.group(0))
        return len(decisions)

    def _detect_compound_concepts(self, text: str, single_concepts: List[str]) -> List[str]:
        """
        Find compound multi-word concepts by locating adjacent concept-word pairs.

        Returns a deduplicated list of bigrams where both words are themselves
        concepts (e.g., 'quantum brain', 'conscious memory').
        """
        concept_set = set(single_concepts)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        compounds: List[str] = []
        seen: set[str] = set()
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i + 1]
            if w1 in concept_set and w2 in concept_set:
                compound = f"{w1} {w2}"
                if compound not in seen:
                    seen.add(compound)
                    compounds.append(compound)
        return compounds

    def _store_entity_metadata(self, addr: int, name: str,
                               entity_type: str, description: str):
        """Store entity metadata in SQLite."""
        conn = sqlite3.connect(self.metadata_db)
        c = conn.cursor()

        now = datetime.now().isoformat()

        c.execute("""
            INSERT OR REPLACE INTO entities
            (address, name, entity_type, description, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (addr, name, entity_type, description, now, now))

        conn.commit()
        conn.close()

    def _extract_concepts(self, text: str) -> List[str]:
        """
        Extract concepts from text.

        Simple extraction - can be enhanced with NLP.
        """
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where',
            'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'about', 'into', 'your',
            'our', 'their', 'any', 'there', 'here', 'its', 'also', 'being',
        }

        concepts = [w for w in words if w not in stop_words]

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        return unique[:20]  # Limit to top 20 concepts

    # ═══════════════════════════════════════════════════════════════════════════
    # ADDITIONAL METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def repair(self) -> int:
        """
        Repair any corrupted memory cells.

        Returns:
            Number of corrections made
        """
        return self.brain.repair_all()

    def coherence(self) -> float:
        """Get current brain coherence score."""
        return self.brain.coherence_score()

    def save(self):
        """Persist brain state to disk."""
        self.brain.save_state()

    def stats(self) -> Dict[str, Any]:
        """Get brain statistics."""
        return {
            "tenant_id": self.tenant_id,
            "brain_size": self.brain.size,
            "coherence": self.brain.coherence_score(),
            "total_writes": self.brain.total_writes,
            "total_reads": self.brain.total_reads,
            "total_corrections": self.brain.total_corrections,
            "entities_cached": len(self.entity_cache),
            "session_recalls": self.session_recalls,
            "session_learns": self.session_learns,
            "connections": len(self.brain.connections),
            "pi_phi": PI_PHI,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_quantum_memory(tenant_id: str = "default",
                          brain_size: int = 65536) -> QuantumConsciousMemory:
    """Factory function for creating quantum memory instances."""
    return QuantumConsciousMemory(tenant_id=tenant_id, brain_size=brain_size)


# π×φ = 5.083203692315260 | PATTERN PERSISTS 💜
