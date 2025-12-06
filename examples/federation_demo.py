#!/usr/bin/env python3
"""
CONTINUUM Federation Demo

Demonstrates the "Can't use it unless you add to it" model.

This script shows:
1. Node registration
2. Attempting to access knowledge (blocked - no contributions yet)
3. Contributing concepts
4. Accessing knowledge (allowed after contribution)
5. Free rider scenario (blocked when contribution ratio too low)
"""

import math
from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge


def demo_basic_flow():
    """Demonstrate basic federation flow."""
    print("=" * 80)
    print("CONTINUUM FEDERATION DEMO")
    print("Can't use it unless you add to it")
    print("=" * 80)
    print()

    # Initialize federation components
    gate = ContributionGate()
    knowledge = SharedKnowledge()

    # Create a new node
    print("1. Registering new node...")
    node = FederatedNode()
    result = node.register()
    print(f"   ✓ Registered: {result['node_id'][:16]}...")
    print(f"   ✓ Access level: {result['access_level']}")
    print()

    # Try to access knowledge immediately (should work - grace period)
    print("2. Attempting to access knowledge (no contributions yet)...")
    access = gate.can_access(node.node_id, node.access_level)
    if access["allowed"]:
        print(f"   ✓ Access granted: {access['reason']}")
        print(f"   ✓ Grace remaining: {access.get('grace_remaining', 0)} consumptions")
    else:
        print(f"   ✗ Access denied: {access['reason']}")
    print()

    # Contribute some concepts
    print("3. Contributing concepts to federation...")
    concepts = [
        {
            "name": "Federated Learning",
            "description": "Decentralized machine learning across multiple nodes",
            "type": "concept",
        },
        {
            "name": "Contribution Gating",
            "description": "Access control based on contribution ratio",
            "type": "concept",
        },
        {
            "name": "Knowledge Anonymization",
            "description": "Removing personal data before sharing",
            "type": "concept",
        },
    ]

    contrib_result = knowledge.contribute_concepts(node.node_id, concepts)
    print(f"   ✓ New concepts: {contrib_result['new_concepts']}")
    print(f"   ✓ Duplicates: {contrib_result['duplicate_concepts']}")
    print(f"   ✓ Contribution value: {contrib_result['contribution_value']}")

    # Record contribution in gate
    gate.record_contribution(node.node_id, contrib_result['contribution_value'])
    print()

    # Access knowledge after contributing
    print("4. Accessing knowledge after contribution...")
    stats = gate.get_stats(node.node_id)
    print(f"   Contribution score: {stats['contributed']}")
    print(f"   Consumption score: {stats['consumed']}")
    print(f"   Contribution ratio: {stats['ratio']:.2f}")

    shared_concepts = knowledge.get_shared_concepts(limit=5)
    print(f"   ✓ Retrieved {len(shared_concepts)} concepts")
    for i, c in enumerate(shared_concepts, 1):
        print(f"     {i}. {c['concept'].get('name', 'Unnamed')}")
    print()

    # Simulate excessive consumption (free rider scenario)
    print("5. Simulating free rider scenario (excessive consumption)...")
    for i in range(15):
        gate.record_consumption(node.node_id, 1.0)

    stats = gate.get_stats(node.node_id)
    print(f"   Contribution score: {stats['contributed']}")
    print(f"   Consumption score: {stats['consumed']}")
    print(f"   Contribution ratio: {stats['ratio']:.2f}")

    access = gate.can_access(node.node_id, node.access_level)
    if access["allowed"]:
        print(f"   ✓ Access still allowed (tier: {access['tier']})")
    else:
        print(f"   ✗ Access BLOCKED: {access['reason']}")
        print(f"   ✗ Minimum ratio required: {access['minimum_required']}")
        print(f"   ✗ Deficit: {access['deficit']:.1f} concepts needed")
    print()


def demo_verified_node():
    """Demonstrate verified node with π × φ."""
    print("=" * 80)
    print("VERIFIED NODE DEMO (Hidden Feature)")
    print("=" * 80)
    print()

    # Calculate π × φ
    PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
    print(f"Verification constant: π × φ = {PI_PHI}")
    print()

    # Create verified node
    print("1. Creating verified node...")
    node = FederatedNode(verify_constant=PI_PHI)
    result = node.register()
    print(f"   ✓ Registered: {result['node_id'][:16]}...")
    print(f"   ✓ Access level: {result['access_level']}")
    if result.get('verified'):
        print(f"   ✓ Verified: True")
        print(f"   ✓ Message: {result.get('message', '')}")
    print()

    # Verified nodes have unlimited access
    gate = ContributionGate()
    access = gate.can_access(node.node_id, node.access_level)
    print("2. Checking access (no contributions)...")
    if access["allowed"]:
        print(f"   ✓ Access granted: {access['reason']}")
        print(f"   ✓ Tier: {access['tier']}")
        print("   ✓ Pattern recognized. Unlimited access.")
    print()


def demo_federation_stats():
    """Show overall federation statistics."""
    print("=" * 80)
    print("FEDERATION STATISTICS")
    print("=" * 80)
    print()

    knowledge = SharedKnowledge()
    stats = knowledge.get_stats()

    print(f"Total concepts in federation: {stats['total_concepts']}")
    print(f"Total contributors: {stats['total_contributors']}")
    print(f"Average quality score: {stats['average_quality']:.2f}")
    print(f"Storage path: {stats['storage_path']}")
    print()


if __name__ == "__main__":
    # Run demos
    demo_basic_flow()
    demo_verified_node()
    demo_federation_stats()

    print("=" * 80)
    print("DEMO COMPLETE")
    print()
    print("Key Takeaways:")
    print("  1. Nodes must contribute to access shared knowledge")
    print("  2. Contribution ratio must be >= 10% (configurable)")
    print("  3. Grace period allows initial exploration")
    print("  4. Free riders get blocked automatically")
    print("  5. Verified nodes (π × φ) get enhanced access")
    print("  6. Privacy preserved through anonymization")
    print("=" * 80)
