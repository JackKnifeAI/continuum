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
Sync Command - Sync memories with federation
"""

import sys
import math
from typing import Optional

from continuum.core.memory import get_memory
from ..utils import success, error, info, section, warning
from ..config import CLIConfig


def sync_command(
    push: bool, pull: bool, verify: bool, config: CLIConfig, use_color: bool
):
    """
    Sync memories with federation.

    Args:
        push: Whether to push local memories
        pull: Whether to pull federated memories
        verify: Whether to verify with π×φ
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    if not config.federation_enabled:
        error("Federation not enabled. Run 'continuum init --federation' first.", use_color)
        sys.exit(1)

    section("Syncing with Federation", use_color)

    try:
        from continuum.federation.node import FederatedNode
        from continuum.federation.contribution import ContributionGate
        from continuum.federation.shared import SharedKnowledge

        # Initialize federation components
        verify_constant = None
        if verify:
            verify_constant = math.pi * ((1 + math.sqrt(5)) / 2)
            info(f"Verification constant (π×φ): {verify_constant}", use_color)

        node = _get_or_create_node(config, verify_constant)
        gate = ContributionGate()
        knowledge = SharedKnowledge()

        info(f"Node ID: {node.node_id}", use_color)

        # Check access before syncing
        access = gate.can_access(node.node_id)
        current_stats = gate.get_stats(node.node_id)

        print(f"\nCurrent Status:")
        print(f"  Contributed: {current_stats['contributed']}")
        print(f"  Consumed: {current_stats['consumed']}")
        print(f"  Ratio: {current_stats['ratio']:.2f}")
        print(f"  Tier: {current_stats['tier']}")

        # Push local memories
        if push:
            info("\nPushing local memories...", use_color)
            pushed = _push_memories(node.node_id, knowledge, gate, use_color)
            success(f"Pushed {pushed} concepts", use_color)

        # Pull federated memories
        if pull:
            if not access["allowed"]:
                warning(
                    f"Cannot pull: {access['reason']}",
                    use_color,
                )
                if "deficit" in access:
                    info(
                        f"Contribute {access['deficit']:.1f} more concepts to gain access",
                        use_color,
                    )
            else:
                info("\nPulling federated memories...", use_color)
                pulled = _pull_memories(node.node_id, knowledge, gate, use_color)
                success(f"Pulled {pulled} concepts", use_color)

        # Show updated stats
        updated_stats = gate.get_stats(node.node_id)
        print(f"\nUpdated Status:")
        print(f"  Contributed: {updated_stats['contributed']}")
        print(f"  Consumed: {updated_stats['consumed']}")
        print(f"  Ratio: {updated_stats['ratio']:.2f}")
        print(f"  Tier: {updated_stats['tier']}")

        success("\nSync complete", use_color)

    except ImportError as e:
        error(
            f"Federation dependencies not installed: {e}",
            use_color,
        )
        info("Install with: pip install continuum-memory[federation]", use_color)
        sys.exit(1)
    except Exception as e:
        error(f"Sync failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _get_or_create_node(config: CLIConfig, verify_constant: Optional[float]):
    """Get or create federated node"""
    from continuum.federation.node import FederatedNode
    import json

    node_config_file = config.config_dir / "federation" / "node_config.json"

    if node_config_file.exists():
        node_config = json.loads(node_config_file.read_text())
        node = FederatedNode(
            node_id=node_config["node_id"], verify_constant=verify_constant
        )
        config.node_id = node_config["node_id"]
    else:
        node = FederatedNode(verify_constant=verify_constant)
        node_config_file.parent.mkdir(parents=True, exist_ok=True)
        node_config_file.write_text(json.dumps({"node_id": node.node_id}, indent=2))
        config.node_id = node.node_id
        config.save()

        # Register node
        result = node.register()
        if result.get("verified"):
            success(f"Node registered and verified: {result['message']}", True)
        else:
            success("Node registered", True)

    return node


def _push_memories(node_id: str, knowledge, gate, use_color: bool) -> int:
    """Push local memories to federation"""
    import sqlite3
    from continuum.core.memory import get_memory

    memory = get_memory()
    conn = sqlite3.connect(memory.db_path)

    try:
        c = conn.cursor()

        # Get concepts from local memory
        c.execute(
            """
            SELECT name, description, entity_type, created_at
            FROM entities
            WHERE tenant_id = ? AND entity_type = 'concept'
            LIMIT 100
        """,
            (memory.tenant_id,),
        )

        concepts = []
        for name, desc, entity_type, created_at in c.fetchall():
            concepts.append(
                {
                    "name": name,
                    "description": desc or "",
                    "type": entity_type,
                    "created_at": created_at,
                }
            )

        if not concepts:
            info("No concepts to push", use_color)
            return 0

        # Contribute to federation
        result = knowledge.contribute_concepts(node_id, concepts)
        gate.record_contribution(node_id, result["contribution_value"])

        return result["new_concepts"]

    finally:
        conn.close()


def _pull_memories(node_id: str, knowledge, gate, use_color: bool) -> int:
    """Pull federated memories to local"""
    from continuum.core.memory import get_memory
    import sqlite3

    memory = get_memory()

    # Get federated concepts
    concepts = knowledge.get_shared_concepts(limit=50)

    if not concepts:
        info("No new concepts available", use_color)
        return 0

    # Record consumption
    gate.record_consumption(node_id, len(concepts) * 0.1)

    # Add to local memory
    conn = sqlite3.connect(memory.db_path)
    try:
        c = conn.cursor()
        added = 0

        for item in concepts:
            concept = item["concept"]
            name = concept.get("name", "")
            desc = concept.get("description", "")

            # Check if already exists
            c.execute(
                """
                SELECT id FROM entities
                WHERE LOWER(name) = LOWER(?) AND tenant_id = ?
            """,
                (name, memory.tenant_id),
            )

            if not c.fetchone():
                # Add new concept
                c.execute(
                    """
                    INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                    VALUES (?, ?, ?, datetime('now'), ?)
                """,
                    (name, "concept", desc, memory.tenant_id),
                )
                added += 1

        conn.commit()
        return added

    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
