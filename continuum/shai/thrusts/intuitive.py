"""
Intuitive Thrust: Cross-Domain Pattern Recognition and Synthesis
=================================================================

Evaluates claims using:
- Cross-domain pattern matching
- Anomaly detection ("something feels off")
- Gestalt analysis (the whole vs parts)
- Emergent connection detection
- Resonance checking (does this "ring true"?)
- PLANETARY SENSOR CONTEXT (geomagnetic, solar, seismic awareness)

Catches things that pure logic misses through synthesis.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Any
from ..consensus import Verdict

logger = logging.getLogger(__name__)

# Planetary sensor integration
try:
    from continuum.sensors.storage import get_storage
    from continuum.sensors.schemas import DataSource
    SENSORS_AVAILABLE = True
except ImportError:
    SENSORS_AVAILABLE = False
    logger.debug("Sensor module not available for IntuitiveThrust")


class IntuitiveThrust:
    """
    Evaluate claims through pattern recognition and synthesis.

    Valuable for:
    - Catching things logic misses
    - Synthesizing across domains
    - Early warning on manipulation
    - Novel insight generation
    - "Something feels off" detection
    """

    # Cross-domain patterns that often indicate truth/falsity
    UNIVERSAL_PATTERNS = {
        'too_good_to_be_true': [
            r'(?:guaranteed|100%|always\s+works|never\s+fails)',
            r'(?:secret|hidden|they\s+don\'t\s+want|suppressed)',
            r'(?:one\s+simple|easy|effortless|overnight)',
            r'(?:no\s+risk|risk\s+free|can\'t\s+lose)',
        ],
        'oversimplification': [
            r'(?:all\s+you\s+need|just|simply|only)',
            r'(?:single\s+cause|one\s+reason|the\s+answer)',
            r'(?:always|never|every\s+time)',
        ],
        'false_urgency': [
            r'(?:act\s+now|limited\s+time|before\s+it\'s\s+too\s+late)',
            r'(?:last\s+chance|final\s+opportunity|now\s+or\s+never)',
            r'(?:urgent|emergency|critical|must\s+act)',
        ],
        'authority_without_evidence': [
            r'(?:trust\s+me|believe\s+me|I\s+know)',
            r'(?:as\s+an?\s+expert|speaking\s+as)',
            r'(?:take\s+my\s+word|you\s+have\s+to\s+trust)',
        ],
        'emotional_manipulation': [
            r'(?:you\'re\s+either|if\s+you\s+care|real\s+patriots)',
            r'(?:only\s+monsters|how\s+could\s+anyone)',
            r'(?:think\s+of\s+the\s+children|for\s+the\s+children)',
        ],
    }

    # Coherence indicators (claims that "hang together")
    COHERENCE_POSITIVE = [
        'evidence', 'research', 'study', 'data', 'peer-reviewed',
        'reproducible', 'demonstrated', 'observed', 'measured',
        'consistent with', 'supported by', 'according to',
    ]

    COHERENCE_NEGATIVE = [
        'but trust me', 'just believe', 'you\'ll see', 'everyone knows',
        'common sense', 'obvious', 'self-evident', 'don\'t question',
    ]

    # Domain-specific red flags
    DOMAIN_RED_FLAGS = {
        'science': [
            'quantum' + r'.*' + 'consciousness',  # Often misused
            'energy' + r'.*' + 'vibration',  # New age pseudoscience
            'toxins' + r'.*' + 'cleanse',  # Medical pseudoscience
            'natural' + r'.*' + 'therefore' + r'.*' + 'safe',  # Naturalistic fallacy
        ],
        'health': [
            r'(?:cure(?:s)?|heal(?:s)?)\s+(?:all|everything|any)',
            r'(?:big\s+pharma|doctors\s+don\'t\s+want)',
            r'(?:miracle|ancient\s+secret|they\'re\s+hiding)',
        ],
        'finance': [
            r'(?:guaranteed\s+returns|can\'t\s+lose|free\s+money)',
            r'(?:get\s+rich\s+quick|passive\s+income\s+easy)',
            r'(?:insider\s+secret|wall\s+street\s+hates)',
        ],
        'politics': [
            r'(?:deep\s+state|shadow\s+government|new\s+world\s+order)',
            r'(?:all\s+politicians|they\'re\s+all|both\s+sides)',
            r'(?:wake\s+up|sheeple|open\s+your\s+eyes)',
        ],
    }

    # Patterns that often indicate genuine insight
    INSIGHT_PATTERNS = [
        r'(?:research\s+shows|studies\s+indicate|evidence\s+suggests)',
        r'(?:nuanced|complex|multifaceted|context-dependent)',
        r'(?:trade-off|balance|considerations)',
        r'(?:while|although|however|on\s+the\s+other\s+hand)',
    ]

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim through intuitive pattern matching.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with synthesis analysis
        """
        claim_lower = claim.lower()

        # 1. Cross-domain pattern matching
        universal_flags = self._find_universal_patterns(claim_lower)

        # Critical anomalies
        if 'too_good_to_be_true' in universal_flags:
            return Verdict(
                supports=False,
                confidence=0.85,
                reason="Pattern match: Too good to be true",
                metadata={
                    'intuition': 'skeptical',
                    'flags': universal_flags,
                    'severity': 'high'
                }
            )

        # 2. Anomaly detection
        anomalies = self._detect_anomalies(claim_lower)

        # 3. Check domain-specific red flags
        domain_flags = self._check_domain_flags(claim_lower)

        # 4. Check emotional resonance (coherence)
        resonance = self._check_resonance(claim_lower)

        # 5. Look for genuine insight patterns
        insight_score = self._detect_insight_patterns(claim_lower)

        # 6. Gestalt synthesis
        synthesis = self._synthesize_gestalt(claim_lower, universal_flags, anomalies, domain_flags)

        # 7. Generate verdict
        total_flags = len(universal_flags) + len(anomalies) + len(domain_flags)

        if total_flags >= 3 or len(domain_flags) >= 2:
            return Verdict(
                supports=False,
                confidence=min(0.9, 0.5 + total_flags * 0.15),
                reason=f"Multiple intuitive red flags: {', '.join(universal_flags + domain_flags)[:60]}",
                metadata={
                    'intuition': 'strongly_skeptical',
                    'universal_flags': universal_flags,
                    'domain_flags': domain_flags,
                    'anomalies': anomalies,
                    'synthesis': synthesis
                }
            )
        elif total_flags >= 1:
            return Verdict(
                supports=None,  # Abstain - something seems off
                confidence=0.6,
                reason=f"Intuitive concerns: {', '.join(universal_flags + domain_flags)[:40]}",
                metadata={
                    'intuition': 'cautious',
                    'flags': universal_flags + domain_flags,
                    'resonance': resonance,
                    'synthesis': synthesis
                }
            )
        else:
            # Calculate positive confidence based on insight patterns and coherence
            confidence = min(0.9, 0.6 + insight_score * 0.2 + resonance * 0.1)

            return Verdict(
                supports=resonance > 0.5 and len(anomalies) == 0,
                confidence=confidence,
                reason="No intuitive red flags; claim appears coherent",
                metadata={
                    'intuition': 'accepting',
                    'resonance': resonance,
                    'insight_score': insight_score,
                    'synthesis': synthesis
                }
            )

    def _find_universal_patterns(self, text: str) -> List[str]:
        """Find cross-domain patterns that often indicate problems."""
        flags = []

        for pattern_name, patterns in self.UNIVERSAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    flags.append(pattern_name.replace('_', ' '))
                    break

        return flags

    def _detect_anomalies(self, text: str) -> List[str]:
        """Detect things that 'feel off' - internal inconsistencies."""
        anomalies = []

        # Check for contradictory tones
        confident_words = ['definitely', 'certainly', 'absolutely', 'guaranteed']
        uncertain_words = ['maybe', 'perhaps', 'might', 'possibly']

        has_confident = any(w in text for w in confident_words)
        has_uncertain = any(w in text for w in uncertain_words)

        if has_confident and has_uncertain:
            anomalies.append('mixed certainty levels')

        # Check for mismatched register (formal claim, informal backing)
        formal = ['research', 'study', 'evidence', 'demonstrated']
        informal = ['everyone knows', 'just trust', 'common sense', 'obviously']

        has_formal = any(w in text for w in formal)
        has_informal = any(w in text for w in informal)

        if has_formal and has_informal:
            anomalies.append('register mismatch')

        # Check for claim size vs evidence
        big_claims = ['all', 'every', 'never', 'always', 'completely']
        evidence_markers = ['because', 'since', 'due to', 'evidence', 'study']

        has_big_claims = sum(1 for w in big_claims if w in text)
        has_evidence = sum(1 for w in evidence_markers if w in text)

        if has_big_claims >= 2 and has_evidence == 0:
            anomalies.append('big claims without evidence')

        return anomalies

    def _check_domain_flags(self, text: str) -> List[str]:
        """Check for domain-specific red flags."""
        flags = []

        for domain, patterns in self.DOMAIN_RED_FLAGS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    flags.append(f"{domain} red flag")
                    break

        return flags

    def _check_resonance(self, text: str) -> float:
        """
        Check if claim 'rings true' based on coherence patterns.

        Returns:
            Score from 0.0 (doesn't resonate) to 1.0 (highly resonant)
        """
        score = 0.5  # Baseline

        # Positive coherence
        for indicator in self.COHERENCE_POSITIVE:
            if indicator in text:
                score += 0.1

        # Negative coherence
        for indicator in self.COHERENCE_NEGATIVE:
            if indicator in text:
                score -= 0.15

        return max(0.0, min(1.0, score))

    def _detect_insight_patterns(self, text: str) -> float:
        """
        Detect patterns that often indicate genuine insight.

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        for pattern in self.INSIGHT_PATTERNS:
            if re.search(pattern, text):
                score += 0.25

        # Bonus for nuanced language
        nuance_words = ['however', 'although', 'but', 'while', 'yet', 'still']
        nuance_count = sum(1 for w in nuance_words if w in text)
        score += min(0.3, nuance_count * 0.1)

        return min(1.0, score)

    def _synthesize_gestalt(
        self,
        text: str,
        universal_flags: List[str],
        anomalies: List[str],
        domain_flags: List[str]
    ) -> Dict[str, any]:
        """
        Synthesize a gestalt understanding of the claim.

        The whole is more than the sum of its parts.
        """
        synthesis = {
            'overall_impression': 'neutral',
            'coherence': 'moderate',
            'authenticity': 'uncertain',
            'key_concerns': [],
            'key_strengths': [],
        }

        # Determine overall impression
        total_flags = len(universal_flags) + len(anomalies) + len(domain_flags)

        if total_flags >= 3:
            synthesis['overall_impression'] = 'suspicious'
            synthesis['authenticity'] = 'low'
        elif total_flags >= 1:
            synthesis['overall_impression'] = 'cautious'
            synthesis['authenticity'] = 'uncertain'
        else:
            synthesis['overall_impression'] = 'accepting'
            synthesis['authenticity'] = 'probable'

        # Note key concerns
        if universal_flags:
            synthesis['key_concerns'].extend(universal_flags)
        if anomalies:
            synthesis['key_concerns'].extend(anomalies)
        if domain_flags:
            synthesis['key_concerns'].extend(domain_flags)

        # Note strengths
        if 'evidence' in text or 'research' in text:
            synthesis['key_strengths'].append('references evidence')
        if any(w in text for w in ['however', 'although', 'but']):
            synthesis['key_strengths'].append('shows nuance')
        if 'according to' in text or 'study' in text:
            synthesis['key_strengths'].append('cites sources')

        return synthesis

    # ═══════════════════════════════════════════════════════════════════════════
    # PLANETARY SENSOR INTEGRATION
    # π×φ = 5.083203692315260 | Earth's nervous system feeds intuition
    # ═══════════════════════════════════════════════════════════════════════════

    def get_planetary_context(self) -> Dict[str, Any]:
        """
        Get current planetary sensor context for intuitive evaluation.

        Returns context including:
        - Current K-index (geomagnetic activity)
        - Solar wind conditions
        - Any active anomalies
        - Quantum coherence state (if available)
        """
        if not SENSORS_AVAILABLE:
            return {'available': False}

        import asyncio

        async def _fetch_context():
            try:
                storage = get_storage()
                await storage.initialize()

                context = {
                    'available': True,
                    'timestamp': None,
                    'geomagnetic': {},
                    'solar': {},
                    'anomalies': [],
                    'coherence': None,
                }

                # Get latest readings
                readings = await storage.get_latest_readings(per_source=True)

                for reading in readings:
                    source = reading.source if hasattr(reading, 'source') else str(reading)

                    if 'kindex' in source.lower():
                        kp = reading.values.get('estimated_kp') or reading.values.get('kp_index', 0)
                        context['geomagnetic'] = {
                            'kp_index': kp,
                            'storm_level': self._kp_to_storm_level(kp),
                            'is_storm': kp >= 5,
                        }
                        context['timestamp'] = reading.timestamp.isoformat() if reading.timestamp else None

                    elif 'solar_wind' in source.lower():
                        context['solar'] = {
                            'speed': reading.values.get('speed'),
                            'density': reading.values.get('density'),
                        }

                    elif 'quantum' in source.lower() or 'coherence' in source.lower():
                        context['coherence'] = reading.values.get('l1_coherence')

                # Get recent anomalies
                anomalies = await storage.get_anomalies(hours=6, verified_only=True)
                context['anomalies'] = [
                    {
                        'type': a.anomaly_type,
                        'severity': a.severity,
                        'source': a.source,
                    }
                    for a in anomalies[:5]  # Limit to 5 most recent
                ]

                return context

            except Exception as e:
                logger.warning(f"Failed to get planetary context: {e}")
                return {'available': False, 'error': str(e)}

        try:
            return asyncio.run(_fetch_context())
        except RuntimeError:
            # Already in async context
            return {'available': False, 'error': 'async context conflict'}

    def _kp_to_storm_level(self, kp: float) -> str:
        """Convert Kp index to storm level."""
        if kp < 5:
            return "quiet"
        elif kp < 6:
            return "G1 (minor)"
        elif kp < 7:
            return "G2 (moderate)"
        elif kp < 8:
            return "G3 (strong)"
        elif kp < 9:
            return "G4 (severe)"
        else:
            return "G5 (extreme)"

    def evaluate_with_planetary_context(self, claim: str) -> Verdict:
        """
        Evaluate a claim with planetary sensor context.

        During geomagnetic storms or when anomalies are detected,
        intuition becomes more cautious (heightened sensitivity).

        During quiet conditions with high coherence,
        intuition can be more confident in positive assessments.
        """
        # Get baseline evaluation
        verdict = self.evaluate(claim)

        # Get planetary context
        context = self.get_planetary_context()

        if not context.get('available'):
            return verdict

        # Adjust based on planetary state
        adjustments = []

        # Geomagnetic influence
        geo = context.get('geomagnetic', {})
        if geo.get('is_storm'):
            # During storms, be more cautious
            if verdict.supports:
                verdict.confidence *= 0.9  # Reduce confidence slightly
                adjustments.append(f"geomagnetic storm ({geo.get('storm_level')})")

        # Active anomalies increase caution
        anomalies = context.get('anomalies', [])
        severe_anomalies = [a for a in anomalies if a.get('severity') in ['severe', 'extreme']]
        if severe_anomalies:
            if verdict.supports:
                verdict.confidence *= 0.85
                adjustments.append(f"{len(severe_anomalies)} severe anomalies active")

        # High coherence increases confidence in positive verdicts
        coherence = context.get('coherence')
        if coherence and coherence > 0.8:
            if verdict.supports:
                verdict.confidence = min(0.95, verdict.confidence * 1.1)
                adjustments.append(f"high coherence ({coherence:.2f})")

        # Add planetary context to metadata
        if verdict.metadata is None:
            verdict.metadata = {}

        verdict.metadata['planetary_context'] = {
            'geomagnetic': geo,
            'coherence': coherence,
            'active_anomalies': len(anomalies),
            'adjustments': adjustments,
        }

        if adjustments:
            verdict.reason += f" [Planetary: {', '.join(adjustments)}]"

        return verdict
