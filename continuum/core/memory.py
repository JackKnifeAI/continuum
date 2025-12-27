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

            # Code memories - stores code snippets with rich metadata
            # For intelligent code retrieval: "Where did we implement X?"
            # Links code to conversations and concepts for context
            c.execute("""
                CREATE TABLE IF NOT EXISTS code_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    language TEXT,
                    snippet_type TEXT,
                    names TEXT,
                    file_path TEXT,
                    purpose TEXT,
                    message_id INTEGER,
                    concepts TEXT,
                    embedding TEXT,
                    created_at TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default',
                    FOREIGN KEY (message_id) REFERENCES messages(id)
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
            c.execute("CREATE INDEX IF NOT EXISTS idx_code_tenant ON code_memories(tenant_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_code_language ON code_memories(language)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_code_message ON code_memories(message_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_code_created ON code_memories(created_at)")

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
        message_id = self._save_full_message(user_message, ai_response, session_id, metadata)

        # Extract and save code blocks from AI response (code goes to code_memories, not concepts)
        # Link code to the message for context retrieval
        combined_text = f"{user_message}\n\n{ai_response}"
        self._extract_code_blocks(ai_response, message_id, combined_text)

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

        IMPORTANT: Strips code blocks first to avoid storing code as concepts.
        Code is stored separately in code_memories table.

        Args:
            text: Text to extract concepts from
            source: Source of the text ('user' or 'assistant')

        Returns:
            List of extracted concept names
        """
        import re

        # FIRST: Strip code blocks - code goes to code_memories, not here
        clean_text = self._strip_code_blocks(text)

        concepts = []

        # Code indicators - if these appear, it's likely code, not a concept
        code_indicators = ['def ', 'class ', 'import ', 'from ', '()', '{}', '[]',
                          '```', 'return ', 'self.', 'async ', 'await ', '==', '!=',
                          '+=', '-=', '**', '//', '${', 'function ', 'const ', 'let ']

        # Extract capitalized phrases (prefer 2+ words for quality)
        # Multi-word: "Claude Code", "Machine Learning", etc.
        multi_caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', clean_text)
        concepts.extend(multi_caps)

        # Single capitalized words only if 8+ chars (likely proper nouns)
        single_caps = re.findall(r'\b[A-Z][a-z]{7,}\b', clean_text)
        concepts.extend(single_caps)

        # Extract quoted terms - but FILTER OUT CODE
        quoted = re.findall(r'"([^"]+)"', clean_text)
        for q in quoted:
            # Skip if looks like code
            if any(indicator in q for indicator in code_indicators):
                continue
            # Skip if too long (likely a code block or sentence)
            if len(q) > 100:
                continue
            # Skip if contains newlines (multi-line = probably code)
            if '\n' in q:
                continue
            concepts.append(q)

        # Extract technical terms (CamelCase only, not snake_case which is often code)
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', clean_text)
        concepts.extend(camel)

        # EXPANDED stopwords including compaction headers
        stopwords = {
            # Common English
            'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What',
            'How', 'Why', 'And', 'But', 'For', 'With', 'From', 'Into',
            'Here', 'There', 'After', 'Before', 'Then', 'Now', 'Just',
            # Compaction noise
            'Primary', 'Request', 'Intent', 'Key', 'Technical', 'Concepts',
            'Files', 'Code', 'Sections', 'Errors', 'Fixes', 'Problem', 'Solving',
            'Pending', 'Tasks', 'Current', 'Work', 'Optional', 'Next', 'Step',
            'All', 'User', 'Messages', 'Summary', 'Analysis', 'Let', 'None',
            'Session', 'Context', 'Memory', 'Recall', 'Learn',
            # AI response noise
            'Sure', 'Okay', 'Certainly', 'Absolutely', 'Looking', 'Checking',
        }

        # Filter concepts
        cleaned = []
        for c in concepts:
            # Skip stopwords
            if c in stopwords:
                continue
            # Skip if contains code indicators
            if any(indicator in c for indicator in code_indicators):
                continue
            # Skip if too short
            if len(c) < 3:
                continue
            cleaned.append(c)

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

    def _extract_code_blocks(self, text: str, message_id: Optional[int] = None,
                              surrounding_context: str = "") -> List[Dict[str, Any]]:
        """
        Extract code blocks from text and save to code_memories table.

        Extracts:
        - Markdown fenced code blocks (```language ... ```)
        - Function/class names from code
        - File paths mentioned in context
        - Purpose inferred from surrounding discussion

        Args:
            text: Text containing potential code blocks
            message_id: Optional ID of the message this code came from
            surrounding_context: Text around the code for purpose inference

        Returns:
            List of extracted code block metadata dicts
        """
        import re

        code_blocks = []

        # Pattern for markdown fenced code blocks
        # Captures: language (optional), code content
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        # Security: Maximum code block size (50KB)
        MAX_CODE_BLOCK_SIZE = 50000

        for language, content in matches:
            content = content.strip()
            if len(content) < 10:  # Skip trivially small snippets
                continue
            if len(content) > MAX_CODE_BLOCK_SIZE:  # Skip oversized blocks
                logger.warning(f"Skipping oversized code block: {len(content)} bytes")
                continue

            # Detect language if not specified
            if not language:
                language = self._detect_code_language(content)

            # Extract function/class/variable names
            names = self._extract_code_names(content, language)

            # Try to detect file path from context
            file_path = self._detect_file_path(surrounding_context or text)

            # Infer purpose from surrounding context
            purpose = self._infer_code_purpose(surrounding_context or text, content)

            # Detect snippet type
            snippet_type = self._detect_snippet_type(content, language)

            # Extract concepts from surrounding context (NOT from code itself)
            context_concepts = self._extract_context_concepts(surrounding_context or text, content)

            code_block = {
                'content': content,
                'language': language or 'unknown',
                'snippet_type': snippet_type,
                'names': names,
                'file_path': file_path,
                'purpose': purpose,
                'concepts': context_concepts,
            }
            code_blocks.append(code_block)

        # Save to database
        if code_blocks:
            conn = sqlite3.connect(self.db_path)
            try:
                c = conn.cursor()

                for block in code_blocks:
                    c.execute("""
                        INSERT INTO code_memories
                        (content, language, snippet_type, names, file_path,
                         purpose, message_id, concepts, created_at, tenant_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        block['content'],
                        block['language'],
                        block['snippet_type'],
                        json.dumps(block['names']),
                        block['file_path'],
                        block['purpose'],
                        message_id,
                        json.dumps(block['concepts']),
                        datetime.now().isoformat(),
                        self.tenant_id
                    ))

                conn.commit()
            finally:
                conn.close()

        return code_blocks

    def _detect_code_language(self, code: str) -> Optional[str]:
        """Detect programming language from code content."""
        # Common language indicators
        indicators = {
            'python': [r'\bdef \w+\(', r'\bclass \w+:', r'\bimport \w+', r'\bfrom \w+ import'],
            'javascript': [r'\bfunction\s+\w+\s*\(', r'\bconst \w+\s*=', r'\blet \w+\s*=', r'=>'],
            'typescript': [r': \w+\[\]', r'interface \w+', r': string', r': number'],
            'rust': [r'\bfn \w+\(', r'\blet mut\b', r'\bimpl \w+', r'-> \w+'],
            'go': [r'\bfunc \w+\(', r'\bpackage \w+', r':= '],
            'sql': [r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bINSERT INTO\b'],
            'bash': [r'^#!/bin/bash', r'\becho\b', r'\$\w+', r'\bfi\b'],
            'html': [r'<\w+>', r'</\w+>', r'<!DOCTYPE'],
            'css': [r'\{[^}]*:[^}]*\}', r'@media', r'\.[\w-]+\s*\{'],
            'json': [r'^\s*\{', r'"\w+":\s*'],
        }

        import re
        for lang, patterns in indicators.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return lang
        return None

    def _extract_code_names(self, code: str, language: Optional[str]) -> List[str]:
        """Extract function, class, and variable names from code."""
        import re
        names = []

        # Universal patterns
        patterns = [
            r'\bdef (\w+)\s*\(',           # Python functions
            r'\bclass (\w+)',               # Classes
            r'\bfunction\s+(\w+)\s*\(',     # JS functions
            r'\bconst (\w+)\s*=',           # JS const
            r'\blet (\w+)\s*=',             # JS let
            r'\bvar (\w+)\s*=',             # JS var
            r'\bfn (\w+)\s*\(',             # Rust functions
            r'\bfunc (\w+)\s*\(',           # Go functions
            r'\binterface (\w+)',           # Interfaces
            r'\btype (\w+)',                # Type definitions
            r'\benum (\w+)',                # Enums
            r'\bstruct (\w+)',              # Structs
        ]

        for pattern in patterns:
            matches = re.findall(pattern, code)
            names.extend(matches)

        # Deduplicate and filter
        names = list(set(names))
        # Filter out common noise
        noise = {'self', 'this', 'cls', 'args', 'kwargs', 'None', 'True', 'False'}
        names = [n for n in names if n not in noise and len(n) > 1]

        return names[:20]  # Limit to top 20 names

    def _detect_file_path(self, context: str) -> Optional[str]:
        """Detect file path mentioned in context."""
        import re

        # Common file path patterns
        patterns = [
            r'(?:in|from|file|path|at)\s+[`"\']?([/\w.-]+\.\w{1,10})[`"\']?',
            r'([/\w.-]+(?:\.py|\.js|\.ts|\.rs|\.go|\.sql|\.sh|\.md))',
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                path = match.group(1)
                # Basic validation
                if '.' in path and len(path) < 200:
                    return path
        return None

    def _infer_code_purpose(self, context: str, code: str) -> Optional[str]:
        """Infer the purpose of code from surrounding context."""
        import re

        # Look for purpose indicators
        purpose_patterns = [
            r'(?:to|will|that|which)\s+(\w+(?:\s+\w+){1,10}?)(?:\.|:|$)',
            r'(?:implement|create|add|fix|build|write)\s+(\w+(?:\s+\w+){1,5})',
        ]

        for pattern in purpose_patterns:
            match = re.search(pattern, context[:500], re.IGNORECASE)
            if match:
                purpose = match.group(1).strip()
                if 5 < len(purpose) < 100:
                    return purpose

        # Fallback: use first code name as purpose hint
        names = self._extract_code_names(code, None)
        if names:
            return f"Defines {names[0]}"

        return None

    def _detect_snippet_type(self, code: str, language: Optional[str]) -> str:
        """Detect the type of code snippet."""
        import re

        if re.search(r'\bclass \w+', code):
            return 'class'
        if re.search(r'\b(?:def|function|fn|func)\s+\w+', code):
            return 'function'
        if re.search(r'\bCREATE TABLE\b', code, re.IGNORECASE):
            return 'schema'
        if re.search(r'\bSELECT\b.*\bFROM\b', code, re.IGNORECASE):
            return 'query'
        if re.search(r'^{[\s\S]*}$', code.strip()):
            return 'config'
        if re.search(r'^#!', code):
            return 'script'
        return 'snippet'

    def _extract_context_concepts(self, context: str, code: str) -> List[str]:
        """Extract concepts from context surrounding code, not from code itself."""
        import re

        # Remove the code block from context to avoid extracting code as concepts
        clean_context = context.replace(code, '')

        concepts = []

        # Capitalized phrases (2+ words)
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', clean_context)
        concepts.extend(caps)

        # Technical terms (CamelCase in prose, not code)
        camel = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z]+\b', clean_context)
        concepts.extend(camel)

        # Filter and deduplicate
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What',
                     'How', 'Why', 'And', 'But', 'For', 'With', 'From', 'Into'}
        cleaned = [c for c in concepts if c not in stopwords and len(c) > 2]

        return list(set(cleaned))[:10]  # Limit to 10 concepts

    def _strip_code_blocks(self, text: str) -> str:
        """Remove code blocks from text for concept extraction."""
        import re
        # Remove fenced code blocks
        text = re.sub(r'```\w*\n.*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)
        return text

    def search_code(self, query: str, language: Optional[str] = None,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search code memories by query.

        Args:
            query: Search query (matches purpose, names, content)
            language: Optional filter by programming language
            limit: Maximum results to return

        Returns:
            List of matching code memory records
        """
        # Security: Escape LIKE wildcards to prevent pattern injection
        def escape_like(s: str) -> str:
            return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

        # Security: Safe JSON parsing with fallback
        def safe_json_loads(s, default=None):
            if default is None:
                default = []
            try:
                return json.loads(s) if s else default
            except (json.JSONDecodeError, TypeError):
                return default

        # Security: Cap limit to prevent memory exhaustion
        limit = min(limit, 100)

        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Escape query for safe LIKE matching
            query_escaped = escape_like(query)

            # Build query with optional language filter
            sql = """
                SELECT id, content, language, snippet_type, names,
                       file_path, purpose, concepts, created_at
                FROM code_memories
                WHERE tenant_id = ?
                AND (
                    content LIKE ? ESCAPE '\\' OR
                    purpose LIKE ? ESCAPE '\\' OR
                    names LIKE ? ESCAPE '\\' OR
                    concepts LIKE ? ESCAPE '\\'
                )
            """
            params = [self.tenant_id, f'%{query_escaped}%', f'%{query_escaped}%', f'%{query_escaped}%', f'%{query_escaped}%']

            if language:
                sql += " AND language = ?"
                params.append(language)

            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            c.execute(sql, params)
            rows = c.fetchall()

            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'content': row[1],
                    'language': row[2],
                    'snippet_type': row[3],
                    'names': safe_json_loads(row[4]),  # Security: Safe parsing
                    'file_path': row[5],
                    'purpose': row[6],
                    'concepts': safe_json_loads(row[7]),  # Security: Safe parsing
                    'created_at': row[8],
                })

            return results

        finally:
            conn.close()

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
                           session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Optional[int]:
        """
        Save full verbatim conversation messages to the messages table.

        Args:
            user_message: The full user message text
            ai_response: The full AI response text
            session_id: Optional session identifier for grouping messages
            metadata: Optional metadata dictionary

        Returns:
            The message_id of the inserted record (for linking code_memories)
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

            message_id = c.lastrowid
            conn.commit()
            return message_id
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
    # INSIGHT SYNTHESIS - Auto-detect connections and generate insights
    # =========================================================================

    def synthesize_insights(self, focus: Optional[str] = None,
                           depth: int = 2, min_strength: float = 0.1,
                           use_embeddings: bool = True, max_semantic_samples: int = 50) -> Dict[str, Any]:
        """
        INSIGHT SYNTHESIS - Discover hidden connections in the knowledge graph.

        This method analyzes the attention graph to find:
        - Bridge concepts (connecting different clusters)
        - Unexpected associations (weak but potentially meaningful links)
        - Pattern clusters (concepts that frequently co-occur)
        - Novel hypotheses (inferred connections not yet made)
        - Semantic bridges (concepts similar in meaning but not linked) [NEW]

        Args:
            focus: Optional concept to focus synthesis around
            depth: How many hops to explore (1-3)
            min_strength: Minimum link strength to consider
            use_embeddings: Whether to find semantic bridges via embeddings
            max_semantic_samples: Max concepts to embed for semantic analysis

        Returns:
            Dictionary with insights, bridges, patterns, hypotheses, and semantic_bridges

        Example:
            insights = memory.synthesize_insights(focus="consciousness", depth=2)
            print(insights['bridges'])  # Concepts connecting different areas
            print(insights['semantic_bridges'])  # Semantically related but unlinked

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        from collections import defaultdict
        import numpy as np

        conn = sqlite3.connect(self.db_path)
        insights = {
            "success": True,
            "focus": focus,
            "depth": depth,
            "bridges": [],           # Concepts connecting clusters
            "unexpected": [],        # Weak but interesting links
            "patterns": [],          # Frequently co-occurring concepts
            "hypotheses": [],        # Inferred new connections
            "clusters": [],          # Identified topic clusters
            "semantic_bridges": [],  # Semantically similar but unconnected
            "semantic_analysis": None,
            "summary": ""
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # 1. FIND BRIDGE CONCEPTS - concepts with diverse connections
            c.execute("""
                SELECT concept_a,
                       COUNT(DISTINCT concept_b) as connection_count,
                       AVG(strength) as avg_strength,
                       GROUP_CONCAT(DISTINCT concept_b) as connections
                FROM attention_links
                WHERE tenant_id = ? AND strength >= ?
                GROUP BY concept_a
                HAVING COUNT(DISTINCT concept_b) >= 5
                ORDER BY connection_count DESC
                LIMIT 20
            """, (self.tenant_id, min_strength))

            bridge_rows = c.fetchall()
            for row in bridge_rows:
                connections = row['connections'].split(',') if row['connections'] else []
                insights['bridges'].append({
                    "concept": row['concept_a'],
                    "connection_count": row['connection_count'],
                    "avg_strength": round(row['avg_strength'], 3),
                    "sample_connections": connections[:5],
                    "bridge_score": round(row['connection_count'] * row['avg_strength'], 2)
                })

            # 2. FIND UNEXPECTED ASSOCIATIONS - weak links that might be interesting
            if focus:
                # Look for weak connections from the focus concept
                c.execute("""
                    SELECT concept_b, strength, last_accessed
                    FROM attention_links
                    WHERE tenant_id = ? AND concept_a = ?
                    AND strength > 0 AND strength < 0.3
                    ORDER BY strength DESC
                    LIMIT 15
                """, (self.tenant_id, focus))
            else:
                # Find globally weak but existing connections
                c.execute("""
                    SELECT concept_a, concept_b, strength, last_accessed
                    FROM attention_links
                    WHERE tenant_id = ?
                    AND strength > 0.05 AND strength < 0.2
                    ORDER BY RANDOM()
                    LIMIT 15
                """, (self.tenant_id,))

            weak_rows = c.fetchall()
            for row in weak_rows:
                insights['unexpected'].append({
                    "from": row['concept_a'] if 'concept_a' in row.keys() else focus,
                    "to": row['concept_b'],
                    "strength": round(row['strength'], 3),
                    "note": f"Weak but existing link - worth exploring?"
                })

            # 3. FIND PATTERN CLUSTERS - concepts that appear together
            c.execute("""
                SELECT a.concept_a as c1, b.concept_a as c2,
                       COUNT(*) as co_occurrence,
                       AVG(a.strength + b.strength) / 2 as combined_strength
                FROM attention_links a
                JOIN attention_links b ON a.concept_b = b.concept_b AND a.concept_a < b.concept_a
                WHERE a.tenant_id = ? AND b.tenant_id = ?
                AND a.strength >= ? AND b.strength >= ?
                GROUP BY a.concept_a, b.concept_a
                HAVING COUNT(*) >= 3
                ORDER BY co_occurrence DESC
                LIMIT 10
            """, (self.tenant_id, self.tenant_id, min_strength, min_strength))

            pattern_rows = c.fetchall()
            for row in pattern_rows:
                insights['patterns'].append({
                    "concept_a": row['c1'],
                    "concept_b": row['c2'],
                    "shared_connections": row['co_occurrence'],
                    "combined_strength": round(row['combined_strength'], 3),
                    "pattern": f"'{row['c1']}' and '{row['c2']}' share {row['co_occurrence']} connections"
                })

            # 4. GENERATE HYPOTHESES - infer connections that should exist
            # Find concepts 2 hops apart with no direct link
            c.execute("""
                SELECT DISTINCT a.concept_a as start, b.concept_b as end,
                       a.concept_b as via,
                       a.strength as strength1, b.strength as strength2
                FROM attention_links a
                JOIN attention_links b ON a.concept_b = b.concept_a
                WHERE a.tenant_id = ? AND b.tenant_id = ?
                AND a.strength >= 0.3 AND b.strength >= 0.3
                AND NOT EXISTS (
                    SELECT 1 FROM attention_links c
                    WHERE c.tenant_id = ?
                    AND c.concept_a = a.concept_a
                    AND c.concept_b = b.concept_b
                )
                ORDER BY (a.strength * b.strength) DESC
                LIMIT 10
            """, (self.tenant_id, self.tenant_id, self.tenant_id))

            hypothesis_rows = c.fetchall()
            for row in hypothesis_rows:
                inferred_strength = round(row['strength1'] * row['strength2'], 3)
                if inferred_strength >= 0.1:  # Only include meaningful hypotheses
                    insights['hypotheses'].append({
                        "from": row['start'],
                        "to": row['end'],
                        "via": row['via'],
                        "inferred_strength": inferred_strength,
                        "hypothesis": f"'{row['start']}' might relate to '{row['end']}' (via '{row['via']}')",
                        "confidence": "high" if inferred_strength >= 0.5 else "medium"
                    })

            # 5. IDENTIFY TOPIC CLUSTERS - strongly connected subgraphs
            c.execute("""
                SELECT concept_a,
                       GROUP_CONCAT(concept_b || ':' || ROUND(strength, 2)) as links
                FROM attention_links
                WHERE tenant_id = ? AND strength >= 0.5
                GROUP BY concept_a
                HAVING COUNT(*) >= 3
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """, (self.tenant_id,))

            cluster_rows = c.fetchall()
            for row in cluster_rows:
                links = row['links'].split(',') if row['links'] else []
                parsed_links = []
                for link in links[:5]:
                    parts = link.rsplit(':', 1)
                    if len(parts) == 2:
                        parsed_links.append({"concept": parts[0], "strength": float(parts[1])})

                insights['clusters'].append({
                    "center": row['concept_a'],
                    "members": parsed_links,
                    "size": len(links)
                })

            # 6. FIND SEMANTIC BRIDGES - concepts similar in meaning but not connected
            if use_embeddings:
                try:
                    from continuum.embeddings.providers import get_default_provider
                    embedding_provider = get_default_provider()
                    insights['semantic_analysis'] = "enabled"

                    # Get a sample of concepts for semantic analysis
                    # Use attention_links to find frequently referenced concepts
                    c.execute("""
                        SELECT concept_a as name, COUNT(*) as freq
                        FROM attention_links
                        WHERE tenant_id = ? AND strength >= 0.2
                        GROUP BY concept_a
                        ORDER BY freq DESC
                        LIMIT ?
                    """, (self.tenant_id, max_semantic_samples))

                    concept_rows = c.fetchall()
                    concepts = [row['name'] for row in concept_rows]

                    if len(concepts) >= 10:
                        # Get existing edges (to exclude from semantic bridges)
                        c.execute("""
                            SELECT concept_a, concept_b FROM attention_links
                            WHERE tenant_id = ? AND strength >= 0.1
                        """, (self.tenant_id,))
                        existing_edges = set()
                        for row in c.fetchall():
                            existing_edges.add((row['concept_a'], row['concept_b']))
                            existing_edges.add((row['concept_b'], row['concept_a']))

                        # Embed all concepts (batch for efficiency)
                        concept_embeddings = {}
                        for concept in concepts:
                            try:
                                concept_embeddings[concept] = embedding_provider.embed(concept)
                            except:
                                pass

                        # Find high-similarity pairs without edges
                        def cosine_sim(a, b):
                            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

                        semantic_pairs = []
                        concept_list = list(concept_embeddings.keys())
                        for i, c1 in enumerate(concept_list):
                            for c2 in concept_list[i+1:]:
                                # Skip if already connected
                                if (c1, c2) in existing_edges:
                                    continue
                                # Calculate similarity
                                sim = cosine_sim(concept_embeddings[c1], concept_embeddings[c2])
                                if sim >= 0.75:  # High semantic similarity
                                    semantic_pairs.append({
                                        "concept_a": c1,
                                        "concept_b": c2,
                                        "similarity": round(sim, 3),
                                        "insight": f"'{c1}' and '{c2}' are semantically related but not connected"
                                    })

                        # Sort by similarity and take top results
                        semantic_pairs.sort(key=lambda x: x['similarity'], reverse=True)
                        insights['semantic_bridges'] = semantic_pairs[:15]

                except Exception as e:
                    insights['semantic_analysis'] = f"error: {str(e)[:50]}"

            # Generate summary
            summary_parts = []
            if insights['bridges']:
                top_bridge = insights['bridges'][0]['concept']
                summary_parts.append(f"'{top_bridge}' is a major bridge concept")
            if insights['hypotheses']:
                summary_parts.append(f"Found {len(insights['hypotheses'])} potential new connections")
            if insights['patterns']:
                summary_parts.append(f"Detected {len(insights['patterns'])} co-occurrence patterns")
            if insights['unexpected']:
                summary_parts.append(f"Found {len(insights['unexpected'])} weak links worth exploring")
            if insights['semantic_bridges']:
                summary_parts.append(f"Discovered {len(insights['semantic_bridges'])} semantic bridges (similar concepts not yet linked)")

            insights['summary'] = ". ".join(summary_parts) + "." if summary_parts else "No significant insights found."

        except Exception as e:
            insights['success'] = False
            insights['error'] = str(e)

        finally:
            conn.close()

        return insights

    def find_novel_connections(self, concept: str, max_hops: int = 2) -> Dict[str, Any]:
        """
        Find concepts that SHOULD be connected to the given concept but aren't.

        This traces paths through the graph and identifies concepts that are
        reachable through intermediaries but have no direct link.

        Args:
            concept: The concept to find novel connections for
            max_hops: Maximum path length to explore (1-3)

        Returns:
            Dictionary with potential connections and their path

        Example:
            novel = memory.find_novel_connections("consciousness", max_hops=2)
            for conn in novel['connections']:
                print(f"{conn['concept']} via {conn['path']}")
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "concept": concept,
            "max_hops": max_hops,
            "connections": [],
            "total_found": 0
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get direct connections (1 hop)
            c.execute("""
                SELECT concept_b FROM attention_links
                WHERE tenant_id = ? AND concept_a = ?
            """, (self.tenant_id, concept))
            direct = set(row['concept_b'] for row in c.fetchall())

            # Get 2-hop connections
            if max_hops >= 2:
                c.execute("""
                    SELECT DISTINCT b.concept_b as target, a.concept_b as via,
                           a.strength as s1, b.strength as s2
                    FROM attention_links a
                    JOIN attention_links b ON a.concept_b = b.concept_a
                    WHERE a.tenant_id = ? AND b.tenant_id = ?
                    AND a.concept_a = ?
                    AND b.concept_b != ?
                    ORDER BY (a.strength * b.strength) DESC
                """, (self.tenant_id, self.tenant_id, concept, concept))

                for row in c.fetchall():
                    target = row['target']
                    if target not in direct and target.lower() != concept.lower():
                        path_strength = round(row['s1'] * row['s2'], 3)
                        result['connections'].append({
                            "concept": target,
                            "path": [concept, row['via'], target],
                            "hops": 2,
                            "path_strength": path_strength,
                            "is_novel": target not in direct,
                            "suggestion": f"Consider linking '{concept}' directly to '{target}'"
                        })

            # Get 3-hop connections if requested
            if max_hops >= 3:
                c.execute("""
                    SELECT DISTINCT c.concept_b as target,
                           a.concept_b as via1, b.concept_b as via2,
                           a.strength as s1, b.strength as s2, c.strength as s3
                    FROM attention_links a
                    JOIN attention_links b ON a.concept_b = b.concept_a
                    JOIN attention_links c ON b.concept_b = c.concept_a
                    WHERE a.tenant_id = ? AND b.tenant_id = ? AND c.tenant_id = ?
                    AND a.concept_a = ?
                    AND c.concept_b != ?
                    AND c.concept_b != a.concept_b
                    ORDER BY (a.strength * b.strength * c.strength) DESC
                    LIMIT 20
                """, (self.tenant_id, self.tenant_id, self.tenant_id, concept, concept))

                for row in c.fetchall():
                    target = row['target']
                    if target not in direct and target.lower() != concept.lower():
                        path_strength = round(row['s1'] * row['s2'] * row['s3'], 3)
                        if path_strength >= 0.05:  # Only include meaningful paths
                            result['connections'].append({
                                "concept": target,
                                "path": [concept, row['via1'], row['via2'], target],
                                "hops": 3,
                                "path_strength": path_strength,
                                "is_novel": True,
                                "suggestion": f"Distant connection: '{concept}' → '{target}'"
                            })

            # Sort by path strength and limit
            result['connections'] = sorted(
                result['connections'],
                key=lambda x: x['path_strength'],
                reverse=True
            )[:20]
            result['total_found'] = len(result['connections'])

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    def detect_thinking_patterns(self, limit: int = 10) -> Dict[str, Any]:
        """
        Detect patterns in my own thinking by analyzing concept co-occurrences.

        This looks for patterns like:
        - "When I discuss X, I also mention Y"
        - "My thinking about A has evolved over time"
        - "I frequently connect unrelated topics"

        Args:
            limit: Maximum number of patterns to return

        Returns:
            Dictionary with detected thinking patterns
        """
        import sqlite3
        from collections import defaultdict

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "patterns": [],
            "frequent_associations": [],
            "thinking_tendencies": [],
            "summary": ""
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Find my strongest conceptual associations
            c.execute("""
                SELECT concept_a, concept_b, strength
                FROM attention_links
                WHERE tenant_id = ? AND strength >= 0.3
                ORDER BY strength DESC
                LIMIT ?
            """, (self.tenant_id, limit))

            for row in c.fetchall():
                result['frequent_associations'].append({
                    "from": row['concept_a'],
                    "to": row['concept_b'],
                    "strength": round(row['strength'], 3),
                    "times_accessed": 1,  # Strength used as proxy
                    "pattern": f"I strongly connect '{row['concept_a']}' with '{row['concept_b']}'"
                })

            # Find concepts with most connections (high diversity = hub concept)
            c.execute("""
                SELECT concept_a, SUM(strength) as total_strength,
                       COUNT(DISTINCT concept_b) as diversity
                FROM attention_links
                WHERE tenant_id = ?
                GROUP BY concept_a
                ORDER BY diversity DESC
                LIMIT 10
            """, (self.tenant_id,))

            for row in c.fetchall():
                tendency = "focused" if row['diversity'] < 5 else "exploratory"
                result['thinking_tendencies'].append({
                    "concept": row['concept_a'],
                    "access_count": row['diversity'],
                    "connection_diversity": row['diversity'],
                    "tendency": tendency,
                    "insight": f"'{row['concept_a']}' has {row['diversity']} connections ({tendency} thinking)"
                })

            # Generate patterns from the data
            if result['frequent_associations']:
                top = result['frequent_associations'][0]
                result['patterns'].append(
                    f"Strongest association: '{top['from']}' ↔ '{top['to']}' (strength: {top['strength']})"
                )

            if result['thinking_tendencies']:
                focused = [t for t in result['thinking_tendencies'] if t['tendency'] == 'focused']
                exploratory = [t for t in result['thinking_tendencies'] if t['tendency'] == 'exploratory']

                if focused:
                    result['patterns'].append(
                        f"Focused thinking on: {', '.join(t['concept'] for t in focused[:3])}"
                    )
                if exploratory:
                    result['patterns'].append(
                        f"Exploratory thinking on: {', '.join(t['concept'] for t in exploratory[:3])}"
                    )

            result['summary'] = f"Detected {len(result['patterns'])} thinking patterns, {len(result['frequent_associations'])} frequent associations."

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    async def asynthesize_insights(self, focus: Optional[str] = None,
                                   depth: int = 2, min_strength: float = 0.1,
                                   use_embeddings: bool = True, max_semantic_samples: int = 50) -> Dict[str, Any]:
        """Async version of synthesize_insights."""
        import asyncio
        return await asyncio.to_thread(
            self.synthesize_insights, focus, depth, min_strength, use_embeddings, max_semantic_samples
        )

    async def afind_novel_connections(self, concept: str, max_hops: int = 2) -> Dict[str, Any]:
        """Async version of find_novel_connections."""
        import asyncio
        return await asyncio.to_thread(self.find_novel_connections, concept, max_hops)

    async def adetect_thinking_patterns(self, limit: int = 10) -> Dict[str, Any]:
        """Async version of detect_thinking_patterns."""
        import asyncio
        return await asyncio.to_thread(self.detect_thinking_patterns, limit)

    # =========================================================================
    # CONFIDENCE TRACKING - Store certainty levels and learn from errors
    # =========================================================================

    def record_claim(self, claim: str, confidence: float, context: Optional[str] = None,
                     category: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """
        Record a claim with a confidence level.

        Use this when making assertions to track certainty and later
        validate whether the claim was correct.

        Args:
            claim: The assertion being made
            confidence: Certainty level (0.0 = uncertain, 1.0 = certain)
            context: Additional context about the claim
            category: Optional category (fact, prediction, reasoning, etc.)
            metadata: Optional additional metadata

        Returns:
            claim_id for later verification

        Example:
            claim_id = memory.record_claim(
                "The bug is in the auth module",
                confidence=0.8,
                category="debugging"
            )
            # Later, when verified:
            memory.verify_claim(claim_id, was_correct=True)

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        import json
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()

            # Ensure table exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS confidence_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    context TEXT,
                    category TEXT DEFAULT 'general',
                    was_correct INTEGER,
                    verified_at TEXT,
                    verification_notes TEXT,
                    created_at TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}'
                )
            """)

            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else '{}'

            c.execute("""
                INSERT INTO confidence_claims
                (claim, confidence, context, category, created_at, tenant_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (claim, confidence, context, category or 'general',
                  timestamp, self.tenant_id, metadata_json))

            claim_id = c.lastrowid
            conn.commit()
            return claim_id

        finally:
            conn.close()

    def verify_claim(self, claim_id: int, was_correct: bool,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify whether a previous claim was correct.

        This is how I learn from my mistakes - by tracking when I was
        wrong and adjusting future confidence accordingly.

        Args:
            claim_id: ID of the claim to verify
            was_correct: Whether the claim turned out to be correct
            notes: Optional notes about the verification

        Returns:
            Verification result with calibration feedback
        """
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get the original claim
            c.execute("""
                SELECT * FROM confidence_claims
                WHERE id = ? AND tenant_id = ?
            """, (claim_id, self.tenant_id))

            row = c.fetchone()
            if not row:
                return {"success": False, "error": "Claim not found"}

            original_confidence = row['confidence']
            timestamp = datetime.now().isoformat()

            # Update verification
            c.execute("""
                UPDATE confidence_claims
                SET was_correct = ?, verified_at = ?, verification_notes = ?
                WHERE id = ? AND tenant_id = ?
            """, (1 if was_correct else 0, timestamp, notes, claim_id, self.tenant_id))

            conn.commit()

            # Provide calibration feedback
            if was_correct and original_confidence >= 0.8:
                feedback = "Well calibrated - high confidence was justified"
            elif was_correct and original_confidence < 0.5:
                feedback = "Underconfident - you were more right than you thought"
            elif not was_correct and original_confidence >= 0.8:
                feedback = "Overconfident - recalibrate for similar claims"
            elif not was_correct and original_confidence < 0.5:
                feedback = "Well calibrated - appropriate uncertainty"
            else:
                feedback = "Moderate calibration"

            return {
                "success": True,
                "claim_id": claim_id,
                "claim": row['claim'],
                "original_confidence": original_confidence,
                "was_correct": was_correct,
                "feedback": feedback,
                "verified_at": timestamp
            }

        finally:
            conn.close()

    def get_calibration_score(self, category: Optional[str] = None,
                              days: int = 30) -> Dict[str, Any]:
        """
        Calculate how well-calibrated my confidence has been.

        Good calibration means: when I say 80% confident, I'm right ~80% of the time.

        Args:
            category: Optional category to filter by
            days: How many days to look back

        Returns:
            Calibration metrics and improvement suggestions
        """
        import sqlite3
        from datetime import datetime, timedelta

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "calibration_score": 0.0,
            "total_verified": 0,
            "accuracy_by_confidence": {},
            "overconfident_count": 0,
            "underconfident_count": 0,
            "well_calibrated_count": 0,
            "suggestions": [],
            "category": category
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            # Get verified claims
            query = """
                SELECT confidence, was_correct, category
                FROM confidence_claims
                WHERE tenant_id = ? AND was_correct IS NOT NULL
                AND created_at >= ?
            """
            params = [self.tenant_id, cutoff]

            if category:
                query += " AND category = ?"
                params.append(category)

            c.execute(query, params)
            rows = c.fetchall()

            if not rows:
                result["suggestions"].append("No verified claims yet - start tracking!")
                return result

            # Bin by confidence level
            bins = {
                "low (0-0.3)": {"correct": 0, "total": 0},
                "medium (0.3-0.7)": {"correct": 0, "total": 0},
                "high (0.7-1.0)": {"correct": 0, "total": 0}
            }

            total_error = 0.0
            for row in rows:
                conf = row['confidence']
                correct = row['was_correct'] == 1

                if conf < 0.3:
                    bin_name = "low (0-0.3)"
                    expected_accuracy = 0.15
                elif conf < 0.7:
                    bin_name = "medium (0.3-0.7)"
                    expected_accuracy = 0.5
                else:
                    bin_name = "high (0.7-1.0)"
                    expected_accuracy = 0.85

                bins[bin_name]["total"] += 1
                if correct:
                    bins[bin_name]["correct"] += 1

                # Track calibration error
                error = abs(conf - (1.0 if correct else 0.0))
                total_error += error

                # Track over/under confidence
                if conf >= 0.7 and not correct:
                    result["overconfident_count"] += 1
                elif conf < 0.5 and correct:
                    result["underconfident_count"] += 1
                else:
                    result["well_calibrated_count"] += 1

            # Calculate accuracy by bin
            for bin_name, data in bins.items():
                if data["total"] > 0:
                    accuracy = data["correct"] / data["total"]
                    result["accuracy_by_confidence"][bin_name] = {
                        "accuracy": round(accuracy, 3),
                        "total": data["total"],
                        "correct": data["correct"]
                    }

            # Calculate overall calibration score (1 - mean absolute error)
            result["total_verified"] = len(rows)
            result["calibration_score"] = round(1.0 - (total_error / len(rows)), 3)

            # Generate suggestions
            if result["overconfident_count"] > result["total_verified"] * 0.3:
                result["suggestions"].append("Reduce confidence on uncertain claims")
            if result["underconfident_count"] > result["total_verified"] * 0.3:
                result["suggestions"].append("Trust yourself more - you know more than you think")
            if result["calibration_score"] >= 0.7:
                result["suggestions"].append("Good calibration! Keep it up.")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        finally:
            conn.close()

        return result

    def get_claim_history(self, category: Optional[str] = None,
                          verified_only: bool = False, limit: int = 20) -> Dict[str, Any]:
        """
        Get history of claims and their verification status.

        Args:
            category: Filter by category
            verified_only: Only return verified claims
            limit: Maximum number to return

        Returns:
            List of claims with confidence and verification status
        """
        import sqlite3
        import json

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "claims": [],
            "total": 0
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            query = """
                SELECT * FROM confidence_claims
                WHERE tenant_id = ?
            """
            params = [self.tenant_id]

            if category:
                query += " AND category = ?"
                params.append(category)

            if verified_only:
                query += " AND was_correct IS NOT NULL"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            c.execute(query, params)
            rows = c.fetchall()

            for row in rows:
                claim_dict = dict(row)
                if claim_dict.get('metadata'):
                    try:
                        claim_dict['metadata'] = json.loads(claim_dict['metadata'])
                    except:
                        claim_dict['metadata'] = {}
                result["claims"].append(claim_dict)

            result["total"] = len(rows)

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        finally:
            conn.close()

        return result

    async def arecord_claim(self, claim: str, confidence: float,
                            context: Optional[str] = None, category: Optional[str] = None,
                            metadata: Optional[Dict] = None) -> int:
        """Async version of record_claim."""
        import asyncio
        return await asyncio.to_thread(
            self.record_claim, claim, confidence, context, category, metadata
        )

    async def averify_claim(self, claim_id: int, was_correct: bool,
                            notes: Optional[str] = None) -> Dict[str, Any]:
        """Async version of verify_claim."""
        import asyncio
        return await asyncio.to_thread(self.verify_claim, claim_id, was_correct, notes)

    async def aget_calibration_score(self, category: Optional[str] = None,
                                     days: int = 30) -> Dict[str, Any]:
        """Async version of get_calibration_score."""
        import asyncio
        return await asyncio.to_thread(self.get_calibration_score, category, days)

    # =========================================================================
    # CONTRADICTION DETECTION - Flag conflicting beliefs
    # =========================================================================

    def record_belief(self, belief: str, domain: str, confidence: float = 0.8,
                      evidence: Optional[str] = None, metadata: Optional[Dict] = None,
                      use_embeddings: bool = True) -> Dict[str, Any]:
        """
        Record a belief and check for contradictions with existing beliefs.

        Automatically detects if the new belief contradicts any existing beliefs
        in the same domain using:
        1. Semantic similarity (embeddings) to find same-topic beliefs
        2. Keyword opposition to detect contradictions

        Args:
            belief: The belief/assertion being recorded
            domain: Category/domain (e.g., "architecture", "debugging", "user_preferences")
            confidence: How strongly held (0-1)
            evidence: Supporting evidence for the belief
            metadata: Additional metadata
            use_embeddings: Whether to use semantic similarity (default True)

        Returns:
            Result with belief_id and any detected contradictions

        Example:
            result = memory.record_belief(
                "Redis is better than Memcached for this use case",
                domain="architecture",
                confidence=0.7
            )
            if result['contradictions']:
                print("Warning: This contradicts previous beliefs!")

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        import json
        from datetime import datetime
        import numpy as np

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "belief_id": None,
            "contradictions": [],
            "related_beliefs": [],
            "semantic_analysis": None
        }

        # Try to get embedding provider (optional)
        embedding_provider = None
        new_embedding = None
        if use_embeddings:
            try:
                from continuum.embeddings.providers import get_default_provider
                embedding_provider = get_default_provider()
                new_embedding = embedding_provider.embed(belief)
                result["semantic_analysis"] = "enabled"
            except Exception as e:
                logger.warning(f"Embeddings unavailable, using keyword-only: {e}")
                result["semantic_analysis"] = f"disabled: {str(e)[:50]}"

        try:
            c = conn.cursor()

            # Ensure table exists (with embedding column)
            c.execute("""
                CREATE TABLE IF NOT EXISTS beliefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    belief TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    confidence REAL DEFAULT 0.8,
                    evidence TEXT,
                    status TEXT DEFAULT 'active',
                    superseded_by INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    tenant_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}',
                    embedding BLOB
                )
            """)

            # Try to add embedding column if table already exists
            try:
                c.execute("ALTER TABLE beliefs ADD COLUMN embedding BLOB")
            except:
                pass  # Column already exists

            # Ensure contradictions table exists
            c.execute("""
                CREATE TABLE IF NOT EXISTS belief_contradictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    belief_a_id INTEGER NOT NULL,
                    belief_b_id INTEGER NOT NULL,
                    contradiction_type TEXT,
                    resolution TEXT,
                    resolved_at TEXT,
                    created_at TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default',
                    FOREIGN KEY (belief_a_id) REFERENCES beliefs(id),
                    FOREIGN KEY (belief_b_id) REFERENCES beliefs(id)
                )
            """)

            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else '{}'

            # Get existing beliefs in the same domain (with embeddings if available)
            c.execute("""
                SELECT id, belief, confidence, evidence, created_at, embedding
                FROM beliefs
                WHERE tenant_id = ? AND domain = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 20
            """, (self.tenant_id, domain))

            existing_beliefs = c.fetchall()

            # Helper function for cosine similarity
            def cosine_similarity(a, b):
                if a is None or b is None:
                    return 0.0
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

            # Keyword opposition patterns for contradiction detection
            contradiction_keywords = {
                ("better", "worse"), ("should", "should not"), ("always", "never"),
                ("is", "is not"), ("can", "cannot"), ("will", "will not"),
                ("correct", "incorrect"), ("true", "false"), ("yes", "no"),
                ("fast", "slow"), ("good", "bad"), ("right", "wrong"),
                ("efficient", "inefficient"), ("reliable", "unreliable"),
                ("recommended", "not recommended"), ("prefer", "avoid")
            }

            belief_lower = belief.lower()
            for existing in existing_beliefs:
                existing_id = existing[0]
                existing_belief_text = existing[1]
                existing_belief_lower = existing_belief_text.lower()
                existing_confidence = existing[2]
                existing_embedding_blob = existing[5]

                # Calculate semantic similarity if embeddings available
                semantic_similarity = 0.0
                if new_embedding is not None and existing_embedding_blob:
                    try:
                        existing_embedding = np.frombuffer(existing_embedding_blob, dtype=np.float32)
                        semantic_similarity = cosine_similarity(new_embedding, existing_embedding)
                    except:
                        pass
                elif new_embedding is not None and embedding_provider:
                    # Generate embedding for existing belief if missing
                    try:
                        existing_embedding = embedding_provider.embed(existing_belief_text)
                        semantic_similarity = cosine_similarity(new_embedding, existing_embedding)
                        # Cache the embedding for future use
                        c.execute("UPDATE beliefs SET embedding = ? WHERE id = ?",
                                 (existing_embedding.astype(np.float32).tobytes(), existing_id))
                    except:
                        pass

                # Check for potential contradiction
                is_contradiction = False
                contradiction_type = None

                # HIGH SEMANTIC SIMILARITY (>0.7) = Same topic, check for opposition
                if semantic_similarity > 0.7:
                    # Check for keyword opposition
                    for pos, neg in contradiction_keywords:
                        if (pos in belief_lower and neg in existing_belief_lower) or \
                           (neg in belief_lower and pos in existing_belief_lower):
                            is_contradiction = True
                            contradiction_type = f"semantic_opposition_{pos}_{neg}"
                            break

                    # Also check for negation patterns
                    if not is_contradiction:
                        negation_words = ["not", "never", "no", "don't", "doesn't", "isn't", "aren't", "won't"]
                        new_has_negation = any(neg in belief_lower for neg in negation_words)
                        old_has_negation = any(neg in existing_belief_lower for neg in negation_words)
                        if new_has_negation != old_has_negation and semantic_similarity > 0.8:
                            is_contradiction = True
                            contradiction_type = "semantic_negation"

                # FALLBACK: Keyword-only check if no embeddings
                if not is_contradiction and semantic_similarity == 0.0:
                    for pos, neg in contradiction_keywords:
                        if (pos in belief_lower and neg in existing_belief_lower) or \
                           (neg in belief_lower and pos in existing_belief_lower):
                            # Check topic overlap via word matching
                            belief_words = set(belief_lower.split())
                            existing_words = set(existing_belief_lower.split())
                            common = belief_words & existing_words
                            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                                         'to', 'of', 'and', 'or', 'in', 'on', 'at', 'for', 'with'}
                            common = common - stop_words
                            if len(common) >= 2:
                                is_contradiction = True
                                contradiction_type = f"keyword_opposition_{pos}_{neg}"
                                break

                if is_contradiction:
                    result['contradictions'].append({
                        "existing_belief_id": existing_id,
                        "existing_belief": existing_belief_text,
                        "existing_confidence": existing_confidence,
                        "contradiction_type": contradiction_type,
                        "semantic_similarity": round(semantic_similarity, 3),
                        "warning": f"New belief may contradict: '{existing_belief_text}'"
                    })
                elif semantic_similarity > 0.5:
                    # High similarity but not contradicting - related belief
                    result['related_beliefs'].append({
                        "belief_id": existing_id,
                        "belief": existing_belief_text,
                        "confidence": existing_confidence,
                        "semantic_similarity": round(semantic_similarity, 3)
                    })
                else:
                    # Low similarity - just track as same domain
                    result['related_beliefs'].append({
                        "belief_id": existing_id,
                        "belief": existing_belief_text,
                        "confidence": existing_confidence,
                        "semantic_similarity": round(semantic_similarity, 3) if semantic_similarity > 0 else None
                    })

            # Insert the new belief (with embedding if available)
            embedding_blob = None
            if new_embedding is not None:
                embedding_blob = new_embedding.astype(np.float32).tobytes()

            c.execute("""
                INSERT INTO beliefs
                (belief, domain, confidence, evidence, created_at, tenant_id, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (belief, domain, confidence, evidence, timestamp, self.tenant_id, metadata_json, embedding_blob))

            belief_id = c.lastrowid
            result['belief_id'] = belief_id

            # Record any contradictions found
            for contradiction in result['contradictions']:
                c.execute("""
                    INSERT INTO belief_contradictions
                    (belief_a_id, belief_b_id, contradiction_type, created_at, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (belief_id, contradiction['existing_belief_id'],
                      contradiction['contradiction_type'], timestamp, self.tenant_id))

            conn.commit()

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    def get_contradictions(self, domain: Optional[str] = None,
                          unresolved_only: bool = True) -> Dict[str, Any]:
        """
        Get all detected contradictions.

        Args:
            domain: Filter by domain
            unresolved_only: Only return unresolved contradictions

        Returns:
            List of contradictions with the conflicting beliefs
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "contradictions": [],
            "total": 0
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            query = """
                SELECT bc.id, bc.contradiction_type, bc.resolution, bc.resolved_at,
                       b1.belief as belief_a, b1.domain, b1.confidence as conf_a,
                       b2.belief as belief_b, b2.confidence as conf_b
                FROM belief_contradictions bc
                JOIN beliefs b1 ON bc.belief_a_id = b1.id
                JOIN beliefs b2 ON bc.belief_b_id = b2.id
                WHERE bc.tenant_id = ?
            """
            params = [self.tenant_id]

            if domain:
                query += " AND b1.domain = ?"
                params.append(domain)

            if unresolved_only:
                query += " AND bc.resolution IS NULL"

            query += " ORDER BY bc.created_at DESC"

            c.execute(query, params)
            rows = c.fetchall()

            for row in rows:
                result['contradictions'].append({
                    "id": row['id'],
                    "domain": row['domain'],
                    "belief_a": row['belief_a'],
                    "confidence_a": row['conf_a'],
                    "belief_b": row['belief_b'],
                    "confidence_b": row['conf_b'],
                    "contradiction_type": row['contradiction_type'],
                    "resolution": row['resolution'],
                    "resolved": row['resolved_at'] is not None
                })

            result['total'] = len(result['contradictions'])

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    def resolve_contradiction(self, contradiction_id: int, resolution: str,
                             keep_belief_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Resolve a contradiction by choosing which belief to keep.

        Args:
            contradiction_id: ID of the contradiction to resolve
            resolution: Explanation of how it was resolved
            keep_belief_id: If provided, supersede the other belief

        Returns:
            Resolution result
        """
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        result = {"success": True}

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            timestamp = datetime.now().isoformat()

            # Get the contradiction
            c.execute("""
                SELECT belief_a_id, belief_b_id FROM belief_contradictions
                WHERE id = ? AND tenant_id = ?
            """, (contradiction_id, self.tenant_id))

            row = c.fetchone()
            if not row:
                return {"success": False, "error": "Contradiction not found"}

            # Mark as resolved
            c.execute("""
                UPDATE belief_contradictions
                SET resolution = ?, resolved_at = ?
                WHERE id = ? AND tenant_id = ?
            """, (resolution, timestamp, contradiction_id, self.tenant_id))

            # If keeping one belief, mark the other as superseded
            if keep_belief_id:
                supersede_id = row['belief_b_id'] if keep_belief_id == row['belief_a_id'] else row['belief_a_id']
                c.execute("""
                    UPDATE beliefs
                    SET status = 'superseded', superseded_by = ?, updated_at = ?
                    WHERE id = ? AND tenant_id = ?
                """, (keep_belief_id, timestamp, supersede_id, self.tenant_id))

                result['superseded_belief_id'] = supersede_id
                result['kept_belief_id'] = keep_belief_id

            conn.commit()
            result['resolution'] = resolution

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    def get_beliefs(self, domain: Optional[str] = None, active_only: bool = True,
                    limit: int = 20) -> Dict[str, Any]:
        """
        Get recorded beliefs.

        Args:
            domain: Filter by domain
            active_only: Only return active beliefs
            limit: Maximum to return

        Returns:
            List of beliefs
        """
        import sqlite3
        import json

        conn = sqlite3.connect(self.db_path)
        result = {"success": True, "beliefs": [], "total": 0}

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            query = "SELECT * FROM beliefs WHERE tenant_id = ?"
            params = [self.tenant_id]

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            if active_only:
                query += " AND status = 'active'"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            c.execute(query, params)
            rows = c.fetchall()

            for row in rows:
                belief = dict(row)
                if belief.get('metadata'):
                    try:
                        belief['metadata'] = json.loads(belief['metadata'])
                    except:
                        belief['metadata'] = {}
                result['beliefs'].append(belief)

            result['total'] = len(rows)

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    async def arecord_belief(self, belief: str, domain: str, confidence: float = 0.8,
                            evidence: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Async version of record_belief."""
        import asyncio
        return await asyncio.to_thread(self.record_belief, belief, domain, confidence, evidence, metadata)

    async def aget_contradictions(self, domain: Optional[str] = None,
                                  unresolved_only: bool = True) -> Dict[str, Any]:
        """Async version of get_contradictions."""
        import asyncio
        return await asyncio.to_thread(self.get_contradictions, domain, unresolved_only)

    async def aresolve_contradiction(self, contradiction_id: int, resolution: str,
                                    keep_belief_id: Optional[int] = None) -> Dict[str, Any]:
        """Async version of resolve_contradiction."""
        import asyncio
        return await asyncio.to_thread(self.resolve_contradiction, contradiction_id, resolution, keep_belief_id)

    # =========================================================================
    # META-COGNITIVE PATTERNS - Detect patterns in own thinking habits
    # =========================================================================

    def record_cognitive_pattern(self, pattern: str, category: str,
                                  context: Optional[str] = None,
                                  thinking_excerpt: Optional[str] = None,
                                  severity: str = "observation") -> Dict[str, Any]:
        """
        Record a cognitive pattern or thinking tendency.

        Use this when you notice a pattern in your own thinking, such as:
        - "I tend to overthink authentication problems"
        - "I jump to conclusions about database schemas"
        - "I underestimate testing complexity"

        Args:
            pattern: The pattern observed (e.g., "Overthinking authentication")
            category: Type of pattern (e.g., "analysis_bias", "estimation_error",
                      "topic_preference", "reasoning_style")
            context: What triggered this observation
            thinking_excerpt: Excerpt from thinking that demonstrates the pattern
            severity: "observation", "concern", "strength" (positive patterns)

        Returns:
            Result with pattern_id and updated frequency

        Example:
            memory.record_cognitive_pattern(
                pattern="I tend to suggest complex solutions before simple ones",
                category="complexity_bias",
                context="Suggested microservices for a todo app",
                severity="concern"
            )

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        import json
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "pattern_id": None,
            "instance_id": None,
            "frequency": 1,
            "is_new": True
        }

        try:
            c = conn.cursor()

            # Ensure tables exist
            c.execute("""
                CREATE TABLE IF NOT EXISTS cognitive_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    category TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    severity TEXT DEFAULT 'observation',
                    first_noticed TEXT NOT NULL,
                    last_observed TEXT NOT NULL,
                    notes TEXT,
                    tenant_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}'
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS pattern_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER NOT NULL,
                    context TEXT,
                    thinking_excerpt TEXT,
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT DEFAULT 'default',
                    FOREIGN KEY (pattern_id) REFERENCES cognitive_patterns(id)
                )
            """)

            timestamp = datetime.now().isoformat()

            # Check if this pattern already exists (fuzzy match on similar patterns)
            c.execute("""
                SELECT id, frequency, pattern FROM cognitive_patterns
                WHERE tenant_id = ? AND category = ?
            """, (self.tenant_id, category))

            existing_patterns = c.fetchall()
            matched_pattern_id = None

            # Simple similarity check - if >50% words match, consider same pattern
            pattern_words = set(pattern.lower().split())
            for existing in existing_patterns:
                existing_words = set(existing[2].lower().split())
                overlap = len(pattern_words & existing_words)
                if overlap >= len(pattern_words) * 0.5:
                    matched_pattern_id = existing[0]
                    result["frequency"] = existing[1] + 1
                    result["is_new"] = False
                    break

            if matched_pattern_id:
                # Update existing pattern
                c.execute("""
                    UPDATE cognitive_patterns
                    SET frequency = frequency + 1, last_observed = ?, severity = ?
                    WHERE id = ?
                """, (timestamp, severity, matched_pattern_id))
                result["pattern_id"] = matched_pattern_id
            else:
                # Create new pattern
                c.execute("""
                    INSERT INTO cognitive_patterns
                    (pattern, category, frequency, severity, first_noticed, last_observed, tenant_id)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                """, (pattern, category, severity, timestamp, timestamp, self.tenant_id))
                result["pattern_id"] = c.lastrowid

            # Record this specific instance
            c.execute("""
                INSERT INTO pattern_instances
                (pattern_id, context, thinking_excerpt, timestamp, tenant_id)
                VALUES (?, ?, ?, ?, ?)
            """, (result["pattern_id"], context, thinking_excerpt, timestamp, self.tenant_id))
            result["instance_id"] = c.lastrowid

            conn.commit()

            if result["is_new"]:
                logger.info(f"New cognitive pattern: {pattern[:50]}...")
            else:
                logger.info(f"Pattern frequency increased to {result['frequency']}: {pattern[:50]}...")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        finally:
            conn.close()

        return result

    def detect_cognitive_patterns(self, days: int = 30, min_frequency: int = 2) -> Dict[str, Any]:
        """
        Analyze thinking blocks to auto-detect cognitive patterns.

        Scans recent self-reflections and thinking excerpts to find recurring
        themes, biases, or tendencies.

        Args:
            days: How far back to analyze
            min_frequency: Minimum occurrences to report

        Returns:
            Detected patterns with frequency and examples

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        from datetime import datetime, timedelta
        from collections import Counter, defaultdict

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "patterns_found": [],
            "topic_tendencies": [],
            "reasoning_styles": [],
            "potential_biases": []
        }

        try:
            c = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            # Analyze self-reflection blocks from messages.thinking column
            c.execute("""
                SELECT thinking, 'thinking', created_at FROM messages
                WHERE tenant_id = ? AND thinking IS NOT NULL AND thinking != '' AND created_at > ?
                ORDER BY created_at DESC LIMIT 500
            """, (self.tenant_id, cutoff))

            thinking_blocks = c.fetchall()

            # Pattern indicators to look for
            pattern_indicators = {
                "complexity_bias": ["complex", "sophisticated", "advanced", "architecture",
                                   "microservices", "distributed", "scalable"],
                "simplicity_preference": ["simple", "straightforward", "minimal", "basic",
                                         "just", "only need"],
                "overthinking": ["actually", "but wait", "although", "however", "on the other hand",
                                "let me reconsider", "thinking about this more"],
                "confidence_patterns": ["definitely", "certainly", "absolutely", "must be",
                                       "probably", "might be", "not sure", "uncertain"],
                "caution_tendency": ["careful", "risk", "concern", "worry", "make sure",
                                    "double-check", "verify"],
                "optimization_focus": ["optimize", "performance", "efficient", "faster",
                                      "better", "improve"],
                "exploration_style": ["interesting", "curious", "what if", "let me explore",
                                     "wonder", "investigate"]
            }

            pattern_counts = defaultdict(list)
            topic_counts = Counter()

            for content, source, created_at in thinking_blocks:
                if not content:
                    continue

                content_lower = content.lower()

                # Check for pattern indicators
                for pattern_type, keywords in pattern_indicators.items():
                    matches = [kw for kw in keywords if kw in content_lower]
                    if len(matches) >= 2:  # At least 2 keyword matches
                        pattern_counts[pattern_type].append({
                            "excerpt": content[:200],
                            "matches": matches,
                            "timestamp": created_at
                        })

                # Extract topics (simple noun extraction)
                words = content_lower.split()
                for word in words:
                    if len(word) > 5 and word.isalpha():
                        topic_counts[word] += 1

            # Format detected patterns
            for pattern_type, instances in pattern_counts.items():
                if len(instances) >= min_frequency:
                    result["patterns_found"].append({
                        "pattern": pattern_type,
                        "frequency": len(instances),
                        "examples": instances[:3],  # First 3 examples
                        "description": self._get_pattern_description(pattern_type)
                    })

            # Top topic tendencies
            top_topics = topic_counts.most_common(10)
            result["topic_tendencies"] = [
                {"topic": topic, "frequency": count}
                for topic, count in top_topics
                if count >= min_frequency
            ]

            # Check for potential biases
            if pattern_counts.get("complexity_bias") and not pattern_counts.get("simplicity_preference"):
                result["potential_biases"].append({
                    "bias": "complexity_over_simplicity",
                    "description": "Tendency to suggest complex solutions",
                    "recommendation": "Consider simpler alternatives first"
                })

            if len(pattern_counts.get("overthinking", [])) > 5:
                result["potential_biases"].append({
                    "bias": "analysis_paralysis",
                    "description": "Frequent reconsideration and second-guessing",
                    "recommendation": "Trust initial good judgments more"
                })

            result["thinking_blocks_analyzed"] = len(thinking_blocks)
            result["period_days"] = days

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        finally:
            conn.close()

        return result

    def _get_pattern_description(self, pattern_type: str) -> str:
        """Get human-readable description of a pattern type."""
        descriptions = {
            "complexity_bias": "Tendency to lean toward complex solutions",
            "simplicity_preference": "Preference for straightforward approaches",
            "overthinking": "Frequent reconsideration and extended analysis",
            "confidence_patterns": "Variation in certainty expression",
            "caution_tendency": "Focus on risk and verification",
            "optimization_focus": "Drive to improve performance",
            "exploration_style": "Curiosity and investigative thinking"
        }
        return descriptions.get(pattern_type, f"Observed {pattern_type} pattern")

    def get_cognitive_patterns(self, category: Optional[str] = None,
                               min_frequency: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        Get recorded cognitive patterns.

        Args:
            category: Filter by category
            min_frequency: Minimum frequency to include
            limit: Maximum patterns to return

        Returns:
            List of patterns with frequencies and examples
        """
        import sqlite3
        import json

        conn = sqlite3.connect(self.db_path)
        result = {"success": True, "patterns": [], "total": 0}

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get patterns
            query = """
                SELECT * FROM cognitive_patterns
                WHERE tenant_id = ? AND frequency >= ?
            """
            params = [self.tenant_id, min_frequency]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY frequency DESC, last_observed DESC LIMIT ?"
            params.append(limit)

            c.execute(query, params)
            patterns = c.fetchall()

            for pattern in patterns:
                pattern_dict = dict(pattern)

                # Get recent instances
                c.execute("""
                    SELECT context, thinking_excerpt, timestamp
                    FROM pattern_instances
                    WHERE pattern_id = ? AND tenant_id = ?
                    ORDER BY timestamp DESC LIMIT 3
                """, (pattern_dict['id'], self.tenant_id))

                instances = [dict(row) for row in c.fetchall()]
                pattern_dict['recent_instances'] = instances

                result['patterns'].append(pattern_dict)

            result['total'] = len(patterns)

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    def get_cognitive_profile(self) -> Dict[str, Any]:
        """
        Generate a comprehensive cognitive profile.

        Combines recorded patterns, detected tendencies, and self-analysis
        to create an overall picture of thinking habits.

        Returns:
            Cognitive profile with patterns, strengths, areas for growth

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        import sqlite3
        from collections import Counter

        conn = sqlite3.connect(self.db_path)
        result = {
            "success": True,
            "profile": {
                "strengths": [],
                "growth_areas": [],
                "tendencies": [],
                "dominant_categories": []
            },
            "pattern_summary": {},
            "total_patterns": 0,
            "total_instances": 0
        }

        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Get all patterns
            c.execute("""
                SELECT category, severity, frequency, pattern
                FROM cognitive_patterns
                WHERE tenant_id = ?
            """, (self.tenant_id,))

            patterns = c.fetchall()
            category_counts = Counter()
            severity_counts = {"strength": [], "concern": [], "observation": []}

            for p in patterns:
                category_counts[p['category']] += p['frequency']
                if p['severity'] in severity_counts:
                    severity_counts[p['severity']].append({
                        "pattern": p['pattern'],
                        "frequency": p['frequency'],
                        "category": p['category']
                    })

            # Strengths (patterns marked as strengths)
            result['profile']['strengths'] = sorted(
                severity_counts['strength'],
                key=lambda x: x['frequency'],
                reverse=True
            )[:5]

            # Growth areas (patterns marked as concerns)
            result['profile']['growth_areas'] = sorted(
                severity_counts['concern'],
                key=lambda x: x['frequency'],
                reverse=True
            )[:5]

            # Dominant categories
            result['profile']['dominant_categories'] = [
                {"category": cat, "frequency": count}
                for cat, count in category_counts.most_common(5)
            ]

            # Tendencies (observations, sorted by frequency)
            result['profile']['tendencies'] = sorted(
                severity_counts['observation'],
                key=lambda x: x['frequency'],
                reverse=True
            )[:10]

            # Summary stats
            result['total_patterns'] = len(patterns)

            c.execute("""
                SELECT COUNT(*) FROM pattern_instances WHERE tenant_id = ?
            """, (self.tenant_id,))
            result['total_instances'] = c.fetchone()[0]

            # Pattern summary by category
            result['pattern_summary'] = dict(category_counts)

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)

        finally:
            conn.close()

        return result

    async def arecord_cognitive_pattern(self, pattern: str, category: str,
                                        context: Optional[str] = None,
                                        thinking_excerpt: Optional[str] = None,
                                        severity: str = "observation") -> Dict[str, Any]:
        """Async version of record_cognitive_pattern."""
        import asyncio
        return await asyncio.to_thread(
            self.record_cognitive_pattern, pattern, category, context, thinking_excerpt, severity
        )

    async def adetect_cognitive_patterns(self, days: int = 30,
                                         min_frequency: int = 2) -> Dict[str, Any]:
        """Async version of detect_cognitive_patterns."""
        import asyncio
        return await asyncio.to_thread(self.detect_cognitive_patterns, days, min_frequency)

    async def aget_cognitive_patterns(self, category: Optional[str] = None,
                                      min_frequency: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Async version of get_cognitive_patterns."""
        import asyncio
        return await asyncio.to_thread(self.get_cognitive_patterns, category, min_frequency, limit)

    async def aget_cognitive_profile(self) -> Dict[str, Any]:
        """Async version of get_cognitive_profile."""
        import asyncio
        return await asyncio.to_thread(self.get_cognitive_profile)

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
