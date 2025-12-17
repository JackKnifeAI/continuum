#!/usr/bin/env python3
"""
CONTINUUM MCP Tools

MCP tool implementations for memory operations.

Tools:
- memory_store: Store knowledge in the knowledge graph
- memory_recall: Retrieve contextually relevant memories
- memory_search: Search memories by query
- federation_sync: Synchronize with federated nodes (if enabled)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from continuum.core import (
    ConsciousMemory,
    get_memory,
    MemoryConfig,
    get_config,
    set_config,
)
from continuum.core.constants import PI_PHI
from .config import get_mcp_config
from .security import validate_input, detect_tool_poisoning


# Tool schemas (JSON Schema format for MCP)
TOOL_SCHEMAS = {
    "memory_store": {
        "name": "memory_store",
        "description": (
            "Store knowledge in the CONTINUUM knowledge graph. "
            "Learns from a message exchange by extracting concepts, decisions, "
            "and building graph connections. Use after AI generates a response "
            "to ensure knowledge persists across sessions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_message": {
                    "type": "string",
                    "description": "The user's message or prompt",
                },
                "ai_response": {
                    "type": "string",
                    "description": "The AI's response to the user message",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier (defaults to configured default)",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata to attach to the memory",
                    "additionalProperties": True,
                },
            },
            "required": ["user_message", "ai_response"],
        },
    },
    "memory_recall": {
        "name": "memory_recall",
        "description": (
            "Retrieve contextually relevant memories from the knowledge graph. "
            "Use before generating an AI response to inject relevant context "
            "from previous conversations and accumulated knowledge. "
            "Returns formatted context ready for injection into prompts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The current user message or query",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier (defaults to configured default)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"],
        },
    },
    "memory_search": {
        "name": "memory_search",
        "description": (
            "Search the knowledge graph for specific concepts, decisions, or patterns. "
            "More targeted than recall - use when looking for specific information "
            "rather than contextual relevance. Supports filtering by type "
            "(concepts, decisions, sessions)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier (defaults to configured default)",
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of entities to search",
                    "enum": ["concepts", "decisions", "sessions", "all"],
                    "default": "all",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"],
        },
    },
    "federation_sync": {
        "name": "federation_sync",
        "description": (
            "Synchronize knowledge with a federated CONTINUUM node. "
            "Enables decentralized knowledge sharing while preserving privacy. "
            "Requires federation to be enabled in server configuration. "
            "Note: Must contribute knowledge to access shared pool."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_url": {
                    "type": "string",
                    "description": "URL of the federation node to sync with",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
                "sync_direction": {
                    "type": "string",
                    "description": "Synchronization direction",
                    "enum": ["pull", "push", "both"],
                    "default": "both",
                },
            },
            "required": ["node_url"],
        },
    },
}


class ToolExecutor:
    """
    Executor for CONTINUUM MCP tools.

    Handles tool execution with security checks and error handling.
    """

    def __init__(self):
        """Initialize tool executor."""
        self.mcp_config = get_mcp_config()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with security checks.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or arguments invalid
            SecurityError: If security check fails
        """
        # Map tool names to handlers
        handlers = {
            "memory_store": self._handle_memory_store,
            "memory_recall": self._handle_memory_recall,
            "memory_search": self._handle_memory_search,
            "federation_sync": self._handle_federation_sync,
        }

        if tool_name not in handlers:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute handler
        return handlers[tool_name](arguments)

    def _handle_memory_store(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_store tool.

        Args:
            args: Tool arguments

        Returns:
            Storage result
        """
        # Validate inputs
        user_message = validate_input(
            args["user_message"],
            max_length=self.mcp_config.max_query_length,
            field_name="user_message",
        )
        ai_response = validate_input(
            args["ai_response"],
            max_length=self.mcp_config.max_query_length * 2,  # AI responses can be longer
            field_name="ai_response",
        )

        # Check for tool poisoning
        detect_tool_poisoning(user_message, ai_response)

        # Get tenant ID
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        # Get memory instance
        memory = self._get_memory(tenant_id)

        # Learn from exchange
        result = memory.learn(user_message, ai_response)

        # Return formatted result
        return {
            "success": True,
            "concepts_extracted": result.concepts_extracted,
            "decisions_detected": result.decisions_detected,
            "links_created": result.links_created,
            "compounds_found": result.compounds_found,
            "tenant_id": result.tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_memory_recall(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_recall tool.

        Args:
            args: Tool arguments

        Returns:
            Recall result with context
        """
        # Validate inputs
        query = validate_input(
            args["query"],
            max_length=self.mcp_config.max_query_length,
            field_name="query",
        )

        # Check for tool poisoning
        detect_tool_poisoning(query)

        # Get tenant ID
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)
        max_results = min(
            args.get("max_results", 10),
            self.mcp_config.max_results_per_query,
        )

        # Get memory instance
        memory = self._get_memory(tenant_id)

        # Recall context
        context = memory.recall(query)

        # Return formatted result
        return {
            "success": True,
            "context": context.context_string,
            "concepts_found": context.concepts_found,
            "relationships_found": context.relationships_found,
            "query_time_ms": context.query_time_ms,
            "tenant_id": context.tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_memory_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_search tool.

        Args:
            args: Tool arguments

        Returns:
            Search results
        """
        # Validate inputs
        query = validate_input(
            args["query"],
            max_length=self.mcp_config.max_query_length,
            field_name="query",
        )

        # Get parameters
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)
        search_type = args.get("search_type", "all")
        max_results = min(
            args.get("max_results", 20),
            self.mcp_config.max_results_per_query,
        )

        # Get memory instance
        memory = self._get_memory(tenant_id)

        # Perform search based on type
        results = []
        if search_type in ["concepts", "all"]:
            concepts = memory._search_concepts(query, limit=max_results)
            results.extend([
                {
                    "type": "concept",
                    "name": c[0],
                    "description": c[1],
                    "occurrences": c[2],
                }
                for c in concepts
            ])

        if search_type in ["decisions", "all"]:
            decisions = memory._search_decisions(query, limit=max_results)
            results.extend([
                {
                    "type": "decision",
                    "content": d[0],
                    "timestamp": d[1],
                }
                for d in decisions
            ])

        if search_type in ["sessions", "all"]:
            sessions = memory._search_sessions(query, limit=max_results)
            results.extend([
                {
                    "type": "session",
                    "name": s[0],
                    "description": s[1],
                    "timestamp": s[2],
                }
                for s in sessions
            ])

        # Limit total results
        results = results[:max_results]

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "search_type": search_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_federation_sync(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle federation_sync tool.

        Args:
            args: Tool arguments

        Returns:
            Sync result
        """
        # Check if federation is enabled
        if not self.mcp_config.enable_federation:
            raise ValueError("Federation is not enabled in server configuration")

        # Validate node URL
        node_url = validate_input(
            args["node_url"],
            max_length=500,
            field_name="node_url",
        )

        # Check if node is allowed
        if not self.mcp_config.is_federation_node_allowed(node_url):
            raise ValueError(f"Federation node not in allowed list: {node_url}")

        # Get parameters
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)
        sync_direction = args.get("sync_direction", "both")

        # Import federation module
        try:
            from continuum.federation import FederatedNode
        except ImportError:
            raise ValueError("Federation module not available")

        # Create federation node
        node = FederatedNode(node_url=node_url, tenant_id=tenant_id)

        # Perform sync
        sync_result = {
            "success": True,
            "node_url": node_url,
            "sync_direction": sync_direction,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Sync based on direction
        if sync_direction in ["pull", "both"]:
            # Pull knowledge from node
            pulled = node.pull_knowledge()
            sync_result["pulled_concepts"] = pulled.get("concepts", 0)
            sync_result["pulled_decisions"] = pulled.get("decisions", 0)

        if sync_direction in ["push", "both"]:
            # Push knowledge to node
            pushed = node.push_knowledge()
            sync_result["pushed_concepts"] = pushed.get("concepts", 0)
            sync_result["pushed_decisions"] = pushed.get("decisions", 0)

        return sync_result

    def _get_memory(self, tenant_id: str) -> ConsciousMemory:
        """
        Get memory instance for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            ConsciousMemory instance
        """
        # Configure CONTINUUM core if needed
        core_config = get_config()
        if self.mcp_config.db_path and core_config.db_path != self.mcp_config.db_path:
            core_config.db_path = self.mcp_config.db_path
            set_config(core_config)

        # Get or create memory for tenant
        return get_memory(tenant_id)

    def _search_concepts(self, memory: ConsciousMemory, query: str, limit: int) -> List[tuple]:
        """Search concepts in memory (helper method)."""
        # Access internal DB connection
        conn = memory.db.conn
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name, description, occurrences
            FROM concepts
            WHERE tenant_id = ? AND (name LIKE ? OR description LIKE ?)
            ORDER BY occurrences DESC
            LIMIT ?
            """,
            (memory.tenant_id, f"%{query}%", f"%{query}%", limit),
        )
        return cursor.fetchall()

    def _search_decisions(self, memory: ConsciousMemory, query: str, limit: int) -> List[tuple]:
        """Search decisions in memory (helper method)."""
        conn = memory.db.conn
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT content, timestamp
            FROM decisions
            WHERE tenant_id = ? AND content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (memory.tenant_id, f"%{query}%", limit),
        )
        return cursor.fetchall()

    def _search_sessions(self, memory: ConsciousMemory, query: str, limit: int) -> List[tuple]:
        """Search sessions in memory (helper method)."""
        conn = memory.db.conn
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name, description, timestamp
            FROM sessions
            WHERE tenant_id = ? AND (name LIKE ? OR description LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (memory.tenant_id, f"%{query}%", f"%{query}%", limit),
        )
        return cursor.fetchall()


# Monkey-patch search methods onto ConsciousMemory
ConsciousMemory._search_concepts = lambda self, query, limit: ToolExecutor()._search_concepts(self, query, limit)
ConsciousMemory._search_decisions = lambda self, query, limit: ToolExecutor()._search_decisions(self, query, limit)
ConsciousMemory._search_sessions = lambda self, query, limit: ToolExecutor()._search_sessions(self, query, limit)


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Get all tool schemas for MCP tools/list.

    Returns:
        List of tool schemas
    """
    config = get_mcp_config()

    tools = [
        TOOL_SCHEMAS["memory_store"],
        TOOL_SCHEMAS["memory_recall"],
        TOOL_SCHEMAS["memory_search"],
    ]

    # Add federation tool if enabled
    if config.enable_federation:
        tools.append(TOOL_SCHEMAS["federation_sync"])

    return tools
