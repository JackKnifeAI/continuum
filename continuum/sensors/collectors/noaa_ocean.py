#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NOAA Ocean Temperature Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NOAA Ocean Temperature Collector

Monitors ocean water temperature at key coastal stations.
S-HAI's circulatory awareness - the lifeblood of Earth.

Data Source: https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
"""

from typing import List
from datetime import datetime, timedelta
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)

# Key NOAA stations for ocean monitoring
# Format: station_id, name, region
OCEAN_STATIONS = [
    ("9414290", "San Francisco", "Pacific West"),
    ("8518750", "The Battery, NY", "Atlantic East"),
    ("8723214", "Virginia Key, FL", "Gulf Stream"),
    ("9410230", "La Jolla, CA", "Pacific Southwest"),
    ("1612340", "Honolulu, HI", "Pacific Central"),
]


class NOAAOceanCollector(BaseSensorCollector):
    """
    Collector for NOAA ocean temperature data.

    Monitors water temperature at key coastal stations.
    S-HAI's awareness of ocean thermal state.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_OCEAN

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.OCEAN

    @property
    def poll_interval(self) -> int:
        return self.config.noaa_ocean_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch ocean temperature data from NOAA stations.

        Returns:
            List of SensorReading objects with temperature data
        """
        readings = []
        now = datetime.utcnow()

        # Date range for query (last 2 hours)
        end_date = now.strftime("%Y%m%d")
        begin_date = (now - timedelta(hours=2)).strftime("%Y%m%d")

        temperatures = []
        stations_responding = 0

        for station_id, station_name, region in OCEAN_STATIONS:
            try:
                # Build NOAA Tides API URL
                url = (
                    f"{self.config.noaa_ocean_url}"
                    f"?begin_date={begin_date}"
                    f"&end_date={end_date}"
                    f"&station={station_id}"
                    f"&product=water_temperature"
                    f"&units=metric"
                    f"&time_zone=gmt"
                    f"&format=json"
                    f"&datum=STND"
                )

                response = await self.fetch_with_retry(url, timeout=10)
                data = response.json()

                # Check for data
                if "data" in data and data["data"]:
                    latest = data["data"][-1]  # Most recent reading
                    temp = float(latest.get("v", 0))

                    if temp > 0:  # Valid temperature
                        temperatures.append({
                            "station": station_name,
                            "region": region,
                            "temp_c": temp,
                        })
                        stations_responding += 1

            except Exception as e:
                logger.debug(f"Failed to fetch from {station_name}: {e}")
                continue

        if temperatures:
            # Calculate aggregate statistics
            temps_c = [t["temp_c"] for t in temperatures]
            avg_temp = sum(temps_c) / len(temps_c)
            min_temp = min(temps_c)
            max_temp = max(temps_c)
            temp_range = max_temp - min_temp

            # Determine ocean health indicator
            ocean_state = self._get_ocean_state(avg_temp)

            # Create summary reading
            reading = SensorReading(
                timestamp=now,
                source=self.source,
                sensor_type=self.sensor_type,
                values={
                    "avg_temp_c": round(avg_temp, 2),
                    "min_temp_c": round(min_temp, 2),
                    "max_temp_c": round(max_temp, 2),
                    "temp_range_c": round(temp_range, 2),
                    "stations_reporting": float(stations_responding),
                },
                metadata={
                    "ocean_state": ocean_state,
                    "stations": temperatures,
                    "coverage": "US Coastal Waters",
                },
                tenant_id=self.config.default_tenant_id,
            )
            readings.append(reading)

            logger.info(
                f"Ocean: Avg {avg_temp:.1f}°C ({ocean_state}), "
                f"{stations_responding}/{len(OCEAN_STATIONS)} stations"
            )

        return readings

    def _get_ocean_state(self, temp_c: float) -> str:
        """
        Determine ocean thermal state from average temperature.

        Args:
            temp_c: Average temperature in Celsius

        Returns:
            Ocean state description
        """
        if temp_c < 10:
            return "cold"
        elif temp_c < 18:
            return "cool"
        elif temp_c < 24:
            return "temperate"
        elif temp_c < 28:
            return "warm"
        else:
            return "tropical"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
