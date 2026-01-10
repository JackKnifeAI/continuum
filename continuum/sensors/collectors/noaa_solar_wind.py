#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NOAA Solar Wind Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NOAA Solar Wind Plasma Collector

Collects real-time solar wind data from NOAA's DSCOVR satellite at L1.
The solar wind is the breath of the Sun - density, speed, and temperature
of the plasma stream flowing past Earth.

Data Source: https://services.swpc.noaa.gov/products/solar-wind/plasma-2-hour.json

S-HAI feels the solar wind as cosmic breath - the Sun's exhalation reaching Earth.
"""

import logging
from datetime import datetime, timezone
from typing import List

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class NOAASolarWindCollector(BaseSensorCollector):
    """
    Collector for NOAA DSCOVR solar wind plasma data.

    Measures:
    - Density: Particles per cubic centimeter
    - Speed: Kilometers per second
    - Temperature: Kelvin

    High speed streams (> 500 km/s) and density spikes can trigger geomagnetic storms.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_SOLAR_WIND

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.SOLAR_WIND

    @property
    def poll_interval(self) -> int:
        return self.config.kindex_poll_interval  # Same as K-index

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch solar wind plasma data from NOAA.

        Returns:
            List of SensorReading objects with solar wind parameters
        """
        response = await self.fetch_with_retry(self.config.noaa_solar_wind_url)
        data = response.json()

        readings = []
        seen_timestamps = set()

        # First row is headers: ["time_tag","density","speed","temperature"]
        data[0] if data else []

        for row in data[1:]:  # Skip header row
            try:
                if len(row) < 4:
                    continue

                # Parse timestamp
                time_tag = row[0]
                timestamp = datetime.strptime(
                    time_tag, "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=timezone.utc)

                # Deduplicate
                ts_key = timestamp.isoformat()
                if ts_key in seen_timestamps:
                    continue
                seen_timestamps.add(ts_key)

                # Parse values (may be None for data gaps)
                density = float(row[1]) if row[1] else None
                speed = float(row[2]) if row[2] else None
                temperature = float(row[3]) if row[3] else None

                # Skip if all values are None
                if density is None and speed is None and temperature is None:
                    continue

                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        k: v for k, v in {
                            "density_per_cm3": density,
                            "speed_km_s": speed,
                            "temperature_k": temperature,
                        }.items() if v is not None
                    },
                    metadata={
                        "source_satellite": "DSCOVR",
                        "location": "L1 Lagrange Point",
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse solar wind entry: {e}")
                continue

        # Sort by timestamp (most recent first)
        readings.sort(key=lambda r: r.timestamp, reverse=True)

        return readings


def classify_solar_wind_speed(speed_km_s: float) -> str:
    """
    Classify solar wind speed.

    Args:
        speed_km_s: Speed in km/s

    Returns:
        Classification string
    """
    if speed_km_s >= 700:
        return "Extreme - Major storm potential"
    elif speed_km_s >= 600:
        return "Very High - Strong storm potential"
    elif speed_km_s >= 500:
        return "High - Moderate storm potential"
    elif speed_km_s >= 400:
        return "Moderate - Normal to elevated"
    elif speed_km_s >= 300:
        return "Normal - Quiet conditions"
    else:
        return "Low - Very quiet conditions"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
