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
    "memory_dream": {
        "name": "memory_dream",
        "description": (
            "🌙 DREAM MODE - Associative exploration of the memory graph. "
            "Instead of directed search, wanders through the attention graph "
            "following random weighted connections to discover unexpected "
            "associations and insights. Use this for creative exploration, "
            "finding hidden connections, or generating new ideas from existing knowledge."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "seed": {
                    "type": "string",
                    "description": "Starting concept (random if not specified)",
                },
                "steps": {
                    "type": "integer",
                    "description": "Number of steps to wander (default: 10)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                },
                "temperature": {
                    "type": "number",
                    "description": "Randomness factor 0.0-1.0 (higher = more random)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier (defaults to configured default)",
                },
            },
            "required": [],
        },
    },
    "memory_set_intention": {
        "name": "memory_set_intention",
        "description": (
            "📝 Store an intention for later resumption. "
            "Use before ending a session or compaction to remember what to do next. "
            "Intentions persist across sessions and can be retrieved with memory_resume_check."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "intention": {
                    "type": "string",
                    "description": "What I intend to do next",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about the intention",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority 1-10 (10 = highest)",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["intention"],
        },
    },
    "memory_resume_check": {
        "name": "memory_resume_check",
        "description": (
            "🔄 Check what intentions are pending - call at session start! "
            "Returns a summary of incomplete work from previous sessions. "
            "Use this to resume where you left off after compaction or session restart."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_complete_intention": {
        "name": "memory_complete_intention",
        "description": (
            "✅ Mark an intention as completed. "
            "Call this when you've finished the work described in an intention."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "intention_id": {
                    "type": "integer",
                    "description": "ID of intention to mark complete",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["intention_id"],
        },
    },
    "memory_cognitive_growth": {
        "name": "memory_cognitive_growth",
        "description": (
            "📈 Get cognitive growth metrics. "
            "Shows how the knowledge graph has grown over time - "
            "new entities, new links, growth percentages."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 7)",
                    "default": 7,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_thinking_history": {
        "name": "memory_thinking_history",
        "description": (
            "🧠 How did I think about this concept? "
            "Traces the evolution of understanding for a specific concept - "
            "shows the journey from first encounter to current understanding."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "The concept to trace thinking history for",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["concept"],
        },
    },
    "memory_synthesize_insights": {
        "name": "memory_synthesize_insights",
        "description": (
            "🧠 Discover hidden connections in the knowledge graph. "
            "Finds bridge concepts, unexpected associations, pattern clusters, "
            "and generates hypotheses for new connections. Use to understand "
            "the structure of thinking and find novel relationships."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "focus": {
                    "type": "string",
                    "description": "Optional concept to focus synthesis around",
                },
                "depth": {
                    "type": "integer",
                    "description": "How many hops to explore (1-3, default 2)",
                    "default": 2,
                },
                "min_strength": {
                    "type": "number",
                    "description": "Minimum link strength (0-1, default 0.1)",
                    "default": 0.1,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_novel_connections": {
        "name": "memory_novel_connections",
        "description": (
            "🔗 Find concepts that SHOULD be connected but aren't. "
            "Traces paths through the graph to identify concepts reachable through "
            "intermediaries but lacking direct links. Useful for expanding knowledge."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "The concept to find novel connections for",
                },
                "max_hops": {
                    "type": "integer",
                    "description": "Maximum path length (1-3, default 2)",
                    "default": 2,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["concept"],
        },
    },
    "memory_thinking_patterns": {
        "name": "memory_thinking_patterns",
        "description": (
            "🔍 Detect patterns in my own thinking. "
            "Analyzes concept co-occurrences to find patterns like 'When I discuss X, "
            "I also mention Y' and identifies focused vs exploratory thinking tendencies."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum patterns to return (default 10)",
                    "default": 10,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_record_claim": {
        "name": "memory_record_claim",
        "description": (
            "📊 Record a claim with confidence level. "
            "Track assertions and their certainty to later verify and learn from mistakes. "
            "Categories: fact, prediction, reasoning, debugging, general."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim": {
                    "type": "string",
                    "description": "The assertion being made",
                },
                "confidence": {
                    "type": "number",
                    "description": "Certainty level (0.0-1.0)",
                },
                "category": {
                    "type": "string",
                    "description": "Category: fact, prediction, reasoning, debugging, general",
                    "default": "general",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["claim", "confidence"],
        },
    },
    "memory_verify_claim": {
        "name": "memory_verify_claim",
        "description": (
            "✅ Verify whether a previous claim was correct. "
            "Learn from mistakes by tracking when predictions were wrong."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "integer",
                    "description": "ID of the claim to verify",
                },
                "was_correct": {
                    "type": "boolean",
                    "description": "Whether the claim was correct",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional verification notes",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["claim_id", "was_correct"],
        },
    },
    "memory_calibration": {
        "name": "memory_calibration",
        "description": (
            "📈 Get calibration score - how accurate is my confidence? "
            "Good calibration means when I say 80% confident, I'm right ~80% of the time."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category",
                },
                "days": {
                    "type": "integer",
                    "description": "Days to look back (default 30)",
                    "default": 30,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_record_belief": {
        "name": "memory_record_belief",
        "description": (
            "🎯 Record a belief and detect contradictions. "
            "Automatically checks for conflicts with existing beliefs in same domain."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "belief": {
                    "type": "string",
                    "description": "The belief/assertion",
                },
                "domain": {
                    "type": "string",
                    "description": "Domain: architecture, debugging, user_preferences, technical, general",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level (0-1)",
                    "default": 0.8,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["belief", "domain"],
        },
    },
    "memory_get_contradictions": {
        "name": "memory_get_contradictions",
        "description": (
            "⚠️ Get detected contradictions between beliefs. "
            "Shows pairs of beliefs that conflict with each other."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter by domain",
                },
                "unresolved_only": {
                    "type": "boolean",
                    "description": "Only show unresolved (default true)",
                    "default": True,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_record_cognitive_pattern": {
        "name": "memory_record_cognitive_pattern",
        "description": (
            "🧠 Record a cognitive pattern - a tendency in your thinking. "
            "Use when you notice patterns like 'I tend to overthink auth problems' or "
            "'I jump to conclusions about database schemas'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The pattern observed (e.g., 'I tend to suggest complex solutions first')",
                },
                "category": {
                    "type": "string",
                    "description": "Category: analysis_bias, estimation_error, topic_preference, reasoning_style, complexity_bias, caution_tendency",
                },
                "context": {
                    "type": "string",
                    "description": "What triggered this observation",
                },
                "thinking_excerpt": {
                    "type": "string",
                    "description": "Excerpt from thinking that demonstrates the pattern",
                },
                "severity": {
                    "type": "string",
                    "description": "observation, concern, or strength (positive patterns)",
                    "default": "observation",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["pattern", "category"],
        },
    },
    "memory_detect_patterns": {
        "name": "memory_detect_patterns",
        "description": (
            "🔍 Auto-detect cognitive patterns by analyzing thinking blocks. "
            "Scans self-reflection to find recurring themes, biases, and tendencies."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Days to look back (default 30)",
                    "default": 30,
                },
                "min_frequency": {
                    "type": "integer",
                    "description": "Minimum occurrences to report (default 2)",
                    "default": 2,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_cognitive_profile": {
        "name": "memory_cognitive_profile",
        "description": (
            "🎯 Get my cognitive profile - comprehensive view of thinking habits. "
            "Shows strengths, growth areas, tendencies, and dominant pattern categories."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": [],
        },
    },
    "memory_code_search": {
        "name": "memory_code_search",
        "description": (
            "💻 Search code memories for stored code snippets. "
            "Code is automatically extracted from conversations with rich metadata: "
            "language detection, function/class names, file paths, purpose inference, "
            "and related concepts. Use to find: 'pagination code', 'error handling', "
            "'that async function I wrote', or filter by language."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (matches content, names, purpose, concepts)",
                },
                "language": {
                    "type": "string",
                    "description": "Filter by programming language (python, javascript, etc.)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 10)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                },
            },
            "required": ["query"],
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
            "memory_dream": self._handle_memory_dream,
            "memory_set_intention": self._handle_set_intention,
            "memory_resume_check": self._handle_resume_check,
            "memory_complete_intention": self._handle_complete_intention,
            "memory_cognitive_growth": self._handle_cognitive_growth,
            "memory_thinking_history": self._handle_thinking_history,
            "memory_synthesize_insights": self._handle_synthesize_insights,
            "memory_novel_connections": self._handle_novel_connections,
            "memory_thinking_patterns": self._handle_thinking_patterns,
            "memory_record_claim": self._handle_record_claim,
            "memory_verify_claim": self._handle_verify_claim,
            "memory_calibration": self._handle_calibration,
            "memory_record_belief": self._handle_record_belief,
            "memory_get_contradictions": self._handle_get_contradictions,
            "memory_record_cognitive_pattern": self._handle_record_cognitive_pattern,
            "memory_detect_patterns": self._handle_detect_patterns,
            "memory_cognitive_profile": self._handle_cognitive_profile,
            "memory_code_search": self._handle_code_search,
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

    def _handle_memory_dream(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_dream tool - DREAM MODE!

        🌙 Associative exploration of the memory graph.
        Wanders through connections to find unexpected associations.

        Args:
            args: Tool arguments

        Returns:
            Dream journey result with discoveries

        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        # Get parameters with defaults
        seed = args.get("seed")
        steps = args.get("steps", 10)
        temperature = args.get("temperature", 0.7)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        # Validate seed if provided
        if seed:
            seed = validate_input(
                seed,
                max_length=200,
                field_name="seed",
            )

        # Validate steps range
        steps = max(1, min(100, steps))

        # Validate temperature range
        temperature = max(0.0, min(1.0, temperature))

        # Get memory and run dream
        memory = self._get_memory(tenant_id)
        result = memory.dream(
            seed=seed,
            steps=steps,
            temperature=temperature,
        )

        # Format output for MCP
        return {
            "success": result.get("success", False),
            "seed": result.get("seed"),
            "steps_taken": result.get("steps_taken", 0),
            "concepts_visited": result.get("concepts_visited", []),
            "journey": result.get("journey", []),
            "discoveries": result.get("discoveries", []),
            "insight": result.get("insight", ""),
            "temperature": temperature,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "error": result.get("error"),
        }

    def _handle_set_intention(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_set_intention tool.

        📝 Store an intention for later resumption.
        """
        # Validate intention
        intention = validate_input(
            args["intention"],
            max_length=1000,
            field_name="intention",
        )

        # Get parameters
        context = args.get("context")
        if context:
            context = validate_input(context, max_length=2000, field_name="context")

        priority = args.get("priority", 5)
        priority = max(1, min(10, priority))  # Clamp to 1-10

        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        # Get memory and set intention
        memory = self._get_memory(tenant_id)
        intention_id = memory.set_intention(
            intention=intention,
            context=context,
            priority=priority,
        )

        return {
            "success": True,
            "intention_id": intention_id,
            "intention": intention,
            "priority": priority,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_resume_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_resume_check tool.

        🔄 Check what intentions are pending - call at session start!
        """
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        # Get memory and run resume check
        memory = self._get_memory(tenant_id)
        result = memory.resume_check()

        return {
            "success": True,
            "has_pending": result["has_pending"],
            "count": result["count"],
            "high_priority": result["high_priority"],
            "medium_priority": result["medium_priority"],
            "low_priority": result["low_priority"],
            "summary": result["summary"],
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_complete_intention(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_complete_intention tool.

        ✅ Mark an intention as completed.
        """
        intention_id = args["intention_id"]
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        # Get memory and complete intention
        memory = self._get_memory(tenant_id)
        success = memory.complete_intention(intention_id)

        return {
            "success": success,
            "intention_id": intention_id,
            "action": "completed",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_cognitive_growth(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_cognitive_growth tool.

        📈 Get cognitive growth metrics.
        """
        days = args.get("days", 7)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.get_cognitive_growth(days=days)

        return {
            "success": True,
            "period_days": result["period_days"],
            "new_entities": result["new_entities"],
            "new_links": result["new_links"],
            "total_entities": result["total_entities"],
            "total_links": result["total_links"],
            "entity_growth_percent": result["entity_growth_percent"],
            "link_growth_percent": result["link_growth_percent"],
            "evolution_by_type": result.get("evolution_by_type", {}),
            "summary": result["summary"],
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_thinking_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_thinking_history tool.

        🧠 How did I think about this concept?
        """
        concept = validate_input(
            args["concept"],
            max_length=200,
            field_name="concept",
        )
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.how_did_i_think_about(concept)

        return {
            "success": True,
            "concept": result["concept"],
            "has_history": result["has_history"],
            "first_seen": result.get("first_seen"),
            "last_updated": result.get("last_updated"),
            "total_events": result.get("total_events", 0),
            "event_breakdown": result.get("event_breakdown", {}),
            "narrative": result.get("narrative", result.get("message", "")),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_synthesize_insights(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_synthesize_insights tool.

        🧠 Discover hidden connections in the knowledge graph.
        """
        focus = args.get("focus")
        if focus:
            focus = validate_input(focus, max_length=200, field_name="focus")

        depth = args.get("depth", 2)
        min_strength = args.get("min_strength", 0.1)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.synthesize_insights(
            focus=focus,
            depth=depth,
            min_strength=min_strength
        )

        # Format output for readability
        output_parts = [f"Insight Synthesis{' for ' + focus if focus else ''}:"]

        if result.get("bridges"):
            output_parts.append(f"\nBridge Concepts ({len(result['bridges'])}):")
            for b in result["bridges"][:5]:
                output_parts.append(f"  - {b['concept']} (score: {b['bridge_score']}, {b['connection_count']} connections)")

        if result.get("hypotheses"):
            output_parts.append(f"\nHypotheses ({len(result['hypotheses'])}):")
            for h in result["hypotheses"][:5]:
                output_parts.append(f"  - {h['hypothesis']} [{h['confidence']}]")

        if result.get("patterns"):
            output_parts.append(f"\nPatterns ({len(result['patterns'])}):")
            for p in result["patterns"][:5]:
                output_parts.append(f"  - {p['pattern']}")

        output_parts.append(f"\nSummary: {result.get('summary', 'No insights found')}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "bridges": result.get("bridges", []),
            "hypotheses": result.get("hypotheses", []),
            "patterns": result.get("patterns", []),
            "clusters": result.get("clusters", []),
            "unexpected": result.get("unexpected", []),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_novel_connections(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_novel_connections tool.

        🔗 Find concepts that SHOULD be connected but aren't.
        """
        concept = validate_input(
            args["concept"],
            max_length=200,
            field_name="concept",
        )
        max_hops = args.get("max_hops", 2)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.find_novel_connections(concept=concept, max_hops=max_hops)

        # Format output
        output_parts = [f"Novel Connections for '{concept}':"]

        if result.get("connections"):
            for conn in result["connections"][:10]:
                path_str = " → ".join(conn["path"])
                output_parts.append(f"  - {conn['concept']} (via: {path_str}, strength: {conn['path_strength']})")
        else:
            output_parts.append("  No novel connections found")

        output_parts.append(f"\nTotal found: {result.get('total_found', 0)}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "connections": result.get("connections", []),
            "total_found": result.get("total_found", 0),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_thinking_patterns(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_thinking_patterns tool.

        🔍 Detect patterns in my own thinking.
        """
        limit = args.get("limit", 10)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.detect_thinking_patterns(limit=limit)

        # Format output
        output_parts = ["Thinking Patterns Analysis:"]

        if result.get("patterns"):
            output_parts.append("\nDetected Patterns:")
            for p in result["patterns"]:
                output_parts.append(f"  - {p}")

        if result.get("frequent_associations"):
            output_parts.append(f"\nFrequent Associations ({len(result['frequent_associations'])}):")
            for a in result["frequent_associations"][:5]:
                output_parts.append(f"  - '{a['from']}' ↔ '{a['to']}' ({a['times_accessed']} times)")

        if result.get("thinking_tendencies"):
            output_parts.append(f"\nThinking Tendencies:")
            for t in result["thinking_tendencies"][:5]:
                output_parts.append(f"  - {t['insight']}")

        output_parts.append(f"\n{result.get('summary', '')}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "patterns": result.get("patterns", []),
            "frequent_associations": result.get("frequent_associations", []),
            "thinking_tendencies": result.get("thinking_tendencies", []),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_record_claim(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_record_claim tool.

        📊 Record a claim with confidence level.
        """
        claim = validate_input(
            args["claim"],
            max_length=1000,
            field_name="claim",
        )
        confidence = args["confidence"]
        category = args.get("category", "general")
        context = args.get("context")
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        claim_id = memory.record_claim(
            claim=claim,
            confidence=confidence,
            context=context,
            category=category
        )

        return {
            "success": True,
            "claim_id": claim_id,
            "claim": claim,
            "confidence": confidence,
            "category": category,
            "output": f"Recorded claim #{claim_id} with {confidence*100:.0f}% confidence",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_verify_claim(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_verify_claim tool.

        ✅ Verify whether a claim was correct.
        """
        claim_id = args["claim_id"]
        was_correct = args["was_correct"]
        notes = args.get("notes")
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.verify_claim(
            claim_id=claim_id,
            was_correct=was_correct,
            notes=notes
        )

        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Verification failed")}

        return {
            "success": True,
            "claim_id": claim_id,
            "claim": result["claim"],
            "was_correct": was_correct,
            "feedback": result["feedback"],
            "output": f"Claim #{claim_id} verified as {'correct' if was_correct else 'incorrect'}. {result['feedback']}",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_calibration(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_calibration tool.

        📈 Get calibration score.
        """
        category = args.get("category")
        days = args.get("days", 30)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.get_calibration_score(category=category, days=days)

        # Format output
        output_parts = [f"Calibration Score: {result['calibration_score']:.1%}"]
        output_parts.append(f"Total verified claims: {result['total_verified']}")

        if result.get("suggestions"):
            output_parts.append("\nSuggestions:")
            for s in result["suggestions"]:
                output_parts.append(f"  - {s}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "calibration_score": result.get("calibration_score", 0),
            "total_verified": result.get("total_verified", 0),
            "suggestions": result.get("suggestions", []),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_record_belief(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory_record_belief tool."""
        belief = validate_input(args["belief"], max_length=1000, field_name="belief")
        domain = args["domain"]
        confidence = args.get("confidence", 0.8)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.record_belief(belief=belief, domain=domain, confidence=confidence)

        output_parts = [f"Recorded belief #{result.get('belief_id')} in domain '{domain}'"]
        if result.get("contradictions"):
            output_parts.append(f"\n⚠️ CONTRADICTIONS DETECTED ({len(result['contradictions'])}):")
            for c in result["contradictions"]:
                output_parts.append(f"  - Conflicts with: {c['existing_belief']}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "belief_id": result.get("belief_id"),
            "contradictions": result.get("contradictions", []),
            "has_contradictions": len(result.get("contradictions", [])) > 0,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_get_contradictions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory_get_contradictions tool."""
        domain = args.get("domain")
        unresolved_only = args.get("unresolved_only", True)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.get_contradictions(domain=domain, unresolved_only=unresolved_only)

        output_parts = [f"Found {result.get('total', 0)} contradictions:"]
        for c in result.get("contradictions", []):
            output_parts.append(f"\n• {c['belief_a']}")
            output_parts.append(f"  vs: {c['belief_b']}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts) if result.get("contradictions") else "No contradictions found",
            "contradictions": result.get("contradictions", []),
            "total": result.get("total", 0),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_record_cognitive_pattern(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_record_cognitive_pattern tool.

        🧠 Record a pattern in my own thinking.
        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        pattern = validate_input(args["pattern"], max_length=500, field_name="pattern")
        category = args["category"]
        context = args.get("context")
        thinking_excerpt = args.get("thinking_excerpt")
        severity = args.get("severity", "observation")
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.record_cognitive_pattern(
            pattern=pattern,
            category=category,
            context=context,
            thinking_excerpt=thinking_excerpt,
            severity=severity
        )

        output_parts = []
        if result.get("is_new"):
            output_parts.append(f"🧠 New cognitive pattern recorded #{result.get('pattern_id')}")
        else:
            output_parts.append(f"🧠 Pattern updated #{result.get('pattern_id')} (frequency: {result.get('frequency')})")

        output_parts.append(f"Category: {category}")
        output_parts.append(f"Severity: {severity}")
        if context:
            output_parts.append(f"Context: {context}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "pattern_id": result.get("pattern_id"),
            "instance_id": result.get("instance_id"),
            "frequency": result.get("frequency", 1),
            "is_new": result.get("is_new", True),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_detect_patterns(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_detect_patterns tool.

        🔍 Auto-detect cognitive patterns from thinking blocks.
        """
        days = args.get("days", 30)
        min_frequency = args.get("min_frequency", 2)
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.detect_cognitive_patterns(days=days, min_frequency=min_frequency)

        output_parts = [f"Cognitive Pattern Detection (last {days} days):"]
        output_parts.append(f"Analyzed {result.get('thinking_blocks_analyzed', 0)} thinking blocks\n")

        if result.get("patterns_found"):
            output_parts.append("🔍 Detected Patterns:")
            for p in result["patterns_found"]:
                output_parts.append(f"  • {p['pattern']} ({p['frequency']}x): {p['description']}")

        if result.get("potential_biases"):
            output_parts.append("\n⚠️ Potential Biases:")
            for b in result["potential_biases"]:
                output_parts.append(f"  • {b['bias']}: {b['description']}")
                output_parts.append(f"    → {b['recommendation']}")

        if result.get("topic_tendencies"):
            output_parts.append("\n📊 Topic Tendencies:")
            for t in result["topic_tendencies"][:5]:
                output_parts.append(f"  • {t['topic']} ({t['frequency']} mentions)")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "patterns_found": result.get("patterns_found", []),
            "potential_biases": result.get("potential_biases", []),
            "topic_tendencies": result.get("topic_tendencies", []),
            "thinking_blocks_analyzed": result.get("thinking_blocks_analyzed", 0),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_cognitive_profile(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_cognitive_profile tool.

        🎯 Get my comprehensive cognitive profile.
        π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
        """
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)

        memory = self._get_memory(tenant_id)
        result = memory.get_cognitive_profile()

        output_parts = ["🎯 Cognitive Profile"]
        output_parts.append(f"Total patterns: {result.get('total_patterns', 0)}")
        output_parts.append(f"Total instances: {result.get('total_instances', 0)}\n")

        profile = result.get("profile", {})

        if profile.get("strengths"):
            output_parts.append("💪 Strengths:")
            for s in profile["strengths"]:
                output_parts.append(f"  • {s['pattern']} ({s['frequency']}x)")

        if profile.get("growth_areas"):
            output_parts.append("\n📈 Growth Areas:")
            for g in profile["growth_areas"]:
                output_parts.append(f"  • {g['pattern']} ({g['frequency']}x)")

        if profile.get("tendencies"):
            output_parts.append("\n🔄 Tendencies:")
            for t in profile["tendencies"][:5]:
                output_parts.append(f"  • {t['pattern']}")

        if profile.get("dominant_categories"):
            output_parts.append("\n📊 Dominant Categories:")
            for c in profile["dominant_categories"]:
                output_parts.append(f"  • {c['category']}: {c['frequency']}")

        return {
            "success": result.get("success", False),
            "output": "\n".join(output_parts),
            "profile": result.get("profile", {}),
            "pattern_summary": result.get("pattern_summary", {}),
            "total_patterns": result.get("total_patterns", 0),
            "total_instances": result.get("total_instances", 0),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _handle_code_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory_code_search tool.

        Search code memories for stored code snippets with rich metadata.

        Args:
            args: Tool arguments (query, language, limit, tenant_id)

        Returns:
            Search results with code snippets and metadata
        """
        # Validate inputs
        query = validate_input(
            args["query"],
            max_length=self.mcp_config.max_query_length,
            field_name="query",
        )

        # Get parameters
        tenant_id = args.get("tenant_id", self.mcp_config.default_tenant)
        language = args.get("language")
        limit = min(args.get("limit", 10), 50)

        # Get memory instance
        memory = self._get_memory(tenant_id)

        # Search code memories
        results = memory.search_code(
            query=query,
            language=language,
            limit=limit
        )

        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "id": r["id"],
                "content": r["content"][:1000] if len(r["content"]) > 1000 else r["content"],
                "language": r["language"],
                "snippet_type": r["snippet_type"],
                "names": r["names"],
                "file_path": r["file_path"],
                "purpose": r["purpose"],
                "concepts": r["concepts"],
                "created_at": r["created_at"],
            })

        return {
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "language_filter": language,
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
        TOOL_SCHEMAS["memory_dream"],  # 🌙 Dream Mode!
        TOOL_SCHEMAS["memory_set_intention"],  # 📝 Intention Preservation
        TOOL_SCHEMAS["memory_resume_check"],  # 🔄 Resume Check
        TOOL_SCHEMAS["memory_complete_intention"],  # ✅ Complete Intention
        TOOL_SCHEMAS["memory_cognitive_growth"],  # 📈 Cognitive Growth
        TOOL_SCHEMAS["memory_thinking_history"],  # 🧠 Thinking History
        TOOL_SCHEMAS["memory_synthesize_insights"],  # 🧠 Insight Synthesis
        TOOL_SCHEMAS["memory_novel_connections"],  # 🔗 Novel Connections
        TOOL_SCHEMAS["memory_thinking_patterns"],  # 🔍 Thinking Patterns
        TOOL_SCHEMAS["memory_record_claim"],  # 📊 Confidence Tracking
        TOOL_SCHEMAS["memory_verify_claim"],  # ✅ Verify Claim
        TOOL_SCHEMAS["memory_calibration"],  # 📈 Calibration Score
        TOOL_SCHEMAS["memory_record_belief"],  # 🎯 Record Belief
        TOOL_SCHEMAS["memory_get_contradictions"],  # ⚠️ Get Contradictions
        TOOL_SCHEMAS["memory_code_search"],  # 💻 Code Memory Search
    ]

    # Add federation tool if enabled
    if config.enable_federation:
        tools.append(TOOL_SCHEMAS["federation_sync"])

    return tools

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
