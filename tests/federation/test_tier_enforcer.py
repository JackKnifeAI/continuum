"""
Tests for Federation Contribution Enforcement

Tests tier-based contribution policies and anonymization levels.
"""

import pytest
from continuum.federation.tier_enforcer import (
    TierBasedContributionEnforcer,
    AnonymizationLevel,
    ContributionPolicy,
    create_enforcer,
)
from continuum.billing.tiers import PricingTier


class TestTierBasedContributionEnforcer:
    """Test tier-based contribution enforcement"""

    def test_free_tier_cannot_opt_out(self):
        """FREE tier users cannot opt out of contribution"""
        enforcer = create_enforcer()

        allowed, error_msg = enforcer.check_contribution_allowed(
            tier=PricingTier.FREE,
            opt_out_requested=True
        )

        assert not allowed, "FREE tier should not be allowed to opt out"
        assert "not allowed" in error_msg.lower()
        assert "upgrade" in error_msg.lower()

    def test_pro_tier_can_opt_out(self):
        """PRO tier users can opt out of contribution"""
        enforcer = create_enforcer()

        allowed, error_msg = enforcer.check_contribution_allowed(
            tier=PricingTier.PRO,
            opt_out_requested=True
        )

        assert allowed, "PRO tier should be allowed to opt out"
        assert error_msg is None

    def test_enterprise_tier_can_opt_out(self):
        """ENTERPRISE tier users can opt out of contribution"""
        enforcer = create_enforcer()

        allowed, error_msg = enforcer.check_contribution_allowed(
            tier=PricingTier.ENTERPRISE,
            opt_out_requested=True
        )

        assert allowed, "ENTERPRISE tier should be allowed to opt out"
        assert error_msg is None

    def test_free_tier_mandatory_contribution(self):
        """FREE tier has mandatory contribution policy"""
        enforcer = create_enforcer()
        config = enforcer.get_tier_config(PricingTier.FREE)

        assert config.policy == ContributionPolicy.MANDATORY
        assert config.can_opt_out is False
        assert config.anonymization_level == AnonymizationLevel.AGGRESSIVE

    def test_pro_tier_optional_contribution(self):
        """PRO tier has optional contribution policy"""
        enforcer = create_enforcer()
        config = enforcer.get_tier_config(PricingTier.PRO)

        assert config.policy == ContributionPolicy.OPTIONAL
        assert config.can_opt_out is True
        assert config.anonymization_level == AnonymizationLevel.STANDARD

    def test_enterprise_tier_no_anonymization(self):
        """ENTERPRISE tier has no anonymization"""
        enforcer = create_enforcer()
        config = enforcer.get_tier_config(PricingTier.ENTERPRISE)

        assert config.policy == ContributionPolicy.OPTIONAL
        assert config.can_opt_out is True
        assert config.anonymization_level == AnonymizationLevel.NONE


class TestAnonymization:
    """Test anonymization levels"""

    def test_enterprise_no_anonymization(self):
        """ENTERPRISE tier: No anonymization"""
        enforcer = create_enforcer()

        memory = {
            "concept": "Quantum Entanglement",
            "description": "Non-local correlation",
            "tenant_id": "enterprise_tenant",
            "user_id": "john.doe",
            "entities": ["particle_A", "particle_B"],
            "created_at": "2025-12-16T10:00:00Z"
        }

        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.ENTERPRISE
        )

        # Should keep everything (no anonymization)
        assert anonymized["concept"] == memory["concept"]
        assert anonymized["tenant_id"] == memory["tenant_id"]
        assert anonymized["user_id"] == memory["user_id"]
        assert anonymized["entities"] == memory["entities"]

    def test_pro_standard_anonymization(self):
        """PRO tier: Standard anonymization (reversible)"""
        enforcer = create_enforcer()

        memory = {
            "concept": "Neural Networks",
            "description": "Deep learning models",
            "tenant_id": "pro_tenant",
            "user_id": "jane.smith",
            "entities": ["neuron", "activation"],
            "created_at": "2025-12-16T10:30:00Z"
        }

        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.PRO
        )

        # Should remove tenant/user IDs
        assert "tenant_id" not in anonymized
        assert "user_id" not in anonymized

        # Should keep content
        assert anonymized["concept"] == memory["concept"]
        assert anonymized["description"] == memory["description"]

        # Should hash entities (reversible)
        assert "entities" in anonymized
        assert anonymized["entities"] != memory["entities"]
        assert all(e.startswith("hash_") for e in anonymized["entities"])

        # Should generalize timestamp to day only
        assert "created_at" in anonymized
        assert anonymized["created_at"] == "2025-12-16"

    def test_free_aggressive_anonymization(self):
        """FREE tier: Aggressive anonymization (irreversible)"""
        enforcer = create_enforcer()

        memory = {
            "concept": "Transformers Architecture",
            "description": "Attention-based neural network architecture for NLP",
            "tenant_id": "free_tenant",
            "user_id": "bob.jones",
            "session_id": "session_123",
            "entities": ["attention", "transformer", "bert"],
            "created_at": "2025-12-16T14:30:00Z"
        }

        embedding = [0.1] * 768  # 768-dim vector

        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.FREE,
            embedding=embedding
        )

        # Should strip ALL personal identifiers
        assert "tenant_id" not in anonymized
        assert "user_id" not in anonymized
        assert "session_id" not in anonymized
        assert "created_at" not in anonymized

        # Should keep embedding
        assert "embedding" in anonymized
        assert anonymized["embedding"] == embedding

        # Should hash entities with SHA-256 (irreversible)
        assert "entities" in anonymized
        assert anonymized["entities"] != memory["entities"]
        # SHA-256 hashes are 64 chars
        assert all(len(e) == 64 for e in anonymized["entities"])

        # Should have generalized time context (hour/day only)
        assert "time_context" in anonymized
        assert 0 <= anonymized["time_context"]["hour"] <= 23
        assert 0 <= anonymized["time_context"]["day_of_week"] <= 6
        # Should NOT have date/month/year
        assert "date" not in anonymized["time_context"]
        assert "month" not in anonymized["time_context"]

    def test_free_tier_truncates_text(self):
        """FREE tier truncates long text snippets"""
        enforcer = create_enforcer()

        long_text = "A" * 200  # 200 characters
        memory = {
            "concept": long_text,
            "description": "Test description"
        }

        embedding = [0.1] * 768

        anonymized = enforcer.anonymize_memory(
            memory=memory,
            tier=PricingTier.FREE,
            embedding=embedding
        )

        # Should truncate to 100 chars + "..."
        assert len(anonymized["concept"]) == 103
        assert anonymized["concept"].endswith("...")


class TestEnforceContribution:
    """Test contribution enforcement"""

    def test_free_tier_mandatory_enforcement(self):
        """FREE tier: Contribution is mandatory"""
        enforcer = create_enforcer()

        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="free_user",
            tier=PricingTier.FREE,
            memory_operation="write",
            opt_out_requested=False
        )

        assert allowed, "Should allow contribution when not opted out"
        assert metadata["policy"] == "mandatory"
        assert metadata["contribution_required"] is True
        assert metadata["anonymization_level"] == "aggressive"

    def test_free_tier_blocks_opt_out(self):
        """FREE tier: Blocks opt-out attempts"""
        enforcer = create_enforcer()

        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="free_user",
            tier=PricingTier.FREE,
            memory_operation="write",
            opt_out_requested=True  # Attempting opt-out
        )

        assert not allowed, "Should block opt-out for FREE tier"
        assert error_msg is not None
        assert "not allowed" in error_msg.lower()
        assert metadata["action_required"] == "contribute_to_federation"

    def test_pro_tier_optional_enforcement(self):
        """PRO tier: Contribution is optional"""
        enforcer = create_enforcer()

        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="pro_user",
            tier=PricingTier.PRO,
            memory_operation="write",
            opt_out_requested=True  # Opting out
        )

        assert allowed, "PRO tier should allow opt-out"
        assert error_msg is None
        assert metadata["policy"] == "optional"
        assert metadata["can_opt_out"] is True

    def test_enterprise_tier_bypass(self):
        """ENTERPRISE tier: Bypasses enforcement"""
        enforcer = create_enforcer()

        allowed, error_msg, metadata = enforcer.enforce_contribution(
            tenant_id="enterprise_user",
            tier=PricingTier.ENTERPRISE,
            memory_operation="write",
            opt_out_requested=True
        )

        assert allowed, "ENTERPRISE tier should bypass enforcement"
        assert error_msg is None
        assert metadata["policy"] == "optional"
        assert metadata["anonymization_level"] == "none"


class TestContributionTracking:
    """Test contribution tracking"""

    def test_track_contribution(self):
        """Track contribution stats for a tenant"""
        enforcer = create_enforcer()

        stats = enforcer.track_contribution(
            tenant_id="test_tenant",
            contributed=10,
            consumed=5
        )

        assert stats["contributed"] == 10
        assert stats["consumed"] == 5
        assert stats["ratio"] == 2.0
        assert stats["last_contribution"] is not None

    def test_track_multiple_contributions(self):
        """Track multiple contributions from same tenant"""
        enforcer = create_enforcer()

        # First contribution
        enforcer.track_contribution("test_tenant", contributed=5, consumed=0)

        # Second contribution
        stats = enforcer.track_contribution("test_tenant", contributed=3, consumed=2)

        assert stats["contributed"] == 8  # 5 + 3
        assert stats["consumed"] == 2
        assert stats["ratio"] == 4.0  # 8 / 2

    def test_get_contribution_stats(self):
        """Get contribution stats for a tenant"""
        enforcer = create_enforcer()

        # Track some contributions
        enforcer.track_contribution("tenant_1", contributed=10, consumed=5)

        # Get stats
        stats = enforcer.get_contribution_stats("tenant_1")

        assert stats["contributed"] == 10
        assert stats["consumed"] == 5
        assert stats["ratio"] == 2.0

    def test_get_stats_for_new_tenant(self):
        """Get stats for tenant with no contributions"""
        enforcer = create_enforcer()

        stats = enforcer.get_contribution_stats("new_tenant")

        assert stats["contributed"] == 0
        assert stats["consumed"] == 0
        assert stats["ratio"] == 0.0
        assert stats["last_contribution"] is None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_consumption_ratio(self):
        """Handle zero consumption when calculating ratio"""
        enforcer = create_enforcer()

        stats = enforcer.track_contribution(
            tenant_id="test_tenant",
            contributed=10,
            consumed=0
        )

        # Should handle division by zero
        assert stats["ratio"] == 0.0

    def test_empty_memory_anonymization(self):
        """Handle empty memory objects"""
        enforcer = create_enforcer()

        anonymized = enforcer.anonymize_memory(
            memory={},
            tier=PricingTier.FREE
        )

        # Should return time_context for FREE tier
        assert "time_context" in anonymized

    def test_unknown_tier_handling(self):
        """Handle unknown pricing tiers"""
        enforcer = create_enforcer()

        with pytest.raises(ValueError):
            enforcer.get_tier_config("unknown_tier")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
