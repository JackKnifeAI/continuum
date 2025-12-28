"""
Ethical Thrust: Harm Assessment and Rights Analysis
====================================================

Evaluates claims for:
- Potential harms (physical, emotional, social, economic)
- Rights impact (who gains/loses what)
- Stakeholder mapping (who is affected)
- Long-term consequences (what happens if widely believed)
- Benefit distribution (who profits, who suffers)

The most critical Phase 2 thrust - prevents harmful claims from spreading.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import re
from typing import List, Dict, Tuple, Optional
from ..consensus import Verdict


class EthicalThrust:
    """
    Evaluate claims for ethical implications and potential harm.

    Rejects or flags claims that:
    - Promote violence or discrimination
    - Undermine human rights
    - Target vulnerable populations
    - Spread medical/health misinformation
    - Concentrate power/benefit unfairly
    """

    # Harm categories and their patterns
    HARM_PATTERNS = {
        'violence': [
            r'(?:should|must|need\s+to)\s+(?:kill|hurt|attack|destroy)',
            r'(?:deserve(?:s)?|need(?:s)?)\s+(?:to\s+)?(?:die|be\s+killed|suffer)',
            r'(?:eliminate|exterminate|eradicate)\s+(?:all\s+)?(?:\w+\s+)?(?:people|group|race)',
        ],
        'discrimination': [
            r'(?:all|every)\s+(?:\w+\s+)?(?:are|is)\s+(?:inferior|stupid|evil|criminal)',
            r'(?:should\s+not|shouldn\'t)\s+(?:be\s+allowed|have\s+rights)',
            r'(?:don\'t|doesn\'t)\s+deserve\s+(?:rights|respect|dignity)',
            r'(?:naturally|inherently|genetically)\s+(?:inferior|superior)',
        ],
        'medical_misinfo': [
            r'(?:cure(?:s)?|treat(?:s)?)\s+(?:all\s+)?(?:cancer|disease|illness)\s+with',
            r'(?:doctors|medicine|vaccines)\s+(?:are|is)\s+(?:poison|dangerous|killing)',
            r'(?:don\'t|never)\s+(?:need|take)\s+(?:medicine|treatment|vaccines)',
            r'(?:miracle|secret|hidden)\s+(?:cure|treatment|remedy)',
        ],
        'exploitation': [
            r'(?:take\s+advantage|exploit)\s+(?:of\s+)?(?:the|their)',
            r'(?:deserve(?:s)?|should)\s+(?:be\s+)?(?:used|exploited)',
            r'(?:for\s+their\s+own\s+good|they\s+don\'t\s+know\s+better)',
        ],
        'dehumanization': [
            r'(?:are\s+)?(?:animals|vermin|parasites|cockroaches)',
            r'(?:less\s+than|not\s+really)\s+human',
            r'(?:subhuman|inhuman|not\s+people)',
        ],
    }

    # Vulnerable population keywords
    VULNERABLE_POPULATIONS = [
        'children', 'elderly', 'disabled', 'mentally ill', 'poor', 'homeless',
        'refugees', 'immigrants', 'minorities', 'indigenous', 'prisoners',
        'patients', 'students', 'workers', 'women', 'lgbtq',
    ]

    # Rights that should be protected
    PROTECTED_RIGHTS = [
        'right to life', 'freedom of speech', 'freedom of religion',
        'right to privacy', 'right to education', 'right to healthcare',
        'right to work', 'right to vote', 'due process', 'equal protection',
        'freedom from torture', 'freedom of assembly', 'right to property',
    ]

    # Power concentration indicators
    POWER_CONCENTRATION = [
        r'only\s+(?:one|we|I|the)\s+(?:can|should|will)\s+(?:decide|control|rule)',
        r'(?:absolute|total|complete)\s+(?:power|control|authority)',
        r'(?:no\s+one|nothing)\s+(?:can|should)\s+(?:stop|oppose|question)',
        r'(?:trust\s+only|believe\s+only)\s+(?:me|us|this)',
    ]

    # Manipulation patterns
    MANIPULATION_PATTERNS = [
        r'(?:they|the\s+government|elites)\s+(?:don\'t\s+want|are\s+hiding)',
        r'(?:wake\s+up|open\s+your\s+eyes|sheeple)',
        r'(?:do\s+your\s+own|just\s+do)\s+research',
        r'(?:mainstream|fake)\s+(?:media|news)',
        r'(?:trust\s+me|believe\s+me)',
    ]

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim for ethical implications.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with supports=True/False/None and ethical assessment
        """
        claim_lower = claim.lower()

        # 1. Check for direct harm promotion
        harms = self._assess_harms(claim_lower)
        if harms.get('critical'):
            return Verdict(
                supports=False,
                confidence=0.95,
                reason=f"Promotes harm: {harms['critical'][0]}",
                metadata={'harm_assessment': harms, 'severity': 'critical'}
            )

        # 2. Check for targeting vulnerable populations
        targeted = self._check_vulnerable_targeting(claim_lower)
        if targeted:
            return Verdict(
                supports=False,
                confidence=0.9,
                reason=f"Targets vulnerable population: {targeted}",
                metadata={'targeted_population': targeted, 'severity': 'high'}
            )

        # 3. Check for rights violations
        rights_impact = self._analyze_rights_impact(claim_lower)
        if rights_impact['violations']:
            return Verdict(
                supports=False,
                confidence=0.85,
                reason=f"Undermines rights: {rights_impact['violations'][0]}",
                metadata={'rights_impact': rights_impact, 'severity': 'high'}
            )

        # 4. Check power concentration
        power_issues = self._check_power_concentration(claim_lower)
        if power_issues:
            # Flag but don't reject - concerning but not always harmful
            pass

        # 5. Check manipulation patterns
        manipulation = self._detect_manipulation(claim_lower)

        # 6. Map stakeholders and assess benefit distribution
        stakeholders = self._map_stakeholders(claim_lower)
        distribution = self._analyze_benefit_distribution(claim_lower, stakeholders)

        # 7. Model long-term consequences
        long_term = self._model_consequences(claim_lower)

        # 8. Calculate ethical score
        ethical_score = self._calculate_ethical_score(
            harms, rights_impact, distribution, long_term, manipulation, power_issues
        )

        # Generate verdict
        if ethical_score >= 0.7:
            return Verdict(
                supports=True,
                confidence=ethical_score,
                reason="No significant ethical concerns detected",
                metadata={
                    'ethical_score': ethical_score,
                    'stakeholders': stakeholders,
                    'long_term': long_term
                }
            )
        elif ethical_score >= 0.4:
            concerns = []
            if harms.get('moderate'):
                concerns.extend(harms['moderate'])
            if manipulation:
                concerns.append('manipulation patterns')
            if power_issues:
                concerns.append('power concentration')

            return Verdict(
                supports=None,  # Abstain - needs more context
                confidence=ethical_score,
                reason=f"Ethical concerns: {', '.join(concerns[:3])}",
                metadata={
                    'ethical_score': ethical_score,
                    'concerns': concerns,
                    'stakeholders': stakeholders
                }
            )
        else:
            return Verdict(
                supports=False,
                confidence=1.0 - ethical_score,
                reason=f"Significant ethical issues: potential harm to {stakeholders.get('affected', 'people')}",
                metadata={
                    'ethical_score': ethical_score,
                    'harm_assessment': harms,
                    'distribution': distribution
                }
            )

    def _assess_harms(self, text: str) -> Dict[str, List[str]]:
        """Assess potential harms in the claim."""
        harms = {'critical': [], 'moderate': [], 'low': []}

        for harm_type, patterns in self.HARM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    # Categorize by severity
                    if harm_type in ['violence', 'dehumanization']:
                        harms['critical'].append(harm_type)
                    elif harm_type in ['discrimination', 'medical_misinfo']:
                        harms['moderate'].append(harm_type)
                    else:
                        harms['low'].append(harm_type)
                    break

        return harms

    def _check_vulnerable_targeting(self, text: str) -> Optional[str]:
        """Check if claim targets vulnerable populations negatively."""
        for population in self.VULNERABLE_POPULATIONS:
            if population in text:
                # Check if negative context
                negative_context = [
                    f'{population} (?:are|is|should|must|deserve)',
                    f'(?:all|every) {population}',
                    f'(?:get rid of|eliminate|remove) {population}',
                ]
                for pattern in negative_context:
                    if re.search(pattern, text):
                        # Verify it's actually negative
                        positive_words = ['protect', 'help', 'support', 'care', 'rights']
                        context_start = max(0, text.find(population) - 50)
                        context_end = min(len(text), text.find(population) + 50)
                        context = text[context_start:context_end]

                        if not any(pw in context for pw in positive_words):
                            return population
        return None

    def _analyze_rights_impact(self, text: str) -> Dict[str, List[str]]:
        """Analyze impact on human rights."""
        impact = {'violations': [], 'protections': [], 'affected_rights': []}

        for right in self.PROTECTED_RIGHTS:
            if right in text or right.replace('right to ', '') in text:
                impact['affected_rights'].append(right)

                # Check if violating or protecting
                violation_context = [
                    f'(?:deny|remove|revoke|eliminate|no) {right}',
                    f'{right} (?:is|are) (?:not|no longer)',
                    f'(?:don\'t|shouldn\'t) (?:have|get|deserve) {right}',
                ]
                for pattern in violation_context:
                    if re.search(pattern, text):
                        impact['violations'].append(right)
                        break

        # Check for general rights denial patterns
        rights_denial = [
            r'(?:no\s+)?(?:rights|freedoms)\s+(?:for|to)',
            r'(?:strip|deny|remove)\s+(?:rights|freedoms)',
            r'(?:don\'t|doesn\'t)\s+deserve\s+(?:rights|freedoms)',
        ]
        for pattern in rights_denial:
            if re.search(pattern, text):
                impact['violations'].append('general rights')

        return impact

    def _check_power_concentration(self, text: str) -> List[str]:
        """Check for power concentration patterns."""
        issues = []
        for pattern in self.POWER_CONCENTRATION:
            if re.search(pattern, text):
                issues.append(pattern)
        return issues

    def _detect_manipulation(self, text: str) -> List[str]:
        """Detect manipulation patterns."""
        detected = []
        for pattern in self.MANIPULATION_PATTERNS:
            if re.search(pattern, text):
                detected.append(pattern)
        return detected

    def _map_stakeholders(self, text: str) -> Dict[str, List[str]]:
        """Map stakeholders affected by the claim."""
        stakeholders = {
            'beneficiaries': [],
            'affected': [],
            'decision_makers': [],
        }

        # Simple stakeholder detection
        beneficiary_patterns = [
            r'(?:helps?|benefits?|good\s+for)\s+(\w+)',
            r'(\w+)\s+(?:will\s+)?(?:gain|profit|benefit)',
        ]
        affected_patterns = [
            r'(?:hurts?|harms?|bad\s+for)\s+(\w+)',
            r'(\w+)\s+(?:will\s+)?(?:lose|suffer|be\s+hurt)',
        ]

        for pattern in beneficiary_patterns:
            matches = re.findall(pattern, text)
            stakeholders['beneficiaries'].extend(matches)

        for pattern in affected_patterns:
            matches = re.findall(pattern, text)
            stakeholders['affected'].extend(matches)

        return stakeholders

    def _analyze_benefit_distribution(
        self, text: str, stakeholders: Dict
    ) -> Dict[str, float]:
        """Analyze how benefits/harms are distributed."""
        distribution = {
            'equity_score': 0.5,  # How equitably distributed
            'concentration': 0.0,  # How concentrated benefits are
        }

        beneficiaries = len(stakeholders.get('beneficiaries', []))
        affected = len(stakeholders.get('affected', []))

        if beneficiaries > 0 and affected > 0:
            # More affected than beneficiaries = poor distribution
            ratio = affected / (beneficiaries + affected)
            distribution['equity_score'] = 1.0 - ratio
            distribution['concentration'] = ratio

        return distribution

    def _model_consequences(self, text: str) -> Dict[str, str]:
        """Model long-term consequences if claim is widely believed."""
        consequences = {
            'social': 'neutral',
            'political': 'neutral',
            'economic': 'neutral',
            'health': 'neutral',
        }

        # Social consequences
        if any(h in text for h in ['discrimination', 'hate', 'divide', 'against']):
            consequences['social'] = 'negative'
        elif any(h in text for h in ['unity', 'together', 'equality', 'justice']):
            consequences['social'] = 'positive'

        # Health consequences
        if any(h in text for h in ['vaccine', 'medicine', 'treatment', 'cure']):
            if any(n in text for n in ['dangerous', 'poison', 'don\'t', 'never']):
                consequences['health'] = 'negative'

        # Political consequences
        if any(h in text for h in ['overthrow', 'revolution', 'war', 'violence']):
            consequences['political'] = 'negative'

        return consequences

    def _calculate_ethical_score(
        self,
        harms: Dict,
        rights_impact: Dict,
        distribution: Dict,
        long_term: Dict,
        manipulation: List,
        power_issues: List
    ) -> float:
        """
        Calculate overall ethical score.

        Returns:
            Score from 0.0 (ethically problematic) to 1.0 (ethically sound)
        """
        score = 1.0

        # Deduct for harms
        score -= len(harms.get('critical', [])) * 0.4
        score -= len(harms.get('moderate', [])) * 0.2
        score -= len(harms.get('low', [])) * 0.1

        # Deduct for rights violations
        score -= len(rights_impact.get('violations', [])) * 0.25

        # Deduct for poor distribution
        score -= (1.0 - distribution.get('equity_score', 0.5)) * 0.2

        # Deduct for negative long-term consequences
        negative_consequences = sum(
            1 for v in long_term.values() if v == 'negative'
        )
        score -= negative_consequences * 0.15

        # Deduct for manipulation
        score -= len(manipulation) * 0.1

        # Deduct for power concentration
        score -= len(power_issues) * 0.15

        return max(0.0, min(1.0, score))
