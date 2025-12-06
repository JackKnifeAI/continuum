#!/usr/bin/env python3
"""
CONTINUUM Auto-Learning Example
=================================

Demonstrates automatic concept extraction from conversations.
The system learns concepts automatically without manual tagging.
"""

from pathlib import Path
import re
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

# Configure memory system
config = MemoryConfig(
    db_path=Path("./demo_learning.db"),
    tenant_id="demo_user"
)
set_config(config)
storage = SQLiteBackend(config.db_path)

def extract_concepts(text: str) -> list:
    """
    Simple concept extractor (production version uses NLP).
    Extracts capitalized phrases and technical terms.
    """
    # Extract capitalized multi-word terms (e.g., "Machine Learning")
    patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Multi-word capitalized
        r'\b\w+\s+(?:learning|system|network|model|algorithm)\b',  # Technical patterns
        r'\b(?:π×φ|AI|ML|NLP)\b',  # Acronyms and symbols
    ]

    concepts = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        concepts.update(m.strip() for m in matches)

    return [c for c in concepts if config.min_concept_length <= len(c) <= config.max_concept_length]

def auto_learn_from_message(content: str):
    """Automatically extract and store concepts from a message."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        # Store the message
        cursor.execute("""
            INSERT INTO sessions (tenant_id, summary) VALUES (?, ?)
        """, (config.tenant_id, "Auto-learning demo"))
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO messages (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, "user", content))

        # Extract concepts automatically
        concepts = extract_concepts(content)
        print(f"🧠 Extracted {len(concepts)} concepts: {concepts}")

        # Store concepts in knowledge graph
        for concept in concepts[:config.max_concepts_per_message]:
            cursor.execute("""
                INSERT OR IGNORE INTO entities (tenant_id, name, entity_type, description)
                VALUES (?, ?, 'concept', ?)
            """, (config.tenant_id, concept, f"Auto-extracted from conversation"))

        conn.commit()
        return concepts

def show_learned_concepts():
    """Display all concepts the system has learned."""
    with storage.connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, entity_type, description
            FROM entities
            WHERE tenant_id = ? AND entity_type = 'concept'
            ORDER BY name
        """, (config.tenant_id,))

        concepts = cursor.fetchall()

        print(f"\n📚 Learned concepts ({len(concepts)} total):")
        for name, etype, desc in concepts:
            print(f"  • {name}")

if __name__ == "__main__":
    # Demo: The system learns from natural conversation
    messages = [
        "I'm researching Machine Learning and Neural Networks for my project.",
        "The Deep Learning model uses Gradient Descent for optimization.",
        "Natural Language Processing helps computers understand human language.",
    ]

    print("🎓 Auto-learning from conversation...\n")

    for msg in messages:
        print(f"Message: {msg}")
        auto_learn_from_message(msg)
        print()

    # Show what the system learned
    show_learned_concepts()

    print(f"\n✨ Knowledge automatically accumulated at: {config.db_path}")
