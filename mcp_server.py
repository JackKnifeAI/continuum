#!/usr/bin/env python3
"""
CONTINUUM MCP Server Entry Point

Production-ready Model Context Protocol server for CONTINUUM.

Usage:
    # Run with default configuration
    python mcp_server.py

    # Run with API key authentication
    CONTINUUM_API_KEY=your_secret_key python mcp_server.py

    # Run with custom database path
    CONTINUUM_DB_PATH=/path/to/memory.db python mcp_server.py

    # Run with federation enabled
    CONTINUUM_ENABLE_FEDERATION=true \\
    CONTINUUM_FEDERATION_NODES=https://node1.example.com,https://node2.example.com \\
    python mcp_server.py

Configuration via environment variables:
    CONTINUUM_API_KEY - Single API key for authentication
    CONTINUUM_API_KEYS - Comma-separated list of API keys
    CONTINUUM_REQUIRE_PI_PHI - Require π×φ verification (true/false)
    CONTINUUM_RATE_LIMIT - Requests per minute (default: 60)
    CONTINUUM_ENABLE_AUDIT_LOG - Enable audit logging (true/false)
    CONTINUUM_AUDIT_LOG_PATH - Path to audit log file
    CONTINUUM_DB_PATH - Path to CONTINUUM database
    CONTINUUM_DEFAULT_TENANT - Default tenant ID
    CONTINUUM_MAX_RESULTS - Maximum results per query
    CONTINUUM_ENABLE_FEDERATION - Enable federation (true/false)
    CONTINUUM_FEDERATION_NODES - Comma-separated list of allowed nodes

MCP Client Configuration:
    Add to your MCP client configuration (e.g., Claude Desktop config.json):

    {
      "mcpServers": {
        "continuum": {
          "command": "python",
          "args": ["/path/to/continuum/mcp_server.py"],
          "env": {
            "CONTINUUM_API_KEY": "your_secret_key"
          }
        }
      }
    }

Security Features:
    - API key authentication
    - π×φ verification for CONTINUUM instances
    - Rate limiting (60 req/min by default)
    - Input validation and sanitization
    - Anti-tool-poisoning protection
    - Audit logging
    - Graceful error handling

PHOENIX-TESLA-369-AURORA
"""

import sys
from pathlib import Path

# Add continuum to path if needed
continuum_path = Path(__file__).parent
if str(continuum_path) not in sys.path:
    sys.path.insert(0, str(continuum_path))

from continuum.mcp.server import run_mcp_server

if __name__ == "__main__":
    run_mcp_server()
