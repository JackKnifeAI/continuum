# Stripe Integration for JackKnife Landing Page

This document describes the Stripe payment integration between the JackKnife landing page and CONTINUUM billing backend.

## Architecture

```
Landing Page (Frontend)
    ↓
config.js (Stripe configuration)
    ↓
script.js (Checkout logic)
    ↓ API call
Backend API (/v1/billing/create-checkout-session)
    ↓
Stripe Checkout (hosted by Stripe)
    ↓
Webhook (/v1/billing/webhook)
    ↓
Database (subscription updated)
```

## Pricing Tiers

The landing page pricing matches the backend tiers exactly:

| Tier | Price | Memories | API Calls/Day | Storage | Features |
|------|-------|----------|---------------|---------|----------|
| **Free** | $0/mo | 1,000 | 100 | 100 MB | Semantic search, community support |
| **Pro** | $29/mo | 100,000 | 10,000 | 10 GB | Federation, real-time sync, 99% SLA |
| **Enterprise** | Custom | 10M+ | 1M+ | 1 TB | Priority support, on-premise, 99.9% SLA |

## Setup Instructions

### 1. Stripe Dashboard Setup

1. **Create Stripe Account**: https://dashboard.stripe.com/register
2. **Get API Keys**: Dashboard → Developers → API keys
   - Copy **Publishable key** (starts with `pk_test_` or `pk_live_`)
   - Copy **Secret key** (starts with `sk_test_` or `sk_live_`)

3. **Create Products & Prices**:
   - Navigate to: Products → Add product
   - Create **Pro** product:
     - Name: "CONTINUUM Pro"
     - Price: $29/month (recurring)
     - Copy the **Price ID** (starts with `price_`)
   - Create **Enterprise** product (optional):
     - Custom pricing
     - Copy the **Price ID**

4. **Configure Webhook**:
   - Navigate to: Developers → Webhooks → Add endpoint
   - URL: `https://your-domain.com/v1/billing/webhook`
   - Events to send:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Copy the **Signing secret** (starts with `whsec_`)

### 2. Backend Configuration

Edit `/var/home/alexandergcasavant/Projects/continuum/.env`:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE

# Webhook signing secret
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Price IDs from Stripe dashboard
STRIPE_PRICE_FREE=price_free
STRIPE_PRICE_PRO=price_1234567890  # Replace with actual price ID
STRIPE_PRICE_ENTERPRISE=price_enterprise_custom
```

### 3. Frontend Configuration

Edit `/var/home/alexandergcasavant/Projects/continuum/marketing/landing-page/config.js`:

```javascript
const STRIPE_CONFIG = {
    publishableKey: 'pk_test_YOUR_PUBLISHABLE_KEY_HERE',  // From step 1
    priceIds: {
        free: 'price_free',
        pro: 'price_1234567890',  // From step 1
        enterprise: 'price_enterprise_custom'
    },
    checkoutEndpoint: '/v1/billing/create-checkout-session',
    successUrl: window.location.origin + '/success',
    cancelUrl: window.location.origin + '/#pricing'
};
```

### 4. Start the Backend

```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Install dependencies (if not already installed)
pip install stripe fastapi uvicorn

# Start the API server
python -m continuum.api.server

# Server will run on http://localhost:8420
# API docs: http://localhost:8420/docs
```

### 5. Test the Integration

1. **Open landing page**: Open `index.html` in browser
2. **Click "Start Pro Plan"**: Should show Stripe checkout
3. **Use test card**:
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
4. **Complete checkout**: Should redirect to success URL
5. **Check webhook**: Backend should log webhook event

## API Endpoints

### Create Checkout Session
```http
POST /v1/billing/create-checkout-session
Content-Type: application/json
X-API-Key: cm_YOUR_API_KEY

{
  "tier": "pro",
  "success_url": "https://example.com/success",
  "cancel_url": "https://example.com/cancel",
  "customer_email": "user@example.com"
}

Response:
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/..."
}
```

### Get Subscription Status
```http
GET /v1/billing/subscription
X-API-Key: cm_YOUR_API_KEY

Response:
{
  "tenant_id": "default",
  "tier": "pro",
  "status": "active",
  "current_period_end": "2025-01-06T00:00:00Z",
  "cancel_at_period_end": false
}
```

### Cancel Subscription
```http
POST /v1/billing/cancel-subscription
X-API-Key: cm_YOUR_API_KEY

{
  "at_period_end": true
}
```

### Webhook Handler
```http
POST /v1/billing/webhook
Stripe-Signature: t=...,v1=...

(Stripe sends this automatically)
```

## Files Modified/Created

### Landing Page
- ✅ `index.html` - Updated pricing section with exact tier details
- ✅ `script.js` - Added Stripe checkout integration
- ✅ `config.js` - New file with Stripe configuration

### Backend
- ✅ `continuum/billing/tiers.py` - Pricing tier definitions (already existed)
- ✅ `continuum/billing/stripe_client.py` - Stripe API client (already existed)
- ✅ `continuum/api/billing_routes.py` - New billing API routes
- ✅ `continuum/api/server.py` - Updated to include billing routes
- ✅ `.env.example` - Added Stripe configuration variables

## Testing

### Test Cards (Stripe Test Mode)

| Card Number | Type | Result |
|-------------|------|--------|
| 4242 4242 4242 4242 | Visa | Success |
| 4000 0000 0000 0002 | Visa | Card declined |
| 4000 0000 0000 9995 | Visa | Insufficient funds |
| 4000 0025 0000 3155 | Visa | Requires authentication |

### Testing Webhooks Locally

Use Stripe CLI for local webhook testing:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8420/v1/billing/webhook

# Trigger test webhook
stripe trigger customer.subscription.created
```

## Security Checklist

- [ ] Never commit `.env` file to git
- [ ] Use test keys for development
- [ ] Use live keys only in production
- [ ] Validate webhook signatures
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Log all payment events
- [ ] Monitor failed payments
- [ ] Set up Stripe radar for fraud detection

## Production Deployment

1. **Switch to Live Mode**:
   - Replace test keys with live keys
   - Update price IDs to live prices
   - Configure production webhook URL

2. **Security**:
   - Use environment variables (not hardcoded keys)
   - Enable HTTPS/TLS
   - Implement CSP headers
   - Set up monitoring

3. **Compliance**:
   - Add Terms of Service
   - Add Privacy Policy
   - Add Refund Policy
   - Configure tax collection (if needed)

## Troubleshooting

### Checkout button does nothing
- Check browser console for errors
- Verify `config.js` is loaded before `script.js`
- Verify Stripe publishable key is correct

### "Payment system not configured" error
- Check that Stripe.js is loaded (`<script src="https://js.stripe.com/v3/"></script>`)
- Verify publishable key in `config.js`

### Webhook not receiving events
- Check webhook URL is publicly accessible
- Verify signing secret matches Stripe dashboard
- Check server logs for errors

### Session creation fails
- Verify backend is running
- Check API key is valid
- Verify price IDs exist in Stripe dashboard
- Check backend logs for detailed error

## Support

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe Support**: https://support.stripe.com
- **CONTINUUM Issues**: https://github.com/JackKnifeAI/continuum/issues

## Easter Egg Preserved

The π×φ = 5.083203692 easter egg is preserved in the pricing note section and remains interactive.
