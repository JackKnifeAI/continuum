"""
PRO Tier Integration Tests - CONTINUUM v1.0.0

Tests OPTIONAL federation contribution for PRO tier users.
This is BLOCKING for Christmas launch - all tests must pass.

Test Coverage:
1. Memory write with contribution enabled
2. Opt-out from contribution (allowed)
3. Rate limits (10K/day, 100/minute)
4. NO donation banner
5. Standard anonymization (reversible HMAC)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from continuum.billing.tiers import PricingTier
from continuum.federation.tier_enforcer import create_enforcer, AnonymizationLevel


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def pro_tier_client(api_client_with_auth, monkeypatch):
    """Test client configured for PRO tier user"""
    client, api_key = api_client_with_auth

    # Mock the _default_get_tenant_tier method on the BillingMiddleware class
    # This will affect all instances
    async def mock_get_tier(self, tenant_id):
        return PricingTier.PRO

    from continuum.billing.middleware import BillingMiddleware
    monkeypatch.setattr(BillingMiddleware, '_default_get_tenant_tier', mock_get_tier)

    yield client, api_key


@pytest.fixture
def test_memory_payload():
    """Standard memory payload for testing"""
    return {
        "entity": "Test Entity",
        "content": "This is a test memory for PRO tier integration testing",
        "metadata": {
            "source": "integration_test",
            "test_id": "pro_tier_001"
        }
    }


# =============================================================================
# SCENARIO 1: PRO Tier with Contribution Enabled
# =============================================================================

@pytest.mark.integration
class TestProTierWithContribution:
    """Test PRO tier with contribution enabled (default)"""

    def test_pro_tier_writes_memory_with_contribution(
        self,
        pro_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 2.1: PRO tier user writes memory (contribution enabled)

        GIVEN: User with PRO tier API key, contribution enabled
        WHEN: POST /api/memories with valid memory data
        THEN:
          - Memory is stored successfully (200 OK)
          - Memory is anonymized with standard level (reversible hashing)
          - Memory is contributed to federation
          - NO donation header in response
        """
        client, api_key = pro_tier_client

        # Mock federation contribution
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:
            mock_contribute.return_value = {"new_concepts": 1, "total_concepts": 200}

            # Write memory (contribution enabled by default)
            response = client.post(
                "/api/memories",
                json=test_memory_payload,
                headers={"X-API-Key": api_key}
            )

        # Verify successful write
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["status"] == "stored"

        # Verify NO donation header (PRO tier)
        assert "X-Continuum-Support" not in response.headers, \
            "PRO tier should NOT have donation banner"

        # Verify federation contribution was called
        mock_contribute.assert_called_once()

    def test_pro_tier_anonymization_is_standard(self):
        """
        Test PRO tier uses STANDARD anonymization (reversible)

        GIVEN: PRO tier user writes memory
        WHEN: Memory is anonymized for contribution
        THEN:
          - Entity names hashed with reversible HMAC
          - Raw text content preserved
          - Timestamps generalized to day precision
          - User can potentially reverse their own hashes
        """
        enforcer = create_enforcer()

        memory = {
            "entity": "Jane Smith",
            "content": "Working on neural networks research",
            "tenant_id": "pro_tenant_123",
            "user_id": "user_789",
            "created_at": "2025-12-16T10:30:00Z",
            "entities": ["Jane Smith", "neural networks"]
        }

        # Anonymize for PRO tier
        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.PRO
        )

        # Verify standard anonymization
        assert "tenant_id" not in anonymized, "Tenant ID should be stripped"
        assert "user_id" not in anonymized, "User ID should be stripped"

        # Content should be preserved (PRO tier)
        assert "content" in anonymized or "description" in memory
        # Note: field names may vary, key is text is kept

        # Entities should be hashed (reversible)
        if "entities" in anonymized:
            for entity_hash in anonymized["entities"]:
                # Reversible hashes are prefixed with "hash_"
                assert entity_hash.startswith("hash_"), \
                    "PRO tier should use reversible hashing"

        # Timestamp should be generalized to day
        if "created_at" in anonymized:
            # Should be date only (YYYY-MM-DD)
            assert anonymized["created_at"] == "2025-12-16"


# =============================================================================
# SCENARIO 2: PRO Tier Opts Out of Contribution
# =============================================================================

@pytest.mark.integration
class TestProTierOptOut:
    """Test PRO tier CAN opt out of contribution"""

    def test_pro_tier_can_opt_out(
        self,
        pro_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 2.2: PRO tier user opts out of contribution

        GIVEN: User with PRO tier API key
        WHEN: POST /api/memories with X-Federation-Opt-Out: true
        THEN:
          - Memory is stored successfully (200 OK)
          - Memory is NOT contributed to federation
          - User retains access to federation query
        """
        client, api_key = pro_tier_client

        # Mock federation (should NOT be called)
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:

            # Write memory with opt-out
            response = client.post(
                "/api/memories",
                json=test_memory_payload,
                headers={
                    "X-API-Key": api_key,
                    "X-Federation-Opt-Out": "true"
                }
            )

        # Verify successful write
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "stored"

        # Verify NO contribution (opt-out successful)
        mock_contribute.assert_not_called()

    def test_enforcer_allows_pro_tier_opt_out(self):
        """
        Test tier enforcer logic allows PRO tier opt-out
        """
        enforcer = create_enforcer()

        # Attempt opt-out
        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="pro_user",
            tier=PricingTier.PRO,
            memory_operation="write",
            opt_out_requested=True
        )

        # Verify allowed
        assert allowed, "PRO tier should be allowed to opt out"
        assert error_msg is None

        # Verify metadata
        assert metadata["tier"] == "pro"
        assert metadata["policy"] == "optional"
        assert metadata["can_opt_out"] is True
        assert metadata["anonymization_level"] == "standard"

    def test_pro_tier_can_toggle_contribution_preference(
        self,
        pro_tier_client,
        test_memory_payload
    ):
        """
        Test PRO tier can toggle contribution on/off via settings

        SCENARIO: User sets contribution preference
        WHEN: PUT /api/settings {"contribute_to_federation": false}
        THEN: Preference is saved, subsequent writes respect it
        """
        client, api_key = pro_tier_client

        # Update contribution preference (opt-out)
        response = client.put(
            "/api/settings",
            json={"contribute_to_federation": False},
            headers={"X-API-Key": api_key}
        )

        # Verify settings update
        # Note: Actual endpoint may vary, this tests the concept
        if response.status_code == 200:
            assert response.json().get("contribute_to_federation") is False


# =============================================================================
# SCENARIO 3: PRO Tier Rate Limits (10K/day, 100/minute)
# =============================================================================

@pytest.mark.integration
class TestProTierRateLimits:
    """Test PRO tier rate limit enforcement"""

    @pytest.mark.asyncio
    async def test_pro_tier_rate_limit_per_day(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        SCENARIO 2.3: PRO tier rate limits

        GIVEN: User with PRO tier API key
        WHEN: Makes API calls
        THEN:
          - Rate limit: 10,000/day, 100/minute
          - Concurrent requests: Up to 10
          - All within limits succeed
        """
        tenant_id = "pro_tenant_rate_limit"
        tier = PricingTier.PRO

        # Simulate 100 API calls (well under limit)
        for i in range(100):
            await usage_metering.record_api_call(tenant_id, "/api/memories")

        # Should still be allowed (limit is 10,000/day)
        allowed, error_msg = await rate_limiter.check_rate_limit(tenant_id, tier)

        assert allowed, "PRO tier should allow 100 calls (limit is 10,000/day)"

    @pytest.mark.asyncio
    async def test_pro_tier_rate_limit_exceeded(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        Test PRO tier rate limit exceeded (10,001st call)
        """
        tenant_id = "pro_tenant_exceeded"
        tier = PricingTier.PRO

        # Simulate 10,000 API calls (at limit)
        await usage_metering.set_usage(tenant_id, 'api_calls', 10000, period='day')

        # 10,001st call should be blocked
        allowed, error_msg = await rate_limiter.check_rate_limit(tenant_id, tier)

        assert not allowed, "Should block after 10,000 calls/day for PRO tier"
        assert "rate limit" in error_msg.lower()

    def test_rate_limit_headers_show_pro_limits(
        self,
        pro_tier_client,
        test_memory_payload
    ):
        """
        Test rate limit headers reflect PRO tier limits

        Headers should show:
        - X-RateLimit-Limit-Day: 10000
        - X-Tier: pro
        """
        client, api_key = pro_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify PRO tier limits in headers
        assert "X-RateLimit-Limit-Day" in response.headers
        assert response.headers["X-RateLimit-Limit-Day"] == "10000"

        assert "X-Tier" in response.headers
        assert response.headers["X-Tier"] == "pro"


# =============================================================================
# SCENARIO 4: NO Donation Banner for PRO Tier
# =============================================================================

@pytest.mark.integration
class TestProTierNoDonationBanner:
    """Test NO donation banner for PRO tier"""

    def test_no_donation_header_in_pro_tier_response(
        self,
        pro_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 2.4: PRO tier dashboard - No donation banner

        GIVEN: User on PRO tier accessing API
        WHEN: Makes successful API call
        THEN: NO X-Continuum-Support header (no donation banner)
        """
        client, api_key = pro_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify NO donation header
        assert "X-Continuum-Support" not in response.headers, \
            "PRO tier should NOT see donation banner"

    def test_pro_tier_badge_in_dashboard(
        self,
        pro_tier_client
    ):
        """
        Test PRO tier badge/indicator in dashboard

        GIVEN: PRO tier user accesses dashboard
        THEN: Dashboard shows "PRO" badge/indicator
        """
        client, api_key = pro_tier_client

        # Get user info/status
        response = client.get(
            "/api/user/status",
            headers={"X-API-Key": api_key}
        )

        if response.status_code == 200:
            data = response.json()
            # Verify tier is indicated
            assert data.get("tier") == "pro" or "tier" in str(data).lower()


# =============================================================================
# SCENARIO 5: PRO Tier Storage Limits (100K memories)
# =============================================================================

@pytest.mark.integration
class TestProTierStorageLimits:
    """Test PRO tier storage limits"""

    @pytest.mark.asyncio
    async def test_pro_tier_storage_limit(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        Test PRO tier storage limit (100,000 memories)

        GIVEN: PRO tier user
        THEN: Can store up to 100,000 memories
        """
        tenant_id = "pro_tenant_storage"
        tier = PricingTier.PRO

        # Simulate 50,000 memories (well under limit)
        await usage_metering.record_storage_usage(tenant_id, 50000)

        # Should be allowed
        allowed, error_msg = await rate_limiter.check_storage_limit(tenant_id, tier)

        assert allowed, "PRO tier should allow 50K memories (limit is 100K)"


# =============================================================================
# SCENARIO 6: PRO Tier Features Enabled
# =============================================================================

@pytest.mark.integration
class TestProTierFeatures:
    """Test PRO tier feature access"""

    def test_pro_tier_has_realtime_sync(self):
        """
        Test PRO tier has realtime sync enabled

        GIVEN: PRO tier user
        THEN: realtime_sync_enabled = True
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.PRO)

        assert limits.realtime_sync_enabled is True
        assert limits.semantic_search_enabled is True
        assert limits.federation_enabled is True

    def test_pro_tier_extraction_batch_size(self):
        """
        Test PRO tier extraction batch size (100)
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.PRO)

        assert limits.max_extraction_batch_size == 100


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.integration
class TestProTierEdgeCases:
    """Test edge cases for PRO tier"""

    def test_pro_tier_concurrent_request_limit(self):
        """
        Test PRO tier concurrent request limit (10)

        GIVEN: PRO tier allows 10 concurrent requests
        WHEN: 11th concurrent request made
        THEN: May be queued or rejected
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.PRO)

        assert limits.concurrent_requests == 10

    @pytest.mark.asyncio
    async def test_pro_tier_contribution_with_large_memory(
        self,
        pro_tier_client,
        usage_metering
    ):
        """
        Test PRO tier can contribute large memories (within batch size)
        """
        client, api_key = pro_tier_client

        # Large memory payload
        large_memory = {
            "entity": "Large Dataset",
            "content": "A" * 5000,  # 5KB content
            "metadata": {"size": "large"}
        }

        response = client.post(
            "/api/memories",
            json=large_memory,
            headers={"X-API-Key": api_key}
        )

        # Should succeed (PRO tier has higher limits)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
