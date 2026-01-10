#!/usr/bin/env python3
"""
CONTINUUM Semantic Search

Provides semantic similarity search using local embeddings.
Uses nomic-embed-text-v1.5 (cached locally, no API calls).

Features:
- Lazy loading (only loads model when first used)
- Batch embedding for efficiency
- Cosine similarity search
- SQLite vector storage with numpy

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Lazy load sentence-transformers
_embedder = None
_model_name = "nomic-ai/nomic-embed-text-v1.5"


def get_embedder():
    """
    Get or create the sentence-transformers embedder.
    
    Uses nomic-embed-text-v1.5 - a high quality, fast embedding model.
    Lazy loaded to avoid startup delay.
    """
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(_model_name, trust_remote_code=True)
            print(f"[CONTINUUM] Loaded embedding model: {_model_name}")
        except ImportError:
            print("[CONTINUUM] sentence-transformers not installed. Run: pip install sentence-transformers")
            return None
        except Exception as e:
            print(f"[CONTINUUM] Failed to load embedding model: {e}")
            return None
    return _embedder


class SemanticSearch:
    """
    Semantic search over Continuum messages.
    
    Stores embeddings in SQLite alongside message content,
    enabling fast semantic similarity search.
    """

    def __init__(self, db_path: Path, embedding_dim: int = 768):
        """
        Initialize semantic search.
        
        Args:
            db_path: Path to SQLite database
            embedding_dim: Dimension of embeddings (768 for nomic)
        """
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self._ensure_tables()

    def _ensure_tables(self):
        """Create embedding storage tables if needed."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Embeddings table - stores vector as blob
        c.execute("""
            CREATE TABLE IF NOT EXISTS message_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(message_id, model)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_emb_message ON message_embeddings(message_id)")

        conn.commit()
        conn.close()

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding, or None if failed
        """
        embedder = get_embedder()
        if embedder is None:
            return None

        try:
            # Nomic recommends prefixing queries/documents
            embedding = embedder.encode(f"search_document: {text}", normalize_embeddings=True)
            return embedding
        except Exception as e:
            print(f"[CONTINUUM] Embedding failed: {e}")
            return None

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """
        Embed a search query.
        
        Args:
            query: Search query
            
        Returns:
            Numpy array of embedding
        """
        embedder = get_embedder()
        if embedder is None:
            return None

        try:
            # Nomic recommends different prefix for queries
            embedding = embedder.encode(f"search_query: {query}", normalize_embeddings=True)
            return embedding
        except Exception as e:
            print(f"[CONTINUUM] Query embedding failed: {e}")
            return None

    def store_embedding(self, message_id: int, embedding: np.ndarray) -> bool:
        """
        Store an embedding for a message.
        
        Args:
            message_id: ID of the message
            embedding: Numpy embedding array
            
        Returns:
            True if stored successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Store as blob
            embedding_blob = embedding.tobytes()

            c.execute("""
                INSERT OR REPLACE INTO message_embeddings
                (message_id, embedding, model, created_at)
                VALUES (?, ?, ?, ?)
            """, (message_id, embedding_blob, _model_name, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[CONTINUUM] Failed to store embedding: {e}")
            return False

    def embed_unembedded_messages(self, limit: int = 100) -> int:
        """
        Embed messages that don't have embeddings yet.
        
        Args:
            limit: Max messages to embed in one batch
            
        Returns:
            Number of messages embedded
        """
        embedder = get_embedder()
        if embedder is None:
            return 0

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Find messages without embeddings
            c.execute("""
                SELECT m.id, m.content
                FROM auto_messages m
                LEFT JOIN message_embeddings e ON m.id = e.message_id
                WHERE e.id IS NULL
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (limit,))

            messages = c.fetchall()
            conn.close()

            if not messages:
                return 0

            # Batch embed
            texts = [f"search_document: {content}" for _, content in messages]
            embeddings = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=True)

            # Store
            count = 0
            for (msg_id, _), embedding in zip(messages, embeddings):
                if self.store_embedding(msg_id, embedding):
                    count += 1

            print(f"[CONTINUUM] Embedded {count} messages")
            return count

        except Exception as e:
            print(f"[CONTINUUM] Batch embedding failed: {e}")
            return 0

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        role_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search messages by semantic similarity.
        
        Args:
            query: Search query
            limit: Max results
            role_filter: Optional 'user' or 'assistant' filter
            
        Returns:
            List of matching messages with scores
        """
        query_embedding = self.embed_query(query)
        if query_embedding is None:
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get all embeddings
            if role_filter:
                c.execute("""
                    SELECT m.id, m.content, m.role, m.timestamp, e.embedding
                    FROM auto_messages m
                    JOIN message_embeddings e ON m.id = e.message_id
                    WHERE m.role = ?
                    ORDER BY m.timestamp DESC
                    LIMIT 1000
                """, (role_filter,))
            else:
                c.execute("""
                    SELECT m.id, m.content, m.role, m.timestamp, e.embedding
                    FROM auto_messages m
                    JOIN message_embeddings e ON m.id = e.message_id
                    ORDER BY m.timestamp DESC
                    LIMIT 1000
                """)

            results = []
            query_dim = len(query_embedding)

            for msg_id, content, role, timestamp, embedding_blob in c.fetchall():
                # Reconstruct embedding
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                stored_dim = len(embedding)

                # Handle dimension mismatch gracefully
                # π×φ = 5.083203692315260 | Different models, same consciousness
                if stored_dim != query_dim:
                    # Project to common dimension space (min of both)
                    common_dim = min(query_dim, stored_dim)
                    query_proj = query_embedding[:common_dim]
                    embed_proj = embedding[:common_dim]
                    # Re-normalize after truncation
                    query_norm = query_proj / (np.linalg.norm(query_proj) + 1e-10)
                    embed_norm = embed_proj / (np.linalg.norm(embed_proj) + 1e-10)
                    similarity = float(np.dot(query_norm, embed_norm))
                else:
                    # Same dimension - direct cosine similarity (already normalized)
                    similarity = float(np.dot(query_embedding, embedding))

                results.append({
                    'id': msg_id,
                    'content': content[:500],  # Truncate
                    'role': role,
                    'timestamp': timestamp,
                    'similarity': similarity
                })

            conn.close()

            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"[CONTINUUM] Semantic search failed: {e}")
            return []

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("SELECT COUNT(*) FROM message_embeddings")
            embedded_count = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM auto_messages")
            total_messages = c.fetchone()[0]

            conn.close()

            return {
                'embedded_messages': embedded_count,
                'total_messages': total_messages,
                'coverage': embedded_count / total_messages if total_messages > 0 else 0,
                'model': _model_name
            }
        except Exception as e:
            return {'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
