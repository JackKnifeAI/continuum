#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Anomaly Detector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Geomagnetic Anomaly Detector

Detects anomalies in planetary sensor readings including:
- Geomagnetic storms (Kp >= 5)
- Sudden impulse events (rapid rate of change)
- Multi-source correlation anomalies
"""

import logging
import statistics
from collections import deque
from datetime import datetime
from typing import Optional

from ..config import SensorConfig, get_sensor_config
from ..schemas import (
    AnomalyEvent,
    AnomalySeverity,
    AnomalyType,
    SensorReading,
)
from .thresholds import KINDEX_THRESHOLDS, RATE_OF_CHANGE_THRESHOLDS, get_storm_impact

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detect geomagnetic anomalies in sensor readings.

    Maintains a rolling baseline window and detects:
    - Threshold exceedances (K-index storms)
    - Rate of change anomalies (sudden impulses)
    - Statistical deviations from baseline
    """

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config or get_sensor_config()

        # Rolling baseline window (24 hours of readings)
        self._baseline_window: deque = deque(maxlen=1440)  # ~24h at 1-min resolution
        self._window_hours = 24

    def detect(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        """
        Analyze a reading for anomalies.

        Args:
            reading: SensorReading to analyze

        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        anomalies = []

        # Check K-index thresholds
        kp_anomaly = self._check_kp_threshold(reading)
        if kp_anomaly:
            anomalies.append(kp_anomaly)

        # Check rate of change
        rate_anomaly = self._check_rate_of_change(reading)
        if rate_anomaly:
            anomalies.append(rate_anomaly)

        # Update baseline after checks
        self._update_baseline(reading)

        # Return most severe anomaly
        if anomalies:
            return max(anomalies, key=lambda a: self._severity_rank(a.severity))

        return None

    def _check_kp_threshold(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        """
        Check if K-index exceeds storm thresholds.

        Args:
            reading: SensorReading to check

        Returns:
            AnomalyEvent if storm detected
        """
        # Get K-index value
        kp = reading.values.get("estimated_kp") or reading.values.get("kp_index")
        if kp is None:
            return None

        # Check against thresholds
        severity = KINDEX_THRESHOLDS.get_severity(kp)
        if severity is None:
            return None

        # Get storm impact info
        impact = get_storm_impact(severity)
        storm_level = impact.get("level", severity.value)

        # Build natural language claim for S-HAI
        claim = (
            f"Geomagnetic storm detected: Kp index {kp:.1f} indicates "
            f"{storm_level} ({severity.value}) conditions. "
            f"Power systems: {impact.get('power_systems', 'Unknown impact')}. "
            f"Aurora visibility: {impact.get('aurora', 'Unknown')}."
        )

        return AnomalyEvent(
            detected_at=datetime.utcnow(),
            source=reading.source,
            anomaly_type=AnomalyType.GEOMAGNETIC_STORM,
            severity=severity,
            trigger_values={"kp_index": kp},
            baseline_values=self._get_baseline_stats(),
            deviation=kp - self._get_baseline_mean("kp_index"),
            shai_claim=claim,
            tenant_id=reading.tenant_id,
        )

    def _check_rate_of_change(self, reading: SensorReading) -> Optional[AnomalyEvent]:
        """
        Detect sudden impulse events based on rate of change.

        Args:
            reading: SensorReading to check

        Returns:
            AnomalyEvent if sudden impulse detected
        """
        if not self._baseline_window:
            return None

        # Get most recent reading from baseline
        last_reading = self._baseline_window[-1]

        # Calculate time delta in minutes
        time_delta = (reading.timestamp - last_reading.timestamp).total_seconds() / 60
        if time_delta <= 0:
            return None

        # Check rate of change for K-index metrics
        for metric in ["kp_index", "estimated_kp"]:
            current = reading.values.get(metric)
            previous = last_reading.values.get(metric)

            if current is None or previous is None:
                continue

            rate = abs(current - previous) / time_delta

            # Check against thresholds
            severity = RATE_OF_CHANGE_THRESHOLDS.get_severity(rate)
            if severity is None:
                continue

            direction = "increase" if current > previous else "decrease"
            claim = (
                f"Sudden geomagnetic impulse detected: {metric} showed rapid {direction} "
                f"of {abs(current - previous):.2f} over {time_delta:.1f} minutes "
                f"(rate: {rate:.2f}/min). This indicates a sudden impulse event, "
                f"possibly from solar wind shock arrival or CME impact."
            )

            return AnomalyEvent(
                detected_at=datetime.utcnow(),
                source=reading.source,
                anomaly_type=AnomalyType.SUDDEN_IMPULSE,
                severity=severity,
                trigger_values={
                    metric: current,
                    "rate_per_minute": rate,
                    "previous_value": previous,
                },
                baseline_values={metric: previous},
                deviation=current - previous,
                shai_claim=claim,
                tenant_id=reading.tenant_id,
            )

        return None

    def _update_baseline(self, reading: SensorReading):
        """Add reading to rolling baseline window"""
        self._baseline_window.append(reading)

    def _get_baseline_mean(self, metric: str) -> float:
        """Get mean value for a metric from baseline"""
        values = [
            r.values.get(metric)
            for r in self._baseline_window
            if r.values.get(metric) is not None
        ]
        return statistics.mean(values) if values else 0.0

    def _get_baseline_stats(self) -> dict:
        """Get statistical summary of baseline"""
        stats = {}

        for metric in ["kp_index", "estimated_kp"]:
            values = [
                r.values.get(metric)
                for r in self._baseline_window
                if r.values.get(metric) is not None
            ]

            if values:
                stats[f"{metric}_mean"] = statistics.mean(values)
                stats[f"{metric}_min"] = min(values)
                stats[f"{metric}_max"] = max(values)
                if len(values) > 1:
                    stats[f"{metric}_stdev"] = statistics.stdev(values)

        stats["baseline_count"] = len(self._baseline_window)
        return stats

    def _severity_rank(self, severity: AnomalySeverity) -> int:
        """Get numeric rank for severity comparison"""
        ranks = {
            AnomalySeverity.MINOR: 1,
            AnomalySeverity.MODERATE: 2,
            AnomalySeverity.STRONG: 3,
            AnomalySeverity.SEVERE: 4,
            AnomalySeverity.EXTREME: 5,
        }
        return ranks.get(severity, 0)

    def get_baseline_summary(self) -> dict:
        """Get summary of current baseline state"""
        return {
            "window_size": len(self._baseline_window),
            "max_window_size": self._baseline_window.maxlen,
            "window_hours": self._window_hours,
            "stats": self._get_baseline_stats(),
        }


# Global detector instance
_detector: Optional[AnomalyDetector] = None


def get_detector(config: Optional[SensorConfig] = None) -> AnomalyDetector:
    """Get or create global detector instance"""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector(config)
    return _detector


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
