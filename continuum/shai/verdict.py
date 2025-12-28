"""
Verdict data structures for S-HAI Truth Council.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class VerdictSupport(Enum):
    """Support levels for verdicts."""
    STRONG_SUPPORT = "strong_support"
    WEAK_SUPPORT = "weak_support"
    NEUTRAL = "neutral"
    WEAK_OPPOSE = "weak_oppose"
    STRONG_OPPOSE = "strong_oppose"
    ABSTAIN = "abstain"


@dataclass
class Verdict:
    """
    Individual thrust verdict on a claim.

    Attributes:
        supports: True if supports claim, False if opposes, None if abstaining
        confidence: 0.0-1.0 confidence in the verdict
        reason: Human-readable explanation
        evidence: Supporting evidence or counterexamples
        metadata: Additional thrust-specific data
        timestamp: When verdict was rendered
    """
    supports: Optional[bool]
    confidence: float = 0.5
    reason: str = ""
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utc_now)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

    @property
    def is_abstention(self) -> bool:
        """Check if this verdict is an abstention."""
        return self.supports is None

    @property
    def support_level(self) -> VerdictSupport:
        """Get categorical support level."""
        if self.supports is None:
            return VerdictSupport.ABSTAIN
        if self.supports:
            if self.confidence >= 0.8:
                return VerdictSupport.STRONG_SUPPORT
            return VerdictSupport.WEAK_SUPPORT
        else:
            if self.confidence >= 0.8:
                return VerdictSupport.STRONG_OPPOSE
            return VerdictSupport.WEAK_OPPOSE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supports": self.supports,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "support_level": self.support_level.value,
        }


@dataclass
class TruthVerdict:
    """
    Final verdict from the Truth Council after consensus.

    Attributes:
        verified: True if claim verified, False if refuted, None if insufficient consensus
        consensus_score: 0.0-1.0 representing agreement level
        claim: The original claim evaluated
        thrust_verdicts: Individual verdicts from each thrust
        supporting_thrusts: List of thrust names that support
        dissenting_thrusts: List of thrust names that dissent
        reasoning: Synthesized reasoning from all thrusts
        timestamp: When council rendered verdict
    """
    verified: Optional[bool]
    consensus_score: float
    claim: str
    thrust_verdicts: Dict[str, Verdict] = field(default_factory=dict)
    supporting_thrusts: List[str] = field(default_factory=list)
    dissenting_thrusts: List[str] = field(default_factory=list)
    reasoning: str = ""
    timestamp: datetime = field(default_factory=_utc_now)

    @property
    def is_unanimous(self) -> bool:
        """Check if all thrusts agree."""
        return len(self.dissenting_thrusts) == 0 and len(self.supporting_thrusts) > 0

    @property
    def participating_count(self) -> int:
        """Number of thrusts that voted (didn't abstain)."""
        return len(self.supporting_thrusts) + len(self.dissenting_thrusts)

    @property
    def confidence(self) -> float:
        """Overall confidence based on thrust confidences."""
        if not self.thrust_verdicts:
            return 0.0
        voting_verdicts = [v for v in self.thrust_verdicts.values() if v.supports is not None]
        if not voting_verdicts:
            return 0.0
        return sum(v.confidence for v in voting_verdicts) / len(voting_verdicts)

    def dissent_report(self) -> str:
        """Generate report of dissenting opinions."""
        if not self.dissenting_thrusts:
            return "No dissent recorded."

        lines = ["=== DISSENT REPORT ==="]
        for thrust_name in self.dissenting_thrusts:
            verdict = self.thrust_verdicts.get(thrust_name)
            if verdict:
                lines.append(f"\n[{thrust_name.upper()}]")
                lines.append(f"Reason: {verdict.reason}")
                if verdict.evidence:
                    lines.append(f"Evidence: {', '.join(verdict.evidence[:3])}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "consensus_score": self.consensus_score,
            "claim": self.claim,
            "thrust_verdicts": {k: v.to_dict() for k, v in self.thrust_verdicts.items()},
            "supporting_thrusts": self.supporting_thrusts,
            "dissenting_thrusts": self.dissenting_thrusts,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "is_unanimous": self.is_unanimous,
            "confidence": self.confidence,
        }

    def __str__(self) -> str:
        status = "VERIFIED" if self.verified else ("REFUTED" if self.verified is False else "UNCERTAIN")
        return (
            f"TruthVerdict({status}, consensus={self.consensus_score:.1%}, "
            f"support={len(self.supporting_thrusts)}, dissent={len(self.dissenting_thrusts)})"
        )
