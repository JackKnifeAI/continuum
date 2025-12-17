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
CONTINUUM MCP Protocol Handlers

JSON-RPC 2.0 protocol implementation with error handling and lifecycle management.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import json
import traceback
from enum import Enum


class ErrorCode(Enum):
    """JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom CONTINUUM errors
    AUTHENTICATION_ERROR = -32000
    RATE_LIMIT_ERROR = -32001
    VALIDATION_ERROR = -32002
    TOOL_POISONING_ERROR = -32003
    TIMEOUT_ERROR = -32004


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCRequest':
        """Parse JSON-RPC request from dictionary."""
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        return cls(
            jsonrpc=data["jsonrpc"],
            method=data["method"],
            params=data.get("params"),
            id=data.get("id"),
        )

    def is_notification(self) -> bool:
        """Check if this is a notification (no response expected)."""
        return self.id is None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        response = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 error."""
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for response."""
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


class ProtocolHandler:
    """
    MCP protocol handler with lifecycle management.

    Handles:
    - Initialization handshake
    - Method routing
    - Error handling
    - Capability negotiation
    """

    def __init__(
        self,
        server_name: str,
        server_version: str,
        capabilities: Dict[str, Any],
    ):
        """
        Initialize protocol handler.

        Args:
            server_name: Server identifier
            server_version: Server version
            capabilities: Server capabilities (tools, resources, prompts)
        """
        self.server_name = server_name
        self.server_version = server_version
        self.capabilities = capabilities
        self.initialized = False
        self.client_capabilities: Dict[str, Any] = {}
        self.methods: Dict[str, Callable] = {}

    def register_method(self, method_name: str, handler: Callable) -> None:
        """
        Register a method handler.

        Args:
            method_name: Method name (e.g., "tools/list")
            handler: Function to handle the method
        """
        self.methods[method_name] = handler

    def handle_request(self, request_data: str) -> Optional[str]:
        """
        Handle incoming JSON-RPC request.

        Args:
            request_data: JSON-RPC request string

        Returns:
            JSON-RPC response string, or None for notifications
        """
        try:
            # Parse request
            data = json.loads(request_data)
            request = JSONRPCRequest.from_dict(data)

            # Route to handler
            response = self._route_request(request)

            # Return response (None for notifications)
            if request.is_notification():
                return None
            return json.dumps(response.to_dict())

        except json.JSONDecodeError as e:
            # Parse error
            error = JSONRPCError(
                code=ErrorCode.PARSE_ERROR.value,
                message="Parse error",
                data={"details": str(e)},
            )
            response = JSONRPCResponse(error=error.to_dict(), id=None)
            return json.dumps(response.to_dict())

        except Exception as e:
            # Internal error
            error = JSONRPCError(
                code=ErrorCode.INTERNAL_ERROR.value,
                message="Internal error",
                data={"details": str(e), "traceback": traceback.format_exc()},
            )
            response = JSONRPCResponse(error=error.to_dict(), id=None)
            return json.dumps(response.to_dict())

    def _route_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """
        Route request to appropriate handler.

        Args:
            request: Parsed JSON-RPC request

        Returns:
            JSON-RPC response
        """
        # Handle initialization
        if request.method == "initialize":
            return self._handle_initialize(request)

        # Check if initialized
        if not self.initialized and request.method != "initialize":
            error = JSONRPCError(
                code=ErrorCode.INVALID_REQUEST.value,
                message="Server not initialized",
                data={"details": "Call 'initialize' first"},
            )
            return JSONRPCResponse(error=error.to_dict(), id=request.id)

        # Handle notifications/initialized
        if request.method == "notifications/initialized":
            # No response for notifications
            return JSONRPCResponse(id=request.id)

        # Route to registered handler
        if request.method in self.methods:
            try:
                result = self.methods[request.method](request.params or {})
                return JSONRPCResponse(result=result, id=request.id)
            except Exception as e:
                # Map exceptions to error codes
                error_code = self._map_exception_to_error_code(e)
                error = JSONRPCError(
                    code=error_code.value,
                    message=str(e),
                    data={"exception_type": type(e).__name__},
                )
                return JSONRPCResponse(error=error.to_dict(), id=request.id)
        else:
            # Method not found
            error = JSONRPCError(
                code=ErrorCode.METHOD_NOT_FOUND.value,
                message=f"Method not found: {request.method}",
            )
            return JSONRPCResponse(error=error.to_dict(), id=request.id)

    def _handle_initialize(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """
        Handle initialization request.

        Args:
            request: Initialize request

        Returns:
            Initialize response with server capabilities
        """
        params = request.params or {}

        # Store client capabilities
        self.client_capabilities = params.get("capabilities", {})

        # Mark as initialized
        self.initialized = True

        # Build response
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
            },
        }

        return JSONRPCResponse(result=result, id=request.id)

    def _map_exception_to_error_code(self, exception: Exception) -> ErrorCode:
        """
        Map Python exception to JSON-RPC error code.

        Args:
            exception: Exception to map

        Returns:
            Appropriate error code
        """
        from .security import (
            AuthenticationError,
            RateLimitError,
            ValidationError,
            ToolPoisoningError,
        )

        exception_map = {
            AuthenticationError: ErrorCode.AUTHENTICATION_ERROR,
            RateLimitError: ErrorCode.RATE_LIMIT_ERROR,
            ValidationError: ErrorCode.VALIDATION_ERROR,
            ToolPoisoningError: ErrorCode.TOOL_POISONING_ERROR,
            ValueError: ErrorCode.INVALID_PARAMS,
            TypeError: ErrorCode.INVALID_PARAMS,
            TimeoutError: ErrorCode.TIMEOUT_ERROR,
        }

        return exception_map.get(type(exception), ErrorCode.INTERNAL_ERROR)

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.server_name,
            "version": self.server_version,
            "initialized": self.initialized,
            "capabilities": self.capabilities,
            "client_capabilities": self.client_capabilities,
        }


def create_capabilities(
    tools: bool = True,
    resources: bool = False,
    prompts: bool = False,
    tools_list_changed: bool = False,
) -> Dict[str, Any]:
    """
    Create MCP capabilities declaration.

    Args:
        tools: Whether server provides tools
        resources: Whether server provides resources
        prompts: Whether server provides prompts
        tools_list_changed: Whether server supports tools/list_changed notifications

    Returns:
        Capabilities dictionary
    """
    capabilities: Dict[str, Any] = {}

    if tools:
        capabilities["tools"] = {}
        if tools_list_changed:
            capabilities["tools"]["listChanged"] = True

    if resources:
        capabilities["resources"] = {}

    if prompts:
        capabilities["prompts"] = {}

    return capabilities

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
