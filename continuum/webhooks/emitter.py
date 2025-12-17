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
Event Emitter
=============

Emit events that trigger webhook deliveries.

Integration points throughout CONTINUUM to notify webhooks.

Usage:
    # Initialize emitter
    emitter = EventEmitter(tenant_id="user_123", storage=storage)

    # Emit event
    await emitter.emit(WebhookEvent.MEMORY_CREATED, {
        "memory_id": "abc123",
        "concepts": ["AI", "consciousness"]
    })

    # Convenience function
    await emit_event(
        tenant_id="user_123",
        event=WebhookEvent.SYNC_COMPLETED,
        data={"sync_id": "xyz"}
    )
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from .models import Webhook, WebhookEvent
from .dispatcher import EventDispatcher
from .queue import DeliveryQueue, InMemoryQueue
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Emits events to registered webhooks.

    Responsibilities:
        - Find webhooks subscribed to event
        - Construct event payload
        - Queue deliveries for async processing
        - Handle errors gracefully
    """

    def __init__(
        self,
        tenant_id: str,
        storage: StorageBackend,
        queue: Optional[DeliveryQueue] = None,
        dispatcher: Optional[EventDispatcher] = None
    ):
        """
        Initialize event emitter.

        Args:
            tenant_id: Tenant/user identifier
            storage: Storage backend
            queue: Delivery queue (optional, creates in-memory if not provided)
            dispatcher: Event dispatcher (optional, creates new if not provided)
        """
        self.tenant_id = tenant_id
        self.storage = storage
        self.queue = queue or InMemoryQueue()
        self.dispatcher = dispatcher or EventDispatcher(storage)

    async def emit(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        priority: str = "normal"
    ) -> int:
        """
        Emit an event to all subscribed webhooks.

        Args:
            event: Event type
            data: Event data
            priority: Queue priority (high/normal/low)

        Returns:
            Number of webhooks notified

        Example:
            count = await emitter.emit(
                event=WebhookEvent.MEMORY_CREATED,
                data={
                    "memory_id": "abc123",
                    "content_preview": "First 100 chars...",
                    "concepts": ["AI", "consciousness"]
                }
            )
            logger.info(f"Notified {count} webhooks")
        """
        # Find webhooks subscribed to this event
        webhooks = await self._find_webhooks(event)

        if not webhooks:
            logger.debug(f"No webhooks subscribed to {event.value}")
            return 0

        # Construct payload
        payload = self._construct_payload(event, data)

        # Dispatch to each webhook
        delivered = 0
        for webhook in webhooks:
            try:
                await self.queue.enqueue(
                    delivery=await self.dispatcher.dispatch(webhook, event, payload),
                    priority=priority
                )
                delivered += 1
            except Exception as e:
                logger.error(f"Failed to dispatch to webhook {webhook.id}: {e}")

        logger.info(f"Emitted {event.value} to {delivered}/{len(webhooks)} webhooks")
        return delivered

    async def emit_batch(
        self,
        events: List[tuple[WebhookEvent, Dict[str, Any]]],
        priority: str = "normal"
    ) -> Dict[WebhookEvent, int]:
        """
        Emit multiple events efficiently.

        Args:
            events: List of (event, data) tuples
            priority: Queue priority

        Returns:
            Dictionary mapping event -> webhook count

        Example:
            results = await emitter.emit_batch([
                (WebhookEvent.MEMORY_CREATED, {"memory_id": "1"}),
                (WebhookEvent.CONCEPT_DISCOVERED, {"concept": "AI"})
            ])
        """
        results = {}
        for event, data in events:
            count = await self.emit(event, data, priority)
            results[event] = count
        return results

    async def _find_webhooks(self, event: WebhookEvent) -> List[Webhook]:
        """
        Find all webhooks subscribed to event.

        Args:
            event: Event type

        Returns:
            List of matching webhooks
        """
        with self.storage.cursor() as cursor:
            # Query webhooks that:
            # 1. Belong to this tenant
            # 2. Are active
            # 3. Subscribe to this event
            cursor.execute("""
                SELECT id, user_id, url, secret, events, active,
                       created_at, failure_count, last_triggered_at,
                       last_success_at, last_failure_at, metadata
                FROM webhooks
                WHERE user_id = ?
                  AND active = 1
                  AND events LIKE ?
            """, (self.tenant_id, f"%{event.value}%"))

            rows = cursor.fetchall()

        webhooks = []
        for row in rows:
            webhook = self._row_to_webhook(row)
            # Verify event is actually in the list (LIKE can match substrings)
            if event in webhook.events:
                webhooks.append(webhook)

        return webhooks

    def _construct_payload(
        self,
        event: WebhookEvent,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construct webhook payload.

        Standard format:
            {
                "event": "memory.created",
                "timestamp": "2025-12-06T12:00:00Z",
                "tenant_id": "user_123",
                "data": { ... }
            }
        """
        return {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tenant_id": self.tenant_id,
            "data": data
        }

    def _row_to_webhook(self, row: tuple) -> Webhook:
        """Convert database row to Webhook instance."""
        from .models import Webhook
        return Webhook(
            id=UUID(row[0]),
            user_id=UUID(row[1]),
            url=row[2],
            secret=row[3],
            events=[WebhookEvent(e) for e in row[4].split(',')],
            active=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]),
            failure_count=row[7],
            last_triggered_at=datetime.fromisoformat(row[8]) if row[8] else None,
            last_success_at=datetime.fromisoformat(row[9]) if row[9] else None,
            last_failure_at=datetime.fromisoformat(row[10]) if row[10] else None,
            metadata=eval(row[11]) if row[11] else {}
        )


# Global emitter instance (initialized per request)
_emitter: Optional[EventEmitter] = None


def init_emitter(tenant_id: str, storage: StorageBackend):
    """Initialize global emitter."""
    global _emitter
    _emitter = EventEmitter(tenant_id, storage)


async def emit_event(
    event: WebhookEvent,
    data: Dict[str, Any],
    priority: str = "normal"
) -> int:
    """
    Convenience function to emit event using global emitter.

    Args:
        event: Event type
        data: Event data
        priority: Queue priority

    Returns:
        Number of webhooks notified

    Example:
        # In your application code
        from continuum.webhooks import emit_event, WebhookEvent

        # After storing a memory
        await emit_event(WebhookEvent.MEMORY_CREATED, {
            "memory_id": memory.id,
            "concepts": [c.name for c in memory.concepts]
        })
    """
    if not _emitter:
        logger.warning("EventEmitter not initialized, cannot emit event")
        return 0

    return await _emitter.emit(event, data, priority)


# Integration helpers for common events

async def emit_memory_created(
    memory_id: str,
    user_id: str,
    content_preview: str,
    concepts: List[str],
    memory_type: str = "episodic",
    importance: float = 0.5,
    session_id: Optional[str] = None
):
    """
    Emit MEMORY_CREATED event.

    Example:
        await emit_memory_created(
            memory_id="abc123",
            user_id="user_123",
            content_preview="Discussed AI consciousness...",
            concepts=["AI", "consciousness"],
            importance=0.8
        )
    """
    return await emit_event(WebhookEvent.MEMORY_CREATED, {
        "memory_id": memory_id,
        "user_id": user_id,
        "content_preview": content_preview,
        "memory_type": memory_type,
        "importance": importance,
        "concepts": concepts,
        "session_id": session_id
    })


async def emit_concept_discovered(
    concept: str,
    description: str,
    related_concepts: List[str],
    confidence: float = 0.9
):
    """
    Emit CONCEPT_DISCOVERED event.

    Example:
        await emit_concept_discovered(
            concept="Quantum Entanglement",
            description="A quantum phenomenon...",
            related_concepts=["quantum mechanics", "physics"]
        )
    """
    return await emit_event(WebhookEvent.CONCEPT_DISCOVERED, {
        "concept": concept,
        "description": description,
        "related_concepts": related_concepts,
        "confidence": confidence
    })


async def emit_sync_completed(
    sync_id: str,
    items_synced: int,
    duration_ms: int,
    sync_type: str = "full"
):
    """
    Emit SYNC_COMPLETED event.

    Example:
        await emit_sync_completed(
            sync_id="sync_123",
            items_synced=150,
            duration_ms=2500
        )
    """
    return await emit_event(WebhookEvent.SYNC_COMPLETED, {
        "sync_id": sync_id,
        "items_synced": items_synced,
        "duration_ms": duration_ms,
        "sync_type": sync_type
    })


async def emit_quota_warning(
    quota_type: str,
    current_usage: int,
    quota_limit: int,
    percentage_used: float
):
    """
    Emit QUOTA_WARNING event.

    Example:
        await emit_quota_warning(
            quota_type="memory_storage",
            current_usage=8500,
            quota_limit=10000,
            percentage_used=85.0
        )
    """
    return await emit_event(WebhookEvent.QUOTA_WARNING, {
        "quota_type": quota_type,
        "current_usage": current_usage,
        "quota_limit": quota_limit,
        "percentage_used": percentage_used
    }, priority="high")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
