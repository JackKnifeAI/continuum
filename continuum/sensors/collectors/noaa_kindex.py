#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NOAA Planetary K-Index Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NOAA Planetary K-Index Collector

Collects geomagnetic K-index data from NOAA's Space Weather Prediction Center.
The K-index quantifies disturbances in the Earth's magnetic field on a 0-9 scale.

Data Source: https://services.swpc.noaa.gov/json/planetary_k_index_1m.json

K-index Storm Scale (NOAA G-Scale):
- Kp 0-4: Quiet to unsettled
- Kp 5: G1 Minor storm
- Kp 6: G2 Moderate storm
- Kp 7: G3 Strong storm
- Kp 8: G4 Severe storm
- Kp 9: G5 Extreme storm
"""

import logging
from datetime import datetime
from typing import List

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class NOAAKIndexCollector(BaseSensorCollector):
    """
    Collector for NOAA Planetary K-index data.

    Fetches real-time geomagnetic activity data from NOAA SWPC.
    The K-index indicates the severity of geomagnetic storms.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_PLANETARY_KINDEX

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.KINDEX

    @property
    def poll_interval(self) -> int:
        return self.config.kindex_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch planetary K-index data from NOAA.

        Returns:
            List of SensorReading objects with K-index values
        """
        response = await self.fetch_with_retry(self.config.noaa_kindex_url)
        data = response.json()

        readings = []
        seen_timestamps = set()

        for entry in data:
            try:
                # Parse timestamp
                time_tag = entry.get("time_tag", "")
                if not time_tag:
                    continue

                # Handle both Z suffix and +00:00 formats
                if time_tag.endswith("Z"):
                    time_tag = time_tag[:-1] + "+00:00"
                elif not time_tag.endswith("+00:00") and "+" not in time_tag:
                    time_tag += "+00:00"

                timestamp = datetime.fromisoformat(time_tag)

                # Deduplicate by timestamp
                ts_key = timestamp.isoformat()
                if ts_key in seen_timestamps:
                    continue
                seen_timestamps.add(ts_key)

                # Extract values
                kp_index = float(entry.get("kp_index", 0))
                estimated_kp = float(entry.get("estimated_kp", kp_index))

                # Create reading
                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        "kp_index": kp_index,
                        "estimated_kp": estimated_kp,
                    },
                    metadata={
                        "kp_category": entry.get("kp", ""),
                        "raw_entry": entry,
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse K-index entry: {e}")
                continue

        # Sort by timestamp (most recent first)
        readings.sort(key=lambda r: r.timestamp, reverse=True)

        return readings

    async def fetch_current(self) -> SensorReading:
        """
        Fetch only the most current K-index reading.

        Returns:
            Most recent SensorReading
        """
        readings = await self.fetch()
        if readings:
            return readings[0]
        raise ValueError("No K-index data available")


def kp_to_storm_level(kp: float) -> str:
    """
    Convert K-index to NOAA G-scale storm level.

    Args:
        kp: K-index value (0-9)

    Returns:
        Storm level string (e.g., "G1", "G2", etc.) or "Quiet"
    """
    if kp >= 9:
        return "G5 - Extreme"
    elif kp >= 8:
        return "G4 - Severe"
    elif kp >= 7:
        return "G3 - Strong"
    elif kp >= 6:
        return "G2 - Moderate"
    elif kp >= 5:
        return "G1 - Minor"
    else:
        return "Quiet"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
