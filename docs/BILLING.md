# CONTINUUM Cloud - Billing & Stripe Integration

Complete billing infrastructure for CONTINUUM Cloud with Stripe integration, usage metering, and tier-based access control.

## Overview

The billing system provides:

- **Stripe Integration**: Customer management, subscriptions, webhooks
- **Usage Metering**: Track API calls, storage, federation contributions
- **Rate Limiting**: Enforce tier-based limits on API usage
- **Feature Access Control**: Tier-based feature gating
- **FastAPI Middleware**: Automatic billing enforcement in the request/response cycle

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  BillingMiddleware                                           │
│  ├─ Rate Limiting                                            │
│  ├─ Usage Recording                                          │
│  └─ Concurrent Request Tracking                              │
├─────────────────────────────────────────────────────────────┤
│  FeatureAccessMiddleware                                     │
│  └─ Tier-based Feature Gating                                │
├─────────────────────────────────────────────────────────────┤
│  StorageLimitMiddleware                                      │
│  └─ Storage Quota Enforcement                                │
├─────────────────────────────────────────────────────────────┤
│  Application Routes                                          │
│  ├─ /api/memories                                            │
│  ├─ /api/federation                                          │
│  └─ /api/search                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐
  │ UsageMetering│    │ RateLimiter  │    │ StripeClient   │
  └─────────────┘    └──────────────┘    └────────────────┘
         │                                         │
         ▼                                         ▼
  ┌─────────────┐                         ┌────────────────┐
  │  SQLite DB  │                         │  Stripe API    │
  │  (Usage)    │                         │                │
  └─────────────┘                         └────────────────┘
```

## Pricing Tiers

### Free Tier ($0/month)

**Limits:**
- 1,000 memories
- 100 API calls/day
- 10 API calls/minute
- 100 MB storage
- 2 concurrent requests

**Features:**
- ✅ Semantic search
- ❌ Federation
- ❌ Real-time sync
- Community support

### Pro Tier ($29/month)

**Limits:**
- 100,000 memories
- 10,000 API calls/day
- 100 API calls/minute
- 10 GB storage
- 10 concurrent requests

**Features:**
- ✅ Semantic search
- ✅ Federation (normal priority)
- ✅ Real-time sync
- Email support (24hr SLA)
- 99% uptime SLA

**Overage Pricing:**
- $0.10 per 1,000 API calls over quota

### Enterprise Tier (Custom Pricing)

**Limits:**
- 10,000,000 memories
- 1,000,000 API calls/day
- 1,000 API calls/minute
- 1 TB storage
- 100 concurrent requests

**Features:**
- ✅ All features
- ✅ Federation (critical priority)
- ✅ Dedicated support
- Priority support (1hr SLA)
- 99.9% uptime SLA
- Custom contract terms

## Installation

### 1. Install Stripe SDK

```bash
pip install stripe
```

### 2. Configure Environment Variables

```bash
# Stripe API Keys
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_PUBLISHABLE_KEY="pk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."

# Stripe Price IDs (from Stripe Dashboard)
export STRIPE_PRICE_FREE="price_free"
export STRIPE_PRICE_PRO="price_1234567890"
export STRIPE_PRICE_ENTERPRISE="price_0987654321"
```

### 3. Create Stripe Products

In the Stripe Dashboard, create products and prices:

**Free Tier:**
- Product: "CONTINUUM Free"
- Price: $0/month
- Price ID: `price_free`

**Pro Tier:**
- Product: "CONTINUUM Pro"
- Price: $29/month
- Metered billing for overages: $0.10 per 1,000 API calls
- Price IDs: `price_pro_monthly`, `price_pro_api_calls`

**Enterprise Tier:**
- Product: "CONTINUUM Enterprise"
- Custom pricing (set per customer)
- Price ID: `price_enterprise_custom`

## Usage

### Initialize Billing Components

```python
from continuum.billing import (
    StripeClient,
    UsageMetering,
    RateLimiter,
    BillingMiddleware,
    FeatureAccessMiddleware,
    StorageLimitMiddleware
)

# Initialize components
stripe_client = StripeClient()
metering = UsageMetering()
rate_limiter = RateLimiter(metering)

# Function to get tenant's pricing tier
async def get_tenant_tier(tenant_id: str) -> PricingTier:
    # Query database or cache for tenant's subscription tier
    # Example implementation:
    subscription = await db.get_subscription(tenant_id)
    return subscription.tier

# Add middleware to FastAPI app
app.add_middleware(
    BillingMiddleware,
    metering=metering,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier,
    exclude_paths=["/health", "/docs"]
)

app.add_middleware(
    FeatureAccessMiddleware,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier,
    feature_map={
        "/api/federation": "federation",
        "/api/realtime": "realtime_sync"
    }
)

app.add_middleware(
    StorageLimitMiddleware,
    metering=metering,
    rate_limiter=rate_limiter,
    get_tenant_tier=get_tenant_tier
)
```

### Create Customer and Subscription

```python
from continuum.billing import StripeClient, PricingTier, get_stripe_price_id

stripe_client = StripeClient()

# Create customer
customer = await stripe_client.create_customer(
    email="user@example.com",
    tenant_id="tenant_123",
    metadata={"source": "web_signup"}
)

# Create Pro subscription
price_id = get_stripe_price_id(PricingTier.PRO)
subscription = await stripe_client.create_subscription(
    customer_id=customer.id,
    price_id=price_id,
    trial_days=14  # Optional 14-day trial
)

print(f"Subscription created: {subscription.id}")
print(f"Status: {subscription.status}")
```

### Record Usage

```python
from continuum.billing import UsageMetering

metering = UsageMetering()

# Record API call
await metering.record_api_call(
    tenant_id="tenant_123",
    endpoint="/api/memories/search"
)

# Record storage usage
await metering.record_storage_usage(
    tenant_id="tenant_123",
    memories=5000,
    embeddings=5000,
    bytes_used=50_000_000  # 50 MB
)

# Record federation contribution
await metering.record_federation_contribution(
    tenant_id="tenant_123",
    shared_memories=10
)

# Get current usage
api_calls_today = await metering.get_usage("tenant_123", "api_calls", period="day")
storage_usage = await metering.get_storage_usage("tenant_123")
print(f"API calls today: {api_calls_today}")
print(f"Storage: {storage_usage}")
```

### Check Rate Limits

```python
from continuum.billing import RateLimiter, PricingTier

rate_limiter = RateLimiter(metering)

# Check if request is allowed
allowed, error_msg = await rate_limiter.check_rate_limit(
    tenant_id="tenant_123",
    tier=PricingTier.PRO
)

if not allowed:
    raise HTTPException(status_code=429, detail=error_msg)

# Check storage limit
allowed, error_msg = await rate_limiter.check_storage_limit(
    tenant_id="tenant_123",
    tier=PricingTier.PRO
)

if not allowed:
    raise HTTPException(status_code=507, detail=error_msg)

# Check feature access
allowed, error_msg = await rate_limiter.check_feature_access(
    tier=PricingTier.FREE,
    feature="federation"
)

if not allowed:
    raise HTTPException(status_code=403, detail=error_msg)
```

### Handle Webhooks

```python
from fastapi import Request, HTTPException
from continuum.billing import StripeClient

stripe_client = StripeClient()

@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        # Verify webhook signature
        event = stripe_client.verify_webhook_signature(
            payload=payload,
            signature=signature
        )

        # Handle event
        result = await stripe_client.handle_webhook_event(event)

        return {"status": "success", "result": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Webhook Events

The system handles these Stripe webhook events:

### Customer Events
- `customer.created` - New customer created
- `customer.updated` - Customer details updated
- `customer.deleted` - Customer deleted

### Subscription Events
- `customer.subscription.created` - New subscription created
- `customer.subscription.updated` - Subscription changed (tier upgrade/downgrade, status change)
- `customer.subscription.deleted` - Subscription canceled

### Payment Events
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed (implement retry logic)
- `payment_method.attached` - Payment method added

## Rate Limit Headers

API responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit-Day: 10000
X-RateLimit-Limit-Minute: 100
X-RateLimit-Remaining-Day: 9543
X-RateLimit-Remaining-Minute: 87
X-RateLimit-Reset: 1640000000
X-Tier: pro
X-Request-Duration-Ms: 145
```

## Error Responses

### Rate Limit Exceeded (429)

```json
{
  "error": "Rate limit exceeded (100 calls/minute)",
  "tier": "pro",
  "upgrade_url": "/billing/upgrade"
}
```

### Storage Limit Exceeded (507)

```json
{
  "error": "Storage limit exceeded (10000 MB)",
  "current_usage": {
    "memories": 95000,
    "embeddings": 95000,
    "bytes": 10500000000
  },
  "tier": "pro",
  "upgrade_url": "/billing/upgrade"
}
```

### Feature Not Available (403)

```json
{
  "error": "Feature 'federation' not available on free tier",
  "feature": "federation",
  "current_tier": "free",
  "upgrade_url": "/billing/upgrade"
}
```

## Security

### PCI Compliance

- **Never store credit card data** - Use Stripe.js and Stripe Elements for card collection
- **Server-side only** - Stripe secret key must never be exposed to clients
- **Use publishable key** - Only use `pk_live_...` on the client side
- **Webhook signatures** - Always verify webhook signatures to prevent replay attacks

### API Key Storage

```python
# GOOD: Use environment variables
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# BAD: Never hardcode API keys
stripe.api_key = "sk_live_..."  # ❌ DON'T DO THIS
```

### Webhook Signature Verification

```python
# ALWAYS verify webhook signatures
event = stripe_client.verify_webhook_signature(
    payload=payload,
    signature=signature
)

# Never skip verification, even in development
```

### Rate Limit Bypass Prevention

- Middleware validates tenant ID from authenticated token
- Cannot spoof tenant ID via headers alone
- Each request is tracked with authenticated identity

## Database Schema

Usage data is stored in SQLite (or other backend):

```sql
-- Usage tracking
CREATE TABLE usage_records (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,  -- 'api_calls', 'storage', 'federation'
    metric_value INTEGER NOT NULL,
    period TEXT NOT NULL,       -- '2024-01-15' or '2024-01-15-14-30'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_period (tenant_id, period)
);

-- Subscription tracking
CREATE TABLE subscriptions (
    tenant_id TEXT PRIMARY KEY,
    stripe_customer_id TEXT NOT NULL,
    stripe_subscription_id TEXT,
    tier TEXT NOT NULL,         -- 'free', 'pro', 'enterprise'
    status TEXT NOT NULL,       -- 'active', 'canceled', etc.
    current_period_start DATETIME,
    current_period_end DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Testing

### Test Mode

Use Stripe test mode for development:

```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_test_..."
```

### Test Cards

Stripe provides test card numbers:

- **Success**: `4242 4242 4242 4242`
- **Declined**: `4000 0000 0000 0002`
- **Requires 3D Secure**: `4000 0027 6000 3184`

### Webhook Testing

Use Stripe CLI to test webhooks locally:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/billing/webhook

# Trigger test events
stripe trigger customer.subscription.created
stripe trigger invoice.payment_failed
```

## Monitoring

### Key Metrics to Track

1. **Revenue Metrics**
   - MRR (Monthly Recurring Revenue)
   - Churn rate
   - Upgrade/downgrade rates
   - Average revenue per user (ARPU)

2. **Usage Metrics**
   - API calls per tier
   - Storage usage trends
   - Rate limit hit rate
   - Feature adoption rates

3. **Customer Health**
   - Payment success rate
   - Trial conversion rate
   - Time to first value
   - Support ticket volume by tier

### Logging

```python
import logging

# Enable billing logs
logging.getLogger('continuum.billing').setLevel(logging.INFO)

# Log important events
logger.info(f"Subscription created: {subscription_id}")
logger.warning(f"Rate limit exceeded for {tenant_id}")
logger.error(f"Payment failed for invoice {invoice_id}")
```

## Common Workflows

### User Signs Up (Free Tier)

1. User creates account → `tenant_id` assigned
2. Default to Free tier (no Stripe customer yet)
3. User starts using API within Free tier limits

### User Upgrades to Pro

1. User enters payment details → Stripe.js creates `payment_method`
2. Backend creates Stripe customer
3. Attach payment method to customer
4. Create subscription with Pro price ID
5. Update tenant tier in database
6. User immediately gets Pro tier limits

### User Exceeds Pro Tier Limits

1. API call exceeds daily limit
2. BillingMiddleware returns 429 error with upgrade prompt
3. Usage beyond quota can be billed as overage (metered billing)
4. User upgrades to Enterprise or pays overage fees

### Subscription Renewal

1. Stripe automatically charges at period end
2. `invoice.payment_succeeded` webhook received
3. Update subscription period in database
4. Continue service

### Payment Failure

1. Stripe attempts payment, fails
2. `invoice.payment_failed` webhook received
3. Send email notification to user
4. Stripe retries payment (configurable)
5. If all retries fail, suspend service or downgrade to Free

## Roadmap

### Phase 1: Core Billing ✅
- Stripe integration
- Usage metering
- Rate limiting
- Tier enforcement

### Phase 2: Advanced Features
- Usage-based pricing for API overages
- Annual billing discount (20% off)
- Team/organization billing
- Invoice management dashboard

### Phase 3: Analytics & Optimization
- Revenue analytics dashboard
- Churn prediction
- Usage forecasting
- Custom enterprise contracts

## Support

For billing issues:
- Email: billing@continuum.ai
- Stripe Dashboard: https://dashboard.stripe.com
- Documentation: https://stripe.com/docs

## License

CONTINUUM Cloud Billing System
Copyright (c) 2024
