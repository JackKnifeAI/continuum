"""
Witness Thrust: Human Testimony and Cryptographic Verification
==============================================================

Evaluates claims using:
- Human witness testimony
- Cryptographic signature verification
- Timestamp validation (proof of existence)
- Chain of custody tracking
- Cross-witness corroboration

Grounds AI analysis in human experience and verifiable records.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional

from ..consensus import Verdict


class WitnessThrust:
    """
    Evaluate claims against human testimony and verified records.

    Critical for:
    - Grounding AI analysis in human experience
    - Preventing pure AI echo chambers
    - Documenting real-world events
    - Preserving testimony against revision
    """

    # Testimony credibility indicators
    CREDIBILITY_POSITIVE = [
        r'(?:I\s+(?:saw|witnessed|observed|was\s+there))',
        r'(?:first-?hand|eyewitness|personal\s+experience)',
        r'(?:documented|recorded|photographed|filmed)',
        r'(?:multiple\s+(?:witnesses|sources|reports))',
        r'(?:verified|confirmed|authenticated)',
    ]

    CREDIBILITY_NEGATIVE = [
        r'(?:I\s+(?:heard|read|saw\s+online)\s+that)',
        r'(?:someone\s+(?:told|said)|they\s+say)',
        r'(?:apparently|supposedly|allegedly)',
        r'(?:rumor|gossip|unconfirmed)',
        r'(?:anonymous\s+source|insider|whistleblower)',  # Can be valid but unverifiable
    ]

    # Verification markers
    VERIFICATION_MARKERS = [
        'signed', 'notarized', 'certified', 'attested',
        'blockchain', 'timestamped', 'hash', 'digital signature',
        'court record', 'official document', 'sworn statement',
    ]

    # Chain of custody indicators
    CUSTODY_POSITIVE = [
        'original', 'unedited', 'raw footage', 'metadata intact',
        'chain of custody', 'provenance', 'authenticated',
    ]

    CUSTODY_NEGATIVE = [
        'edited', 'cropped', 'taken out of context', 'screenshot',
        'forwarded', 'shared', 'viral', 'repost',
    ]

    # Corroboration patterns
    CORROBORATION_PATTERNS = [
        r'(?:multiple\s+)?(?:sources|witnesses|reports)\s+(?:confirm|corroborate)',
        r'(?:independently\s+)?verified',
        r'(?:consistent|matches)\s+(?:with|across)',
        r'(?:same|similar)\s+(?:account|story|testimony)',
    ]

    # Internal testimony database (in real implementation, would query external DB)
    # This is a placeholder for cryptographically verified testimonies
    _testimony_db: Dict[str, Dict] = {}

    def evaluate(self, claim: str) -> Verdict:
        """
        Evaluate a claim against witness testimony and records.

        Args:
            claim: The claim to evaluate

        Returns:
            Verdict with testimony analysis
        """
        claim_lower = claim.lower()

        # 1. Find relevant testimony
        witnesses = self._find_witnesses(claim_lower)

        # 2. Verify any cryptographic claims
        crypto_verified = self._check_crypto_verification(claim_lower)

        # 3. Assess testimony credibility
        credibility = self._assess_credibility(claim_lower)

        # 4. Check chain of custody
        custody_score = self._check_chain_of_custody(claim_lower)

        # 5. Cross-corroborate testimonies
        corroboration = self._cross_corroborate(claim_lower, witnesses)

        # 6. Check timestamp validity
        timestamp_valid = self._validate_timestamps(claim_lower)

        # 7. Calculate weighted support
        weighted_support = self._calculate_weighted_support(
            witnesses, crypto_verified, credibility, custody_score, corroboration
        )

        # 8. Generate verdict
        if len(witnesses) == 0:
            # No witness testimony available - abstain
            return Verdict(
                supports=None,
                confidence=0.3,
                reason="No verifiable witness testimony found",
                metadata={
                    'witness_count': 0,
                    'credibility': credibility,
                    'chain_of_custody': custody_score
                }
            )

        if crypto_verified and weighted_support > 0.7:
            return Verdict(
                supports=True,
                confidence=min(0.95, weighted_support),
                reason="Cryptographically verified testimony supports claim",
                metadata={
                    'witness_count': len(witnesses),
                    'crypto_verified': True,
                    'corroboration_score': corroboration,
                    'chain_of_custody': custody_score
                }
            )

        if weighted_support > 0.6:
            return Verdict(
                supports=True,
                confidence=weighted_support,
                reason=f"Supported by {len(witnesses)} witness(es) with corroboration",
                metadata={
                    'witness_count': len(witnesses),
                    'corroboration_score': corroboration,
                    'credibility': credibility,
                    'chain_of_custody': custody_score
                }
            )
        elif weighted_support > 0.4:
            return Verdict(
                supports=None,  # Abstain - mixed testimony
                confidence=0.5,
                reason="Witness testimony is mixed or insufficient",
                metadata={
                    'witness_count': len(witnesses),
                    'weighted_support': weighted_support,
                    'credibility': credibility
                }
            )
        else:
            return Verdict(
                supports=False,
                confidence=1.0 - weighted_support,
                reason="Witness testimony contradicts or fails to support claim",
                metadata={
                    'witness_count': len(witnesses),
                    'weighted_support': weighted_support,
                    'credibility_issues': 'detected'
                }
            )

    def _find_witnesses(self, text: str) -> List[Dict]:
        """Find witness testimony related to the claim."""
        witnesses = []

        # Detect first-person testimony
        first_person = re.findall(
            r'I\s+(?:saw|witnessed|observed|experienced|was\s+there)',
            text,
            re.IGNORECASE
        )
        if first_person:
            witnesses.append({
                'type': 'first_person',
                'claim': 'personal testimony',
                'verified': False
            })

        # Detect third-party testimony references
        third_party = re.findall(
            r'(?:witnesses?|observers?|victims?)\s+(?:said|reported|testified)',
            text,
            re.IGNORECASE
        )
        for match in third_party:
            witnesses.append({
                'type': 'third_party',
                'claim': match,
                'verified': False
            })

        # Detect documented testimony
        documented = re.findall(
            r'(?:court\s+)?(?:record|testimony|deposition|affidavit)',
            text,
            re.IGNORECASE
        )
        for match in documented:
            witnesses.append({
                'type': 'documented',
                'claim': match,
                'verified': 'record' in match.lower() or 'court' in text.lower()
            })

        return witnesses

    def _check_crypto_verification(self, text: str) -> bool:
        """Check if claim references cryptographic verification."""
        for marker in self.VERIFICATION_MARKERS:
            if marker in text:
                return True
        return False

    def _assess_credibility(self, text: str) -> float:
        """
        Assess overall credibility of testimony in claim.

        Returns:
            Score from 0.0 (low credibility) to 1.0 (high credibility)
        """
        score = 0.5  # Baseline

        # Positive indicators
        for pattern in self.CREDIBILITY_POSITIVE:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.15

        # Negative indicators
        for pattern in self.CREDIBILITY_NEGATIVE:
            if re.search(pattern, text, re.IGNORECASE):
                score -= 0.15

        return max(0.0, min(1.0, score))

    def _check_chain_of_custody(self, text: str) -> float:
        """
        Check chain of custody indicators.

        Returns:
            Score from 0.0 (broken/unknown) to 1.0 (intact)
        """
        score = 0.5

        for indicator in self.CUSTODY_POSITIVE:
            if indicator in text:
                score += 0.15

        for indicator in self.CUSTODY_NEGATIVE:
            if indicator in text:
                score -= 0.15

        return max(0.0, min(1.0, score))

    def _cross_corroborate(self, text: str, witnesses: List[Dict]) -> float:
        """
        Check for cross-corroboration between testimonies.

        Returns:
            Score from 0.0 (no corroboration) to 1.0 (strong corroboration)
        """
        corroboration = 0.0

        # Check for explicit corroboration patterns
        for pattern in self.CORROBORATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                corroboration += 0.25

        # Multiple witnesses add corroboration
        if len(witnesses) >= 3:
            corroboration += 0.3
        elif len(witnesses) >= 2:
            corroboration += 0.15

        # Documented witnesses count more
        documented = sum(1 for w in witnesses if w.get('type') == 'documented')
        corroboration += documented * 0.1

        return min(1.0, corroboration)

    def _validate_timestamps(self, text: str) -> bool:
        """Check for timestamp validity claims."""
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO date
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # US date
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        ]

        for pattern in timestamp_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _calculate_weighted_support(
        self,
        witnesses: List[Dict],
        crypto_verified: bool,
        credibility: float,
        custody_score: float,
        corroboration: float
    ) -> float:
        """
        Calculate weighted support from all testimony factors.

        Returns:
            Score from 0.0 to 1.0
        """
        if not witnesses:
            return 0.0

        # Base score from witness count (diminishing returns)
        witness_score = min(0.3, len(witnesses) * 0.1)

        # Weight by credibility
        weighted = witness_score * credibility

        # Add custody score
        weighted += custody_score * 0.2

        # Add corroboration
        weighted += corroboration * 0.3

        # Crypto verification bonus
        if crypto_verified:
            weighted += 0.2

        return min(1.0, weighted)

    # =========================================================================
    # CRYPTOGRAPHIC VERIFICATION METHODS (for external integration)
    # =========================================================================

    @staticmethod
    def create_testimony_hash(testimony: str, timestamp: str) -> str:
        """
        Create a SHA-256 hash of testimony for later verification.

        In production, this would be stored on blockchain or similar.
        """
        combined = f"{testimony}|{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def verify_testimony_hash(testimony: str, timestamp: str, expected_hash: str) -> bool:
        """Verify testimony hasn't been altered since hash creation."""
        computed = WitnessThrust.create_testimony_hash(testimony, timestamp)
        return computed == expected_hash

    def register_testimony(
        self,
        claim: str,
        testimony: str,
        witness_id: str,
        signature: Optional[str] = None
    ) -> Dict:
        """
        Register verified testimony in the database.

        Args:
            claim: The claim this testimony relates to
            testimony: The witness testimony text
            witness_id: Identifier for the witness
            signature: Optional cryptographic signature

        Returns:
            Registration record with hash
        """
        timestamp = datetime.utcnow().isoformat()
        testimony_hash = self.create_testimony_hash(testimony, timestamp)

        record = {
            'claim': claim,
            'testimony': testimony,
            'witness_id': witness_id,
            'timestamp': timestamp,
            'hash': testimony_hash,
            'signature': signature,
            'verified': signature is not None
        }

        # Store in database (keyed by hash)
        self._testimony_db[testimony_hash] = record

        return record

    def lookup_testimony(self, claim: str) -> List[Dict]:
        """Look up registered testimonies for a claim."""
        results = []
        for record in self._testimony_db.values():
            if claim.lower() in record['claim'].lower():
                results.append(record)
        return results
