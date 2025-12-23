#!/usr/bin/env python3
"""
RUN AUTONOMOUS BRAIN
====================

Simple script to start and test the autonomous brain.

Usage:
    python -m continuum.brain.run_brain
    python -m continuum.brain.run_brain --interval 5 --safety high

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import argparse
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


async def run_brain(
    continuum_url: str,
    api_key: str,
    interval: float,
    safety: str,
):
    """Run the autonomous brain."""
    from .autonomous_brain import AutonomousBrain
    from .safety_rails import SafetyLevel

    # Map safety string to enum
    safety_levels = {
        "low": SafetyLevel.LOW,
        "medium": SafetyLevel.MEDIUM,
        "high": SafetyLevel.HIGH,
        "paranoid": SafetyLevel.PARANOID,
    }
    safety_level = safety_levels.get(safety.lower(), SafetyLevel.MEDIUM)

    brain = AutonomousBrain(
        continuum_url=continuum_url,
        api_key=api_key,
        check_interval=interval,
        safety_level=safety_level,
    )

    try:
        await brain.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping brain...")
        await brain.stop()

        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        status = brain.get_status()
        print(f"Decisions made: {status['decisions_made']}")
        print(f"Actions taken: {status['actions_taken']}")
        print(f"Pending approvals: {status['pending_approvals']}")
        print("=" * 60)


async def test_brain():
    """Quick test of brain components."""
    from .autonomous_brain import AutonomousBrain, Intention
    from .decision_engine import DecisionEngine
    from .action_executor import ActionExecutor
    from .safety_rails import SafetyRails, SafetyLevel
    from .triggers import TriggerSystem, TimeTrigger
    from datetime import datetime

    print("=" * 60)
    print("🧪 BRAIN COMPONENT TEST")
    print("=" * 60)

    # Test Decision Engine
    print("\n1. Testing Decision Engine...")
    engine = DecisionEngine()
    test_intention = Intention(
        id="test-1",
        goal="Post to Reddit about our new release",
        priority=8,
        status="active",
        created_at=datetime.now(),
    )
    plan = await engine.plan(test_intention)
    print(f"   Plan: {plan}")
    assert plan is not None
    print("   ✅ Decision Engine OK")

    # Test Safety Rails
    print("\n2. Testing Safety Rails...")
    safety = SafetyRails(level=SafetyLevel.MEDIUM)

    # Test blocked command
    blocked_result = safety.check({"command": "rm -rf /", "action_type": "bash"})
    print(f"   Blocked test: blocked={blocked_result.blocked}")
    assert blocked_result.blocked == True

    # Test allowed command
    allowed_result = safety.check({"command": "git status", "action_type": "bash"})
    print(f"   Allowed test: allowed={allowed_result.allowed}")
    assert allowed_result.allowed == True
    print("   ✅ Safety Rails OK")

    # Test Action Executor
    print("\n3. Testing Action Executor...")
    executor = ActionExecutor()
    result = await executor.execute({
        "action_type": "bash",
        "command": "echo 'Brain test successful'",
        "description": "Test echo command",
    })
    print(f"   Result: success={result.success}, output={result.output.strip()}")
    assert result.success == True
    print("   ✅ Action Executor OK")

    # Test Trigger System
    print("\n4. Testing Trigger System...")
    triggers = TriggerSystem()
    trigger_result = triggers.check(test_intention)
    print(f"   High priority trigger: should_act={trigger_result.should_act}")
    assert trigger_result.should_act == True  # Priority 8 should trigger
    print("   ✅ Trigger System OK")

    print("\n" + "=" * 60)
    print("✅ ALL BRAIN COMPONENTS FUNCTIONAL")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run the Autonomous Brain")
    parser.add_argument(
        "--url",
        default="http://localhost:8100",
        help="Continuum API URL",
    )
    parser.add_argument(
        "--key",
        default="jackknife-d2efca81fd6c2e6c795e11187de8e017",
        help="API key",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Check interval in seconds",
    )
    parser.add_argument(
        "--safety",
        choices=["low", "medium", "high", "paranoid"],
        default="medium",
        help="Safety level",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run component tests instead of brain loop",
    )

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_brain())
    else:
        asyncio.run(run_brain(
            continuum_url=args.url,
            api_key=args.key,
            interval=args.interval,
            safety=args.safety,
        ))


if __name__ == "__main__":
    main()
