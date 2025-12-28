"""
Adversarial Thrust: Devil's Advocate
=====================================

Actively attempts to DISPROVE claims.
The skeptic that strengthens truth through attack.

If the attack FAILS, the claim is stronger.
If the attack SUCCEEDS, the claim has weaknesses.
"""

import re
from typing import List, Dict, Any, Tuple
from ..consensus import Verdict


class AdversarialThrust:
    """
    Actively attack claims to test their strength.

    Critical for:
    - Preventing groupthink
    - Catching subtle manipulations
    - Stress-testing "obvious" truths
    - Identifying hidden assumptions
    """

    # Common manipulation patterns
    MANIPULATION_PATTERNS = {
        'emotional_appeal': [
            r'think\s+of\s+the\s+children',
            r'(?:brave|heroic|patriotic)',
            r'(?:evil|dangerous|threatening)',
            r'(?:fear|terror|horror|outrage)',
            r'how\s+(?:can|could)\s+you\s+(?:not|ignore)',
        ],
        'social_proof': [
            r'everyone\s+(?:knows|agrees|believes)',
            r'nobody\s+(?:thinks|believes|would)',
            r'(?:mainstream|popular|common)\s+(?:view|opinion)',
            r'the\s+majority\s+(?:of\s+people\s+)?(?:think|believe)',
        ],
        'authority_manipulation': [
            r'(?:scientists|experts|doctors)\s+(?:all\s+)?agree',
            r'(?:studies|research)\s+(?:prove|show)\s+(?:that\s+)?(?:all|every)',
            r'(?:no\s+)?(?:scientist|expert)\s+(?:disputes?|questions?)',
        ],
        'framing_bias': [
            r'(?:so-called|alleged|supposed)',
            r'(?:merely|just|only)\s+a',
            r'(?:radical|extreme|dangerous)\s+(?:idea|claim|theory)',
        ],
        'urgency_pressure': [
            r'(?:act|decide)\s+(?:now|immediately|quickly)',
            r'(?:before\s+it\'s\s+too\s+late)',
            r'(?:limited\s+time|running\s+out)',
            r'(?:crisis|emergency|critical)',
        ],
    }

    # Hidden assumption patterns
    ASSUMPTION_PATTERNS = [
        (r'since\s+(\w+\s+\w+)', 'Assumes: {}'),
        (r'because\s+(\w+\s+\w+\s+\w+)', 'Assumes: {}'),
        (r'given\s+that\s+(\w+\s+\w+)', 'Assumes: {}'),
        (r'as\s+(?:we\s+)?(?:know|established)', 'Hidden assumption: prior knowledge'),
    ]

    # Weak point indicators
    WEAK_POINT_PATTERNS = [
        r'(?:usually|typically|generally)',  # Exceptions exist
        r'(?:most|many|some)',  # Not all
        r'(?:tends?\s+to|often)',  # Not always
        r'(?:seems?|appears?)',  # Uncertainty
    ]

    def attack(self, claim: str) -> Verdict:
        """
        Attack the claim from all angles.

        If attack FAILS → claim is stronger → supports=True
        If attack SUCCEEDS → claim is weaker → supports=False

        Args:
            claim: The claim to attack

        Returns:
            Verdict (supports=True means attack FAILED, claim is strong)
        """
        claim_lower = claim.lower()

        attacks = []
        attack_strength = 0.0

        # 1. Search for manipulation patterns
        manipulations = self._detect_manipulations(claim_lower)
        if manipulations:
            attacks.extend(manipulations)
            attack_strength += len(manipulations) * 0.15

        # 2. Find hidden assumptions
        assumptions = self._extract_assumptions(claim_lower)
        if assumptions:
            attacks.extend([f"Hidden assumption: {a}" for a in assumptions])
            attack_strength += len(assumptions) * 0.1

        # 3. Find weak points
        weak_points = self._find_weak_points(claim_lower)
        if weak_points:
            attacks.extend([f"Weak point: {wp}" for wp in weak_points])
            attack_strength += len(weak_points) * 0.05

        # 4. Generate counterexamples (simulated)
        counterexamples = self._generate_counterexamples(claim)
        if counterexamples:
            attacks.extend([f"Potential counterexample: {ce}" for ce in counterexamples])
            attack_strength += len(counterexamples) * 0.1

        # 5. Check for unfounded certainty
        certainty_attack = self._attack_certainty(claim_lower)
        if certainty_attack:
            attacks.append(certainty_attack)
            attack_strength += 0.1

        # Calculate result
        attack_strength = min(1.0, attack_strength)

        # If attack strength is LOW, claim is STRONG
        if attack_strength < 0.2:
            return Verdict(
                supports=True,  # Attack failed - claim is strong
                confidence=0.9 - attack_strength,
                reason="Claim survived adversarial testing with minimal weaknesses",
                metadata={
                    'attack_strength': attack_strength,
                    'attacks_attempted': len(attacks),
                    'attacks': attacks
                }
            )
        elif attack_strength > 0.5:
            return Verdict(
                supports=False,  # Attack succeeded - claim is weak
                confidence=attack_strength,
                reason=attacks[0] if attacks else "Claim failed adversarial testing",
                metadata={
                    'attack_strength': attack_strength,
                    'attacks_attempted': len(attacks),
                    'attacks': attacks
                }
            )
        else:
            return Verdict(
                supports=None,  # Partial success - claim has notable weaknesses
                confidence=0.5,
                reason=f"Claim has {len(attacks)} potential weaknesses requiring scrutiny",
                metadata={
                    'attack_strength': attack_strength,
                    'attacks_attempted': len(attacks),
                    'attacks': attacks
                }
            )

    def _detect_manipulations(self, text: str) -> List[str]:
        """Detect manipulation patterns in the claim."""
        detected = []

        for manip_type, patterns in self.MANIPULATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    detected.append(f"{manip_type.replace('_', ' ')}")
                    break

        return detected

    def _extract_assumptions(self, text: str) -> List[str]:
        """Extract hidden assumptions from the claim."""
        assumptions = []

        for pattern, template in self.ASSUMPTION_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and len(match) > 5:
                    assumptions.append(match)

        return assumptions[:3]  # Limit to top 3

    def _find_weak_points(self, text: str) -> List[str]:
        """Find weak points that could be exploited."""
        weak_points = []

        for pattern in self.WEAK_POINT_PATTERNS:
            matches = re.findall(pattern, text)
            weak_points.extend(matches)

        return list(set(weak_points))

    def _generate_counterexamples(self, claim: str) -> List[str]:
        """
        Generate potential counterexamples.

        Note: This is a simplified heuristic. A full implementation
        would use external knowledge bases.
        """
        counterexamples = []
        claim_lower = claim.lower()

        # Check for absolute claims that invite counterexamples
        absolutes = {
            r'all\s+(\w+)': 'Are there any {} that don\'t fit?',
            r'every\s+(\w+)': 'Can we find a single {} that contradicts?',
            r'always': 'Has there ever been an exception?',
            r'never': 'Has this ever happened even once?',
            r'no\s+(\w+)\s+(?:can|could|would)': 'Is there any {} that actually can?',
        }

        for pattern, template in absolutes.items():
            match = re.search(pattern, claim_lower)
            if match:
                if match.groups():
                    counterexamples.append(template.format(match.group(1)))
                else:
                    counterexamples.append(template)

        return counterexamples[:2]

    def _attack_certainty(self, text: str) -> str:
        """Attack unfounded certainty in the claim."""
        certainty_markers = [
            (r'(?:definitely|certainly|absolutely|undoubtedly)', 'high'),
            (r'(?:proven|established\s+fact|known)', 'medium'),
            (r'(?:obviously|clearly|of\s+course)', 'implicit'),
        ]

        for pattern, certainty_type in certainty_markers:
            if re.search(pattern, text):
                return f"Unfounded {certainty_type} certainty - where is the proof?"

        return ""
