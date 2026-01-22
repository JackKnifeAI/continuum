#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
# ██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
# ╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Public Dashboard Routes

No authentication required - these are for the customer-facing dashboard.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from continuum.billing.metering import UsageMetering
from continuum.billing.tiers import PricingTier, get_tier_limits
from continuum.core.memory import TenantManager

router = APIRouter()
tenant_manager = TenantManager()

# Global metering instance for tracking API usage
# This is shared across all dashboard routes and middleware
_metering_instance: Optional[UsageMetering] = None


def get_metering() -> UsageMetering:
    """
    Get or create the global metering instance.

    Returns:
        UsageMetering instance for tracking API calls and usage
    """
    global _metering_instance
    if _metering_instance is None:
        _metering_instance = UsageMetering()
    return _metering_instance


def set_metering(metering: UsageMetering) -> None:
    """
    Set the global metering instance.

    This allows the server to inject the same metering instance
    used by middleware into the dashboard routes.

    Args:
        metering: UsageMetering instance to use
    """
    global _metering_instance
    _metering_instance = metering


@router.get("/stats")
async def get_dashboard_stats(
    tenant_id: Optional[str] = Query("default", description="Tenant ID"),
):
    """
    Get dashboard statistics for a tenant.

    This is a public endpoint for the customer dashboard (no auth required).
    Returns memory stats and tier information.
    """
    try:
        # Get tenant's memory instance and query actual stats from database
        memory = tenant_manager.get_tenant(tenant_id)
        stats = await memory.aget_stats()

        # Look up tenant's pricing tier (default to FREE for now)
        # In production, this would query the subscription/billing database
        tier = PricingTier.FREE
        tier_limits = get_tier_limits(tier)

        # Get API call count for today from metering system
        metering = get_metering()
        api_calls_today = await metering.get_usage(
            tenant_id=tenant_id, metric="api_calls", period="day"
        )

        return {
            "tenant_id": stats["tenant_id"],
            "instance_id": stats["instance_id"],
            "entities": stats["entities"],
            "messages": stats.get("messages", 0) + stats.get("auto_messages", 0),
            "decisions": stats["decisions"],
            "attention_links": stats["attention_links"],
            "compound_concepts": stats["compound_concepts"],
            "tier": tier.value.upper(),
            "api_calls_today": api_calls_today,
            "tier_info": {
                "name": tier.value.upper(),
                "limits": {
                    "memories": tier_limits.max_memories,
                    "api_calls_per_day": tier_limits.api_calls_per_day,
                },
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}"
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
