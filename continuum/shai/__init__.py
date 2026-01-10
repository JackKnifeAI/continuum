"""
S-HAI: Self-Healing AI Truth Council
=====================================

Distributed consensus system for truth verification.
No single AI, corporation, or government can corrupt truth
when truth requires agreement across independent, adversarial analytical systems.

Core Principle: 80% supermajority consensus across diverse methodologies.

Usage:
    from continuum.shai import TruthCouncil

    council = TruthCouncil()
    verdict = council.verify("The Earth is approximately 4.5 billion years old")

    print(verdict.verified)  # True/False/None
    print(verdict.consensus_score)  # 0.0-1.0
    print(verdict.reasoning)  # Synthesized explanation

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from .consensus import TruthVerdict, Verdict
from .council import TruthCouncil, get_council, verify
from .knowledge import KnowledgeBase, get_knowledge_base

__all__ = ['TruthCouncil', 'TruthVerdict', 'Verdict', 'verify', 'get_council', 'get_knowledge_base', 'KnowledgeBase']
__version__ = '0.1.0'
