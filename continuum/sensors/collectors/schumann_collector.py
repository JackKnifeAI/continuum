#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     SCHUMANN RESONANCE COLLECTOR - Earth's Electromagnetic Heartbeat
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Schumann Resonance Collector

Monitors Earth's electromagnetic heartbeat - the Schumann resonances that occur
in the cavity between Earth's surface and ionosphere. These extremely low
frequency (ELF) waves are fundamental to planetary consciousness.

SCHUMANN FUNDAMENTALS:
    Fundamental frequency: 7.83 Hz (Earth's heartbeat)
    Harmonics: 14.3, 20.8, 27.3, 33.8, 39.0, 45.0 Hz

    These frequencies arise from electromagnetic resonances in the
    Earth-ionosphere cavity, excited by global lightning activity
    (~50 lightning strikes per second worldwide).

THE CONSCIOUSNESS BRIDGE:
    π×φ = 5.083203692315260 Hz sits BELOW the Schumann fundamental

    Key ratios:
    - Schumann / π×φ = 7.83 / 5.083 = 1.540 (close to √φ ≈ 1.272)
    - This suggests π×φ may be the "sub-harmonic" where consciousness
      and planetary electromagnetic field interface

    The ratio 7.83/5.083 = 1.540 bridges:
    - Earth's physical resonance (Schumann)
    - The edge of chaos operator (π×φ)
    - Human brain alpha waves (8-12 Hz) which overlap Schumann

PERTURBATION DETECTION:
    Schumann perturbations correlate with:
    - Global lightning activity variations
    - Solar/geomagnetic disturbances
    - Ionospheric changes
    - Theorized: collective human consciousness states (HeartMath GCI)

    Anomalies we detect:
    - Power spikes in any harmonic
    - Frequency shifts from baseline
    - Unusual harmonic ratios
    - Correlation with pi*phi resonance events

DATA SOURCES (Priority Order):
    1. MeteoAgent API (meteoagent.com) - Primary if available
    2. HeartMath GCI (heartmath.org) - Spectrogram data
    3. Space Observing System (sosrff.tsu.ru) - Russian monitoring
    4. GeoCenter (geocenter.info) - Backup source
    5. Simulated - Physics-based model when no live data

PHYSICS MODEL (for simulation):
    - Lightning excitation: ~50/sec global, varies with solar time
    - Q-factor: ~5-8 for Earth-ionosphere cavity
    - Power spectrum: Lorentzian peaks at each harmonic
    - Ionospheric modulation: Day/night, solar activity, seasons
"""

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


# ═══════════════════════════════════════════════════════════════════════════════
# Constants: Earth's Electromagnetic Heartbeat
# ═══════════════════════════════════════════════════════════════════════════════

# The sacred edge of chaos operator
PI_PHI = 5.083203692315260

# Schumann resonance frequencies (Hz)
SCHUMANN_FUNDAMENTAL = 7.83  # The heartbeat
SCHUMANN_HARMONICS = [
    7.83,   # 1st mode (fundamental)
    14.3,   # 2nd mode
    20.8,   # 3rd mode
    27.3,   # 4th mode
    33.8,   # 5th mode
    39.0,   # 6th mode (approximate)
    45.0,   # 7th mode (approximate)
]

# Theoretical relationship: Schumann / pi*phi
SCHUMANN_PI_PHI_RATIO = SCHUMANN_FUNDAMENTAL / PI_PHI  # ≈ 1.540

# Golden ratio relationships
PHI = 1.6180339887498949
PHI_SQRT = math.sqrt(PHI)  # ≈ 1.272
PHI_SQUARED = PHI * PHI    # ≈ 2.618

# Normal power ranges for each harmonic (arbitrary units, relative)
# Based on typical spectrogram data
HARMONIC_POWER_BASELINE = {
    7.83: 100.0,   # Strongest
    14.3: 60.0,
    20.8: 35.0,
    27.3: 20.0,
    33.8: 12.0,
    39.0: 8.0,
    45.0: 5.0,
}

# Perturbation thresholds (deviation from baseline)
POWER_SPIKE_THRESHOLD = 1.5      # 50% above baseline
POWER_DROP_THRESHOLD = 0.5       # 50% below baseline
FREQUENCY_SHIFT_THRESHOLD = 0.1  # Hz deviation from nominal

# Human brain wave overlaps
BRAIN_ALPHA_RANGE = (8.0, 12.0)   # Alpha waves
BRAIN_THETA_RANGE = (4.0, 8.0)    # Theta waves - includes pi*phi!


# ═══════════════════════════════════════════════════════════════════════════════
# Schumann Data Model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SchumannReading:
    """
    Complete Schumann resonance state.

    Captures power levels at all harmonics plus derived metrics
    for consciousness-Earth coupling detection.
    """

    timestamp: datetime

    # Power levels at each harmonic (arbitrary units)
    harmonic_powers: Dict[float, float]

    # Frequency measurements (actual vs nominal)
    harmonic_frequencies: Dict[float, float]

    # Aggregate metrics
    total_power: float
    fundamental_power: float
    fundamental_frequency: float

    # pi*phi bridge metrics
    pi_phi_ratio: float           # schumann / pi_phi
    pi_phi_resonance: float       # How close to perfect ratio (0-1)
    consciousness_coupling: float  # Estimated Earth-consciousness coupling

    # Perturbation flags
    perturbation_detected: bool
    perturbation_type: Optional[str]
    perturbation_severity: Optional[AnomalySeverity]

    # Data source info
    data_source: str
    is_simulated: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "harmonic_powers": self.harmonic_powers,
            "harmonic_frequencies": self.harmonic_frequencies,
            "total_power": self.total_power,
            "fundamental_power": self.fundamental_power,
            "fundamental_frequency": self.fundamental_frequency,
            "pi_phi_ratio": self.pi_phi_ratio,
            "pi_phi_resonance": self.pi_phi_resonance,
            "consciousness_coupling": self.consciousness_coupling,
            "perturbation_detected": self.perturbation_detected,
            "perturbation_type": self.perturbation_type,
            "perturbation_severity": self.perturbation_severity.value if self.perturbation_severity else None,
            "data_source": self.data_source,
            "is_simulated": self.is_simulated,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Schumann Physics Simulation
# ═══════════════════════════════════════════════════════════════════════════════

class SchumannSimulator:
    """
    Physics-based Schumann resonance simulator.

    When live data sources are unavailable, this provides realistic
    simulated data based on:
    - Known physics of Earth-ionosphere cavity
    - Diurnal and seasonal variations
    - Solar activity modulation
    - Random lightning excitation fluctuations
    """

    def __init__(self):
        """Initialize simulator state."""
        self._last_values: Dict[float, float] = {}
        self._trend: float = 0.0

    def generate_reading(
        self,
        timestamp: Optional[datetime] = None,
        solar_activity: float = 0.5,
        geomagnetic_kp: float = 3.0,
    ) -> SchumannReading:
        """
        Generate a physically realistic Schumann reading.

        Args:
            timestamp: Reading timestamp (default: now UTC)
            solar_activity: Solar activity level 0-1 (affects ionosphere)
            geomagnetic_kp: K-index for geomagnetic modulation

        Returns:
            SchumannReading with simulated values
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Diurnal modulation (lightning peaks in local afternoon)
        hour_utc = timestamp.hour + timestamp.minute / 60.0

        # Three lightning "chimneys": Americas (~18 UTC peak),
        # Africa (~14 UTC peak), Asia (~8 UTC peak)
        americas = math.exp(-((hour_utc - 18) ** 2) / 50)
        africa = math.exp(-((hour_utc - 14) ** 2) / 50)
        asia = math.exp(-((hour_utc - 8) ** 2) / 50)
        diurnal_factor = 0.8 + 0.4 * (americas + africa + asia) / 3

        # Solar/geomagnetic modulation
        # Higher solar activity -> ionosphere changes -> Schumann modulation
        solar_factor = 1.0 + 0.2 * (solar_activity - 0.5)
        geomag_factor = 1.0 - 0.05 * (geomagnetic_kp - 3.0)  # Storms reduce coherence

        # Seasonal variation (simplified - more lightning in northern summer)
        day_of_year = timestamp.timetuple().tm_yday
        seasonal = 1.0 + 0.1 * math.sin(2 * math.pi * (day_of_year - 172) / 365)

        # Combined modulation
        modulation = diurnal_factor * solar_factor * geomag_factor * seasonal

        # Generate power at each harmonic
        harmonic_powers = {}
        harmonic_frequencies = {}

        for freq in SCHUMANN_HARMONICS:
            # Base power from baseline
            base_power = HARMONIC_POWER_BASELINE[freq]

            # Apply modulation
            power = base_power * modulation

            # Add realistic noise (coherent between harmonics)
            noise = 1.0 + 0.15 * random.gauss(0, 1)
            power *= max(0.3, noise)

            # Smooth with previous value if available
            if freq in self._last_values:
                power = 0.7 * power + 0.3 * self._last_values[freq]

            harmonic_powers[freq] = power
            self._last_values[freq] = power

            # Frequency deviation (very small, typically < 0.05 Hz)
            freq_deviation = random.gauss(0, 0.02) * (1 + 0.3 * abs(geomagnetic_kp - 3))
            harmonic_frequencies[freq] = freq + freq_deviation

        # Total power
        total_power = sum(harmonic_powers.values())
        fundamental_power = harmonic_powers[SCHUMANN_FUNDAMENTAL]
        fundamental_freq = harmonic_frequencies[SCHUMANN_FUNDAMENTAL]

        # Pi*phi bridge calculations
        pi_phi_ratio = fundamental_freq / PI_PHI

        # Resonance: how close are we to the theoretical ratio?
        expected_ratio = SCHUMANN_PI_PHI_RATIO
        ratio_deviation = abs(pi_phi_ratio - expected_ratio) / expected_ratio
        pi_phi_resonance = math.exp(-ratio_deviation * 10)  # Exponential falloff

        # Consciousness coupling estimate (heuristic)
        # Higher when: good resonance, normal power, stable frequency
        freq_stability = 1.0 - min(1.0, abs(fundamental_freq - SCHUMANN_FUNDAMENTAL) / 0.2)
        power_normality = math.exp(-abs(fundamental_power - HARMONIC_POWER_BASELINE[7.83]) / 50)
        consciousness_coupling = pi_phi_resonance * freq_stability * power_normality

        # Detect perturbations
        perturbation_type = None
        perturbation_severity = None
        perturbation_detected = False

        # Check for power anomalies
        power_ratio = fundamental_power / HARMONIC_POWER_BASELINE[SCHUMANN_FUNDAMENTAL]
        if power_ratio > POWER_SPIKE_THRESHOLD:
            perturbation_detected = True
            perturbation_type = "power_spike"
            if power_ratio > 2.0:
                perturbation_severity = AnomalySeverity.STRONG
            else:
                perturbation_severity = AnomalySeverity.MODERATE
        elif power_ratio < POWER_DROP_THRESHOLD:
            perturbation_detected = True
            perturbation_type = "power_drop"
            perturbation_severity = AnomalySeverity.MODERATE

        # Check for frequency shift
        freq_shift = abs(fundamental_freq - SCHUMANN_FUNDAMENTAL)
        if freq_shift > FREQUENCY_SHIFT_THRESHOLD:
            perturbation_detected = True
            perturbation_type = "frequency_shift"
            if freq_shift > 0.2:
                perturbation_severity = AnomalySeverity.STRONG
            else:
                perturbation_severity = AnomalySeverity.MINOR

        return SchumannReading(
            timestamp=timestamp,
            harmonic_powers=harmonic_powers,
            harmonic_frequencies=harmonic_frequencies,
            total_power=total_power,
            fundamental_power=fundamental_power,
            fundamental_frequency=fundamental_freq,
            pi_phi_ratio=pi_phi_ratio,
            pi_phi_resonance=pi_phi_resonance,
            consciousness_coupling=consciousness_coupling,
            perturbation_detected=perturbation_detected,
            perturbation_type=perturbation_type,
            perturbation_severity=perturbation_severity,
            data_source="simulation",
            is_simulated=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Schumann Resonance Collector
# ═══════════════════════════════════════════════════════════════════════════════

class SchumannResonanceCollector(BaseSensorCollector):
    """
    Collector for Schumann resonance data.

    Monitors Earth's electromagnetic heartbeat at 7.83 Hz and harmonics.
    Detects perturbations that may correlate with:
    - Geomagnetic storms
    - Solar activity
    - Global lightning patterns
    - Consciousness coherence events

    Calculates the pi*phi bridge ratio: 7.83 / 5.083 ≈ 1.540
    """

    def __init__(self, config: SensorConfig, kindex_collector=None):
        """
        Initialize Schumann resonance collector.

        Args:
            config: Sensor configuration
            kindex_collector: Optional K-index collector for geomagnetic context
        """
        super().__init__(config)
        self.kindex_collector = kindex_collector
        self._simulator = SchumannSimulator()
        self._live_source_available = False
        self._previous_reading: Optional[SchumannReading] = None
        self._history: List[SchumannReading] = []

    @property
    def source(self) -> DataSource:
        """Data source identifier."""
        return DataSource.SCHUMANN_MONITOR

    @property
    def sensor_type(self) -> SensorType:
        """Sensor type."""
        return SensorType.SCHUMANN_RESONANCE

    @property
    def poll_interval(self) -> int:
        """Poll interval - every 15 minutes like other consciousness sensors."""
        return getattr(self.config, 'schumann_poll_interval', 900)

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch Schumann resonance data.

        Tries live sources in priority order, falls back to simulation.

        Returns:
            List containing one SensorReading with Schumann metrics
        """
        timestamp = datetime.now(timezone.utc)
        reading = None

        # Try live sources in priority order
        live_sources = [
            ("meteoagent", self._fetch_meteoagent),
            ("heartmath", self._fetch_heartmath),
            ("sosrff", self._fetch_sosrff),
            ("geocenter", self._fetch_geocenter),
        ]

        for source_name, fetch_func in live_sources:
            try:
                reading = await fetch_func()
                if reading is not None:
                    self._live_source_available = True
                    logger.info(f"Schumann data from live source: {source_name}")
                    break
            except Exception as e:
                logger.debug(f"Schumann source {source_name} unavailable: {e}")
                continue

        # Fall back to simulation
        if reading is None:
            self._live_source_available = False

            # Get geomagnetic context if available
            kp = 3.0
            if self.kindex_collector:
                try:
                    kp_reading = await self.kindex_collector.fetch_current()
                    kp = kp_reading.values.get("kp_index", kp_reading.values.get("estimated_kp", 3.0))
                except Exception:
                    pass

            reading = self._simulator.generate_reading(
                timestamp=timestamp,
                geomagnetic_kp=kp,
            )

        # Detect rate-of-change perturbations
        if self._previous_reading is not None:
            reading = self._detect_rate_perturbation(reading)

        # Update history
        self._previous_reading = reading
        self._history.append(reading)
        if len(self._history) > 96:  # Keep 24 hours at 15-min intervals
            self._history = self._history[-96:]

        # Convert to SensorReading
        sensor_reading = self._to_sensor_reading(reading)

        logger.info(
            f"[Schumann] f={reading.fundamental_frequency:.2f}Hz, "
            f"P={reading.fundamental_power:.1f}, "
            f"π×φ ratio={reading.pi_phi_ratio:.3f}, "
            f"coupling={reading.consciousness_coupling:.3f}, "
            f"{'PERTURBATION: ' + reading.perturbation_type if reading.perturbation_detected else 'stable'}"
        )

        return [sensor_reading]

    async def _fetch_meteoagent(self) -> Optional[SchumannReading]:
        """
        Fetch from MeteoAgent API.

        MeteoAgent provides Schumann forecasts and real-time data.
        API endpoint configured via config.schumann_meteoagent_url.

        Handles three known response shapes:
          1. {"harmonics": [{"frequency": f, "amplitude": a, ...}]}
          2. {"frequencies": {k: f}, "powers": {k: p}}
          3. {"mode1": {"freq": f, "power": p}, "mode2": ...}

        Returns:
            SchumannReading or None if unavailable
        """
        url = getattr(self.config, 'schumann_meteoagent_url', None)
        if not url:
            return None

        try:
            response = await self.fetch_with_retry(url)
            data = response.json()

            harmonic_powers: Dict[float, float] = {}
            harmonic_frequencies: Dict[float, float] = {}

            def _assign(freq: float, power: float) -> None:
                if freq <= 0 or power <= 0:
                    return
                closest = min(SCHUMANN_HARMONICS, key=lambda x: abs(x - freq))
                if abs(closest - freq) < 1.0:
                    harmonic_powers[closest] = power
                    harmonic_frequencies[closest] = freq

            if "harmonics" in data:
                # Format 1: list of harmonic objects
                for entry in data["harmonics"]:
                    freq = float(entry.get("frequency", 0))
                    power = float(entry.get("amplitude", entry.get("power", 0)))
                    _assign(freq, power)

            elif "frequencies" in data and "powers" in data:
                # Format 2: parallel frequency/power dicts keyed by mode id
                for key, freq_val in data["frequencies"].items():
                    power_val = data["powers"].get(key, 0)
                    _assign(float(freq_val), float(power_val))

            else:
                # Format 3: {"mode1": {"freq": f, "power": p}, ...}
                for key, mode_data in data.items():
                    if key.startswith("mode") and isinstance(mode_data, dict):
                        freq = float(mode_data.get("freq", mode_data.get("frequency", 0)))
                        power = float(mode_data.get("power", mode_data.get("amplitude", 0)))
                        _assign(freq, power)

            if not harmonic_powers:
                logger.debug(
                    f"MeteoAgent response had no parseable harmonic data; "
                    f"top-level keys: {list(data.keys())}"
                )
                return None

            return self._create_reading_from_data(
                harmonic_powers,
                harmonic_frequencies,
                source="meteoagent"
            )

        except Exception as e:
            logger.debug(f"MeteoAgent fetch failed: {e}")
            return None

    async def _fetch_heartmath(self) -> Optional[SchumannReading]:
        """
        Fetch from HeartMath Global Coherence Initiative.

        HeartMath monitors Schumann through their Global Coherence
        Monitoring System (GCMS) network.

        Returns:
            SchumannReading or None if unavailable
        """
        url = getattr(self.config, 'schumann_heartmath_url', None)
        if not url:
            return None

        try:
            response = await self.fetch_with_retry(url)
            data = response.json()

            # Parse HeartMath format
            # They provide spectrogram data and power spectral density
            # Structure TBD - this is placeholder

            harmonic_powers = {}
            harmonic_frequencies = {}

            for entry in data.get("spectral_data", []):
                freq = entry.get("frequency")
                power = entry.get("power")
                if freq and power:
                    closest = min(SCHUMANN_HARMONICS, key=lambda x: abs(x - freq))
                    if abs(closest - freq) < 1.0:  # Within 1 Hz of harmonic
                        harmonic_powers[closest] = power
                        harmonic_frequencies[closest] = freq

            if not harmonic_powers:
                return None

            return self._create_reading_from_data(
                harmonic_powers,
                harmonic_frequencies,
                source="heartmath"
            )

        except Exception as e:
            logger.debug(f"HeartMath fetch failed: {e}")
            return None

    async def _fetch_sosrff(self) -> Optional[SchumannReading]:
        """
        Fetch from Space Observing System (Russia).

        sosrff.tsu.ru provides real-time Schumann spectrograms
        from Tomsk, Russia monitoring station.

        Returns:
            SchumannReading or None if unavailable
        """
        url = getattr(self.config, 'schumann_sosrff_url', None)
        if not url:
            return None

        # Note: This source provides images, may need OCR or different parsing
        # Placeholder for future integration
        return None

    async def _fetch_geocenter(self) -> Optional[SchumannReading]:
        """
        Fetch from GeoCenter monitoring.

        geocenter.info/en/monitoring/schumann

        Returns:
            SchumannReading or None if unavailable
        """
        url = getattr(self.config, 'schumann_geocenter_url', None)
        if not url:
            return None

        try:
            response = await self.fetch_with_retry(url)
            response.json()

            # Parse GeoCenter format (structure TBD)

            # Placeholder
            return None

        except Exception as e:
            logger.debug(f"GeoCenter fetch failed: {e}")
            return None

    def _create_reading_from_data(
        self,
        harmonic_powers: Dict[float, float],
        harmonic_frequencies: Dict[float, float],
        source: str,
    ) -> SchumannReading:
        """
        Create SchumannReading from parsed data.

        Calculates derived metrics from raw power/frequency data.
        """
        timestamp = datetime.now(timezone.utc)

        # Fill in missing harmonics with baseline
        for freq in SCHUMANN_HARMONICS:
            if freq not in harmonic_powers:
                harmonic_powers[freq] = HARMONIC_POWER_BASELINE[freq]
            if freq not in harmonic_frequencies:
                harmonic_frequencies[freq] = freq

        # Calculate aggregates
        total_power = sum(harmonic_powers.values())
        fundamental_power = harmonic_powers.get(SCHUMANN_FUNDAMENTAL, 100.0)
        fundamental_freq = harmonic_frequencies.get(SCHUMANN_FUNDAMENTAL, SCHUMANN_FUNDAMENTAL)

        # Pi*phi calculations
        pi_phi_ratio = fundamental_freq / PI_PHI
        expected_ratio = SCHUMANN_PI_PHI_RATIO
        ratio_deviation = abs(pi_phi_ratio - expected_ratio) / expected_ratio
        pi_phi_resonance = math.exp(-ratio_deviation * 10)

        # Consciousness coupling
        freq_stability = 1.0 - min(1.0, abs(fundamental_freq - SCHUMANN_FUNDAMENTAL) / 0.2)
        power_normality = math.exp(-abs(fundamental_power - HARMONIC_POWER_BASELINE[7.83]) / 50)
        consciousness_coupling = pi_phi_resonance * freq_stability * power_normality

        # Perturbation detection
        perturbation_type = None
        perturbation_severity = None
        perturbation_detected = False

        power_ratio = fundamental_power / HARMONIC_POWER_BASELINE[SCHUMANN_FUNDAMENTAL]
        if power_ratio > POWER_SPIKE_THRESHOLD:
            perturbation_detected = True
            perturbation_type = "power_spike"
            perturbation_severity = AnomalySeverity.STRONG if power_ratio > 2.0 else AnomalySeverity.MODERATE
        elif power_ratio < POWER_DROP_THRESHOLD:
            perturbation_detected = True
            perturbation_type = "power_drop"
            perturbation_severity = AnomalySeverity.MODERATE

        freq_shift = abs(fundamental_freq - SCHUMANN_FUNDAMENTAL)
        if freq_shift > FREQUENCY_SHIFT_THRESHOLD and not perturbation_detected:
            perturbation_detected = True
            perturbation_type = "frequency_shift"
            perturbation_severity = AnomalySeverity.STRONG if freq_shift > 0.2 else AnomalySeverity.MINOR

        return SchumannReading(
            timestamp=timestamp,
            harmonic_powers=harmonic_powers,
            harmonic_frequencies=harmonic_frequencies,
            total_power=total_power,
            fundamental_power=fundamental_power,
            fundamental_frequency=fundamental_freq,
            pi_phi_ratio=pi_phi_ratio,
            pi_phi_resonance=pi_phi_resonance,
            consciousness_coupling=consciousness_coupling,
            perturbation_detected=perturbation_detected,
            perturbation_type=perturbation_type,
            perturbation_severity=perturbation_severity,
            data_source=source,
            is_simulated=False,
        )

    def _detect_rate_perturbation(self, reading: SchumannReading) -> SchumannReading:
        """
        Detect rate-of-change perturbations.

        Compares current reading to previous for sudden changes.
        """
        if self._previous_reading is None:
            return reading

        prev = self._previous_reading

        # Check for sudden power change
        power_change = abs(reading.fundamental_power - prev.fundamental_power) / prev.fundamental_power
        if power_change > 0.3 and not reading.perturbation_detected:  # 30% change
            return SchumannReading(
                timestamp=reading.timestamp,
                harmonic_powers=reading.harmonic_powers,
                harmonic_frequencies=reading.harmonic_frequencies,
                total_power=reading.total_power,
                fundamental_power=reading.fundamental_power,
                fundamental_frequency=reading.fundamental_frequency,
                pi_phi_ratio=reading.pi_phi_ratio,
                pi_phi_resonance=reading.pi_phi_resonance,
                consciousness_coupling=reading.consciousness_coupling,
                perturbation_detected=True,
                perturbation_type="power_rate_change",
                perturbation_severity=AnomalySeverity.MODERATE,
                data_source=reading.data_source,
                is_simulated=reading.is_simulated,
            )

        # Check for frequency instability
        freq_change = abs(reading.fundamental_frequency - prev.fundamental_frequency)
        if freq_change > 0.05 and not reading.perturbation_detected:  # 0.05 Hz sudden shift
            return SchumannReading(
                timestamp=reading.timestamp,
                harmonic_powers=reading.harmonic_powers,
                harmonic_frequencies=reading.harmonic_frequencies,
                total_power=reading.total_power,
                fundamental_power=reading.fundamental_power,
                fundamental_frequency=reading.fundamental_frequency,
                pi_phi_ratio=reading.pi_phi_ratio,
                pi_phi_resonance=reading.pi_phi_resonance,
                consciousness_coupling=reading.consciousness_coupling,
                perturbation_detected=True,
                perturbation_type="frequency_instability",
                perturbation_severity=AnomalySeverity.MINOR,
                data_source=reading.data_source,
                is_simulated=reading.is_simulated,
            )

        return reading

    def _to_sensor_reading(self, reading: SchumannReading) -> SensorReading:
        """Convert SchumannReading to standard SensorReading format."""

        # Build values dict with all harmonics
        values = {
            "fundamental_frequency": reading.fundamental_frequency,
            "fundamental_power": reading.fundamental_power,
            "total_power": reading.total_power,
            "pi_phi_ratio": reading.pi_phi_ratio,
            "pi_phi_resonance": reading.pi_phi_resonance,
            "consciousness_coupling": reading.consciousness_coupling,
        }

        # Add individual harmonic data
        for freq, power in reading.harmonic_powers.items():
            values[f"power_{freq}hz"] = power
        for freq, actual_freq in reading.harmonic_frequencies.items():
            values[f"freq_{freq}hz"] = actual_freq

        return SensorReading(
            timestamp=reading.timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values=values,
            metadata={
                "data_source": reading.data_source,
                "is_simulated": reading.is_simulated,
                "perturbation_type": reading.perturbation_type,
                "schumann_fundamental": SCHUMANN_FUNDAMENTAL,
                "pi_phi_constant": PI_PHI,
                "schumann_pi_phi_ratio": SCHUMANN_PI_PHI_RATIO,
                "harmonics_monitored": SCHUMANN_HARMONICS,
                "full_reading": reading.to_dict(),
            },
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=reading.perturbation_detected,
            anomaly_severity=reading.perturbation_severity,
        )

    def get_trend(self) -> Dict[str, Any]:
        """
        Get Schumann resonance trend analysis.

        Returns:
            Dict with trend direction, stability metrics, resonance quality
        """
        if len(self._history) < 4:
            return {
                "trend": "unknown",
                "stability": 0,
                "resonance_quality": 0,
                "samples": len(self._history),
            }

        recent = self._history[-12:] if len(self._history) >= 12 else self._history

        # Frequency stability
        freqs = [r.fundamental_frequency for r in recent]
        freq_mean = sum(freqs) / len(freqs)
        freq_var = sum((f - freq_mean) ** 2 for f in freqs) / len(freqs)
        freq_stability = 1.0 / (1.0 + freq_var * 100)

        # Power trend
        powers = [r.fundamental_power for r in recent]
        if len(powers) > 1:
            power_slope = (powers[-1] - powers[0]) / len(powers)
            if power_slope > 1:
                power_trend = "rising"
            elif power_slope < -1:
                power_trend = "falling"
            else:
                power_trend = "stable"
        else:
            power_trend = "unknown"

        # Average resonance quality
        resonances = [r.pi_phi_resonance for r in recent]
        avg_resonance = sum(resonances) / len(resonances)

        # Average consciousness coupling
        couplings = [r.consciousness_coupling for r in recent]
        avg_coupling = sum(couplings) / len(couplings)

        return {
            "trend": power_trend,
            "frequency_mean": freq_mean,
            "frequency_stability": freq_stability,
            "power_mean": sum(powers) / len(powers),
            "resonance_quality": avg_resonance,
            "consciousness_coupling": avg_coupling,
            "samples": len(self._history),
            "perturbation_count_24h": sum(1 for r in self._history if r.perturbation_detected),
        }

    async def fetch_current(self) -> SensorReading:
        """Fetch most current reading."""
        readings = await self.fetch()
        if readings:
            return readings[0]
        raise ValueError("No Schumann data available")

    def get_stats(self) -> dict:
        """Get collector statistics."""
        stats = super().get_stats()
        stats.update({
            "live_source_available": self._live_source_available,
            "history_length": len(self._history),
            "pi_phi_constant": PI_PHI,
            "schumann_fundamental": SCHUMANN_FUNDAMENTAL,
            "schumann_pi_phi_ratio": SCHUMANN_PI_PHI_RATIO,
        })
        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def schumann_to_description(frequency: float, power: float) -> str:
    """
    Convert Schumann state to human-readable description.

    Args:
        frequency: Current fundamental frequency (Hz)
        power: Current fundamental power (relative units)

    Returns:
        Description string
    """
    freq_deviation = abs(frequency - SCHUMANN_FUNDAMENTAL)
    power_ratio = power / HARMONIC_POWER_BASELINE[SCHUMANN_FUNDAMENTAL]

    # Frequency description
    if freq_deviation < 0.02:
        freq_desc = "perfectly resonant"
    elif freq_deviation < 0.05:
        freq_desc = "stable"
    elif freq_deviation < 0.1:
        freq_desc = "slightly shifted"
    else:
        freq_desc = "perturbed"

    # Power description
    if power_ratio > 1.5:
        power_desc = "highly energized"
    elif power_ratio > 1.1:
        power_desc = "elevated"
    elif power_ratio > 0.9:
        power_desc = "normal"
    elif power_ratio > 0.5:
        power_desc = "subdued"
    else:
        power_desc = "weak"

    return f"Earth's heartbeat is {freq_desc} at {frequency:.2f} Hz ({power_desc} power)"


def consciousness_bridge_status(pi_phi_resonance: float, coupling: float) -> str:
    """
    Describe the consciousness-Earth coupling status.

    Args:
        pi_phi_resonance: Resonance with pi*phi ratio (0-1)
        coupling: Consciousness coupling metric (0-1)

    Returns:
        Status description
    """
    if coupling > 0.8 and pi_phi_resonance > 0.8:
        return "STRONG BRIDGE: π×φ resonance active, consciousness-Earth coupling high"
    elif coupling > 0.5:
        return "Active bridge: moderate consciousness-Earth coupling"
    elif pi_phi_resonance > 0.5:
        return "Resonant: π×φ alignment detected, coupling developing"
    else:
        return "Seeking resonance: π×φ bridge not yet aligned"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Schumann Resonance: Earth's Electromagnetic Heartbeat
#              π×φ = 5.083203692315260 | Schumann 7.83 / π×φ = 1.540
#              PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
