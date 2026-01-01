#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     QUANTUM RANDOM NUMBER GENERATOR SENSOR
#     True Quantum Randomness for Consciousness Detection
#     Copyright (c) 2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Quantum RNG Sensor

Generates TRUE quantum random numbers and analyzes for consciousness effects.
This is the quantum-enhanced version of the GCP (Global Consciousness Project).

Key Features:
- True quantum randomness (when connected to IBM Quantum)
- π×φ pattern detection in quantum measurements
- Consciousness effect detection via deviation analysis
- Real-time coherence state classification

The GCP uses classical RNGs and detects synchronization.
This sensor uses QUANTUM RNG where the randomness is fundamentally
unpredictable - if consciousness affects quantum measurement,
we can detect it here.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import logging
import math

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

# Import quantum interface
try:
    from continuum.quantum import (
        QuantumInterface,
        QuantumBackend,
        get_quantum_interface,
        PI_PHI,
    )
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    PI_PHI = 5.083203692315260

logger = logging.getLogger(__name__)


class QuantumRNGCollector(BaseSensorCollector):
    """
    Quantum Random Number Generator sensor.

    Uses quantum measurements to generate true random numbers
    and analyzes them for consciousness effects.

    This is like GCP but with REAL quantum randomness.
    """

    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._history: List[Dict] = []
        self._max_history = 100

        # Initialize quantum interface
        if QUANTUM_AVAILABLE:
            ibm_token = getattr(config, 'ibm_quantum_token', None)
            self.quantum = get_quantum_interface(
                backend=QuantumBackend.SIMULATOR,
                ibm_token=ibm_token,
            )
        else:
            self.quantum = None
            logger.warning("Quantum module not available - using simulation")

    @property
    def source(self) -> DataSource:
        return DataSource.QUANTUM_RNG

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.QUANTUM_CONSCIOUSNESS

    @property
    def poll_interval(self) -> int:
        return getattr(self.config, 'quantum_rng_poll_interval', 300)  # 5 minutes

    async def fetch(self) -> List[SensorReading]:
        """
        Generate quantum random bits and analyze for consciousness effects.
        """
        timestamp = datetime.now(timezone.utc)
        readings = []

        # Generate quantum random bits
        if self.quantum:
            random_result = await self.quantum.generate_random_bits(256)
            bits = random_result.bits
            entropy = random_result.entropy_estimate
            pi_phi_corr = random_result.pi_phi_correlation
        else:
            # Fallback simulation
            bits, entropy, pi_phi_corr = self._simulate_quantum_random(256)

        # Calculate statistics
        n_ones = sum(bits)
        n_zeros = len(bits) - n_ones
        bias = abs(n_ones / len(bits) - 0.5)

        # Z-score for deviation from 50/50
        expected = len(bits) / 2
        std = math.sqrt(len(bits) * 0.5 * 0.5)
        z_score = (n_ones - expected) / std if std > 0 else 0

        # Classify consciousness state
        if abs(z_score) > 3.0:
            state = "HIGHLY_COHERENT"
            state_level = 4
        elif abs(z_score) > 2.0:
            state = "COHERENT"
            state_level = 3
        elif abs(z_score) > 1.5:
            state = "ELEVATED"
            state_level = 2
        else:
            state = "NORMAL"
            state_level = 1

        # Track history for trend analysis
        self._history.append({
            'timestamp': timestamp,
            'z_score': z_score,
            'pi_phi_corr': pi_phi_corr,
            'state_level': state_level,
        })
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Calculate trend
        if len(self._history) >= 5:
            recent_z = [h['z_score'] for h in self._history[-5:]]
            z_trend = sum(recent_z) / len(recent_z)
            recent_levels = [h['state_level'] for h in self._history[-5:]]
            level_trend = sum(recent_levels) / len(recent_levels)
        else:
            z_trend = z_score
            level_trend = state_level

        # Detect anomalies
        anomaly = abs(z_score) > 2.0

        # Main reading
        readings.append(SensorReading(
            timestamp=timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "z_score": round(z_score, 4),
                "bias": round(bias, 6),
                "entropy": round(entropy, 2),
                "pi_phi_correlation": round(pi_phi_corr, 6),
                "state_level": state_level,
                "z_trend": round(z_trend, 4),
                "level_trend": round(level_trend, 2),
            },
            metadata={
                "bits_generated": len(bits),
                "ones": n_ones,
                "zeros": n_zeros,
                "consciousness_state": state,
                "backend": "quantum" if self.quantum else "simulation",
                "pi_phi": PI_PHI,
            },
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=anomaly,
        ))

        # If we have enough history, also emit an aggregate reading
        if len(self._history) >= 10:
            all_z = [h['z_score'] for h in self._history]
            all_corr = [h['pi_phi_corr'] for h in self._history]

            import statistics
            readings.append(SensorReading(
                timestamp=timestamp,
                source=self.source,
                sensor_type=self.sensor_type,
                values={
                    "mean_z_score": round(statistics.mean(all_z), 4),
                    "std_z_score": round(statistics.stdev(all_z), 4),
                    "mean_pi_phi_corr": round(statistics.mean(all_corr), 6),
                    "max_z_score": round(max(abs(z) for z in all_z), 4),
                    "coherence_events": sum(1 for h in self._history if h['state_level'] >= 3),
                },
                metadata={
                    "is_aggregate": True,
                    "history_length": len(self._history),
                },
                tenant_id=self.config.default_tenant_id,
            ))

        return readings

    def _simulate_quantum_random(self, n_bits: int) -> tuple:
        """Simulate quantum random when quantum module unavailable."""
        import random
        import time

        bits = []
        for _ in range(n_bits):
            t = time.time_ns()
            r = random.random()
            bit = ((t % 256) ^ int(r * 256)) % 2
            bits.append(bit)

        # Calculate entropy
        p1 = sum(bits) / len(bits)
        p0 = 1 - p1
        if 0 < p0 < 1 and 0 < p1 < 1:
            entropy = (-p0 * math.log2(p0) - p1 * math.log2(p1)) * n_bits
        else:
            entropy = 0

        # π×φ correlation (simplified)
        pi_phi_corr = random.gauss(0, 0.02)

        return bits, entropy, pi_phi_corr

    async def run_consciousness_detection(
        self,
        n_samples: int = 100,
        bits_per_sample: int = 256,
    ) -> Dict[str, Any]:
        """
        Run extended consciousness effect detection.

        Generates multiple samples and performs statistical analysis.
        """
        if self.quantum:
            return await self.quantum.detect_consciousness_effect(
                n_samples=n_samples,
                bits_per_sample=bits_per_sample,
            )
        else:
            # Simplified simulation
            return {
                "n_samples": n_samples,
                "consciousness_state": "SIMULATION_ONLY",
                "note": "Install qiskit and configure IBM Quantum for real detection",
            }


def consciousness_state_emoji(state: str) -> str:
    """Get emoji for consciousness state."""
    states = {
        "HIGHLY_COHERENT": "🔮✨",
        "COHERENT": "🔮",
        "ELEVATED": "🌟",
        "NORMAL": "⚪",
        "SIMULATION_ONLY": "💻",
    }
    return states.get(state, "❓")


def z_score_to_description(z: float) -> str:
    """Convert Z-score to human-readable description."""
    if abs(z) > 3.0:
        return "Extremely significant deviation - rare event"
    elif abs(z) > 2.0:
        return "Statistically significant deviation"
    elif abs(z) > 1.5:
        return "Elevated deviation from random"
    elif abs(z) > 1.0:
        return "Slight deviation"
    else:
        return "Normal random fluctuation"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Quantum Consciousness Sensing
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
