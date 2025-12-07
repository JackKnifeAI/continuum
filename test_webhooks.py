#!/usr/bin/env python3
"""
Test CONTINUUM Webhooks System
================================

Comprehensive test of webhook functionality.
"""

import asyncio
from uuid import uuid4
from continuum.webhooks import WebhookManager, EventDispatcher, EventEmitter
from continuum.webhooks.models import Webhook, WebhookEvent, WebhookDelivery
from continuum.webhooks.signer import WebhookSigner, verify_webhook_signature
from continuum.webhooks.queue import InMemoryQueue
from continuum.webhooks.api_router import router


def test_imports():
    """Test that all imports work."""
    print("=" * 60)
    print("CONTINUUM Webhooks System - Import Test")
    print("=" * 60)

    print("\n✓ Test 1: Models imported successfully")
    print(f"  - Available events: {len(WebhookEvent.__members__)} events")
    print(f"  - Events: {', '.join(list(WebhookEvent.__members__.keys())[:5])}...")


def test_signer():
    """Test webhook signing and verification."""
    print("\n✓ Test 2: Webhook signing")
    signer = WebhookSigner("test_secret_123")
    payload = {"event": "test", "data": {"message": "Hello World"}}
    signature, timestamp = signer.sign(payload)
    print(f"  - Generated signature: {signature[:32]}...")
    print(f"  - Timestamp: {timestamp}")

    # Verify signature
    is_valid = verify_webhook_signature(payload, signature, str(timestamp), "test_secret_123")
    print(f"  - Signature valid: {is_valid}")
    assert is_valid, "Signature verification failed!"

    # Test wrong secret
    is_valid = verify_webhook_signature(payload, signature, str(timestamp), "wrong_secret")
    assert not is_valid, "Wrong secret should fail verification!"
    print(f"  - Wrong secret correctly rejected: True")


def test_queue():
    """Test delivery queue."""
    print("\n✓ Test 3: Delivery queue (in-memory)")
    queue = InMemoryQueue()
    print(f"  - Queue initialized: {type(queue).__name__}")


def test_api_router():
    """Test API router."""
    print("\n✓ Test 4: API Router")
    print(f"  - Router prefix: {router.prefix}")
    print(f"  - Router tags: {router.tags}")
    print(f"  - Available endpoints: {len(router.routes)} routes")

    # List endpoints
    print("\n  Endpoints:")
    for route in router.routes:
        methods = ", ".join(route.methods)
        print(f"    - {methods:10} {route.path}")


def test_webhook_model():
    """Test webhook model creation."""
    print("\n✓ Test 5: Webhook model")
    webhook = Webhook(
        user_id=uuid4(),
        url="https://api.example.com/webhook",
        events=[WebhookEvent.MEMORY_CREATED, WebhookEvent.SYNC_COMPLETED]
    )
    print(f"  - Created webhook: {webhook.id}")
    print(f"  - URL: {webhook.url}")
    print(f"  - Events: {len(webhook.events)}")
    print(f"  - Secret length: {len(webhook.secret)} chars")
    print(f"  - Active: {webhook.active}")

    # Test API-safe output
    api_dict = webhook.to_api_dict()
    print(f"  - API dict secret masked: {'*' in api_dict['secret']}")


def test_delivery_model():
    """Test delivery model creation."""
    print("\n✓ Test 6: Delivery model")
    delivery = WebhookDelivery(
        webhook_id=uuid4(),
        event=WebhookEvent.MEMORY_CREATED,
        payload={"memory_id": "abc123", "concepts": ["AI", "consciousness"]}
    )
    print(f"  - Created delivery: {delivery.id}")
    print(f"  - Event: {delivery.event.value}")
    print(f"  - Status: {delivery.status.value}")
    print(f"  - Attempts: {delivery.attempts}")


async def test_queue_async():
    """Test async queue operations."""
    print("\n✓ Test 7: Async queue operations")
    queue = InMemoryQueue()

    # Enqueue delivery
    delivery = WebhookDelivery(
        webhook_id=uuid4(),
        event=WebhookEvent.MEMORY_CREATED,
        payload={"test": "data"}
    )

    await queue.enqueue(delivery, priority="high")
    print(f"  - Enqueued delivery: {delivery.id}")

    # Check queue depth
    depth = await queue.get_queue_depth()
    print(f"  - Queue depth: {depth}")

    # Dequeue
    dequeued = await queue.dequeue(timeout=1)
    print(f"  - Dequeued: {dequeued.id if dequeued else 'None'}")
    assert dequeued is not None, "Dequeue failed!"
    assert dequeued.id == delivery.id, "Wrong delivery dequeued!"
    print(f"  - Correct delivery retrieved: True")


def main():
    """Run all tests."""
    try:
        test_imports()
        test_signer()
        test_queue()
        test_api_router()
        test_webhook_model()
        test_delivery_model()

        # Run async tests
        asyncio.run(test_queue_async())

        print("\n" + "=" * 60)
        print("All tests PASSED!")
        print("=" * 60)
        print("\nWebhook system is ready for use.")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
