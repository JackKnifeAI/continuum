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
Serve Command - Start local MCP server
"""

import sys
import asyncio
from typing import Optional

from ..utils import success, error, info, section, warning
from ..config import CLIConfig


def serve_command(
    host: str, port: int, stdio: bool, config: CLIConfig, use_color: bool
):
    """
    Start local MCP (Model Context Protocol) server.

    Args:
        host: Server host
        port: Server port
        stdio: Whether to use stdio transport
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    if stdio:
        _serve_stdio(config, use_color)
    else:
        _serve_http(host, port, config, use_color)


def _serve_http(host: str, port: int, config: CLIConfig, use_color: bool):
    """Start HTTP/WebSocket MCP server"""
    section("Starting CONTINUUM MCP Server", use_color)

    info(f"Host: {host}", use_color)
    info(f"Port: {port}", use_color)
    info(f"Database: {config.db_path}", use_color)

    try:
        # Try to import FastAPI server
        try:
            from continuum.api.server import app
            import uvicorn

            success("Starting FastAPI server...", use_color)
            print(f"\nAPI available at: http://{host}:{port}")
            print(f"Documentation: http://{host}:{port}/docs")
            print(f"WebSocket: ws://{host}:{port}/ws")
            print("\nPress Ctrl+C to stop\n")

            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,
            )

        except ImportError:
            error(
                "FastAPI/Uvicorn not installed. Install with: pip install continuum-memory[dev]",
                use_color,
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n")
        info("Server stopped", use_color)
    except Exception as e:
        error(f"Server failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _serve_stdio(config: CLIConfig, use_color: bool):
    """Start stdio MCP server (for direct integration)"""
    section("Starting CONTINUUM MCP Server (stdio)", use_color)

    info(f"Database: {config.db_path}", use_color)
    info("Reading from stdin, writing to stdout", use_color)
    info("Press Ctrl+C to stop\n", use_color)

    try:
        # Use the production MCP server implementation
        from continuum.mcp.server import run_mcp_server

        run_mcp_server()
    except KeyboardInterrupt:
        print("\n")
        info("Server stopped", use_color)
    except Exception as e:
        error(f"Server failed: {e}", use_color)
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
