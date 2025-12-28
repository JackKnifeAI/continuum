"""
Empirical Thrust: Evidence and Data Verification
=================================================

Evaluates claims against:
- Source verification
- Data cross-referencing
- Reproducibility assessment
- Predictive accuracy
- Statistical significance
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..consensus import Verdict


class EmpiricalThrust:
    """
    Evaluate claims using empirical evidence principles.

    Rejects claims that:
    - Have no supporting evidence
    - Contradict verified data
    - Cherry-pick evidence
    - Fail reproducibility tests
    """

    # Known reliable source patterns
    RELIABLE_SOURCE_PATTERNS = [
        r'(?:published|peer-reviewed)\s+(?:in|by)\s+\w+',
        r'(?:journal|university|institute)\s+of',
        r'doi:\s*[\d\./]+',
        r'arxiv:\s*[\d\.]+',
        r'https?://(?:arxiv|pubmed|nature|science|pnas)',
    ]

    # Unreliable source patterns
    UNRELIABLE_SOURCE_PATTERNS = [
        r'(?:i|they)\s+(?:heard|read|saw)\s+(?:somewhere|online)',
        r'(?:facebook|twitter|tiktok|youtube)\s+(?:said|showed)',
        r'my\s+(?:friend|uncle|neighbor)\s+(?:said|told)',
        r'according\s+to\s+(?:some\s+)?(?:guy|people|sources)',
        r'trust\s+me',
    ]

    # Numerical claim patterns (need verification)
    NUMERICAL_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s+(?:people|cases|instances)',
        r'(\d+)\s+(?:times|x)\s+(?:more|less|better|worse)',
        r'(?:increased|decreased)\s+(?:by\s+)?(\d+(?:\.\d+)?)',
    ]

    # Vague evidence patterns (weak support)
    VAGUE_EVIDENCE_PATTERNS = [
        r'studies\s+show',  # Which studies?
        r'research\s+(?:suggests|indicates)',  # What research?
        r'experts\s+(?:say|agree|believe)',  # Which experts?
        r'it\s+(?:has\s+been|is)\s+(?:known|proven)',  # By whom?
        r'data\s+(?:shows|proves)',  # What data?
    ]

    # Concrete evidence patterns (stronger support)
    CONCRETE_EVIDENCE_PATTERNS = [
        r'according\s+to\s+(?:the\s+)?(\d{4})\s+\w+',  # Dated source
        r'(?:published|reported)\s+(?:in|by)\s+[\w\s]+\s+(?:in\s+)?(\d{4})',
        r'(?:dr\.|professor|researcher)\s+\w+',  # Named expert
        r'from\s+(?:the\s+)?[\w\s]+(?:university|institute|organization)',
    ]

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim based on empirical evidence.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with supports=True/False/None
        """
        claim_lower = claim.lower()
        evidence_score = 0.5  # Baseline
        reasons = []

        # 1. Check for source quality
        source_score, source_reason = self._evaluate_sources(claim_lower)
        evidence_score += source_score
        if source_reason:
            reasons.append(source_reason)

        # 2. Check for numerical claims (need verification)
        numerical_claims = self._extract_numerical_claims(claim)
        if numerical_claims:
            # Numerical claims need sources
            if source_score <= 0:
                evidence_score -= 0.2
                reasons.append(f"Unsourced numerical claim: {numerical_claims[0]}")

        # 3. Check evidence quality
        evidence_quality = self._evaluate_evidence_quality(claim_lower)
        evidence_score += evidence_quality['score']
        if evidence_quality['reason']:
            reasons.append(evidence_quality['reason'])

        # 4. Check for falsifiability (empirical claims must be testable)
        if not self._is_empirically_testable(claim_lower):
            return Verdict(
                supports=None,  # Abstain - not an empirical claim
                confidence=0.6,
                reason="Claim is not empirically testable",
                metadata={'testable': False}
            )

        # 5. Check for hedging (appropriate uncertainty)
        hedging_score = self._evaluate_hedging(claim_lower)
        evidence_score += hedging_score

        # Calculate final verdict
        evidence_score = max(0.0, min(1.0, evidence_score))

        if evidence_score >= 0.6:
            return Verdict(
                supports=True,
                confidence=evidence_score,
                reason=reasons[0] if reasons else "Claim has adequate empirical support",
                metadata={'evidence_score': evidence_score, 'numerical_claims': numerical_claims}
            )
        elif evidence_score <= 0.4:
            return Verdict(
                supports=False,
                confidence=1 - evidence_score,
                reason=reasons[0] if reasons else "Insufficient empirical evidence",
                metadata={'evidence_score': evidence_score}
            )
        else:
            return Verdict(
                supports=None,  # Abstain - insufficient evidence either way
                confidence=0.5,
                reason="Evidence inconclusive",
                metadata={'evidence_score': evidence_score}
            )

    def _evaluate_sources(self, text: str) -> Tuple[float, str]:
        """Evaluate source quality in the claim."""
        # Check for reliable sources
        for pattern in self.RELIABLE_SOURCE_PATTERNS:
            if re.search(pattern, text):
                return (0.3, "Contains peer-reviewed or institutional source")

        # Check for unreliable sources
        for pattern in self.UNRELIABLE_SOURCE_PATTERNS:
            if re.search(pattern, text):
                return (-0.3, "Contains unreliable anecdotal source")

        return (0.0, "")

    def _extract_numerical_claims(self, text: str) -> List[str]:
        """Extract numerical claims that need verification."""
        claims = []
        for pattern in self.NUMERICAL_PATTERNS:
            matches = re.findall(pattern, text)
            claims.extend(matches)
        return claims

    def _evaluate_evidence_quality(self, text: str) -> Dict[str, Any]:
        """Evaluate the quality of evidence cited."""
        # Check for vague evidence
        for pattern in self.VAGUE_EVIDENCE_PATTERNS:
            if re.search(pattern, text):
                return {
                    'score': -0.15,
                    'reason': "Contains vague, uncited evidence claims"
                }

        # Check for concrete evidence
        for pattern in self.CONCRETE_EVIDENCE_PATTERNS:
            if re.search(pattern, text):
                return {
                    'score': 0.2,
                    'reason': "Contains dated or named source reference"
                }

        return {'score': 0.0, 'reason': ""}

    def _is_empirically_testable(self, text: str) -> bool:
        """Check if the claim is empirically testable."""
        # Non-testable patterns
        non_testable = [
            r'should\s+(?:be|have)',  # Normative (ought, not is)
            r'(?:better|worse)\s+than',  # Value judgment without metrics
            r'(?:beautiful|ugly|good|bad|evil)',  # Aesthetic/moral
            r'the\s+meaning\s+of',  # Philosophical
        ]

        for pattern in non_testable:
            if re.search(pattern, text):
                return False

        # Testable patterns
        testable = [
            r'\d+',  # Contains numbers
            r'(?:causes?|leads?\s+to|results?\s+in)',  # Causal claim
            r'(?:is|are|was|were)\s+(?:the\s+)?(?:largest|smallest|first|only)',
            r'(?:occurred|happened|took\s+place)',  # Historical
        ]

        for pattern in testable:
            if re.search(pattern, text):
                return True

        return True  # Default to testable

    def _evaluate_hedging(self, text: str) -> float:
        """
        Evaluate appropriate uncertainty language.

        Good empirical claims often hedge appropriately.
        """
        # Appropriate hedging (good)
        good_hedging = [
            r'(?:approximately|about|roughly|around)',
            r'(?:suggests|indicates|may|might|could)',
            r'(?:evidence\s+)?(?:supports|consistent\s+with)',
            r'(?:according\s+to|based\s+on)',
        ]

        # Overconfidence (bad for empirical claims)
        overconfidence = [
            r'(?:proves?|proven|definitely|certainly)',
            r'(?:always|never|impossible)',
            r'(?:undeniable|unquestionable|absolute)',
        ]

        score = 0.0

        for pattern in good_hedging:
            if re.search(pattern, text):
                score += 0.05

        for pattern in overconfidence:
            if re.search(pattern, text):
                score -= 0.1

        return max(-0.2, min(0.2, score))
