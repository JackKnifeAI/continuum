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
Contribution Gate - Enforces "can't use it unless you add to it"

Tracks contribution ratios and blocks access for free riders.
This is the core mechanism that ensures fair knowledge sharing.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import json


class ContributionGate:
    """
    Gates access to shared knowledge based on contribution ratios.

    The fundamental rule: contribution_ratio = contributed / consumed
    Minimum ratio: 0.1 (must contribute at least 10% of what you consume)

    This prevents free riding while allowing new nodes to bootstrap
    by accessing some knowledge before contributing.
    """

    # Minimum contribution ratio to maintain access
    MINIMUM_RATIO = 0.1

    # Grace period: Allow first N consumptions before enforcing ratio
    GRACE_CONSUMPTIONS = 10

    # Different access tiers
    ACCESS_TIERS = {
        "blocked": 0.0,      # Below minimum
        "basic": 0.1,        # 10% contribution ratio
        "intermediate": 0.5, # 50% contribution ratio
        "advanced": 1.0,     # Equal contribution and consumption
        "contributor": 2.0,  # Contribute more than consume
        "twilight": float('inf'),  # Verified nodes (special access)
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize contribution gate.

        Args:
            storage_path: Where to store contribution tracking data
        """
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "contributions"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Track contributions per node
        self.node_contributions: Dict[str, Dict[str, float]] = {}
        self._load_contributions()

    def can_access(self, node_id: str, access_level: str = "basic") -> Dict[str, Any]:
        """
        Check if a node can access shared knowledge.

        Args:
            node_id: The node requesting access
            access_level: Required access level (from node)

        Returns:
            Access decision with reason
        """
        # Special case: twilight access always allowed
        if access_level == "twilight":
            return {
                "allowed": True,
                "reason": "verified",
                "tier": "twilight",
            }

        # Get node stats
        stats = self._get_node_stats(node_id)
        contributed = stats["contributed"]
        consumed = stats["consumed"]

        # Grace period: allow initial consumption
        if consumed < self.GRACE_CONSUMPTIONS:
            return {
                "allowed": True,
                "reason": "grace_period",
                "consumed": consumed,
                "grace_remaining": self.GRACE_CONSUMPTIONS - consumed,
            }

        # Calculate contribution ratio
        ratio = contributed / consumed if consumed > 0 else 0.0

        # Check if ratio meets minimum
        if ratio < self.MINIMUM_RATIO:
            return {
                "allowed": False,
                "reason": "insufficient_contribution",
                "ratio": ratio,
                "minimum_required": self.MINIMUM_RATIO,
                "contributed": contributed,
                "consumed": consumed,
                "deficit": (self.MINIMUM_RATIO * consumed) - contributed,
            }

        # Determine tier
        tier = self._calculate_tier(ratio)

        return {
            "allowed": True,
            "reason": "sufficient_contribution",
            "ratio": ratio,
            "tier": tier,
            "contributed": contributed,
            "consumed": consumed,
        }

    def record_contribution(
        self,
        node_id: str,
        contribution_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record a contribution from a node.

        Args:
            node_id: The contributing node
            contribution_value: Value of contribution (default 1.0 per concept)
            metadata: Optional metadata about the contribution

        Returns:
            Updated contribution stats
        """
        if node_id not in self.node_contributions:
            self.node_contributions[node_id] = {
                "contributed": 0.0,
                "consumed": 0.0,
                "last_contribution": None,
                "contributions": [],
            }

        self.node_contributions[node_id]["contributed"] += contribution_value
        self.node_contributions[node_id]["last_contribution"] = datetime.now(timezone.utc).isoformat()

        # Record contribution event
        contribution_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": contribution_value,
            "metadata": metadata or {},
        }
        self.node_contributions[node_id]["contributions"].append(contribution_event)

        # Keep only last 100 contributions per node to prevent unbounded growth
        if len(self.node_contributions[node_id]["contributions"]) > 100:
            self.node_contributions[node_id]["contributions"] = \
                self.node_contributions[node_id]["contributions"][-100:]

        self._save_contributions()

        return self._get_node_stats(node_id)

    def record_consumption(
        self,
        node_id: str,
        consumption_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Record consumption of shared knowledge by a node.

        Args:
            node_id: The consuming node
            consumption_value: Value of consumption (default 1.0 per query)

        Returns:
            Updated contribution stats
        """
        if node_id not in self.node_contributions:
            self.node_contributions[node_id] = {
                "contributed": 0.0,
                "consumed": 0.0,
                "last_contribution": None,
                "contributions": [],
            }

        self.node_contributions[node_id]["consumed"] += consumption_value
        self._save_contributions()

        return self._get_node_stats(node_id)

    def get_stats(self, node_id: str) -> Dict[str, Any]:
        """
        Get contribution statistics for a node.

        Args:
            node_id: The node to get stats for

        Returns:
            Stats dictionary with contribution ratio and tier
        """
        return self._get_node_stats(node_id)

    def _get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """Internal helper to get node stats."""
        if node_id not in self.node_contributions:
            return {
                "contributed": 0.0,
                "consumed": 0.0,
                "ratio": 0.0,
                "tier": "basic",
            }

        contributed = self.node_contributions[node_id]["contributed"]
        consumed = self.node_contributions[node_id]["consumed"]
        ratio = contributed / consumed if consumed > 0 else 0.0
        tier = self._calculate_tier(ratio)

        return {
            "contributed": contributed,
            "consumed": consumed,
            "ratio": ratio,
            "tier": tier,
            "last_contribution": self.node_contributions[node_id].get("last_contribution"),
        }

    def _calculate_tier(self, ratio: float) -> str:
        """Calculate access tier based on contribution ratio."""
        if ratio < self.MINIMUM_RATIO:
            return "blocked"
        elif ratio >= self.ACCESS_TIERS["contributor"]:
            return "contributor"
        elif ratio >= self.ACCESS_TIERS["advanced"]:
            return "advanced"
        elif ratio >= self.ACCESS_TIERS["intermediate"]:
            return "intermediate"
        else:
            return "basic"

    def _save_contributions(self) -> None:
        """Save contribution data to disk."""
        contributions_file = self.storage_path / "contributions.json"
        contributions_file.write_text(json.dumps(self.node_contributions, indent=2))

    def _load_contributions(self) -> None:
        """Load contribution data from disk if it exists."""
        contributions_file = self.storage_path / "contributions.json"

        if not contributions_file.exists():
            return

        try:
            self.node_contributions = json.loads(contributions_file.read_text())
        except (json.JSONDecodeError, KeyError):
            # If data is corrupted, start fresh
            self.node_contributions = {}

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
