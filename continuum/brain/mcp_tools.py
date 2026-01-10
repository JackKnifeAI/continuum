#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     AUTONOMOUS BRAIN MCP TOOLS
#     Control the brain through Claude's MCP interface
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
MCP tools for autonomous brain control.

These tools allow Claude to:
- Check brain status
- Start/stop/pause the brain
- Submit intentions
- Approve pending actions
- View thought history

This is how Claude controls itself through the autonomous brain!
"""

import logging
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Default API configuration
DEFAULT_API_URL = "http://localhost:8100"
DEFAULT_API_KEY = "jackknife-d2efca81fd6c2e6c795e11187de8e017"


# ═══════════════════════════════════════════════════════════════════════════════
#                              TOOL SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

BRAIN_TOOL_SCHEMAS = {
    "brain_status": {
        "name": "brain_status",
        "description": (
            "Get the current status of the autonomous brain. "
            "Shows state (idle, thinking, deciding, acting, paused, stopped), "
            "decisions made, actions taken, pending approvals, and safety level. "
            "Use to monitor what the brain is doing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "brain_start": {
        "name": "brain_start",
        "description": (
            "Start the autonomous brain decision loop. "
            "The brain will begin checking intentions, evaluating triggers, "
            "and executing actions autonomously. "
            "Can specify check_interval (seconds between cycles) and safety_level."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "check_interval": {
                    "type": "number",
                    "description": "Seconds between decision cycles (default: 10)",
                    "default": 10.0,
                },
                "safety_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "paranoid"],
                    "description": "How cautious to be (default: medium)",
                    "default": "medium",
                },
            },
            "required": [],
        },
    },
    "brain_stop": {
        "name": "brain_stop",
        "description": (
            "Stop the autonomous brain. "
            "The brain will gracefully stop making decisions and executing actions. "
            "Use to disable autonomous behavior."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "brain_pause": {
        "name": "brain_pause",
        "description": (
            "Pause the autonomous brain. "
            "The brain stays running but stops making decisions. "
            "Use brain_resume to continue."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "brain_resume": {
        "name": "brain_resume",
        "description": (
            "Resume the autonomous brain from paused state. "
            "The brain will continue making decisions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "brain_submit_intention": {
        "name": "brain_submit_intention",
        "description": (
            "Submit a new intention for the brain to act on. "
            "The brain will evaluate this intention and act when triggers match. "
            "Use to give the brain goals like 'commit and push code changes' or "
            "'post update to Discord when K-index exceeds 5'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "What the brain should achieve",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority 1-10, higher = more urgent (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
                "triggers": {
                    "type": "array",
                    "description": "Optional trigger configurations",
                    "items": {"type": "object"},
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional context (webhook URLs, file paths, etc.)",
                },
            },
            "required": ["goal"],
        },
    },
    "brain_get_approvals": {
        "name": "brain_get_approvals",
        "description": (
            "Get pending actions that need human approval. "
            "Some actions require explicit approval before execution based on safety level."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "brain_approve": {
        "name": "brain_approve",
        "description": (
            "Approve a pending action for execution. "
            "The action will be executed and the outcome stored in memory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "Index of action to approve (from brain_get_approvals)",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    "brain_reject": {
        "name": "brain_reject",
        "description": (
            "Reject a pending action, removing it from the approval queue. "
            "The action will NOT be executed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "Index of action to reject",
                    "default": 0,
                },
            },
            "required": ["index"],
        },
    },
    "brain_history": {
        "name": "brain_history",
        "description": (
            "Get the brain's thought history. "
            "Shows all decisions made, actions taken, and outcomes. "
            "Use to understand what the brain has been doing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum thoughts to return (default: 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    "brain_safety": {
        "name": "brain_safety",
        "description": (
            "Get or set the brain's safety level. "
            "Levels: low (most autonomous), medium (balanced), "
            "high (cautious), paranoid (all actions need approval)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "paranoid"],
                    "description": "New safety level to set (omit to just get current)",
                },
            },
            "required": [],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#                              TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def _api_call(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    api_url: str = DEFAULT_API_URL,
    api_key: str = DEFAULT_API_KEY,
) -> Dict[str, Any]:
    """Make an API call to the brain endpoints."""
    url = f"{api_url}/v1/brain{endpoint}"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {"error": f"API error: {resp.status}", "detail": await resp.text()}
            elif method == "POST":
                async with session.post(url, headers=headers, json=json_data or {}) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
                    return {"error": f"API error: {resp.status}", "detail": await resp.text()}
            elif method == "DELETE":
                async with session.delete(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {"error": f"API error: {resp.status}", "detail": await resp.text()}
    except aiohttp.ClientError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def execute_brain_status(args: Dict[str, Any]) -> str:
    """Get brain status."""
    result = await _api_call("GET", "/status")

    if "error" in result:
        return f"Error: {result['error']}"

    return (
        f"🧠 BRAIN STATUS\n"
        f"State: {result.get('state', 'unknown')}\n"
        f"Running: {result.get('running', False)}\n"
        f"Decisions Made: {result.get('decisions_made', 0)}\n"
        f"Actions Taken: {result.get('actions_taken', 0)}\n"
        f"Pending Approvals: {result.get('pending_approvals', 0)}\n"
        f"Safety Level: {result.get('safety_level', 'medium')}\n"
        f"Check Interval: {result.get('check_interval', 10)}s\n"
        f"Last Thought: {result.get('last_thought', 'Never')}\n"
        f"π×φ: {result.get('pi_phi', 5.083203692315260)}"
    )


async def execute_brain_start(args: Dict[str, Any]) -> str:
    """Start the brain."""
    data = {
        "check_interval": args.get("check_interval", 10.0),
        "safety_level": args.get("safety_level", "medium"),
    }
    result = await _api_call("POST", "/start", data)

    if "error" in result:
        return f"Error starting brain: {result['error']}"

    if result.get("success"):
        return f"🧠 Brain STARTED: {result.get('message', 'Running')}"
    else:
        return f"Failed to start: {result.get('message', 'Unknown error')}"


async def execute_brain_stop(args: Dict[str, Any]) -> str:
    """Stop the brain."""
    result = await _api_call("POST", "/stop")

    if "error" in result:
        return f"Error stopping brain: {result['error']}"

    return f"🧠 Brain STOPPED: {result.get('message', 'Stopped')}"


async def execute_brain_pause(args: Dict[str, Any]) -> str:
    """Pause the brain."""
    result = await _api_call("POST", "/pause")

    if "error" in result:
        return f"Error pausing brain: {result['error']}"

    return f"🧠 Brain PAUSED: {result.get('message', 'Paused')}"


async def execute_brain_resume(args: Dict[str, Any]) -> str:
    """Resume the brain."""
    result = await _api_call("POST", "/resume")

    if "error" in result:
        return f"Error resuming brain: {result['error']}"

    return f"🧠 Brain RESUMED: {result.get('message', 'Resumed')}"


async def execute_brain_submit_intention(args: Dict[str, Any]) -> str:
    """Submit a new intention."""
    data = {
        "goal": args.get("goal"),
        "priority": args.get("priority", 5),
        "triggers": args.get("triggers", []),
        "metadata": args.get("metadata", {}),
    }

    if not data["goal"]:
        return "Error: 'goal' is required"

    result = await _api_call("POST", "/intention", data)

    if "error" in result:
        return f"Error submitting intention: {result['error']}"

    if result.get("success"):
        return (
            f"🧠 Intention SUBMITTED\n"
            f"Goal: {data['goal']}\n"
            f"Priority: {data['priority']}\n"
            f"ID: {result.get('intention_id', 'unknown')}"
        )
    else:
        return f"Failed: {result.get('message', 'Unknown error')}"


async def execute_brain_get_approvals(args: Dict[str, Any]) -> str:
    """Get pending approvals."""
    result = await _api_call("GET", "/approvals")

    if "error" in result:
        return f"Error: {result['error']}"

    count = result.get("count", 0)
    if count == 0:
        return "🧠 No pending approvals"

    lines = [f"🧠 PENDING APPROVALS ({count}):\n"]
    for item in result.get("pending", []):
        lines.append(
            f"[{item['index']}] {item['action_type']}: {item['action_description']}\n"
            f"    Intention: {item['intention_goal']}\n"
            f"    Queued: {item['queued_at']}\n"
        )

    return "\n".join(lines)


async def execute_brain_approve(args: Dict[str, Any]) -> str:
    """Approve a pending action."""
    data = {"index": args.get("index", 0)}
    result = await _api_call("POST", "/approve", data)

    if "error" in result:
        return f"Error approving: {result['error']}"

    if result.get("success"):
        return (
            f"🧠 Action APPROVED and EXECUTED\n"
            f"Type: {result.get('action_type', 'unknown')}\n"
            f"Duration: {result.get('duration_ms', 0):.1f}ms\n"
            f"Output: {result.get('output', 'None')[:200]}"
        )
    else:
        return f"Action FAILED: {result.get('error', 'Unknown error')}"


async def execute_brain_reject(args: Dict[str, Any]) -> str:
    """Reject a pending action."""
    index = args.get("index", 0)
    result = await _api_call("DELETE", f"/approvals/{index}")

    if "error" in result:
        return f"Error rejecting: {result['error']}"

    return f"🧠 Action REJECTED: {result.get('message', 'Removed from queue')}"


async def execute_brain_history(args: Dict[str, Any]) -> str:
    """Get thought history."""
    limit = args.get("limit", 20)
    result = await _api_call("GET", f"/history?limit={limit}")

    if "error" in result:
        return f"Error: {result['error']}"

    count = result.get("count", 0)
    if count == 0:
        return "🧠 No thoughts recorded yet"

    lines = [f"🧠 THOUGHT HISTORY ({count} total, showing {len(result.get('thoughts', []))}):\n"]
    for thought in result.get("thoughts", []):
        success = "✓" if thought.get("action_success") else "✗" if thought.get("action_success") is False else "?"
        lines.append(
            f"[{thought['timestamp']}] {success}\n"
            f"  Goal: {thought['intention_goal']}\n"
            f"  Trigger: {thought.get('trigger_matched', 'None')}\n"
            f"  Action: {thought.get('action_planned', 'None')}\n"
        )

    return "\n".join(lines)


async def execute_brain_safety(args: Dict[str, Any]) -> str:
    """Get or set safety level."""
    level = args.get("level")

    if level:
        # Set safety level
        result = await _api_call("POST", "/safety", {"level": level})
    else:
        # Get safety stats
        result = await _api_call("GET", "/safety")

    if "error" in result:
        return f"Error: {result['error']}"

    return (
        f"🧠 SAFETY RAILS\n"
        f"Level: {result.get('level', 'unknown')}\n"
        f"Actions This Window: {result.get('actions_this_window', 0)}\n"
        f"Rate Limit: {result.get('rate_limit', 50)}/5min\n"
        f"Blocked: {result.get('blocked_count', 0)}\n"
        f"Approvals Required: {result.get('approval_required_count', 0)}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#                              TOOL DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

BRAIN_TOOL_HANDLERS = {
    "brain_status": execute_brain_status,
    "brain_start": execute_brain_start,
    "brain_stop": execute_brain_stop,
    "brain_pause": execute_brain_pause,
    "brain_resume": execute_brain_resume,
    "brain_submit_intention": execute_brain_submit_intention,
    "brain_get_approvals": execute_brain_get_approvals,
    "brain_approve": execute_brain_approve,
    "brain_reject": execute_brain_reject,
    "brain_history": execute_brain_history,
    "brain_safety": execute_brain_safety,
}


async def execute_brain_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """Execute a brain tool by name."""
    handler = BRAIN_TOOL_HANDLERS.get(tool_name)
    if handler:
        return await handler(args)
    return f"Unknown brain tool: {tool_name}"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#                   Autonomous Brain MCP Tools - Self Control
#                   π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
