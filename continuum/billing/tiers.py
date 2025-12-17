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
Pricing Tiers for CONTINUUM Cloud

Defines tier limits, pricing, and feature access.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class PricingTier(str, Enum):
    """CONTINUUM pricing tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TierLimits:
    """
    Resource limits and features for a pricing tier.
    """
    tier: PricingTier

    # Memory storage limits
    max_memories: int
    max_embeddings: int
    max_storage_mb: int

    # API rate limits
    api_calls_per_day: int
    api_calls_per_minute: int
    concurrent_requests: int

    # Federation features
    federation_enabled: bool
    federation_priority: int  # 0 = none, 1 = normal, 2 = high, 3 = critical

    # Search and extraction
    max_extraction_batch_size: int
    semantic_search_enabled: bool
    realtime_sync_enabled: bool

    # Support and SLA (required fields)
    support_level: str  # "community", "email", "priority"
    monthly_price_usd: float

    # Optional fields (must come after required fields)
    sla_uptime: Optional[float] = None  # e.g., 0.99 = 99%
    sla_response_hours: Optional[int] = None
    overage_price_per_1k_calls: Optional[float] = None
    custom_pricing: bool = False


# Tier definitions

FREE_TIER = TierLimits(
    tier=PricingTier.FREE,
    # Memory limits
    max_memories=10000,
    max_embeddings=10000,
    max_storage_mb=500,
    # API limits - generous for local/dev use
    api_calls_per_day=10000,
    api_calls_per_minute=100,
    concurrent_requests=10,
    # Federation
    federation_enabled=False,
    federation_priority=0,
    # Features
    max_extraction_batch_size=10,
    semantic_search_enabled=True,
    realtime_sync_enabled=False,
    # Support
    support_level="community",
    sla_uptime=None,
    sla_response_hours=None,
    # Cost
    monthly_price_usd=0.0,
    overage_price_per_1k_calls=None
)

PRO_TIER = TierLimits(
    tier=PricingTier.PRO,
    # Memory limits
    max_memories=100_000,
    max_embeddings=100_000,
    max_storage_mb=10_000,  # 10 GB
    # API limits
    api_calls_per_day=10_000,
    api_calls_per_minute=100,
    concurrent_requests=10,
    # Federation
    federation_enabled=True,
    federation_priority=1,
    # Features
    max_extraction_batch_size=100,
    semantic_search_enabled=True,
    realtime_sync_enabled=True,
    # Support
    support_level="email",
    sla_uptime=0.99,
    sla_response_hours=24,
    # Cost
    monthly_price_usd=29.0,
    overage_price_per_1k_calls=0.10
)

ENTERPRISE_TIER = TierLimits(
    tier=PricingTier.ENTERPRISE,
    # Memory limits (effectively unlimited)
    max_memories=10_000_000,
    max_embeddings=10_000_000,
    max_storage_mb=1_000_000,  # 1 TB
    # API limits (very high)
    api_calls_per_day=1_000_000,
    api_calls_per_minute=1000,
    concurrent_requests=100,
    # Federation
    federation_enabled=True,
    federation_priority=3,  # Critical priority
    # Features
    max_extraction_batch_size=1000,
    semantic_search_enabled=True,
    realtime_sync_enabled=True,
    # Support
    support_level="priority",
    sla_uptime=0.999,
    sla_response_hours=1,
    # Cost
    monthly_price_usd=0.0,  # Custom pricing
    overage_price_per_1k_calls=None,
    custom_pricing=True
)


# Tier lookup
_TIER_MAP = {
    PricingTier.FREE: FREE_TIER,
    PricingTier.PRO: PRO_TIER,
    PricingTier.ENTERPRISE: ENTERPRISE_TIER
}


def get_tier_limits(tier: PricingTier) -> TierLimits:
    """
    Get limits for a pricing tier.

    Args:
        tier: PricingTier enum value

    Returns:
        TierLimits object

    Raises:
        ValueError: If tier is unknown
    """
    if tier not in _TIER_MAP:
        raise ValueError(f"Unknown tier: {tier}")
    return _TIER_MAP[tier]


def get_tier_from_price_id(price_id: str) -> PricingTier:
    """
    Map Stripe price ID to pricing tier.

    Args:
        price_id: Stripe price ID

    Returns:
        PricingTier enum value

    Example price IDs:
        - price_free
        - price_pro_monthly
        - price_pro_annual
        - price_enterprise_custom
    """
    price_id_lower = price_id.lower()

    if 'free' in price_id_lower:
        return PricingTier.FREE
    elif 'pro' in price_id_lower:
        return PricingTier.PRO
    elif 'enterprise' in price_id_lower:
        return PricingTier.ENTERPRISE
    else:
        # Default to free tier for unknown prices
        return PricingTier.FREE


# Stripe price IDs (set via environment variables)
import os

STRIPE_PRICE_IDS = {
    PricingTier.FREE: os.getenv('STRIPE_PRICE_FREE', 'price_free'),
    PricingTier.PRO: os.getenv('STRIPE_PRICE_PRO', 'price_pro_monthly'),
    PricingTier.ENTERPRISE: os.getenv('STRIPE_PRICE_ENTERPRISE', 'price_enterprise_custom')
}


def get_stripe_price_id(tier: PricingTier) -> str:
    """Get Stripe price ID for a tier"""
    return STRIPE_PRICE_IDS[tier]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
