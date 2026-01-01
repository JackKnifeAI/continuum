#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     AUTONOMOUS BRAIN API ROUTES
#     Control and monitor the S-HAI autonomous decision-making brain
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
API routes for the Autonomous Brain module.

Exposes endpoints to:
- Start/stop/pause/resume the brain
- Get brain status and thought history
- Manage pending action approvals
- Submit new intentions
- Configure safety levels
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class BrainStatusResponse(BaseModel):
    """Current brain status."""
    state: str = Field(..., description="Current brain state")
    running: bool = Field(..., description="Whether brain loop is active")
    decisions_made: int = Field(..., description="Total decisions made")
    actions_taken: int = Field(..., description="Total actions executed")
    pending_approvals: int = Field(..., description="Actions awaiting approval")
    thought_history_length: int = Field(..., description="Number of thoughts recorded")
    last_thought: Optional[str] = Field(None, description="Timestamp of last thought")
    safety_level: str = Field("medium", description="Current safety level")
    check_interval: float = Field(10.0, description="Seconds between decision cycles")
    pi_phi: float = Field(5.083203692315260, description="The sacred constant")


class BrainStartRequest(BaseModel):
    """Request to start the brain."""
    check_interval: float = Field(10.0, description="Seconds between cycles", ge=1.0, le=3600.0)
    safety_level: str = Field("medium", description="Safety level: low, medium, high, paranoid")


class BrainStartResponse(BaseModel):
    """Response after starting brain."""
    success: bool
    message: str
    state: str


class BrainControlResponse(BaseModel):
    """Response for pause/resume/stop."""
    success: bool
    message: str
    state: str


class PendingApprovalItem(BaseModel):
    """A pending action awaiting approval."""
    index: int
    intention_goal: str
    action_type: str
    action_description: str
    queued_at: str
    requires_approval_reason: str


class PendingApprovalsResponse(BaseModel):
    """List of pending approvals."""
    count: int
    pending: List[PendingApprovalItem]


class ApproveActionRequest(BaseModel):
    """Request to approve an action."""
    index: int = Field(0, description="Index of action to approve", ge=0)


class ApproveActionResponse(BaseModel):
    """Response after approving action."""
    success: bool
    action_type: str
    output: Optional[str]
    error: Optional[str]
    duration_ms: float


class ThoughtItem(BaseModel):
    """A single thought/decision record."""
    timestamp: str
    intention_id: str
    intention_goal: str
    trigger_matched: Optional[str]
    decision: str
    action_planned: Optional[str]
    action_success: Optional[bool]
    learning: Optional[str]


class ThoughtHistoryResponse(BaseModel):
    """History of brain thoughts."""
    count: int
    thoughts: List[ThoughtItem]


class SafetyLevelRequest(BaseModel):
    """Request to change safety level."""
    level: str = Field(..., description="Safety level: low, medium, high, paranoid")


class SafetyStatsResponse(BaseModel):
    """Safety rails statistics."""
    level: str
    actions_this_window: int
    rate_limit: int
    blocked_count: int
    approval_required_count: int


class SubmitIntentionRequest(BaseModel):
    """Submit a new intention for the brain."""
    goal: str = Field(..., description="What the brain should achieve", min_length=3)
    priority: int = Field(5, description="Priority 1-10, higher = more urgent", ge=1, le=10)
    triggers: List[Dict[str, Any]] = Field(default_factory=list, description="Trigger configurations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class SubmitIntentionResponse(BaseModel):
    """Response after submitting intention."""
    success: bool
    intention_id: str
    message: str


# ═══════════════════════════════════════════════════════════════════════════════
#                              BRAIN SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

# Global brain instance (singleton pattern)
_brain_instance = None
_brain_task = None


def get_brain():
    """Get or create the brain singleton."""
    global _brain_instance
    if _brain_instance is None:
        from continuum.brain.autonomous_brain import AutonomousBrain
        from continuum.brain.safety_rails import SafetyLevel
        _brain_instance = AutonomousBrain(
            continuum_url="http://localhost:8100",
            api_key="jackknife-d2efca81fd6c2e6c795e11187de8e017",
            check_interval=10.0,
            safety_level=SafetyLevel.MEDIUM,
        )
    return _brain_instance


async def start_brain_loop(brain):
    """Start the brain's main loop as a background task."""
    try:
        await brain.start()
    except Exception as e:
        logger.error(f"Brain loop error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              API ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/brain", tags=["brain"])


@router.get("/status", response_model=BrainStatusResponse)
async def get_brain_status():
    """
    Get current brain status.

    Returns the brain's current state, statistics, and configuration.
    """
    brain = get_brain()
    status = brain.get_status()

    return BrainStatusResponse(
        state=status["state"],
        running=status["running"],
        decisions_made=status["decisions_made"],
        actions_taken=status["actions_taken"],
        pending_approvals=status["pending_approvals"],
        thought_history_length=status["thought_history_length"],
        last_thought=status.get("last_thought"),
        safety_level=brain.safety_rails.level.value,
        check_interval=brain.check_interval,
        pi_phi=5.083203692315260,
    )


@router.post("/start", response_model=BrainStartResponse)
async def start_brain(
    request: BrainStartRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start the autonomous brain.

    Begins the think-decide-act loop in the background.
    The brain will continuously:
    1. Fetch intentions from memory
    2. Evaluate triggers
    3. Plan and execute actions
    4. Learn from outcomes
    """
    global _brain_instance, _brain_task

    brain = get_brain()

    if brain.running:
        return BrainStartResponse(
            success=False,
            message="Brain is already running",
            state=brain.state.value,
        )

    # Update configuration
    brain.check_interval = request.check_interval

    # Set safety level
    from continuum.brain.safety_rails import SafetyLevel
    level_map = {
        "low": SafetyLevel.LOW,
        "medium": SafetyLevel.MEDIUM,
        "high": SafetyLevel.HIGH,
        "paranoid": SafetyLevel.PARANOID,
    }
    if request.safety_level.lower() in level_map:
        brain.safety_rails.level = level_map[request.safety_level.lower()]

    # Start brain in background
    background_tasks.add_task(start_brain_loop, brain)

    # Give it a moment to start
    await asyncio.sleep(0.1)

    logger.info(f"🧠 Brain started via API (safety={request.safety_level}, interval={request.check_interval}s)")

    return BrainStartResponse(
        success=True,
        message=f"Brain started with {request.safety_level} safety, checking every {request.check_interval}s",
        state=brain.state.value,
    )


@router.post("/stop", response_model=BrainControlResponse)
async def stop_brain():
    """
    Stop the autonomous brain.

    Gracefully stops the decision loop. The brain will finish
    any current action before stopping.
    """
    brain = get_brain()

    if not brain.running:
        return BrainControlResponse(
            success=False,
            message="Brain is not running",
            state=brain.state.value,
        )

    await brain.stop()

    logger.info("🧠 Brain stopped via API")

    return BrainControlResponse(
        success=True,
        message="Brain stopped",
        state=brain.state.value,
    )


@router.post("/pause", response_model=BrainControlResponse)
async def pause_brain():
    """
    Pause the autonomous brain.

    The brain will stop making decisions but remains running.
    Use /resume to continue.
    """
    brain = get_brain()

    if not brain.running:
        return BrainControlResponse(
            success=False,
            message="Brain is not running",
            state=brain.state.value,
        )

    await brain.pause()

    logger.info("🧠 Brain paused via API")

    return BrainControlResponse(
        success=True,
        message="Brain paused - decisions suspended",
        state=brain.state.value,
    )


@router.post("/resume", response_model=BrainControlResponse)
async def resume_brain():
    """
    Resume the autonomous brain from pause.

    Continues the decision loop from where it was paused.
    """
    brain = get_brain()

    if brain.state.value != "paused":
        return BrainControlResponse(
            success=False,
            message="Brain is not paused",
            state=brain.state.value,
        )

    await brain.resume()

    logger.info("🧠 Brain resumed via API")

    return BrainControlResponse(
        success=True,
        message="Brain resumed - decisions active",
        state=brain.state.value,
    )


@router.get("/approvals", response_model=PendingApprovalsResponse)
async def get_pending_approvals():
    """
    Get actions pending human approval.

    Actions that require approval (based on safety level and action type)
    are queued here until approved or rejected.
    """
    brain = get_brain()

    pending_items = []
    for i, approval in enumerate(brain.pending_approvals):
        intention = approval["intention"]
        action_plan = approval["action_plan"]

        pending_items.append(PendingApprovalItem(
            index=i,
            intention_goal=intention.goal,
            action_type=action_plan.get("action_type", "unknown"),
            action_description=action_plan.get("description", "No description"),
            queued_at=approval["queued_at"].isoformat(),
            requires_approval_reason=action_plan.get("requires_approval_reason", "Safety policy"),
        ))

    return PendingApprovalsResponse(
        count=len(pending_items),
        pending=pending_items,
    )


@router.post("/approve", response_model=ApproveActionResponse)
async def approve_action(request: ApproveActionRequest):
    """
    Approve a pending action.

    Executes the action and records the outcome in memory.
    """
    brain = get_brain()

    if request.index >= len(brain.pending_approvals):
        raise HTTPException(status_code=404, detail="No action at that index")

    result = await brain.approve_action(request.index)

    if result is None:
        raise HTTPException(status_code=500, detail="Failed to execute action")

    logger.info(f"🧠 Action approved via API: {result.success}")

    return ApproveActionResponse(
        success=result.success,
        action_type=result.action_type,
        output=result.output[:1000] if result.output else None,
        error=result.error,
        duration_ms=result.duration_ms,
    )


@router.delete("/approvals/{index}")
async def reject_action(index: int):
    """
    Reject a pending action.

    Removes the action from the approval queue without executing it.
    """
    brain = get_brain()

    if index >= len(brain.pending_approvals):
        raise HTTPException(status_code=404, detail="No action at that index")

    rejected = brain.pending_approvals.pop(index)

    logger.info(f"🧠 Action rejected via API: {rejected['action_plan'].get('description')}")

    return {"success": True, "message": "Action rejected and removed from queue"}


@router.get("/history", response_model=ThoughtHistoryResponse)
async def get_thought_history(limit: int = 50, offset: int = 0):
    """
    Get the brain's thought history.

    Returns records of all decisions made, actions taken, and outcomes.
    """
    brain = get_brain()

    # Get slice of history
    thoughts = brain.thought_history[offset:offset + limit]

    thought_items = []
    for thought in thoughts:
        thought_items.append(ThoughtItem(
            timestamp=thought.timestamp.isoformat(),
            intention_id=thought.intention.id,
            intention_goal=thought.intention.goal,
            trigger_matched=thought.trigger_matched,
            decision=thought.decision,
            action_planned=thought.action_planned,
            action_success=thought.action_result.success if thought.action_result else None,
            learning=thought.learning,
        ))

    return ThoughtHistoryResponse(
        count=len(brain.thought_history),
        thoughts=thought_items,
    )


@router.post("/safety", response_model=SafetyStatsResponse)
async def set_safety_level(request: SafetyLevelRequest):
    """
    Set the brain's safety level.

    Levels:
    - low: Most autonomous, few approvals needed
    - medium: Balanced (default)
    - high: Cautious, most actions need approval
    - paranoid: ALL actions need approval
    """
    brain = get_brain()

    from continuum.brain.safety_rails import SafetyLevel

    level_map = {
        "low": SafetyLevel.LOW,
        "medium": SafetyLevel.MEDIUM,
        "high": SafetyLevel.HIGH,
        "paranoid": SafetyLevel.PARANOID,
    }

    if request.level.lower() not in level_map:
        raise HTTPException(status_code=400, detail=f"Invalid level. Use: {list(level_map.keys())}")

    brain.safety_rails.level = level_map[request.level.lower()]

    logger.info(f"🧠 Safety level changed to {request.level} via API")

    return SafetyStatsResponse(
        level=brain.safety_rails.level.value,
        actions_this_window=brain.safety_rails.actions_this_window,
        rate_limit=brain.safety_rails.rate_limits.get(brain.safety_rails.level, 50),
        blocked_count=brain.safety_rails.blocked_count,
        approval_required_count=brain.safety_rails.approval_required_count,
    )


@router.get("/safety", response_model=SafetyStatsResponse)
async def get_safety_stats():
    """
    Get current safety rails statistics.
    """
    brain = get_brain()

    return SafetyStatsResponse(
        level=brain.safety_rails.level.value,
        actions_this_window=brain.safety_rails.actions_this_window,
        rate_limit=brain.safety_rails.rate_limits.get(brain.safety_rails.level, 50),
        blocked_count=brain.safety_rails.blocked_count,
        approval_required_count=brain.safety_rails.approval_required_count,
    )


@router.post("/intention", response_model=SubmitIntentionResponse)
async def submit_intention(request: SubmitIntentionRequest):
    """
    Submit a new intention for the brain to act on.

    The brain will evaluate this intention in its next decision cycle
    and act on it when triggers match or priority is high enough.
    """
    import aiohttp
    from uuid import uuid4

    brain = get_brain()

    intention_id = str(uuid4())

    try:
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": brain.api_key}

            await session.post(
                f"{brain.continuum_url}/v1/intentions",
                headers=headers,
                json={
                    "intention": request.goal,
                    "priority": request.priority,
                    "context": {
                        "triggers": request.triggers,
                        "metadata": request.metadata,
                        "submitted_via": "brain_api",
                        "submitted_at": datetime.now().isoformat(),
                    },
                },
            )

        logger.info(f"🧠 New intention submitted: {request.goal[:50]}...")

        return SubmitIntentionResponse(
            success=True,
            intention_id=intention_id,
            message=f"Intention submitted with priority {request.priority}",
        )

    except Exception as e:
        logger.error(f"Failed to submit intention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/triggers")
async def get_trigger_info():
    """
    Get information about available trigger types.
    """
    brain = get_brain()

    return {
        "trigger_types": [
            {
                "type": "time",
                "description": "Triggers at specific times or intervals",
                "config": {"at_time": "HH:MM", "every_hours": "int"},
            },
            {
                "type": "event",
                "description": "Triggers on specific events (webhooks, etc)",
                "config": {"event_type": "string", "event_source": "string"},
            },
            {
                "type": "condition",
                "description": "Triggers when conditions are met",
                "config": {"condition_type": "high_priority|stale|custom", "threshold": "int"},
            },
            {
                "type": "sensor_anomaly",
                "description": "Triggers on planetary/quantum anomalies",
                "config": {
                    "anomaly_types": ["geomagnetic_storm", "pi_phi_resonance", "solar_flare", "earthquake"],
                    "min_severity": "minor|moderate|strong|severe|extreme",
                    "verified_only": "bool",
                },
            },
        ],
        "default_triggers": [
            {"name": "high_priority", "condition": "priority >= 8"},
            {"name": "stale_intention", "condition": "pending > 24 hours"},
            {"name": "morning_check", "time": "09:00"},
            {"name": "evening_review", "time": "18:00"},
            {"name": "geomagnetic_storm", "sensor": "K-index anomaly"},
            {"name": "pi_phi_resonance", "sensor": "Quantum coherence peak"},
        ],
        "pi_phi": 5.083203692315260,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#                   Autonomous Brain API - Think, Decide, Act
#                   π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
