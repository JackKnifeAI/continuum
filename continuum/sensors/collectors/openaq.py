#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     OpenAQ Air Quality Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
OpenAQ Air Quality Collector

Monitors global air quality through the OpenAQ network.
S-HAI's respiratory awareness of Earth's atmosphere.

Data Source: https://api.openaq.org/v3/
"""

from typing import List
from datetime import datetime
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)

# AQI breakpoints (US EPA standard)
AQI_LEVELS = {
    (0, 50): ("good", "Air quality is satisfactory"),
    (51, 100): ("moderate", "Acceptable; sensitive groups may experience issues"),
    (101, 150): ("unhealthy_sensitive", "Sensitive groups may experience health effects"),
    (151, 200): ("unhealthy", "Everyone may experience health effects"),
    (201, 300): ("very_unhealthy", "Health alert: significant risk"),
    (301, 500): ("hazardous", "Health emergency: everyone affected"),
}


class OpenAQCollector(BaseSensorCollector):
    """
    Collector for OpenAQ air quality data.

    Monitors PM2.5, PM10, O3, NO2, SO2, and CO levels globally.
    S-HAI's awareness of atmospheric health.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.OPENAQ

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.AIR_QUALITY

    @property
    def poll_interval(self) -> int:
        return self.config.openaq_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch air quality data from OpenAQ.

        Returns:
            List of SensorReading objects with air quality metrics
        """
        # Use the v2 API which doesn't require authentication
        # Query for latest PM2.5 measurements globally
        url = "https://api.openaq.org/v2/latest?limit=100&parameter=pm25&order_by=lastUpdated&sort=desc"

        headers = {
            "Accept": "application/json",
        }

        response = await self.fetch_with_retry(url, headers=headers)
        data = response.json()

        readings = []
        now = datetime.utcnow()

        results = data.get("results", [])

        if not results:
            logger.warning("No OpenAQ data returned")
            return readings

        # Aggregate global statistics
        pm25_values = []
        locations_count = 0
        countries = set()

        for location in results[:100]:  # Process locations
            locations_count += 1

            # Get country (v2 format)
            country = location.get("country", "")
            if country:
                countries.add(country)

            # Get measurements (v2 format)
            measurements = location.get("measurements", [])
            for m in measurements:
                param = m.get("parameter", "")
                value = m.get("value", 0)

                if param == "pm25" and value and value > 0:
                    pm25_values.append(value)

        # Calculate averages and max values
        avg_pm25 = sum(pm25_values) / len(pm25_values) if pm25_values else 0
        max_pm25 = max(pm25_values) if pm25_values else 0
        avg_pm10 = 0.0  # Not queried in this endpoint

        # Calculate approximate AQI from PM2.5 (simplified)
        aqi = self._pm25_to_aqi(avg_pm25)
        aqi_level, aqi_description = self._get_aqi_level(aqi)

        # Create summary reading
        reading = SensorReading(
            timestamp=now,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "avg_pm25": round(avg_pm25, 2),
                "max_pm25": round(max_pm25, 2),
                "avg_pm10": round(avg_pm10, 2),
                "aqi_estimate": round(aqi, 1),
                "locations_sampled": float(locations_count),
                "countries_sampled": float(len(countries)),
            },
            metadata={
                "aqi_level": aqi_level,
                "aqi_description": aqi_description,
                "countries": sorted(countries),
                "pm25_readings": len(pm25_values),
            },
            tenant_id=self.config.default_tenant_id,
        )
        readings.append(reading)

        logger.info(
            f"Air Quality: PM2.5 avg={avg_pm25:.1f}, AQI≈{aqi:.0f} ({aqi_level}), "
            f"{locations_count} locations, {len(countries)} countries"
        )

        return readings

    def _pm25_to_aqi(self, pm25: float) -> float:
        """
        Convert PM2.5 concentration to approximate AQI (US EPA).

        Args:
            pm25: PM2.5 concentration in μg/m³

        Returns:
            Approximate AQI value
        """
        # Simplified linear interpolation based on EPA breakpoints
        breakpoints = [
            (0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.4, 301, 500),
        ]

        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= pm25 <= c_high:
                return ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low

        # Above 500.4
        return 500 if pm25 > 500.4 else 0

    def _get_aqi_level(self, aqi: float) -> tuple:
        """
        Get AQI level name and description.

        Args:
            aqi: AQI value

        Returns:
            Tuple of (level_name, description)
        """
        for (low, high), (level, desc) in AQI_LEVELS.items():
            if low <= aqi <= high:
                return level, desc
        return "unknown", "Unable to determine air quality"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
