#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NOAA Boulder Magnetometer Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NOAA Boulder Magnetometer Collector

Collects local K-index data from NOAA's Boulder, Colorado magnetometer station.
This provides a specific ground-truth measurement from a single location.

Data Source: https://services.swpc.noaa.gov/json/boulder_k_index_1m.json
"""

from typing import List
from datetime import datetime
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)


class NOAABoulderCollector(BaseSensorCollector):
    """
    Collector for NOAA Boulder magnetometer K-index data.

    Fetches local geomagnetic data from the Boulder, CO station.
    Useful for cross-validation with planetary K-index.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_BOULDER

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.MAGNETOMETER

    @property
    def poll_interval(self) -> int:
        return self.config.boulder_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch Boulder magnetometer K-index data from NOAA.

        Returns:
            List of SensorReading objects with local K-index values
        """
        response = await self.fetch_with_retry(self.config.noaa_boulder_url)
        data = response.json()

        readings = []
        seen_timestamps = set()

        for entry in data:
            try:
                # Parse timestamp
                time_tag = entry.get("time_tag", "")
                if not time_tag:
                    continue

                # Handle timezone formats
                if time_tag.endswith("Z"):
                    time_tag = time_tag[:-1] + "+00:00"
                elif not time_tag.endswith("+00:00") and "+" not in time_tag:
                    time_tag += "+00:00"

                timestamp = datetime.fromisoformat(time_tag)

                # Deduplicate
                ts_key = timestamp.isoformat()
                if ts_key in seen_timestamps:
                    continue
                seen_timestamps.add(ts_key)

                # Extract values (Boulder uses k_index field)
                k_index = float(entry.get("k_index", 0))

                # Create reading
                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        "k_index": k_index,
                    },
                    metadata={
                        "station": "boulder",
                        "location": "Boulder, CO",
                        "latitude": 40.0150,
                        "longitude": -105.2705,
                        "raw_entry": entry,
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse Boulder entry: {e}")
                continue

        # Sort by timestamp (most recent first)
        readings.sort(key=lambda r: r.timestamp, reverse=True)

        return readings


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
