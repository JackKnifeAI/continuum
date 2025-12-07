"""
Integration Tests for CONTINUUM Billing System

Tests rate limiting, tier limits, usage metering, and billing enforcement.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from continuum.billing.tiers import PricingTier, get_tier_limits, FREE_TIER, PRO_TIER, ENTERPRISE_TIER
from continuum.billing.metering import UsageMetering, RateLimiter


@pytest.mark.integration
class TestTierLimits:
    """Test pricing tier definitions and limits"""

    def test_free_tier_limits(self):
        """Test FREE tier has expected limits"""
        limits = get_tier_limits(PricingTier.FREE)

        assert limits.tier == PricingTier.FREE
        assert limits.max_memories == 1000
        assert limits.api_calls_per_day == 100
        assert limits.api_calls_per_minute == 10
        assert limits.concurrent_requests == 2
        assert limits.federation_enabled is False
        assert limits.monthly_price_usd == 0.0

    def test_pro_tier_limits(self):
        """Test PRO tier has expected limits"""
        limits = get_tier_limits(PricingTier.PRO)

        assert limits.tier == PricingTier.PRO
        assert limits.max_memories == 100_000
        assert limits.api_calls_per_day == 10_000
        assert limits.api_calls_per_minute == 100
        assert limits.concurrent_requests == 10
        assert limits.federation_enabled is True
        assert limits.realtime_sync_enabled is True
        assert limits.monthly_price_usd == 29.0

    def test_enterprise_tier_limits(self):
        """Test ENTERPRISE tier has expected limits"""
        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.tier == PricingTier.ENTERPRISE
        assert limits.max_memories == 10_000_000
        assert limits.api_calls_per_day == 1_000_000
        assert limits.api_calls_per_minute == 1000
        assert limits.concurrent_requests == 100
        assert limits.federation_enabled is True
        assert limits.federation_priority == 3  # Critical
        assert limits.custom_pricing is True

    def test_tier_hierarchy(self):
        """Test that tiers increase in capability"""
        free = get_tier_limits(PricingTier.FREE)
        pro = get_tier_limits(PricingTier.PRO)
        enterprise = get_tier_limits(PricingTier.ENTERPRISE)

        # Memory limits increase
        assert free.max_memories < pro.max_memories < enterprise.max_memories

        # API limits increase
        assert free.api_calls_per_day < pro.api_calls_per_day < enterprise.api_calls_per_day
        assert free.concurrent_requests < pro.concurrent_requests < enterprise.concurrent_requests

        # Features expand
        assert not free.federation_enabled
        assert pro.federation_enabled
        assert enterprise.federation_enabled


@pytest.mark.integration
@pytest.mark.asyncio
class TestUsageMetering:
    """Test usage tracking and metering"""

    async def test_record_api_call(self, usage_metering):
        """Test recording API calls"""
        await usage_metering.record_api_call("tenant_test", "/v1/recall")

        usage = await usage_metering.get_usage("tenant_test", "api_calls", "day")
        assert usage == 1

    async def test_multiple_api_calls(self, usage_metering):
        """Test recording multiple API calls"""
        for i in range(5):
            await usage_metering.record_api_call("tenant_test", "/v1/learn")

        usage = await usage_metering.get_usage("tenant_test", "api_calls", "day")
        assert usage == 5

    async def test_endpoint_tracking(self, usage_metering):
        """Test endpoint-specific usage tracking"""
        await usage_metering.record_api_call("tenant_test", "/v1/recall")
        await usage_metering.record_api_call("tenant_test", "/v1/recall")
        await usage_metering.record_api_call("tenant_test", "/v1/learn")

        # Check total calls
        total = await usage_metering.get_usage("tenant_test", "api_calls", "day")
        assert total == 3

    async def test_storage_usage_tracking(self, usage_metering):
        """Test storage usage tracking"""
        await usage_metering.record_storage_usage(
            "tenant_test",
            memories=100,
            embeddings=100,
            bytes_used=1024 * 1024  # 1 MB
        )

        storage = await usage_metering.get_storage_usage("tenant_test")
        assert storage['memories'] == 100
        assert storage['embeddings'] == 100
        assert storage['bytes'] == 1024 * 1024

    async def test_federation_contribution_tracking(self, usage_metering):
        """Test federation contribution tracking"""
        await usage_metering.record_federation_contribution("tenant_test", shared_memories=10)

        usage = await usage_metering.get_usage("tenant_test", "federation_shares", "day")
        assert usage == 10

    async def test_extraction_tracking(self, usage_metering):
        """Test extraction operation tracking"""
        await usage_metering.record_extraction("tenant_test", batch_size=50)

        extractions = await usage_metering.get_usage("tenant_test", "extractions", "day")
        items = await usage_metering.get_usage("tenant_test", "extraction_items", "day")

        assert extractions == 1
        assert items == 50

    async def test_tenant_isolation_in_metering(self, usage_metering):
        """Test that usage is isolated per tenant"""
        await usage_metering.record_api_call("tenant_a", "/v1/recall")
        await usage_metering.record_api_call("tenant_a", "/v1/recall")
        await usage_metering.record_api_call("tenant_b", "/v1/recall")

        usage_a = await usage_metering.get_usage("tenant_a", "api_calls", "day")
        usage_b = await usage_metering.get_usage("tenant_b", "api_calls", "day")

        assert usage_a == 2
        assert usage_b == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting enforcement"""

    async def test_free_tier_rate_limit(self, usage_metering, rate_limiter):
        """Test FREE tier rate limits are enforced"""
        tenant_id = "free_tenant"

        # Simulate calls up to limit
        for i in range(10):  # FREE tier: 10 per minute
            await usage_metering.record_api_call(tenant_id, "/v1/recall")

        # Check rate limit
        allowed, error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)

        # Should be at limit or over
        assert allowed is False
        assert "Rate limit exceeded" in error or "exceeded" in error.lower()

    async def test_pro_tier_higher_limits(self, usage_metering, rate_limiter):
        """Test PRO tier has higher limits than FREE"""
        tenant_id = "pro_tenant"

        # Simulate calls that would exceed FREE but not PRO
        for i in range(50):  # FREE: 10/min, PRO: 100/min
            await usage_metering.record_api_call(tenant_id, "/v1/recall")

        # Should fail for FREE
        free_allowed, free_error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)
        assert free_allowed is False

        # Should pass for PRO
        pro_allowed, pro_error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.PRO)
        assert pro_allowed is True

    async def test_daily_limit_enforcement(self, usage_metering, rate_limiter):
        """Test daily API call limits"""
        tenant_id = "daily_test"

        # Simulate calls up to daily limit for FREE tier (100/day)
        for i in range(101):
            await usage_metering.record_api_call(tenant_id, "/v1/recall")

        # Should be over daily limit
        allowed, error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)
        assert allowed is False
        assert "daily" in error.lower() or "exceeded" in error.lower()

    async def test_concurrent_request_limit(self, rate_limiter):
        """Test concurrent request limiting"""
        tenant_id = "concurrent_test"

        # Acquire slots up to FREE tier limit (2)
        await rate_limiter.acquire_request_slot(tenant_id)
        await rate_limiter.acquire_request_slot(tenant_id)

        # Check if over limit
        allowed, error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)
        assert allowed is False
        assert "concurrent" in error.lower()

        # Release a slot
        await rate_limiter.release_request_slot(tenant_id)

        # Should be allowed now
        allowed, error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)
        assert allowed is True

    async def test_storage_limit_check(self, usage_metering, rate_limiter):
        """Test storage limit enforcement"""
        tenant_id = "storage_test"

        # Record storage exceeding FREE tier limit (1000 memories)
        await usage_metering.record_storage_usage(
            tenant_id,
            memories=1001,
            embeddings=500,
            bytes_used=50 * 1024 * 1024  # 50 MB
        )

        # Should fail storage check for FREE tier
        allowed, error = await rate_limiter.check_storage_limit(tenant_id, PricingTier.FREE)
        assert allowed is False
        assert "memory limit" in error.lower() or "exceeded" in error.lower()

        # Should pass for PRO tier (100k limit)
        allowed, error = await rate_limiter.check_storage_limit(tenant_id, PricingTier.PRO)
        assert allowed is True

    async def test_feature_access_control(self, rate_limiter):
        """Test feature access based on tier"""
        # FREE tier should not have federation
        allowed, error = await rate_limiter.check_feature_access(PricingTier.FREE, 'federation')
        assert allowed is False
        assert "not available" in error.lower()

        # PRO tier should have federation
        allowed, error = await rate_limiter.check_feature_access(PricingTier.PRO, 'federation')
        assert allowed is True

        # All tiers should have semantic search
        for tier in [PricingTier.FREE, PricingTier.PRO, PricingTier.ENTERPRISE]:
            allowed, error = await rate_limiter.check_feature_access(tier, 'semantic_search')
            assert allowed is True


@pytest.mark.integration
class TestAPIBillingIntegration:
    """Test billing integration with API endpoints"""

    def test_api_call_without_tier_succeeds(self, api_client):
        """Test API calls work without billing (defaults to FREE)"""
        response = api_client.get("/v1/health")
        assert response.status_code == 200

    def test_learn_endpoint_metering(self, api_client):
        """Test that learn endpoint can be metered"""
        response = api_client.post("/v1/learn", json={
            "user_message": "Test message",
            "ai_response": "Test response"
        })

        assert response.status_code == 200

    def test_recall_endpoint_metering(self, api_client):
        """Test that recall endpoint can be metered"""
        response = api_client.post("/v1/recall", json={
            "message": "Test query"
        })

        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
class TestBillingWorkflow:
    """Test complete billing workflow"""

    async def test_usage_accumulation(self, usage_metering):
        """Test that usage accumulates correctly over time"""
        tenant_id = "workflow_test"

        # Simulate realistic usage pattern
        # Day 1: 10 API calls
        for i in range(10):
            await usage_metering.record_api_call(tenant_id, "/v1/recall")

        # Record storage
        await usage_metering.record_storage_usage(tenant_id, memories=50)

        # Record federation
        await usage_metering.record_federation_contribution(tenant_id, shared_memories=5)

        # Check accumulated usage
        api_calls = await usage_metering.get_usage(tenant_id, "api_calls", "day")
        storage = await usage_metering.get_storage_usage(tenant_id)
        federation = await usage_metering.get_usage(tenant_id, "federation_shares", "day")

        assert api_calls == 10
        assert storage['memories'] == 50
        assert federation == 5

    async def test_tier_upgrade_scenario(self, usage_metering, rate_limiter):
        """Test scenario where tenant needs to upgrade tier"""
        tenant_id = "upgrade_test"

        # Start with FREE tier, hit limits
        for i in range(15):
            await usage_metering.record_api_call(tenant_id, "/v1/recall")

        # Should fail FREE tier check
        free_allowed, free_error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.FREE)
        assert free_allowed is False

        # Simulate upgrade to PRO tier
        # PRO tier should allow the same usage
        pro_allowed, pro_error = await rate_limiter.check_rate_limit(tenant_id, PricingTier.PRO)
        assert pro_allowed is True


@pytest.mark.integration
class TestMockStripeIntegration:
    """Test Stripe integration with mocks"""

    async def test_create_customer(self, mock_stripe_client):
        """Test customer creation in Stripe"""
        result = mock_stripe_client.create_customer(
            email="test@example.com",
            metadata={"tenant_id": "test_tenant"}
        )

        assert result["id"].startswith("cus_")

    async def test_create_subscription(self, mock_stripe_client):
        """Test subscription creation"""
        result = mock_stripe_client.create_subscription(
            customer_id="cus_test123",
            price_id="price_pro_monthly"
        )

        assert result["id"].startswith("sub_")
        assert result["status"] == "active"

    async def test_report_usage(self, mock_stripe_client):
        """Test usage reporting to Stripe"""
        result = mock_stripe_client.report_usage(
            subscription_item_id="si_test123",
            quantity=100,
            action="increment"
        )

        assert "id" in result
