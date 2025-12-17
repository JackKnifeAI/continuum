#!/usr/bin/env python3
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
                    tenant_id TEXT DEFAULT 'default'
                )
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

        Args:
            concepts: List of concepts to link

        Returns:
            Number of links created
        """
        if len(concepts) < 2:
            return 0

        config = get_config()
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            links_created = 0

            # Create links between all pairs of concepts
            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    # Check if link exists
                    c.execute("""
                        SELECT id, strength FROM attention_links
                        WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                           OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                        AND tenant_id = ?
                    """, (concept_a, concept_b, concept_b, concept_a, self.tenant_id))

                    existing = c.fetchone()

                    if existing:
                        # Strengthen existing link (Hebbian learning)
                        link_id, current_strength = existing
                        new_strength = min(1.0, current_strength + config.hebbian_rate)
                        c.execute("""
                            UPDATE attention_links
                            SET strength = ?
                            WHERE id = ?
                        """, (new_strength, link_id))
                    else:
                        # Create new link
                        c.execute("""
                            INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (concept_a, concept_b, 'co-occurrence', config.min_link_strength,
                              datetime.now().isoformat(), self.tenant_id))
                        links_created += 1

            conn.commit()
        finally:
            conn.close()

        return links_created

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
                     metadata: Optional[Dict] = None, session_id: Optional[str] = None) -> LearningResult:
        """
        Async version of learn() - learn from a message exchange.

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
        if not ASYNC_AVAILABLE:
            raise RuntimeError("aiosqlite not installed. Install with: pip install aiosqlite")

        # Extract and save concepts from both messages
        user_concepts = await self._aextract_and_save_concepts(user_message, 'user')
        ai_concepts = await self._aextract_and_save_concepts(ai_response, 'assistant')

        # Detect and save decisions from AI response
        decisions = await self._aextract_and_save_decisions(ai_response)

        # Build attention graph links between concepts
        all_concepts = list(set(user_concepts + ai_concepts))
        links = await self._abuild_attention_links(all_concepts)

        # Detect compound concepts
        compounds = await self._adetect_compound_concepts(all_concepts)

        # Save the raw messages to auto_messages table
        await self._asave_message('user', user_message, metadata)
        await self._asave_message('assistant', ai_response, metadata)

        # Save full verbatim messages to messages table
        await self._asave_full_message(user_message, ai_response, session_id, metadata)

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
        """Async version of _build_attention_links"""
        if len(concepts) < 2:
            return 0

        config = get_config()
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            links_created = 0

            # Create links between all pairs of concepts
            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    # Check if link exists
                    await c.execute("""
                        SELECT id, strength FROM attention_links
                        WHERE ((LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?))
                           OR (LOWER(concept_a) = LOWER(?) AND LOWER(concept_b) = LOWER(?)))
                        AND tenant_id = ?
                    """, (concept_a, concept_b, concept_b, concept_a, self.tenant_id))

                    existing = await c.fetchone()

                    if existing:
                        # Strengthen existing link (Hebbian learning)
                        link_id, current_strength = existing
                        new_strength = min(1.0, current_strength + config.hebbian_rate)
                        await c.execute("""
                            UPDATE attention_links
                            SET strength = ?
                            WHERE id = ?
                        """, (new_strength, link_id))
                    else:
                        # Create new link
                        await c.execute("""
                            INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (concept_a, concept_b, 'co-occurrence', config.min_link_strength,
                              datetime.now().isoformat(), self.tenant_id))
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
                                  session_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Async version of _save_full_message"""
        async with aiosqlite.connect(self.db_path) as conn:
            c = await conn.cursor()

            # Use instance_id as session_id if not provided
            session = session_id or self.instance_id
            meta_json = json.dumps(metadata) if metadata else '{}'

            await c.execute("""
                INSERT INTO messages (user_message, ai_response, session_id, created_at, tenant_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_message, ai_response, session, datetime.now().isoformat(), self.tenant_id, meta_json))

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
