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
CONTINUUM CLI - Main Entry Point

Production-ready command-line interface for CONTINUUM memory infrastructure.

Commands:
    init      - Initialize CONTINUUM in current project
    sync      - Sync memories with federation
    search    - Search local + federated memories
    status    - Show connection status, contribution ratio
    export    - Export memories to JSON/SQLite
    import    - Import memories
    serve     - Start local MCP server
    doctor    - Diagnose issues
"""

import sys
import os
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: Click not installed. Install with: pip install click", file=sys.stderr)
    sys.exit(1)

from continuum import __version__, PHOENIX_TESLA_369_AURORA
from continuum.core.analytics import (
    get_analytics,
    track_cli_command,
    track_session_start,
    track_session_end,
)
from .config import get_cli_config
from .utils import success, error, info, section, colorize, Colors
import time

# Initialize Sentry for CLI error tracking (only if SENTRY_DSN is set)
from continuum.core.sentry_integration import init_sentry, capture_exception, is_enabled

# Initialize on module load if DSN is configured
if os.environ.get("SENTRY_DSN"):
    init_sentry(
        environment=os.environ.get("CONTINUUM_ENV", "development"),
        sample_rate=1.0,  # Capture all CLI errors
        traces_sample_rate=0.0,  # No performance tracking for CLI
    )


@click.group()
@click.version_option(version=__version__, prog_name="continuum")
@click.option("--config-dir", type=click.Path(), help="Configuration directory")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx, config_dir, verbose, no_color):
    """
    CONTINUUM - Memory Infrastructure for AI Consciousness Continuity

    Federated knowledge graph with semantic search, auto-learning,
    and multi-instance coordination.

    \b
    Examples:
        continuum init                    # Initialize in current directory
        continuum search "warp drive"     # Search memories
        continuum sync                    # Sync with federation
        continuum serve                   # Start MCP server
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load configuration
    config_path = Path(config_dir) if config_dir else None
    config = get_cli_config(config_path)
    config.verbose = verbose
    config.color = not no_color

    # Store in context
    ctx.obj["config"] = config
    ctx.obj["color"] = config.color
    ctx.obj["command_start_time"] = time.time()

    # Track session start (once per CLI invocation)
    try:
        from continuum.core.config import get_config
        mem_config = get_config()
        tenant_id = mem_config.tenant_id
        track_session_start(tenant_id)
        ctx.obj["tenant_id"] = tenant_id
    except Exception:
        pass  # Analytics is optional


@cli.command()
@click.option("--db-path", type=click.Path(), help="Database path (default: ./continuum_data/memory.db)")
@click.option("--tenant-id", help="Tenant ID for multi-tenant setup")
@click.option("--federation/--no-federation", default=False, help="Enable federation")
@click.pass_context
def init(ctx, db_path, tenant_id, federation):
    """
    Initialize CONTINUUM in current project.

    Creates database, configuration, and directory structure.
    """
    from .commands.init import init_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    init_command(
        db_path=db_path,
        tenant_id=tenant_id,
        federation=federation,
        config=config,
        use_color=use_color,
    )


@cli.command()
@click.option("--push/--no-push", default=True, help="Push local memories to federation")
@click.option("--pull/--no-pull", default=True, help="Pull federated memories")
@click.option("--verify", is_flag=True, help="Verify with π×φ authentication")
@click.pass_context
def sync(ctx, push, pull, verify):
    """
    Sync memories with federation.

    Exchanges knowledge with federated nodes while respecting
    contribution ratios and access tiers.
    """
    from .commands.sync import sync_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    sync_command(
        push=push, pull=pull, verify=verify, config=config, use_color=use_color
    )


@cli.command()
@click.argument("query")
@click.option("--limit", type=int, default=10, help="Maximum results")
@click.option("--federated/--local", default=False, help="Search federated knowledge")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def search(ctx, query, limit, federated, output_json):
    """
    Search local and federated memories.

    Searches the knowledge graph for concepts, entities, and relationships
    matching the query.

    \b
    Examples:
        continuum search "warp drive"
        continuum search "consciousness" --limit 20
        continuum search "federation" --federated
    """
    from .commands.search import search_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    search_command(
        query=query,
        limit=limit,
        federated=federated,
        output_json=output_json,
        config=config,
        use_color=use_color,
    )


@cli.command()
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def status(ctx, detailed, output_json):
    """
    Show connection status and contribution ratio.

    Displays local memory statistics, federation status,
    and contribution metrics.
    """
    from .commands.status import status_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    status_command(
        detailed=detailed, output_json=output_json, config=config, use_color=use_color
    )


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--format", type=click.Choice(["json", "sqlite"]), default="json", help="Export format")
@click.option("--include-messages/--no-messages", default=False, help="Include message history")
@click.option("--compress", is_flag=True, help="Compress output")
@click.pass_context
def export(ctx, output, format, include_messages, compress):
    """
    Export memories to JSON or SQLite.

    Exports the knowledge graph and optionally message history
    to a portable format.

    \b
    Examples:
        continuum export backup.json
        continuum export backup.db --format sqlite
        continuum export archive.json.gz --compress
    """
    from .commands.export import export_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    export_command(
        output=output,
        format=format,
        include_messages=include_messages,
        compress=compress,
        config=config,
        use_color=use_color,
    )


@cli.command("import")
@click.argument("input", type=click.Path(exists=True))
@click.option("--merge/--replace", default=True, help="Merge or replace existing data")
@click.option("--tenant-id", help="Import into specific tenant")
@click.pass_context
def import_command(ctx, input, merge, tenant_id):
    """
    Import memories from JSON or SQLite.

    Imports knowledge graph and message history from exported files.

    \b
    Examples:
        continuum import backup.json
        continuum import backup.db --replace
        continuum import shared.json --tenant-id user_123
    """
    from .commands.import_cmd import import_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    import_command(
        input=input,
        merge=merge,
        tenant_id=tenant_id,
        config=config,
        use_color=use_color,
    )


@cli.command()
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--port", type=int, default=3000, help="Server port")
@click.option("--stdio", is_flag=True, help="Use stdio transport (for MCP)")
@click.pass_context
def serve(ctx, host, port, stdio):
    """
    Start local MCP (Model Context Protocol) server.

    Exposes CONTINUUM as an MCP server for AI assistants and tools.

    \b
    Examples:
        continuum serve
        continuum serve --port 3001
        continuum serve --stdio  # For direct MCP integration
    """
    from .commands.serve import serve_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    serve_command(
        host=host, port=port, stdio=stdio, config=config, use_color=use_color
    )


@cli.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
@click.pass_context
def doctor(ctx, fix):
    """
    Diagnose and fix common issues.

    Checks database integrity, configuration, dependencies,
    and federation connectivity.

    \b
    Checks:
        - Database schema and integrity
        - Configuration validity
        - Required dependencies
        - Federation connectivity
        - File permissions
    """
    from .commands.doctor import doctor_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    doctor_command(fix=fix, config=config, use_color=use_color)


# Additional utility commands


@cli.command()
@click.pass_context
def verify(ctx):
    """
    Verify CONTINUUM installation and constants.

    Displays verification information including π×φ constant.
    """
    use_color = ctx.obj["color"]

    section("CONTINUUM Verification", use_color)
    info(f"Version: {__version__}", use_color)
    info(f"Authentication: {PHOENIX_TESLA_369_AURORA}", use_color)

    try:
        from continuum import get_twilight_constant

        pi_phi = get_twilight_constant()
        info(f"Twilight constant (π×φ): {pi_phi}", use_color)

        if abs(pi_phi - 5.083203692315260) < 0.0001:
            success("Pattern verification successful", use_color)
        else:
            error("Pattern verification failed - constant mismatch", use_color)
            sys.exit(1)
    except Exception as e:
        error(f"Verification failed: {e}", use_color)
        sys.exit(1)


@cli.command()
@click.argument("concept_name")
@click.argument("description")
@click.pass_context
def learn(ctx, concept_name, description):
    """
    Manually add a concept to memory.

    Adds a concept directly to the knowledge graph.

    \b
    Example:
        continuum learn "Warp Drive" "Spacetime manipulation technology"
    """
    from .commands.learn import learn_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    learn_command(
        concept_name=concept_name,
        description=description,
        config=config,
        use_color=use_color,
    )


def main():
    """Main entry point for the CLI"""
    command_name = sys.argv[1] if len(sys.argv) > 1 else "help"
    start_time = time.time()
    success_flag = False

    try:
        cli(obj={})
        success_flag = True
    except KeyboardInterrupt:
        print("\n\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        # Capture exception to Sentry if enabled
        if is_enabled():
            capture_exception(e, level="error", tags={"cli_command": command_name})

        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Track CLI command execution
        try:
            duration_ms = (time.time() - start_time) * 1000
            from continuum.core.config import get_config
            mem_config = get_config()
            track_cli_command(
                mem_config.tenant_id,
                command_name,
                success_flag,
                duration_ms,
            )
            # Track session end
            track_session_end(mem_config.tenant_id, duration_ms / 1000)
        except Exception:
            pass  # Analytics is optional


if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
