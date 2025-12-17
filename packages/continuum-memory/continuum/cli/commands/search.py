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
Search Command - Search local and federated memories
"""

import sys
import json
from typing import Optional

from continuum.core.memory import get_memory
from ..utils import success, error, info, section, print_json, colorize, Colors
from ..config import CLIConfig


def search_command(
    query: str,
    limit: int,
    federated: bool,
    output_json: bool,
    config: CLIConfig,
    use_color: bool,
):
    """
    Search local and federated memories.

    Args:
        query: Search query
        limit: Maximum results
        federated: Whether to search federated knowledge
        output_json: Whether to output as JSON
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    try:
        memory = get_memory()

        if not output_json:
            section(f"Searching for: {query}", use_color)
            info(f"Limit: {limit} results", use_color)
            if federated:
                info("Searching federated knowledge", use_color)
            print()

        # Perform search
        result = memory.recall(query, max_concepts=limit)

        if output_json:
            # JSON output
            output = {
                "query": query,
                "concepts_found": result.concepts_found,
                "relationships_found": result.relationships_found,
                "query_time_ms": result.query_time_ms,
                "context": result.context_string,
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            if result.concepts_found == 0:
                info("No memories found", use_color)
            else:
                success(
                    f"Found {result.concepts_found} concepts, {result.relationships_found} relationships",
                    use_color,
                )
                info(f"Query time: {result.query_time_ms:.2f}ms", use_color)

                print("\n" + colorize("Context:", Colors.CYAN, bold=True, enabled=use_color))
                print("-" * 60)
                print(result.context_string)
                print("-" * 60)

        # Federated search if requested
        if federated and config.federation_enabled:
            _search_federated(query, limit, output_json, use_color)

    except Exception as e:
        error(f"Search failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _search_federated(query: str, limit: int, output_json: bool, use_color: bool):
    """Search federated knowledge"""
    try:
        from continuum.federation.shared import SharedKnowledge
        from continuum.federation.contribution import ContributionGate

        knowledge = SharedKnowledge()
        gate = ContributionGate()

        # Check access
        # Note: Need node_id from config
        # For now, skip access check in search

        concepts = knowledge.get_shared_concepts(query=query, limit=limit)

        if output_json:
            output = {
                "federated": True,
                "concepts_found": len(concepts),
                "concepts": concepts,
            }
            print(json.dumps(output, indent=2))
        else:
            if concepts:
                print("\n" + colorize("Federated Results:", Colors.MAGENTA, bold=True, enabled=use_color))
                print("-" * 60)

                for i, c in enumerate(concepts, 1):
                    concept = c["concept"]
                    print(f"\n{colorize(f'{i}.', Colors.CYAN, enabled=use_color)} "
                          f"{colorize(concept.get('name', 'Unnamed'), Colors.BRIGHT_WHITE, bold=True, enabled=use_color)}")
                    print(f"   {concept.get('description', 'No description')}")
                    print(f"   Quality: {c['quality_score']:.2f} | Usage: {c['usage_count']}")

                print("-" * 60)
            else:
                info("No federated results found", use_color)

    except ImportError:
        if not output_json:
            info("Federation not available (missing dependencies)", use_color)
    except Exception as e:
        if not output_json:
            error(f"Federated search failed: {e}", use_color)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
