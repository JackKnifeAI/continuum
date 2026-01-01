#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Anomaly Detection Thresholds
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Anomaly Detection Thresholds

Configurable threshold definitions for different types of anomalies.
Based on NOAA Space Weather Scales.
"""

from dataclasses import dataclass
from typing import Optional

from ..schemas import AnomalySeverity


@dataclass
class AnomalyThreshold:
    """
    Threshold configuration for a specific metric.

    Defines severity levels based on metric values.
    """
    metric: str
    minor: float      # G1 threshold
    moderate: float   # G2 threshold
    strong: float     # G3 threshold
    severe: float     # G4 threshold
    extreme: float    # G5 threshold

    def get_severity(self, value: float) -> Optional[AnomalySeverity]:
        """
        Determine severity level for a value.

        Args:
            value: Metric value to check

        Returns:
            AnomalySeverity if threshold exceeded, None otherwise
        """
        if value >= self.extreme:
            return AnomalySeverity.EXTREME
        elif value >= self.severe:
            return AnomalySeverity.SEVERE
        elif value >= self.strong:
            return AnomalySeverity.STRONG
        elif value >= self.moderate:
            return AnomalySeverity.MODERATE
        elif value >= self.minor:
            return AnomalySeverity.MINOR
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# NOAA Geomagnetic Storm Scale (G-Scale)
# https://www.swpc.noaa.gov/noaa-scales-explanation
# ═══════════════════════════════════════════════════════════════════════════════

KINDEX_THRESHOLDS = AnomalyThreshold(
    metric="kp_index",
    minor=5.0,      # G1 - Minor storm
    moderate=6.0,   # G2 - Moderate storm
    strong=7.0,     # G3 - Strong storm
    severe=8.0,     # G4 - Severe storm
    extreme=9.0,    # G5 - Extreme storm
)

# Rate of change thresholds (nT/minute)
RATE_OF_CHANGE_THRESHOLDS = AnomalyThreshold(
    metric="rate_of_change",
    minor=1.0,      # Noticeable change
    moderate=2.0,   # Significant change
    strong=3.0,     # Rapid change
    severe=4.0,     # Very rapid change
    extreme=5.0,    # Extreme sudden impulse
)


# ═══════════════════════════════════════════════════════════════════════════════
# Storm Impact Descriptions
# ═══════════════════════════════════════════════════════════════════════════════

STORM_IMPACTS = {
    AnomalySeverity.MINOR: {
        "level": "G1",
        "power_systems": "Weak power grid fluctuations",
        "spacecraft": "Minor impact on satellite operations",
        "navigation": "Migratory animals may be affected",
        "radio": "Weak HF radio degradation at high latitudes",
        "aurora": "Aurora visible at high latitudes (60+ degrees)",
    },
    AnomalySeverity.MODERATE: {
        "level": "G2",
        "power_systems": "High-latitude power systems may experience voltage alarms",
        "spacecraft": "Corrective actions may be needed for orientation",
        "navigation": "Intermittent GPS issues at high latitudes",
        "radio": "HF radio degradation at high latitudes",
        "aurora": "Aurora visible at 55+ degrees latitude",
    },
    AnomalySeverity.STRONG: {
        "level": "G3",
        "power_systems": "Voltage corrections may be required, false alarms on protection devices",
        "spacecraft": "Surface charging may occur, increased drag on LEO satellites",
        "navigation": "Intermittent GPS problems",
        "radio": "HF radio intermittent",
        "aurora": "Aurora visible at 50+ degrees latitude",
    },
    AnomalySeverity.SEVERE: {
        "level": "G4",
        "power_systems": "Possible widespread voltage control problems",
        "spacecraft": "Surface charging and tracking problems",
        "navigation": "GPS degraded for hours",
        "radio": "HF radio propagation sporadic",
        "aurora": "Aurora visible at 45+ degrees latitude",
    },
    AnomalySeverity.EXTREME: {
        "level": "G5",
        "power_systems": "Widespread voltage control problems, possible grid collapse",
        "spacecraft": "Extensive surface charging, orientation problems",
        "navigation": "GPS may be unavailable for days",
        "radio": "HF radio blackout for 1-2 days",
        "aurora": "Aurora visible at 40+ degrees latitude (visible from Florida!)",
    },
}


def get_storm_impact(severity: AnomalySeverity) -> dict:
    """
    Get detailed impact description for a storm severity level.

    Args:
        severity: AnomalySeverity level

    Returns:
        Dictionary of impact descriptions
    """
    return STORM_IMPACTS.get(severity, {})


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
