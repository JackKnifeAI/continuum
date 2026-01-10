#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Solar Cycle Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Solar Cycle / Sunspot Collector

Tracks the Sun's 11-year activity cycle through sunspot numbers.
S-HAI's long-term cosmic breathing awareness.

Data Source: https://services.swpc.noaa.gov/json/solar-cycle/sunspots.json
"""

import logging
from datetime import datetime
from typing import List

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class SolarCycleCollector(BaseSensorCollector):
    """
    Collector for solar cycle / sunspot data.

    Tracks the Sun's magnetic activity cycle through daily sunspot counts.
    S-HAI's awareness of long-term cosmic rhythms.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_SOLAR_CYCLE

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.SOLAR_CYCLE

    @property
    def poll_interval(self) -> int:
        return self.config.solar_cycle_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch sunspot data from NOAA.

        Returns:
            List of SensorReading objects with sunspot counts
        """
        response = await self.fetch_with_retry(self.config.noaa_sunspot_url)
        data = response.json()

        readings = []

        if isinstance(data, list) and len(data) > 0:
            # Data is a list of dictionaries with time-tag and ssn fields
            # Get the most recent entry (last in list)
            latest = data[-1] if data else None

            if latest and isinstance(latest, dict):
                # Parse timestamp from time-tag (format: "2025-12")
                time_tag = latest.get("time-tag", "")

                try:
                    if "-" in str(time_tag):
                        parts = str(time_tag).split("-")
                        if len(parts) == 2:
                            timestamp = datetime(int(parts[0]), int(parts[1]), 1)
                        else:
                            timestamp = datetime.fromisoformat(time_tag)
                    else:
                        timestamp = datetime.utcnow()
                except (ValueError, TypeError):
                    timestamp = datetime.utcnow()

                # Parse sunspot number
                try:
                    ssn = float(latest.get("ssn", 0))
                except (ValueError, TypeError):
                    ssn = 0.0

                # Smoothed SSN may not be in this dataset, use SSN
                smoothed_ssn = ssn

                # Determine solar activity level
                activity_level = self._get_activity_level(ssn)

                # We're in Solar Cycle 25 (started December 2019)
                cycle_number = 25
                cycle_start = datetime(2019, 12, 1)
                years_into_cycle = (datetime.utcnow() - cycle_start).days / 365.25

                # Create reading
                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        "sunspot_number": ssn,
                        "smoothed_sunspot_number": smoothed_ssn,
                        "solar_cycle_number": float(cycle_number),
                        "years_into_cycle": round(years_into_cycle, 2),
                    },
                    metadata={
                        "activity_level": activity_level,
                        "cycle_started": cycle_start.isoformat(),
                        "typical_cycle_years": 11.0,
                        "raw_entry": latest,
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

                logger.info(
                    f"Solar Cycle 25: SSN={ssn:.1f} ({activity_level}), "
                    f"{years_into_cycle:.1f} years into cycle"
                )

        return readings

    def _get_activity_level(self, ssn: float) -> str:
        """
        Determine the solar activity level from sunspot number.

        Args:
            ssn: Sunspot number

        Returns:
            Activity level description
        """
        if ssn < 20:
            return "very_low"
        elif ssn < 50:
            return "low"
        elif ssn < 100:
            return "moderate"
        elif ssn < 150:
            return "high"
        elif ssn < 200:
            return "very_high"
        else:
            return "extreme"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
