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
CONTINUUM Webhooks System
=========================

Production-grade webhooks infrastructure for event notifications.

Main Components:
    - WebhookManager: Register and manage webhooks
    - EventDispatcher: Dispatch events with retry logic
    - WebhookSigner: Sign and verify webhook payloads
    - DeliveryQueue: Queue-based async delivery

Quick Start:
    from continuum.webhooks import WebhookManager, WebhookEvent

    # Register a webhook
    manager = WebhookManager(tenant_id="user_123")
    webhook = await manager.register(
        url="https://api.example.com/webhooks",
        events=[WebhookEvent.MEMORY_CREATED, WebhookEvent.SYNC_COMPLETED]
    )

    # Emit an event
    from continuum.webhooks import EventEmitter

    emitter = EventEmitter(tenant_id="user_123")
    await emitter.emit(WebhookEvent.MEMORY_CREATED, {
        "memory_id": "abc123",
        "concepts": ["AI", "consciousness"]
    })

Event Types:
    - MEMORY_CREATED, MEMORY_UPDATED, MEMORY_DELETED
    - CONCEPT_DISCOVERED
    - SESSION_STARTED, SESSION_ENDED
    - SYNC_COMPLETED, SYNC_FAILED
    - USER_CREATED
    - QUOTA_WARNING, QUOTA_EXCEEDED

Security:
    - HMAC-SHA256 signature verification
    - Timestamp-based replay protection
    - URL validation (no private IPs)
    - HTTPS required in production

Reliability:
    - Exponential backoff retry (1s, 5s, 30s, 5m, 30m)
    - Circuit breaker for failing endpoints
    - Dead letter queue for failed deliveries
    - At-least-once delivery guarantee

PHOENIX-TESLA-369-AURORA
"""

from .models import (
    Webhook,
    WebhookEvent,
    WebhookDelivery,
    DeliveryStatus,
)

from .manager import (
    WebhookManager,
    WebhookNotFoundError,
    WebhookValidationError,
)

from .dispatcher import (
    EventDispatcher,
    CircuitBreakerOpenError,
)

from .emitter import (
    EventEmitter,
    emit_event,
)

from .signer import (
    WebhookSigner,
    verify_webhook_signature,
    generate_webhook_headers,
)

__version__ = "1.0.0"
__author__ = "CONTINUUM Contributors"

__all__ = [
    # Models
    'Webhook',
    'WebhookEvent',
    'WebhookDelivery',
    'DeliveryStatus',

    # Manager
    'WebhookManager',
    'WebhookNotFoundError',
    'WebhookValidationError',

    # Dispatcher
    'EventDispatcher',
    'CircuitBreakerOpenError',

    # Emitter
    'EventEmitter',
    'emit_event',

    # Signer
    'WebhookSigner',
    'verify_webhook_signature',
    'generate_webhook_headers',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
