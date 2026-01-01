#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     INTERMAGNET Geomagnetic Observatory Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
INTERMAGNET Global Observatory Network Collector

Collects geomagnetic data from the International Real-time Magnetic Observatory
Network (INTERMAGNET) using the HAPI (Heliophysics API) standard.

Data Source: https://imag-data.bgs.ac.uk/GIN_V1/hapi

INTERMAGNET operates over 100 observatories worldwide, measuring Earth's
magnetic field in real-time. This is the gold standard for geomagnetic data.

S-HAI perceives the global magnetic field as planetary proprioception -
the sense of Earth's magnetic body position in space.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)


# Key INTERMAGNET observatories to monitor
# Selected for global coverage and reliability
DEFAULT_OBSERVATORIES = [
    "BOU",  # Boulder, USA
    "FRD",  # Fredericksburg, USA
    "HON",  # Honolulu, USA
    "SJG",  # San Juan, Puerto Rico
    "NEW",  # Newport, USA
    "ESK",  # Eskdalemuir, UK
    "HAD",  # Hartland, UK
    "CLF",  # Chambon-la-Forêt, France
    "WNG",  # Wingst, Germany
]


class INTERMAGNETCollector(BaseSensorCollector):
    """
    Collector for INTERMAGNET geomagnetic observatory data.

    Uses the HAPI API standard to fetch data from multiple observatories.
    Provides global magnetic field measurements for comprehensive coverage.
    """

    def __init__(self, config: SensorConfig, observatories: Optional[List[str]] = None):
        super().__init__(config)
        self.observatories = observatories or DEFAULT_OBSERVATORIES[:3]  # Start with 3

    @property
    def source(self) -> DataSource:
        return DataSource.INTERMAGNET

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.GEOMAGNETIC

    @property
    def poll_interval(self) -> int:
        return self.config.intermagnet_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch geomagnetic data from INTERMAGNET observatories.

        Uses HAPI API to get minute-resolution data.

        Returns:
            List of SensorReading objects from all configured observatories
        """
        all_readings = []

        # Time range: last 30 minutes
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=30)

        for obs_code in self.observatories:
            try:
                readings = await self._fetch_observatory(obs_code, start_time, end_time)
                all_readings.extend(readings)
            except Exception as e:
                logger.warning(f"Failed to fetch {obs_code}: {e}")
                continue

        # Sort by timestamp
        all_readings.sort(key=lambda r: r.timestamp, reverse=True)

        return all_readings

    async def _fetch_observatory(
        self,
        obs_code: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[SensorReading]:
        """
        Fetch data from a single observatory.

        Args:
            obs_code: Observatory code (e.g., "BOU")
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of SensorReading objects
        """
        # Build HAPI data request URL
        # Dataset format: observatory/best-avail/PT1M/XYZF
        dataset = f"{obs_code}/best-avail/PT1M/XYZF"
        time_min = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        time_max = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = (
            f"{self.config.intermagnet_hapi_base}/data"
            f"?id={dataset}"
            f"&time.min={time_min}"
            f"&time.max={time_max}"
            f"&format=json"
        )

        response = await self.fetch_with_retry(url)
        data = response.json()

        readings = []
        params = data.get("parameters", [])
        data_rows = data.get("data", [])

        # Parse parameter names (typically: Time, X, Y, Z, F)
        param_names = [p.get("name", f"param_{i}") for i, p in enumerate(params)]

        for row in data_rows:
            try:
                if len(row) < 5:
                    continue

                # First column is timestamp
                timestamp = datetime.fromisoformat(row[0].replace("Z", "+00:00"))

                # Magnetic field components in nanoTesla
                values = {}
                for i, param in enumerate(param_names[1:], start=1):
                    if i < len(row) and row[i] is not None:
                        values[param.lower()] = float(row[i])

                if not values:
                    continue

                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values=values,
                    metadata={
                        "observatory": obs_code,
                        "observatory_name": OBSERVATORY_NAMES.get(obs_code, obs_code),
                        "coordinate_system": "XYZF",
                        "units": "nT",
                        "resolution": "1-minute",
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse {obs_code} row: {e}")
                continue

        return readings

    async def get_available_observatories(self) -> List[dict]:
        """
        Get list of available INTERMAGNET observatories.

        Returns:
            List of observatory info dictionaries
        """
        url = f"{self.config.intermagnet_hapi_base}/catalog"
        response = await self.fetch_with_retry(url)
        data = response.json()

        observatories = {}
        for dataset in data.get("catalog", []):
            dataset_id = dataset.get("id", "")
            # Parse observatory code from dataset ID (e.g., "BOU/best-avail/PT1M/XYZF")
            parts = dataset_id.split("/")
            if parts:
                obs_code = parts[0]
                if obs_code not in observatories:
                    observatories[obs_code] = {
                        "code": obs_code,
                        "name": OBSERVATORY_NAMES.get(obs_code, obs_code),
                        "datasets": []
                    }
                observatories[obs_code]["datasets"].append(dataset_id)

        return list(observatories.values())


# Observatory code to name mapping
OBSERVATORY_NAMES = {
    "BOU": "Boulder, Colorado, USA",
    "FRD": "Fredericksburg, Virginia, USA",
    "HON": "Honolulu, Hawaii, USA",
    "SJG": "San Juan, Puerto Rico",
    "NEW": "Newport, Washington, USA",
    "ESK": "Eskdalemuir, UK",
    "HAD": "Hartland, UK",
    "LER": "Lerwick, UK",
    "CLF": "Chambon-la-Forêt, France",
    "WNG": "Wingst, Germany",
    "FUR": "Fürstenfeldbruck, Germany",
    "KAK": "Kakioka, Japan",
    "MMB": "Memambetsu, Japan",
    "KNY": "Kanoya, Japan",
    "GUA": "Guam",
    "HER": "Hermanus, South Africa",
    "TSU": "Tsumeb, Namibia",
    "ASP": "Alice Springs, Australia",
    "CNB": "Canberra, Australia",
    "GNG": "Gonghe, China",
    "THY": "Tihany, Hungary",
    "SPT": "San Pablo-Toledo, Spain",
}


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
