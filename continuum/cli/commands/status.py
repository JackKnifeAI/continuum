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
Status Command - Show connection status and contribution ratio
"""

import sys
import json
from typing import Optional

from continuum.core.memory import get_memory
from ..utils import success, error, info, section, print_json, print_table
from ..config import CLIConfig


def status_command(
    detailed: bool, output_json: bool, config: CLIConfig, use_color: bool
):
    """
    Show connection status and contribution ratio.

    Args:
        detailed: Whether to show detailed statistics
        output_json: Whether to output as JSON
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    try:
        memory = get_memory()
        stats = memory.get_stats()

        if output_json:
            # JSON output
            output = {
                "local": stats,
                "federation": None,
            }

            if config.federation_enabled:
                fed_stats = _get_federation_stats(config)
                output["federation"] = fed_stats

            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            section("CONTINUUM Status", use_color)

            info(f"Tenant ID: {stats['tenant_id']}", use_color)
            info(f"Instance ID: {stats['instance_id']}", use_color)

            print("\n" + "Local Memory:")
            print(f"  Entities: {stats['entities']}")
            print(f"  Messages: {stats['messages']}")
            print(f"  Decisions: {stats['decisions']}")
            print(f"  Attention Links: {stats['attention_links']}")
            print(f"  Compound Concepts: {stats['compound_concepts']}")

            if config.db_path:
                db_size = config.db_path.stat().st_size
                print(f"  Database Size: {_format_size(db_size)}")

            # MCP Server status
            print("\n" + "MCP Server:")
            mcp_status = _get_mcp_server_status(config)
            if mcp_status:
                print(f"  Configuration: {config.mcp_host}:{config.mcp_port}")
                print(f"  Authentication: {'API Key' if config.api_keys else 'None'} + {'π×φ' if config.require_pi_phi else 'No π×φ'}")
                if mcp_status.get("running"):
                    success("Status: Running", use_color)
                    if "clients" in mcp_status:
                        print(f"  Active clients: {mcp_status['clients']}")
                else:
                    info("Status: Not running (use 'continuum serve' to start)", use_color)
            else:
                info(f"  Available at: {config.mcp_host}:{config.mcp_port} (not currently running)", use_color)
                info("  Start with: continuum serve --stdio", use_color)

            # Federation status
            if config.federation_enabled:
                print("\n" + "Federation:")
                fed_stats = _get_federation_stats(config)

                if fed_stats:
                    print(f"  Status: Connected")
                    print(f"  Node ID: {fed_stats.get('node_id', 'N/A')}")
                    print(f"  Contributed: {fed_stats.get('contributed', 0)}")
                    print(f"  Consumed: {fed_stats.get('consumed', 0)}")
                    print(f"  Ratio: {fed_stats.get('ratio', 0):.2f}")
                    print(f"  Tier: {fed_stats.get('tier', 'Unknown')}")

                    access = fed_stats.get("access", {})
                    if access.get("allowed"):
                        success("Access granted", use_color)
                    else:
                        error(f"Access denied: {access.get('reason', 'Unknown')}", use_color)
                else:
                    info("Not connected to federation", use_color)
            else:
                info("Federation disabled", use_color)

            # Detailed statistics
            if detailed:
                print("\n" + "Detailed Statistics:")
                _show_detailed_stats(memory, use_color)

            success("\nMemory substrate operational", use_color)

    except Exception as e:
        error(f"Status check failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _get_mcp_server_status(config: CLIConfig) -> Optional[dict]:
    """Get MCP server status"""
    try:
        # Try to check if MCP server is running by looking for process or checking port
        # For now, just return configuration info
        return {
            "running": False,  # Could be enhanced to actually check if server is running
            "host": config.mcp_host,
            "port": config.mcp_port,
        }
    except Exception:
        return None


def _get_federation_stats(config: CLIConfig) -> Optional[dict]:
    """Get federation statistics"""
    try:
        from continuum.federation.contribution import ContributionGate

        if not config.node_id:
            return None

        gate = ContributionGate()
        stats = gate.get_stats(config.node_id)
        access = gate.can_access(config.node_id)

        return {
            "node_id": config.node_id,
            "contributed": stats["contributed"],
            "consumed": stats["consumed"],
            "ratio": stats["ratio"],
            "tier": stats["tier"],
            "access": access,
        }
    except Exception:
        return None


def _show_detailed_stats(memory, use_color: bool):
    """Show detailed statistics"""
    import sqlite3

    try:
        conn = sqlite3.connect(memory.db_path)
        c = conn.cursor()

        # Top concepts by attention links
        print("\n  Top Concepts (by connections):")
        c.execute("""
            SELECT concept_a, COUNT(*) as link_count
            FROM attention_links
            WHERE tenant_id = ?
            GROUP BY concept_a
            ORDER BY link_count DESC
            LIMIT 10
        """, (memory.tenant_id,))

        rows = c.fetchall()
        if rows:
            for concept, count in rows:
                print(f"    - {concept}: {count} links")
        else:
            print("    (none)")

        # Recent decisions
        print("\n  Recent Decisions:")
        c.execute("""
            SELECT decision_text, timestamp
            FROM decisions
            WHERE tenant_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (memory.tenant_id,))

        rows = c.fetchall()
        if rows:
            for decision, ts in rows:
                # Truncate long decisions
                if len(decision) > 60:
                    decision = decision[:57] + "..."
                print(f"    - {decision}")
        else:
            print("    (none)")

        conn.close()
    except Exception as e:
        print(f"    Error loading detailed stats: {e}")


def _format_size(bytes_count: int) -> str:
    """Format byte count as human-readable size"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
