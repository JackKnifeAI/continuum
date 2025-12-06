"""
CONTINUUM Federation - Decentralized Knowledge Sharing

The key differentiator: "Can't use it unless you add to it"

Users must contribute knowledge to access the shared knowledge pool.
This creates a growing, collective AI knowledge graph while preserving privacy
through anonymization and blocking free riders via contribution gates.
"""

from continuum.federation.node import FederatedNode
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge

__all__ = [
    "FederatedNode",
    "ContributionGate",
    "SharedKnowledge",
]
