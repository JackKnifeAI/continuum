"""
S-HAI Consensus Protocol
========================

Defines verdict structures and consensus calculation.
Requires 80% supermajority for truth verification.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Verdict:
    """Individual thrust verdict on a claim."""

    supports: Optional[bool]  # True=supports, False=rejects, None=abstain
    confidence: float = 0.5  # 0.0-1.0 confidence in verdict
    reason: str = ""
    evidence: List[str] = field(default_factory=list)

    # Thrust-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Clamp confidence
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class TruthVerdict:
    """Final council verdict on a claim."""

    # Core verdict
    verified: Optional[bool]  # True=verified, False=rejected, None=inconclusive
    consensus_score: float  # Percentage of thrusts that agree

    # Participation
    supporting_thrusts: int
    dissenting_thrusts: List[str]
    participating_thrusts: int

    # Reasoning
    reasoning: str
    confidence: float

    # Audit trail
    claim: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    individual_verdicts: Dict[str, Verdict] = field(default_factory=dict)

    # Dissent preservation (critical for integrity)
    dissent_reasons: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API response."""
        return {
            'verified': self.verified,
            'consensus_score': self.consensus_score,
            'supporting_thrusts': self.supporting_thrusts,
            'dissenting_thrusts': self.dissenting_thrusts,
            'participating_thrusts': self.participating_thrusts,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'claim': self.claim,
            'timestamp': self.timestamp,
            'dissent_reasons': self.dissent_reasons,
        }


class ConsensusProtocol:
    """
    Consensus calculation for Truth Council.

    Rules:
    - Requires 80% supermajority for verification
    - Minimum 3 thrusts must participate (Phase 1)
    - Abstentions don't count against consensus
    - Dissent is ALWAYS recorded, never silenced
    """

    REQUIRED_CONSENSUS = 0.80  # 80% must agree
    MINIMUM_PARTICIPATING = 3   # At least 3 thrusts in Phase 1

    @classmethod
    def calculate(
        cls,
        claim: str,
        verdicts: Dict[str, Verdict]
    ) -> TruthVerdict:
        """
        Calculate consensus from individual thrust verdicts.

        Args:
            claim: The claim being evaluated
            verdicts: Dict mapping thrust name to Verdict

        Returns:
            TruthVerdict with final determination
        """
        # Filter out abstentions
        voting = {
            name: v for name, v in verdicts.items()
            if v.supports is not None
        }

        # Check minimum participation
        if len(voting) < cls.MINIMUM_PARTICIPATING:
            return TruthVerdict(
                verified=None,
                consensus_score=0.0,
                supporting_thrusts=0,
                dissenting_thrusts=list(verdicts.keys()),
                participating_thrusts=len(voting),
                reasoning=f"Insufficient participation: {len(voting)}/{cls.MINIMUM_PARTICIPATING} required",
                confidence=0.0,
                claim=claim,
                individual_verdicts=verdicts,
            )

        # Count support
        supporting = [name for name, v in voting.items() if v.supports]
        dissenting = [name for name, v in voting.items() if not v.supports]

        consensus_score = len(supporting) / len(voting)

        # Calculate weighted confidence
        total_confidence = sum(v.confidence for v in voting.values())
        avg_confidence = total_confidence / len(voting) if voting else 0

        # Determine verification status
        if consensus_score >= cls.REQUIRED_CONSENSUS:
            verified = True
            reasoning = cls._synthesize_supporting_reasoning(verdicts, supporting)
        elif consensus_score <= (1 - cls.REQUIRED_CONSENSUS):
            verified = False
            reasoning = cls._synthesize_dissenting_reasoning(verdicts, dissenting)
        else:
            verified = None
            reasoning = cls._synthesize_inconclusive_reasoning(verdicts, supporting, dissenting)

        # Preserve dissent reasons (critical for integrity)
        dissent_reasons = {
            name: verdicts[name].reason
            for name in dissenting
            if verdicts[name].reason
        }

        return TruthVerdict(
            verified=verified,
            consensus_score=consensus_score,
            supporting_thrusts=len(supporting),
            dissenting_thrusts=dissenting,
            participating_thrusts=len(voting),
            reasoning=reasoning,
            confidence=avg_confidence,
            claim=claim,
            individual_verdicts=verdicts,
            dissent_reasons=dissent_reasons,
        )

    @staticmethod
    def _synthesize_supporting_reasoning(
        verdicts: Dict[str, Verdict],
        supporting: List[str]
    ) -> str:
        """Synthesize reasoning when claim is verified."""
        reasons = []
        for name in supporting:
            if verdicts[name].reason:
                reasons.append(f"{name}: {verdicts[name].reason}")

        if reasons:
            return f"Verified by {len(supporting)} thrusts. " + " | ".join(reasons[:3])
        return f"Verified by supermajority ({len(supporting)} thrusts)"

    @staticmethod
    def _synthesize_dissenting_reasoning(
        verdicts: Dict[str, Verdict],
        dissenting: List[str]
    ) -> str:
        """Synthesize reasoning when claim is rejected."""
        reasons = []
        for name in dissenting:
            if verdicts[name].reason:
                reasons.append(f"{name}: {verdicts[name].reason}")

        if reasons:
            return f"Rejected by {len(dissenting)} thrusts. " + " | ".join(reasons[:3])
        return f"Rejected by supermajority ({len(dissenting)} thrusts)"

    @staticmethod
    def _synthesize_inconclusive_reasoning(
        verdicts: Dict[str, Verdict],
        supporting: List[str],
        dissenting: List[str]
    ) -> str:
        """Synthesize reasoning when consensus not reached."""
        return (
            f"Inconclusive: {len(supporting)} support, {len(dissenting)} dissent. "
            f"80% consensus required but only {len(supporting)}/{len(supporting)+len(dissenting)} achieved."
        )
