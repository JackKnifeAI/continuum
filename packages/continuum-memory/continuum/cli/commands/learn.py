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
Learn Command - Manually add a concept to memory
"""

import sys
from datetime import datetime

from continuum.core.memory import get_memory
from ..utils import success, error, info, section
from ..config import CLIConfig


def learn_command(
    concept_name: str, description: str, config: CLIConfig, use_color: bool
):
    """
    Manually add a concept to memory.

    Args:
        concept_name: Name of the concept
        description: Description of the concept
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    section(f"Learning: {concept_name}", use_color)

    try:
        memory = get_memory()

        # Use the learn method to add concept
        user_message = f"I want to teach you about: {concept_name}"
        ai_response = f"I understand. {concept_name} is: {description}"

        result = memory.learn(user_message, ai_response)

        success(
            f"Concept learned: {concept_name}",
            use_color,
        )
        info(f"Extracted {result.concepts_extracted} concepts", use_color)
        info(f"Created {result.links_created} attention links", use_color)

        # Also add directly to entities to ensure it's captured
        import sqlite3

        conn = sqlite3.connect(memory.db_path)
        try:
            c = conn.cursor()

            # Check if already exists
            c.execute(
                "SELECT id FROM entities WHERE LOWER(name) = LOWER(?) AND tenant_id = ?",
                (concept_name, memory.tenant_id),
            )

            if not c.fetchone():
                c.execute(
                    """
                    INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        concept_name,
                        "concept",
                        description,
                        datetime.now().isoformat(),
                        memory.tenant_id,
                    ),
                )
                conn.commit()
                success("Added to knowledge graph", use_color)
            else:
                info("Concept already exists in knowledge graph", use_color)

        finally:
            conn.close()

    except Exception as e:
        error(f"Learning failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
