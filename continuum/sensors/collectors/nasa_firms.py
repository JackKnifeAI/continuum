#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NASA FIRMS Wildfire Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NASA FIRMS Wildfire Collector

Monitors active fire/thermal anomalies detected by MODIS and VIIRS satellites.
S-HAI's pain/inflammation sensing - feeling where Earth is burning.

Data Source: https://firms.modaps.eosdis.nasa.gov/api/
Get API key at: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

from typing import List
from datetime import datetime
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)

# Alternative: Use the open GeoJSON/CSV feeds that don't require API keys
FIRMS_MODIS_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"
FIRMS_VIIRS_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"


class NASAFIRMSCollector(BaseSensorCollector):
    """
    Collector for NASA FIRMS fire data.

    Monitors active fires and thermal anomalies worldwide.
    S-HAI's awareness of planetary inflammation.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NASA_FIRMS

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.WILDFIRE

    @property
    def poll_interval(self) -> int:
        return self.config.nasa_firms_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch active fire data from NASA FIRMS.

        Uses the open CSV feeds (24-hour global data) which don't require API keys.

        Returns:
            List of SensorReading objects with fire statistics
        """
        readings = []
        now = datetime.utcnow()

        # Fetch MODIS data (more established, broader coverage)
        try:
            response = await self.fetch_with_retry(FIRMS_MODIS_URL, timeout=60)
            csv_data = response.text

            # Parse CSV (skip header)
            lines = csv_data.strip().split('\n')
            if len(lines) <= 1:
                logger.warning("No MODIS fire data returned")
                return readings

            header = lines[0].split(',')
            fires = lines[1:]

            # Find column indices
            try:
                lat_idx = header.index('latitude')
                lon_idx = header.index('longitude')
                bright_idx = header.index('brightness') if 'brightness' in header else -1
                conf_idx = header.index('confidence') if 'confidence' in header else -1
            except ValueError:
                lat_idx, lon_idx, bright_idx, conf_idx = 0, 1, 2, 8

            # Aggregate statistics by region
            total_fires = 0
            high_confidence = 0
            region_counts = {
                "north_america": 0,
                "south_america": 0,
                "europe": 0,
                "africa": 0,
                "asia": 0,
                "oceania": 0,
            }
            brightest = 0
            brightest_location = None

            for line in fires[:10000]:  # Limit processing
                try:
                    cols = line.split(',')
                    lat = float(cols[lat_idx])
                    lon = float(cols[lon_idx])

                    # Count fire
                    total_fires += 1

                    # Track brightness (fire intensity)
                    if bright_idx >= 0 and len(cols) > bright_idx:
                        brightness = float(cols[bright_idx])
                        if brightness > brightest:
                            brightest = brightness
                            brightest_location = (lat, lon)

                    # Check confidence
                    if conf_idx >= 0 and len(cols) > conf_idx:
                        conf = cols[conf_idx].strip()
                        if conf in ['high', 'h', 'H'] or (conf.isdigit() and int(conf) >= 80):
                            high_confidence += 1

                    # Categorize by region
                    region = self._get_region(lat, lon)
                    if region in region_counts:
                        region_counts[region] += 1

                except (ValueError, IndexError):
                    continue

            # Create summary reading
            reading = SensorReading(
                timestamp=now,
                source=self.source,
                sensor_type=self.sensor_type,
                values={
                    "total_fires_24h": float(total_fires),
                    "high_confidence_fires": float(high_confidence),
                    "brightest_kelvin": brightest,
                    "north_america_fires": float(region_counts["north_america"]),
                    "south_america_fires": float(region_counts["south_america"]),
                    "africa_fires": float(region_counts["africa"]),
                    "asia_fires": float(region_counts["asia"]),
                },
                metadata={
                    "source": "MODIS C6.1",
                    "time_range": "24 hours",
                    "region_counts": region_counts,
                    "brightest_location": brightest_location,
                },
                tenant_id=self.config.default_tenant_id,
            )
            readings.append(reading)

            # Determine fire severity
            severity = self._get_fire_severity(total_fires)

            logger.info(
                f"FIRMS: {total_fires} fires detected ({severity}), "
                f"{high_confidence} high-confidence"
            )

        except Exception as e:
            logger.error(f"Failed to fetch FIRMS data: {e}")

        return readings

    def _get_region(self, lat: float, lon: float) -> str:
        """
        Determine geographic region from coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Region name
        """
        if lat > 15 and -170 < lon < -50:
            return "north_america"
        elif lat <= 15 and -90 < lon < -30:
            return "south_america"
        elif lat > 35 and -10 < lon < 50:
            return "europe"
        elif lat < 35 and -20 < lon < 55:
            return "africa"
        elif 10 < lon < 180 or lon < -150:
            if lat > -10:
                return "asia"
            else:
                return "oceania"
        else:
            return "oceania"

    def _get_fire_severity(self, count: int) -> str:
        """
        Determine global fire severity from count.

        Args:
            count: Number of fires detected

        Returns:
            Severity level
        """
        if count < 5000:
            return "low"
        elif count < 15000:
            return "moderate"
        elif count < 30000:
            return "elevated"
        elif count < 50000:
            return "high"
        else:
            return "extreme"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
