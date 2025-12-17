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
Webhook API Router
==================

FastAPI routes for webhook management.

Endpoints:
    POST   /webhooks              - Create webhook
    GET    /webhooks              - List webhooks
    GET    /webhooks/{id}         - Get webhook details
    PATCH  /webhooks/{id}         - Update webhook
    DELETE /webhooks/{id}         - Delete webhook
    POST   /webhooks/{id}/test    - Send test event
    GET    /webhooks/{id}/deliveries - Delivery history
    POST   /webhooks/{id}/retry/{delivery_id} - Retry delivery
    GET    /webhooks/{id}/stats   - Webhook statistics
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, HttpUrl, Field

from .models import WebhookEvent, Webhook, WebhookDelivery, WebhookStats
from .manager import WebhookManager, WebhookNotFoundError, WebhookValidationError
from ..storage.base import StorageBackend

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_tenant_id(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Extract tenant ID from API key.

    For now, returns a default tenant ID. In production, this should:
    1. Validate the API key
    2. Look up the associated tenant
    3. Return the tenant ID

    Args:
        x_api_key: Optional API key from header

    Returns:
        Tenant ID
    """
    # TODO: Implement proper API key validation
    # For now, use key as tenant ID or default
    if x_api_key:
        return x_api_key
    return "default"


def get_storage() -> StorageBackend:
    """
    Get storage backend instance.

    For now, creates a new SQLite backend. In production, this should:
    1. Use a global/application-level storage instance
    2. Handle connection pooling
    3. Support multiple backend types

    Returns:
        Storage backend instance
    """
    # TODO: Use application-level storage instance
    from ..storage.sqlite_backend import SQLiteBackend
    import os

    # Use default database path
    db_path = os.path.expanduser("~/.continuum/memory.db")
    return SQLiteBackend(db_path=db_path)


# Request/Response Schemas
class CreateWebhookRequest(BaseModel):
    """Request to create webhook."""
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[WebhookEvent] = Field(..., description="Events to subscribe to")
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Webhook description")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://api.example.com/webhooks/continuum",
                "events": ["memory.created", "sync.completed"],
                "name": "Production Webhook",
                "description": "Receives all memory and sync events"
            }
        }


class WebhookResponse(BaseModel):
    """Webhook details response."""
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    last_triggered_at: Optional[str]
    last_success_at: Optional[str]
    last_failure_at: Optional[str]
    failure_count: int
    metadata: dict


class UpdateWebhookRequest(BaseModel):
    """Request to update webhook."""
    url: Optional[HttpUrl] = None
    events: Optional[List[WebhookEvent]] = None
    active: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None


class WebhookListResponse(BaseModel):
    """List of webhooks."""
    webhooks: List[WebhookResponse]
    total: int


class DeliveryResponse(BaseModel):
    """Delivery details response."""
    id: str
    event: str
    status: str
    attempts: int
    response_code: Optional[int]
    duration_ms: int
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]


class DeliveryListResponse(BaseModel):
    """List of deliveries."""
    deliveries: List[DeliveryResponse]
    total: int


class StatsResponse(BaseModel):
    """Webhook statistics."""
    webhook_id: str
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    avg_duration_ms: float
    last_24h_deliveries: int
    last_24h_success_rate: float


class TestWebhookResponse(BaseModel):
    """Test webhook result."""
    success: bool
    message: str


# Endpoints

@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    request: CreateWebhookRequest,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Create a new webhook.

    Subscribes to specified events and validates the URL.

    Returns:
        Created webhook details (secret is masked)

    Raises:
        400: Invalid URL (private IP, invalid domain, etc.)
        409: Webhook already exists for this URL
    """
    try:
        manager = WebhookManager(tenant_id, storage)

        # Build metadata
        metadata = {}
        if request.name:
            metadata["name"] = request.name
        if request.description:
            metadata["description"] = request.description

        webhook = await manager.register(
            url=str(request.url),
            events=request.events,
            metadata=metadata
        )

        return webhook.to_api_dict()

    except WebhookValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    active_only: bool = False,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    List all webhooks for tenant.

    Args:
        active_only: Only return active webhooks

    Returns:
        List of webhooks
    """
    manager = WebhookManager(tenant_id, storage)
    webhooks = await manager.list(active_only=active_only)

    return {
        "webhooks": [w.to_api_dict() for w in webhooks],
        "total": len(webhooks)
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Get webhook details.

    Returns:
        Webhook details

    Raises:
        404: Webhook not found
    """
    try:
        manager = WebhookManager(tenant_id, storage)
        webhook = await manager.get(webhook_id)
        return webhook.to_api_dict()
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    request: UpdateWebhookRequest,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Update webhook configuration.

    Can update URL, events, active status, and metadata.

    Returns:
        Updated webhook details

    Raises:
        404: Webhook not found
        400: Invalid URL
    """
    try:
        manager = WebhookManager(tenant_id, storage)

        # Build metadata update
        metadata = {}
        if request.name is not None:
            metadata["name"] = request.name
        if request.description is not None:
            metadata["description"] = request.description

        webhook = await manager.update(
            webhook_id=webhook_id,
            url=str(request.url) if request.url else None,
            events=request.events,
            active=request.active,
            metadata=metadata if metadata else None
        )

        return webhook.to_api_dict()

    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")
    except WebhookValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Delete a webhook.

    Permanently removes the webhook. Pending deliveries will still be attempted.

    Raises:
        404: Webhook not found
    """
    manager = WebhookManager(tenant_id, storage)
    deleted = await manager.delete(webhook_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/{webhook_id}/test", response_model=TestWebhookResponse)
async def test_webhook(
    webhook_id: UUID,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Send a test event to webhook.

    Sends a 'webhook.test' event to verify the endpoint is working.

    Returns:
        Test result (success/failure)

    Raises:
        404: Webhook not found
    """
    try:
        manager = WebhookManager(tenant_id, storage)
        success = await manager.test(webhook_id)

        return {
            "success": success,
            "message": "Test event delivered successfully" if success else "Test event failed"
        }
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/{webhook_id}/deliveries", response_model=DeliveryListResponse)
async def get_deliveries(
    webhook_id: UUID,
    limit: int = 100,
    offset: int = 0,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Get delivery history for webhook.

    Returns recent deliveries with status, timing, and error information.

    Args:
        limit: Maximum deliveries to return (1-1000)
        offset: Pagination offset

    Returns:
        List of deliveries

    Raises:
        404: Webhook not found
    """
    try:
        manager = WebhookManager(tenant_id, storage)

        # Verify webhook exists
        await manager.get(webhook_id)

        deliveries = await manager.get_deliveries(webhook_id, limit, offset)

        return {
            "deliveries": [d.to_dict() for d in deliveries],
            "total": len(deliveries)
        }
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/{webhook_id}/retry/{delivery_id}", status_code=status.HTTP_202_ACCEPTED)
async def retry_delivery(
    webhook_id: UUID,
    delivery_id: UUID,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Manually retry a failed delivery.

    Re-queues the delivery for immediate processing.

    Returns:
        Accepted (202) if retry queued

    Raises:
        404: Webhook or delivery not found
    """
    try:
        manager = WebhookManager(tenant_id, storage)
        from .dispatcher import EventDispatcher

        # Verify webhook exists
        await manager.get(webhook_id)

        dispatcher = EventDispatcher(storage)
        success = await dispatcher.retry_delivery(delivery_id)

        if not success:
            raise HTTPException(status_code=404, detail="Delivery not found")

        return {"message": "Retry queued"}

    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/{webhook_id}/stats", response_model=StatsResponse)
async def get_webhook_stats(
    webhook_id: UUID,
    tenant_id: str = Depends(get_tenant_id),
    storage: StorageBackend = Depends(get_storage)
):
    """
    Get webhook statistics.

    Returns delivery metrics, success rates, and performance data.

    Raises:
        404: Webhook not found
    """
    try:
        manager = WebhookManager(tenant_id, storage)
        stats = await manager.get_stats(webhook_id)

        success_rate = (
            (stats.successful_deliveries / stats.total_deliveries * 100)
            if stats.total_deliveries > 0 else 0.0
        )

        return {
            "webhook_id": str(stats.webhook_id),
            "total_deliveries": stats.total_deliveries,
            "successful_deliveries": stats.successful_deliveries,
            "failed_deliveries": stats.failed_deliveries,
            "success_rate": success_rate,
            "avg_duration_ms": stats.avg_duration_ms,
            "last_24h_deliveries": stats.last_24h_deliveries,
            "last_24h_success_rate": stats.last_24h_success_rate
        }
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail="Webhook not found")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
