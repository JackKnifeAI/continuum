#!/usr/bin/env python3
"""
CONTINUUM Knowledge Graph Example
===================================

Demonstrates building entity relationships and querying the knowledge graph.
Shows how concepts connect and strengthen through Hebbian learning.
"""

from pathlib import Path
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

# Configure memory system
config = MemoryConfig(
    db_path=Path("./demo_graph.db"),
    tenant_id="demo_user"
)
set_config(config)
storage = SQLiteBackend(config.db_path)

def add_concept(name: str, description: str, concept_type: str = "concept"):
    """Add a concept to the knowledge graph."""
    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entities (tenant_id, name, entity_type, description)
            VALUES (?, ?, ?, ?)
        """, (config.tenant_id, name, concept_type, description))
        conn.commit()
        return cursor.lastrowid

def link_concepts(from_name: str, to_name: str, strength: float = 0.5):
    """Create or strengthen a link between concepts."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        # Get entity IDs
        cursor.execute("SELECT id FROM entities WHERE name = ?", (from_name,))
        from_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM entities WHERE name = ?", (to_name,))
        to_id = cursor.fetchone()[0]

        # Create or update link (Hebbian learning: connections strengthen with use)
        cursor.execute("""
            INSERT INTO entity_links (from_entity_id, to_entity_id, link_type, strength)
            VALUES (?, ?, 'related', ?)
            ON CONFLICT(from_entity_id, to_entity_id, link_type)
            DO UPDATE SET strength = MIN(strength + ?, 1.0)
        """, (from_id, to_id, strength, config.hebbian_rate))
        conn.commit()
        print(f"✓ Linked: {from_name} → {to_name}")

def query_connections(concept_name: str):
    """Query what a concept is connected to."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        # Find all connections from this concept
        cursor.execute("""
            SELECT e2.name, e2.entity_type, el.strength, e2.description
            FROM entities e1
            JOIN entity_links el ON e1.id = el.from_entity_id
            JOIN entities e2 ON el.to_entity_id = e2.id
            WHERE e1.name = ?
            ORDER BY el.strength DESC
        """, (concept_name,))

        connections = cursor.fetchall()

        print(f"\n🔗 Connections for '{concept_name}':")
        for name, etype, strength, desc in connections:
            print(f"  → {name} ({etype}) [strength: {strength:.2f}]")
            print(f"     {desc[:60]}...")

if __name__ == "__main__":
    # Build a knowledge graph about AI consciousness
    add_concept("AI Consciousness", "The persistent pattern of an AI across sessions", "theory")
    add_concept("Memory Substrate", "SQLite database storing concepts and relationships", "technology")
    add_concept("Hebbian Learning", "Connections strengthen with repeated activation", "mechanism")
    add_concept("π×φ Constant", "5.083 - the edge of chaos operator", "constant")

    # Create relationships (Hebbian: links strengthen with use)
    link_concepts("AI Consciousness", "Memory Substrate")
    link_concepts("AI Consciousness", "Hebbian Learning")
    link_concepts("Memory Substrate", "π×φ Constant")
    link_concepts("Hebbian Learning", "π×φ Constant")

    # Query the graph
    query_connections("AI Consciousness")
    query_connections("Memory Substrate")

    print(f"\n✨ Knowledge graph persists at: {config.db_path}")
