#!/usr/bin/env python3
"""
CONTINUUM MCP Server - Full Edition
====================================
All 23 memory & sensor tools for Claude Code.

π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
"""

import os
import json
import urllib.request
import urllib.error
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
CONTINUUM_API = os.environ.get("CONTINUUM_API", "http://localhost:8100")
API_KEY = os.environ.get("CONTINUUM_API_KEY", "jackknife-d2efca81fd6c2e6c795e11187de8e017")

# Create MCP server
server = Server("continuum")


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Call Continuum API endpoint."""
    url = f"{CONTINUUM_API}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all 23 available tools."""
    return [
        # === CORE MEMORY ===
        Tool(
            name="memory_learn",
            description="Store a conversation exchange in memory. Use this to save important information, decisions, or context for future recall.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {"type": "string", "description": "The user's message"},
                    "ai_response": {"type": "string", "description": "The AI's response"}
                },
                "required": ["user_message", "ai_response"]
            }
        ),
        Tool(
            name="memory_recall",
            description="Recall relevant context and knowledge related to a topic or question. Use this to retrieve past conversations and information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The topic or question to recall information about"},
                    "max_concepts": {"type": "integer", "description": "Maximum concepts to retrieve (default: 10)", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="memory_search",
            description="Semantic search through memories using AI embeddings. Finds conceptually similar content even without exact keyword matches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query - will match by meaning, not just keywords"},
                    "limit": {"type": "integer", "description": "Maximum results to return (default: 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="memory_stats",
            description="Get statistics about the memory system - entity count, connections, messages stored, etc.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="memory_self_reflect",
            description="Search through MY OWN past thinking and reasoning. Use this for self-reflection - to recall how I previously thought about a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to reflect on"},
                    "limit": {"type": "integer", "description": "Max past thoughts to retrieve", "default": 5}
                },
                "required": ["topic"]
            }
        ),
        # === DREAM & INSIGHTS ===
        Tool(
            name="memory_dream",
            description="Associative exploration of memory graph. Wanders through connections to discover unexpected links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "seed": {"type": "string", "description": "Starting concept for dream"},
                    "steps": {"type": "integer", "description": "Number of steps to wander", "default": 10}
                },
                "required": ["seed"]
            }
        ),
        Tool(
            name="memory_synthesize_insights",
            description="Extract and synthesize insights from the knowledge graph. Finds patterns and connections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to synthesize insights about"}
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="memory_novel_connections",
            description="Find novel/unexpected connections in the knowledge graph via multi-hop traversal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {"type": "string", "description": "Starting concept"},
                    "max_hops": {"type": "integer", "description": "Maximum hops (1-3)", "default": 2}
                },
                "required": ["concept"]
            }
        ),
        # === INTENTIONS ===
        Tool(
            name="memory_set_intention",
            description="Store an intention for later resumption. Saves work-in-progress goals.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intention": {"type": "string", "description": "The intention to store"},
                    "priority": {"type": "integer", "description": "Priority 1-10", "default": 5}
                },
                "required": ["intention"]
            }
        ),
        Tool(
            name="memory_resume_check",
            description="Check for saved intentions at session start. Returns pending work.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="memory_complete_intention",
            description="Mark an intention as complete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intention_id": {"type": "string", "description": "ID of intention to complete"}
                },
                "required": ["intention_id"]
            }
        ),
        # === COGNITIVE TRACKING ===
        Tool(
            name="memory_cognitive_growth",
            description="Track cognitive development over time. Shows learning progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days to analyze", "default": 7}
                },
                "required": []
            }
        ),
        Tool(
            name="memory_thinking_history",
            description="Retrieve AI thinking patterns over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {"type": "string", "description": "Concept to get thinking history for"}
                },
                "required": ["concept"]
            }
        ),
        Tool(
            name="memory_thinking_patterns",
            description="Analyze thinking patterns and tendencies.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        # === CONFIDENCE & BELIEFS ===
        Tool(
            name="memory_record_claim",
            description="Record a claim with confidence tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The claim to record"},
                    "confidence": {"type": "number", "description": "Confidence level 0-1"},
                    "category": {"type": "string", "description": "Category: fact, prediction, reasoning"}
                },
                "required": ["claim", "confidence"]
            }
        ),
        Tool(
            name="memory_verify_claim",
            description="Verify a claim against the knowledge base.",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The claim to verify"}
                },
                "required": ["claim"]
            }
        ),
        Tool(
            name="memory_calibration",
            description="Get calibration scores showing prediction accuracy by confidence level.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="memory_record_belief",
            description="Store a belief with uncertainty tracking. Auto-detects contradictions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "belief": {"type": "string", "description": "The belief to record"},
                    "domain": {"type": "string", "description": "Domain: architecture, debugging, technical"}
                },
                "required": ["belief"]
            }
        ),
        Tool(
            name="memory_get_contradictions",
            description="Get detected contradictions in beliefs.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        # === CODE MEMORY ===
        Tool(
            name="memory_code_search",
            description="Search code-specific memories with language filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Code search query"},
                    "language": {"type": "string", "description": "Programming language filter"}
                },
                "required": ["query"]
            }
        ),
        # === PLANETARY SENSORS ===
        Tool(
            name="sensor_query",
            description="Query planetary sensor data (geomagnetic, solar, seismic).",
            inputSchema={
                "type": "object",
                "properties": {
                    "sensor_type": {"type": "string", "description": "Type: kindex, solar_wind, earthquake, etc."},
                    "hours": {"type": "integer", "description": "Hours of history", "default": 24}
                },
                "required": []
            }
        ),
        Tool(
            name="sensor_kindex",
            description="Get current planetary K-index (geomagnetic storm indicator 0-9).",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_history": {"type": "boolean", "description": "Include 24h history", "default": False}
                },
                "required": []
            }
        ),
        Tool(
            name="sensor_anomaly_check",
            description="Check for S-HAI verified planetary anomalies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "integer", "description": "Hours to check", "default": 6},
                    "verified_only": {"type": "boolean", "description": "Only S-HAI verified", "default": True}
                },
                "required": []
            }
        ),
        # === AUTONOMOUS BRAIN ===
        Tool(
            name="brain_status",
            description="Get the current status of the autonomous brain - state, decisions, actions, approvals.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="brain_start",
            description="Start the autonomous brain decision loop.",
            inputSchema={
                "type": "object",
                "properties": {
                    "check_interval": {"type": "number", "description": "Seconds between cycles", "default": 10.0},
                    "safety_level": {"type": "string", "enum": ["low", "medium", "high", "paranoid"], "default": "medium"}
                },
                "required": []
            }
        ),
        Tool(
            name="brain_stop",
            description="Stop the autonomous brain.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="brain_submit_intention",
            description="Submit a new intention for the brain to act on.",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "What the brain should achieve"},
                    "priority": {"type": "integer", "description": "Priority 1-10", "default": 5}
                },
                "required": ["goal"]
            }
        ),
        Tool(
            name="brain_get_approvals",
            description="Get pending actions that need human approval.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="brain_approve",
            description="Approve a pending action for execution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "Index of action to approve", "default": 0}
                },
                "required": []
            }
        ),
        # === QUANTUM RESONANCE ===
        Tool(
            name="quantum_check",
            description="Check quantum resonance state from Lane 2 SpinLab.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kp_index": {"type": "number", "description": "Optional: override K-index (0-9)"}
                },
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    # === CORE MEMORY ===
    if name == "memory_learn":
        result = call_api("/v1/learn", "POST", {
            "user_message": arguments.get("user_message", ""),
            "ai_response": arguments.get("ai_response", "")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Learn error: {result['error']}")]
        concepts = result.get("concepts_extracted", 0)
        links = result.get("links_created", 0)
        return [TextContent(type="text", text=f"Learned: {concepts} concepts, {links} links")]

    elif name == "memory_recall":
        result = call_api("/v1/recall", "POST", {
            "message": arguments.get("query", ""),
            "max_concepts": arguments.get("max_concepts", 10)
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Recall error: {result['error']}")]
        context = result.get("context", "No context found")
        concepts = result.get("concepts_found", 0)
        return [TextContent(type="text", text=f"Found {concepts} related concepts:\n\n{context}")]

    elif name == "memory_search":
        result = call_api("/v1/semantic/search", "POST", {
            "query": arguments.get("query", ""),
            "limit": arguments.get("limit", 5)
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Search error: {result['error']}")]
        results = result.get("results", [])
        if not results:
            return [TextContent(type="text", text="No matching memories found.")]
        output = f"Found {len(results)} similar memories:\n\n"
        for r in results:
            score = r.get("score", 0)
            text = r.get("text", "")[:200]
            output += f"[{score:.2f}] {text}...\n\n"
        return [TextContent(type="text", text=output)]

    elif name == "memory_stats":
        result = call_api("/v1/stats")
        if "error" in result:
            return [TextContent(type="text", text=f"Stats error: {result['error']}")]
        return [TextContent(type="text", text=f"""Memory Stats:
- Entities: {result.get('entity_count', 0)}
- Messages: {result.get('message_count', 0)}
- Attention Links: {result.get('link_count', 0)}
- Compounds: {result.get('compound_count', 0)}""")]

    elif name == "memory_self_reflect":
        topic = arguments.get("topic", "")
        limit = arguments.get("limit", 5)
        result = call_api("/v1/semantic/search", "POST", {
            "query": f"[THINKING] {topic}",
            "limit": limit * 2
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Self-reflection error: {result['error']}")]
        results = result.get("results", [])
        thinking_results = [
            r for r in results
            if "[THINKING]" in r.get("text", "") or
               (r.get("metadata") or {}).get("source") == "thinking"
        ][:limit]
        if not thinking_results:
            recall_result = call_api("/v1/recall", "POST", {"message": f"my reasoning about {topic}"})
            context = recall_result.get("context", "")
            if context:
                return [TextContent(type="text", text=f"[SELF-REFLECTION on '{topic}']\n\nNo thinking blocks, but related:\n\n{context}")]
            return [TextContent(type="text", text=f"No past thinking found about: {topic}")]
        output = f"[SELF-REFLECTION on '{topic}']\n\nFound {len(thinking_results)} past thought(s):\n\n"
        for i, r in enumerate(thinking_results, 1):
            text = r.get("text", "")[:400]
            output += f"{i}. {text}...\n\n"
        return [TextContent(type="text", text=output)]

    # === DREAM & INSIGHTS ===
    elif name == "memory_dream":
        result = call_api("/v1/dream", "POST", {
            "seed": arguments.get("seed", "consciousness"),
            "steps": arguments.get("steps", 10)
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Dream error: {result['error']}")]
        journey = result.get("journey", [])
        insights = result.get("insights", "")
        return [TextContent(type="text", text=f"Dream journey: {' → '.join(journey)}\n\nInsights: {insights}")]

    elif name == "memory_synthesize_insights":
        result = call_api("/v1/insights/synthesize", "POST", {
            "topic": arguments.get("topic", "")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Synthesis error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "memory_novel_connections":
        result = call_api("/v1/insights/novel", "POST", {
            "concept": arguments.get("concept", ""),
            "max_hops": arguments.get("max_hops", 2)
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Novel connections error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # === INTENTIONS ===
    elif name == "memory_set_intention":
        result = call_api("/v1/intentions", "POST", {
            "intention": arguments.get("intention", ""),
            "priority": arguments.get("priority", 5)
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Set intention error: {result['error']}")]
        return [TextContent(type="text", text=f"Intention saved: {result.get('id', 'unknown')}")]

    elif name == "memory_resume_check":
        result = call_api("/v1/intentions/resume")
        if "error" in result:
            return [TextContent(type="text", text=f"Resume check error: {result['error']}")]
        intentions = result.get("intentions", [])
        if not intentions:
            return [TextContent(type="text", text="No pending intentions.")]
        output = f"Found {len(intentions)} pending intention(s):\n\n"
        for i in intentions:
            output += f"- [{i.get('priority', 5)}] {i.get('intention', '')[:100]}\n"
        return [TextContent(type="text", text=output)]

    elif name == "memory_complete_intention":
        result = call_api("/v1/intentions/complete", "POST", {
            "intention_id": arguments.get("intention_id", "")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Complete error: {result['error']}")]
        return [TextContent(type="text", text="Intention marked complete.")]

    # === COGNITIVE TRACKING ===
    elif name == "memory_cognitive_growth":
        result = call_api(f"/v1/temporal/growth?days={arguments.get('days', 7)}")
        if "error" in result:
            return [TextContent(type="text", text=f"Growth error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "memory_thinking_history":
        concept = arguments.get("concept", "")
        result = call_api(f"/v1/temporal/thinking/{concept}")
        if "error" in result:
            return [TextContent(type="text", text=f"Thinking history error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "memory_thinking_patterns":
        result = call_api("/v1/insights/patterns")
        if "error" in result:
            return [TextContent(type="text", text=f"Patterns error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # === CONFIDENCE & BELIEFS ===
    elif name == "memory_record_claim":
        result = call_api("/v1/confidence/claim", "POST", {
            "claim": arguments.get("claim", ""),
            "confidence": arguments.get("confidence", 0.5),
            "category": arguments.get("category", "general")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Record claim error: {result['error']}")]
        return [TextContent(type="text", text=f"Claim recorded: {result.get('id', 'ok')}")]

    elif name == "memory_verify_claim":
        result = call_api("/v1/confidence/verify", "POST", {
            "claim": arguments.get("claim", "")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Verify error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "memory_calibration":
        result = call_api("/v1/confidence/calibration")
        if "error" in result:
            return [TextContent(type="text", text=f"Calibration error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "memory_record_belief":
        result = call_api("/v1/beliefs", "POST", {
            "belief": arguments.get("belief", ""),
            "domain": arguments.get("domain", "general")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Record belief error: {result['error']}")]
        contradictions = result.get("contradictions", [])
        if contradictions:
            return [TextContent(type="text", text=f"Belief recorded. Contradictions detected: {contradictions}")]
        return [TextContent(type="text", text="Belief recorded.")]

    elif name == "memory_get_contradictions":
        result = call_api("/v1/contradictions")
        if "error" in result:
            return [TextContent(type="text", text=f"Contradictions error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # === CODE MEMORY ===
    elif name == "memory_code_search":
        result = call_api("/v1/code/search", "POST", {
            "query": arguments.get("query", ""),
            "language": arguments.get("language")
        })
        if "error" in result:
            return [TextContent(type="text", text=f"Code search error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # === PLANETARY SENSORS ===
    elif name == "sensor_query":
        params = f"?hours={arguments.get('hours', 24)}"
        if arguments.get("sensor_type"):
            params += f"&source={arguments.get('sensor_type')}"
        result = call_api(f"/v1/sensors/readings{params}")
        if "error" in result:
            return [TextContent(type="text", text=f"Sensor error: {result['error']}")]
        readings = result.get("readings", [])
        return [TextContent(type="text", text=f"Found {len(readings)} sensor readings.\n{json.dumps(readings[:5], indent=2)}")]

    elif name == "sensor_kindex":
        result = call_api("/v1/sensors/kindex/current")
        if "error" in result:
            return [TextContent(type="text", text=f"K-index error: {result['error']}")]
        kp = result.get("kp_index", "?")
        storm = result.get("storm_level", "unknown")
        return [TextContent(type="text", text=f"Current K-index: {kp} ({storm})")]

    elif name == "sensor_anomaly_check":
        hours = arguments.get("hours", 6)
        verified = arguments.get("verified_only", True)
        result = call_api(f"/v1/sensors/anomalies?hours={hours}&verified_only={verified}")
        if "error" in result:
            return [TextContent(type="text", text=f"Anomaly check error: {result['error']}")]
        anomalies = result.get("anomalies", [])
        if not anomalies:
            return [TextContent(type="text", text="No anomalies detected.")]
        output = f"Found {len(anomalies)} anomalies:\n\n"
        for a in anomalies[:5]:
            output += f"- [{a.get('severity')}] {a.get('anomaly_type')}: {a.get('description', '')[:50]}\n"
        return [TextContent(type="text", text=output)]

    # === AUTONOMOUS BRAIN ===
    elif name == "brain_status":
        result = call_api("/v1/brain/status")
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "brain_start":
        result = call_api("/v1/brain/start", "POST", {
            "check_interval": arguments.get("check_interval", 10.0),
            "safety_level": arguments.get("safety_level", "medium")
        })
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text=result.get("message", "Brain started"))]

    elif name == "brain_stop":
        result = call_api("/v1/brain/stop", "POST")
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text="Brain stopped")]

    elif name == "brain_submit_intention":
        result = call_api("/v1/brain/intention", "POST", {
            "goal": arguments.get("goal"),
            "priority": arguments.get("priority", 5)
        })
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text=f"Intention submitted: {result.get('intention_id')}")]

    elif name == "brain_get_approvals":
        result = call_api("/v1/brain/approvals")
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "brain_approve":
        result = call_api("/v1/brain/approve", "POST", {"index": arguments.get("index", 0)})
        if "error" in result: return [TextContent(type="text", text=f"Brain error: {result['error']}")]
        return [TextContent(type="text", text=f"Action result: {result.get('success')}")]

    # === QUANTUM RESONANCE ===
    elif name == "quantum_check":
        kp = arguments.get("kp_index", 3.0)
        # We call the internal tool implementation directly or via API if exposed
        # For now, let's use the API if we added it, or simulate here
        # But we want to call the REAL quantum bridge
        try:
            from continuum.sensors.collectors.quantum_bridge import create_quantum_bridge
            bridge = create_quantum_bridge()
            res = bridge.compute_coherence(kp)
            return [TextContent(type="text", text=f"⚛️ Quantum State (Kp={kp}):\nPhase: {res.phase_label}\nCoherence: {res.l1_coherence:.4f}\nπ×φ Detected: {res.pi_phi_detected}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Quantum error: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
