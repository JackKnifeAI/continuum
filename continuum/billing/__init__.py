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
CONTINUUM Billing Module

Stripe integration for subscription management, usage metering, and billing.
Supports Free, Pro, and Enterprise tiers with usage-based pricing.
"""

from typing import Optional

from .metering import RateLimiter, UsageMetering
from .middleware import (
    BillingMiddleware,
    FeatureAccessMiddleware,
    FederationContributionMiddleware,
    StorageLimitMiddleware,
)
from .stripe_client import StripeClient, SubscriptionStatus
from .tiers import PricingTier, TierLimits, get_tier_limits

# ---------------------------------------------------------------------------
# Shared singleton - ensures BillingMiddleware and dashboard routes read from
# the same in-memory counters.
# ---------------------------------------------------------------------------

_metering_instance: Optional[UsageMetering] = None


def get_metering() -> UsageMetering:
    """Return the process-wide UsageMetering singleton, creating it if needed."""
    global _metering_instance
    if _metering_instance is None:
        _metering_instance = UsageMetering()
    return _metering_instance


__all__ = [
    'StripeClient',
    'SubscriptionStatus',
    'UsageMetering',
    'RateLimiter',
    'PricingTier',
    'TierLimits',
    'get_tier_limits',
    'BillingMiddleware',
    'FeatureAccessMiddleware',
    'StorageLimitMiddleware',
    'FederationContributionMiddleware',
    'get_metering',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
