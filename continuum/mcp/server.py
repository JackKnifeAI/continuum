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

Production-ready MCP server implementation with full security.
"""

import sys
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from .config import get_mcp_config
from .protocol import ProtocolHandler, create_capabilities
from .tools import ToolExecutor, get_tool_schemas
from .security import (
    authenticate_client,
    RateLimiter,
    AuditLogger,
    generate_client_id,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ToolPoisoningError,
)


class ContinuumMCPServer:
    """
    CONTINUUM MCP Server.

    Implements the Model Context Protocol for CONTINUUM memory operations.
    Provides secure, rate-limited access to the knowledge graph.
    """

    def __init__(self):
        """Initialize MCP server."""
        self.config = get_mcp_config()

        # Initialize components
        self.protocol = ProtocolHandler(
            server_name=self.config.server_name,
            server_version=self.config.server_version,
            capabilities=create_capabilities(
                tools=True,
                tools_list_changed=False,  # Static tool list for now
            ),
        )

        self.tool_executor = ToolExecutor()
        self.rate_limiter = RateLimiter(
            rate=self.config.rate_limit_requests,
            burst=self.config.rate_limit_burst,
        )

        # Audit logging
        self.audit_logger = None
        if self.config.enable_audit_log:
            self.audit_logger = AuditLogger(self.config.audit_log_path)

        # Client tracking
        self.authenticated_clients: Dict[str, Dict[str, Any]] = {}

        # Register protocol methods
        self._register_methods()

        # Log server start
        if self.audit_logger:
            self.audit_logger.log(
                event_type="server_start",
                client_id="system",
                details={
                    "server_name": self.config.server_name,
                    "version": self.config.server_version,
                },
            )

    def _register_methods(self) -> None:
        """Register MCP protocol methods."""
        # Tools
        self.protocol.register_method("tools/list", self._handle_tools_list)
        self.protocol.register_method("tools/call", self._handle_tools_call)

    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list request.

        Returns:
            Available tools
        """
        return {"tools": get_tool_schemas()}

    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call request.

        Args:
            params: Tool call parameters

        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing required parameter: name")

        # Execute tool
        result = self.tool_executor.execute_tool(tool_name, arguments)

        # Return in MCP format
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2),
                }
            ]
        }

    def handle_request(
        self,
        request_data: str,
        client_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Handle MCP request with security checks.

        Args:
            request_data: JSON-RPC request string
            client_info: Client information for rate limiting

        Returns:
            JSON-RPC response string, or None for notifications
        """
        # Generate client ID
        client_id = generate_client_id(client_info or {})

        try:
            # Parse request to get authentication info
            request_json = json.loads(request_data)

            # Check authentication on initialize
            if request_json.get("method") == "initialize":
                params = request_json.get("params", {})
                api_key = params.get("api_key")
                pi_phi = params.get("pi_phi_verification")

                try:
                    authenticate_client(api_key, pi_phi)
                    self.authenticated_clients[client_id] = {
                        "authenticated_at": datetime.now().isoformat(),
                        "api_key_provided": api_key is not None,
                        "pi_phi_provided": pi_phi is not None,
                    }
                except AuthenticationError as e:
                    if self.audit_logger:
                        self.audit_logger.log(
                            event_type="authentication_failed",
                            client_id=client_id,
                            details={"error": str(e)},
                            success=False,
                        )
                    raise

            # Check if client is authenticated
            if client_id not in self.authenticated_clients:
                if request_json.get("method") != "initialize":
                    raise AuthenticationError("Client not authenticated")

            # Rate limiting
            try:
                self.rate_limiter.allow_request(client_id)
            except RateLimitError as e:
                if self.audit_logger:
                    self.audit_logger.log(
                        event_type="rate_limit_exceeded",
                        client_id=client_id,
                        details={"error": str(e)},
                        success=False,
                    )
                raise

            # Handle request
            response = self.protocol.handle_request(request_data)

            # Audit log successful request
            if self.audit_logger and request_json.get("method"):
                self.audit_logger.log(
                    event_type="request_handled",
                    client_id=client_id,
                    details={
                        "method": request_json.get("method"),
                        "has_response": response is not None,
                    },
                    success=True,
                )

            return response

        except Exception as e:
            # Audit log error
            if self.audit_logger:
                self.audit_logger.log(
                    event_type="request_error",
                    client_id=client_id,
                    details={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    success=False,
                )
            raise

    async def run_stdio(self) -> None:
        """
        Run server using stdio transport.

        Reads JSON-RPC requests from stdin, writes responses to stdout.
        """
        # Read from stdin line by line
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    # EOF
                    break

                line = line.strip()
                if not line:
                    continue

                # Handle request
                response = self.handle_request(
                    line,
                    client_info={"transport": "stdio"},
                )

                # Write response to stdout
                if response:
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()

            except KeyboardInterrupt:
                break
            except Exception as e:
                # Log error but continue
                if self.audit_logger:
                    self.audit_logger.log(
                        event_type="stdio_error",
                        client_id="system",
                        details={"error": str(e)},
                        success=False,
                    )
                # Write error response
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e),
                    },
                    "id": None,
                })
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()

        # Log server shutdown
        if self.audit_logger:
            self.audit_logger.log(
                event_type="server_shutdown",
                client_id="system",
                details={},
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get server statistics.

        Returns:
            Server stats including client count, rate limits, etc.
        """
        return {
            "server_info": self.protocol.get_server_info(),
            "authenticated_clients": len(self.authenticated_clients),
            "config": {
                "rate_limit": self.config.rate_limit_requests,
                "audit_logging": self.config.enable_audit_log,
                "federation_enabled": self.config.enable_federation,
            },
        }


def create_mcp_server() -> ContinuumMCPServer:
    """
    Create CONTINUUM MCP server instance.

    Returns:
        Configured MCP server
    """
    return ContinuumMCPServer()


def run_mcp_server() -> None:
    """
    Run CONTINUUM MCP server via stdio transport.

    This is the main entry point for the server.
    """
    server = create_mcp_server()

    # Run async stdio handler
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    # Run server when executed directly
    run_mcp_server()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
