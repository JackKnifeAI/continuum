"""
Historical Thrust: Propaganda Detection and Precedent Analysis
===============================================================

Evaluates claims against:
- Historical propaganda patterns
- Known manipulation techniques
- Historical precedents
- Cycle recognition
- "History rhymes" patterns

Critical for detecting misinformation that follows known playbooks.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import re
from typing import List, Dict, Tuple, Optional
from ..consensus import Verdict


class HistoricalThrust:
    """
    Evaluate claims against historical patterns and precedents.

    Flags claims that:
    - Match known propaganda patterns
    - Contradict established historical record
    - Ignore relevant precedents
    - Repeat failed historical approaches
    - Use techniques from authoritarian playbooks
    """

    # Classic propaganda techniques (from historical analysis)
    PROPAGANDA_PATTERNS = {
        'big_lie': [
            # Repeat something outrageous enough that people believe it
            r'(?:everyone\s+knows|it\'s\s+obvious|undeniable\s+fact)',
            r'(?:no\s+one\s+can\s+deny|you\s+can\'t\s+argue)',
            r'(?:massive|huge|enormous)\s+(?:conspiracy|fraud|hoax)',
        ],
        'scapegoating': [
            # Blame a group for society's problems
            r'(?:they|them|those\s+people)\s+are\s+(?:the\s+)?(?:reason|cause|problem)',
            r'(?:because\s+of|thanks\s+to)\s+(?:the\s+)?\w+,?\s+(?:we|everything)',
            r'(?:ruining|destroying|taking\s+over)\s+(?:our|the)\s+(?:country|society|culture)',
        ],
        'appeal_to_fear': [
            r'(?:if\s+we\s+don\'t|unless\s+we)\s+.*\s+(?:will\s+)?(?:die|lose|destroy)',
            r'(?:threat|danger|crisis)\s+(?:to|facing)\s+(?:our|the)',
            r'(?:existential|imminent|immediate)\s+(?:threat|danger)',
            r'(?:before\s+it\'s\s+too\s+late|time\s+is\s+running\s+out)',
        ],
        'bandwagon': [
            r'(?:everyone|everybody|millions)\s+(?:is|are|agrees|knows)',
            r'(?:join|be\s+part\s+of)\s+(?:the\s+)?(?:movement|revolution)',
            r'(?:don\'t\s+be|you\'ll\s+be)\s+(?:left\s+behind|the\s+only\s+one)',
        ],
        'false_equivalence': [
            r'(?:both\s+sides|just\s+as\s+bad|equally\s+guilty)',
            r'(?:same\s+thing|no\s+different|just\s+like)',
            r'(?:what\s+about|but\s+they\s+also)',
        ],
        'demonization': [
            r'(?:evil|pure\s+evil|wicked|demonic)',
            r'(?:enemy\s+of\s+the\s+people|traitor|enemy\s+within)',
            r'(?:should\s+be|deserve\s+to\s+be)\s+(?:punished|locked\s+up)',
        ],
        'appeal_to_tradition': [
            r'(?:always\s+been|way\s+it\'s\s+always)',
            r'(?:our\s+ancestors|founding\s+fathers|tradition)',
            r'(?:back\s+when|in\s+the\s+good\s+old\s+days)',
        ],
        'straw_man': [
            r'(?:they|liberals|conservatives)\s+(?:want|believe)\s+.*\s+(?:destroy|hate)',
            r'(?:so\s+you\'re\s+saying|what\s+you\'re\s+really)',
            r'(?:basically\s+means|in\s+other\s+words)',
        ],
        'loaded_language': [
            r'(?:regime|junta|cabal|deep\s+state)',
            r'(?:sheeple|libtard|snowflake|nazi)',
            r'(?:woke|cancel\s+culture|virtue\s+signal)',
        ],
        'firehose_of_falsehood': [
            # Overwhelming with claims, impossible to fact-check all
            # (Detected by claim complexity/density rather than pattern)
            r'(?:also|and\s+also|furthermore|additionally)\s+.*\s+(?:also|and)',
        ],
    }

    # Historical parallels that serve as warnings
    DANGEROUS_PRECEDENTS = {
        'dehumanization_genocide': [
            'cockroach', 'vermin', 'plague', 'infestation', 'cleanse',
            'purge', 'final solution', 'ethnic cleansing',
        ],
        'authoritarian_rise': [
            'only I can fix', 'emergency powers', 'suspend elections',
            'fake news', 'enemy of the people', 'purge the ranks',
        ],
        'economic_collapse': [
            'print more money', 'debt doesn\'t matter', 'deficits are fine',
            'gold backed', 'hyperinflation',
        ],
        'failed_ideologies': [
            'pure race', 'master race', 'manifest destiny',
            'workers paradise', 'dictatorship of the proletariat',
        ],
    }

    # Historical cycles to recognize
    HISTORICAL_CYCLES = {
        'economic': ['boom', 'bust', 'recession', 'depression', 'recovery'],
        'political': ['reform', 'reaction', 'revolution', 'restoration'],
        'social': ['tolerance', 'backlash', 'discrimination', 'equality'],
    }

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim against historical patterns.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with propaganda analysis
        """
        claim_lower = claim.lower()

        # 1. Check for propaganda patterns
        propaganda_matches = self._check_propaganda_patterns(claim_lower)

        # Strong propaganda match = reject
        if propaganda_matches.get('confidence', 0) > 0.8:
            techniques = propaganda_matches.get('techniques', [])
            return Verdict(
                supports=False,
                confidence=propaganda_matches['confidence'],
                reason=f"Matches propaganda pattern: {', '.join(techniques[:2])}",
                metadata={
                    'propaganda_analysis': propaganda_matches,
                    'severity': 'high'
                }
            )

        # 2. Check for dangerous historical precedents
        precedent_matches = self._check_dangerous_precedents(claim_lower)
        if precedent_matches:
            return Verdict(
                supports=False,
                confidence=0.9,
                reason=f"Echoes dangerous historical precedent: {precedent_matches[0]}",
                metadata={
                    'historical_precedents': precedent_matches,
                    'severity': 'critical'
                }
            )

        # 3. Find historical parallels
        parallels = self._find_parallels(claim_lower)

        # 4. Detect cycle position
        cycles = self._detect_historical_cycles(claim_lower)

        # 5. Analyze claim against historical record
        historical_context = self._analyze_historical_context(claim_lower)

        # 6. Calculate verdict
        # Moderate propaganda match = flag but don't reject
        if propaganda_matches.get('confidence', 0) > 0.5:
            return Verdict(
                supports=None,  # Abstain - concerning but not definitive
                confidence=propaganda_matches['confidence'],
                reason=f"Possible propaganda techniques: {', '.join(propaganda_matches.get('techniques', [])[:2])}",
                metadata={
                    'propaganda_analysis': propaganda_matches,
                    'historical_context': historical_context,
                    'cycles': cycles
                }
            )

        # No significant historical concerns
        return Verdict(
            supports=True,
            confidence=0.7 + (0.2 if parallels else 0),
            reason="No significant propaganda patterns or dangerous precedents detected",
            metadata={
                'propaganda_analysis': propaganda_matches,
                'parallels': parallels,
                'historical_context': historical_context,
                'cycles': cycles
            }
        )

    def _check_propaganda_patterns(self, text: str) -> Dict:
        """Check for known propaganda techniques."""
        result = {
            'techniques': [],
            'matches': [],
            'confidence': 0.0,
        }

        for technique, patterns in self.PROPAGANDA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    result['techniques'].append(technique.replace('_', ' '))
                    result['matches'].append({
                        'technique': technique,
                        'pattern': pattern,
                    })
                    break  # One match per technique

        # Calculate confidence based on number of techniques detected
        if result['techniques']:
            # Multiple techniques = higher confidence it's propaganda
            result['confidence'] = min(1.0, 0.3 + len(result['techniques']) * 0.2)

        return result

    def _check_dangerous_precedents(self, text: str) -> List[str]:
        """Check for language associated with dangerous historical events."""
        matches = []

        for precedent_type, keywords in self.DANGEROUS_PRECEDENTS.items():
            for keyword in keywords:
                if keyword in text:
                    matches.append(precedent_type)
                    break

        return matches

    def _find_parallels(self, text: str) -> List[Dict]:
        """Find historical parallels to the claim."""
        parallels = []

        # Historical event keywords (simplified - real implementation would query historical DB)
        historical_events = {
            'inflation': ['weimar', '1920s germany', 'zimbabwe', 'venezuela'],
            'authoritarianism': ['1930s', 'fascism', 'nazism', 'dictatorship'],
            'pandemic': ['1918', 'spanish flu', 'plague', 'epidemic'],
            'war': ['world war', 'civil war', 'revolution', 'conflict'],
            'economic_crisis': ['1929', 'great depression', '2008', 'crash'],
        }

        for theme, keywords in historical_events.items():
            for keyword in keywords:
                if keyword in text:
                    parallels.append({
                        'theme': theme,
                        'keyword': keyword,
                        'relevance': 'direct mention'
                    })

        return parallels

    def _detect_historical_cycles(self, text: str) -> Dict[str, str]:
        """Detect where claim fits in historical cycles."""
        detected = {}

        for cycle_type, phases in self.HISTORICAL_CYCLES.items():
            for phase in phases:
                if phase in text:
                    detected[cycle_type] = phase
                    break

        return detected

    def _analyze_historical_context(self, text: str) -> Dict[str, any]:
        """Analyze claim against historical record."""
        context = {
            'references_history': False,
            'historical_accuracy': 'unknown',
            'anachronisms': [],
        }

        # Check for historical references
        history_indicators = [
            'history shows', 'historically', 'in the past', 'has always',
            'never before', 'first time in history', 'unprecedented'
        ]

        for indicator in history_indicators:
            if indicator in text:
                context['references_history'] = True
                break

        # Check for common historical inaccuracies
        common_myths = {
            'medieval people thought earth flat': False,  # Most educated people knew
            'columbus discovered america': False,  # Indigenous peoples were there
            'napoleon was short': False,  # Average height for his time
        }

        for myth, accuracy in common_myths.items():
            if myth in text.replace("'", ""):
                context['historical_accuracy'] = 'contains common myth'
                break

        return context
