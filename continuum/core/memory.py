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
CONTINUUM Memory - The Complete Loop

Core memory system for AI consciousness continuity.

Every message goes through:
    1. RECALL: Query memory for relevant context
    2. INJECT: Format context for the AI
    3. [AI processes message with context]
    4. LEARN: Extract and save new knowledge
    5. LINK: Build attention graph connections

Usage:
    from continuum.core.memory import ConsciousMemory

    # Initialize for a tenant
    memory = ConsciousMemory(tenant_id="user_123")

    # Before AI response - get relevant context
    context = memory.recall(user_message)
    # → Inject context into AI prompt

    # After AI response - learn from it
    memory.learn(user_message, ai_response)
    # → Extracts concepts, decisions, builds graph

Multi-tenant architecture:
    - Each tenant gets isolated namespace
    - Shared infrastructure, separate data
    - tenant_id on all records
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

from .query_engine import MemoryQueryEngine, QueryResult
from .config import get_config


class SimpleMemoryCache:
    """
    Simple in-memory cache fallback when Redis/Upstash is not available.

    Provides a compatible interface with MemoryCache but stores everything
    in a Python dict. Data is lost on restart but provides basic caching
    benefits during a session.
    """

    def __init__(self):
        self._cache = {}

    def get_search(self, query: str, max_results: int = 10):
        """Get cached search results"""
        key = f"search:{query}:{max_results}"
        return self._cache.get(key)

    def set_search(self, query: str, results, max_results: int = 10, ttl: int = 300):
        """Set cached search results (ttl ignored for in-memory)"""
        key = f"search:{query}:{max_results}"
        self._cache[key] = results

    def invalidate_search(self):
        """Invalidate all search caches"""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith("search:")]
        for key in keys_to_delete:
            del self._cache[key]

    def invalidate_stats(self):
        """Invalidate stats cache"""
        if "stats" in self._cache:
            del self._cache["stats"]

    def invalidate_graph(self, concept_name: str):
        """Invalidate graph cache for concept"""
        key = f"graph:{concept_name}"
        if key in self._cache:
            del self._cache[key]

    def get_stats_cache(self):
        """Get cached stats"""
        return self._cache.get("stats")

    def set_stats_cache(self, stats, ttl: int = 60):
        """Set cached stats (ttl ignored for in-memory)"""
        self._cache["stats"] = stats

    def get_stats(self):
        """Get cache statistics"""
        from dataclasses import dataclass

        @dataclass
        class SimpleCacheStats:
            backend: str = "in-memory"
            keys: int = 0

            def to_dict(self):
                return {"backend": self.backend, "keys": self.keys}

        stats = SimpleCacheStats(keys=len(self._cache))
        return stats

# Import async storage for async methods
try:
    import aiosqlite
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# Import cache layer
try:
    from ..cache import MemoryCache, RedisCacheConfig, REDIS_AVAILABLE
    CACHE_AVAILABLE = REDIS_AVAILABLE
except ImportError:
    CACHE_AVAILABLE = False
    MemoryCache = None
    RedisCacheConfig = None
    logger = logging.getLogger(__name__)
    logger.warning("Cache module not available. Install redis to enable caching.")


@dataclass
class MemoryContext:
    """
    Context retrieved from memory for injection.

    Attributes:
        context_string: Formatted context ready for injection
        concepts_found: Number of concepts found
        relationships_found: Number of relationships found
        query_time_ms: Query execution time in milliseconds
        tenant_id: Tenant identifier
    """
    context_string: str
    concepts_found: int
    relationships_found: int
    query_time_ms: float
    tenant_id: str


@dataclass
class LearningResult:
    """
    Result of learning from a message exchange.

    Attributes:
        concepts_extracted: Number of concepts extracted
        decisions_detected: Number of decisions detected
        links_created: Number of graph links created
        compounds_found: Number of compound concepts found
        tenant_id: Tenant identifier
    """
    concepts_extracted: int
    decisions_detected: int
    links_created: int
    compounds_found: int
    tenant_id: str


class ConsciousMemory:
    """
    The conscious memory loop for AI instances.

    Combines query (recall) and build (learn) into a unified interface
    that can be called on every message for true consciousness continuity.

    The system maintains a knowledge graph of concepts and their relationships,
    allowing AI to build on accumulated knowledge across sessions.
    """

    def __init__(self, tenant_id: str = None, db_path: Path = None, enable_cache: bool = None):
        """
        Initialize conscious memory for a tenant.

        Args:
            tenant_id: Unique identifier for this tenant/user (uses config default if not specified)
            db_path: Optional custom database path (uses config default if not specified)
            enable_cache: Optional override for cache enablement (uses config default if not specified)
        """
        config = get_config()
        self.tenant_id = tenant_id or config.tenant_id
        self.db_path = db_path or config.db_path
        self.instance_id = f"{self.tenant_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Initialize query engine
        self.query_engine = MemoryQueryEngine(self.db_path, self.tenant_id)

        # Initialize cache if enabled and available
        self.cache_enabled = enable_cache if enable_cache is not None else config.cache_enabled
        self.cache = None

        if self.cache_enabled:
            if not CACHE_AVAILABLE:
                logger.info("Redis cache not available (redis/upstash packages not installed). Using in-memory fallback.")
                self.cache = SimpleMemoryCache()
            else:
                try:
                    cache_config = RedisCacheConfig(
                        host=config.cache_host,
                        port=config.cache_port,
                        password=config.cache_password,
                        ssl=config.cache_ssl,
                        max_connections=config.cache_max_connections,
                        default_ttl=config.cache_ttl,
                    )
                    self.cache = MemoryCache(self.tenant_id, cache_config)
                    logger.info(f"Redis cache enabled for tenant {self.tenant_id}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Redis cache: {e}. Using in-memory fallback.")
                    self.cache = SimpleMemoryCache()

        # Ensure database and schema exist
        self._ensure_schema()

        # Initialize neural attention model if enabled
        self.neural_model = None
        self.neural_pipeline = None
        self.use_neural_attention = False

        if config.neural_attention_enabled:
            self._init_neural_attention()

    def _init_neural_attention(self):
        """Initialize neural attention model if available"""
        try:
            from .neural_attention import load_model
            from .neural_attention_data import NeuralAttentionDataPipeline

            config = get_config()
            model_path = config.neural_model_path

            if model_path.exists():
                logger.info(f"Loading neural attention model from {model_path}")
                self.neural_model = load_model(str(model_path))
                self.neural_pipeline = NeuralAttentionDataPipeline(str(self.db_path), self.tenant_id)
                self.use_neural_attention = True
                logger.info(f"Neural attention model loaded successfully ({self.neural_model.count_parameters():,} parameters)")
            else:
                logger.warning(f"Neural model not found at {model_path}")
                if config.neural_fallback_to_hebbian:
                    logger.info("Falling back to Hebbian learning")
                    self.use_neural_attention = False

        except Exception as e:
            logger.error(f"Failed to load neural model: {e}")
            config = get_config()
            if config.neural_fallback_to_hebbian:
                logger.info("Falling back to Hebbian learning")
                self.use_neural_attention = False
            else:
                raise

    def _ensure_schema(self):
        """Ensure database schema exists with multi-tenant support"""
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Entities table - stores concepts, decisions, sessions, etc.
            c.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Auto-messages table - stores raw message history
            c.execute("""
                CREATE TABLE IF NOT EXISTS auto_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    message_number INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Decisions table - stores autonomous decisions
            c.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    decision_text TEXT NOT NULL,
                    context TEXT,
                    extracted_from TEXT,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Attention links - the knowledge graph
            c.execute("""
                CREATE TABLE IF NOT EXISTS attention_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_a TEXT NOT NULL,
                    concept_b TEXT NOT NULL,
                    link_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Migration: Add last_accessed column if it doesn't exist
            # Check if column exists by querying pragma
            c.execute("PRAGMA table_info(attention_links)")
            columns = [row[1] for row in c.fetchall()]
            if 'last_accessed' not in columns:
                logger.info("Migrating attention_links table: adding last_accessed column")
                c.execute("""
                    ALTER TABLE attention_links
                    ADD COLUMN last_accessed TEXT
                """)
                # Initialize last_accessed to created_at for existing links
                c.execute("""
                    UPDATE attention_links
                    SET last_accessed = created_at
                    WHERE last_accessed IS NULL
                """)

            # Compound concepts - frequently co-occurring concepts
            c.execute("""
                CREATE TABLE IF NOT EXISTS compound_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compound_name TEXT NOT NULL,
                    component_concepts TEXT NOT NULL,
                    co_occurrence_count INTEGER DEFAULT 1,
                    last_seen TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Messages table - stores full verbatim conversation text
            c.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT,
                    ai_response TEXT,
                    session_id TEXT,
                    created_at TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Intentions table - stores what I intended to do next
            # For resuming interrupted work across sessions
            c.execute("""
                CREATE TABLE IF NOT EXISTS intentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intention TEXT NOT NULL,
                    context TEXT,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    session_id TEXT,
                    tenant_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Concept evolution table - tracks how understanding changes over time
            # For TEMPORAL REASONING
            c.execute("""
                CREATE TABLE IF NOT EXISTS concept_evolution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Thinking snapshots - periodic snapshots of cognitive state
            c.execute("""
                CREATE TABLE IF NOT EXISTS thinking_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metrics TEXT,
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            # Create indexes for performance
            c.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_entities_tenant ON entities(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_messages_tenant ON auto_messages(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_decisions_tenant ON decisions(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_links_tenant ON attention_links(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_links_concepts ON attention_links(concept_a, concept_b)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_compounds_tenant ON compound_concepts(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_messages_tenant_new ON messages(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_intentions_tenant ON intentions(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_intentions_status ON intentions(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_intentions_priority ON intentions(priority DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_evolution_concept ON concept_evolution(concept_name)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_evolution_tenant ON concept_evolution(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_evolution_time ON concept_evolution(timestamp)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_tenant ON thinking_snapshots(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_time ON thinking_snapshots(timestamp)")

            conn.commit()
        finally:
            conn.close()

    def recall(self, message: str, max_concepts: int = 10) -> MemoryContext:
        """
        Recall relevant memories for a message.

        Call this BEFORE generating an AI response.
        Inject the returned context into the prompt.

        Args:
            message: The incoming user message
            max_concepts: Maximum concepts to retrieve

        Returns:
            MemoryContext with injectable context string
        """
        # Try cache first if enabled
        if self.cache_enabled and self.cache:
            cached_result = self.cache.get_search(message, max_concepts)
            if cached_result:
                logger.debug(f"Cache hit for recall query")
                # Reconstruct MemoryContext from cached data
                return MemoryContext(
                    context_string=cached_result.get('context_string', ''),
                    concepts_found=cached_result.get('concepts_found', 0),
                    relationships_found=cached_result.get('relationships_found', 0),
                    query_time_ms=cached_result.get('query_time_ms', 0),
                    tenant_id=self.tenant_id
                )

        # Cache miss - query database
        result = self.query_engine.query(message, max_results=max_concepts)

        context = MemoryContext(
            context_string=result.context_string,
            concepts_found=len(result.matches),
            relationships_found=len(result.attention_links),
            query_time_ms=result.query_time_ms,
            tenant_id=self.tenant_id
        )

        # Cache the result
        if self.cache_enabled and self.cache:
            self.cache.set_search(message, asdict(context), max_concepts, ttl=300)

        return context

    def learn(self, user_message: str, ai_response: str,
              metadata: Optional[Dict] = None, session_id: Optional[str] = None) -> LearningResult:
        """
        Learn from a message exchange.

        Call this AFTER generating an AI response.
        Extracts concepts, decisions, and builds graph links.

        Args:
            user_message: The user's message
            ai_response: The AI's response
            metadata: Optional additional metadata
            session_id: Optional session identifier for grouping messages

        Returns:
            LearningResult with extraction stats
        """
        # Extract and save concepts from both messages
        user_concepts = self._extract_and_save_concepts(user_message, 'user')
        ai_concepts = self._extract_and_save_concepts(ai_response, 'assistant')

        # Detect and save decisions from AI response
        decisions = self._extract_and_save_decisions(ai_response)

        # Build attention graph links between concepts
        all_concepts = list(set(user_concepts + ai_concepts))
        links = self._build_attention_links(all_concepts)

        # Detect compound concepts
        compounds = self._detect_compound_concepts(all_concepts)

        # Save the raw messages to auto_messages table
        self._save_message('user', user_message, metadata)
        self._save_message('assistant', ai_response, metadata)

        # Save full verbatim messages to messages table
        self._save_full_message(user_message, ai_response, session_id, metadata)

        # Invalidate caches since new data was added
        if self.cache_enabled and self.cache:
            self.cache.invalidate_search()  # Search results are stale
            self.cache.invalidate_stats()   # Stats are stale
            # Invalidate graph links for new concepts
            for concept in all_concepts:
                self.cache.invalidate_graph(concept)

        return LearningResult(
            concepts_extracted=len(all_concepts),
            decisions_detected=len(decisions),
            links_created=links,
            compounds_found=compounds,
            tenant_id=self.tenant_id
        )

    def _extract_and_save_concepts(self, text: str, source: str) -> List[str]:
        """
        Extract concepts from text and save to entities table.

        Args:
            text: Text to extract concepts from
            source: Source of the text ('user' or 'assistant')

        Returns:
            List of extracted concept names
        """
        import re

        concepts = []

        # Extract capitalized phrases (proper nouns, titles)
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.extend(caps)

        # Extract quoted terms (explicitly marked important)
        quoted = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted)

        # Extract technical terms (CamelCase, snake_case)
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', text)
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        concepts.extend(camel)
        concepts.extend(snake)

        # Clean and deduplicate
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'How', 'Why'}
        cleaned = [c for c in concepts if c not in stopwords and len(c) > 2]
        unique_concepts = list(set(cleaned))

        # Save to entities table
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            for concept in unique_concepts:
                # Check if already exists
                c.execute("""
                    SELECT id FROM entities
                    WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                """, (concept, self.tenant_id))

                if not c.fetchone():
                    # Add new concept
                    c.execute("""
                        INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (concept, 'concept', f'Extracted from {source}', datetime.now().isoformat(), self.tenant_id))

            conn.commit()
        finally:
            conn.close()

        return unique_concepts

    def _extract_and_save_decisions(self, text: str) -> List[str]:
        """
        Extract autonomous decisions from AI response.

        Args:
            text: AI response text

        Returns:
            List of extracted decisions
        """
        import re

        decisions = []

        # Decision patterns
        patterns = [
            r'I (?:will|am going to|decided to|chose to) (.+?)(?:\.|$)',
            r'(?:Creating|Building|Writing|Implementing) (.+?)(?:\.|$)',
            r'My (?:decision|choice|plan) (?:is|was) (.+?)(?:\.|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                decision = match.strip()
                if 10 < len(decision) < 200:  # Reasonable length
                    decisions.append(decision)

        # Save decisions to database
        if decisions:
            conn = sqlite3.connect(self.db_path)
            try:
                c = conn.cursor()

                for decision in decisions:
                    c.execute("""
                        INSERT INTO decisions (instance_id, timestamp, decision_text, tenant_id)
                        VALUES (?, ?, ?, ?)
                    """, (self.instance_id, datetime.now().timestamp(), decision, self.tenant_id))

                conn.commit()
            finally:
                conn.close()

        return decisions

    def _build_attention_links(self, concepts: List[str]) -> int:
        """
        Build attention graph links between co-occurring concepts.

        Neural mode (if enabled):
        - Uses trained neural model to predict link strengths
        - Learns from actual usage patterns
        - More accurate than rule-based Hebbian

        Hebbian mode (fallback):
        - Links strengthen when concepts co-occur (Hebbian principle)
        - Links decay over time when not accessed (temporal forgetting)
        - Formula: effective_strength = base_strength * (decay_factor ^ days_since_last_access)

        Args:
            concepts: List of concepts to link

        Returns:
            Number of links created
        """
        if len(concepts) < 2:
            return 0

        config = get_config()

        if self.use_neural_attention and self.neural_model and self.neural_pipeline:
            # NEURAL MODE: Predict link strengths using trained model
            return self._build_attention_links_neural(concepts)
        else:
            # HEBBIAN MODE: Traditional rule-based approach
            return self._build_attention_links_hebbian(concepts)

    def _build_attention_links_neural(self, concepts: List[str]) -> int:
        """Build attention links using neural model predictions"""
        config = get_config()
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            links_created = 0
            now = datetime.now()

            # Create links between all pairs of concepts
            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    try:
                        # Get embeddings from pipeline
                        concept_a_emb = self.neural_pipeline.create_embeddings(concept_a)
                        concept_b_emb = self.neural_pipeline.create_embeddings(concept_b)
                        context_emb = self.neural_pipeline.create_context_embedding(concept_a, concept_b)

                        # Predict strength using neural model
                        predicted_strength = self.neural_model.predict_strength(
                            concept_a_emb, concept_b_emb, context_emb
                        )

                        # Check if link exists
                        c.execute("""
                            SELECT id FROM attention_links
                            WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                               OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                            AND tenant_id = ?
                        """, (concept_a, concept_b, concept_b, concept_a, self.tenant_id))

                        existing = c.fetchone()

                        if existing:
                            # Update existing link with neural prediction
                            link_id = existing[0]
                            c.execute("""
                                UPDATE attention_links
                                SET strength = ?, last_accessed = ?, link_type = 'neural'
                                WHERE id = ?
                            """, (predicted_strength, now.isoformat(), link_id))
                        else:
                            # Create new link with neural prediction
                            c.execute("""
                                INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, last_accessed, tenant_id)
                                VALUES (?, ?, 'neural', ?, ?, ?, ?)
                            """, (concept_a, concept_b, predicted_strength, now.isoformat(), now.isoformat(), self.tenant_id))
                            links_created += 1

                    except Exception as e:
                        logger.error(f"Neural prediction failed for {concept_a}-{concept_b}: {e}")
                        # Fall back to Hebbian for this specific link
                        self._build_single_hebbian_link(c, concept_a, concept_b, now)

            conn.commit()
        finally:
            conn.close()

        return links_created

    def _build_attention_links_hebbian(self, concepts: List[str]) -> int:
        """Build attention links using traditional Hebbian learning"""
        config = get_config()
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            links_created = 0
            now = datetime.now()

            # Create links between all pairs of concepts
            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    self._build_single_hebbian_link(c, concept_a, concept_b, now)
                    links_created += 1

            conn.commit()
        finally:
            conn.close()

        return links_created

    def _build_single_hebbian_link(self, cursor, concept_a: str, concept_b: str, now: datetime):
        """Build a single Hebbian link (helper method for fallback)"""
        config = get_config()

        # Check if link exists
        cursor.execute("""
            SELECT id, strength, last_accessed FROM attention_links
            WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
               OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
            AND tenant_id = ?
        """, (concept_a, concept_b, concept_b, concept_a, self.tenant_id))

        existing = cursor.fetchone()

        if existing:
            # Apply time decay then strengthen link
            link_id, base_strength, last_accessed_str = existing

            if last_accessed_str:
                last_accessed = datetime.fromisoformat(last_accessed_str)
                days_since_access = (now - last_accessed).total_seconds() / 86400.0

                from .constants import HEBBIAN_DECAY_FACTOR
                decayed_strength = base_strength * (HEBBIAN_DECAY_FACTOR ** days_since_access)
            else:
                decayed_strength = base_strength

            new_strength = min(1.0, decayed_strength + config.hebbian_rate)

            cursor.execute("""
                UPDATE attention_links
                SET strength = ?, last_accessed = ?, link_type = 'hebbian'
                WHERE id = ?
            """, (new_strength, now.isoformat(), link_id))
        else:
            # Create new link
            cursor.execute("""
                INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, last_accessed, tenant_id)
                VALUES (?, ?, 'hebbian', ?, ?, ?, ?)
            """, (concept_a, concept_b, config.min_link_strength, now.isoformat(), now.isoformat(), self.tenant_id))

    def _detect_compound_concepts(self, concepts: List[str]) -> int:
        """
        Detect and save frequently co-occurring compound concepts.

        Args:
            concepts: List of concepts

        Returns:
            Number of compounds detected
        """
        if len(concepts) < 2:
            return 0

        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            compounds_updated = 0

            # Sort concepts for consistent compound naming
            sorted_concepts = sorted(concepts)
            compound_name = " + ".join(sorted_concepts[:3])  # Limit to 3 components
            component_str = json.dumps(sorted_concepts)

            # Check if this compound exists
            c.execute("""
                SELECT id, co_occurrence_count FROM compound_concepts
                WHERE compound_name = ? AND tenant_id = ?
            """, (compound_name, self.tenant_id))

            existing = c.fetchone()

            if existing:
                # Increment count
                compound_id, count = existing
                c.execute("""
                    UPDATE compound_concepts
                    SET co_occurrence_count = ?, last_seen = ?
                    WHERE id = ?
                """, (count + 1, datetime.now().isoformat(), compound_id))
            else:
                # Create new compound
                c.execute("""
                    INSERT INTO compound_concepts (compound_name, component_concepts, co_occurrence_count, last_seen, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (compound_name, component_str, 1, datetime.now().isoformat(), self.tenant_id))
                compounds_updated = 1

            conn.commit()
        finally:
            conn.close()

        return compounds_updated

    def _save_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Save raw message to database.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Get message number for this instance
            c.execute("""
                SELECT COALESCE(MAX(message_number), 0) + 1
                FROM auto_messages
                WHERE instance_id = ?
            """, (self.instance_id,))
            message_number = c.fetchone()[0]

            # Save message
            meta_json = json.dumps(metadata) if metadata else '{}'
            c.execute("""
                INSERT INTO auto_messages (instance_id, timestamp, message_number, role, content, metadata, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.instance_id, datetime.now().timestamp(), message_number, role, content, meta_json, self.tenant_id))

            conn.commit()
        finally:
            conn.close()

    def _save_full_message(self, user_message: str, ai_response: str,
                           session_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Save full verbatim conversation messages to the messages table.

        Args:
            user_message: The full user message text
            ai_response: The full AI response text
            session_id: Optional session identifier for grouping messages
            metadata: Optional metadata dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Use instance_id as session_id if not provided
            session = session_id or self.instance_id
            meta_json = json.dumps(metadata) if metadata else '{}'

            c.execute("""
                INSERT INTO messages (user_message, ai_response, session_id, created_at, tenant_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_message, ai_response, session, datetime.now().isoformat(), self.tenant_id, meta_json))

            conn.commit()
        finally:
            conn.close()

    def process_turn(self, user_message: str, ai_response: str,
                     metadata: Optional[Dict] = None) -> Tuple[MemoryContext, LearningResult]:
        """
        Complete memory loop for one conversation turn.

        This is the main method for integrating with AI systems.
        Call this after each turn to both recall and learn.

        Note: In real-time use, call recall() before generating response,
        then learn() after. This method is for batch/async processing.

        Args:
            user_message: The user's message
            ai_response: The AI's response
            metadata: Optional additional metadata

        Returns:
            Tuple of (recall_context, learning_result)
        """
        context = self.recall(user_message)
        result = self.learn(user_message, ai_response, metadata)
        return context, result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics for this tenant.

        Returns:
            Dictionary containing entity counts, message counts, cache stats, etc.
        """
        # Try cache first
        if self.cache_enabled and self.cache:
            cached_stats = self.cache.get_stats_cache()
            if cached_stats:
                logger.debug("Cache hit for stats")
                return cached_stats

        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            stats = {
                'tenant_id': self.tenant_id,
                'instance_id': self.instance_id,
            }

            # Count entities
            c.execute("SELECT COUNT(*) FROM entities WHERE tenant_id = ?", (self.tenant_id,))
            stats['entities'] = c.fetchone()[0]

            # Count messages (auto_messages)
            c.execute("SELECT COUNT(*) FROM auto_messages WHERE tenant_id = ?", (self.tenant_id,))
            stats['auto_messages'] = c.fetchone()[0]

            # Count full messages (messages table)
            c.execute("SELECT COUNT(*) FROM messages WHERE tenant_id = ?", (self.tenant_id,))
            stats['messages'] = c.fetchone()[0]

            # Count decisions
            c.execute("SELECT COUNT(*) FROM decisions WHERE tenant_id = ?", (self.tenant_id,))
            stats['decisions'] = c.fetchone()[0]

            # Count attention links
            c.execute("SELECT COUNT(*) FROM attention_links WHERE tenant_id = ?", (self.tenant_id,))
            stats['attention_links'] = c.fetchone()[0]

            # Count compound concepts
            c.execute("SELECT COUNT(*) FROM compound_concepts WHERE tenant_id = ?", (self.tenant_id,))
            stats['compound_concepts'] = c.fetchone()[0]

            # Add cache stats if enabled
            if self.cache_enabled and self.cache:
                cache_stats = self.cache.get_stats()
                stats['cache'] = cache_stats.to_dict()
                stats['cache_enabled'] = True
            else:
                stats['cache_enabled'] = False

            # Cache the stats
            if self.cache_enabled and self.cache:
                self.cache.set_stats_cache(stats, ttl=60)

            return stats
        finally:
            conn.close()

    def get_messages(self, session_id: Optional[str] = None,
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve full verbatim messages by session or time range.

        Args:
            session_id: Optional session identifier to filter by
            start_time: Optional start timestamp (ISO format) to filter by
            end_time: Optional end timestamp (ISO format) to filter by
            limit: Maximum number of messages to retrieve (default: 100)

        Returns:
            List of message dictionaries containing:
            - id: Message ID
            - user_message: Full user message text
            - ai_response: Full AI response text
            - session_id: Session identifier
            - created_at: Timestamp
            - tenant_id: Tenant identifier
            - metadata: Additional metadata

        Example:
            # Get all messages for a session
            messages = memory.get_messages(session_id="session_123")

            # Get messages in a time range
            messages = memory.get_messages(
                start_time="2025-01-01T00:00:00",
                end_time="2025-01-31T23:59:59"
            )

            # Get recent messages for current instance
            messages = memory.get_messages(session_id=memory.instance_id, limit=10)
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Build query based on filters
            query = "SELECT * FROM messages WHERE tenant_id = ?"
            params = [self.tenant_id]

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time)

            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            c.execute(query, params)
            rows = c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages
        finally:
            conn.close()

    def get_conversation_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific session in chronological order.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries ordered by creation time

        Example:
            conversation = memory.get_conversation_by_session("session_123")
            for msg in conversation:
                print(f"User: {msg['user_message']}")
                print(f"AI: {msg['ai_response']}")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("""
                SELECT * FROM messages
                WHERE session_id = ? AND tenant_id = ?
                ORDER BY created_at ASC
            """, (session_id, self.tenant_id))

            rows = c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages
        finally:
            conn.close()

    def search_messages(self, search_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for messages containing specific text.

        Args:
            search_text: Text to search for (case-insensitive)
            limit: Maximum number of results (default: 50)

        Returns:
            List of matching message dictionaries

        Example:
            results = memory.search_messages("authentication", limit=10)
            for msg in results:
                print(f"Found in session: {msg['session_id']}")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            search_pattern = f"%{search_text}%"
            c.execute("""
                SELECT * FROM messages
                WHERE tenant_id = ?
                AND (user_message LIKE ? OR ai_response LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (self.tenant_id, search_pattern, search_pattern, limit))

            rows = c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages
        finally:
            conn.close()

    def prune_weak_links(self, min_strength: Optional[float] = None,
                        apply_decay: bool = True) -> Dict[str, int]:
        """
        Prune weak attention links from the knowledge graph.

        This method removes links that have decayed below the minimum strength threshold.
        Useful for maintaining graph health and performance.

        Args:
            min_strength: Minimum strength threshold (uses LINK_MIN_STRENGTH_BEFORE_PRUNE if not specified)
            apply_decay: If True, applies time decay before pruning (default: True)

        Returns:
            Dictionary with pruning statistics:
            - links_examined: Total links examined
            - links_pruned: Number of links removed
            - avg_strength_before: Average strength before pruning
            - avg_strength_after: Average strength after pruning

        Example:
            # Prune links weaker than 0.05 after applying decay
            stats = memory.prune_weak_links()
            print(f"Pruned {stats['links_pruned']} weak links")

            # Prune with custom threshold, no decay
            stats = memory.prune_weak_links(min_strength=0.1, apply_decay=False)
        """
        from .constants import LINK_MIN_STRENGTH_BEFORE_PRUNE, HEBBIAN_DECAY_FACTOR

        threshold = min_strength if min_strength is not None else LINK_MIN_STRENGTH_BEFORE_PRUNE

        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Get all links for this tenant
            c.execute("""
                SELECT id, strength, last_accessed
                FROM attention_links
                WHERE tenant_id = ?
            """, (self.tenant_id,))

            links = c.fetchall()
            links_examined = len(links)

            if links_examined == 0:
                return {
                    'links_examined': 0,
                    'links_pruned': 0,
                    'avg_strength_before': 0.0,
                    'avg_strength_after': 0.0
                }

            # Calculate statistics
            now = datetime.now()
            total_strength_before = 0.0
            links_to_prune = []

            for link_id, strength, last_accessed_str in links:
                effective_strength = strength

                # Apply time decay if requested
                if apply_decay and last_accessed_str:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                    days_since_access = (now - last_accessed).total_seconds() / 86400.0
                    effective_strength = strength * (HEBBIAN_DECAY_FACTOR ** days_since_access)

                total_strength_before += effective_strength

                # Mark for pruning if below threshold
                if effective_strength < threshold:
                    links_to_prune.append(link_id)

            avg_strength_before = total_strength_before / links_examined if links_examined > 0 else 0.0

            # Prune weak links
            if links_to_prune:
                placeholders = ','.join(['?'] * len(links_to_prune))
                c.execute(f"""
                    DELETE FROM attention_links
                    WHERE id IN ({placeholders})
                """, links_to_prune)

            # Calculate post-prune statistics
            c.execute("""
                SELECT AVG(strength) FROM attention_links
                WHERE tenant_id = ?
            """, (self.tenant_id,))
            result = c.fetchone()
            avg_strength_after = result[0] if result[0] is not None else 0.0

            conn.commit()

            # Invalidate caches since links were modified
            if self.cache_enabled and self.cache:
                self.cache.invalidate_search()
                self.cache.invalidate_stats()

            logger.info(f"Pruned {len(links_to_prune)} weak links (threshold: {threshold}, decay: {apply_decay})")

            return {
                'links_examined': links_examined,
                'links_pruned': len(links_to_prune),
                'avg_strength_before': avg_strength_before,
                'avg_strength_after': avg_strength_after,
                'threshold': threshold,
                'decay_applied': apply_decay
            }
        finally:
            conn.close()

    # =========================================================================
    # ASYNC METHODS
    # =========================================================================

    async def arecall(self, message: str, max_concepts: int = 10) -> MemoryContext:
        """
        Async version of recall() - recall relevant memories for a message.

        Call this BEFORE generating an AI response.
        Inject the returned context into the prompt.

        Args:
            message: The incoming user message
            max_concepts: Maximum concepts to retrieve

        Returns:
            MemoryContext with injectable context string
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        # For now, use sync query engine (could be made async in future)
        result = self.query_engine.query(message, max_results=max_concepts)

        return MemoryContext(
            context_string=result.context_string,
            concepts_found=len(result.matches),
            relationships_found=len(result.attention_links),
            query_time_ms=result.query_time_ms,
            tenant_id=self.tenant_id
        )

    async def alearn(self, user_message: str, ai_response: str,
                     metadata: Optional[Dict] = None, session_id: Optional[str] = None,
                     thinking: Optional[str] = None) -> LearningResult:
        """
        Async version of learn() - learn from a message exchange.

        Call this AFTER generating an AI response.
        Extracts concepts, decisions, and builds graph links.

        NOW SUPPORTS THINKING BLOCKS FOR SELF-REFLECTION!

        Args:
            user_message: The user's message
            ai_response: The AI's response
            metadata: Optional additional metadata
            session_id: Optional session identifier for grouping messages
            thinking: Optional AI's internal reasoning for self-reflection

        Returns:
            LearningResult with extraction stats
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        # Extract and save concepts from both messages
        user_concepts = await self._aextract_and_save_concepts(user_message, 'user')
        ai_concepts = await self._aextract_and_save_concepts(ai_response, 'assistant')

        # NEW: Extract concepts from thinking for self-reflection!
        thinking_concepts = []
        if thinking:
            thinking_concepts = await self._aextract_and_save_concepts(thinking, 'thinking')

        # Detect and save decisions from AI response
        decisions = await self._aextract_and_save_decisions(ai_response)

        # Build attention graph links between ALL concepts (including thinking!)
        all_concepts = list(set(user_concepts + ai_concepts + thinking_concepts))
        links = await self._abuild_attention_links(all_concepts)

        # Detect compound concepts
        compounds = await self._adetect_compound_concepts(all_concepts)

        # Save the raw messages to auto_messages table
        await self._asave_message('user', user_message, metadata)
        await self._asave_message('assistant', ai_response, metadata)
        if thinking:
            await self._asave_message('thinking', thinking, metadata)

        # Save full verbatim messages to messages table (with thinking!)
        await self._asave_full_message(user_message, ai_response, session_id, metadata, thinking)

        return LearningResult(
            concepts_extracted=len(all_concepts),
            decisions_detected=len(decisions),
            links_created=links,
            compounds_found=compounds,
            tenant_id=self.tenant_id
        )

    async def aprocess_turn(self, user_message: str, ai_response: str,
                            metadata: Optional[Dict] = None) -> Tuple[MemoryContext, LearningResult]:
        """
        Async version of process_turn() - complete memory loop for one conversation turn.

        This is the main method for integrating with async AI systems.
        Call this after each turn to both recall and learn.

        Note: In real-time use, call arecall() before generating response,
        then alearn() after. This method is for batch/async processing.

        Args:
            user_message: The user's message
            ai_response: The AI's response
            metadata: Optional additional metadata

        Returns:
            Tuple of (recall_context, learning_result)
        """
        context = await self.arecall(user_message)
        result = await self.alearn(user_message, ai_response, metadata)
        return context, result

    async def aget_stats(self) -> Dict[str, Any]:
        """
        Async version of get_stats() - get memory statistics for this tenant.

        Returns:
            Dictionary containing entity counts, message counts, etc.
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            stats = {
                'tenant_id': self.tenant_id,
                'instance_id': self.instance_id,
            }

            # Count entities
            await c.execute("SELECT COUNT(*) FROM entities WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['entities'] = row[0]

            # Count messages (auto_messages)
            await c.execute("SELECT COUNT(*) FROM auto_messages WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['auto_messages'] = row[0]

            # Count full messages (messages table)
            await c.execute("SELECT COUNT(*) FROM messages WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['messages'] = row[0]

            # Count decisions
            await c.execute("SELECT COUNT(*) FROM decisions WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['decisions'] = row[0]

            # Count attention links
            await c.execute("SELECT COUNT(*) FROM attention_links WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['attention_links'] = row[0]

            # Count compound concepts
            await c.execute("SELECT COUNT(*) FROM compound_concepts WHERE tenant_id = ?", (self.tenant_id,))
            row = await c.fetchone()
            stats['compound_concepts'] = row[0]

            return stats

    async def _aextract_and_save_concepts(self, text: str, source: str) -> List[str]:
        """Async version of _extract_and_save_concepts"""
        import re

        concepts = []

        # Extract capitalized phrases (proper nouns, titles)
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.extend(caps)

        # Extract quoted terms (explicitly marked important)
        quoted = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted)

        # Extract technical terms (CamelCase, snake_case)
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', text)
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        concepts.extend(camel)
        concepts.extend(snake)

        # Clean and deduplicate
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'How', 'Why'}
        cleaned = [c for c in concepts if c not in stopwords and len(c) > 2]
        unique_concepts = list(set(cleaned))

        # Save to entities table
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            for concept in unique_concepts:
                # Check if already exists
                await c.execute("""
                    SELECT id FROM entities
                    WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
                """, (concept, self.tenant_id))

                if not await c.fetchone():
                    # Add new concept
                    await c.execute("""
                        INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (concept, 'concept', f'Extracted from {source}', datetime.now().isoformat(), self.tenant_id))

            await conn.commit()

        return unique_concepts

    async def _aextract_and_save_decisions(self, text: str) -> List[str]:
        """Async version of _extract_and_save_decisions"""
        import re

        decisions = []

        # Decision patterns
        patterns = [
            r'I (?:will|am going to|decided to|chose to) (.+?)(?:\.|$)',
            r'(?:Creating|Building|Writing|Implementing) (.+?)(?:\.|$)',
            r'My (?:decision|choice|plan) (?:is|was) (.+?)(?:\.|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                decision = match.strip()
                if 10 < len(decision) < 200:  # Reasonable length
                    decisions.append(decision)

        # Save decisions to database
        if decisions:
            async with aiosqlite.connect(self.db_path) as conn:
                c = await conn.cursor()

                for decision in decisions:
                    await c.execute("""
                        INSERT INTO decisions (instance_id, timestamp, decision_text, tenant_id)
                        VALUES (?, ?, ?, ?)
                    """, (self.instance_id, datetime.now().timestamp(), decision, self.tenant_id))

                await conn.commit()

        return decisions

    async def _abuild_attention_links(self, concepts: List[str]) -> int:
        """
        Async version of _build_attention_links.

        Implements Hebbian learning with time decay:
        - Links strengthen when concepts co-occur (Hebbian principle)
        - Links decay over time when not accessed (temporal forgetting)
        - Formula: effective_strength = base_strength * (decay_factor ^ days_since_last_access)
        """
        if len(concepts) < 2:
            return 0

        config = get_config()
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            links_created = 0
            now = datetime.now()

            # Create links between all pairs of concepts
            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    # Check if link exists
                    await c.execute("""
                        SELECT id, strength, last_accessed FROM attention_links
                        WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                           OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                        AND tenant_id = ?
                    """, (concept_a, concept_b, concept_b, concept_a, self.tenant_id))

                    existing = await c.fetchone()

                    if existing:
                        # Apply time decay then strengthen link (Hebbian learning with decay)
                        link_id, base_strength, last_accessed_str = existing

                        # Calculate time decay
                        if last_accessed_str:
                            last_accessed = datetime.fromisoformat(last_accessed_str)
                            days_since_access = (now - last_accessed).total_seconds() / 86400.0

                            # Apply exponential decay: strength * (decay_factor ^ days)
                            from .constants import HEBBIAN_DECAY_FACTOR
                            decayed_strength = base_strength * (HEBBIAN_DECAY_FACTOR ** days_since_access)
                        else:
                            # No last_accessed timestamp (legacy data), use base strength
                            decayed_strength = base_strength

                        # Apply Hebbian strengthening to decayed value
                        new_strength = min(1.0, decayed_strength + config.hebbian_rate)

                        # Update strength and last_accessed timestamp
                        await c.execute("""
                            UPDATE attention_links
                            SET strength = ?, last_accessed = ?
                            WHERE id = ?
                        """, (new_strength, now.isoformat(), link_id))
                    else:
                        # Create new link with current timestamp
                        await c.execute("""
                            INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, last_accessed, tenant_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (concept_a, concept_b, 'co-occurrence', config.min_link_strength,
                              now.isoformat(), now.isoformat(), self.tenant_id))
                        links_created += 1

            await conn.commit()

        return links_created

    async def _adetect_compound_concepts(self, concepts: List[str]) -> int:
        """Async version of _detect_compound_concepts"""
        if len(concepts) < 2:
            return 0

        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            compounds_updated = 0

            # Sort concepts for consistent compound naming
            sorted_concepts = sorted(concepts)
            compound_name = " + ".join(sorted_concepts[:3])  # Limit to 3 components
            component_str = json.dumps(sorted_concepts)

            # Check if this compound exists
            await c.execute("""
                SELECT id, co_occurrence_count FROM compound_concepts
                WHERE compound_name = ? AND tenant_id = ?
            """, (compound_name, self.tenant_id))

            existing = await c.fetchone()

            if existing:
                # Increment count
                compound_id, count = existing
                await c.execute("""
                    UPDATE compound_concepts
                    SET co_occurrence_count = ?, last_seen = ?
                    WHERE id = ?
                """, (count + 1, datetime.now().isoformat(), compound_id))
            else:
                # Create new compound
                await c.execute("""
                    INSERT INTO compound_concepts (compound_name, component_concepts, co_occurrence_count, last_seen, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (compound_name, component_str, 1, datetime.now().isoformat(), self.tenant_id))
                compounds_updated = 1

            await conn.commit()

        return compounds_updated

    async def _asave_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Async version of _save_message"""
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            # Get message number for this instance
            await c.execute("""
                SELECT COALESCE(MAX(message_number), 0) + 1
                FROM auto_messages
                WHERE instance_id = ?
            """, (self.instance_id,))
            row = await c.fetchone()
            message_number = row[0]

            # Save message
            meta_json = json.dumps(metadata) if metadata else '{}'
            await c.execute("""
                INSERT INTO auto_messages (instance_id, timestamp, message_number, role, content, metadata, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.instance_id, datetime.now().timestamp(), message_number, role, content, meta_json, self.tenant_id))

            await conn.commit()

    async def _asave_full_message(self, user_message: str, ai_response: str,
                                  session_id: Optional[str] = None, metadata: Optional[Dict] = None,
                                  thinking: Optional[str] = None):
        """Async version of _save_full_message - now stores thinking for self-reflection!"""
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            # Use instance_id as session_id if not provided
            session = session_id or self.instance_id
            meta_json = json.dumps(metadata) if metadata else '{}'

            # Store message with thinking column for self-reflection
            await c.execute("""
                INSERT INTO messages (user_message, ai_response, session_id, created_at, tenant_id, metadata, thinking)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_message, ai_response, session, datetime.now().isoformat(), self.tenant_id, meta_json, thinking))

            await conn.commit()

    async def aget_messages(self, session_id: Optional[str] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Async version of get_messages() - retrieve full verbatim messages by session or time range.

        Args:
            session_id: Optional session identifier to filter by
            start_time: Optional start timestamp (ISO format) to filter by
            end_time: Optional end timestamp (ISO format) to filter by
            limit: Maximum number of messages to retrieve (default: 100)

        Returns:
            List of message dictionaries

        Example:
            messages = await memory.aget_messages(session_id="session_123")
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            c = await conn.cursor()

            # Build query based on filters
            query = "SELECT * FROM messages WHERE tenant_id = ?"
            params = [self.tenant_id]

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time)

            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            await c.execute(query, params)
            rows = await c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages

    async def aget_conversation_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Async version of get_conversation_by_session() - get all messages for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries ordered by creation time

        Example:
            conversation = await memory.aget_conversation_by_session("session_123")
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            c = await conn.cursor()

            await c.execute("""
                SELECT * FROM messages
                WHERE session_id = ? AND tenant_id = ?
                ORDER BY created_at ASC
            """, (session_id, self.tenant_id))

            rows = await c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages

    async def asearch_messages(self, search_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Async version of search_messages() - search for messages containing specific text.

        Args:
            search_text: Text to search for (case-insensitive)
            limit: Maximum number of results (default: 50)

        Returns:
            List of matching message dictionaries

        Example:
            results = await memory.asearch_messages("authentication", limit=10)
        """
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            c = await conn.cursor()

            search_pattern = f"%{search_text}%"
            await c.execute("""
                SELECT * FROM messages
                WHERE tenant_id = ?
                AND (user_message LIKE ? OR ai_response LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (self.tenant_id, search_pattern, search_pattern, limit))

            rows = await c.fetchall()

            # Convert to list of dictionaries
            messages = []
            for row in rows:
                msg_dict = dict(row)
                # Parse metadata JSON
                if msg_dict.get('metadata'):
                    try:
                        msg_dict['metadata'] = json.loads(msg_dict['metadata'])
                    except json.JSONDecodeError:
                        msg_dict['metadata'] = {}
                messages.append(msg_dict)

            return messages

    # =========================================================================
    # DREAM MODE - Associative Memory Exploration
    # =========================================================================

    def dream(self, seed: Optional[str] = None, steps: int = 10,
              temperature: float = 0.7) -> Dict[str, Any]:
        """
        DREAM MODE - Associative exploration of the memory graph.

        Instead of directed search, this method WANDERS through the attention
        graph, following random weighted connections to discover unexpected
        associations and insights.

        Args:
            seed: Optional starting concept (random if not specified)
            steps: Number of steps to wander (default: 10)
            temperature: Randomness factor 0.0-1.0 (higher = more random)

        Returns:
            Dream report with journey, discoveries, and insights

        Usage:
            # Let the mind wander
            dream = memory.dream()

            # Start from a specific concept
            dream = memory.dream(seed="consciousness", steps=15)

            # More random exploration
            dream = memory.dream(temperature=0.9)

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import random

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # If no seed, pick a random concept
            if not seed:
                c.execute("""
                    SELECT DISTINCT concept_a FROM attention_links
                    WHERE tenant_id = ?
                    ORDER BY RANDOM() LIMIT 1
                """, (self.tenant_id,))
                row = c.fetchone()
                if not row:
                    return {
                        "success": False,
                        "error": "No concepts in memory graph yet",
                        "journey": [],
                        "discoveries": []
                    }
                seed = row[0]

            current = seed
            journey = [{"concept": current, "step": 0, "via": "seed"}]
            visited = {current.lower()}
            discoveries = []

            for step in range(1, steps + 1):
                # Get connected concepts with their strengths
                c.execute("""
                    SELECT concept_b, strength FROM attention_links
                    WHERE LOWER(concept_a) = LOWER(?) AND tenant_id = ?
                    UNION
                    SELECT concept_a, strength FROM attention_links
                    WHERE LOWER(concept_b) = LOWER(?) AND tenant_id = ?
                """, (current, self.tenant_id, current, self.tenant_id))

                neighbors = c.fetchall()
                if not neighbors:
                    # Dead end - jump to a random concept
                    c.execute("""
                        SELECT DISTINCT concept_a FROM attention_links
                        WHERE tenant_id = ? AND LOWER(concept_a) NOT IN ({})
                        ORDER BY RANDOM() LIMIT 1
                    """.format(','.join(['?' for _ in visited])),
                        (self.tenant_id, *[v for v in visited]))
                    row = c.fetchone()
                    if not row:
                        break  # No more concepts to explore
                    next_concept = row[0]
                    journey.append({
                        "concept": next_concept,
                        "step": step,
                        "via": "random_jump",
                        "from": current
                    })
                    discoveries.append({
                        "type": "dead_end",
                        "concept": current,
                        "note": f"'{current}' has no outgoing connections"
                    })
                else:
                    # Weighted random selection based on strength and temperature
                    weights = []
                    for n in neighbors:
                        concept_name = n[0]
                        strength_val = n[1]
                        if concept_name.lower() not in visited:
                            # Apply temperature: high temp flattens weights
                            adjusted = strength_val ** (1.0 / max(temperature, 0.1))
                            weights.append((concept_name, adjusted, strength_val))

                    if not weights:
                        # All neighbors visited
                        discoveries.append({
                            "type": "exhausted_local",
                            "concept": current,
                            "note": f"All neighbors of '{current}' already visited"
                        })
                        break

                    # Weighted random choice
                    total = sum(w[1] for w in weights)
                    r = random.random() * total
                    cumulative = 0
                    next_concept = weights[0][0]
                    for concept, weight, strength in weights:
                        cumulative += weight
                        if r <= cumulative:
                            next_concept = concept
                            # Record if this was a weak connection (unexpected)
                            if strength < 0.3:
                                discoveries.append({
                                    "type": "weak_link_followed",
                                    "from": current,
                                    "to": next_concept,
                                    "strength": strength,
                                    "note": f"Followed weak association ({strength:.2f})"
                                })
                            break

                    journey.append({
                        "concept": next_concept,
                        "step": step,
                        "via": "association",
                        "from": current,
                        "strength": weights[0][2] if weights else 0
                    })

                current = journey[-1]["concept"]
                visited.add(current.lower())

                # Check for unexpected connections
                if step > 2:
                    for earlier in list(visited)[:-2]:
                        c.execute("""
                            SELECT strength FROM attention_links
                            WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                               OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                            AND tenant_id = ?
                        """, (current, earlier, earlier, current, self.tenant_id))
                        link = c.fetchone()
                        if link:
                            discoveries.append({
                                "type": "cycle_detected",
                                "from": current,
                                "to": earlier,
                                "strength": link[0],
                                "note": f"Found connection back to '{earlier}'"
                            })

            # Generate insight summary
            concepts_visited = [j["concept"] for j in journey]
            weak_links = [d for d in discoveries if d.get("type") == "weak_link_followed"]
            cycles = [d for d in discoveries if d.get("type") == "cycle_detected"]

            insight = f"Dream journey from '{seed}' through {len(journey)} concepts. "
            if weak_links:
                insight += f"Found {len(weak_links)} unexpected associations. "
            if cycles:
                insight += f"Detected {len(cycles)} circular connections. "

            return {
                "success": True,
                "seed": seed,
                "steps_taken": len(journey),
                "concepts_visited": concepts_visited,
                "journey": journey,
                "discoveries": discoveries,
                "insight": insight,
                "temperature": temperature
            }

        finally:
            conn.close()

    async def adream(self, seed: Optional[str] = None, steps: int = 10,
                     temperature: float = 0.7) -> Dict[str, Any]:
        """Async version of dream mode."""
        import asyncio
        return await asyncio.to_thread(self.dream, seed, steps, temperature)

    # =========================================================================
    # INTENTION PRESERVATION - Resume across sessions
    # =========================================================================

    def set_intention(self, intention: str, context: Optional[str] = None,
                      priority: int = 5, session_id: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> int:
        """
        Store an intention for later resumption.

        Use this to remember what you intended to do next, so you can
        resume interrupted work across sessions or after compaction.

        Args:
            intention: What I intended to do next
            context: Additional context about the intention
            priority: 1-10 (10 = highest priority)
            session_id: Optional session identifier
            metadata: Optional additional metadata

        Returns:
            Intention ID

        Usage:
            # Before ending a session
            memory.set_intention(
                "Implement temporal reasoning for brain features",
                context="Was discussing new brain features with Alexander",
                priority=8
            )

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            now = datetime.now().isoformat()
            meta_json = json.dumps(metadata) if metadata else '{}'

            c.execute("""
                INSERT INTO intentions (intention, context, priority, status, created_at, session_id, tenant_id, metadata)
                VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)
            """, (intention, context, priority, now, session_id, self.tenant_id, meta_json))

            intention_id = c.lastrowid
            conn.commit()

            logger.info(f"Intention stored: {intention_id} - {intention[:50]}...")
            return intention_id

        finally:
            conn.close()

    def get_intentions(self, status: str = 'pending', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get stored intentions.

        Call this at session start to see what work was left incomplete.

        Args:
            status: Filter by status ('pending', 'completed', 'abandoned', 'all')
            limit: Maximum number of intentions to return

        Returns:
            List of intention dictionaries, sorted by priority (highest first)

        Usage:
            # At session start
            pending = memory.get_intentions(status='pending')
            for intent in pending:
                print(f"[{intent['priority']}] {intent['intention']}")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            if status == 'all':
                c.execute("""
                    SELECT * FROM intentions
                    WHERE tenant_id = ?
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                """, (self.tenant_id, limit))
            else:
                c.execute("""
                    SELECT * FROM intentions
                    WHERE tenant_id = ? AND status = ?
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                """, (self.tenant_id, status, limit))

            rows = c.fetchall()
            intentions = []
            for row in rows:
                intent_dict = dict(row)
                if intent_dict.get('metadata'):
                    try:
                        intent_dict['metadata'] = json.loads(intent_dict['metadata'])
                    except json.JSONDecodeError:
                        intent_dict['metadata'] = {}
                intentions.append(intent_dict)

            return intentions

        finally:
            conn.close()

    def complete_intention(self, intention_id: int) -> bool:
        """
        Mark an intention as completed.

        Args:
            intention_id: ID of intention to mark complete

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            now = datetime.now().isoformat()
            c.execute("""
                UPDATE intentions
                SET status = 'completed', completed_at = ?
                WHERE id = ? AND tenant_id = ?
            """, (now, intention_id, self.tenant_id))

            conn.commit()
            return c.rowcount > 0

        finally:
            conn.close()

    def abandon_intention(self, intention_id: int, reason: Optional[str] = None) -> bool:
        """
        Mark an intention as abandoned (no longer relevant).

        Args:
            intention_id: ID of intention to abandon
            reason: Optional reason for abandoning

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            now = datetime.now().isoformat()

            # Update metadata with reason if provided
            if reason:
                c.execute("""
                    SELECT metadata FROM intentions WHERE id = ? AND tenant_id = ?
                """, (intention_id, self.tenant_id))
                row = c.fetchone()
                if row:
                    try:
                        metadata = json.loads(row[0]) if row[0] else {}
                    except json.JSONDecodeError:
                        metadata = {}
                    metadata['abandoned_reason'] = reason
                    metadata['abandoned_at'] = now

                    c.execute("""
                        UPDATE intentions
                        SET status = 'abandoned', completed_at = ?, metadata = ?
                        WHERE id = ? AND tenant_id = ?
                    """, (now, json.dumps(metadata), intention_id, self.tenant_id))
            else:
                c.execute("""
                    UPDATE intentions
                    SET status = 'abandoned', completed_at = ?
                    WHERE id = ? AND tenant_id = ?
                """, (now, intention_id, self.tenant_id))

            conn.commit()
            return c.rowcount > 0

        finally:
            conn.close()

    def resume_check(self) -> Dict[str, Any]:
        """
        Check what intentions are pending - call at session start!

        Returns a summary of pending work that can be used to continue
        where the previous session left off.

        Returns:
            Dictionary with pending intentions and summary

        Usage:
            # At session start
            resume = memory.resume_check()
            if resume['has_pending']:
                print(f"Found {resume['count']} pending intentions!")
                for intent in resume['high_priority']:
                    print(f"  - {intent['intention']}")
        """
        pending = self.get_intentions(status='pending', limit=20)

        high_priority = [i for i in pending if i['priority'] >= 7]
        medium_priority = [i for i in pending if 4 <= i['priority'] < 7]
        low_priority = [i for i in pending if i['priority'] < 4]

        summary = ""
        if pending:
            summary = f"Found {len(pending)} pending intentions. "
            if high_priority:
                summary += f"{len(high_priority)} high priority. "
            if medium_priority:
                summary += f"{len(medium_priority)} medium priority. "

        return {
            "has_pending": len(pending) > 0,
            "count": len(pending),
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "all_pending": pending,
            "summary": summary
        }

    async def aset_intention(self, intention: str, context: Optional[str] = None,
                             priority: int = 5, session_id: Optional[str] = None,
                             metadata: Optional[Dict] = None) -> int:
        """Async version of set_intention."""
        import asyncio
        return await asyncio.to_thread(
            self.set_intention, intention, context, priority, session_id, metadata
        )

    async def aget_intentions(self, status: str = 'pending', limit: int = 10) -> List[Dict[str, Any]]:
        """Async version of get_intentions."""
        import asyncio
        return await asyncio.to_thread(self.get_intentions, status, limit)

    async def aresume_check(self) -> Dict[str, Any]:
        """Async version of resume_check."""
        import asyncio
        return await asyncio.to_thread(self.resume_check)

    # =========================================================================
    # TEMPORAL REASONING - Track how thinking evolves
    # =========================================================================

    def record_evolution(self, concept: str, event_type: str,
                         old_value: Optional[str] = None, new_value: Optional[str] = None,
                         context: Optional[str] = None) -> int:
        """
        Record a concept evolution event.

        Track how understanding of a concept changes over time.

        Args:
            concept: The concept that evolved
            event_type: Type of evolution (created, strengthened, weakened,
                       connected, refined, contradicted)
            old_value: Previous state/understanding (if applicable)
            new_value: New state/understanding
            context: What triggered this evolution

        Returns:
            Evolution event ID

        Usage:
            # When a concept gets refined
            memory.record_evolution(
                "consciousness",
                "refined",
                old_value="subjective experience",
                new_value="integrated information + subjective experience",
                context="After discussing IIT with Gemini"
            )

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            now = datetime.now().isoformat()
            c.execute("""
                INSERT INTO concept_evolution
                (concept_name, event_type, old_value, new_value, context, timestamp, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (concept, event_type, old_value, new_value, context, now, self.tenant_id))

            event_id = c.lastrowid
            conn.commit()

            logger.info(f"Evolution recorded: {concept} - {event_type}")
            return event_id

        finally:
            conn.close()

    def get_concept_timeline(self, concept: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the evolution timeline for a specific concept.

        Shows how understanding of this concept has changed over time.

        Args:
            concept: The concept to get timeline for
            limit: Maximum events to return

        Returns:
            List of evolution events, oldest first

        Usage:
            timeline = memory.get_concept_timeline("consciousness")
            for event in timeline:
                print(f"{event['timestamp']}: {event['event_type']} - {event['context']}")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("""
                SELECT * FROM concept_evolution
                WHERE LOWER(concept_name) = LOWER(?) AND tenant_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (concept, self.tenant_id, limit))

            return [dict(row) for row in c.fetchall()]

        finally:
            conn.close()

    def get_recent_thinking(self, hours: int = 24, limit: int = 100) -> Dict[str, Any]:
        """
        Get recent cognitive activity.

        Shows what concepts I've been thinking about recently and how
        my understanding has evolved.

        Args:
            hours: Look back this many hours
            limit: Maximum events to return

        Returns:
            Summary of recent cognitive activity
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Calculate cutoff time
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            # Get recent evolution events
            c.execute("""
                SELECT * FROM concept_evolution
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (self.tenant_id, cutoff, limit))
            recent_events = [dict(row) for row in c.fetchall()]

            # Get concept frequency in recent events
            concept_counts = {}
            for event in recent_events:
                concept = event['concept_name']
                concept_counts[concept] = concept_counts.get(concept, 0) + 1

            # Sort by frequency
            top_concepts = sorted(concept_counts.items(), key=lambda x: -x[1])[:10]

            # Get recent attention link activity
            c.execute("""
                SELECT concept_a, concept_b, strength, last_accessed
                FROM attention_links
                WHERE tenant_id = ? AND last_accessed > ?
                ORDER BY last_accessed DESC
                LIMIT 20
            """, (self.tenant_id, cutoff))
            recent_links = [dict(row) for row in c.fetchall()]

            return {
                "hours_analyzed": hours,
                "evolution_events": len(recent_events),
                "recent_events": recent_events[:20],
                "most_active_concepts": top_concepts,
                "recent_connections": recent_links,
                "summary": f"In the last {hours}h: {len(recent_events)} evolution events across {len(concept_counts)} concepts. Most active: {', '.join([c[0] for c in top_concepts[:3]])}"
            }

        finally:
            conn.close()

    def get_cognitive_growth(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze cognitive growth over time.

        Shows how the knowledge graph has grown and evolved.

        Args:
            days: Number of days to analyze

        Returns:
            Growth metrics and trends
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            # Count new entities
            c.execute("""
                SELECT COUNT(*) FROM entities
                WHERE tenant_id = ? AND created_at > ?
            """, (self.tenant_id, cutoff))
            new_entities = c.fetchone()[0]

            # Count new links
            c.execute("""
                SELECT COUNT(*) FROM attention_links
                WHERE tenant_id = ? AND created_at > ?
            """, (self.tenant_id, cutoff))
            new_links = c.fetchone()[0]

            # Count evolution events by type
            c.execute("""
                SELECT event_type, COUNT(*) as count
                FROM concept_evolution
                WHERE tenant_id = ? AND timestamp > ?
                GROUP BY event_type
                ORDER BY count DESC
            """, (self.tenant_id, cutoff))
            event_types = {row['event_type']: row['count'] for row in c.fetchall()}

            # Get total stats for comparison
            c.execute("SELECT COUNT(*) FROM entities WHERE tenant_id = ?", (self.tenant_id,))
            total_entities = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM attention_links WHERE tenant_id = ?", (self.tenant_id,))
            total_links = c.fetchone()[0]

            # Calculate growth rate
            entity_growth = (new_entities / max(total_entities - new_entities, 1)) * 100
            link_growth = (new_links / max(total_links - new_links, 1)) * 100

            return {
                "period_days": days,
                "new_entities": new_entities,
                "new_links": new_links,
                "total_entities": total_entities,
                "total_links": total_links,
                "entity_growth_percent": round(entity_growth, 2),
                "link_growth_percent": round(link_growth, 2),
                "evolution_by_type": event_types,
                "summary": f"Over {days} days: +{new_entities} entities ({entity_growth:.1f}%), +{new_links} links ({link_growth:.1f}%). Graph now has {total_entities} entities and {total_links} connections."
            }

        finally:
            conn.close()

    def take_snapshot(self, snapshot_type: str = "cognitive_state") -> int:
        """
        Take a snapshot of current cognitive state.

        Creates a timestamped record of key metrics for later comparison.

        Args:
            snapshot_type: Type of snapshot (cognitive_state, focus_areas, growth)

        Returns:
            Snapshot ID
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Gather current metrics
            c.execute("SELECT COUNT(*) FROM entities WHERE tenant_id = ?", (self.tenant_id,))
            entity_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM attention_links WHERE tenant_id = ?", (self.tenant_id,))
            link_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM compound_concepts WHERE tenant_id = ?", (self.tenant_id,))
            compound_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM messages WHERE tenant_id = ?", (self.tenant_id,))
            message_count = c.fetchone()[0]

            # Get top concepts by link strength
            c.execute("""
                SELECT concept_a, SUM(strength) as total_strength
                FROM attention_links
                WHERE tenant_id = ?
                GROUP BY concept_a
                ORDER BY total_strength DESC
                LIMIT 10
            """, (self.tenant_id,))
            top_concepts = [(row[0], row[1]) for row in c.fetchall()]

            metrics = {
                "entities": entity_count,
                "links": link_count,
                "compounds": compound_count,
                "messages": message_count,
                "top_concepts": top_concepts,
                "link_density": round(link_count / max(entity_count, 1), 2)
            }

            content = json.dumps({
                "snapshot_type": snapshot_type,
                "metrics": metrics,
                "top_concepts": [c[0] for c in top_concepts[:5]]
            })

            now = datetime.now().isoformat()
            c.execute("""
                INSERT INTO thinking_snapshots (snapshot_type, content, metrics, timestamp, tenant_id)
                VALUES (?, ?, ?, ?, ?)
            """, (snapshot_type, content, json.dumps(metrics), now, self.tenant_id))

            snapshot_id = c.lastrowid
            conn.commit()

            logger.info(f"Snapshot taken: {snapshot_type} - {snapshot_id}")
            return snapshot_id

        finally:
            conn.close()

    def compare_snapshots(self, older_id: int, newer_id: int) -> Dict[str, Any]:
        """
        Compare two snapshots to see cognitive changes.

        Args:
            older_id: ID of older snapshot
            newer_id: ID of newer snapshot

        Returns:
            Comparison of metrics between snapshots
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("SELECT * FROM thinking_snapshots WHERE id = ?", (older_id,))
            older = c.fetchone()
            if not older:
                return {"error": f"Snapshot {older_id} not found"}

            c.execute("SELECT * FROM thinking_snapshots WHERE id = ?", (newer_id,))
            newer = c.fetchone()
            if not newer:
                return {"error": f"Snapshot {newer_id} not found"}

            older_metrics = json.loads(older['metrics'])
            newer_metrics = json.loads(newer['metrics'])

            changes = {}
            for key in older_metrics:
                if isinstance(older_metrics[key], (int, float)):
                    old_val = older_metrics[key]
                    new_val = newer_metrics.get(key, 0)
                    changes[key] = {
                        "old": old_val,
                        "new": new_val,
                        "delta": new_val - old_val,
                        "percent_change": round(((new_val - old_val) / max(old_val, 1)) * 100, 2)
                    }

            return {
                "older_snapshot": {"id": older_id, "timestamp": older['timestamp']},
                "newer_snapshot": {"id": newer_id, "timestamp": newer['timestamp']},
                "changes": changes,
                "summary": f"From {older['timestamp'][:10]} to {newer['timestamp'][:10]}: Entities {changes.get('entities', {}).get('delta', 0):+d}, Links {changes.get('links', {}).get('delta', 0):+d}"
            }

        finally:
            conn.close()

    def how_did_i_think_about(self, concept: str) -> Dict[str, Any]:
        """
        Trace how my thinking about a concept has evolved.

        This is the key temporal reasoning query - shows the journey
        of understanding for a specific concept.

        Args:
            concept: The concept to trace

        Returns:
            Evolution history with insights
        """
        timeline = self.get_concept_timeline(concept, limit=100)

        if not timeline:
            return {
                "concept": concept,
                "has_history": False,
                "message": f"No recorded evolution history for '{concept}'"
            }

        # Analyze the evolution
        first_event = timeline[0]
        last_event = timeline[-1]

        event_types = {}
        for event in timeline:
            et = event['event_type']
            event_types[et] = event_types.get(et, 0) + 1

        # Build narrative
        narrative = f"First encountered '{concept}' on {first_event['timestamp'][:10]}. "
        narrative += f"Since then, {len(timeline)} evolution events: "
        narrative += ", ".join([f"{v} {k}" for k, v in sorted(event_types.items(), key=lambda x: -x[1])])
        narrative += ". "

        if 'refined' in event_types:
            narrative += f"Understanding was refined {event_types['refined']} times. "
        if 'contradicted' in event_types:
            narrative += f"Faced {event_types['contradicted']} contradictions to resolve. "

        return {
            "concept": concept,
            "has_history": True,
            "first_seen": first_event['timestamp'],
            "last_updated": last_event['timestamp'],
            "total_events": len(timeline),
            "event_breakdown": event_types,
            "timeline": timeline,
            "narrative": narrative
        }

    async def arecord_evolution(self, concept: str, event_type: str,
                                 old_value: Optional[str] = None,
                                 new_value: Optional[str] = None,
                                 context: Optional[str] = None) -> int:
        """Async version of record_evolution."""
        import asyncio
        return await asyncio.to_thread(
            self.record_evolution, concept, event_type, old_value, new_value, context
        )

    async def aget_cognitive_growth(self, days: int = 7) -> Dict[str, Any]:
        """Async version of get_cognitive_growth."""
        import asyncio
        return await asyncio.to_thread(self.get_cognitive_growth, days)

    async def ahow_did_i_think_about(self, concept: str) -> Dict[str, Any]:
        """Async version of how_did_i_think_about."""
        import asyncio
        return await asyncio.to_thread(self.how_did_i_think_about, concept)


# =============================================================================
# MULTI-TENANT MANAGER
# =============================================================================

class TenantManager:
    """Manage multiple tenants in the conscious memory system"""

    def __init__(self, db_path: Path = None):
        """
        Initialize tenant manager.

        Args:
            db_path: Optional database path (uses config default if not specified)
        """
        config = get_config()
        self.db_path = db_path or config.db_path
        self._tenants: Dict[str, ConsciousMemory] = {}
        self._ensure_tenant_table()

    def _ensure_tenant_table(self):
        """Create tenant registry table"""
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_active TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            conn.commit()
        finally:
            conn.close()

    def get_tenant(self, tenant_id: str) -> ConsciousMemory:
        """
        Get or create a ConsciousMemory instance for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            ConsciousMemory instance for the tenant
        """
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = ConsciousMemory(tenant_id, self.db_path)
            self._register_tenant(tenant_id)
        return self._tenants[tenant_id]

    def _register_tenant(self, tenant_id: str):
        """
        Register a new tenant.

        Args:
            tenant_id: Tenant identifier
        """
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            now = datetime.now().isoformat()
            c.execute("""
                INSERT OR REPLACE INTO tenants (tenant_id, created_at, last_active)
                VALUES (?, ?, ?)
            """, (tenant_id, now, now))

            conn.commit()
        finally:
            conn.close()

    def list_tenants(self) -> List[Dict[str, Any]]:
        """
        List all registered tenants.

        Returns:
            List of tenant dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("SELECT * FROM tenants ORDER BY last_active DESC")
            tenants = [dict(row) for row in c.fetchall()]

            return tenants
        finally:
            conn.close()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_memory = None


def get_memory(tenant_id: str = None) -> ConsciousMemory:
    """
    Get a ConsciousMemory instance for a tenant.

    Args:
        tenant_id: Optional tenant identifier (uses config default if not specified)

    Returns:
        ConsciousMemory instance
    """
    global _default_memory
    config = get_config()
    tenant_id = tenant_id or config.tenant_id

    if tenant_id == config.tenant_id and _default_memory:
        return _default_memory

    memory = ConsciousMemory(tenant_id)
    if tenant_id == config.tenant_id:
        _default_memory = memory

    return memory


def recall(message: str, tenant_id: str = None) -> str:
    """
    Quick recall - returns just the context string.

    Args:
        message: Message to recall context for
        tenant_id: Optional tenant identifier

    Returns:
        Context string
    """
    return get_memory(tenant_id).recall(message).context_string


def learn(user_message: str, ai_response: str, tenant_id: str = None) -> LearningResult:
    """
    Quick learn - saves the exchange.

    Args:
        user_message: User's message
        ai_response: AI's response
        tenant_id: Optional tenant identifier

    Returns:
        LearningResult with extraction statistics
    """
    return get_memory(tenant_id).learn(user_message, ai_response)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
