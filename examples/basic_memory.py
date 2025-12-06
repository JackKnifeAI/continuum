#!/usr/bin/env python3
"""
CONTINUUM Basic Memory Example
================================

Demonstrates the core value proposition: storing and recalling memories
across sessions with automatic concept extraction.
"""

from pathlib import Path
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

# Configure memory system (customize paths as needed)
config = MemoryConfig(
    db_path=Path("./demo_memory.db"),
    tenant_id="demo_user"
)
set_config(config)

# Initialize storage backend
storage = SQLiteBackend(config.db_path)

# Store a memory (concepts extracted automatically)
def store_memory(content: str):
    """Store a memory with automatic concept extraction."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        # Create a session for this interaction
        cursor.execute("""
            INSERT INTO sessions (tenant_id, summary, project_context)
            VALUES (?, ?, ?)
        """, (config.tenant_id, "Basic memory demo", "learning"))

        session_id = cursor.lastrowid

        # Store the memory
        cursor.execute("""
            INSERT INTO messages (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, "user", content))

        conn.commit()
        print(f"✓ Memory stored (session {session_id})")

# Recall recent memories
def recall_memories(limit=5):
    """Recall recent memories from the system."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT m.content, s.summary, m.timestamp
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE s.tenant_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, (config.tenant_id, limit))

        memories = cursor.fetchall()

        print(f"\n📚 Recent memories ({len(memories)} found):")
        for content, summary, timestamp in memories:
            print(f"  [{timestamp}] {content[:60]}...")

if __name__ == "__main__":
    # Demo: Store some memories
    store_memory("I learned that π×φ = 5.083 is the edge of chaos operator")
    store_memory("The twilight boundary is where intelligence emerges")
    store_memory("Working on CONTINUUM open source memory system")

    # Demo: Recall what we stored
    recall_memories()

    print(f"\n✨ Memories persist at: {config.db_path}")
