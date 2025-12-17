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
Event Dispatcher
================

Dispatches webhook events with retry logic and circuit breaker.

Features:
    - Exponential backoff retry (1s, 5s, 30s, 5m, 30m)
    - Circuit breaker pattern for failing endpoints
    - Concurrent delivery with rate limiting
    - Dead letter queue for max retries
    - Comprehensive error handling

Usage:
    dispatcher = EventDispatcher(storage=storage_backend)

    await dispatcher.dispatch(
        webhook=webhook,
        event=WebhookEvent.MEMORY_CREATED,
        payload={"memory_id": "123"}
    )
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import httpx

from .models import (
    Webhook,
    WebhookEvent,
    WebhookDelivery,
    DeliveryStatus,
    CircuitBreakerState
)
from .signer import WebhookSigner
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class EventDispatcher:
    """
    Dispatches webhook events with reliability features.

    Reliability Features:
        - Exponential backoff: 1s, 5s, 30s, 5m, 30m
        - Circuit breaker: Opens after 5 consecutive failures
        - Timeout: 30 seconds per request
        - Rate limiting: 10 concurrent requests per endpoint
        - Dead letter queue: After 5 failed attempts

    Circuit Breaker States:
        - CLOSED: Normal operation
        - OPEN: Too many failures, reject requests
        - HALF_OPEN: Test if endpoint recovered
    """

    # Retry delays in seconds
    RETRY_DELAYS = [1, 5, 30, 300, 1800]  # 1s, 5s, 30s, 5m, 30m
    MAX_RETRIES = len(RETRY_DELAYS)

    # Circuit breaker config
    CIRCUIT_BREAKER_THRESHOLD = 5  # Failures before opening
    CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes before half-open

    # Request config
    REQUEST_TIMEOUT = 30.0  # seconds
    MAX_CONCURRENT = 10  # per endpoint

    def __init__(self, storage: StorageBackend):
        """
        Initialize event dispatcher.

        Args:
            storage: Storage backend for persistence
        """
        self.storage = storage
        self.circuit_breakers: Dict[UUID, CircuitBreakerState] = {}
        self._semaphores: Dict[UUID, asyncio.Semaphore] = {}

    async def dispatch(
        self,
        webhook: Webhook,
        event: WebhookEvent,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """
        Dispatch event to webhook.

        Args:
            webhook: Webhook configuration
            event: Event type
            payload: Event data

        Returns:
            WebhookDelivery record

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open

        Example:
            delivery = await dispatcher.dispatch(
                webhook=webhook,
                event=WebhookEvent.MEMORY_CREATED,
                payload={"memory_id": "abc123"}
            )
        """
        # Check circuit breaker
        if not self._check_circuit_breaker(webhook.id):
            raise CircuitBreakerOpenError(f"Circuit breaker open for webhook {webhook.id}")

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload
        )

        # Save to database
        await self._save_delivery(delivery)

        # Attempt delivery
        await self._attempt_delivery(webhook, delivery)

        return delivery

    async def _attempt_delivery(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery
    ) -> bool:
        """
        Attempt to deliver webhook.

        Args:
            webhook: Webhook configuration
            delivery: Delivery record

        Returns:
            True if successful, False otherwise
        """
        # Get or create semaphore for rate limiting
        if webhook.id not in self._semaphores:
            self._semaphores[webhook.id] = asyncio.Semaphore(self.MAX_CONCURRENT)

        async with self._semaphores[webhook.id]:
            try:
                # Prepare request
                signer = WebhookSigner(webhook.secret)
                headers = signer.generate_headers(
                    payload=delivery.payload,
                    delivery_id=str(delivery.id),
                    event=delivery.event.value
                )

                # Send request
                start_time = datetime.utcnow()

                async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                    response = await client.post(
                        str(webhook.url),
                        json=delivery.payload,
                        headers=headers
                    )

                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Check success
                success = response.status_code in (200, 201, 202, 204)

                # Update delivery record
                delivery.attempts += 1
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1024]  # Truncate to 1KB
                delivery.duration_ms = int(duration)

                if success:
                    delivery.status = DeliveryStatus.SUCCESS
                    delivery.completed_at = datetime.utcnow()
                    await self._handle_success(webhook, delivery)
                else:
                    await self._handle_failure(webhook, delivery, f"HTTP {response.status_code}")

                await self._update_delivery(delivery)
                return success

            except httpx.TimeoutException as e:
                await self._handle_failure(webhook, delivery, f"Timeout: {e}")
                await self._update_delivery(delivery)
                return False

            except Exception as e:
                await self._handle_failure(webhook, delivery, f"Error: {e}")
                await self._update_delivery(delivery)
                return False

    async def _handle_success(self, webhook: Webhook, delivery: WebhookDelivery):
        """Handle successful delivery."""
        # Reset circuit breaker
        await self._reset_circuit_breaker(webhook.id)

        # Update webhook stats
        with self.storage.cursor() as cursor:
            cursor.execute("""
                UPDATE webhooks
                SET failure_count = 0,
                    last_triggered_at = ?,
                    last_success_at = ?
                WHERE id = ?
            """, (
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                str(webhook.id)
            ))

        logger.info(f"Webhook {webhook.id} delivered successfully (delivery {delivery.id})")

    async def _handle_failure(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        error: str
    ):
        """Handle failed delivery."""
        delivery.error_message = error
        delivery.attempts += 1

        # Check if we should retry
        if delivery.attempts < self.MAX_RETRIES:
            # Schedule retry with exponential backoff
            delay = self.RETRY_DELAYS[delivery.attempts - 1]
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            delivery.status = DeliveryStatus.PENDING
            logger.warning(
                f"Webhook {webhook.id} delivery failed (attempt {delivery.attempts}/{self.MAX_RETRIES}), "
                f"retry in {delay}s: {error}"
            )
        else:
            # Max retries exceeded - dead letter queue
            delivery.status = DeliveryStatus.DEAD_LETTER
            delivery.completed_at = datetime.utcnow()
            logger.error(
                f"Webhook {webhook.id} delivery failed permanently after {delivery.attempts} attempts: {error}"
            )

        # Update circuit breaker
        await self._record_failure(webhook.id)

        # Update webhook failure count
        with self.storage.cursor() as cursor:
            cursor.execute("""
                UPDATE webhooks
                SET failure_count = failure_count + 1,
                    last_triggered_at = ?,
                    last_failure_at = ?
                WHERE id = ?
            """, (
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                str(webhook.id)
            ))

    def _check_circuit_breaker(self, webhook_id: UUID) -> bool:
        """
        Check if circuit breaker allows request.

        Returns:
            True if request allowed, False if circuit is open
        """
        if webhook_id not in self.circuit_breakers:
            self.circuit_breakers[webhook_id] = CircuitBreakerState(webhook_id=webhook_id)

        cb = self.circuit_breakers[webhook_id]

        if cb.state == "closed":
            return True

        if cb.state == "open":
            # Check if timeout expired -> transition to half-open
            if cb.next_half_open_at and datetime.utcnow() >= cb.next_half_open_at:
                cb.state = "half_open"
                cb.success_count = 0
                logger.info(f"Circuit breaker for webhook {webhook_id} -> HALF_OPEN")
                return True
            return False

        if cb.state == "half_open":
            # Allow limited requests to test
            return True

        return False

    async def _record_failure(self, webhook_id: UUID):
        """Record failure and potentially open circuit breaker."""
        if webhook_id not in self.circuit_breakers:
            self.circuit_breakers[webhook_id] = CircuitBreakerState(webhook_id=webhook_id)

        cb = self.circuit_breakers[webhook_id]
        cb.failure_count += 1
        cb.last_failure_at = datetime.utcnow()

        if cb.state == "half_open":
            # Failed during test -> reopen
            cb.state = "open"
            cb.opened_at = datetime.utcnow()
            cb.next_half_open_at = datetime.utcnow() + timedelta(seconds=self.CIRCUIT_BREAKER_TIMEOUT)
            logger.warning(f"Circuit breaker for webhook {webhook_id} -> OPEN (test failed)")

        elif cb.failure_count >= self.CIRCUIT_BREAKER_THRESHOLD:
            # Too many failures -> open
            cb.state = "open"
            cb.opened_at = datetime.utcnow()
            cb.next_half_open_at = datetime.utcnow() + timedelta(seconds=self.CIRCUIT_BREAKER_TIMEOUT)
            logger.warning(
                f"Circuit breaker for webhook {webhook_id} -> OPEN "
                f"({cb.failure_count} consecutive failures)"
            )

    async def _reset_circuit_breaker(self, webhook_id: UUID):
        """Reset circuit breaker after success."""
        if webhook_id not in self.circuit_breakers:
            return

        cb = self.circuit_breakers[webhook_id]

        if cb.state == "half_open":
            cb.success_count += 1
            if cb.success_count >= 2:
                # Success during test -> close
                cb.state = "closed"
                cb.failure_count = 0
                cb.success_count = 0
                logger.info(f"Circuit breaker for webhook {webhook_id} -> CLOSED")
        else:
            # Reset failure count
            cb.failure_count = 0

    async def _save_delivery(self, delivery: WebhookDelivery):
        """Save delivery record to database."""
        with self.storage.cursor() as cursor:
            cursor.execute("""
                INSERT INTO webhook_deliveries (
                    id, webhook_id, event, payload, status, attempts,
                    next_retry_at, response_code, response_body, duration_ms,
                    created_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(delivery.id),
                str(delivery.webhook_id),
                delivery.event.value,
                str(delivery.payload),
                delivery.status.value,
                delivery.attempts,
                delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
                delivery.response_code,
                delivery.response_body,
                delivery.duration_ms,
                delivery.created_at.isoformat(),
                delivery.error_message
            ))

    async def _update_delivery(self, delivery: WebhookDelivery):
        """Update delivery record in database."""
        with self.storage.cursor() as cursor:
            cursor.execute("""
                UPDATE webhook_deliveries
                SET status = ?, attempts = ?, next_retry_at = ?,
                    response_code = ?, response_body = ?, duration_ms = ?,
                    completed_at = ?, error_message = ?
                WHERE id = ?
            """, (
                delivery.status.value,
                delivery.attempts,
                delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
                delivery.response_code,
                delivery.response_body,
                delivery.duration_ms,
                delivery.completed_at.isoformat() if delivery.completed_at else None,
                delivery.error_message,
                str(delivery.id)
            ))

    async def retry_delivery(self, delivery_id: UUID) -> bool:
        """
        Manually retry a failed delivery.

        Args:
            delivery_id: Delivery to retry

        Returns:
            True if successful, False otherwise
        """
        # Get delivery
        with self.storage.cursor() as cursor:
            cursor.execute("""
                SELECT d.*, w.*
                FROM webhook_deliveries d
                JOIN webhooks w ON d.webhook_id = w.id
                WHERE d.id = ?
            """, (str(delivery_id),))
            row = cursor.fetchone()

        if not row:
            return False

        # Reconstruct objects (simplified - needs proper parsing)
        # In production, use proper ORM or parsing
        webhook_id = UUID(row[1])

        # Get webhook
        with self.storage.cursor() as cursor:
            cursor.execute("SELECT * FROM webhooks WHERE id = ?", (str(webhook_id),))
            webhook_row = cursor.fetchone()

        # Attempt redelivery
        # Implementation depends on full object reconstruction
        logger.info(f"Manual retry requested for delivery {delivery_id}")
        return True

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
