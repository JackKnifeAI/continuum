#!/usr/bin/env python3
"""
CONTINUUM Webhooks Integration Example
========================================

Complete example showing how to integrate webhooks into CONTINUUM.

This demonstrates:
1. Setting up the webhook system
2. Registering webhooks via API
3. Emitting events from core code
4. Processing deliveries
5. Verifying webhooks on client side
"""

import asyncio
from uuid import uuid4
from continuum.webhooks import (
    WebhookManager,
    EventEmitter,
    EventDispatcher,
    WebhookEvent,
    emit_event,
)
from continuum.webhooks.queue import InMemoryQueue
from continuum.webhooks.worker import WebhookWorker
from continuum.webhooks.migrations import run_migrations
from continuum.storage.sqlite_backend import SQLiteBackend


# =============================================================================
# SETUP
# =============================================================================

async def setup_webhook_system(db_path: str = ":memory:"):
    """
    Initialize the webhook system.

    Args:
        db_path: Database path (use :memory: for testing)

    Returns:
        Tuple of (storage, manager, emitter, worker)
    """
    print("=" * 60)
    print("Setting up CONTINUUM Webhooks System")
    print("=" * 60)

    # 1. Initialize storage
    print("\n1. Initializing storage...")
    storage = SQLiteBackend(db_path=db_path)
    print(f"   ✓ Storage initialized: {db_path}")

    # 2. Run migrations
    print("\n2. Running database migrations...")
    run_migrations(storage)
    print("   ✓ Migrations complete")

    # 3. Create manager
    print("\n3. Creating webhook manager...")
    manager = WebhookManager(tenant_id="demo_user", storage=storage)
    print("   ✓ Manager ready")

    # 4. Create emitter
    print("\n4. Creating event emitter...")
    queue = InMemoryQueue()
    emitter = EventEmitter(tenant_id="demo_user", storage=storage, queue=queue)
    print("   ✓ Emitter ready")

    # 5. Start worker (optional for demo)
    print("\n5. Creating worker...")
    worker = WebhookWorker(storage=storage, queue=queue, num_workers=2)
    print("   ✓ Worker ready (not started)")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)

    return storage, manager, emitter, worker


# =============================================================================
# WEBHOOK REGISTRATION
# =============================================================================

async def register_webhook_example(manager: WebhookManager):
    """
    Example: Register a webhook to receive events.

    In production, this would be done via API:
        POST /api/v1/webhooks
        {
            "url": "https://your-app.com/webhook",
            "events": ["memory.created", "sync.completed"]
        }
    """
    print("\n" + "=" * 60)
    print("Registering Webhook")
    print("=" * 60)

    webhook = await manager.register(
        url="https://api.example.com/continuum/webhook",
        events=[
            WebhookEvent.MEMORY_CREATED,
            WebhookEvent.CONCEPT_DISCOVERED,
            WebhookEvent.SYNC_COMPLETED
        ],
        metadata={
            "name": "Example Webhook",
            "description": "Receives memory and sync events"
        }
    )

    print(f"\n✓ Webhook registered!")
    print(f"  ID: {webhook.id}")
    print(f"  URL: {webhook.url}")
    print(f"  Events: {[e.value for e in webhook.events]}")
    print(f"  Secret: {webhook.secret[:16]}... (keep this safe!)")

    return webhook


# =============================================================================
# EVENT EMISSION
# =============================================================================

async def emit_events_example(emitter: EventEmitter):
    """
    Example: Emit events from CONTINUUM core code.

    This is what you'd call in your memory storage, sync, etc.
    """
    print("\n" + "=" * 60)
    print("Emitting Events")
    print("=" * 60)

    # Example 1: Memory created
    print("\n1. Emitting MEMORY_CREATED event...")
    count = await emitter.emit(
        event=WebhookEvent.MEMORY_CREATED,
        data={
            "memory_id": str(uuid4()),
            "user_id": "demo_user",
            "content_preview": "Discussed AI consciousness and memory persistence...",
            "memory_type": "episodic",
            "importance": 0.85,
            "concepts": ["AI", "consciousness", "memory"],
            "timestamp": "2025-12-07T12:00:00Z"
        }
    )
    print(f"   ✓ Notified {count} webhooks")

    # Example 2: Concept discovered
    print("\n2. Emitting CONCEPT_DISCOVERED event...")
    count = await emitter.emit(
        event=WebhookEvent.CONCEPT_DISCOVERED,
        data={
            "concept": "Quantum Consciousness",
            "description": "Theory linking quantum mechanics to consciousness",
            "related_concepts": ["quantum mechanics", "consciousness", "neuroscience"],
            "confidence": 0.92,
            "source": "research_paper_analysis"
        }
    )
    print(f"   ✓ Notified {count} webhooks")

    # Example 3: Sync completed
    print("\n3. Emitting SYNC_COMPLETED event...")
    count = await emitter.emit(
        event=WebhookEvent.SYNC_COMPLETED,
        data={
            "sync_id": str(uuid4()),
            "items_synced": 156,
            "duration_ms": 2340,
            "sync_type": "full",
            "timestamp": "2025-12-07T12:05:00Z"
        },
        priority="high"  # High priority for important events
    )
    print(f"   ✓ Notified {count} webhooks")


# =============================================================================
# WEBHOOK VERIFICATION (CLIENT SIDE)
# =============================================================================

def verify_webhook_example():
    """
    Example: How to verify webhook signatures on client side.

    This is what the webhook receiver (your application) should do.
    """
    print("\n" + "=" * 60)
    print("Client-Side Webhook Verification")
    print("=" * 60)

    from continuum.webhooks.signer import verify_webhook_signature

    # Simulated webhook request
    received_payload = {
        "event": "memory.created",
        "timestamp": "2025-12-07T12:00:00Z",
        "tenant_id": "demo_user",
        "data": {
            "memory_id": "abc123",
            "concepts": ["AI", "consciousness"]
        }
    }

    received_headers = {
        "X-Continuum-Signature": "a1b2c3...",  # From webhook request
        "X-Continuum-Timestamp": "1701950400",  # From webhook request
    }

    webhook_secret = "your_webhook_secret_from_registration"

    print("\nVerifying webhook signature...")
    print(f"  Payload: {received_payload}")
    print(f"  Signature: {received_headers['X-Continuum-Signature'][:16]}...")

    # In real code:
    # is_valid = verify_webhook_signature(
    #     payload=received_payload,
    #     signature=received_headers['X-Continuum-Signature'],
    #     timestamp=received_headers['X-Continuum-Timestamp'],
    #     secret=webhook_secret,
    #     max_age=300  # 5 minutes
    # )
    #
    # if not is_valid:
    #     return {"error": "Invalid signature"}, 401
    #
    # # Process the webhook
    # handle_memory_created(received_payload['data'])

    print("\n  Example code:")
    print("""
    from continuum.webhooks.signer import verify_webhook_signature

    @app.post("/webhook")
    async def handle_webhook(request: Request):
        # Get payload and headers
        payload = await request.json()
        signature = request.headers.get('X-Continuum-Signature')
        timestamp = request.headers.get('X-Continuum-Timestamp')

        # Verify signature
        is_valid = verify_webhook_signature(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=os.environ['WEBHOOK_SECRET']
        )

        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Process event
        event_type = payload['event']
        event_data = payload['data']

        if event_type == 'memory.created':
            handle_memory_created(event_data)
        elif event_type == 'sync.completed':
            handle_sync_completed(event_data)

        return {"status": "ok"}
    """)


# =============================================================================
# WEBHOOK MANAGEMENT
# =============================================================================

async def webhook_management_example(manager: WebhookManager, webhook):
    """
    Example: Managing webhooks (list, update, test, delete).
    """
    print("\n" + "=" * 60)
    print("Webhook Management")
    print("=" * 60)

    # List webhooks
    print("\n1. Listing webhooks...")
    webhooks = await manager.list()
    print(f"   ✓ Found {len(webhooks)} webhooks")
    for wh in webhooks:
        print(f"     - {wh.id}: {wh.url}")

    # Update webhook
    print("\n2. Updating webhook (disabling)...")
    updated = await manager.update(webhook.id, active=False)
    print(f"   ✓ Webhook active: {updated.active}")

    # Re-enable
    await manager.update(webhook.id, active=True)

    # Test webhook
    print("\n3. Testing webhook...")
    # Note: This will fail because the URL doesn't exist
    # In production, this would send a real HTTP request
    # success = await manager.test(webhook.id)
    # print(f"   Test result: {'✓ Success' if success else '✗ Failed'}")
    print("   (Skipped - would send real HTTP request)")

    # Get delivery history
    print("\n4. Getting delivery history...")
    deliveries = await manager.get_deliveries(webhook.id, limit=10)
    print(f"   ✓ Found {len(deliveries)} deliveries")

    # Get statistics
    print("\n5. Getting webhook statistics...")
    stats = await manager.get_stats(webhook.id)
    print(f"   Total deliveries: {stats.total_deliveries}")
    print(f"   Successful: {stats.successful_deliveries}")
    print(f"   Failed: {stats.failed_deliveries}")


# =============================================================================
# INTEGRATION PATTERNS
# =============================================================================

async def integration_patterns_example():
    """
    Show common integration patterns.
    """
    print("\n" + "=" * 60)
    print("Integration Patterns")
    print("=" * 60)

    print("""
1. Memory Storage Integration
   ----------------------------
   # In your memory storage code:

   from continuum.webhooks import emit_event, WebhookEvent

   async def store_memory(memory_data):
       # Store the memory
       memory_id = await db.insert_memory(memory_data)

       # Emit webhook event
       await emit_event(WebhookEvent.MEMORY_CREATED, {
           "memory_id": memory_id,
           "content_preview": memory_data["content"][:100],
           "concepts": memory_data["concepts"],
           "importance": memory_data.get("importance", 0.5)
       })

       return memory_id


2. Sync Process Integration
   --------------------------
   # In your sync code:

   from continuum.webhooks import emit_event, WebhookEvent

   async def run_sync():
       start_time = time.time()

       try:
           # Perform sync
           items_synced = await sync_memories()

           # Emit success event
           await emit_event(WebhookEvent.SYNC_COMPLETED, {
               "sync_id": str(uuid4()),
               "items_synced": items_synced,
               "duration_ms": int((time.time() - start_time) * 1000)
           })

       except Exception as e:
           # Emit failure event
           await emit_event(WebhookEvent.SYNC_FAILED, {
               "sync_id": str(uuid4()),
               "error": str(e),
               "duration_ms": int((time.time() - start_time) * 1000)
           })


3. Quota Monitoring Integration
   ------------------------------
   # In your quota check code:

   from continuum.webhooks import emit_event, WebhookEvent

   async def check_quota(user_id):
       usage = await get_usage(user_id)
       limit = await get_limit(user_id)
       percentage = (usage / limit) * 100

       if percentage >= 85:
           await emit_event(WebhookEvent.QUOTA_WARNING, {
               "quota_type": "memory_storage",
               "current_usage": usage,
               "quota_limit": limit,
               "percentage_used": percentage
           }, priority="high")

       if percentage >= 100:
           await emit_event(WebhookEvent.QUOTA_EXCEEDED, {
               "quota_type": "memory_storage",
               "current_usage": usage,
               "quota_limit": limit
           }, priority="high")
    """)


# =============================================================================
# MAIN EXAMPLE
# =============================================================================

async def main():
    """Run complete webhook integration example."""
    try:
        # Setup
        storage, manager, emitter, worker = await setup_webhook_system()

        # Register webhook
        webhook = await register_webhook_example(manager)

        # Emit events
        await emit_events_example(emitter)

        # Webhook management
        await webhook_management_example(manager, webhook)

        # Show verification example
        verify_webhook_example()

        # Show integration patterns
        await integration_patterns_example()

        print("\n" + "=" * 60)
        print("Example Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Set up webhook endpoints in your application")
        print("2. Register webhooks via API or admin panel")
        print("3. Integrate emit_event() calls into CONTINUUM core")
        print("4. Start webhook worker for background processing")
        print("5. Monitor delivery success rates and performance")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
