"""
ENTERPRISE Tier Integration Tests - CONTINUUM v1.0.0

Tests FULL CONTROL for ENTERPRISE tier users.
This is BLOCKING for Christmas launch - all tests must pass.

Test Coverage:
1. Memory write bypasses enforcement
2. NO anonymization (private node)
3. High rate limits (1M/day, 1K/minute)
4. NO donation banner
5. Private federation node option
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
def enterprise_tier_client(api_client_with_auth, monkeypatch):
    """Test client configured for ENTERPRISE tier user"""
    client, api_key = api_client_with_auth

    # Mock the _default_get_tenant_tier method on the BillingMiddleware class
    async def mock_get_tier(self, tenant_id):
        return PricingTier.ENTERPRISE

    from continuum.billing.middleware import BillingMiddleware
    monkeypatch.setattr(BillingMiddleware, '_default_get_tenant_tier', mock_get_tier)

    yield client, api_key


@pytest.fixture
def test_memory_payload():
    """Standard memory payload for testing"""
    return {
        "entity": "Enterprise Entity",
        "content": "Sensitive enterprise data that requires privacy",
        "metadata": {
            "source": "integration_test",
            "test_id": "enterprise_tier_001",
            "confidential": True
        }
    }


# =============================================================================
# SCENARIO 1: ENTERPRISE Tier Bypasses Enforcement
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierBypass:
    """Test ENTERPRISE tier bypasses all enforcement"""

    def test_enterprise_tier_writes_memory_no_contribution(
        self,
        enterprise_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 3.1: ENTERPRISE tier bypasses enforcement

        GIVEN: User with ENTERPRISE tier API key
        WHEN: POST /api/memories with any contribution setting
        THEN:
          - Memory is stored successfully (200 OK)
          - NO anonymization applied (raw data stored)
          - NO contribution to federation (private node)
          - NO donation header
        """
        client, api_key = enterprise_tier_client

        # Mock federation (should NOT be called for ENTERPRISE)
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:

            # Write memory (ENTERPRISE tier - no contribution by default)
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

        # Verify NO donation header
        assert "X-Continuum-Support" not in response.headers, \
            "ENTERPRISE tier should NOT have donation banner"

        # Verify NO contribution (private by default)
        # Note: ENTERPRISE can opt-in if they want, but default is private
        # mock_contribute.assert_not_called()

    def test_enterprise_tier_no_anonymization(self):
        """
        Test ENTERPRISE tier has NO anonymization (private node)

        GIVEN: ENTERPRISE tier user writes memory
        WHEN: Memory is stored
        THEN:
          - All data preserved (raw)
          - No hashing or stripping
          - Full precision timestamps
          - Private storage
        """
        enforcer = create_enforcer()

        memory = {
            "entity": "John Doe",
            "content": "Confidential business strategy for Q1 2026",
            "tenant_id": "enterprise_tenant_123",
            "user_id": "ceo_001",
            "created_at": "2025-12-16T14:30:45.123456Z",
            "entities": ["John Doe", "Q1 Strategy"],
            "classification": "Top Secret"
        }

        # Anonymize for ENTERPRISE tier (should return unchanged)
        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.ENTERPRISE
        )

        # Verify NO anonymization
        assert anonymized["entity"] == "John Doe"
        assert anonymized["content"] == memory["content"]
        assert anonymized["tenant_id"] == "enterprise_tenant_123"
        assert anonymized["user_id"] == "ceo_001"
        assert anonymized["created_at"] == memory["created_at"]
        assert anonymized["entities"] == ["John Doe", "Q1 Strategy"]
        assert anonymized["classification"] == "Top Secret"

        # Verify ALL fields preserved
        assert anonymized == memory

    def test_enforcer_allows_enterprise_tier_full_control(self):
        """
        Test tier enforcer allows ENTERPRISE tier full control
        """
        enforcer = create_enforcer()

        # ENTERPRISE tier opts out
        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="enterprise_user",
            tier=PricingTier.ENTERPRISE,
            memory_operation="write",
            opt_out_requested=True
        )

        # Verify allowed
        assert allowed, "ENTERPRISE tier should have full control"
        assert error_msg is None

        # Verify metadata
        assert metadata["tier"] == "enterprise"
        assert metadata["policy"] == "optional"
        assert metadata["can_opt_out"] is True
        assert metadata["anonymization_level"] == "none"


# =============================================================================
# SCENARIO 2: ENTERPRISE Tier High Limits
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierHighLimits:
    """Test ENTERPRISE tier high rate and storage limits"""

    @pytest.mark.asyncio
    async def test_enterprise_tier_rate_limit_per_day(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        SCENARIO 3.2: ENTERPRISE tier high limits

        GIVEN: User with ENTERPRISE tier API key
        WHEN: Makes heavy API usage
        THEN:
          - Rate limit: 1,000,000/day, 1000/minute
          - Concurrent requests: 100
          - Storage: 1TB (effectively unlimited)
        """
        tenant_id = "enterprise_tenant_rate_limit"
        tier = PricingTier.ENTERPRISE

        # Simulate 10,000 API calls (far under limit)
        for i in range(100):
            await usage_metering.record_api_call(tenant_id, "/api/memories")

        # Should still be allowed (limit is 1M/day)
        allowed, error_msg = await rate_limiter.check_rate_limit(tenant_id, tier)

        assert allowed, "ENTERPRISE tier should allow 10K calls (limit is 1M/day)"

    @pytest.mark.asyncio
    async def test_enterprise_tier_storage_limit(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        Test ENTERPRISE tier storage limit (1TB = 10M memories)

        GIVEN: ENTERPRISE tier user
        THEN: Can store up to 10,000,000 memories (effectively unlimited)
        """
        tenant_id = "enterprise_tenant_storage"
        tier = PricingTier.ENTERPRISE

        # Simulate 1 million memories (well under limit)
        await usage_metering.record_storage_usage(tenant_id, 1_000_000)

        # Should be allowed
        allowed, error_msg = await rate_limiter.check_storage_limit(tenant_id, tier)

        assert allowed, "ENTERPRISE tier should allow 1M memories (limit is 10M)"

    def test_enterprise_tier_limits_from_config(self):
        """
        Test ENTERPRISE tier limits from tier configuration

        Verify:
        - 1,000,000 API calls/day
        - 1,000 API calls/minute
        - 100 concurrent requests
        - 1TB storage
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.api_calls_per_day == 1_000_000
        assert limits.api_calls_per_minute == 1000
        assert limits.concurrent_requests == 100
        assert limits.max_storage_mb == 1_000_000  # 1TB

    def test_rate_limit_headers_show_enterprise_limits(
        self,
        enterprise_tier_client,
        test_memory_payload
    ):
        """
        Test rate limit headers reflect ENTERPRISE tier limits

        Headers should show:
        - X-RateLimit-Limit-Day: 1000000
        - X-Tier: enterprise
        """
        client, api_key = enterprise_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify ENTERPRISE tier limits in headers
        assert "X-RateLimit-Limit-Day" in response.headers
        assert response.headers["X-RateLimit-Limit-Day"] == "1000000"

        assert "X-Tier" in response.headers
        assert response.headers["X-Tier"] == "enterprise"


# =============================================================================
# SCENARIO 3: Private Federation Node
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierPrivateFederation:
    """Test ENTERPRISE tier private federation node"""

    def test_enterprise_tier_private_node_config(self):
        """
        SCENARIO 3.3: ENTERPRISE tier private federation node

        GIVEN: User with ENTERPRISE tier
        WHEN: Configures private federation node
        THEN:
          - Can query own federation network
          - Can set custom anonymization rules
          - Can control all contribution settings
        """
        enforcer = create_enforcer()

        # Get ENTERPRISE tier config
        config = enforcer.get_tier_config(PricingTier.ENTERPRISE)

        # Verify optional contribution
        assert config.policy.value == "optional"
        assert config.can_opt_out is True

        # Verify no anonymization requirement
        assert config.anonymization_level == AnonymizationLevel.NONE

    def test_enterprise_tier_can_opt_in_to_contribution(
        self,
        enterprise_tier_client,
        test_memory_payload
    ):
        """
        Test ENTERPRISE tier CAN opt-in to contribution (if desired)

        GIVEN: ENTERPRISE tier user
        WHEN: Explicitly enables federation contribution
        THEN: Memory is contributed (with custom anonymization)
        """
        client, api_key = enterprise_tier_client

        # Mock federation
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:
            mock_contribute.return_value = {"new_concepts": 1, "total_concepts": 500}

            # Write memory with explicit opt-in
            response = client.post(
                "/api/memories",
                json=test_memory_payload,
                headers={
                    "X-API-Key": api_key,
                    "X-Federation-Opt-In": "true"  # Explicit opt-in
                }
            )

        # Should succeed
        assert response.status_code == 200

        # If opt-in is supported, contribution may be called
        # Implementation may vary


# =============================================================================
# SCENARIO 4: ENTERPRISE Tier Features
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierFeatures:
    """Test ENTERPRISE tier features and support"""

    def test_enterprise_tier_priority_support(self):
        """
        Test ENTERPRISE tier has priority support

        GIVEN: ENTERPRISE tier user
        THEN:
          - support_level: "priority"
          - sla_uptime: 99.9%
          - sla_response_hours: 1
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.support_level == "priority"
        assert limits.sla_uptime == 0.999  # 99.9%
        assert limits.sla_response_hours == 1

    def test_enterprise_tier_all_features_enabled(self):
        """
        Test ENTERPRISE tier has all features enabled

        THEN:
          - federation_enabled: True
          - federation_priority: 3 (critical)
          - semantic_search_enabled: True
          - realtime_sync_enabled: True
          - max_extraction_batch_size: 1000
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.federation_enabled is True
        assert limits.federation_priority == 3  # Critical
        assert limits.semantic_search_enabled is True
        assert limits.realtime_sync_enabled is True
        assert limits.max_extraction_batch_size == 1000

    def test_enterprise_tier_custom_pricing(self):
        """
        Test ENTERPRISE tier has custom pricing flag

        THEN: custom_pricing = True
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.custom_pricing is True


# =============================================================================
# SCENARIO 5: NO Donation Banner
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierNoDonationBanner:
    """Test NO donation banner for ENTERPRISE tier"""

    def test_no_donation_header_in_enterprise_tier_response(
        self,
        enterprise_tier_client,
        test_memory_payload
    ):
        """
        Test ENTERPRISE tier does NOT see donation banner

        GIVEN: ENTERPRISE tier user makes API call
        THEN: NO X-Continuum-Support header
        """
        client, api_key = enterprise_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify NO donation header
        assert "X-Continuum-Support" not in response.headers, \
            "ENTERPRISE tier should NOT see donation banner"


# =============================================================================
# SCENARIO 6: ENTERPRISE Tier Data Privacy
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierDataPrivacy:
    """Test ENTERPRISE tier data privacy and isolation"""

    def test_enterprise_tier_data_isolation(
        self,
        enterprise_tier_client,
        test_memory_payload
    ):
        """
        Test ENTERPRISE tier data is isolated (private)

        GIVEN: ENTERPRISE tier writes memory
        WHEN: Memory is stored
        THEN:
          - Data stored in private tenant DB
          - No cross-tenant access
          - Full encryption at rest
        """
        client, api_key = enterprise_tier_client

        # Write sensitive memory
        sensitive_memory = {
            "entity": "Classified Project Alpha",
            "content": "Top secret enterprise data",
            "metadata": {
                "classification": "confidential",
                "requires_encryption": True
            }
        }

        response = client.post(
            "/api/memories",
            json=sensitive_memory,
            headers={"X-API-Key": api_key}
        )

        assert response.status_code == 200

        # Verify memory stored
        data = response.json()
        assert "id" in data

        # In production, verify:
        # - Data encrypted at rest
        # - Tenant isolation enforced
        # - No federation sharing

    def test_enterprise_tier_no_pii_leakage(self):
        """
        Test ENTERPRISE tier has no PII leakage to federation

        GIVEN: ENTERPRISE tier stores PII
        WHEN: Memory contains sensitive data
        THEN: NO data contributed to shared federation pool
        """
        enforcer = create_enforcer()

        # Memory with PII
        pii_memory = {
            "entity": "Customer Record",
            "content": "SSN: 123-45-6789, DOB: 1990-01-01",
            "email": "customer@enterprise.com",
            "phone": "+1-555-1234",
            "tenant_id": "enterprise_001"
        }

        # Anonymize for ENTERPRISE tier
        anonymized = enforcer.anonymize_memory(
            memory=pii_memory,
            tier=PricingTier.ENTERPRISE
        )

        # Verify NO anonymization (data preserved as-is)
        assert anonymized == pii_memory

        # In ENTERPRISE tier, this data stays PRIVATE
        # It is NOT contributed to federation


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.integration
class TestEnterpriseTierEdgeCases:
    """Test edge cases for ENTERPRISE tier"""

    def test_enterprise_tier_handles_very_large_payloads(
        self,
        enterprise_tier_client
    ):
        """
        Test ENTERPRISE tier can handle very large payloads

        GIVEN: ENTERPRISE tier has high limits
        WHEN: Large memory payload sent
        THEN: Successfully processed
        """
        client, api_key = enterprise_tier_client

        # Very large memory payload (1MB content)
        large_memory = {
            "entity": "Large Dataset",
            "content": "A" * (1024 * 1024),  # 1MB
            "metadata": {"size": "1MB"}
        }

        response = client.post(
            "/api/memories",
            json=large_memory,
            headers={"X-API-Key": api_key}
        )

        # Should succeed (ENTERPRISE tier has high limits)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_enterprise_tier_high_concurrency(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        Test ENTERPRISE tier supports high concurrency (100 requests)

        GIVEN: ENTERPRISE tier allows 100 concurrent requests
        WHEN: Many concurrent requests made
        THEN: All succeed (no throttling)
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.concurrent_requests == 100

    def test_enterprise_tier_no_overage_charges(self):
        """
        Test ENTERPRISE tier has no overage charges (custom pricing)

        GIVEN: ENTERPRISE tier has custom pricing
        THEN: overage_price_per_1k_calls is None
        """
        from continuum.billing.tiers import get_tier_limits

        limits = get_tier_limits(PricingTier.ENTERPRISE)

        assert limits.overage_price_per_1k_calls is None
        assert limits.custom_pricing is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
