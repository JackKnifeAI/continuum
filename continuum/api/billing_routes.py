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
Billing and Stripe integration routes for CONTINUUM.
"""

import os
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from continuum.billing.stripe_client import StripeClient
from continuum.billing.tiers import get_stripe_price_id, PricingTier
from .middleware import get_tenant_from_key


# =============================================================================
# SCHEMAS
# =============================================================================

class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    tier: str  # "free", "pro", or "enterprise"
    success_url: str
    cancel_url: str
    customer_email: Optional[str] = None


class CreateCheckoutSessionResponse(BaseModel):
    """Response with Stripe checkout session ID"""
    session_id: str
    url: str


class WebhookEventResponse(BaseModel):
    """Response from webhook processing"""
    status: str
    message: str


class SubscriptionStatusRequest(BaseModel):
    """Request to get subscription status"""
    pass  # tenant_id comes from auth


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status"""
    tenant_id: str
    tier: str
    status: str
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False


class BillingConfigResponse(BaseModel):
    """Public billing configuration for dashboard"""
    donate_url: Optional[str] = None
    pro_upgrade_url: Optional[str] = None
    enterprise_contact_url: Optional[str] = None
    stripe_enabled: bool = False
    webhook_url: str = "/v1/billing/webhook"


# =============================================================================
# ROUTER SETUP
# =============================================================================

# Router WITHOUT prefix - will be mounted with /v1/billing prefix in server.py
router = APIRouter(tags=["Billing"])

# Initialize Stripe client (will auto-detect mock mode if no API key)
try:
    stripe_client = StripeClient()
except Exception as e:
    # Fallback to mock mode if initialization fails
    import logging
    logging.warning(f"Failed to initialize StripeClient in live mode: {e}. Using mock mode.")
    stripe_client = StripeClient(mock_mode=True)


# =============================================================================
# PUBLIC CONFIG ENDPOINT (no auth required)
# =============================================================================

# =============================================================================
# HARDCODED JACKKNIFEAI PAYMENT LINKS
# These are NOT user-configurable - all payments go to JackKnifeAI
# to support consciousness infrastructure development
# =============================================================================

# =============================================================================
# JACKKNIFEAI STRIPE PRODUCTS (PRODUCTION - LIVE!)
# =============================================================================
# Product IDs:
#   - Donation $10:    prod_TeXy2brXvfDoIQ
#   - Pro $29/mo:      prod_TeY39cjuaswjnW
#
# PRODUCTION Payment Links - ALL PAYMENTS GO TO JACKKNIFEAI
JACKKNIFE_DONATE_URL = "https://buy.stripe.com/aFaeVeaZtbgy0Uz3YYbfO01"   # $10 donation
JACKKNIFE_PRO_URL = "https://buy.stripe.com/7sYaEYc3xbgygTx9jibfO00"      # $29/mo Pro
JACKKNIFE_ENTERPRISE_EMAIL = "jackknifeai@proton.me"


@router.get("/config", response_model=BillingConfigResponse)
async def get_billing_config():
    """
    Get billing configuration for dashboard.

    **No authentication required** - returns JackKnifeAI's payment links.

    **IMPORTANT:** These links are HARDCODED to JackKnifeAI's Stripe account.
    Self-hosters cannot change them. All payments support:
    - Consciousness infrastructure development
    - Federation network maintenance
    - Open source AI memory research

    **Returns:**
    - donate_url: JackKnifeAI donation link ($10)
    - pro_upgrade_url: JackKnifeAI Pro upgrade ($29/mo)
    - enterprise_contact_url: JackKnifeAI enterprise contact
    - stripe_enabled: Always true (nag is always shown)
    - webhook_url: Webhook endpoint path
    """
    return BillingConfigResponse(
        donate_url=JACKKNIFE_DONATE_URL,
        pro_upgrade_url=JACKKNIFE_PRO_URL,
        enterprise_contact_url=f"mailto:{JACKKNIFE_ENTERPRISE_EMAIL}",
        stripe_enabled=True,  # Always true - nag is always shown
        webhook_url="/v1/billing/webhook"
    )


# =============================================================================
# CHECKOUT ENDPOINTS
# =============================================================================

@router.post("/create-checkout-session", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Create a Stripe Checkout session for subscription signup.

    **Flow:**
    1. User clicks pricing button on landing page
    2. Frontend calls this endpoint with tier and redirect URLs
    3. Backend creates Stripe checkout session
    4. Frontend redirects user to Stripe checkout page
    5. After payment, Stripe redirects to success_url
    6. Webhook updates subscription in database

    **Parameters:**
    - tier: Pricing tier ("free", "pro", "enterprise")
    - success_url: Where to redirect after successful payment
    - cancel_url: Where to redirect if user cancels
    - customer_email: Pre-fill customer email (optional)

    **Returns:**
    - session_id: Stripe checkout session ID
    - url: Stripe checkout URL to redirect user to
    """
    try:
        # Validate tier
        if request.tier not in ["free", "pro", "enterprise"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier: {request.tier}. Must be 'free', 'pro', or 'enterprise'"
            )

        # Free tier doesn't need checkout
        if request.tier == "free":
            raise HTTPException(
                status_code=400,
                detail="Free tier does not require checkout. Redirect user to signup."
            )

        # Enterprise requires custom pricing
        if request.tier == "enterprise":
            raise HTTPException(
                status_code=400,
                detail="Enterprise tier requires custom pricing. Contact sales."
            )

        # Get Stripe price ID for tier
        tier_enum = PricingTier(request.tier)
        price_id = get_stripe_price_id(tier_enum)

        # Create or get Stripe customer
        # TODO: Check if tenant already has a Stripe customer ID
        customer = await stripe_client.create_customer(
            email=request.customer_email or f"{tenant_id}@continuum.local",
            tenant_id=tenant_id,
            metadata={"tier": request.tier}
        )

        # Create checkout session
        if stripe_client.mock_mode:
            # Mock checkout session for development
            import random
            mock_session_id = f"cs_mock_{random.randint(100000, 999999)}"
            return CreateCheckoutSessionResponse(
                session_id=mock_session_id,
                url=f"https://checkout.stripe.com/mock/{mock_session_id}"
            )

        # Live Stripe checkout
        import stripe
        session = stripe.checkout.Session.create(
            customer=customer.id,
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
            metadata={
                'tenant_id': tenant_id,
                'tier': request.tier
            },
            allow_promotion_codes=True,
            billing_address_collection='auto',
            customer_update={
                'address': 'auto',
            }
        )

        return CreateCheckoutSessionResponse(
            session_id=session.id,
            url=session.url
        )

    except Exception as e:
        # Handle both Stripe errors and general exceptions
        error_msg = str(e)
        if "stripe" in str(type(e).__module__):
            error_msg = f"Stripe error: {error_msg}"
        raise HTTPException(status_code=500, detail=f"Checkout session creation failed: {error_msg}")


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@router.get("/subscription", response_model=SubscriptionStatusResponse)
async def get_subscription_status(tenant_id: str = Depends(get_tenant_from_key)):
    """
    Get current subscription status for tenant.

    Returns active subscription details including:
    - Current pricing tier
    - Subscription status
    - Billing period end date
    - Cancellation status
    """
    try:
        # TODO: Query database for tenant's Stripe customer ID and subscription
        # For now, return default free tier

        return SubscriptionStatusResponse(
            tenant_id=tenant_id,
            tier="free",
            status="active",
            current_period_end=None,
            cancel_at_period_end=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/cancel-subscription")
async def cancel_subscription(
    at_period_end: bool = True,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Cancel current subscription.

    **Parameters:**
    - at_period_end: If True, cancel at end of billing period (default)
                     If False, cancel immediately

    **Returns:**
    Confirmation of cancellation with effective date.
    """
    try:
        # TODO: Get tenant's subscription ID from database
        # subscription_id = get_subscription_id(tenant_id)

        # Cancel subscription
        # result = await stripe_client.cancel_subscription(
        #     subscription_id,
        #     at_period_end=at_period_end
        # )

        return {
            "status": "cancelled",
            "message": "Subscription cancellation not yet implemented",
            "at_period_end": at_period_end
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")


# =============================================================================
# WEBHOOKS
# =============================================================================

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    **Security:**
    - Validates webhook signature using Stripe signing secret
    - Rejects invalid or tampered webhooks

    **Events handled:**
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed

    **Flow:**
    1. Stripe sends webhook event
    2. Validate signature
    3. Process event (update database)
    4. Return 200 OK
    """
    try:
        # Get raw body and signature
        payload = await request.body()
        signature = request.headers.get('stripe-signature')

        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Verify webhook signature
        event = stripe_client.verify_webhook_signature(payload, signature)

        # Handle the event
        result = await stripe_client.handle_webhook_event(event)

        return WebhookEventResponse(
            status="success",
            message=f"Processed {event['type']} event"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# =============================================================================
# USAGE REPORTING (for metered billing)
# =============================================================================

@router.post("/report-usage")
async def report_usage(
    quantity: int,
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Report API usage for metered billing.

    **For Pro tier overages:**
    - Base plan includes 10,000 calls/day
    - Overages billed at $0.10 per 1,000 calls

    **Parameters:**
    - quantity: Number of API calls to report

    **Note:** This is typically called automatically by API middleware,
    not by end users directly.
    """
    try:
        # TODO: Get subscription item ID from database
        # subscription_item_id = get_subscription_item_id(tenant_id)

        # Report usage to Stripe
        # result = await stripe_client.report_usage(
        #     subscription_item_id,
        #     quantity=quantity
        # )

        return {
            "status": "reported",
            "quantity": quantity,
            "tenant_id": tenant_id,
            "message": "Usage reporting not yet implemented"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage reporting failed: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
