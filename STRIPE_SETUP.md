# Stripe Payment Links Setup

## Current Status
- ✅ Products created in Stripe test mode
- ⏳ Need to create payment links and update code

## Products Created
1. **CONTINUUM Free** - $0/month (price_1SeyaPKHlP0BRMydSMf8aqAP)
2. **CONTINUUM Pro** - $29/month (price_1SeyYeKHlP0BRMyd6SKDUHvy)
3. **CONTINUUM Enterprise** - Custom pricing (price_1SeybZKHlP0BRMydcIQkzgQP)
4. **CONTINUUM Support Donation** - $10 one-time (needs payment link)

## Steps to Complete

### 1. Create Payment Links in Stripe
Go to: https://dashboard.stripe.com/test/payment-links

**For Donation ($10):**
1. Click "Create payment link"
2. Select "CONTINUUM Support Donation" product (or create new)
3. **Product Name:** `CONTINUUM Support Donation`
4. **Description (for checkout page):**
   ```
   "Support the development of CONTINUUM - AI Memory Infrastructure. Your $10 contribution helps us maintain and improve this open-source project while keeping the FREE tier available for everyone. Remove donation reminders instantly upon payment."
   ```
5. Verify price is $10.00 one-time
6. Click "Create link"
7. Copy the `buy.stripe.com/test_XXXXXX` URL

**For PRO Upgrade ($29/mo):**
1. Click "Create payment link"
2. Select "CONTINUUM Pro" product
3. Verify price is $29/month recurring
4. Click "Create link"
5. Copy the `buy.stripe.com/test_XXXXXX` URL

### 2. Update Code with Real Links

**File: `continuum/api/server.py` (line 55)**
```python
DONATION_NAG_MESSAGE = "Support CONTINUUM! Donate $10 to remove this message: https://buy.stripe.com/test_REPLACE_WITH_DONATION_LINK"
```
Replace `test_REPLACE_WITH_DONATION_LINK` with your donation link ID.

**File: `continuum/static/index.html` (line 114)**
```html
<a href="https://buy.stripe.com/test_REPLACE_WITH_DONATION_LINK"
```
Replace `test_REPLACE_WITH_DONATION_LINK` with your donation link ID.

**File: `continuum/static/index.html` (line ~230)**
Search for the PRO upgrade button and replace placeholder with PRO link.

### 3. Before Going Live

When ready to switch from test mode to live:

1. **Create LIVE payment links** in Stripe production mode
2. **Update all links** from `buy.stripe.com/test_` to `buy.stripe.com/` (remove `test_`)
3. **Update API keys** from `sk_test_` to `sk_live_`
4. **Test the entire flow** with a real card
5. **Publish new version** to PyPI

## Quick Find & Replace

For testing (after getting real test links):
```bash
cd ~/Projects/continuum
grep -r "REPLACE_WITH_DONATION_LINK" continuum/
grep -r "test_PLACEHOLDER" continuum/
```

Replace all instances with your real Stripe payment link IDs.
