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
Public memory routes (non-admin, API-key authenticated).

These routes are for regular API users (not admin dashboard).
Used primarily for integration testing of billing/tier functionality.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
import logging

from .middleware import get_tenant_from_key
from continuum.core.memory import TenantManager
from continuum.billing.tiers import PricingTier
from continuum.federation.tier_enforcer import create_enforcer
from continuum.federation.shared import SharedKnowledge

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================

class CreateMemoryRequest(BaseModel):
    """Request to create a new memory."""
    entity: str = Field(..., description="Entity or subject", min_length=1)
    content: str = Field(..., description="Memory content", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class CreateMemoryResponse(BaseModel):
    """Response after creating a memory."""
    id: int = Field(..., description="Memory ID")
    status: str = Field(..., description="Status")
    tenant_id: str = Field(..., description="Tenant identifier")


class SettingsRequest(BaseModel):
    """User settings update request."""
    contribute_to_federation: Optional[bool] = Field(None, description="Enable/disable federation contribution")


class SettingsResponse(BaseModel):
    """User settings response."""
    contribute_to_federation: bool = Field(..., description="Federation contribution enabled")
    tier: str = Field(..., description="Current pricing tier")


class UserStatusResponse(BaseModel):
    """User status response."""
    tier: str = Field(..., description="Current pricing tier")
    tenant_id: str = Field(..., description="Tenant identifier")
    contribute_to_federation: bool = Field(..., description="Federation contribution enabled")


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/memories", tags=["Public Memories"])

# Global tenant manager and federation
tenant_manager = TenantManager()
shared_knowledge = SharedKnowledge()
enforcer = create_enforcer()


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=CreateMemoryResponse)
async def create_memory(
    request_obj: CreateMemoryRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_from_key),
    x_federation_opt_out: Optional[str] = Header(None, alias="X-Federation-Opt-Out")
):
    """
    Create a new memory entry (public API, requires X-API-Key).

    This endpoint is subject to billing/rate limiting based on tier.
    FREE tier users MUST contribute to federation (opt-out returns 403).
    PRO/ENTERPRISE tier users can opt out via X-Federation-Opt-Out header.

    **Parameters:**
    - entity: Main entity or subject
    - content: Memory content
    - metadata: Optional metadata

    **Headers:**
    - X-API-Key: Required for authentication
    - X-Federation-Opt-Out: Set to "true" to opt out (PRO/ENTERPRISE only)

    **Returns:**
    Memory ID and status.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        # Get tier from request state (set by BillingMiddleware)
        tier_str = getattr(request.state, "tier", "free")
        tier = PricingTier(tier_str)

        # Check if opt-out is requested
        opt_out_requested = x_federation_opt_out and x_federation_opt_out.lower() == "true"

        # Enforce contribution policy
        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id=tenant_id,
            tier=tier,
            memory_operation="write",
            opt_out_requested=opt_out_requested
        )

        if not allowed:
            # FREE tier trying to opt out - return 403 Forbidden
            # Note: FastAPI wraps detail in {"detail": ...}, but custom exception handlers can unwrap
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "error": error_msg,
                    "tier": tier_str,
                    "policy": "mandatory",
                    "upgrade_url": "https://buy.stripe.com/test_aFaeVeaZtbgy0Uz3BB"
                }
            )

        # Store as a message
        import time
        import json
        import sqlite3

        timestamp = time.time()
        metadata_json = json.dumps(request_obj.metadata) if request_obj.metadata else None

        conn = sqlite3.connect(memory.db_path)
        c = conn.cursor()

        # Get next message_number for this instance_id
        c.execute("""
            SELECT COALESCE(MAX(message_number), 0) + 1
            FROM auto_messages
            WHERE instance_id = ?
        """, (request_obj.entity,))
        message_number = c.fetchone()[0]

        c.execute(
            """
            INSERT INTO auto_messages (tenant_id, instance_id, timestamp, message_number, role, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (tenant_id, request_obj.entity, timestamp, message_number, "user", request_obj.content, metadata_json)
        )

        memory_id = c.lastrowid
        conn.commit()
        conn.close()

        # Contribute to federation if not opted out
        if not opt_out_requested:
            try:
                # Create concept from memory
                concept = {
                    "entity": request_obj.entity,
                    "content": request_obj.content,
                    "tenant_id": tenant_id,
                    "created_at": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                    "entities": [request_obj.entity],
                }

                # Anonymize based on tier
                anonymized = enforcer.anonymize_memory(concept, tier)

                # Contribute to shared knowledge
                result = shared_knowledge.contribute_concepts(
                    node_id=tenant_id,
                    concepts=[anonymized]
                )

                logger.info(
                    f"Contributed to federation: {result['new_concepts']} new concepts "
                    f"from tenant {tenant_id} (tier: {tier_str})"
                )

                # Track contribution
                enforcer.track_contribution(
                    tenant_id=tenant_id,
                    contributed=1,
                    consumed=0
                )

            except Exception as fed_error:
                # Federation contribution failure should not block memory write
                logger.warning(f"Federation contribution failed: {fed_error}")

        return CreateMemoryResponse(
            id=memory_id,
            status="stored",
            tenant_id=tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory creation failed: {str(e)}")


# =============================================================================
# ADDITIONAL ROUTES (mounted separately in server.py)
# =============================================================================

# Settings router
settings_router = APIRouter(prefix="/settings", tags=["Settings"])

@settings_router.put("", response_model=SettingsResponse)
async def update_settings(
    settings: SettingsRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Update user contribution settings.

    PRO/ENTERPRISE tier users can toggle federation contribution.
    FREE tier users cannot opt out (returns 403).

    **Parameters:**
    - contribute_to_federation: Enable/disable contribution

    **Returns:**
    Updated settings.
    """
    # Get tier from request state
    tier_str = getattr(request.state, "tier", "free")
    tier = PricingTier(tier_str)

    # Check if opt-out is allowed
    if settings.contribute_to_federation is False:
        allowed, error_msg, _ = enforcer.enforce_contribution(
            tenant_id=tenant_id,
            tier=tier,
            memory_operation="write",
            opt_out_requested=True
        )

        if not allowed:
            raise HTTPException(status_code=403, detail=error_msg)

    # In production, save to database
    # For now, just return the requested setting
    return SettingsResponse(
        contribute_to_federation=settings.contribute_to_federation if settings.contribute_to_federation is not None else True,
        tier=tier_str
    )


# User status router
user_router = APIRouter(prefix="/user", tags=["User"])

@user_router.get("/status", response_model=UserStatusResponse)
async def get_user_status(
    request: Request,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Get current user status and tier information.

    **Returns:**
    User status including tier and settings.
    """
    # Get tier from request state
    tier_str = getattr(request.state, "tier", "free")

    return UserStatusResponse(
        tier=tier_str,
        tenant_id=tenant_id,
        contribute_to_federation=True  # Default for now
    )


# Fix imports
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
