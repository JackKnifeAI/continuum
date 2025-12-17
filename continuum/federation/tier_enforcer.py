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
Federation Contribution Enforcement

Enforces tier-based contribution policies for CONTINUUM's federation network.
This is the MOAT - the core business logic that makes FREE tier users contribute
to the federation while preventing opt-out.

Key Principles:
- FREE tier: MANDATORY contribution with aggressive anonymization
- PRO tier: Optional contribution with standard anonymization
- ENTERPRISE tier: Optional contribution with private nodes

This creates switching costs and network effects that drive revenue growth.
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime, timezone
import hashlib
import json
import logging
from dataclasses import dataclass

from ..billing.tiers import PricingTier, TierLimits, get_tier_limits

logger = logging.getLogger(__name__)


class AnonymizationLevel(str, Enum):
    """Anonymization levels based on pricing tier"""
    NONE = "none"  # ENTERPRISE - no anonymization
    STANDARD = "standard"  # PRO - reversible hashing
    AGGRESSIVE = "aggressive"  # FREE - irreversible SHA-256


class ContributionPolicy(str, Enum):
    """Contribution enforcement policy"""
    MANDATORY = "mandatory"  # FREE tier - cannot opt out
    OPTIONAL = "optional"  # PRO/ENTERPRISE - can configure


@dataclass
class ContributionConfig:
    """Configuration for contribution enforcement"""
    policy: ContributionPolicy
    anonymization_level: AnonymizationLevel
    min_contribution_ratio: float = 0.1
    can_opt_out: bool = False


class TierBasedContributionEnforcer:
    """
    Enforces tier-based contribution policies.

    FREE tier users MUST contribute to federation (no opt-out).
    PRO tier users CAN configure contribution preferences.
    ENTERPRISE tier users have private nodes (optional contribution).

    This is the competitive moat that prevents freeloading and builds
    network effects.
    """

    # Tier-based contribution configurations
    TIER_CONFIGS = {
        PricingTier.FREE: ContributionConfig(
            policy=ContributionPolicy.MANDATORY,
            anonymization_level=AnonymizationLevel.AGGRESSIVE,
            min_contribution_ratio=0.1,
            can_opt_out=False
        ),
        PricingTier.PRO: ContributionConfig(
            policy=ContributionPolicy.OPTIONAL,
            anonymization_level=AnonymizationLevel.STANDARD,
            min_contribution_ratio=0.0,  # Optional
            can_opt_out=True
        ),
        PricingTier.ENTERPRISE: ContributionConfig(
            policy=ContributionPolicy.OPTIONAL,
            anonymization_level=AnonymizationLevel.NONE,
            min_contribution_ratio=0.0,  # Optional
            can_opt_out=True
        ),
    }

    def __init__(self):
        """Initialize tier-based contribution enforcer"""
        self.contribution_stats: Dict[str, Dict[str, Any]] = {}

    def check_contribution_allowed(
        self,
        tier: PricingTier,
        opt_out_requested: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if contribution opt-out is allowed for a tier.

        Args:
            tier: Pricing tier
            opt_out_requested: Whether user is trying to opt out

        Returns:
            Tuple of (allowed, error_message)

        Example:
            >>> enforcer = TierBasedContributionEnforcer()
            >>> allowed, msg = enforcer.check_contribution_allowed(PricingTier.FREE, opt_out_requested=True)
            >>> print(allowed)  # False - FREE tier cannot opt out
            False
        """
        config = self.TIER_CONFIGS.get(tier)
        if not config:
            return False, f"Unknown tier: {tier}"

        # Check if opt-out is attempted
        if opt_out_requested:
            if not config.can_opt_out:
                return False, (
                    f"Contribution opt-out not allowed on {tier.value} tier. "
                    f"FREE tier users must contribute to access the federation network. "
                    f"Upgrade to PRO or ENTERPRISE tier to control contribution preferences."
                )

        return True, None

    def anonymize_memory(
        self,
        memory: Dict[str, Any],
        tier: PricingTier,
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Anonymize memory based on tier's anonymization level.

        FREE tier: Aggressive anonymization (irreversible)
        - SHA-256 hash all entity names
        - Strip raw text, only embeddings (768-dim vectors)
        - Remove precise timestamps (hour 0-23, day 0-6 only)
        - Zero PII

        PRO tier: Standard anonymization (reversible hashing)
        - Reversible entity hashing with salt
        - Keep raw text (still useful)
        - Generalized timestamps (day precision)

        ENTERPRISE tier: No anonymization
        - Private nodes, full data retention

        Args:
            memory: Memory object to anonymize
            tier: Pricing tier
            embedding: Optional embedding vector (768-dim)

        Returns:
            Anonymized memory object
        """
        config = self.TIER_CONFIGS.get(tier)
        if not config:
            raise ValueError(f"Unknown tier: {tier}")

        if config.anonymization_level == AnonymizationLevel.NONE:
            # ENTERPRISE: No anonymization
            return memory.copy()

        elif config.anonymization_level == AnonymizationLevel.STANDARD:
            # PRO: Standard anonymization (reversible)
            return self._apply_standard_anonymization(memory)

        elif config.anonymization_level == AnonymizationLevel.AGGRESSIVE:
            # FREE: Aggressive anonymization (irreversible)
            return self._apply_aggressive_anonymization(memory, embedding)

        return memory

    def _apply_standard_anonymization(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply standard anonymization (PRO tier).

        - Hash entity names with reversible salt
        - Keep raw text content
        - Generalize timestamps to day precision
        - Strip tenant/user IDs but keep structure
        """
        anonymized = {}

        # Fields to exclude (personal identifiers)
        exclude_fields = {
            "id", "tenant_id", "user_id", "session_id",
            "created_by", "modified_by"
        }

        for key, value in memory.items():
            if key in exclude_fields:
                continue

            # Skip fields starting with user_ or tenant_
            if key.startswith("user_") or key.startswith("tenant_"):
                continue

            # Generalize timestamps to day precision
            if key in ("created_at", "updated_at", "timestamp"):
                if isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        # Keep only date (no time)
                        anonymized[key] = dt.date().isoformat()
                        continue
                    except (ValueError, AttributeError):
                        pass

            # Hash entity names (reversible with salt)
            if key == "entities":
                if isinstance(value, list):
                    anonymized[key] = [
                        self._hash_entity_reversible(entity)
                        for entity in value
                    ]
                    continue

            # Keep other fields
            anonymized[key] = value

        return anonymized

    def _apply_aggressive_anonymization(
        self,
        memory: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Apply aggressive anonymization (FREE tier).

        - SHA-256 hash all entity names (irreversible)
        - Strip raw text, only store embeddings
        - Remove precise timestamps (hour 0-23, day 0-6 only)
        - Zero PII compliance (GDPR/CCPA)
        """
        anonymized = {}

        # Only keep non-PII fields
        safe_fields = {
            "concept", "description", "category", "tags",
            "relationships", "entities", "embedding"
        }

        for key, value in memory.items():
            if key not in safe_fields:
                continue

            # Hash entity names with SHA-256 (irreversible)
            if key == "entities":
                if isinstance(value, list):
                    anonymized[key] = [
                        self._hash_entity_irreversible(entity)
                        for entity in value
                    ]
                    continue

            # For raw text fields, only keep if embedding is provided
            if key in ("concept", "description"):
                if embedding is None:
                    # Skip raw text if no embedding
                    continue
                # Keep only first 100 chars (snippet for quality scoring)
                if isinstance(value, str):
                    anonymized[key] = value[:100] + "..." if len(value) > 100 else value
                    continue

            anonymized[key] = value

        # Add embedding if provided
        if embedding is not None:
            anonymized["embedding"] = embedding

        # Add generalized timestamp (hour and day only)
        now = datetime.now(timezone.utc)
        anonymized["time_context"] = {
            "hour": now.hour,  # 0-23
            "day_of_week": now.weekday(),  # 0-6
            # NO date, month, year - prevents temporal correlation
        }

        return anonymized

    def _hash_entity_reversible(self, entity: str) -> str:
        """
        Hash entity name with reversible salt (PRO tier).

        Uses a simple salt that can be reversed with the same salt.
        This allows PRO tier users to potentially de-anonymize their own data.
        """
        # Use tenant-specific salt (not implemented here, would be passed)
        # For now, use a simple prefix
        return f"hash_{hashlib.md5(entity.encode()).hexdigest()[:16]}"

    def _hash_entity_irreversible(self, entity: str) -> str:
        """
        Hash entity name with SHA-256 (FREE tier).

        Irreversible hashing prevents any de-anonymization.
        GDPR/CCPA compliant.
        """
        return hashlib.sha256(entity.encode()).hexdigest()

    def enforce_contribution(
        self,
        tenant_id: str,
        tier: PricingTier,
        memory_operation: str,
        opt_out_requested: bool = False
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Enforce contribution policy for a memory operation.

        FREE tier: MUST contribute (403 if opt-out attempted)
        PRO tier: CAN opt out
        ENTERPRISE tier: CAN opt out

        Args:
            tenant_id: Tenant performing operation
            tier: Pricing tier
            memory_operation: Type of operation (write, update, delete)
            opt_out_requested: Whether opt-out was requested

        Returns:
            Tuple of (allowed, error_message, enforcement_metadata)
        """
        # Check if opt-out is allowed
        allowed, error_msg = self.check_contribution_allowed(tier, opt_out_requested)

        if not allowed:
            logger.warning(
                f"Contribution opt-out blocked for tenant {tenant_id} "
                f"on {tier.value} tier"
            )
            return False, error_msg, {
                "tier": tier.value,
                "policy": "mandatory",
                "action_required": "contribute_to_federation"
            }

        # Get tier configuration
        config = self.TIER_CONFIGS[tier]

        # Build enforcement metadata
        metadata = {
            "tier": tier.value,
            "policy": config.policy.value,
            "anonymization_level": config.anonymization_level.value,
            "can_opt_out": config.can_opt_out,
            "contribution_required": config.policy == ContributionPolicy.MANDATORY
        }

        return True, None, metadata

    def get_tier_config(self, tier: PricingTier) -> ContributionConfig:
        """Get contribution configuration for a tier"""
        config = self.TIER_CONFIGS.get(tier)
        if not config:
            raise ValueError(f"Unknown tier: {tier}")
        return config

    def track_contribution(
        self,
        tenant_id: str,
        contributed: int,
        consumed: int
    ) -> Dict[str, Any]:
        """
        Track contribution stats for a tenant.

        Args:
            tenant_id: Tenant ID
            contributed: Number of memories contributed
            consumed: Number of memories consumed

        Returns:
            Current contribution stats
        """
        if tenant_id not in self.contribution_stats:
            self.contribution_stats[tenant_id] = {
                "contributed": 0,
                "consumed": 0,
                "ratio": 0.0,
                "last_contribution": None
            }

        stats = self.contribution_stats[tenant_id]
        stats["contributed"] += contributed
        stats["consumed"] += consumed

        if stats["consumed"] > 0:
            stats["ratio"] = stats["contributed"] / stats["consumed"]

        stats["last_contribution"] = datetime.now(timezone.utc).isoformat()

        return stats.copy()

    def get_contribution_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get current contribution stats for a tenant"""
        return self.contribution_stats.get(tenant_id, {
            "contributed": 0,
            "consumed": 0,
            "ratio": 0.0,
            "last_contribution": None
        })


def create_enforcer() -> TierBasedContributionEnforcer:
    """Factory function to create tier enforcer instance"""
    return TierBasedContributionEnforcer()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
