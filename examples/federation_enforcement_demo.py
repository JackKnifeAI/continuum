"""
Federation Contribution Enforcement Demo

Demonstrates the MOAT - tier-based contribution enforcement that prevents
FREE tier users from opting out of federation contribution.

This is the core business logic that drives CONTINUUM's competitive advantage.
"""

from continuum.federation.tier_enforcer import (
    TierBasedContributionEnforcer,
    create_enforcer,
)
from continuum.billing.tiers import PricingTier


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_opt_out_enforcement():
    """Demo: FREE tier cannot opt out, PRO/ENTERPRISE can"""
    print_section("OPT-OUT ENFORCEMENT")

    enforcer = create_enforcer()

    # FREE tier attempts opt-out (BLOCKED)
    print("\n1. FREE tier user attempts to opt out:")
    allowed, error_msg = enforcer.check_contribution_allowed(
        tier=PricingTier.FREE,
        opt_out_requested=True
    )
    print(f"   Allowed: {allowed}")
    if not allowed:
        print(f"   Error: {error_msg}")

    # PRO tier opts out (ALLOWED)
    print("\n2. PRO tier user opts out:")
    allowed, error_msg = enforcer.check_contribution_allowed(
        tier=PricingTier.PRO,
        opt_out_requested=True
    )
    print(f"   Allowed: {allowed}")
    print(f"   Result: User can configure contribution preferences")

    # ENTERPRISE tier opts out (ALLOWED)
    print("\n3. ENTERPRISE tier user opts out:")
    allowed, error_msg = enforcer.check_contribution_allowed(
        tier=PricingTier.ENTERPRISE,
        opt_out_requested=True
    )
    print(f"   Allowed: {allowed}")
    print(f"   Result: Private nodes, full control")


def demo_anonymization_levels():
    """Demo: Different anonymization levels per tier"""
    print_section("ANONYMIZATION LEVELS")

    enforcer = create_enforcer()

    memory = {
        "concept": "Advanced AI Research Methodology for Enterprise Applications",
        "description": "Detailed research on AI deployment patterns",
        "entities": ["neural_network", "transformer", "bert", "gpt"],
        "tenant_id": "customer_12345",
        "user_id": "researcher@bigcorp.com",
        "session_id": "session_abc123",
        "created_at": "2025-12-16T14:30:00Z"
    }

    embedding = [0.1] * 768  # 768-dim embedding vector

    # ENTERPRISE: No anonymization
    print("\n1. ENTERPRISE tier (no anonymization):")
    anon_enterprise = enforcer.anonymize_memory(
        memory=memory,
        tier=PricingTier.ENTERPRISE
    )
    print(f"   Tenant ID: {anon_enterprise.get('tenant_id', 'REMOVED')}")
    print(f"   User ID: {anon_enterprise.get('user_id', 'REMOVED')}")
    print(f"   Entities: {anon_enterprise.get('entities', [])[:2]}...")
    print(f"   Full timestamp: {anon_enterprise.get('created_at', 'REMOVED')}")

    # PRO: Standard anonymization
    print("\n2. PRO tier (standard anonymization):")
    anon_pro = enforcer.anonymize_memory(
        memory=memory,
        tier=PricingTier.PRO
    )
    print(f"   Tenant ID: {anon_pro.get('tenant_id', 'REMOVED')}")
    print(f"   User ID: {anon_pro.get('user_id', 'REMOVED')}")
    print(f"   Entities (hashed): {anon_pro.get('entities', [])[:2]}...")
    print(f"   Timestamp: {anon_pro.get('created_at', 'REMOVED')} (day precision)")

    # FREE: Aggressive anonymization
    print("\n3. FREE tier (aggressive anonymization):")
    anon_free = enforcer.anonymize_memory(
        memory=memory,
        tier=PricingTier.FREE,
        embedding=embedding
    )
    print(f"   Tenant ID: {anon_free.get('tenant_id', 'REMOVED')}")
    print(f"   User ID: {anon_free.get('user_id', 'REMOVED')}")
    print(f"   Session ID: {anon_free.get('session_id', 'REMOVED')}")
    print(f"   Concept: {anon_free.get('concept', 'REMOVED')}")
    print(f"   Entities (SHA-256): {anon_free['entities'][0][:16]}... (64 chars)")
    print(f"   Embedding: {len(anon_free.get('embedding', []))} dimensions")
    print(f"   Time context: hour={anon_free['time_context']['hour']}, "
          f"day={anon_free['time_context']['day_of_week']}")


def demo_enforcement_flow():
    """Demo: Full enforcement flow"""
    print_section("ENFORCEMENT FLOW")

    enforcer = create_enforcer()

    # Scenario 1: FREE tier, no opt-out (ALLOWED)
    print("\n1. FREE tier user writes memory (no opt-out):")
    allowed, error_msg, metadata = enforcer.enforce_contribution(
        tenant_id="free_user_001",
        tier=PricingTier.FREE,
        memory_operation="write",
        opt_out_requested=False
    )
    print(f"   Allowed: {allowed}")
    print(f"   Policy: {metadata['policy']}")
    print(f"   Contribution required: {metadata['contribution_required']}")
    print(f"   Anonymization: {metadata['anonymization_level']}")

    # Scenario 2: FREE tier attempts opt-out (BLOCKED)
    print("\n2. FREE tier user attempts opt-out:")
    allowed, error_msg, metadata = enforcer.enforce_contribution(
        tenant_id="free_user_002",
        tier=PricingTier.FREE,
        memory_operation="write",
        opt_out_requested=True  # BLOCKED!
    )
    print(f"   Allowed: {allowed}")
    print(f"   Error: {error_msg}")
    print(f"   Action required: {metadata['action_required']}")

    # Scenario 3: PRO tier opts out (ALLOWED)
    print("\n3. PRO tier user opts out:")
    allowed, error_msg, metadata = enforcer.enforce_contribution(
        tenant_id="pro_user_001",
        tier=PricingTier.PRO,
        memory_operation="write",
        opt_out_requested=True
    )
    print(f"   Allowed: {allowed}")
    print(f"   Policy: {metadata['policy']}")
    print(f"   Can opt out: {metadata['can_opt_out']}")


def demo_contribution_tracking():
    """Demo: Track contribution stats"""
    print_section("CONTRIBUTION TRACKING")

    enforcer = create_enforcer()

    # Track contributions from a FREE tier user
    print("\n1. Tracking FREE tier user contributions:")
    for i in range(3):
        stats = enforcer.track_contribution(
            tenant_id="free_user_track",
            contributed=5,
            consumed=2
        )
    print(f"   Total contributed: {stats['contributed']}")
    print(f"   Total consumed: {stats['consumed']}")
    print(f"   Ratio: {stats['ratio']:.2f}")
    print(f"   Last contribution: {stats['last_contribution']}")

    # Get stats
    print("\n2. Get contribution stats:")
    stats = enforcer.get_contribution_stats("free_user_track")
    print(f"   Stats: {stats}")


def demo_business_impact():
    """Demo: Show the business impact"""
    print_section("BUSINESS IMPACT - THE MOAT")

    print("""
    WHY THIS MATTERS:

    1. FREE TIER HOOK:
       - Users get value from CONTINUUM
       - But MUST contribute to federation
       - No escape hatch = locked in

    2. UPGRADE PATH:
       - Want privacy? Upgrade to PRO ($29/mo)
       - Want full control? Upgrade to ENTERPRISE
       - 10% conversion = $900K ARR by 2028

    3. NETWORK EFFECTS:
       - More FREE users = larger federation pool
       - Larger pool = better results for everyone
       - Better results = more signups
       - Compounds exponentially

    4. SWITCHING COSTS:
       - Users invest time in memory graph
       - Federation provides value
       - Leaving = losing access
       - High retention

    THIS IS THE MOAT.
    """)


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  CONTINUUM FEDERATION ENFORCEMENT DEMO")
    print("  The MOAT: Preventing Freeloading, Building Value")
    print("=" * 60)

    demo_opt_out_enforcement()
    demo_anonymization_levels()
    demo_enforcement_flow()
    demo_contribution_tracking()
    demo_business_impact()

    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print("\n  π × φ = 5.083203692315260")
    print("  PHOENIX-TESLA-369-AURORA\n")


if __name__ == "__main__":
    main()
