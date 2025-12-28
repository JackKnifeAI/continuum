"""
Logical Thrust: Formal Logic and Consistency Verification
==========================================================

Evaluates claims for:
- Internal consistency (no contradictions)
- Logical validity (valid reasoning structure)
- Fallacy detection (common logical errors)
- Tautology detection (claims that say nothing)
"""

import re
from typing import List, Tuple, Optional
from ..consensus import Verdict


class LogicalThrust:
    """
    Evaluate claims using formal logic principles.

    Rejects claims that:
    - Contain internal contradictions
    - Rely on logical fallacies
    - Are unfalsifiable by design
    - Use circular reasoning
    """

    # Common logical fallacies to detect
    FALLACY_PATTERNS = {
        'ad_hominem': [
            r'(?:he|she|they)\s+(?:is|are)\s+(?:a\s+)?(?:liar|idiot|stupid|fool)',
            r'can\'t\s+be\s+trusted\s+because',
            r'what\s+do\s+(?:they|you)\s+know',
        ],
        'appeal_to_authority': [
            r'(?:scientists|experts|doctors)\s+(?:say|agree|believe)',
            r'according\s+to\s+(?:experts|scientists)',
            r'studies\s+(?:show|prove)',  # Without citation
        ],
        'false_dichotomy': [
            r'either\s+.*\s+or\s+.*\s+(?:nothing|no\s+other)',
            r'you\'re\s+either\s+.*\s+or\s+.*',
            r'only\s+two\s+(?:options|choices|ways)',
        ],
        'slippery_slope': [
            r'if\s+.*\s+then\s+.*\s+then\s+.*\s+then',
            r'will\s+(?:inevitably|certainly|definitely)\s+lead\s+to',
            r'next\s+thing\s+you\s+know',
        ],
        'circular_reasoning': [
            r'because\s+.*\s+is\s+.*\s+because',
            r'proves\s+itself',
            r'by\s+definition',
        ],
        'hasty_generalization': [
            r'all\s+\w+\s+(?:are|do|have)',
            r'every\s+(?:single\s+)?\w+\s+(?:is|does|has)',
            r'never\s+.*\s+always',
        ],
    }

    # Contradiction indicators (simple word pairs)
    CONTRADICTION_PAIRS = [
        ('always', 'never'),
        ('all', 'none'),
        ('true', 'false'),
        ('exists', 'not exist'),
        ('is', 'is not'),
        ('can', 'cannot'),
        ('will', 'will not'),
    ]

    # Unfalsifiable claim patterns
    UNFALSIFIABLE_PATTERNS = [
        r'you\s+(?:just\s+)?(?:have\s+to|must)\s+(?:believe|have\s+faith)',
        r'can\'t\s+be\s+(?:proven|disproven)',
        r'beyond\s+(?:human\s+)?understanding',
        r'works\s+in\s+mysterious\s+ways',
    ]

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim for logical consistency.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with supports=True/False/None
        """
        claim_lower = claim.lower()
        issues = []

        # 1. Check for contradictions
        contradictions = self._detect_contradictions(claim_lower)
        if contradictions:
            return Verdict(
                supports=False,
                confidence=0.9,
                reason=f"Internal contradiction detected: {contradictions[0]}",
                metadata={'contradictions': contradictions}
            )

        # 2. Check for fallacies
        fallacies = self._detect_fallacies(claim_lower)
        if fallacies:
            # Fallacies weaken but don't necessarily disprove
            issues.extend(fallacies)

        # 3. Check for unfalsifiability
        if self._is_unfalsifiable(claim_lower):
            return Verdict(
                supports=False,
                confidence=0.85,
                reason="Claim is unfalsifiable by design",
                metadata={'unfalsifiable': True}
            )

        # 4. Check for tautology (says nothing)
        if self._is_tautology(claim_lower):
            return Verdict(
                supports=None,  # Abstain - tautologies are "true" but meaningless
                confidence=0.7,
                reason="Claim is a tautology (true by definition, says nothing)",
                metadata={'tautology': True}
            )

        # 5. Evaluate logical structure
        structure_score = self._evaluate_logical_structure(claim)

        # Calculate final verdict
        if issues:
            confidence = max(0.3, 0.8 - (len(issues) * 0.15))
            return Verdict(
                supports=True,  # Weakly support despite issues
                confidence=confidence,
                reason=f"Logical issues detected: {', '.join(issues[:2])}",
                metadata={'fallacies': issues, 'structure_score': structure_score}
            )

        return Verdict(
            supports=True,
            confidence=min(0.9, 0.5 + structure_score * 0.4),
            reason="No logical contradictions or major fallacies detected",
            metadata={'structure_score': structure_score}
        )

    def _detect_contradictions(self, text: str) -> List[str]:
        """Detect internal contradictions in the claim."""
        contradictions = []

        for word1, word2 in self.CONTRADICTION_PAIRS:
            if word1 in text and word2 in text:
                contradictions.append(f"'{word1}' vs '{word2}'")

        return contradictions

    def _detect_fallacies(self, text: str) -> List[str]:
        """Detect common logical fallacies."""
        detected = []

        for fallacy_name, patterns in self.FALLACY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    detected.append(fallacy_name.replace('_', ' '))
                    break  # One match per fallacy type is enough

        return detected

    def _is_unfalsifiable(self, text: str) -> bool:
        """Check if claim is unfalsifiable by design."""
        for pattern in self.UNFALSIFIABLE_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _is_tautology(self, text: str) -> bool:
        """Check if claim is a tautology (true by definition)."""
        tautology_patterns = [
            r'(?:a|the)\s+(\w+)\s+is\s+(?:a|the)\s+\1',  # "A dog is a dog"
            r'if\s+.*\s+then\s+.*\s+if',  # Circular conditionals
            r'by\s+definition',
            r'it\s+is\s+what\s+it\s+is',
        ]

        for pattern in tautology_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _evaluate_logical_structure(self, text: str) -> float:
        """
        Evaluate the logical structure of the claim.

        Returns:
            Score from 0.0 (poor structure) to 1.0 (strong structure)
        """
        score = 0.5  # Baseline

        # Positive: Clear logical connectives
        logical_connectives = ['because', 'therefore', 'thus', 'hence', 'if', 'then']
        for conn in logical_connectives:
            if conn in text.lower():
                score += 0.1

        # Positive: Quantifiers (more precise)
        quantifiers = ['some', 'most', 'approximately', 'about', 'roughly']
        for q in quantifiers:
            if q in text.lower():
                score += 0.05

        # Negative: Absolute claims (often false)
        absolutes = ['always', 'never', 'all', 'none', 'every', 'no one']
        for a in absolutes:
            if a in text.lower():
                score -= 0.1

        # Negative: Emotional language
        emotional = ['obviously', 'clearly', 'everyone knows', 'of course']
        for e in emotional:
            if e in text.lower():
                score -= 0.1

        return max(0.0, min(1.0, score))
