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
Stripe API Client for CONTINUUM

Handles customer management, subscriptions, usage-based billing, and webhooks.
"""

import os
import hmac
import hashlib
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Try to import stripe, but allow graceful degradation to mock mode
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe library not installed. Running in mock mode. Install with: pip install stripe")


class SubscriptionStatus(Enum):
    """Stripe subscription statuses"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    PAUSED = "paused"


class StripeClient:
    """
    Stripe API wrapper for CONTINUUM billing operations.

    Handles:
    - Customer creation and management
    - Subscription lifecycle (create, update, cancel)
    - Usage-based metering for API calls
    - Webhook signature verification
    - Payment method management

    **Mock Mode:**
    If Stripe SDK is not installed or API key is not provided,
    the client runs in mock mode for development/testing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        mock_mode: bool = False
    ):
        """
        Initialize Stripe client.

        Args:
            api_key: Stripe secret key (defaults to STRIPE_SECRET_KEY env var)
            webhook_secret: Stripe webhook signing secret (defaults to STRIPE_WEBHOOK_SECRET)
            mock_mode: Force mock mode (useful for testing without Stripe)
        """
        self.api_key = api_key or os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = webhook_secret or os.getenv('STRIPE_WEBHOOK_SECRET')

        # Determine if we should run in mock mode
        self.mock_mode = mock_mode or not STRIPE_AVAILABLE or not self.api_key

        if self.mock_mode:
            logger.warning(
                "Stripe client running in MOCK MODE. "
                "No real Stripe API calls will be made. "
                "Set STRIPE_SECRET_KEY environment variable to enable live mode."
            )
        else:
            stripe.api_key = self.api_key
            logger.info("Stripe client initialized in LIVE MODE")

    def _mock_customer(self, email: str, tenant_id: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a mock customer object for development"""
        import random
        return {
            "id": f"cus_mock_{random.randint(100000, 999999)}",
            "object": "customer",
            "email": email,
            "metadata": {"tenant_id": tenant_id, **(metadata or {})},
            "created": int(datetime.now(timezone.utc).timestamp()),
        }

    def _mock_subscription(self, customer_id: str, price_id: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a mock subscription object for development"""
        import random
        now = datetime.now(timezone.utc)
        return {
            "id": f"sub_mock_{random.randint(100000, 999999)}",
            "object": "subscription",
            "customer": customer_id,
            "status": "active",
            "items": {
                "data": [{
                    "id": f"si_mock_{random.randint(100000, 999999)}",
                    "price": {"id": price_id},
                }]
            },
            "metadata": metadata or {},
            "created": int(now.timestamp()),
            "current_period_start": int(now.timestamp()),
            "current_period_end": int((now.replace(month=now.month+1 if now.month < 12 else 1)).timestamp()),
        }

    # Customer Management

    async def create_customer(
        self,
        email: str,
        tenant_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Stripe customer.

        Args:
            email: Customer email
            tenant_id: CONTINUUM tenant ID
            metadata: Additional metadata

        Returns:
            Customer object
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Creating customer for {email} (tenant: {tenant_id})")
            return self._mock_customer(email, tenant_id, metadata)

        try:
            customer_metadata = {"tenant_id": tenant_id}
            if metadata:
                customer_metadata.update(metadata)

            customer = stripe.Customer.create(
                email=email,
                metadata=customer_metadata
            )

            logger.info(f"Created Stripe customer {customer.id} for tenant {tenant_id}")
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer by Stripe ID"""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {e}")
            raise

    async def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update customer details"""
        try:
            return stripe.Customer.modify(customer_id, **kwargs)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer {customer_id}: {e}")
            raise

    async def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """Delete customer (use cautiously)"""
        try:
            return stripe.Customer.delete(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to delete customer {customer_id}: {e}")
            raise

    # Subscription Management

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None,
        trial_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID (e.g., price_pro_monthly)
            metadata: Additional metadata
            trial_days: Number of trial days (optional)

        Returns:
            Subscription object
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Creating subscription for customer {customer_id} with price {price_id}")
            return self._mock_subscription(customer_id, price_id, metadata)

        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {}
            }

            if trial_days:
                params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**params)

            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription by ID"""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise

    async def update_subscription(
        self,
        subscription_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update subscription (e.g., change plan).

        Args:
            subscription_id: Stripe subscription ID
            **kwargs: Subscription update parameters

        Returns:
            Updated subscription object
        """
        try:
            return stripe.Subscription.modify(subscription_id, **kwargs)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription {subscription_id}: {e}")
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period

        Returns:
            Canceled subscription object
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(f"Canceled subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise

    async def list_customer_subscriptions(
        self,
        customer_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID
            status: Filter by status (e.g., 'active')

        Returns:
            List of subscription objects
        """
        try:
            params = {"customer": customer_id}
            if status:
                params["status"] = status

            subscriptions = stripe.Subscription.list(**params)
            return subscriptions.data

        except stripe.error.StripeError as e:
            logger.error(f"Failed to list subscriptions for {customer_id}: {e}")
            raise

    # Usage-Based Billing

    async def report_usage(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: Optional[int] = None,
        action: str = "increment"
    ) -> Dict[str, Any]:
        """
        Report usage for metered billing.

        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity
            timestamp: Unix timestamp (defaults to now)
            action: 'increment' or 'set'

        Returns:
            Usage record object
        """
        try:
            params = {
                "quantity": quantity,
                "action": action
            }

            if timestamp:
                params["timestamp"] = timestamp
            else:
                params["timestamp"] = int(datetime.now(timezone.utc).timestamp())

            usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                **params
            )

            logger.debug(f"Reported {quantity} usage for item {subscription_item_id}")
            return usage_record

        except stripe.error.StripeError as e:
            logger.error(f"Failed to report usage: {e}")
            raise

    async def list_usage_records(
        self,
        subscription_item_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List usage records for a subscription item"""
        try:
            records = stripe.SubscriptionItem.list_usage_record_summaries(
                subscription_item_id,
                limit=limit
            )
            return records.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list usage records: {e}")
            raise

    # Payment Methods

    async def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str,
        set_default: bool = True
    ) -> Dict[str, Any]:
        """
        Attach payment method to customer.

        Args:
            customer_id: Stripe customer ID
            payment_method_id: Payment method ID
            set_default: Set as default payment method

        Returns:
            Payment method object
        """
        try:
            # Attach payment method
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            # Set as default if requested
            if set_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )

            logger.info(f"Attached payment method {payment_method_id} to {customer_id}")
            return payment_method

        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise

    async def list_payment_methods(
        self,
        customer_id: str,
        type: str = "card"
    ) -> List[Dict[str, Any]]:
        """List customer's payment methods"""
        try:
            methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type=type
            )
            return methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            raise

    # Webhooks

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        tolerance: int = 300
    ) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Request body (raw bytes)
            signature: Stripe-Signature header value
            tolerance: Maximum age of webhook (seconds)

        Returns:
            Verified event object

        Raises:
            ValueError: If signature is invalid
        """
        if self.mock_mode:
            # In mock mode, parse payload as JSON
            import json
            logger.warning("[MOCK] Skipping webhook signature verification")
            try:
                event = json.loads(payload.decode('utf-8'))
                return event
            except Exception as e:
                raise ValueError(f"Invalid webhook payload in mock mode: {e}")

        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
                tolerance=tolerance
            )

            logger.info(f"Verified webhook event: {event['type']}")
            return event

        except ValueError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid signature")

    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook events.

        Args:
            event: Verified Stripe event

        Returns:
            Processing result
        """
        event_type = event['type']
        data = event['data']['object']

        handlers = {
            'customer.created': self._handle_customer_created,
            'customer.updated': self._handle_customer_updated,
            'customer.deleted': self._handle_customer_deleted,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_payment_succeeded,
            'invoice.payment_failed': self._handle_payment_failed,
            'payment_method.attached': self._handle_payment_method_attached,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(data)
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")
            return {"status": "unhandled", "type": event_type}

    # Webhook Event Handlers

    async def _handle_customer_created(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.created event"""
        logger.info(f"Customer created: {customer['id']}")
        return {"status": "ok", "customer_id": customer['id']}

    async def _handle_customer_updated(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.updated event"""
        logger.info(f"Customer updated: {customer['id']}")
        return {"status": "ok", "customer_id": customer['id']}

    async def _handle_customer_deleted(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.deleted event"""
        logger.warning(f"Customer deleted: {customer['id']}")
        return {"status": "ok", "customer_id": customer['id']}

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.created event"""
        logger.info(f"Subscription created: {subscription['id']}")
        return {"status": "ok", "subscription_id": subscription['id']}

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.updated event"""
        logger.info(f"Subscription updated: {subscription['id']} - status: {subscription['status']}")
        return {"status": "ok", "subscription_id": subscription['id']}

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event"""
        logger.warning(f"Subscription deleted: {subscription['id']}")
        return {"status": "ok", "subscription_id": subscription['id']}

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event"""
        logger.info(f"Payment succeeded for invoice: {invoice['id']}")
        return {"status": "ok", "invoice_id": invoice['id']}

    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        logger.error(f"Payment failed for invoice: {invoice['id']}")
        # TODO: Implement payment failure handling (email notification, retry logic, etc.)
        return {"status": "ok", "invoice_id": invoice['id']}

    async def _handle_payment_method_attached(self, payment_method: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_method.attached event"""
        logger.info(f"Payment method attached: {payment_method['id']}")
        return {"status": "ok", "payment_method_id": payment_method['id']}

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
