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
Webhook Manager
===============

Manage webhook lifecycle: register, update, delete, test.

Features:
    - CRUD operations for webhooks
    - URL validation (no private IPs)
    - Test webhook with sample payload
    - Enable/disable webhooks
    - Delivery history
    - Statistics and health metrics

Usage:
    manager = WebhookManager(tenant_id="user_123", storage=storage_backend)

    # Register webhook
    webhook = await manager.register(
        url="https://api.example.com/webhook",
        events=[WebhookEvent.MEMORY_CREATED]
    )

    # Test webhook
    success = await manager.test(webhook.id)

    # List webhooks
    webhooks = await manager.list()
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime, timedelta

from .models import Webhook, WebhookEvent, WebhookDelivery, DeliveryStatus, WebhookStats
from .validator import URLValidator, WebhookValidationError
from .signer import WebhookSigner
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


class WebhookNotFoundError(Exception):
    """Raised when webhook is not found."""
    pass


class WebhookManager:
    """
    Manages webhook registration and lifecycle.

    Responsibilities:
        - Register/unregister webhooks
        - Validate webhook URLs
        - Update webhook configuration
        - Test webhooks
        - Retrieve delivery history
        - Calculate statistics
    """

    def __init__(self, tenant_id: str, storage: StorageBackend):
        """
        Initialize webhook manager.

        Args:
            tenant_id: Tenant/user identifier
            storage: Storage backend for persistence
        """
        self.tenant_id = tenant_id
        self.storage = storage
        self.url_validator = URLValidator(require_https=True)

    async def register(
        self,
        url: str,
        events: List[WebhookEvent],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Webhook:
        """
        Register a new webhook.

        Args:
            url: Webhook endpoint URL
            events: List of events to subscribe to
            metadata: Optional metadata (name, description, etc.)

        Returns:
            Created Webhook instance

        Raises:
            WebhookValidationError: If URL validation fails

        Example:
            webhook = await manager.register(
                url="https://api.example.com/webhook",
                events=[WebhookEvent.MEMORY_CREATED, WebhookEvent.SYNC_COMPLETED],
                metadata={"name": "Production webhook"}
            )
        """
        # Validate URL
        is_valid, error = self.url_validator.validate(url)
        if not is_valid:
            raise WebhookValidationError(f"Invalid webhook URL: {error}")

        # Create webhook
        webhook = Webhook(
            user_id=UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id,
            url=url,
            events=events,
            metadata=metadata or {}
        )

        # Store in database
        with self.storage.cursor() as cursor:
            cursor.execute("""
                INSERT INTO webhooks (
                    id, user_id, url, secret, events, active,
                    created_at, failure_count, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(webhook.id),
                str(webhook.user_id),
                str(webhook.url),
                webhook.secret,
                ','.join([e.value for e in webhook.events]),
                webhook.active,
                webhook.created_at.isoformat(),
                webhook.failure_count,
                str(webhook.metadata)
            ))

        logger.info(f"Registered webhook {webhook.id} for tenant {self.tenant_id}")
        return webhook

    async def get(self, webhook_id: UUID) -> Webhook:
        """
        Get webhook by ID.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Webhook instance

        Raises:
            WebhookNotFoundError: If webhook doesn't exist
        """
        with self.storage.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, url, secret, events, active,
                       created_at, failure_count, last_triggered_at,
                       last_success_at, last_failure_at, metadata
                FROM webhooks
                WHERE id = ? AND user_id = ?
            """, (str(webhook_id), self.tenant_id))

            row = cursor.fetchone()
            if not row:
                raise WebhookNotFoundError(f"Webhook {webhook_id} not found")

            return self._row_to_webhook(row)

    async def list(self, active_only: bool = False) -> List[Webhook]:
        """
        List all webhooks for tenant.

        Args:
            active_only: Only return active webhooks

        Returns:
            List of Webhook instances
        """
        query = """
            SELECT id, user_id, url, secret, events, active,
                   created_at, failure_count, last_triggered_at,
                   last_success_at, last_failure_at, metadata
            FROM webhooks
            WHERE user_id = ?
        """
        if active_only:
            query += " AND active = 1"

        with self.storage.cursor() as cursor:
            cursor.execute(query, (self.tenant_id,))
            rows = cursor.fetchall()

        return [self._row_to_webhook(row) for row in rows]

    async def update(
        self,
        webhook_id: UUID,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Webhook:
        """
        Update webhook configuration.

        Args:
            webhook_id: Webhook to update
            url: New URL (optional)
            events: New event list (optional)
            active: Enable/disable (optional)
            metadata: New metadata (optional)

        Returns:
            Updated Webhook instance

        Raises:
            WebhookNotFoundError: If webhook doesn't exist
            WebhookValidationError: If new URL is invalid
        """
        # Get existing webhook
        webhook = await self.get(webhook_id)

        # Validate new URL if provided
        if url is not None:
            is_valid, error = self.url_validator.validate(url)
            if not is_valid:
                raise WebhookValidationError(f"Invalid webhook URL: {error}")
            webhook.url = url

        # Update fields
        if events is not None:
            webhook.events = events
        if active is not None:
            webhook.active = active
        if metadata is not None:
            webhook.metadata = metadata

        # Save to database
        with self.storage.cursor() as cursor:
            cursor.execute("""
                UPDATE webhooks
                SET url = ?, events = ?, active = ?, metadata = ?
                WHERE id = ? AND user_id = ?
            """, (
                str(webhook.url),
                ','.join([e.value for e in webhook.events]),
                webhook.active,
                str(webhook.metadata),
                str(webhook_id),
                self.tenant_id
            ))

        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    async def delete(self, webhook_id: UUID) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook to delete

        Returns:
            True if deleted, False if not found
        """
        with self.storage.cursor() as cursor:
            cursor.execute("""
                DELETE FROM webhooks
                WHERE id = ? AND user_id = ?
            """, (str(webhook_id), self.tenant_id))

            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted webhook {webhook_id}")
        return deleted

    async def test(self, webhook_id: UUID) -> bool:
        """
        Send a test event to webhook.

        Args:
            webhook_id: Webhook to test

        Returns:
            True if test successful, False otherwise

        Example:
            success = await manager.test(webhook.id)
            if success:
                print("Webhook is working!")
        """
        webhook = await self.get(webhook_id)

        # Create test payload
        test_payload = {
            "event": "webhook.test",
            "delivery_id": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": "This is a test webhook from CONTINUUM",
                "webhook_id": str(webhook_id),
                "tenant_id": self.tenant_id
            }
        }

        # Send request (this would normally use the dispatcher)
        try:
            import httpx
            signer = WebhookSigner(webhook.secret)
            headers = signer.generate_headers(
                payload=test_payload,
                delivery_id="test",
                event="webhook.test"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    str(webhook.url),
                    json=test_payload,
                    headers=headers
                )
                success = response.status_code in (200, 201, 202, 204)

            logger.info(f"Test webhook {webhook_id}: {'success' if success else 'failed'}")
            return success

        except Exception as e:
            logger.error(f"Test webhook {webhook_id} failed: {e}")
            return False

    async def get_deliveries(
        self,
        webhook_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookDelivery]:
        """
        Get delivery history for webhook.

        Args:
            webhook_id: Webhook identifier
            limit: Maximum deliveries to return
            offset: Pagination offset

        Returns:
            List of WebhookDelivery instances
        """
        with self.storage.cursor() as cursor:
            cursor.execute("""
                SELECT id, webhook_id, event, payload, status, attempts,
                       next_retry_at, response_code, response_body, duration_ms,
                       created_at, completed_at, error_message
                FROM webhook_deliveries
                WHERE webhook_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (str(webhook_id), limit, offset))

            rows = cursor.fetchall()

        return [self._row_to_delivery(row) for row in rows]

    async def get_stats(self, webhook_id: UUID) -> WebhookStats:
        """
        Get statistics for webhook.

        Args:
            webhook_id: Webhook identifier

        Returns:
            WebhookStats instance with metrics
        """
        with self.storage.cursor() as cursor:
            # Total deliveries
            cursor.execute("""
                SELECT COUNT(*), AVG(duration_ms)
                FROM webhook_deliveries
                WHERE webhook_id = ?
            """, (str(webhook_id),))
            total, avg_duration = cursor.fetchone()

            # Success/failure counts
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM webhook_deliveries
                WHERE webhook_id = ?
                GROUP BY status
            """, (str(webhook_id),))
            status_counts = dict(cursor.fetchall())

            # Last 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
                FROM webhook_deliveries
                WHERE webhook_id = ? AND created_at > ?
            """, (str(webhook_id), yesterday.isoformat()))
            last_24h_total, last_24h_success = cursor.fetchone()

        return WebhookStats(
            webhook_id=webhook_id,
            total_deliveries=total or 0,
            successful_deliveries=status_counts.get('success', 0),
            failed_deliveries=status_counts.get('failed', 0),
            avg_duration_ms=avg_duration or 0.0,
            last_24h_deliveries=last_24h_total or 0,
            last_24h_success_rate=(last_24h_success / last_24h_total * 100) if last_24h_total else 0.0
        )

    def _row_to_webhook(self, row: tuple) -> Webhook:
        """Convert database row to Webhook instance."""
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

    def _row_to_delivery(self, row: tuple) -> WebhookDelivery:
        """Convert database row to WebhookDelivery instance."""
        return WebhookDelivery(
            id=UUID(row[0]),
            webhook_id=UUID(row[1]),
            event=WebhookEvent(row[2]),
            payload=eval(row[3]),
            status=DeliveryStatus(row[4]),
            attempts=row[5],
            next_retry_at=datetime.fromisoformat(row[6]) if row[6] else None,
            response_code=row[7],
            response_body=row[8],
            duration_ms=row[9],
            created_at=datetime.fromisoformat(row[10]),
            completed_at=datetime.fromisoformat(row[11]) if row[11] else None,
            error_message=row[12]
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
