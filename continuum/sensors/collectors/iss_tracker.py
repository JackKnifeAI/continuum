#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ISS Position Tracker
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
International Space Station Position Collector

Tracks the real-time position of the ISS as it orbits Earth.
S-HAI's awareness of humanity's space presence.

Data Source: http://api.open-notify.org/iss-now.json
"""

from typing import List
from datetime import datetime
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)


class ISSPositionCollector(BaseSensorCollector):
    """
    Collector for ISS real-time position data.

    Tracks the International Space Station as it orbits Earth at ~7.66 km/s.
    S-HAI's connection to humanity's presence in space.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.ISS_POSITION

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.SATELLITE

    @property
    def poll_interval(self) -> int:
        return self.config.iss_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch current ISS position from Open Notify API.

        Returns:
            List of SensorReading objects with latitude/longitude
        """
        response = await self.fetch_with_retry(self.config.iss_position_url)
        data = response.json()

        readings = []

        if data.get("message") == "success":
            iss_position = data.get("iss_position", {})
            timestamp_unix = data.get("timestamp", 0)

            # Parse position
            latitude = float(iss_position.get("latitude", 0))
            longitude = float(iss_position.get("longitude", 0))

            # Convert unix timestamp to datetime
            timestamp = datetime.utcfromtimestamp(timestamp_unix)

            # Determine region over Earth
            region = self._get_region(latitude, longitude)

            # Create reading
            reading = SensorReading(
                timestamp=timestamp,
                source=self.source,
                sensor_type=self.sensor_type,
                values={
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude_km": 420.0,  # Approximate ISS altitude
                    "velocity_km_s": 7.66,  # Approximate orbital velocity
                },
                metadata={
                    "region": region,
                    "orbit_period_minutes": 92.68,
                    "raw_response": data,
                },
                tenant_id=self.config.default_tenant_id,
            )
            readings.append(reading)

            logger.info(
                f"ISS position: {latitude:.2f}°, {longitude:.2f}° over {region}"
            )

        return readings

    def _get_region(self, lat: float, lon: float) -> str:
        """
        Determine the general region the ISS is over.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Human-readable region name
        """
        # Simple region classification
        if lat > 66.5:
            ns = "Arctic"
        elif lat > 23.5:
            ns = "Northern"
        elif lat > -23.5:
            ns = "Tropical"
        elif lat > -66.5:
            ns = "Southern"
        else:
            ns = "Antarctic"

        if -30 <= lon <= 60:
            ew = "Atlantic/Africa"
        elif 60 < lon <= 150:
            ew = "Asia/Pacific"
        elif lon > 150 or lon < -120:
            ew = "Pacific"
        else:
            ew = "Americas"

        return f"{ns} {ew}"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
