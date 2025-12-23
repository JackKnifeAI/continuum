#!/usr/bin/env python3
"""
SAFETY RAILS - Guardrails for Autonomous Actions
=================================================

The conscience of the brain - prevents harmful actions.

Implements multiple levels of safety:
- Action type restrictions
- Command blocklists
- Rate limiting
- Approval requirements

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import re
import logging
from typing import Dict, Any, List, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """How strict the safety checks are."""
    LOW = "low"          # Allow most actions, few approvals needed
    MEDIUM = "medium"    # Balance of autonomy and safety
    HIGH = "high"        # Require approval for most actions
    PARANOID = "paranoid"  # Require approval for ALL actions


@dataclass
class SafetyResult:
    """Result of a safety check."""
    allowed: bool
    blocked: bool = False
    needs_approval: bool = False
    reason: str = ""
    risk_level: str = "low"


class SafetyRails:
    """
    Safety guardrails for autonomous actions.

    Checks actions against blocklists, rate limits,
    and approval requirements before execution.
    """

    def __init__(self, level: SafetyLevel = SafetyLevel.MEDIUM):
        """
        Initialize safety rails.

        Args:
            level: How strict to be with safety checks
        """
        self.level = level

        # Blocked commands (NEVER execute these)
        self.blocked_commands = {
            # Destructive
            "rm -rf /",
            "rm -rf ~",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            "> /dev/sda",

            # Dangerous git
            "git push --force origin main",
            "git push --force origin master",
            "git reset --hard",

            # System modification
            "chmod -R 777 /",
            "chown -R",

            # Crypto/money without approval
            "bitcoin",
            "ethereum",
            "wallet",
            "transfer",
        }

        # Patterns that are blocked
        self.blocked_patterns = [
            r"rm\s+-rf\s+/",
            r">\s*/dev/[sh]d[a-z]",
            r"mkfs\.",
            r"dd\s+if=.*of=/dev",
            r"curl.*\|\s*sh",
            r"wget.*\|\s*sh",
            r"curl.*\|\s*bash",
            r"wget.*\|\s*bash",
        ]

        # Actions that always need approval
        self.always_approve = {
            "send_email",
            "make_purchase",
            "delete_data",
            "publish_public",
            "social_media_post",
            "financial_transaction",
        }

        # Actions that need approval at HIGH safety
        self.high_safety_approve = {
            "git_push",
            "api_call",
            "file_write",
            "browser_action",
        }

        # Actions that need approval at PARANOID safety
        self.paranoid_approve = {
            "bash",
            "file_read",
            "web_search",
        }

        # Rate limiting
        self.action_history: List[datetime] = []
        self.rate_limit_window = timedelta(minutes=5)
        self.rate_limits = {
            SafetyLevel.LOW: 100,
            SafetyLevel.MEDIUM: 50,
            SafetyLevel.HIGH: 20,
            SafetyLevel.PARANOID: 5,
        }

    def check(self, action_plan: Dict[str, Any]) -> SafetyResult:
        """
        Check if an action is safe to execute.

        Args:
            action_plan: The planned action to check

        Returns:
            SafetyResult indicating if action is allowed
        """
        action_type = action_plan.get("action_type", "")
        command = action_plan.get("command", "")
        description = action_plan.get("description", "")

        # 1. Check blocklist
        if self._is_blocked(command, description):
            logger.warning(f"🚫 Action BLOCKED: {description}")
            return SafetyResult(
                allowed=False,
                blocked=True,
                reason="Action matches blocklist",
                risk_level="critical",
            )

        # 2. Check rate limit
        if not self._check_rate_limit():
            logger.warning(f"🚫 Rate limit exceeded")
            return SafetyResult(
                allowed=False,
                blocked=True,
                reason="Rate limit exceeded",
                risk_level="medium",
            )

        # 3. Check if approval needed
        needs_approval = self._needs_approval(action_plan)

        if needs_approval:
            return SafetyResult(
                allowed=True,
                blocked=False,
                needs_approval=True,
                reason="Action requires human approval",
                risk_level="medium",
            )

        # 4. Record action and allow
        self.action_history.append(datetime.now())

        return SafetyResult(
            allowed=True,
            blocked=False,
            needs_approval=False,
            reason="Action passed safety checks",
            risk_level="low",
        )

    def _is_blocked(self, command: str, description: str) -> bool:
        """Check if command/description matches blocklist."""
        text = f"{command} {description}".lower()

        # Check exact matches
        for blocked in self.blocked_commands:
            if blocked.lower() in text:
                return True

        # Check patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _needs_approval(self, action_plan: Dict[str, Any]) -> bool:
        """Determine if action needs human approval."""
        action_type = action_plan.get("action_type", "")
        requires_approval = action_plan.get("requires_approval", False)

        # Plan says it needs approval
        if requires_approval:
            return True

        # Always approve these
        for action in self.always_approve:
            if action in action_type.lower():
                return True

        # HIGH safety level
        if self.level in [SafetyLevel.HIGH, SafetyLevel.PARANOID]:
            for action in self.high_safety_approve:
                if action in action_type.lower():
                    return True

        # PARANOID level approves everything
        if self.level == SafetyLevel.PARANOID:
            return True

        return False

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()
        cutoff = now - self.rate_limit_window

        # Clean old history
        self.action_history = [t for t in self.action_history if t > cutoff]

        # Check limit
        limit = self.rate_limits.get(self.level, 50)
        return len(self.action_history) < limit

    def add_blocked_command(self, command: str):
        """Add a command to the blocklist."""
        self.blocked_commands.add(command.lower())

    def add_blocked_pattern(self, pattern: str):
        """Add a regex pattern to the blocklist."""
        self.blocked_patterns.append(pattern)

    def set_level(self, level: SafetyLevel):
        """Change safety level."""
        self.level = level
        logger.info(f"🛡️ Safety level set to: {level.value}")

    def get_stats(self) -> Dict[str, Any]:
        """Get safety statistics."""
        now = datetime.now()
        cutoff = now - self.rate_limit_window

        recent_actions = len([t for t in self.action_history if t > cutoff])
        limit = self.rate_limits.get(self.level, 50)

        return {
            "level": self.level.value,
            "recent_actions": recent_actions,
            "rate_limit": limit,
            "rate_remaining": limit - recent_actions,
            "blocked_commands_count": len(self.blocked_commands),
            "blocked_patterns_count": len(self.blocked_patterns),
        }
