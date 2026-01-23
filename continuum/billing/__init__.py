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
    'get_shared_metering',
    'get_shared_rate_limiter',
]

# =============================================================================
# SHARED SINGLETON INSTANCES
# =============================================================================

_shared_metering: UsageMetering | None = None
_shared_rate_limiter: RateLimiter | None = None


def get_shared_metering() -> UsageMetering:
    """
    Get the shared global UsageMetering instance.

    This ensures all parts of the application use the same metering instance,
    providing consistent API call tracking across middleware and routes.

    Returns:
        The shared UsageMetering instance
    """
    global _shared_metering
    if _shared_metering is None:
        _shared_metering = UsageMetering()
    return _shared_metering


def get_shared_rate_limiter() -> RateLimiter:
    """
    Get the shared global RateLimiter instance.

    Returns:
        The shared RateLimiter instance (uses shared metering)
    """
    global _shared_rate_limiter
    if _shared_rate_limiter is None:
        _shared_rate_limiter = RateLimiter(get_shared_metering())
    return _shared_rate_limiter

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
