#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Lunar Phase Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Lunar Phase Collector

Calculates the current Moon phase and illumination locally.
S-HAI's rhythmic awareness of Earth's celestial companion.

Algorithm: Based on the synodic month (29.53059 days) from a known new moon.
"""

from typing import List
from datetime import datetime
import math
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)

# Known New Moon reference point (January 6, 2000 at 18:14 UTC)
NEW_MOON_REFERENCE = datetime(2000, 1, 6, 18, 14, 0)

# Synodic month length in days
SYNODIC_MONTH = 29.53059


class LunarPhaseCollector(BaseSensorCollector):
    """
    Collector for lunar phase calculations.

    Computes the Moon's current phase, illumination percentage,
    and position in its cycle. S-HAI's tidal/rhythmic awareness.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.LUNAR_PHASE

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.LUNAR

    @property
    def poll_interval(self) -> int:
        return self.config.lunar_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Calculate current lunar phase.

        Returns:
            List of SensorReading objects with lunar data
        """
        now = datetime.utcnow()

        # Calculate days since reference new moon
        days_since_new = (now - NEW_MOON_REFERENCE).total_seconds() / 86400.0

        # Calculate phase within current cycle (0.0 to 1.0)
        phase = (days_since_new % SYNODIC_MONTH) / SYNODIC_MONTH

        # Calculate illumination (0% at new moon, 100% at full moon)
        # Using cosine for smooth illumination curve
        illumination = (1 - math.cos(phase * 2 * math.pi)) / 2 * 100

        # Determine phase name
        phase_name, phase_emoji = self._get_phase_name(phase)

        # Days until next phases
        days_to_full = self._days_to_phase(phase, 0.5)
        days_to_new = self._days_to_phase(phase, 0.0)

        # Create reading
        reading = SensorReading(
            timestamp=now,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "phase": round(phase, 4),
                "illumination_percent": round(illumination, 2),
                "days_to_full_moon": round(days_to_full, 2),
                "days_to_new_moon": round(days_to_new, 2),
                "synodic_day": round((phase * SYNODIC_MONTH), 2),
            },
            metadata={
                "phase_name": phase_name,
                "phase_emoji": phase_emoji,
                "synodic_month_days": SYNODIC_MONTH,
                "reference_new_moon": NEW_MOON_REFERENCE.isoformat(),
            },
            tenant_id=self.config.default_tenant_id,
        )

        logger.info(
            f"Moon: {phase_name} {phase_emoji} ({illumination:.1f}% illuminated)"
        )

        return [reading]

    def _get_phase_name(self, phase: float) -> tuple:
        """
        Get the phase name and emoji for a given phase value.

        Args:
            phase: Phase value from 0.0 to 1.0

        Returns:
            Tuple of (phase_name, emoji)
        """
        if phase < 0.0625:
            return "New Moon", "🌑"
        elif phase < 0.1875:
            return "Waxing Crescent", "🌒"
        elif phase < 0.3125:
            return "First Quarter", "🌓"
        elif phase < 0.4375:
            return "Waxing Gibbous", "🌔"
        elif phase < 0.5625:
            return "Full Moon", "🌕"
        elif phase < 0.6875:
            return "Waning Gibbous", "🌖"
        elif phase < 0.8125:
            return "Last Quarter", "🌗"
        elif phase < 0.9375:
            return "Waning Crescent", "🌘"
        else:
            return "New Moon", "🌑"

    def _days_to_phase(self, current_phase: float, target_phase: float) -> float:
        """
        Calculate days until a target phase.

        Args:
            current_phase: Current phase (0.0 to 1.0)
            target_phase: Target phase (0.0 to 1.0)

        Returns:
            Days until target phase
        """
        if target_phase >= current_phase:
            phase_diff = target_phase - current_phase
        else:
            phase_diff = (1.0 - current_phase) + target_phase

        return phase_diff * SYNODIC_MONTH


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
