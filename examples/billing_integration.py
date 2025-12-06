"""
CONTINUUM Billing Integration Example

Shows how to integrate the billing system into a FastAPI application.
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import os

# Import billing components
from continuum.billing import (
    StripeClient,
    UsageMetering,
    RateLimiter,
    PricingTier,
    get_tier_limits,
    BillingMiddleware,
    FeatureAccessMiddleware,
    StorageLimitMiddleware,
)

# Initialize FastAPI app
app = FastAPI(title="CONTINUUM Cloud API")

# Initialize billing components
stripe_client = StripeClient(
    api_key=os.getenv('STRIPE_SECRET_KEY'),
    webhook_secret=os.getenv('STRIPE_WEBHOOK_SECRET')
)
metering = UsageMetering()
rate_limiter = RateLimiter(metering)


# Database mock (replace with actual database)
class SubscriptionDB:
    """Mock subscription database"""

    def __init__(self):
        self.subscriptions = {}

    async def get_subscription(self, tenant_id: str) -> dict:
        """Get subscription for tenant"""
        return self.subscriptions.get(tenant_id, {
            'tenant_id': tenant_id,
            'tier': PricingTier.FREE,
            'stripe_customer_id': None,
            'stripe_subscription_id': None,
            'status': 'active'
        })

    async def update_subscription(self, tenant_id: str, data: dict):
        """Update subscription"""
        if tenant_id not in self.subscriptions:
            self.subscriptions[tenant_id] = {}
        self.subscriptions[tenant_id].update(data)


db = SubscriptionDB()


# Helper function to get tenant's tier
async def get_tenant_tier(tenant_id: str) -> PricingTier:
    """Get pricing tier for tenant"""
    subscription = await db.get_subscription(tenant_id)
    return subscription.get('tier', PricingTier.FREE)


# Add billing middleware
app.add_middleware(
    BillingMiddleware,
    metering=metering,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier,
    exclude_paths=["/health", "/docs", "/redoc", "/openapi.json"]
)

app.add_middleware(
    FeatureAccessMiddleware,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier,
    feature_map={
        "/api/federation": "federation",
        "/api/realtime": "realtime_sync",
        "/api/search/semantic": "semantic_search"
    }
)

app.add_middleware(
    StorageLimitMiddleware,
    metering=metering,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier,
    write_endpoints=["/api/memories", "/api/embeddings"]
)


# Routes

@app.get("/health")
async def health_check():
    """Health check (excluded from billing)"""
    return {"status": "healthy"}


@app.get("/api/tier")
async def get_current_tier(request: Request):
    """Get current pricing tier for authenticated tenant"""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    tier = await get_tenant_tier(tenant_id)
    limits = get_tier_limits(tier)

    # Get current usage
    usage = await metering.get_storage_usage(tenant_id)
    api_calls_today = await metering.get_usage(tenant_id, 'api_calls', period='day')

    return {
        "tier": tier.value,
        "limits": {
            "memories": limits.max_memories,
            "api_calls_per_day": limits.api_calls_per_day,
            "storage_mb": limits.max_storage_mb,
            "federation": limits.federation_enabled
        },
        "usage": {
            "memories": usage.get('memories', 0),
            "api_calls_today": api_calls_today,
            "storage_bytes": usage.get('bytes', 0)
        }
    }


@app.post("/api/memories")
async def create_memory(request: Request, data: dict):
    """
    Create a memory (subject to storage limits).

    Storage is checked by StorageLimitMiddleware before this runs.
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    # Create memory (mock implementation)
    memory_id = "mem_" + os.urandom(8).hex()

    # Record storage usage
    usage = await metering.get_storage_usage(tenant_id)
    new_memory_count = usage.get('memories', 0) + 1
    await metering.record_storage_usage(
        tenant_id=tenant_id,
        memories=new_memory_count,
        bytes_used=usage.get('bytes', 0) + len(str(data))
    )

    return {
        "id": memory_id,
        "status": "created",
        "tenant_id": tenant_id
    }


@app.get("/api/federation/shared")
async def get_federated_memories(request: Request):
    """
    Access federated memories (Pro/Enterprise only).

    FeatureAccessMiddleware checks for 'federation' feature.
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    # Return federated memories
    return {
        "memories": [
            {"id": "fed_1", "content": "Shared memory 1"},
            {"id": "fed_2", "content": "Shared memory 2"}
        ],
        "count": 2
    }


@app.post("/api/subscription/create")
async def create_subscription(request: Request, tier: PricingTier):
    """Create a new subscription for tenant"""
    tenant_id = request.headers.get("X-Tenant-ID")
    email = request.headers.get("X-User-Email")

    if not tenant_id or not email:
        raise HTTPException(status_code=401, detail="Missing authentication")

    # Check if already has subscription
    existing = await db.get_subscription(tenant_id)
    if existing.get('stripe_customer_id'):
        raise HTTPException(status_code=400, detail="Subscription already exists")

    # Create Stripe customer
    customer = await stripe_client.create_customer(
        email=email,
        tenant_id=tenant_id,
        metadata={"signup_source": "api"}
    )

    # Create subscription
    from continuum.billing.tiers import get_stripe_price_id
    price_id = get_stripe_price_id(tier)

    subscription = await stripe_client.create_subscription(
        customer_id=customer.id,
        price_id=price_id,
        metadata={"tenant_id": tenant_id}
    )

    # Update database
    await db.update_subscription(tenant_id, {
        'tier': tier,
        'stripe_customer_id': customer.id,
        'stripe_subscription_id': subscription.id,
        'status': subscription.status
    })

    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "tier": tier.value
    }


@app.post("/api/subscription/cancel")
async def cancel_subscription(request: Request):
    """Cancel subscription (downgrade to Free tier)"""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    subscription = await db.get_subscription(tenant_id)
    if not subscription.get('stripe_subscription_id'):
        raise HTTPException(status_code=404, detail="No active subscription")

    # Cancel subscription at period end
    await stripe_client.cancel_subscription(
        subscription_id=subscription['stripe_subscription_id'],
        at_period_end=True
    )

    # Update database (will downgrade to Free at period end)
    await db.update_subscription(tenant_id, {
        'status': 'canceled'
    })

    return {
        "status": "canceled",
        "message": "Subscription will end at period end"
    }


@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Called by Stripe to notify about subscription changes, payments, etc.
    """
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        # Verify webhook signature
        event = stripe_client.verify_webhook_signature(
            payload=payload,
            signature=signature
        )

        # Handle event
        result = await stripe_client.handle_webhook_event(event)

        # Update database based on event
        if event['type'] == 'customer.subscription.updated':
            subscription_data = event['data']['object']
            tenant_id = subscription_data['metadata'].get('tenant_id')

            if tenant_id:
                # Update subscription status in database
                await db.update_subscription(tenant_id, {
                    'status': subscription_data['status']
                })

                # If subscription is canceled, downgrade to Free
                if subscription_data['status'] == 'canceled':
                    await db.update_subscription(tenant_id, {
                        'tier': PricingTier.FREE
                    })

        return {"status": "success", "result": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/usage")
async def get_usage_stats(request: Request):
    """Get usage statistics for tenant"""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    # Get all usage metrics
    storage = await metering.get_storage_usage(tenant_id)
    api_calls_today = await metering.get_usage(tenant_id, 'api_calls', period='day')
    api_calls_this_minute = await metering.get_usage(tenant_id, 'api_calls', period='minute')

    tier = await get_tenant_tier(tenant_id)
    limits = get_tier_limits(tier)

    return {
        "tier": tier.value,
        "usage": {
            "memories": {
                "current": storage.get('memories', 0),
                "limit": limits.max_memories,
                "percentage": (storage.get('memories', 0) / limits.max_memories) * 100
            },
            "api_calls": {
                "today": api_calls_today,
                "daily_limit": limits.api_calls_per_day,
                "this_minute": api_calls_this_minute,
                "minute_limit": limits.api_calls_per_minute
            },
            "storage": {
                "bytes": storage.get('bytes', 0),
                "mb": storage.get('bytes', 0) / (1024 * 1024),
                "limit_mb": limits.max_storage_mb
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
