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
Shared Billing Instances

Provides singleton instances of metering and rate limiter to ensure
consistent usage tracking across all routes and middleware.

This solves the problem of multiple routes creating separate UsageMetering
instances with independent in-memory caches, which would lead to inconsistent
API call counts and rate limit enforcement.
"""

from .metering import RateLimiter, UsageMetering

# Singleton instances - shared across the entire application
# These are initialized once on import and reused everywhere
_metering_instance = None
_rate_limiter_instance = None


def get_metering() -> UsageMetering:
    """
    Get the shared UsageMetering instance.

    Returns:
        UsageMetering: Shared metering instance
    """
    global _metering_instance
    if _metering_instance is None:
        _metering_instance = UsageMetering()
    return _metering_instance


def get_rate_limiter() -> RateLimiter:
    """
    Get the shared RateLimiter instance.

    Returns:
        RateLimiter: Shared rate limiter instance
    """
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(get_metering())
    return _rate_limiter_instance


def reset_instances() -> None:
    """
    Reset singleton instances (useful for testing).

    This clears the cached instances so new ones will be created
    on the next call to get_metering() or get_rate_limiter().
    """
    global _metering_instance, _rate_limiter_instance
    _metering_instance = None
    _rate_limiter_instance = None

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
