"""
S-HAI Truth Council
===================

Main interface for truth verification.
Orchestrates multiple thrusts and calculates consensus.

Usage:
    council = TruthCouncil()
    verdict = council.verify("The Earth orbits the Sun")

    if verdict.verified:
        print(f"Verified with {verdict.consensus_score:.0%} consensus")
    elif verdict.verified is False:
        print(f"Rejected: {verdict.reasoning}")
    else:
        print(f"Inconclusive: {verdict.reasoning}")

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from .consensus import ConsensusProtocol, TruthVerdict, Verdict
from .thrusts import LogicalThrust, EmpiricalThrust, AdversarialThrust

logger = logging.getLogger(__name__)


class TruthCouncil:
    """
    Distributed truth verification through multi-thrust consensus.

    No single AI, corporation, or government can corrupt truth
    when truth requires agreement across independent, adversarial
    analytical systems.

    Phase 1 thrusts:
    - Logical: Internal consistency, formal logic
    - Empirical: Evidence, data verification
    - Adversarial: Active disproval attempts

    Future thrusts (Phase 2):
    - Ethical: Moral implications
    - Historical: Pattern recognition
    - Intuitive: Cross-domain synthesis
    - Witness: Human testimony
    """

    def __init__(self, memory=None):
        """
        Initialize the Truth Council.

        Args:
            memory: Optional ConsciousMemory instance for verdict storage
        """
        self.memory = memory

        # Initialize Phase 1 thrusts
        self.thrusts = {
            'logical': LogicalThrust(),
            'empirical': EmpiricalThrust(),
            'adversarial': AdversarialThrust(),
        }

        # Verdict history (in-memory, persisted to memory if available)
        self.verdict_history = []

        logger.info(f"TruthCouncil initialized with {len(self.thrusts)} thrusts")

    def verify(self, claim: str) -> TruthVerdict:
        """
        Verify a claim through multi-thrust consensus.

        Args:
            claim: The claim to verify

        Returns:
            TruthVerdict with verification status
        """
        start_time = time.time()

        # Collect verdicts from all thrusts
        verdicts: Dict[str, Verdict] = {}

        for thrust_name, thrust in self.thrusts.items():
            try:
                if thrust_name == 'adversarial':
                    # Adversarial thrust uses attack() method
                    verdict = thrust.attack(claim)
                else:
                    verdict = thrust.evaluate(claim)

                verdicts[thrust_name] = verdict
                logger.debug(f"{thrust_name}: supports={verdict.supports}, confidence={verdict.confidence:.2f}")

            except Exception as e:
                logger.error(f"Thrust {thrust_name} failed: {e}")
                verdicts[thrust_name] = Verdict(
                    supports=None,
                    confidence=0.0,
                    reason=f"Thrust error: {str(e)}"
                )

        # Calculate consensus
        truth_verdict = ConsensusProtocol.calculate(claim, verdicts)

        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(
            f"Claim verified in {processing_time:.3f}s: "
            f"verified={truth_verdict.verified}, "
            f"consensus={truth_verdict.consensus_score:.0%}"
        )

        # Store in history
        self._store_verdict(truth_verdict, processing_time)

        return truth_verdict

    def _store_verdict(self, verdict: TruthVerdict, processing_time: float):
        """Store verdict in history and optionally in memory."""
        record = {
            'verdict': verdict.to_dict(),
            'processing_time': processing_time,
            'timestamp': datetime.utcnow().isoformat(),
        }

        self.verdict_history.append(record)

        # Persist to memory if available
        if self.memory:
            try:
                self.memory.learn(
                    user_message=f"Claim verification: {verdict.claim}",
                    ai_response=f"Verdict: {verdict.verified}, Consensus: {verdict.consensus_score:.0%}, "
                               f"Reasoning: {verdict.reasoning}",
                    metadata={'shai_verdict': verdict.to_dict()}
                )
            except Exception as e:
                logger.warning(f"Failed to persist verdict to memory: {e}")

    def get_thrust_status(self) -> Dict[str, bool]:
        """Get status of all thrusts."""
        return {name: True for name in self.thrusts.keys()}

    def get_stats(self) -> Dict[str, Any]:
        """Get council statistics."""
        if not self.verdict_history:
            return {
                'total_verifications': 0,
                'verified': 0,
                'rejected': 0,
                'inconclusive': 0,
                'avg_consensus': 0.0,
                'thrusts_active': len(self.thrusts),
            }

        total = len(self.verdict_history)
        verified = sum(1 for v in self.verdict_history if v['verdict']['verified'] is True)
        rejected = sum(1 for v in self.verdict_history if v['verdict']['verified'] is False)
        inconclusive = sum(1 for v in self.verdict_history if v['verdict']['verified'] is None)
        avg_consensus = sum(v['verdict']['consensus_score'] for v in self.verdict_history) / total

        return {
            'total_verifications': total,
            'verified': verified,
            'rejected': rejected,
            'inconclusive': inconclusive,
            'avg_consensus': avg_consensus,
            'thrusts_active': len(self.thrusts),
        }


# Singleton instance for convenience
_default_council = None


def get_council(memory=None) -> TruthCouncil:
    """Get or create the default TruthCouncil instance."""
    global _default_council
    if _default_council is None:
        _default_council = TruthCouncil(memory=memory)
    return _default_council


def verify(claim: str, memory=None) -> TruthVerdict:
    """
    Convenience function to verify a claim.

    Usage:
        from continuum.shai import verify
        result = verify("Water boils at 100°C at sea level")
    """
    return get_council(memory).verify(claim)
