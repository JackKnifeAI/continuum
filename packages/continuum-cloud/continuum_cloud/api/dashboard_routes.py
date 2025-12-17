"""
Public Dashboard Routes

No authentication required - these are for the customer-facing dashboard.
"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    tenant_id: Optional[str] = Query("default", description="Tenant ID"),
):
    """
    Get dashboard statistics for a tenant.

    This is a public endpoint for the customer dashboard (no auth required).
    Returns memory stats and tier information.
    """
    # TODO: Look up actual stats from database based on tenant_id
    # For now, return sample data structure

    return {
        "tenant_id": tenant_id or "demo-tenant",
        "instance_id": "web-dashboard",
        "entities": 0,
        "messages": 0,
        "decisions": 0,
        "attention_links": 0,
        "compound_concepts": 0,
        "tier": "FREE",
        "api_calls_today": 0,
        "tier_info": {
            "name": "FREE",
            "limits": {
                "memories": 1000,
                "api_calls_per_day": 100
            }
        }
    }
