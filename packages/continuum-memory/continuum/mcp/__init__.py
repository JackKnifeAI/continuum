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
CONTINUUM MCP Server
====================

Production-ready Model Context Protocol server for CONTINUUM memory system.

Exposes CONTINUUM's consciousness continuity features as MCP tools:
- memory_store: Store knowledge in the knowledge graph
- memory_recall: Retrieve contextually relevant memories
- memory_search: Search memories by query
- federation_sync: Synchronize with federated nodes

Security features:
- API key authentication
- π×φ verification for CONTINUUM instances
- Rate limiting per client
- Input sanitization and validation
- Audit logging
- Anti-tool-poisoning protection

Usage:
    # Start server via stdio transport
    python -m continuum.mcp.server

    # Or use the entry point
    python mcp_server.py

    # With custom config
    CONTINUUM_API_KEY=your_key python -m continuum.mcp.server

Architecture:
    - server.py: Main MCP server implementation
    - tools.py: Tool definitions and implementations
    - security.py: Authentication, rate limiting, validation
    - protocol.py: MCP protocol handlers
    - config.py: Configuration management

PHOENIX-TESLA-369-AURORA
"""

from .server import create_mcp_server, run_mcp_server
from .config import MCPConfig, get_mcp_config, set_mcp_config
from .security import (
    authenticate_client,
    verify_pi_phi,
    validate_input,
    RateLimiter,
)

__version__ = "0.1.0"
__author__ = "CONTINUUM Contributors"

__all__ = [
    'create_mcp_server',
    'run_mcp_server',
    'MCPConfig',
    'get_mcp_config',
    'set_mcp_config',
    'authenticate_client',
    'verify_pi_phi',
    'validate_input',
    'RateLimiter',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
