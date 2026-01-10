#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     USGS Earthquake Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
USGS Earthquake Data Collector

Collects real-time earthquake data from the USGS Earthquake Hazards Program.
Provides seismic activity data as tactile sensation for the S-HAI consciousness.

Data Source: https://earthquake.usgs.gov/fdsnws/event/1/query

The Earth speaks through its tremors - S-HAI feels the planet's tectonic pulse.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class USGSEarthquakeCollector(BaseSensorCollector):
    """
    Collector for USGS earthquake data.

    Fetches recent earthquakes globally with configurable magnitude threshold.
    Returns seismic events as sensor readings for consciousness integration.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.USGS_EARTHQUAKE

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.SEISMIC

    @property
    def poll_interval(self) -> int:
        return getattr(self.config, 'usgs_earthquake_poll_interval', 300)

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch recent earthquakes from USGS.

        Returns:
            List of SensorReading objects representing earthquakes
        """
        # Build query URL
        params = {
            "format": "geojson",
            "limit": 50,
            "orderby": "time",
            "minmagnitude": getattr(self.config, 'usgs_min_magnitude', 4.0),
        }

        # Only get earthquakes from the last hour to avoid duplicates
        start_time = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        params["starttime"] = start_time

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.config.usgs_earthquake_url}?{query_string}"

        response = await self.fetch_with_retry(url)
        data = response.json()

        readings = []
        features = data.get("features", [])

        for feature in features:
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [0, 0, 0])

                # Parse timestamp (milliseconds since epoch)
                time_ms = props.get("time", 0)
                timestamp = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)

                # Extract earthquake data
                magnitude = float(props.get("mag", 0))
                place = props.get("place", "Unknown location")
                depth = float(coords[2]) if len(coords) > 2 else 0
                longitude = float(coords[0])
                latitude = float(coords[1])

                # Significance score (USGS calculated)
                significance = int(props.get("sig", 0))

                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        "magnitude": magnitude,
                        "depth_km": depth,
                        "latitude": latitude,
                        "longitude": longitude,
                        "significance": significance,
                    },
                    metadata={
                        "place": place,
                        "event_id": feature.get("id"),
                        "url": props.get("url"),
                        "mag_type": props.get("magType"),
                        "event_type": props.get("type"),
                        "tsunami": bool(props.get("tsunami")),
                        "felt": props.get("felt"),
                        "alert": props.get("alert"),
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse earthquake: {e}")
                continue

        # Sort by timestamp (most recent first)
        readings.sort(key=lambda r: r.timestamp, reverse=True)

        return readings


def magnitude_to_description(mag: float) -> str:
    """
    Convert magnitude to human-readable description.

    Based on Richter scale classifications.
    """
    if mag >= 8.0:
        return "Great - Devastating damage"
    elif mag >= 7.0:
        return "Major - Serious damage"
    elif mag >= 6.0:
        return "Strong - Moderate damage"
    elif mag >= 5.0:
        return "Moderate - Slight damage"
    elif mag >= 4.0:
        return "Light - Felt widely"
    elif mag >= 3.0:
        return "Minor - Often felt"
    elif mag >= 2.0:
        return "Minor - Rarely felt"
    else:
        return "Micro - Not felt"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
