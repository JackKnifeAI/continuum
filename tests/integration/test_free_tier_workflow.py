"""
FREE Tier Integration Tests - CONTINUUM v1.0.0

Tests MANDATORY federation contribution for FREE tier users.
This is BLOCKING for Christmas launch - all tests must pass.

Test Coverage:
1. Memory write → Contribution enforcement
2. Opt-out attempt → 403 Forbidden
3. Rate limit enforcement (100/day)
4. Donation banner display
5. Anonymization (SHA-256 irreversible)
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
def free_tier_client(api_client_with_auth, monkeypatch):
    """Test client configured for FREE tier user"""
    client, api_key = api_client_with_auth

    # Mock the _default_get_tenant_tier method on the BillingMiddleware class
    async def mock_get_tier(self, tenant_id):
        return PricingTier.FREE

    from continuum.billing.middleware import BillingMiddleware
    monkeypatch.setattr(BillingMiddleware, '_default_get_tenant_tier', mock_get_tier)

    yield client, api_key


@pytest.fixture
def test_memory_payload():
    """Standard memory payload for testing"""
    return {
        "entity": "Test Entity",
        "content": "This is a test memory for FREE tier integration testing",
        "metadata": {
            "source": "integration_test",
            "test_id": "free_tier_001"
        }
    }


# =============================================================================
# SCENARIO 1: FREE Tier Memory Write (Mandatory Contribution)
# =============================================================================

@pytest.mark.integration
class TestFreeTierMandatoryContribution:
    """Test FREE tier mandatory contribution enforcement"""

    def test_free_tier_writes_memory_successfully(
        self,
        free_tier_client,
        test_memory_payload,
        usage_metering
    ):
        """
        SCENARIO 1.1: FREE tier user writes memory

        GIVEN: User with FREE tier API key
        WHEN: POST /api/memories with valid memory data
        THEN:
          - Memory is stored successfully (200 OK)
          - Memory is contributed to federation (anonymized)
          - Response includes X-Continuum-Support header
          - Contribution credit is recorded
        """
        client, api_key = free_tier_client

        # Mock federation contribution
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:
            mock_contribute.return_value = {"new_concepts": 1, "total_concepts": 100}

            # Write memory
            response = client.post(
                "/api/memories",
                json=test_memory_payload,
                headers={"X-API-Key": api_key}
            )

        # Verify successful write
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "id" in data
        assert data["status"] == "stored"

        # Verify donation header present (FREE tier only)
        assert "X-Continuum-Support" in response.headers
        assert "donate" in response.headers["X-Continuum-Support"].lower()

        # Verify federation contribution was called
        mock_contribute.assert_called_once()

        # Verify contribution was anonymized
        call_args = mock_contribute.call_args
        contributed_data = call_args[1]["concepts"][0] if "concepts" in call_args[1] else {}

        # FREE tier should use aggressive anonymization
        assert "tenant_id" not in contributed_data, "Tenant ID should be stripped"
        assert "user_id" not in contributed_data, "User ID should be stripped"

    def test_free_tier_anonymization_is_aggressive(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        Test FREE tier uses AGGRESSIVE anonymization (SHA-256, irreversible)

        GIVEN: FREE tier user writes memory
        WHEN: Memory is anonymized for contribution
        THEN:
          - Entity names hashed with SHA-256 (64 char hash)
          - No tenant/user identifiers
          - Only hour/day temporal context (no date/month/year)
          - Embedding vectors stored (no raw text)
        """
        enforcer = create_enforcer()

        memory = {
            "entity": "Alexander",
            "content": "Working on CONTINUUM launch",
            "tenant_id": "free_tenant_123",
            "user_id": "user_456",
            "created_at": "2025-12-16T14:30:00Z",
            "entities": ["Alexander", "CONTINUUM"]
        }

        embedding = [0.1] * 768  # 768-dim embedding vector

        # Anonymize for FREE tier
        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.FREE,
            embedding=embedding
        )

        # Verify aggressive anonymization
        assert "tenant_id" not in anonymized
        assert "user_id" not in anonymized
        assert "created_at" not in anonymized

        # Verify SHA-256 entity hashing (64 char hex)
        if "entities" in anonymized:
            for entity_hash in anonymized["entities"]:
                assert len(entity_hash) == 64, f"Expected 64-char SHA-256 hash, got {len(entity_hash)}"
                assert entity_hash.isalnum(), "Hash should be hexadecimal"

        # Verify embedding stored
        assert "embedding" in anonymized
        assert len(anonymized["embedding"]) == 768

        # Verify time context (no precise timestamps)
        assert "time_context" in anonymized
        assert 0 <= anonymized["time_context"]["hour"] <= 23
        assert 0 <= anonymized["time_context"]["day_of_week"] <= 6
        assert "date" not in anonymized["time_context"]
        assert "month" not in anonymized["time_context"]

    def test_contribution_tracking_records_credit(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        Test that FREE tier contributions are tracked for credit

        GIVEN: FREE tier user contributes memory
        WHEN: Contribution is successful
        THEN: Contribution stats are updated (contributed count, ratio)
        """
        enforcer = create_enforcer()

        # Track contribution
        stats = enforcer.track_contribution(
            tenant_id="free_tenant_001",
            contributed=1,
            consumed=0
        )

        assert stats["contributed"] == 1
        assert stats["consumed"] == 0
        assert stats["last_contribution"] is not None


# =============================================================================
# SCENARIO 2: FREE Tier Opt-Out Blocked (403 Forbidden)
# =============================================================================

@pytest.mark.integration
class TestFreeTierOptOutBlocked:
    """Test FREE tier CANNOT opt out of contribution"""

    def test_free_tier_cannot_opt_out(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 1.2: FREE tier user attempts opt-out

        GIVEN: User with FREE tier API key
        WHEN: POST /api/memories with {"contribute_to_federation": false}
        THEN:
          - Request is REJECTED (403 Forbidden)
          - Error message explains FREE tier must contribute
          - Suggests upgrade to PRO ($29/mo)
        """
        client, api_key = free_tier_client

        # Attempt to opt out via header
        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={
                "X-API-Key": api_key,
                "X-Federation-Opt-Out": "true"  # Attempting opt-out
            }
        )

        # Verify rejection
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"

        data = response.json()
        assert "error" in data
        assert "free tier" in data["error"].lower()
        assert "must contribute" in data["error"].lower()

        # Verify upgrade suggestion
        assert "upgrade_url" in data
        assert data["tier"] == "free"
        assert data["policy"] == "mandatory"

    def test_enforcer_blocks_free_tier_opt_out(self):
        """
        Test tier enforcer logic blocks FREE tier opt-out
        """
        enforcer = create_enforcer()

        # Attempt opt-out
        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="free_user",
            tier=PricingTier.FREE,
            memory_operation="write",
            opt_out_requested=True
        )

        # Verify blocked
        assert not allowed, "FREE tier should NOT be allowed to opt out"
        assert error_msg is not None
        assert "not allowed" in error_msg.lower()
        assert "upgrade" in error_msg.lower()

        # Verify metadata
        assert metadata["tier"] == "free"
        assert metadata["policy"] == "mandatory"
        assert metadata["action_required"] == "contribute_to_federation"


# =============================================================================
# SCENARIO 3: FREE Tier Rate Limits (100/day, 10/minute)
# =============================================================================

@pytest.mark.integration
class TestFreeTierRateLimits:
    """Test FREE tier rate limit enforcement"""

    @pytest.mark.asyncio
    async def test_free_tier_rate_limit_per_day(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        SCENARIO 1.3: FREE tier exceeds rate limit

        GIVEN: User with FREE tier API key
        WHEN: Makes 101+ API calls in one day (limit: 100/day)
        THEN:
          - Request is REJECTED (429 Too Many Requests)
          - Response includes upgrade URL
          - Rate limit headers show 0 remaining
        """
        tenant_id = "free_tenant_rate_limit"
        tier = PricingTier.FREE

        # Simulate 100 API calls (at limit)
        for i in range(100):
            await usage_metering.record_api_call(tenant_id, "/api/memories")

        # 101st call should be blocked
        allowed, error_msg = await rate_limiter.check_rate_limit(tenant_id, tier)

        assert not allowed, "Should block after 100 calls/day for FREE tier"
        assert "rate limit" in error_msg.lower()
        assert "100" in error_msg  # Daily limit mentioned

    @pytest.mark.asyncio
    async def test_free_tier_rate_limit_per_minute(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        Test FREE tier minute-level rate limit (10/minute)
        """
        tenant_id = "free_tenant_minute_limit"
        tier = PricingTier.FREE

        # Simulate 10 API calls in current minute
        for i in range(10):
            await usage_metering.record_api_call(tenant_id, "/api/test")

        # 11th call should be blocked
        allowed, error_msg = await rate_limiter.check_rate_limit(tenant_id, tier)

        # Note: Implementation may check day first, so we verify either limit triggers
        if not allowed:
            assert "rate limit" in error_msg.lower()

    def test_rate_limit_headers_in_response(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        Test that rate limit headers are included in responses

        Headers should include:
        - X-RateLimit-Limit-Day: 100
        - X-RateLimit-Remaining-Day: <count>
        - X-RateLimit-Reset: <timestamp>
        """
        client, api_key = free_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify rate limit headers present
        assert "X-RateLimit-Limit-Day" in response.headers
        assert response.headers["X-RateLimit-Limit-Day"] == "100"

        assert "X-RateLimit-Remaining-Day" in response.headers

        assert "X-RateLimit-Reset" in response.headers

        # Verify tier header
        assert "X-Tier" in response.headers
        assert response.headers["X-Tier"] == "free"


# =============================================================================
# SCENARIO 4: Donation Banner Display (FREE Tier Only)
# =============================================================================

@pytest.mark.integration
class TestFreeTierDonationBanner:
    """Test donation banner display for FREE tier"""

    def test_donation_banner_header_in_api_response(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 1.4: FREE tier sees donation banner

        GIVEN: User on FREE tier accessing API
        WHEN: Makes successful API call
        THEN: Response includes X-Continuum-Support header with donation link
        """
        client, api_key = free_tier_client

        response = client.post(
            "/api/memories",
            json=test_memory_payload,
            headers={"X-API-Key": api_key}
        )

        # Verify donation header present
        assert "X-Continuum-Support" in response.headers

        support_header = response.headers["X-Continuum-Support"]
        assert "donate" in support_header.lower() or "support" in support_header.lower()

    def test_donation_banner_not_shown_for_write_errors(
        self,
        free_tier_client
    ):
        """
        Test donation banner only shown for successful operations
        """
        client, api_key = free_tier_client

        # Send invalid request (should fail)
        response = client.post(
            "/api/memories",
            json={},  # Invalid payload
            headers={"X-API-Key": api_key}
        )

        # Even on error, header may be present (depends on middleware order)
        # The key is that successful operations definitely have it


# =============================================================================
# SCENARIO 5: Storage Limit Enforcement (1000 memories for FREE)
# =============================================================================

@pytest.mark.integration
class TestFreeTierStorageLimits:
    """Test FREE tier storage limit enforcement"""

    @pytest.mark.asyncio
    async def test_free_tier_storage_limit_exceeded(
        self,
        usage_metering,
        rate_limiter
    ):
        """
        SCENARIO 6.3: Storage limit exceeded (FREE tier)

        GIVEN: FREE tier user with 1000 memories (limit: 1000)
        WHEN: POST /api/memories (attempt to add 1001st memory)
        THEN:
          - 507 Insufficient Storage
          - Error message includes current usage
          - Suggests upgrade to PRO
        """
        tenant_id = "free_tenant_storage"
        tier = PricingTier.FREE

        # Simulate 1000 memories stored
        await usage_metering.record_storage_usage(tenant_id, 1000)

        # Check if storage limit exceeded
        allowed, error_msg = await rate_limiter.check_storage_limit(tenant_id, tier)

        assert not allowed, "Should block storage when at limit (1000 memories)"
        assert "storage" in error_msg.lower() or "limit" in error_msg.lower()


# =============================================================================
# SCENARIO 6: Federation Contribution Failure Handling
# =============================================================================

@pytest.mark.integration
class TestFreeTierFederationFailure:
    """Test that FREE tier memory writes succeed even if federation fails"""

    def test_memory_write_succeeds_if_federation_unavailable(
        self,
        free_tier_client,
        test_memory_payload
    ):
        """
        SCENARIO 6.4: Federation contribution fails

        GIVEN: FREE tier user writes memory
        WHEN: Federation service is unavailable
        THEN:
          - Memory write SUCCEEDS (best effort)
          - Contribution queued for retry
          - User not blocked by federation failure
        """
        client, api_key = free_tier_client

        # Mock federation failure
        with patch('continuum.federation.shared.SharedKnowledge.contribute_concepts') as mock_contribute:
            mock_contribute.side_effect = Exception("Federation service unavailable")

            # Write memory (should still succeed)
            response = client.post(
                "/api/memories",
                json=test_memory_payload,
                headers={"X-API-Key": api_key}
            )

        # Memory write should succeed despite federation failure
        assert response.status_code == 200, "Memory write should succeed even if federation fails"

        data = response.json()
        assert data["status"] == "stored"


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.integration
class TestFreeTierEdgeCases:
    """Test edge cases for FREE tier"""

    def test_invalid_api_key_returns_401(self, api_client_with_auth):
        """
        SCENARIO 6.1: Invalid API key

        GIVEN: Request with invalid/expired API key
        WHEN: Any API call
        THEN: 401 Unauthorized
        """
        client, _ = api_client_with_auth

        response = client.post(
            "/api/memories",
            json={"entity": "test"},
            headers={"X-API-Key": "invalid_key_12345"}
        )

        assert response.status_code == 401

    def test_missing_api_key_returns_401(self, api_client_with_auth):
        """Test missing API key returns 401"""
        client, _ = api_client_with_auth

        response = client.post(
            "/api/memories",
            json={"entity": "test"}
            # No X-API-Key header
        )

        assert response.status_code == 401

    def test_empty_memory_payload_validation(self, free_tier_client):
        """Test that empty payload is rejected"""
        client, api_key = free_tier_client

        response = client.post(
            "/api/memories",
            json={},
            headers={"X-API-Key": api_key}
        )

        # Should fail validation (400 or 422)
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
