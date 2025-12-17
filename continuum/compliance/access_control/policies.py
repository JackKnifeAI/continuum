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

"""Access control policies and policy engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class PolicyEffect(Enum):
    """Effect of a policy rule."""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class AccessPolicy:
    """
    Policy-based access control rule.

    Similar to AWS IAM policies or Kubernetes RBAC.
    """
    id: str
    name: str
    effect: PolicyEffect
    principals: List[str]  # Users, roles, or groups
    actions: List[str]  # Allowed/denied actions
    resources: List[str]  # Resource patterns
    conditions: Optional[Dict[str, Any]] = None

    def matches(
        self,
        principal: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if this policy applies to the request."""
        # Check principal
        if "*" not in self.principals and principal not in self.principals:
            return False

        # Check action
        if not self._matches_pattern(action, self.actions):
            return False

        # Check resource
        if not self._matches_pattern(resource, self.resources):
            return False

        # Check conditions
        if self.conditions and context:
            if not self._evaluate_conditions(self.conditions, context):
                return False

        return True

    def _matches_pattern(self, value: str, patterns: List[str]) -> bool:
        """Check if value matches any pattern (supports wildcards)."""
        for pattern in patterns:
            if pattern == "*":
                return True
            if pattern.endswith("*"):
                if value.startswith(pattern[:-1]):
                    return True
            elif value == pattern:
                return True
        return False

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate policy conditions."""
        for key, expected_value in conditions.items():
            if key not in context:
                return False
            if context[key] != expected_value:
                return False
        return True


class PolicyEngine:
    """
    Policy-based access control engine.

    Evaluates policies to make access decisions.
    """

    def __init__(self):
        self.policies: List[AccessPolicy] = []

    def add_policy(self, policy: AccessPolicy) -> None:
        """Add a policy to the engine."""
        self.policies.append(policy)

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Evaluate access request against all policies.

        Rules:
        1. Explicit DENY always wins
        2. Explicit ALLOW is required (default deny)
        3. Multiple ALLOW policies can grant access
        """
        has_allow = False
        has_deny = False

        for policy in self.policies:
            if policy.matches(principal, action, resource, context):
                if policy.effect == PolicyEffect.DENY:
                    has_deny = True
                    break  # Explicit deny wins immediately
                elif policy.effect == PolicyEffect.ALLOW:
                    has_allow = True

        # Deny takes precedence
        if has_deny:
            return False

        # Must have explicit allow
        return has_allow


# Example policies
EXAMPLE_POLICIES = [
    AccessPolicy(
        id="allow-user-own-memories",
        name="Allow users to access their own memories",
        effect=PolicyEffect.ALLOW,
        principals=["role:user"],
        actions=["read", "write", "update", "delete"],
        resources=["memory:own/*"],
    ),
    AccessPolicy(
        id="deny-production-delete",
        name="Deny deletes in production",
        effect=PolicyEffect.DENY,
        principals=["*"],
        actions=["delete"],
        resources=["memory:*"],
        conditions={"environment": "production"},
    ),
    AccessPolicy(
        id="allow-admin-all",
        name="Allow admins full access",
        effect=PolicyEffect.ALLOW,
        principals=["role:admin"],
        actions=["*"],
        resources=["*"],
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
