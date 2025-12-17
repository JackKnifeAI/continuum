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
CONTINUUM Federation CLI

Command-line interface for federation operations.

Usage:
    python -m continuum.federation.cli register [--verify]
    python -m continuum.federation.cli contribute <concept_name> <description>
    python -m continuum.federation.cli request <query>
    python -m continuum.federation.cli status
    python -m continuum.federation.cli stats
"""

import sys
import json
import math
from pathlib import Path
from typing import Optional

from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge


def get_or_create_node(verify: bool = False) -> FederatedNode:
    """Get existing node or create new one."""
    config_dir = Path.home() / ".continuum" / "federation"
    config_file = config_dir / "node_config.json"

    verify_constant = None
    if verify:
        # Calculate π × φ for verification
        verify_constant = math.pi * ((1 + math.sqrt(5)) / 2)

    if config_file.exists():
        config = json.loads(config_file.read_text())
        node = FederatedNode(
            node_id=config['node_id'],
            verify_constant=verify_constant
        )
    else:
        node = FederatedNode(verify_constant=verify_constant)
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"node_id": node.node_id}, indent=2))

    return node


def cmd_register(args):
    """Register node in federation."""
    verify = '--verify' in args

    node = get_or_create_node(verify=verify)
    result = node.register()

    print("Registration Result:")
    print(f"  Node ID: {result['node_id']}")
    print(f"  Access Level: {result['access_level']}")
    if result.get('verified'):
        print(f"  Verified: True")
        print(f"  Message: {result['message']}")
    print(f"  Registered At: {result.get('registered_at', 'N/A')}")


def cmd_contribute(args):
    """Contribute a concept to federation."""
    if len(args) < 2:
        print("Error: Missing arguments")
        print("Usage: contribute <name> <description>")
        sys.exit(1)

    name = args[0]
    description = ' '.join(args[1:])

    node = get_or_create_node()
    gate = ContributionGate()
    knowledge = SharedKnowledge()

    concept = {
        "name": name,
        "description": description,
        "type": "concept",
    }

    result = knowledge.contribute_concepts(node.node_id, [concept])
    gate.record_contribution(node.node_id, result['contribution_value'])

    print("Contribution Result:")
    print(f"  New Concepts: {result['new_concepts']}")
    print(f"  Duplicates: {result['duplicate_concepts']}")
    print(f"  Contribution Value: {result['contribution_value']}")

    status = gate.get_stats(node.node_id)
    print(f"\nYour Stats:")
    print(f"  Contributed: {status['contributed']}")
    print(f"  Consumed: {status['consumed']}")
    print(f"  Ratio: {status['ratio']:.2f}")
    print(f"  Tier: {status['tier']}")


def cmd_request(args):
    """Request knowledge from federation."""
    if len(args) < 1:
        print("Error: Missing query")
        print("Usage: request <query>")
        sys.exit(1)

    query = ' '.join(args)

    node = get_or_create_node()
    gate = ContributionGate()
    knowledge = SharedKnowledge()

    # Check access
    access = gate.can_access(node.node_id)
    if not access['allowed']:
        print(f"Access Denied: {access['reason']}")
        if 'deficit' in access:
            print(f"  Deficit: {access['deficit']:.1f} concepts needed")
            print(f"  Current Ratio: {access['ratio']:.2f}")
            print(f"  Minimum Required: {access['minimum_required']}")
        print("\nContribute concepts to gain access!")
        sys.exit(1)

    # Get knowledge
    concepts = knowledge.get_shared_concepts(query=query, limit=10)
    gate.record_consumption(node.node_id, 1.0)

    print(f"Found {len(concepts)} concepts matching '{query}':\n")
    for i, c in enumerate(concepts, 1):
        concept = c['concept']
        print(f"{i}. {concept.get('name', 'Unnamed')}")
        print(f"   {concept.get('description', 'No description')}")
        print(f"   Quality: {c['quality_score']:.2f} | Usage: {c['usage_count']}")
        print()

    # Show updated stats
    status = gate.get_stats(node.node_id)
    print(f"Your Stats (after consumption):")
    print(f"  Contributed: {status['contributed']}")
    print(f"  Consumed: {status['consumed']}")
    print(f"  Ratio: {status['ratio']:.2f}")
    print(f"  Tier: {status['tier']}")


def cmd_status(args):
    """Show node status."""
    node = get_or_create_node()
    gate = ContributionGate()

    status = gate.get_stats(node.node_id)
    access = gate.can_access(node.node_id)

    print("Node Status:")
    print(f"  Node ID: {node.node_id}")
    print(f"\nContribution Stats:")
    print(f"  Contributed: {status['contributed']}")
    print(f"  Consumed: {status['consumed']}")
    print(f"  Ratio: {status['ratio']:.2f}")
    print(f"  Tier: {status['tier']}")
    print(f"\nAccess:")
    print(f"  Allowed: {access['allowed']}")
    if access['allowed']:
        print(f"  Reason: {access['reason']}")
    else:
        print(f"  Blocked: {access['reason']}")
        if 'deficit' in access:
            print(f"  Deficit: {access['deficit']:.1f} concepts needed")


def cmd_stats(args):
    """Show federation statistics."""
    knowledge = SharedKnowledge()
    stats = knowledge.get_stats()

    print("Federation Statistics:")
    print(f"  Total Concepts: {stats['total_concepts']}")
    print(f"  Total Contributors: {stats['total_contributors']}")
    print(f"  Average Quality: {stats['average_quality']:.2f}")
    print(f"  Storage Path: {stats['storage_path']}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("CONTINUUM Federation CLI")
        print("\nUsage:")
        print("  register [--verify]           Register node (--verify for π×φ)")
        print("  contribute <name> <desc>      Contribute a concept")
        print("  request <query>               Request knowledge")
        print("  status                        Show node status")
        print("  stats                         Show federation stats")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'register': cmd_register,
        'contribute': cmd_contribute,
        'request': cmd_request,
        'status': cmd_status,
        'stats': cmd_stats,
    }

    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)

    try:
        commands[command](args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
