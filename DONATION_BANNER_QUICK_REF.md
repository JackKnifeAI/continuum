# Donation Banner - Quick Reference

## What Was Built

A two-layer persistent donation nag system for FREE tier users:

1. **API Response Header:** Every FREE tier API call includes `X-Continuum-Support` header
2. **Dashboard Banner:** Yellow banner at top of dashboard for FREE tier (persistent, no dismiss)

---

## User Experience

### FREE Tier User View

#### Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ 💛 Love CONTINUUM? Help us keep it free and open source!    │
│ Donate $10 or Upgrade to PRO ($29/mo) for unlimited calls  │
└─────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│                    CONTINUUM Dashboard                      │
│                  [Rest of Dashboard Content]                │
└────────────────────────────────────────────────────────────┘
```

#### API Response (curl)
```bash
$ curl -i http://localhost:8420/v1/recall -H "X-API-Key: test"

HTTP/1.1 200 OK
X-Continuum-Support: Support CONTINUUM: Donate $10 https://... or Upgrade to PRO $29/mo https://...
X-RateLimit-Limit-Day: 100
X-RateLimit-Remaining-Day: 87
X-Tier: free
Content-Type: application/json

{"recall": [...]}
```

### PRO Tier User View
- No banner
- No `X-Continuum-Support` header
- Normal dashboard experience

---

## Files Changed

### 1. `/continuum/api/server.py` (Lines 53-86)
**Before:**
```python
DONATION_NAG_HEADER = "X-Continuum-Donate"
DONATION_NAG_MESSAGE = "Support CONTINUUM! Donate..."

class DonationNagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/v1/"):
            response.headers[DONATION_NAG_HEADER] = DONATION_NAG_MESSAGE
        return response
```

**After:**
```python
DONATION_LINK = "https://buy.stripe.com/test_7sYaEYc3xbgygTx9AA"
PRO_UPGRADE_LINK = "https://buy.stripe.com/test_aFaeVeaZtbgy0Uz3BB"

DONATION_NAG_HEADER = "X-Continuum-Support"
DONATION_NAG_MESSAGE = f"Support CONTINUUM: Donate $10 {DONATION_LINK} or Upgrade to PRO $29/mo {PRO_UPGRADE_LINK}"

class DonationNagMiddleware(BaseHTTPMiddleware):
    """Add donation reminder header to all FREE tier API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/v1/"):
            return response

        tier = getattr(request.state, "tier", "free").lower()
        if tier == "free":
            response.headers[DONATION_NAG_HEADER] = DONATION_NAG_MESSAGE
        return response
```

**Key Changes:**
- Tier-aware (checks `request.state.tier`)
- Proper Stripe checkout links
- Professional header name (`X-Continuum-Support`)
- Only adds header for FREE tier

### 2. `/continuum/billing/middleware.py` (Line 79)
**Added:**
```python
# Store tier in request state for downstream middleware (e.g., DonationNagMiddleware)
request.state.tier = tier.value
```

**Why:** Allows `DonationNagMiddleware` to know the user's tier

### 3. `/continuum/static/index.html`

**Added Banner HTML (Lines 58-67):**
```html
<!-- Donation Banner (FREE tier only) -->
<div id="donation-banner" class="hidden bg-yellow-100 border-b-2 border-yellow-400 px-4 py-3 text-center">
    <p class="text-sm text-yellow-800">
        <span class="font-semibold">💛 Love CONTINUUM?</span> Help us keep it free and open source!
        <a href="https://buy.stripe.com/test_7sYaEYc3xbgygTx9AA" target="_blank" class="underline font-semibold hover:text-yellow-900">Donate $10</a>
        or
        <a href="https://buy.stripe.com/test_aFaeVeaZtbgy0Uz3BB" target="_blank" class="underline font-semibold hover:text-yellow-900">Upgrade to PRO ($29/mo)</a>
        for unlimited API calls and support.
    </p>
</div>
```

**Added JavaScript Logic (Lines 490-493):**
```javascript
// Show/hide donation banner (persistent for FREE tier)
if (tierConfig.showDonation) {
    showElement('donation-banner');
}
```

**Banner Styling:**
- Yellow (`bg-yellow-100`) - visible but not harsh
- Border definition (`border-b-2 border-yellow-400`)
- Center text alignment
- Mobile responsive
- Tailwind CSS

---

## Testing Quick Checklist

- [ ] Access dashboard as FREE tier user → See yellow banner at top
- [ ] Access dashboard as PRO tier user → No banner visible
- [ ] Make API call as FREE tier → See `X-Continuum-Support` header in response
- [ ] Make API call as PRO tier → No `X-Continuum-Support` header
- [ ] Click donation link → Stripe checkout page opens (test mode)
- [ ] Click upgrade link → Stripe checkout page opens (test mode)
- [ ] Refresh page → Banner still visible (persistent)
- [ ] Browser console → No JavaScript errors

---

## Stripe Links (Test Mode)

**Donation Button ($10 one-time):**
```
https://buy.stripe.com/test_7sYaEYc3xbgygTx9AA
```

**PRO Upgrade ($29/month):**
```
https://buy.stripe.com/test_aFaeVeaZtbgy0Uz3BB
```

**Switch to Production:**
Update these links in:
- `continuum/api/server.py` (lines 57-58)
- `continuum/static/index.html` (lines 62, 64)

---

## Deployment Steps

1. **Verify changes:**
   ```bash
   cd ~/Projects/continuum
   git diff continuum/api/server.py
   git diff continuum/billing/middleware.py
   git diff continuum/static/index.html
   ```

2. **Test locally:**
   ```bash
   # Start server
   python -m continuum.api.server

   # Test FREE tier
   curl -i http://localhost:8420/v1/health

   # Visit dashboard
   http://localhost:8420/dashboard
   ```

3. **Commit changes:**
   ```bash
   git add continuum/api/server.py continuum/billing/middleware.py continuum/static/index.html
   git commit -m "feat: Add persistent donation banner for FREE tier users"
   ```

---

## Troubleshooting

### Banner Not Showing
- Check browser console for errors
- Verify `tier` is set to `"free"` in dashboard stats API response
- Ensure JavaScript is enabled

### Header Not Appearing
- Verify request goes to `/v1/*` endpoint (not `/api/*`)
- Check `request.state.tier` is being set by `BillingMiddleware`
- Confirm API key is associated with FREE tier

### Links Not Working
- Verify Stripe links are correct (test mode vs production)
- Check for CORS issues if testing from different domain
- Confirm links are being served with `target="_blank"`

---

## Notes

### Why This Works
1. **Always visible:** Banner at top, no dismiss option
2. **Multiple touchpoints:** Dashboard + API headers
3. **Clear CTAs:** Both donation and upgrade paths
4. **Open-source friendly:** "Help us keep it free" message
5. **Tier-aware:** Only bothers FREE tier users

### Tone & Messaging
- Friendly ("Love CONTINUUM?") not aggressive
- Open-source ethos ("Help us keep it free")
- Clear value prop ("unlimited API calls and support")
- Non-blocking (doesn't interfere with usage)

### Monetization Strategy
**FREE → PRO Conversion Funnel:**
1. User sees banner (awareness)
2. User clicks donation or upgrade link (interest)
3. User lands on Stripe checkout (decision)
4. User pays (conversion)

**Metrics to Track:**
- Banner impression rate (should be 100% for FREE tier)
- Click-through rate on donation link
- Click-through rate on upgrade link
- Conversion rate (clicks → paid)
- Average donation amount

---

## Production Checklist

Before Christmas v1.0.0 launch:

- [ ] Test with staging database (real tier data)
- [ ] Verify banner styling on mobile devices
- [ ] Check Stripe links load correctly (test mode)
- [ ] Monitor API response headers in production
- [ ] Set up analytics tracking for banner clicks
- [ ] Create support docs for handling donation questions
- [ ] Brief support team on new banner

---

## Support

Questions or issues? Check:
- `/DONATION_BANNER_COMPLETE.md` - Full implementation docs
- `/continuum/api/server.py` - Header logic
- `/continuum/billing/middleware.py` - Tier detection
- `/continuum/static/index.html` - UI component

---

**Status:** ✅ Ready for Christmas v1.0.0 launch
**Files Modified:** 3
**Lines Added:** ~30
**Breaking Changes:** None
