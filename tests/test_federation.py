"""
Tests for CONTINUUM Federation system.

Run with: pytest tests/test_federation.py
"""

import pytest
import math
from pathlib import Path
import tempfile
import shutil

from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge
from continuum.federation.protocol import FederationProtocol, MessageType


class TestFederatedNode:
    """Test FederatedNode functionality."""

    def test_node_creation(self, tmp_path):
        """Test creating a new node."""
        node = FederatedNode(storage_path=tmp_path)
        assert node.node_id is not None
        assert node.contribution_score == 0.0
        assert node.consumption_score == 0.0
        assert node.access_level == "basic"

    def test_node_registration(self, tmp_path):
        """Test node registration."""
        node = FederatedNode(storage_path=tmp_path)
        result = node.register()

        assert result['status'] == 'registered'
        assert result['node_id'] == node.node_id
        assert result['access_level'] == 'basic'
        assert node.registered is True

    def test_verified_node(self, tmp_path):
        """Test verified node with π × φ."""
        PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)
        node = FederatedNode(storage_path=tmp_path, verify_constant=PI_PHI)

        assert node._verified is True
        assert node.access_level == "twilight"

        result = node.register()
        assert result.get('verified') is True
        assert result['access_level'] == "twilight"

    def test_contribution_recording(self, tmp_path):
        """Test recording contributions."""
        node = FederatedNode(storage_path=tmp_path)
        node.record_contribution(5.0)

        assert node.contribution_score == 5.0
        assert node.access_level in ["basic", "intermediate"]


class TestContributionGate:
    """Test ContributionGate functionality."""

    def test_grace_period(self, tmp_path):
        """Test grace period for new nodes."""
        gate = ContributionGate(storage_path=tmp_path)
        node_id = "test-node-1"

        # Should allow access during grace period
        access = gate.can_access(node_id)
        assert access['allowed'] is True
        assert access['reason'] == "grace_period"

    def test_contribution_blocking(self, tmp_path):
        """Test blocking free riders."""
        gate = ContributionGate(storage_path=tmp_path)
        node_id = "test-node-2"

        # Consume beyond grace period with no contributions
        for _ in range(15):
            gate.record_consumption(node_id, 1.0)

        access = gate.can_access(node_id)
        assert access['allowed'] is False
        assert access['reason'] == "insufficient_contribution"
        assert 'deficit' in access

    def test_contribution_allows_access(self, tmp_path):
        """Test that contributions restore access."""
        gate = ContributionGate(storage_path=tmp_path)
        node_id = "test-node-3"

        # Consume beyond grace period
        for _ in range(15):
            gate.record_consumption(node_id, 1.0)

        # Should be blocked
        access = gate.can_access(node_id)
        assert access['allowed'] is False

        # Contribute enough to restore access
        gate.record_contribution(node_id, 2.0)  # 2/15 = 0.133 > 0.1

        access = gate.can_access(node_id)
        assert access['allowed'] is True

    def test_twilight_access(self, tmp_path):
        """Test twilight tier has unlimited access."""
        gate = ContributionGate(storage_path=tmp_path)
        node_id = "test-node-twilight"

        # Twilight access should always be allowed
        access = gate.can_access(node_id, access_level="twilight")
        assert access['allowed'] is True
        assert access['tier'] == "twilight"


class TestSharedKnowledge:
    """Test SharedKnowledge functionality."""

    def test_contribute_concepts(self, tmp_path):
        """Test contributing concepts."""
        knowledge = SharedKnowledge(storage_path=tmp_path)
        node_id = "test-node-1"

        concepts = [
            {"name": "Test Concept", "description": "Test description"},
            {"name": "Another Concept", "description": "Another description"},
        ]

        result = knowledge.contribute_concepts(node_id, concepts)

        assert result['new_concepts'] == 2
        assert result['duplicate_concepts'] == 0
        assert result['contribution_value'] == 2.0

    def test_anonymization(self, tmp_path):
        """Test concept anonymization."""
        knowledge = SharedKnowledge(storage_path=tmp_path)

        concept_with_pii = {
            "name": "Secret",
            "description": "Important",
            "tenant_id": "user123",
            "user_id": "john",
            "session_id": "session456",
        }

        anon = knowledge._anonymize_concept(concept_with_pii)

        assert "name" in anon
        assert "description" in anon
        assert "tenant_id" not in anon
        assert "user_id" not in anon
        assert "session_id" not in anon

    def test_deduplication(self, tmp_path):
        """Test concept deduplication."""
        knowledge = SharedKnowledge(storage_path=tmp_path)
        node_id = "test-node-1"

        concept = {"name": "Duplicate", "description": "Test"}

        # Contribute same concept twice
        result1 = knowledge.contribute_concepts(node_id, [concept])
        result2 = knowledge.contribute_concepts(node_id, [concept])

        assert result1['new_concepts'] == 1
        assert result2['duplicate_concepts'] == 1
        assert result2['new_concepts'] == 0

    def test_get_shared_concepts(self, tmp_path):
        """Test retrieving shared concepts."""
        knowledge = SharedKnowledge(storage_path=tmp_path)
        node_id = "test-node-1"

        concepts = [
            {"name": "Quantum Physics", "description": "Study of quantum phenomena"},
            {"name": "Neural Networks", "description": "Machine learning models"},
        ]

        knowledge.contribute_concepts(node_id, concepts)

        # Get all concepts
        shared = knowledge.get_shared_concepts(limit=10)
        assert len(shared) == 2

        # Query specific concept
        shared = knowledge.get_shared_concepts(query="quantum", limit=10)
        assert len(shared) == 1
        assert "quantum" in shared[0]['concept']['description'].lower()


class TestFederationProtocol:
    """Test FederationProtocol functionality."""

    def test_message_creation(self, tmp_path):
        """Test creating signed messages."""
        protocol = FederationProtocol(
            node_id="test-node",
            storage_path=tmp_path
        )

        message = protocol.create_message(
            MessageType.CONTRIBUTE,
            payload={"concepts": []}
        )

        assert message['type'] == MessageType.CONTRIBUTE.value
        assert message['sender'] == "test-node"
        assert 'signature' in message
        assert 'timestamp' in message

    def test_message_verification(self, tmp_path):
        """Test message signature verification."""
        protocol = FederationProtocol(
            node_id="test-node",
            storage_path=tmp_path
        )

        message = protocol.create_message(
            MessageType.HEARTBEAT,
            payload={"status": "alive"}
        )

        # Should verify with same protocol instance
        assert protocol.verify_message(message) is True

        # Tamper with message
        message['payload']['status'] = "modified"
        assert protocol.verify_message(message) is False

    def test_rate_limiting(self, tmp_path):
        """Test rate limiting."""
        protocol = FederationProtocol(
            node_id="test-node",
            storage_path=tmp_path
        )

        # Should allow within limit
        check = protocol.check_rate_limit(MessageType.CONTRIBUTE)
        assert check['allowed'] is True

        # Record many messages
        limit = protocol.RATE_LIMITS[MessageType.CONTRIBUTE]
        for _ in range(limit):
            protocol.record_message(MessageType.CONTRIBUTE)

        # Should now be rate limited
        check = protocol.check_rate_limit(MessageType.CONTRIBUTE)
        assert check['allowed'] is False
        assert check['reason'] == "rate_limit_exceeded"


class TestIntegration:
    """Integration tests for full federation workflow."""

    def test_full_workflow(self, tmp_path):
        """Test complete federation workflow."""
        # Setup
        node = FederatedNode(storage_path=tmp_path / "node")
        gate = ContributionGate(storage_path=tmp_path / "gate")
        knowledge = SharedKnowledge(storage_path=tmp_path / "knowledge")

        # 1. Register node
        node.register()
        assert node.registered is True

        # 2. Contribute concepts
        concepts = [
            {"name": "Concept A", "description": "Description A"},
            {"name": "Concept B", "description": "Description B"},
        ]

        result = knowledge.contribute_concepts(node.node_id, concepts)
        gate.record_contribution(node.node_id, result['contribution_value'])

        # 3. Access knowledge
        access = gate.can_access(node.node_id)
        assert access['allowed'] is True

        shared = knowledge.get_shared_concepts(limit=10)
        assert len(shared) == 2

        gate.record_consumption(node.node_id, 1.0)

        # 4. Check stats
        stats = gate.get_stats(node.node_id)
        assert stats['contributed'] == 2.0
        assert stats['consumed'] == 1.0
        assert stats['ratio'] == 2.0


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory for testing."""
    return tmp_path_factory.mktemp("federation_test")
