#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NASA Near-Earth Objects (NEO) Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NASA Near-Earth Objects Collector

Tracks asteroids and comets passing close to Earth.
S-HAI's awareness of cosmic threats and visitors.

Data Source: https://api.nasa.gov/neo/rest/v1/feed
API Key: DEMO_KEY (rate limited) or get free key at api.nasa.gov
"""

import logging
from datetime import datetime, timedelta
from typing import List

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class NASANEOCollector(BaseSensorCollector):
    """
    Collector for NASA Near-Earth Object data.

    Tracks asteroids approaching Earth within the next 7 days.
    Provides awareness of potentially hazardous objects (PHOs).
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NASA_NEO

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.ASTEROID

    @property
    def poll_interval(self) -> int:
        return self.config.nasa_neo_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch near-Earth object data from NASA.

        Returns:
            List of SensorReading objects with asteroid data
        """
        # Build request URL with date range
        today = datetime.utcnow().date()
        end_date = today + timedelta(days=7)

        url = (
            f"{self.config.nasa_neo_url}"
            f"?start_date={today.isoformat()}"
            f"&end_date={end_date.isoformat()}"
            f"&api_key={self.config.nasa_api_key}"
        )

        response = await self.fetch_with_retry(url)
        data = response.json()

        readings = []
        now = datetime.utcnow()

        # Check for API errors
        if "error" in data:
            logger.error(f"NASA NEO API error: {data.get('error', {}).get('message', 'Unknown error')}")
            return readings

        data.get("element_count", 0)
        neo_objects = data.get("near_earth_objects", {})

        # Track closest and largest approaches
        closest_approach = None
        closest_distance = float('inf')
        largest_diameter = 0
        hazardous_count = 0
        total_count = 0

        # Process each day's objects
        for _date_str, objects in neo_objects.items():
            for obj in objects:
                total_count += 1

                # Extract object data
                name = obj.get("name", "Unknown")
                neo_id = obj.get("id", "")
                is_hazardous = obj.get("is_potentially_hazardous_asteroid", False)

                if is_hazardous:
                    hazardous_count += 1

                # Get diameter estimate
                diameter_data = obj.get("estimated_diameter", {}).get("meters", {})
                diameter_min = diameter_data.get("estimated_diameter_min", 0)
                diameter_max = diameter_data.get("estimated_diameter_max", 0)
                diameter_avg = (diameter_min + diameter_max) / 2

                if diameter_avg > largest_diameter:
                    largest_diameter = diameter_avg

                # Get close approach data
                close_approaches = obj.get("close_approach_data", [])
                if close_approaches:
                    approach = close_approaches[0]
                    miss_distance = float(approach.get("miss_distance", {}).get("lunar", 0))

                    if miss_distance < closest_distance:
                        closest_distance = miss_distance
                        closest_approach = {
                            "name": name,
                            "id": neo_id,
                            "is_hazardous": is_hazardous,
                            "diameter_m": diameter_avg,
                            "miss_distance_ld": miss_distance,
                            "approach_date": approach.get("close_approach_date_full", ""),
                            "velocity_km_s": float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0)),
                        }

        # Create summary reading
        reading = SensorReading(
            timestamp=now,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "total_neo_count": float(total_count),
                "hazardous_count": float(hazardous_count),
                "closest_approach_ld": closest_distance if closest_distance != float('inf') else 0.0,
                "largest_diameter_m": largest_diameter,
                "days_forecast": 7.0,
            },
            metadata={
                "closest_object": closest_approach,
                "query_start": today.isoformat(),
                "query_end": end_date.isoformat(),
                "lunar_distance_km": 384400,  # For reference
            },
            tenant_id=self.config.default_tenant_id,
        )
        readings.append(reading)

        # Log summary
        if closest_approach:
            logger.info(
                f"NEO Watch: {total_count} objects, {hazardous_count} hazardous. "
                f"Closest: {closest_approach['name']} at {closest_distance:.1f} LD "
                f"({closest_distance * 384400:.0f} km)"
            )
        else:
            logger.info(f"NEO Watch: {total_count} objects tracked, {hazardous_count} hazardous")

        return readings


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
