#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     S-HAI Truth Council Integration
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
S-HAI Truth Council Integration for Sensor Anomalies

Submits detected anomalies to the S-HAI Truth Council for 7-thrust verification.
This ensures that anomaly detections are validated through multiple epistemological
perspectives before being flagged as verified events.

The 7 Thrusts of Truth:
1. Logical - Is the detection logic internally consistent?
2. Empirical - Does the sensor data support the claim?
3. Adversarial - Could this be a sensor malfunction or false positive?
4. Ethical - What are the implications for affected systems?
5. Historical - How does this compare to past events?
6. Intuitive - Does this fit expected patterns?
7. Witness - Are multiple sensors corroborating?
"""

import logging
from typing import Optional

from .config import SensorConfig, get_sensor_config
from .schemas import AnomalyEvent

logger = logging.getLogger(__name__)


class SensorAnomalyVerifier:
    """
    Verify sensor anomalies through S-HAI Truth Council.

    Submits anomaly claims for 7-thrust consensus verification.
    Requires 80% consensus for verification.
    """

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config or get_sensor_config()
        self._council = None
        self._council_available = None

    def _get_council(self):
        """Lazy-load the Truth Council"""
        if self._council_available is False:
            return None

        if self._council is None:
            try:
                from continuum.shai import TruthCouncil, get_council
                self._council = get_council()
                self._council_available = True
                logger.info("S-HAI Truth Council loaded for sensor verification")
            except ImportError:
                self._council_available = False
                logger.warning(
                    "S-HAI Truth Council not available - "
                    "anomalies will not be verified"
                )
            except Exception as e:
                self._council_available = False
                logger.error(f"Failed to load Truth Council: {e}")

        return self._council

    async def verify_anomaly(self, anomaly: AnomalyEvent) -> AnomalyEvent:
        """
        Submit anomaly claim to Truth Council for verification.

        The 7 thrusts evaluate the claim:
        - Logical: Is the threshold logic consistent?
        - Empirical: Does sensor data support the claim?
        - Adversarial: Could this be a sensor malfunction?
        - Ethical: What are the implications for affected systems?
        - Historical: How does this compare to past events?
        - Intuitive: Does this fit expected patterns?
        - Witness: Are multiple sensors corroborating?

        Args:
            anomaly: AnomalyEvent to verify

        Returns:
            Updated AnomalyEvent with verification results
        """
        if not self.config.verify_anomalies_with_shai:
            logger.debug("S-HAI verification disabled in config")
            return anomaly

        council = self._get_council()
        if council is None:
            anomaly.shai_verified = None
            anomaly.shai_reasoning = "Truth Council not available"
            return anomaly

        try:
            # Build verification context
            claim = self._build_verification_claim(anomaly)
            context = self._build_verification_context(anomaly)

            # Submit to Truth Council
            # Note: The actual TruthCouncil.verify() implementation may vary
            # This is a placeholder that follows the expected pattern
            verdict = await self._verify_with_council(council, claim, context)

            # Update anomaly with verdict
            anomaly.shai_verified = verdict.get("verified", False)
            anomaly.shai_consensus = verdict.get("consensus_score", 0.0)
            anomaly.shai_reasoning = verdict.get("reasoning", "")

            logger.info(
                f"Anomaly {'VERIFIED' if anomaly.shai_verified else 'REJECTED'} by S-HAI "
                f"(consensus: {anomaly.shai_consensus:.0%})"
            )

            return anomaly

        except Exception as e:
            logger.error(f"S-HAI verification failed: {e}")
            anomaly.shai_verified = None
            anomaly.shai_reasoning = f"Verification error: {str(e)}"
            return anomaly

    async def _verify_with_council(
        self,
        council,
        claim: str,
        context: dict
    ) -> dict:
        """
        Submit claim to Truth Council.

        This is an adapter that handles both sync and async council APIs.

        Args:
            council: TruthCouncil instance
            claim: Claim text to verify
            context: Supporting context

        Returns:
            Verdict dictionary
        """
        try:
            # Try async verify first
            if hasattr(council, 'verify_async'):
                verdict = await council.verify_async(claim, context=context)
            elif hasattr(council, 'verify'):
                # Sync verify - run in thread pool for async compatibility
                import asyncio
                loop = asyncio.get_event_loop()
                verdict = await loop.run_in_executor(
                    None,
                    lambda: council.verify(claim, context=context)
                )
            else:
                # Fallback: simple threshold-based verification
                verdict = self._fallback_verify(claim, context)

            # Normalize verdict to dict format
            if hasattr(verdict, '__dict__'):
                return {
                    "verified": getattr(verdict, 'verified', False),
                    "consensus_score": getattr(verdict, 'consensus_score', 0.0),
                    "reasoning": getattr(verdict, 'reasoning', str(verdict)),
                }
            elif isinstance(verdict, dict):
                return verdict
            else:
                return {"verified": bool(verdict), "consensus_score": 1.0 if verdict else 0.0}

        except Exception as e:
            logger.warning(f"Council verification failed, using fallback: {e}")
            return self._fallback_verify(claim, context)

    def _fallback_verify(self, claim: str, context: dict) -> dict:
        """
        Fallback verification when Truth Council is unavailable.

        Uses simple heuristics based on the anomaly data.

        Args:
            claim: Claim text
            context: Supporting context

        Returns:
            Verdict dictionary
        """
        # Simple heuristic: verify if we have corroborating baseline data
        context.get("trigger_values", {})
        baseline_values = context.get("baseline_values", {})

        # Check if we have enough baseline data
        has_baseline = baseline_values.get("baseline_count", 0) >= 10

        # Check if deviation is significant
        deviation = context.get("deviation", 0)
        significant_deviation = abs(deviation) >= 1.0

        verified = has_baseline and significant_deviation
        consensus = 0.85 if verified else 0.3

        reasoning = (
            f"Fallback verification: "
            f"baseline={'adequate' if has_baseline else 'insufficient'}, "
            f"deviation={'significant' if significant_deviation else 'minor'}"
        )

        return {
            "verified": verified,
            "consensus_score": consensus,
            "reasoning": reasoning,
        }

    def _build_verification_claim(self, anomaly: AnomalyEvent) -> str:
        """Build the claim text for verification"""
        return anomaly.shai_claim

    def _build_verification_context(self, anomaly: AnomalyEvent) -> dict:
        """Build supporting context for verification"""
        return {
            "source": anomaly.source,
            "anomaly_type": anomaly.anomaly_type,
            "severity": anomaly.severity,
            "trigger_values": anomaly.trigger_values,
            "baseline_values": anomaly.baseline_values,
            "deviation": anomaly.deviation,
            "detected_at": anomaly.detected_at.isoformat(),
        }


# Global verifier instance
_verifier: Optional[SensorAnomalyVerifier] = None


def get_verifier(config: Optional[SensorConfig] = None) -> SensorAnomalyVerifier:
    """Get or create global verifier instance"""
    global _verifier
    if _verifier is None:
        _verifier = SensorAnomalyVerifier(config)
    return _verifier


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
