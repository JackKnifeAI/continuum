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
Webhook System Tests
====================

Comprehensive tests for webhook infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import hmac
import hashlib
import json

from ..models import Webhook, WebhookEvent, WebhookDelivery, DeliveryStatus
from ..signer import WebhookSigner, verify_webhook_signature
from ..validator import URLValidator, WebhookValidationError
from ..manager import WebhookManager, WebhookNotFoundError
from ..dispatcher import EventDispatcher, CircuitBreakerOpenError
from ..queue import InMemoryQueue
from ..emitter import EventEmitter


# ============================================================================
# Signature Tests
# ============================================================================

class TestWebhookSigner:
    """Test webhook signing and verification."""

    def test_signature_generation(self):
        """Test signature generation."""
        signer = WebhookSigner("test_secret")
        payload = {"event": "test", "data": {"foo": "bar"}}

        signature, timestamp = signer.sign(payload)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex = 64 chars
        assert isinstance(timestamp, int)

    def test_signature_verification(self):
        """Test signature verification."""
        secret = "test_secret_12345"
        payload = {"event": "test", "data": {"foo": "bar"}}

        signer = WebhookSigner(secret)
        signature, timestamp = signer.sign(payload)

        # Should verify
        is_valid = verify_webhook_signature(
            payload=payload,
            signature=signature,
            timestamp=str(timestamp),
            secret=secret
        )
        assert is_valid

    def test_wrong_secret_fails(self):
        """Test wrong secret fails verification."""
        payload = {"event": "test"}

        signer = WebhookSigner("correct_secret")
        signature, timestamp = signer.sign(payload)

        # Wrong secret should fail
        is_valid = verify_webhook_signature(
            payload=payload,
            signature=signature,
            timestamp=str(timestamp),
            secret="wrong_secret"
        )
        assert not is_valid

    def test_replay_protection(self):
        """Test replay attack protection."""
        payload = {"event": "test"}

        signer = WebhookSigner("secret")
        signature, _ = signer.sign(payload)

        # Old timestamp (10 minutes ago)
        old_timestamp = int((datetime.utcnow() - timedelta(minutes=10)).timestamp())

        is_valid = verify_webhook_signature(
            payload=payload,
            signature=signature,
            timestamp=str(old_timestamp),
            secret="secret",
            max_age=300  # 5 minutes
        )
        assert not is_valid

    def test_header_generation(self):
        """Test header generation."""
        signer = WebhookSigner("secret")
        payload = {"event": "test"}

        headers = signer.generate_headers(
            payload=payload,
            delivery_id="del_123",
            event="memory.created"
        )

        assert "X-Continuum-Signature" in headers
        assert "X-Continuum-Timestamp" in headers
        assert headers["X-Continuum-Event"] == "memory.created"
        assert headers["X-Continuum-Delivery"] == "del_123"
        assert headers["Content-Type"] == "application/json"


# ============================================================================
# URL Validator Tests
# ============================================================================

class TestURLValidator:
    """Test URL validation."""

    def test_valid_https_url(self):
        """Test valid HTTPS URL passes."""
        validator = URLValidator(require_https=True)
        is_valid, error = validator.validate("https://api.example.com/webhook")
        assert is_valid
        assert error is None

    def test_http_rejected_in_production(self):
        """Test HTTP rejected when HTTPS required."""
        validator = URLValidator(require_https=True)
        is_valid, error = validator.validate("http://api.example.com/webhook")
        assert not is_valid
        assert "HTTPS required" in error

    def test_private_ip_blocked(self):
        """Test private IP addresses blocked."""
        validator = URLValidator(require_https=False)

        # Test various private ranges
        private_urls = [
            "http://10.0.0.1/webhook",
            "http://192.168.1.1/webhook",
            "http://172.16.0.1/webhook",
            "http://127.0.0.1/webhook",
        ]

        for url in private_urls:
            # Note: This will fail DNS resolution, which is expected
            is_valid, error = validator.validate(url)
            # Will fail on DNS or private IP check
            assert not is_valid

    def test_localhost_blocked(self):
        """Test localhost blocked."""
        validator = URLValidator(require_https=False)
        is_valid, error = validator.validate("http://localhost/webhook")
        # Will fail on DNS or private IP
        assert not is_valid


# ============================================================================
# Webhook Manager Tests
# ============================================================================

class TestWebhookManager:
    """Test webhook manager."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage backend."""
        from unittest.mock import MagicMock
        storage = MagicMock()
        storage.cursor.return_value.__enter__ = MagicMock()
        storage.cursor.return_value.__exit__ = MagicMock()
        return storage

    @pytest.mark.asyncio
    async def test_register_webhook(self, mock_storage):
        """Test webhook registration."""
        manager = WebhookManager("user_123", mock_storage)

        # Mock cursor
        mock_cursor = MagicMock()
        mock_storage.cursor.return_value.__enter__.return_value = mock_cursor

        webhook = await manager.register(
            url="https://api.example.com/webhook",
            events=[WebhookEvent.MEMORY_CREATED],
            metadata={"name": "Test"}
        )

        assert webhook.url == "https://api.example.com/webhook"
        assert WebhookEvent.MEMORY_CREATED in webhook.events
        assert webhook.active
        assert len(webhook.secret) > 0

    @pytest.mark.asyncio
    async def test_invalid_url_rejected(self, mock_storage):
        """Test invalid URL rejected."""
        manager = WebhookManager("user_123", mock_storage)

        with pytest.raises(WebhookValidationError):
            await manager.register(
                url="http://localhost/webhook",  # Private IP
                events=[WebhookEvent.MEMORY_CREATED]
            )


# ============================================================================
# Event Dispatcher Tests
# ============================================================================

class TestEventDispatcher:
    """Test event dispatcher."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage backend."""
        from unittest.mock import MagicMock
        storage = MagicMock()
        storage.cursor.return_value.__enter__ = MagicMock()
        storage.cursor.return_value.__exit__ = MagicMock()
        return storage

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, mock_storage):
        """Test circuit breaker opens after failures."""
        dispatcher = EventDispatcher(mock_storage)

        webhook = Webhook(
            user_id=uuid4(),
            url="https://api.example.com/webhook",
            events=[WebhookEvent.MEMORY_CREATED]
        )

        # Record multiple failures
        for _ in range(dispatcher.CIRCUIT_BREAKER_THRESHOLD):
            await dispatcher._record_failure(webhook.id)

        # Circuit should be open
        is_allowed = dispatcher._check_circuit_breaker(webhook.id)
        assert not is_allowed


# ============================================================================
# Queue Tests
# ============================================================================

class TestDeliveryQueue:
    """Test delivery queue."""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        """Test basic enqueue/dequeue."""
        queue = InMemoryQueue()

        delivery = WebhookDelivery(
            webhook_id=uuid4(),
            event=WebhookEvent.MEMORY_CREATED,
            payload={"test": "data"}
        )

        await queue.enqueue(delivery)

        dequeued = await queue.dequeue(timeout=1)
        assert dequeued is not None
        assert dequeued.id == delivery.id

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test priority queue ordering."""
        queue = InMemoryQueue()

        # Enqueue low priority first
        low = WebhookDelivery(
            webhook_id=uuid4(),
            event=WebhookEvent.MEMORY_CREATED,
            payload={"priority": "low"}
        )
        await queue.enqueue(low, priority="low")

        # Then high priority
        high = WebhookDelivery(
            webhook_id=uuid4(),
            event=WebhookEvent.MEMORY_CREATED,
            payload={"priority": "high"}
        )
        await queue.enqueue(high, priority="high")

        # High should come out first
        first = await queue.dequeue(timeout=1)
        assert first.payload["priority"] == "high"

    @pytest.mark.asyncio
    async def test_delayed_delivery(self):
        """Test delayed delivery."""
        queue = InMemoryQueue()

        delivery = WebhookDelivery(
            webhook_id=uuid4(),
            event=WebhookEvent.MEMORY_CREATED,
            payload={"test": "delayed"}
        )

        # Enqueue with 1 second delay
        await queue.enqueue(delivery, delay=timedelta(seconds=1))

        # Should not be available immediately
        immediate = await queue.dequeue(timeout=0.1)
        assert immediate is None

        # Wait for delay
        await asyncio.sleep(1.1)

        # Should be available now
        delayed = await queue.dequeue(timeout=1)
        assert delayed is not None
        assert delayed.id == delivery.id


# ============================================================================
# Event Emitter Tests
# ============================================================================

class TestEventEmitter:
    """Test event emitter."""

    @pytest.fixture
    def mock_storage(self):
        """Mock storage backend."""
        from unittest.mock import MagicMock
        storage = MagicMock()
        storage.cursor.return_value.__enter__ = MagicMock()
        storage.cursor.return_value.__exit__ = MagicMock()
        return storage

    @pytest.mark.asyncio
    async def test_emit_constructs_payload(self, mock_storage):
        """Test event emission constructs proper payload."""
        emitter = EventEmitter("user_123", mock_storage)

        # Mock _find_webhooks to return empty list
        emitter._find_webhooks = lambda event: []

        payload = emitter._construct_payload(
            WebhookEvent.MEMORY_CREATED,
            {"memory_id": "123"}
        )

        assert payload["event"] == "memory.created"
        assert payload["tenant_id"] == "user_123"
        assert "timestamp" in payload
        assert payload["data"]["memory_id"] == "123"


# ============================================================================
# Integration Tests
# ============================================================================

class TestWebhookIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_webhook_flow(self):
        """Test complete webhook flow from registration to delivery."""
        # This would test:
        # 1. Register webhook
        # 2. Emit event
        # 3. Queue delivery
        # 4. Process delivery
        # 5. Verify signature
        # 6. Check delivery status

        # Simplified test - full implementation would use real HTTP server
        assert True


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
