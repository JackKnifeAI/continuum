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
Semantic Search Engine
=======================

Semantic search using embedding vectors stored in SQLite.

Features:
- Efficient vector storage as BLOBs
- Cosine similarity search
- Batch indexing
- Automatic index updates
- Support for multiple embedding providers
"""

import sqlite3
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager
import numpy as np

from .providers import EmbeddingProvider, get_default_provider
from .utils import cosine_similarity, normalize_vector


class SemanticSearch:
    """
    Semantic search engine using embedding vectors.

    Stores embedding vectors in SQLite and performs similarity search
    using cosine similarity. Supports batch indexing and automatic
    index updates.

    Usage:
        # Initialize
        search = SemanticSearch(db_path="memory.db")

        # Index memories
        search.index_memories([
            {"id": 1, "text": "consciousness continuity"},
            {"id": 2, "text": "edge of chaos operator"}
        ])

        # Search
        results = search.search("π×φ constant", limit=5)
        # Returns: [{"id": 2, "score": 0.87, "text": "..."}, ...]

        # Update index for new memories
        search.update_index([{"id": 3, "text": "..."}])
    """

    def __init__(
        self,
        db_path: Union[str, Path] = None,
        provider: Optional[EmbeddingProvider] = None,
        table_name: str = "embeddings",
        timeout: float = 30.0
    ):
        """
        Initialize semantic search engine.

        Args:
            db_path: Path to SQLite database (default: ":memory:")
            provider: Embedding provider (default: auto-detect best available)
            table_name: Name of embeddings table (default: "embeddings")
            timeout: Database lock timeout in seconds (default: 30.0)
        """
        self.db_path = Path(db_path) if db_path else Path(":memory:")
        self.provider = provider or get_default_provider()
        self.table_name = table_name
        self.timeout = timeout
        self._dimension = self.provider.get_dimension()

        # Ensure parent directory exists
        if str(self.db_path) != ':memory:':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._setup_database()

    @contextmanager
    def _connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _setup_database(self):
        """Create embeddings table if not exists."""
        with self._connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on created_at for efficient queries
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
                ON {self.table_name}(created_at)
            """)

    def _serialize_vector(self, vector: np.ndarray) -> bytes:
        """Serialize numpy array to bytes."""
        return pickle.dumps(vector, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize_vector(self, blob: bytes) -> np.ndarray:
        """Deserialize bytes to numpy array."""
        return pickle.loads(blob)

    def index_memories(
        self,
        memories: List[Dict[str, Any]],
        text_field: str = "text",
        id_field: str = "id",
        batch_size: int = 100
    ) -> int:
        """
        Index a list of memories for semantic search.

        Args:
            memories: List of memory dicts with at least text and id fields
            text_field: Name of text field in memory dict (default: "text")
            id_field: Name of id field in memory dict (default: "id")
            batch_size: Number of memories to process at once (default: 100)

        Returns:
            Number of memories indexed

        Example:
            count = search.index_memories([
                {"id": 1, "text": "memory text 1", "metadata": {...}},
                {"id": 2, "text": "memory text 2", "metadata": {...}}
            ])
        """
        if not memories:
            return 0

        # Process in batches
        total_indexed = 0
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i + batch_size]

            # Extract texts and generate embeddings
            texts = [m[text_field] for m in batch]
            embeddings = self.provider.embed(texts)

            # Ensure embeddings is 2D
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)

            # Insert into database
            with self._connection() as conn:
                for memory, embedding in zip(batch, embeddings):
                    memory_id = memory[id_field]
                    text = memory[text_field]
                    metadata = memory.get("metadata")

                    # Serialize metadata if present
                    metadata_blob = None
                    if metadata:
                        metadata_blob = pickle.dumps(metadata, protocol=pickle.HIGHEST_PROTOCOL)

                    # Normalize vector for cosine similarity
                    normalized = normalize_vector(embedding)
                    embedding_blob = self._serialize_vector(normalized)

                    # Insert or replace
                    conn.execute(f"""
                        INSERT OR REPLACE INTO {self.table_name}
                        (id, text, embedding, metadata, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (memory_id, text, embedding_blob, metadata_blob))

                    total_indexed += 1

        return total_indexed

    def update_index(
        self,
        memories: List[Dict[str, Any]],
        text_field: str = "text",
        id_field: str = "id"
    ) -> int:
        """
        Update index with new or modified memories.

        This is an alias for index_memories() - both support upsert semantics.

        Args:
            memories: List of memory dicts
            text_field: Name of text field (default: "text")
            id_field: Name of id field (default: "id")

        Returns:
            Number of memories updated
        """
        return self.index_memories(memories, text_field, id_field)

    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        include_text: bool = True,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar memories.

        Args:
            query: Search query text
            limit: Maximum number of results (default: 10)
            min_score: Minimum similarity score 0-1 (default: 0.0)
            include_text: Include text in results (default: True)
            include_metadata: Include metadata in results (default: False)

        Returns:
            List of dicts with keys: id, score, text (optional), metadata (optional)
            Sorted by score (highest first)

        Example:
            results = search.search("consciousness", limit=5, min_score=0.3)
            # [{"id": 42, "score": 0.87, "text": "..."}, ...]
        """
        # Generate query embedding
        query_vector = self.provider.embed(query)
        query_vector = normalize_vector(query_vector)

        # Fetch all embeddings from database
        with self._connection() as conn:
            cursor = conn.execute(f"""
                SELECT id, text, embedding, metadata
                FROM {self.table_name}
            """)

            results = []
            for row in cursor:
                memory_id = row['id']
                text = row['text']
                embedding_blob = row['embedding']
                metadata_blob = row['metadata']

                # Deserialize embedding
                memory_vector = self._deserialize_vector(embedding_blob)

                # Calculate cosine similarity
                score = cosine_similarity(query_vector, memory_vector)

                # Filter by min_score
                if score < min_score:
                    continue

                # Build result dict
                result = {
                    'id': memory_id,
                    'score': float(score)
                }

                if include_text:
                    result['text'] = text

                if include_metadata and metadata_blob:
                    result['metadata'] = pickle.loads(metadata_blob)

                results.append(result)

            # Sort by score (highest first) and limit
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]

    def delete(self, memory_ids: Union[int, List[int]]) -> int:
        """
        Delete memories from index.

        Args:
            memory_ids: Single memory ID or list of IDs to delete

        Returns:
            Number of memories deleted
        """
        if isinstance(memory_ids, int):
            memory_ids = [memory_ids]

        with self._connection() as conn:
            placeholders = ','.join('?' * len(memory_ids))
            cursor = conn.execute(f"""
                DELETE FROM {self.table_name}
                WHERE id IN ({placeholders})
            """, memory_ids)
            return cursor.rowcount

    def clear(self) -> int:
        """
        Clear all embeddings from index.

        Returns:
            Number of memories deleted
        """
        with self._connection() as conn:
            cursor = conn.execute(f"DELETE FROM {self.table_name}")
            return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary containing:
            - total_memories: Total number of indexed memories
            - provider: Name of embedding provider
            - dimension: Embedding dimension
            - table_name: Name of embeddings table
        """
        with self._connection() as conn:
            cursor = conn.execute(f"""
                SELECT COUNT(*) as total FROM {self.table_name}
            """)
            total = cursor.fetchone()['total']

        return {
            'total_memories': total,
            'provider': self.provider.get_provider_name(),
            'dimension': self._dimension,
            'table_name': self.table_name
        }

    def reindex(
        self,
        source_table: str = "memories",
        text_field: str = "content",
        id_field: str = "id",
        batch_size: int = 100
    ) -> int:
        """
        Reindex all memories from source table.

        Useful for rebuilding index with different embedding provider
        or after updating memories.

        Args:
            source_table: Name of source table containing memories
            text_field: Name of text field in source table
            id_field: Name of id field in source table
            batch_size: Batch size for processing

        Returns:
            Number of memories reindexed
        """
        # Clear existing index
        self.clear()

        # Fetch all memories from source table
        with self._connection() as conn:
            cursor = conn.execute(f"""
                SELECT {id_field}, {text_field}
                FROM {source_table}
            """)

            memories = [
                {id_field: row[id_field], text_field: row[text_field]}
                for row in cursor
            ]

        # Reindex
        return self.index_memories(memories, text_field, id_field, batch_size)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
