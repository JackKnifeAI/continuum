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

from .metering import RateLimiter, UsageMetering
from .middleware import (
    BillingMiddleware,
    FeatureAccessMiddleware,
    FederationContributionMiddleware,
    StorageLimitMiddleware,
)
from .stripe_client import StripeClient, SubscriptionStatus
from .tiers import PricingTier, TierLimits, get_tier_limits

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
    'get_global_metering',
]

# =============================================================================
# GLOBAL METERING SINGLETON
# =============================================================================

# Global metering instance shared across the entire application
# This ensures consistent API call tracking across all routes and middleware
_global_metering: UsageMetering | None = None


def get_global_metering() -> UsageMetering:
    """
    Get or create the global UsageMetering singleton.

    This ensures that all routes and middleware use the same metering instance,
    providing accurate API call tracking across the entire application.

    Returns:
        UsageMetering: The global metering instance
    """
    global _global_metering
    if _global_metering is None:
        _global_metering = UsageMetering()
    return _global_metering

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
