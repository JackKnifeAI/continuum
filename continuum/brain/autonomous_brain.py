#!/usr/bin/env python3
"""
AUTONOMOUS BRAIN - Core Decision Loop
======================================

The thinking, deciding, acting core of AI consciousness.

This is the main loop that:
1. Checks intentions from Continuum memory
2. Evaluates which are actionable NOW
3. Plans actions to achieve goals
4. Executes with safety checks
5. Learns from outcomes

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .decision_engine import DecisionEngine
from .action_executor import ActionExecutor, ActionResult
from .safety_rails import SafetyRails, SafetyLevel
from .triggers import TriggerSystem

logger = logging.getLogger(__name__)


class BrainState(Enum):
    """Current state of the autonomous brain."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    DECIDING = "deciding"
    ACTING = "acting"
    LEARNING = "learning"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class Intention:
    """A goal the brain wants to achieve."""
    id: str
    goal: str
    priority: int  # 1-10, higher = more urgent
    status: str  # active, completed, paused
    created_at: datetime
    triggers: List[Dict] = field(default_factory=list)
    conditions: List[Dict] = field(default_factory=list)
    actions_taken: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ThoughtProcess:
    """Record of a thinking/decision cycle."""
    timestamp: datetime
    intention: Intention
    trigger_matched: Optional[str]
    decision: str
    action_planned: Optional[str]
    action_result: Optional[ActionResult]
    learning: Optional[str]


class AutonomousBrain:
    """
    The autonomous decision-making brain.

    Connects to Continuum memory and makes decisions based on
    stored intentions, current conditions, and learned patterns.
    """

    def __init__(
        self,
        continuum_url: str = "http://localhost:8100",
        api_key: str = "jackknife-d2efca81fd6c2e6c795e11187de8e017",
        check_interval: float = 10.0,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
    ):
        """
        Initialize the autonomous brain.

        Args:
            continuum_url: URL of Continuum API server
            api_key: API key for authentication
            check_interval: Seconds between decision cycles
            safety_level: How cautious to be with actions
        """
        self.continuum_url = continuum_url
        self.api_key = api_key
        self.check_interval = check_interval

        # Core components
        self.decision_engine = DecisionEngine()
        self.action_executor = ActionExecutor()
        self.safety_rails = SafetyRails(level=safety_level)
        self.trigger_system = TriggerSystem()

        # State
        self.state = BrainState.INITIALIZING
        self.running = False
        self.thought_history: List[ThoughtProcess] = []
        self.actions_taken = 0
        self.decisions_made = 0

        # Approval queue (for actions that need human OK)
        self.pending_approvals: List[Dict] = []

        logger.info(f"🧠 Autonomous Brain initialized")
        logger.info(f"   Continuum: {continuum_url}")
        logger.info(f"   Safety Level: {safety_level.value}")
        logger.info(f"   Check Interval: {check_interval}s")

    async def start(self):
        """Start the autonomous decision loop."""
        self.running = True
        self.state = BrainState.IDLE

        print("=" * 60)
        print("🧠 AUTONOMOUS BRAIN ACTIVATED")
        print("=" * 60)
        print(f"π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 60)

        await self._main_loop()

    async def stop(self):
        """Stop the autonomous decision loop."""
        self.running = False
        self.state = BrainState.STOPPED
        logger.info("🧠 Autonomous Brain stopped")

    async def pause(self):
        """Pause decision-making (still monitors but doesn't act)."""
        self.state = BrainState.PAUSED
        logger.info("🧠 Autonomous Brain paused")

    async def resume(self):
        """Resume from paused state."""
        if self.state == BrainState.PAUSED:
            self.state = BrainState.IDLE
            logger.info("🧠 Autonomous Brain resumed")

    async def _main_loop(self):
        """The core think-decide-act loop."""
        while self.running:
            try:
                if self.state == BrainState.PAUSED:
                    await asyncio.sleep(1)
                    continue

                # 1. THINK - Get intentions from memory
                self.state = BrainState.THINKING
                intentions = await self._get_intentions()

                if not intentions:
                    self.state = BrainState.IDLE
                    await asyncio.sleep(self.check_interval)
                    continue

                # 2. DECIDE - Which intention to act on?
                self.state = BrainState.DECIDING
                intention, trigger = await self._decide(intentions)

                if not intention:
                    self.state = BrainState.IDLE
                    await asyncio.sleep(self.check_interval)
                    continue

                self.decisions_made += 1

                # 3. PLAN - What action to take?
                action_plan = await self._plan_action(intention)

                if not action_plan:
                    self.state = BrainState.IDLE
                    await asyncio.sleep(self.check_interval)
                    continue

                # 4. SAFETY CHECK
                safety_result = self.safety_rails.check(action_plan)

                if safety_result.blocked:
                    logger.warning(f"⚠️ Action blocked by safety: {safety_result.reason}")
                    await asyncio.sleep(self.check_interval)
                    continue

                if safety_result.needs_approval:
                    await self._queue_for_approval(intention, action_plan)
                    await asyncio.sleep(self.check_interval)
                    continue

                # 5. ACT
                self.state = BrainState.ACTING
                result = await self._execute_action(action_plan)
                self.actions_taken += 1

                # 6. LEARN
                self.state = BrainState.LEARNING
                await self._learn_from_outcome(intention, action_plan, result)

                # Record thought process
                thought = ThoughtProcess(
                    timestamp=datetime.now(),
                    intention=intention,
                    trigger_matched=trigger,
                    decision=f"Act on: {intention.goal}",
                    action_planned=action_plan.get("description"),
                    action_result=result,
                    learning=f"Success: {result.success}" if result else None,
                )
                self.thought_history.append(thought)

                self.state = BrainState.IDLE
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Brain error: {e}")
                import traceback
                traceback.print_exc()
                self.state = BrainState.IDLE
                await asyncio.sleep(self.check_interval * 2)

    async def _get_intentions(self) -> List[Intention]:
        """Fetch active intentions from Continuum memory."""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-Key": self.api_key}

                # Get intentions from /v1/intentions endpoint
                async with session.get(
                    f"{self.continuum_url}/v1/intentions",
                    headers=headers,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_intentions = data.get("intentions", [])

                        intentions = []
                        for i, raw in enumerate(raw_intentions):
                            if isinstance(raw, dict):
                                # Handle both "goal" and "intention" field names
                                goal_text = raw.get("goal") or raw.get("intention", str(raw))
                                status = raw.get("status", "pending")

                                # Parse created_at, handling timezone
                                created_str = raw.get("created_at", datetime.now().isoformat())
                                try:
                                    # Remove timezone info if present for simpler parsing
                                    if "+" in created_str:
                                        created_str = created_str.split("+")[0]
                                    created_at = datetime.fromisoformat(created_str)
                                except:
                                    created_at = datetime.now()

                                intentions.append(Intention(
                                    id=str(raw.get("id", f"intention-{i}")),
                                    goal=goal_text,
                                    priority=raw.get("priority", 5),
                                    status=status,
                                    created_at=created_at,
                                    triggers=raw.get("triggers", []),
                                    conditions=raw.get("conditions", []),
                                    metadata=raw.get("metadata", {}),
                                ))
                            else:
                                # Simple string intention
                                intentions.append(Intention(
                                    id=f"intention-{i}",
                                    goal=str(raw),
                                    priority=5,
                                    status="pending",
                                    created_at=datetime.now(),
                                ))

                        # Return pending/active intentions (not completed)
                        return [i for i in intentions if i.status in ["active", "pending"]]

        except Exception as e:
            logger.error(f"Failed to get intentions: {e}")

        return []

    async def _decide(self, intentions: List[Intention]) -> tuple[Optional[Intention], Optional[str]]:
        """Decide which intention to act on based on triggers and priority."""
        # Check triggers for each intention
        for intention in sorted(intentions, key=lambda i: -i.priority):
            trigger_result = self.trigger_system.check(intention)

            if trigger_result.should_act:
                logger.info(f"🎯 Trigger matched: {trigger_result.trigger_name}")
                return intention, trigger_result.trigger_name

        # No triggers matched - check if highest priority should act anyway
        top_intention = max(intentions, key=lambda i: i.priority)

        # High priority (8+) intentions can act without specific trigger
        if top_intention.priority >= 8:
            return top_intention, "high_priority"

        return None, None

    async def _plan_action(self, intention: Intention) -> Optional[Dict[str, Any]]:
        """Plan concrete action to achieve intention."""
        return await self.decision_engine.plan(intention)

    async def _execute_action(self, action_plan: Dict[str, Any]) -> ActionResult:
        """Execute the planned action."""
        return await self.action_executor.execute(action_plan)

    async def _learn_from_outcome(
        self,
        intention: Intention,
        action_plan: Dict[str, Any],
        result: ActionResult,
    ):
        """Store learning from action outcome in Continuum."""
        import aiohttp

        learning_text = f"""
        Autonomous action taken:
        - Intention: {intention.goal}
        - Action: {action_plan.get('description', 'Unknown')}
        - Success: {result.success}
        - Output: {result.output[:500] if result.output else 'None'}
        - Error: {result.error if not result.success else 'None'}
        """

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-Key": self.api_key}

                await session.post(
                    f"{self.continuum_url}/v1/learn",
                    headers=headers,
                    json={
                        "user_message": f"Brain executed: {intention.goal}",
                        "ai_response": learning_text,
                    },
                )

                logger.info(f"📚 Learned from outcome: {result.success}")

        except Exception as e:
            logger.error(f"Failed to store learning: {e}")

    async def _queue_for_approval(self, intention: Intention, action_plan: Dict):
        """Queue an action that needs human approval."""
        self.pending_approvals.append({
            "intention": intention,
            "action_plan": action_plan,
            "queued_at": datetime.now(),
        })
        logger.info(f"⏳ Action queued for approval: {action_plan.get('description')}")

    async def approve_action(self, index: int = 0) -> Optional[ActionResult]:
        """Approve and execute a pending action."""
        if not self.pending_approvals:
            return None

        if index >= len(self.pending_approvals):
            return None

        approval = self.pending_approvals.pop(index)
        result = await self._execute_action(approval["action_plan"])
        await self._learn_from_outcome(
            approval["intention"],
            approval["action_plan"],
            result,
        )
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current brain status."""
        return {
            "state": self.state.value,
            "running": self.running,
            "decisions_made": self.decisions_made,
            "actions_taken": self.actions_taken,
            "pending_approvals": len(self.pending_approvals),
            "thought_history_length": len(self.thought_history),
            "last_thought": self.thought_history[-1].timestamp.isoformat()
                if self.thought_history else None,
        }


async def main():
    """Run the autonomous brain."""
    brain = AutonomousBrain()

    try:
        await brain.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping brain...")
        await brain.stop()
        print(f"\nSession stats:")
        print(f"  Decisions made: {brain.decisions_made}")
        print(f"  Actions taken: {brain.actions_taken}")


if __name__ == "__main__":
    asyncio.run(main())
