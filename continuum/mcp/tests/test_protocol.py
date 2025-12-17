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
Tests for CONTINUUM MCP protocol handlers.
"""

import json
import pytest
from continuum.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    ProtocolHandler,
    ErrorCode,
    create_capabilities,
)


class TestJSONRPCRequest:
    """Test JSON-RPC request parsing."""

    def test_parse_valid_request(self):
        """Valid request should parse correctly."""
        data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {"arg": "value"},
            "id": 1,
        }
        request = JSONRPCRequest.from_dict(data)
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.params == {"arg": "value"}
        assert request.id == 1

    def test_parse_notification(self):
        """Notification (no id) should parse correctly."""
        data = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        request = JSONRPCRequest.from_dict(data)
        assert request.is_notification()

    def test_parse_without_params(self):
        """Request without params should parse correctly."""
        data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
        }
        request = JSONRPCRequest.from_dict(data)
        assert request.params is None

    def test_invalid_jsonrpc_version(self):
        """Invalid JSON-RPC version should raise error."""
        data = {
            "jsonrpc": "1.0",
            "method": "test",
        }
        with pytest.raises(ValueError):
            JSONRPCRequest.from_dict(data)


class TestJSONRPCResponse:
    """Test JSON-RPC response creation."""

    def test_success_response(self):
        """Success response should format correctly."""
        response = JSONRPCResponse(result={"status": "ok"}, id=1)
        data = response.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["result"] == {"status": "ok"}
        assert data["id"] == 1
        assert "error" not in data

    def test_error_response(self):
        """Error response should format correctly."""
        error = JSONRPCError(
            code=ErrorCode.INVALID_PARAMS.value,
            message="Invalid parameters",
        ).to_dict()
        response = JSONRPCResponse(error=error, id=1)
        data = response.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["error"]["code"] == -32602
        assert data["error"]["message"] == "Invalid parameters"
        assert "result" not in data


class TestProtocolHandler:
    """Test MCP protocol handler."""

    def setup_method(self):
        """Set up test handler."""
        self.handler = ProtocolHandler(
            server_name="test-server",
            server_version="1.0.0",
            capabilities=create_capabilities(tools=True),
        )

    def test_initialization(self):
        """Handler should initialize correctly."""
        assert self.handler.server_name == "test-server"
        assert self.handler.server_version == "1.0.0"
        assert not self.handler.initialized

    def test_handle_initialize(self):
        """Should handle initialize request."""
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        })

        response_str = self.handler.handle_request(request)
        response = json.loads(response_str)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "test-server"
        assert "capabilities" in response["result"]
        assert self.handler.initialized

    def test_requires_initialization(self):
        """Should require initialization before other methods."""
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        })

        response_str = self.handler.handle_request(request)
        response = json.loads(response_str)

        assert "error" in response
        assert response["error"]["code"] == ErrorCode.INVALID_REQUEST.value
        assert "not initialized" in response["error"]["message"]

    def test_method_not_found(self):
        """Should return error for unknown methods."""
        # Initialize first
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        self.handler.handle_request(init_request)

        # Try unknown method
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "unknown/method",
        })

        response_str = self.handler.handle_request(request)
        response = json.loads(response_str)

        assert "error" in response
        assert response["error"]["code"] == ErrorCode.METHOD_NOT_FOUND.value

    def test_register_and_call_method(self):
        """Should register and call custom methods."""
        # Register a test method
        def test_handler(params):
            return {"echo": params.get("message", "")}

        self.handler.register_method("test/echo", test_handler)

        # Initialize
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        self.handler.handle_request(init_request)

        # Call custom method
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "test/echo",
            "params": {"message": "hello"},
        })

        response_str = self.handler.handle_request(request)
        response = json.loads(response_str)

        assert response["result"]["echo"] == "hello"

    def test_handle_notification(self):
        """Should handle notifications without response."""
        # Initialize first
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        self.handler.handle_request(init_request)

        # Send notification
        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        })

        response = self.handler.handle_request(notification)
        assert response is None  # No response for notifications

    def test_parse_error(self):
        """Should handle JSON parse errors."""
        invalid_json = "{'invalid': json}"

        response_str = self.handler.handle_request(invalid_json)
        response = json.loads(response_str)

        assert "error" in response
        assert response["error"]["code"] == ErrorCode.PARSE_ERROR.value

    def test_exception_handling(self):
        """Should handle exceptions in method handlers."""
        # Register method that raises exception
        def failing_handler(params):
            raise ValueError("Test error")

        self.handler.register_method("test/fail", failing_handler)

        # Initialize
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        self.handler.handle_request(init_request)

        # Call failing method
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "test/fail",
        })

        response_str = self.handler.handle_request(request)
        response = json.loads(response_str)

        assert "error" in response
        assert response["error"]["code"] == ErrorCode.INVALID_PARAMS.value
        assert "Test error" in response["error"]["message"]

    def test_get_server_info(self):
        """Should return server information."""
        info = self.handler.get_server_info()
        assert info["name"] == "test-server"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "initialized" in info


class TestCapabilities:
    """Test capability creation."""

    def test_tools_only(self):
        """Should create tools-only capabilities."""
        caps = create_capabilities(tools=True)
        assert "tools" in caps
        assert "resources" not in caps
        assert "prompts" not in caps

    def test_all_capabilities(self):
        """Should create all capabilities."""
        caps = create_capabilities(
            tools=True,
            resources=True,
            prompts=True,
            tools_list_changed=True,
        )
        assert "tools" in caps
        assert "resources" in caps
        assert "prompts" in caps
        assert caps["tools"]["listChanged"] is True

    def test_no_capabilities(self):
        """Should create empty capabilities."""
        caps = create_capabilities()
        assert caps == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
