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
Webhook Data Models
===================

Core data structures for the webhook system.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl, validator
import secrets


class WebhookEvent(str, Enum):
    """
    Events that can trigger webhook notifications.

    Memory Events:
        - MEMORY_CREATED: New memory stored
        - MEMORY_UPDATED: Memory modified
        - MEMORY_DELETED: Memory removed

    Concept Events:
        - CONCEPT_DISCOVERED: New concept extracted

    Session Events:
        - SESSION_STARTED: User session begins
        - SESSION_ENDED: User session ends

    Sync Events:
        - SYNC_COMPLETED: Memory sync successful
        - SYNC_FAILED: Memory sync failed

    User Events:
        - USER_CREATED: New user registered

    Quota Events:
        - QUOTA_WARNING: Approaching quota limits
        - QUOTA_EXCEEDED: Quota limits exceeded
    """
    # Memory events
    MEMORY_CREATED = "memory.created"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_DELETED = "memory.deleted"

    # Concept events
    CONCEPT_DISCOVERED = "concept.discovered"

    # Session events
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"

    # Sync events
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # User events
    USER_CREATED = "user.created"

    # Quota events
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"  # Max retries exceeded


class Webhook(BaseModel):
    """
    Webhook configuration.

    Attributes:
        id: Unique webhook identifier
        user_id: Tenant/user who owns this webhook
        url: Destination URL for webhook deliveries
        secret: Secret key for HMAC signing (never expose in API responses)
        events: List of events this webhook subscribes to
        active: Whether webhook is currently active
        created_at: When webhook was created
        failure_count: Consecutive failure count (for circuit breaker)
        last_triggered_at: Last time an event was sent
        last_success_at: Last successful delivery
        last_failure_at: Last failed delivery
        metadata: Custom metadata (tags, description, etc.)
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    url: HttpUrl
    secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    events: List[WebhookEvent] = Field(default_factory=list)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    failure_count: int = Field(default=0)
    last_triggered_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            HttpUrl: str,
        }

    @validator('events')
    def validate_events(cls, v):
        """Ensure at least one event is subscribed."""
        if not v:
            raise ValueError("Must subscribe to at least one event")
        return v

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to API-safe dictionary (hides secret)."""
        data = self.dict()
        data['secret'] = f"whs_{'*' * 32}"  # Mask secret
        data['id'] = str(data['id'])
        data['user_id'] = str(data['user_id'])
        data['url'] = str(data['url'])
        data['events'] = [e.value for e in data['events']]
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['last_triggered_at']:
            data['last_triggered_at'] = data['last_triggered_at'].isoformat()
        if data['last_success_at']:
            data['last_success_at'] = data['last_success_at'].isoformat()
        if data['last_failure_at']:
            data['last_failure_at'] = data['last_failure_at'].isoformat()
        return data


class WebhookDelivery(BaseModel):
    """
    Record of a webhook delivery attempt.

    Attributes:
        id: Unique delivery identifier
        webhook_id: Reference to webhook configuration
        event: Event type that triggered this delivery
        payload: Event payload sent to webhook
        status: Current delivery status
        attempts: Number of delivery attempts
        next_retry_at: When to retry (if failed)
        response_code: HTTP response code from endpoint
        response_body: Response body (truncated to 1KB)
        duration_ms: Request duration in milliseconds
        created_at: When delivery was created
        completed_at: When delivery completed (success or max retries)
        error_message: Error message if failed
    """
    id: UUID = Field(default_factory=uuid4)
    webhook_id: UUID
    event: WebhookEvent
    payload: Dict[str, Any]
    status: DeliveryStatus = Field(default=DeliveryStatus.PENDING)
    attempts: int = Field(default=0)
    next_retry_at: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = self.dict()
        data['id'] = str(data['id'])
        data['webhook_id'] = str(data['webhook_id'])
        data['event'] = data['event'].value
        data['status'] = data['status'].value
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['completed_at']:
            data['completed_at'] = data['completed_at'].isoformat()
        if data['next_retry_at']:
            data['next_retry_at'] = data['next_retry_at'].isoformat()
        return data


class CircuitBreakerState(BaseModel):
    """Circuit breaker state for a webhook endpoint."""
    webhook_id: UUID
    state: str = Field(default="closed")  # closed, open, half_open
    failure_count: int = Field(default=0)
    success_count: int = Field(default=0)
    last_failure_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    next_half_open_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class WebhookStats(BaseModel):
    """Statistics for a webhook."""
    webhook_id: UUID
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    avg_duration_ms: float = 0.0
    last_24h_deliveries: int = 0
    last_24h_success_rate: float = 0.0

    class Config:
        json_encoders = {
            UUID: str,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
