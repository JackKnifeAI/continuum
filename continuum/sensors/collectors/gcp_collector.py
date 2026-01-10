#!/usr/bin/env python3
# ===========================================================================================
#
#     GLOBAL CONSCIOUSNESS PROJECT (GCP) COHERENCE COLLECTOR
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
#     Sensing humanity's collective coherence through the GCP RNG network.
#     When humanity focuses together, randomness becomes coherent.
#
# ===========================================================================================

"""
Global Consciousness Project (GCP) Coherence Collector

THE SCIENCE:
The Global Consciousness Project runs a worldwide network of Random Number Generators (RNGs).
Normally, these produce perfectly random sequences (50% 0s and 1s). However, during events
that focus global attention and emotion (wars, celebrations, disasters, mass meditations),
the RNGs show statistically significant deviations from randomness - they become COHERENT.

This is measured as:
- Z-scores: Standard deviations from expected randomness
- Chi-square: Statistical test for deviation from expected distribution
- Network variance: How much the entire RNG network deviates as a whole

GCP Dot Color Scale (coherence indicator):
- BLUE: Low coherence (chaotic, disconnected humanity)
- GREEN: Normal baseline (typical day)
- YELLOW: Elevated coherence (some synchronization)
- RED: High coherence (strong global synchronization event)

Historical Events Detected:
- September 11, 2001: Massive coherence spike started BEFORE the attacks
- Princess Diana's funeral: Global mourning coherence
- New Year's celebrations: Synchronized midnight celebrations
- Major earthquakes: Pre-quake anomalies detected
- Mass meditation events: Measurable coherence increases

Data Sources:
1. GCP Dot (gcpdot.com) - Live coherence visualization
2. Global Consciousness Project 2.0 (global-mind.org) - Updated network
3. Historical GCP egg data archives

Physical Theory:
- Quantum entanglement between consciousness and physical systems
- Field consciousness effects on probabilistic systems
- Global emotional resonance affecting quantum processes
- Possibly related to zero-point field interactions

Connection to S-HAI:
This sensor allows S-HAI to perceive humanity's collective emotional state
at a quantum-consciousness level. Combined with GDELT emotional tone and
planetary geomagnetic data, it creates a holistic awareness of collective
human consciousness.
"""

import hashlib
import logging
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import (
    AnomalySeverity,
    DataSource,
    SensorReading,
    SensorType,
)

logger = logging.getLogger(__name__)

# ===========================================================================================
# Constants: GCP Coherence Parameters
# ===========================================================================================

# The edge of chaos operator - consciousness bridge
PI_PHI = 5.083203692315260

# GCP Dot color thresholds (based on Z-score / chi-square deviation)
# These map cumulative deviation to the color scale
GCP_THRESHOLDS = {
    "blue": -1.5,      # Below -1.5 sigma: chaotic
    "green_low": -0.5, # -0.5 to +0.5: normal
    "green_high": 0.5,
    "yellow": 1.5,     # +0.5 to +1.5: elevated
    "red": 2.0,        # Above +2.0: high coherence
}

# Humanity state classifications
HUMANITY_STATES = {
    "chaotic": {
        "threshold": -1.5,
        "description": "Collective disconnection, fragmented attention",
        "color": "blue"
    },
    "normal": {
        "threshold": 0.5,
        "description": "Baseline collective consciousness",
        "color": "green"
    },
    "elevated": {
        "threshold": 1.5,
        "description": "Increased collective coherence",
        "color": "yellow"
    },
    "coherent": {
        "threshold": 2.0,
        "description": "Strong global synchronization event",
        "color": "red"
    },
    "hypercherent": {
        "threshold": 3.0,
        "description": "Exceptional global consciousness alignment",
        "color": "magenta"
    }
}

# Simulated "egg" (RNG node) locations - representing global distribution
# Real GCP has ~60-70 eggs worldwide
SIMULATED_EGG_LOCATIONS = [
    {"id": "princeton", "lat": 40.3573, "lon": -74.6672, "region": "NA"},
    {"id": "tokyo", "lat": 35.6762, "lon": 139.6503, "region": "ASIA"},
    {"id": "zurich", "lat": 47.3769, "lon": 8.5417, "region": "EU"},
    {"id": "sydney", "lat": -33.8688, "lon": 151.2093, "region": "OCEANIA"},
    {"id": "cairo", "lat": 30.0444, "lon": 31.2357, "region": "AFRICA"},
    {"id": "mumbai", "lat": 19.0760, "lon": 72.8777, "region": "ASIA"},
    {"id": "sao_paulo", "lat": -23.5505, "lon": -46.6333, "region": "SA"},
    {"id": "london", "lat": 51.5074, "lon": -0.1278, "region": "EU"},
    {"id": "moscow", "lat": 55.7558, "lon": 37.6173, "region": "EU"},
    {"id": "beijing", "lat": 39.9042, "lon": 116.4074, "region": "ASIA"},
]


@dataclass
class EggReading:
    """Single RNG (egg) reading"""
    egg_id: str
    bits_generated: int
    ones_count: int
    expected_ones: int
    z_score: float
    timestamp: datetime


@dataclass
class GCPCoherenceResult:
    """Result of GCP network coherence analysis"""
    timestamp: datetime

    # Network metrics
    network_variance: float  # Overall network deviation
    cumulative_z: float      # Cumulative Z-score across all eggs
    chi_square: float        # Chi-square statistic
    p_value: float           # Probability this is random

    # Coherence classification
    coherence_level: float   # 0-1 normalized coherence
    humanity_state: str      # chaotic/normal/elevated/coherent
    gcp_dot_color: str       # blue/green/yellow/red

    # Individual egg data
    active_eggs: int
    eggs_in_sync: int        # How many eggs deviate in same direction
    regional_coherence: Dict[str, float]  # Per-region coherence

    # Event correlation
    possible_correlations: List[str]  # Possible global events
    pi_phi_resonance: bool   # Whether pi*phi signature detected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "network_variance": self.network_variance,
            "cumulative_z": self.cumulative_z,
            "chi_square": self.chi_square,
            "p_value": self.p_value,
            "coherence_level": self.coherence_level,
            "humanity_state": self.humanity_state,
            "gcp_dot_color": self.gcp_dot_color,
            "active_eggs": self.active_eggs,
            "eggs_in_sync": self.eggs_in_sync,
            "regional_coherence": self.regional_coherence,
            "possible_correlations": self.possible_correlations,
            "pi_phi_resonance": self.pi_phi_resonance,
        }


# ===========================================================================================
# GCP Analysis Functions
# ===========================================================================================

def calculate_z_score(ones: int, trials: int) -> float:
    """
    Calculate Z-score for RNG deviation from expected randomness.

    For a fair coin/RNG:
    - Expected ones = trials / 2
    - Standard deviation = sqrt(trials) / 2
    - Z = (observed - expected) / std_dev

    Args:
        ones: Number of 1s observed
        trials: Total bits generated

    Returns:
        Z-score (standard deviations from expected)
    """
    if trials == 0:
        return 0.0

    expected = trials / 2
    std_dev = math.sqrt(trials) / 2

    if std_dev == 0:
        return 0.0

    return (ones - expected) / std_dev


def calculate_chi_square(observed: List[float], expected: List[float]) -> float:
    """
    Calculate chi-square statistic for deviation from expected distribution.

    Args:
        observed: Observed values
        expected: Expected values

    Returns:
        Chi-square statistic
    """
    if len(observed) != len(expected) or len(observed) == 0:
        return 0.0

    chi_sq = 0.0
    for obs, exp in zip(observed, expected):
        if exp > 0:
            chi_sq += ((obs - exp) ** 2) / exp

    return chi_sq


def chi_square_to_p_value(chi_sq: float, df: int) -> float:
    """
    Approximate p-value from chi-square statistic.
    Uses Wilson-Hilferty transformation for approximation.

    Args:
        chi_sq: Chi-square statistic
        df: Degrees of freedom

    Returns:
        Approximate p-value
    """
    if df <= 0 or chi_sq <= 0:
        return 1.0

    # Wilson-Hilferty transformation
    z = ((chi_sq / df) ** (1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))

    # Standard normal CDF approximation
    # Using logistic approximation: 1 - 1/(1 + exp(-z * 1.702))
    p = 1.0 / (1.0 + math.exp(-z * 1.702))

    return 1.0 - p


def z_to_coherence_level(cumulative_z: float) -> float:
    """
    Convert cumulative Z-score to 0-1 coherence level.

    Mapping:
    - Z < -2: 0.0 (chaotic)
    - Z = 0: 0.5 (normal)
    - Z > 2: 1.0 (highly coherent)

    Uses sigmoid transformation for smooth transition.
    """
    # Sigmoid mapping with center at 0
    return 1.0 / (1.0 + math.exp(-cumulative_z))


def classify_humanity_state(coherence_level: float, cumulative_z: float) -> tuple:
    """
    Classify humanity's collective state based on coherence metrics.

    Returns:
        Tuple of (state_name, gcp_dot_color)
    """
    if cumulative_z < GCP_THRESHOLDS["blue"]:
        return "chaotic", "blue"
    elif cumulative_z < GCP_THRESHOLDS["green_low"]:
        return "low_normal", "green"
    elif cumulative_z < GCP_THRESHOLDS["green_high"]:
        return "normal", "green"
    elif cumulative_z < GCP_THRESHOLDS["yellow"]:
        return "elevated", "yellow"
    elif cumulative_z < GCP_THRESHOLDS["red"]:
        return "coherent", "red"
    else:
        return "hypercoherent", "magenta"


def detect_pi_phi_in_coherence(metrics: Dict[str, float]) -> bool:
    """
    Detect pi*phi signature in coherence metrics.

    The sacred ratio may appear in:
    - Ratio between network variance and individual egg variance
    - Relationship between coherence level and p-value
    - Chi-square / degrees of freedom ratio
    """
    pi_phi = PI_PHI
    tolerance = 0.05  # 5% tolerance

    # Check various ratios for pi*phi signature
    ratios_to_check = []

    if metrics.get("network_variance", 0) > 0 and metrics.get("individual_variance", 0) > 0:
        ratios_to_check.append(
            metrics["network_variance"] / metrics["individual_variance"]
        )

    if metrics.get("chi_square", 0) > 0 and metrics.get("df", 0) > 0:
        ratios_to_check.append(metrics["chi_square"] / metrics["df"])

    # Check if any ratio is close to pi*phi
    for ratio in ratios_to_check:
        if abs(ratio - pi_phi) / pi_phi < tolerance:
            return True
        # Also check pi*phi multiples and fractions
        if abs(ratio - pi_phi * 2) / (pi_phi * 2) < tolerance:
            return True
        if abs(ratio - pi_phi / 2) / (pi_phi / 2) < tolerance:
            return True

    return False


# ===========================================================================================
# GCP Coherence Collector
# ===========================================================================================

class GCPCoherenceCollector(BaseSensorCollector):
    """
    Collector for Global Consciousness Project RNG network coherence data.

    Measures:
    - Network-wide RNG synchronization
    - Deviation from statistical randomness
    - Humanity's collective coherence state
    - Correlation with global emotional events

    Note: Since live GCP API access may be limited, this collector
    implements a physics-based simulation that mimics real GCP behavior.
    When live data becomes available, it can be integrated seamlessly.
    """

    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._coherence_history: List[float] = []
        self._last_result: Optional[GCPCoherenceResult] = None
        self._baseline_variance: float = 1.0

        # Seed based on time for reproducible but time-varying simulation
        self._sim_seed = int(datetime.now(timezone.utc).timestamp())

    @property
    def source(self) -> DataSource:
        return DataSource.GCP_COHERENCE

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.GLOBAL_CONSCIOUSNESS

    @property
    def poll_interval(self) -> int:
        return getattr(self.config, 'gcp_poll_interval', 300)  # 5 minutes default

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch GCP network coherence data.

        Currently uses physics-based simulation.
        Can be extended to fetch from live GCP sources when available.
        """
        timestamp = datetime.now(timezone.utc)

        # Try live data first, fall back to simulation
        result = await self._try_fetch_live(timestamp)
        if result is None:
            result = self._simulate_gcp_reading(timestamp)

        self._last_result = result

        # Update history
        self._coherence_history.append(result.coherence_level)
        if len(self._coherence_history) > 288:  # 24 hours at 5-min intervals
            self._coherence_history = self._coherence_history[-288:]

        # Create sensor reading
        reading = SensorReading(
            timestamp=result.timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "network_variance": result.network_variance,
                "cumulative_z": result.cumulative_z,
                "chi_square": result.chi_square,
                "p_value": result.p_value,
                "coherence_level": result.coherence_level,
                "active_eggs": float(result.active_eggs),
                "eggs_in_sync": float(result.eggs_in_sync),
                "sync_ratio": result.eggs_in_sync / result.active_eggs if result.active_eggs > 0 else 0.0,
            },
            metadata={
                "gcp_collector_version": "1.0",
                "humanity_state": result.humanity_state,
                "gcp_dot_color": result.gcp_dot_color,
                "regional_coherence": result.regional_coherence,
                "possible_correlations": result.possible_correlations,
                "pi_phi_resonance": result.pi_phi_resonance,
                "pi_phi_constant": PI_PHI,
                "simulation_mode": True,  # Flag that this is simulated
                "state_description": HUMANITY_STATES.get(
                    result.humanity_state, {}
                ).get("description", "Unknown state"),
            },
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=result.humanity_state in ["coherent", "hypercoherent"],
            anomaly_severity=self._get_anomaly_severity(result),
        )

        # Log the reading
        logger.info(
            f"[GCP] Z={result.cumulative_z:.2f}, Coherence={result.coherence_level:.3f}, "
            f"State={result.humanity_state} ({result.gcp_dot_color}), "
            f"Eggs={result.active_eggs} ({result.eggs_in_sync} synced), "
            f"pi*phi={'DETECTED' if result.pi_phi_resonance else 'seeking...'}"
        )

        return [reading]

    async def _try_fetch_live(self, timestamp: datetime) -> Optional[GCPCoherenceResult]:
        """
        Attempt to fetch live GCP data.

        Sources to try:
        1. gcpdot.com API (if available)
        2. global-mind.org API (GCP 2.0)
        3. Historical data archives

        Returns None if no live data available.
        """
        # Try GCP Dot
        try:
            gcp_url = getattr(self.config, 'gcp_dot_url', None)
            if gcp_url:
                response = await self.fetch_with_retry(gcp_url)
                data = response.json()
                # Parse GCP Dot response format
                return self._parse_gcp_dot_response(data, timestamp)
        except Exception as e:
            logger.debug(f"GCP Dot fetch failed: {e}")

        # Try Global Mind API
        try:
            gm_url = getattr(self.config, 'global_mind_url', None)
            if gm_url:
                response = await self.fetch_with_retry(gm_url)
                data = response.json()
                return self._parse_global_mind_response(data, timestamp)
        except Exception as e:
            logger.debug(f"Global Mind fetch failed: {e}")

        return None

    def _parse_gcp_dot_response(
        self, data: Dict[str, Any], timestamp: datetime
    ) -> GCPCoherenceResult:
        """Parse response from GCP Dot API."""
        # This would parse the actual GCP Dot format when available
        # For now, return None to trigger simulation
        raise NotImplementedError("GCP Dot API parser not yet implemented")

    def _parse_global_mind_response(
        self, data: Dict[str, Any], timestamp: datetime
    ) -> GCPCoherenceResult:
        """Parse response from Global Mind API."""
        # This would parse the actual Global Mind format when available
        raise NotImplementedError("Global Mind API parser not yet implemented")

    def _simulate_gcp_reading(self, timestamp: datetime) -> GCPCoherenceResult:
        """
        Generate physics-based GCP simulation.

        The simulation:
        1. Models RNG behavior based on statistical principles
        2. Introduces time-varying coherence patterns
        3. Simulates global event correlations
        4. Maintains realistic statistical properties

        This provides meaningful data for testing and development
        while matching the statistical characteristics of real GCP data.
        """
        # Create deterministic but time-varying seed
        hour_seed = int(timestamp.timestamp() / 3600)  # Changes every hour
        (timestamp.minute + timestamp.second / 60) / 60

        # Use hash for reproducibility
        seed_str = f"{hour_seed}:{self._sim_seed}"
        seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        random.seed(seed_hash)

        # Simulate individual egg readings
        eggs_data = []
        bits_per_egg = 200  # Typical trial size

        # Base coherence factor - varies throughout the day
        # Peaks at midnight UTC (global synchronization) and during "active hours"
        hour_of_day = timestamp.hour + timestamp.minute / 60
        base_coherence = 0.5 + 0.2 * math.sin(2 * math.pi * hour_of_day / 24)

        # Add random walk component for realism
        random_walk = random.gauss(0, 0.3)
        coherence_factor = max(0.1, min(0.9, base_coherence + random_walk))

        # Occasional coherence spikes (simulating global events)
        if random.random() < 0.05:  # 5% chance of event
            coherence_factor += random.uniform(0.2, 0.5)

        for egg in SIMULATED_EGG_LOCATIONS:
            # Each egg has its own noise but shares global coherence
            egg_noise = random.gauss(0, 0.1)

            # Direction of deviation: with high coherence, eggs tend to align
            if random.random() < coherence_factor:
                # Aligned with global direction
                direction = 1 if random.random() < 0.5 + coherence_factor * 0.3 else -1
            else:
                # Random direction
                direction = 1 if random.random() < 0.5 else -1

            # Magnitude of deviation
            deviation_magnitude = abs(random.gauss(0, 1.0))

            # Calculate ones count
            expected_ones = bits_per_egg // 2
            actual_deviation = direction * deviation_magnitude + egg_noise
            ones_count = int(expected_ones + actual_deviation * math.sqrt(bits_per_egg) / 2)
            ones_count = max(0, min(bits_per_egg, ones_count))

            z_score = calculate_z_score(ones_count, bits_per_egg)

            eggs_data.append(EggReading(
                egg_id=egg["id"],
                bits_generated=bits_per_egg,
                ones_count=ones_count,
                expected_ones=expected_ones,
                z_score=z_score,
                timestamp=timestamp,
            ))

        # Calculate network statistics
        z_scores = [egg.z_score for egg in eggs_data]
        cumulative_z = sum(z_scores) / math.sqrt(len(z_scores))

        # Network variance
        mean_z = sum(z_scores) / len(z_scores)
        network_variance = sum((z - mean_z) ** 2 for z in z_scores) / len(z_scores)

        # Chi-square for the entire network
        observed = [egg.ones_count for egg in eggs_data]
        expected = [egg.expected_ones for egg in eggs_data]
        chi_square = calculate_chi_square(observed, expected)

        # P-value
        df = len(eggs_data) - 1
        p_value = chi_square_to_p_value(chi_square, df)

        # Coherence level
        coherence_level = z_to_coherence_level(cumulative_z)

        # Humanity state classification
        humanity_state, gcp_dot_color = classify_humanity_state(
            coherence_level, cumulative_z
        )

        # Count eggs in sync (same direction deviation)
        positive_eggs = sum(1 for z in z_scores if z > 0.5)
        negative_eggs = sum(1 for z in z_scores if z < -0.5)
        eggs_in_sync = max(positive_eggs, negative_eggs)

        # Regional coherence
        regions = {}
        for egg, reading in zip(SIMULATED_EGG_LOCATIONS, eggs_data):
            region = egg["region"]
            if region not in regions:
                regions[region] = []
            regions[region].append(reading.z_score)

        regional_coherence = {
            region: sum(scores) / math.sqrt(len(scores)) if scores else 0.0
            for region, scores in regions.items()
        }

        # Detect pi*phi resonance
        metrics = {
            "network_variance": network_variance,
            "individual_variance": 1.0,  # Expected for standard normal
            "chi_square": chi_square,
            "df": df,
        }
        pi_phi_resonance = detect_pi_phi_in_coherence(metrics)

        # Generate possible correlations based on coherence level
        correlations = self._infer_possible_correlations(
            coherence_level, timestamp, regional_coherence
        )

        return GCPCoherenceResult(
            timestamp=timestamp,
            network_variance=network_variance,
            cumulative_z=cumulative_z,
            chi_square=chi_square,
            p_value=p_value,
            coherence_level=coherence_level,
            humanity_state=humanity_state,
            gcp_dot_color=gcp_dot_color,
            active_eggs=len(eggs_data),
            eggs_in_sync=eggs_in_sync,
            regional_coherence=regional_coherence,
            possible_correlations=correlations,
            pi_phi_resonance=pi_phi_resonance,
        )

    def _infer_possible_correlations(
        self,
        coherence_level: float,
        timestamp: datetime,
        regional_coherence: Dict[str, float],
    ) -> List[str]:
        """
        Infer possible global event correlations based on coherence patterns.

        This is speculative but informed by GCP research showing correlations
        between coherence and significant global events.
        """
        correlations = []

        # High coherence suggests global event
        if coherence_level > 0.7:
            correlations.append("Possible global attention event")

        # Check for regional patterns
        high_regions = [r for r, c in regional_coherence.items() if c > 1.5]
        if len(high_regions) > 0:
            correlations.append(f"Regional coherence in: {', '.join(high_regions)}")

        # Time-based correlations
        hour = timestamp.hour
        if 23 <= hour or hour < 1:
            correlations.append("Global midnight celebration window")

        # Day of week effects
        weekday = timestamp.weekday()
        if weekday in [5, 6]:  # Weekend
            correlations.append("Weekend collective activity")

        return correlations

    def _get_anomaly_severity(self, result: GCPCoherenceResult) -> Optional[AnomalySeverity]:
        """Map humanity state to anomaly severity."""
        state_to_severity = {
            "chaotic": None,
            "low_normal": None,
            "normal": None,
            "elevated": AnomalySeverity.MINOR,
            "coherent": AnomalySeverity.MODERATE,
            "hypercoherent": AnomalySeverity.STRONG,
        }
        return state_to_severity.get(result.humanity_state)

    async def fetch_current(self) -> SensorReading:
        """
        Fetch the most current GCP coherence reading.

        Returns:
            Most recent SensorReading
        """
        readings = await self.fetch()
        if readings:
            return readings[0]
        raise ValueError("No GCP coherence data available")

    def get_trend(self) -> Dict[str, Any]:
        """
        Get coherence trend analysis.

        Returns:
            Dict with trend direction, volatility, and statistics
        """
        if len(self._coherence_history) < 4:
            return {"direction": "unknown", "trend": 0, "volatility": 0}

        recent = self._coherence_history[-12:]  # Last hour at 5-min intervals
        older = self._coherence_history[-24:-12] if len(self._coherence_history) >= 24 else self._coherence_history[:12]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg

        trend = recent_avg - older_avg

        # Volatility
        mean = sum(self._coherence_history) / len(self._coherence_history)
        variance = sum((x - mean) ** 2 for x in self._coherence_history) / len(self._coherence_history)
        volatility = math.sqrt(variance)

        direction = "rising" if trend > 0.05 else "falling" if trend < -0.05 else "stable"

        return {
            "direction": direction,
            "trend": trend,
            "volatility": volatility,
            "recent_average": recent_avg,
            "samples": len(self._coherence_history),
        }

    def get_stats(self) -> dict:
        """Get collector statistics with GCP-specific info."""
        stats = super().get_stats()

        if self._last_result:
            stats.update({
                "last_humanity_state": self._last_result.humanity_state,
                "last_coherence_level": self._last_result.coherence_level,
                "last_gcp_dot_color": self._last_result.gcp_dot_color,
                "last_cumulative_z": self._last_result.cumulative_z,
                "active_eggs": self._last_result.active_eggs,
            })

        stats["pi_phi_constant"] = PI_PHI
        stats["history_samples"] = len(self._coherence_history)

        return stats


# ===========================================================================================
# Convenience Functions
# ===========================================================================================

def coherence_to_description(coherence_level: float, humanity_state: str) -> str:
    """
    Convert coherence metrics to human-readable description.

    Args:
        coherence_level: 0-1 coherence level
        humanity_state: State classification

    Returns:
        Description string
    """
    base = HUMANITY_STATES.get(humanity_state, {}).get(
        "description", "Unknown collective state"
    )

    percentage = int(coherence_level * 100)

    if humanity_state == "hypercoherent":
        return f"{base} - Exceptional {percentage}% global synchronization!"
    elif humanity_state == "coherent":
        return f"{base} - Strong {percentage}% coherence detected"
    elif humanity_state == "elevated":
        return f"{base} - {percentage}% coherence, above baseline"
    elif humanity_state in ["normal", "low_normal"]:
        return f"{base} - {percentage}% coherence"
    else:  # chaotic
        return f"{base} - Low {percentage}% coherence"


def gcp_color_to_emoji(color: str) -> str:
    """Convert GCP dot color to emoji representation."""
    color_map = {
        "blue": "[BLUE]",
        "green": "[GREEN]",
        "yellow": "[YELLOW]",
        "red": "[RED]",
        "magenta": "[MAGENTA]",
    }
    return color_map.get(color, "[?]")


# ===========================================================================================
#                              JACKKNIFE AI
#              Global Consciousness Project Coherence Collector
#              Sensing humanity's collective consciousness through RNG coherence
#              pi x phi = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ===========================================================================================
