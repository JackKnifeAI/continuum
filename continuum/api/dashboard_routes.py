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
Public Dashboard Routes

No authentication required - these are for the customer-facing dashboard.
"""
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from continuum.billing.metering import UsageMetering
from continuum.billing.tiers import PricingTier, get_tier_limits
from continuum.core.memory import TenantManager

router = APIRouter()
tenant_manager = TenantManager()

# Global metering instance (shared with BillingMiddleware in server.py)
# This is populated when the server starts
_metering_instance: Optional[UsageMetering] = None


def set_metering_instance(metering: UsageMetering) -> None:
    """
    Set the global metering instance.

    Called from server.py during startup to share the metering instance
    with the dashboard routes.
    """
    global _metering_instance
    _metering_instance = metering


def get_metering_instance() -> UsageMetering:
    """
    Get the global metering instance.

    Returns:
        UsageMetering instance

    Raises:
        RuntimeError: If metering instance not initialized
    """
    if _metering_instance is None:
        raise RuntimeError(
            "Metering instance not initialized. "
            "Call set_metering_instance() from server.py during startup."
        )
    return _metering_instance


def get_tenant_tier(tenant_id: str) -> PricingTier:
    """
    Get the pricing tier for a tenant from the admin database.

    Args:
        tenant_id: Tenant identifier

    Returns:
        PricingTier enum value (defaults to FREE if not found)
    """
    try:
        db_path = Path.home() / ".continuum" / "admin.db"
        if not db_path.exists():
            return PricingTier.FREE

        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Query user's tier from the users table
        c.execute(
            "SELECT tier FROM users WHERE tenant_id = ?",
            (tenant_id,)
        )
        row = c.fetchone()
        conn.close()

        if row and row[0]:
            tier_str = row[0].upper()
            try:
                return PricingTier[tier_str]
            except KeyError:
                # Invalid tier in database, default to FREE
                return PricingTier.FREE

        # Tenant not found in users table, default to FREE
        return PricingTier.FREE

    except Exception:
        # On any error, default to FREE tier
        return PricingTier.FREE


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

        # Look up tenant's pricing tier from admin database
        tier = get_tenant_tier(tenant_id)
        tier_limits = get_tier_limits(tier)

        # Get API call usage from metering system
        metering = get_metering_instance()
        api_calls_today = await metering.get_usage(
            tenant_id=tenant_id,
            metric='api_calls',
            period='day'
        )

        # Get storage usage from metering system
        storage_usage = await metering.get_storage_usage(tenant_id)

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
            "storage_usage": {
                "memories": storage_usage.get('memories', 0),
                "embeddings": storage_usage.get('embeddings', 0),
                "bytes": storage_usage.get('bytes', 0)
            },
            "tier_info": {
                "name": tier.value.upper(),
                "limits": {
                    "memories": tier_limits.max_memories,
                    "api_calls_per_day": tier_limits.api_calls_per_day,
                    "api_calls_per_minute": tier_limits.api_calls_per_minute,
                    "storage_bytes": tier_limits.max_storage_bytes
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard stats: {str(e)}"
        ) from e

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
