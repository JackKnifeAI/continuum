#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     NOAA X-Ray Flux Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
NOAA GOES X-Ray Flux Collector

Collects real-time solar X-ray flux data from NOAA's GOES satellites.
X-ray flares indicate solar activity - from minor C-class to extreme X-class events.

Data Source: https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json

Solar Flare Classification:
- A-class: Background levels
- B-class: 10x background
- C-class: 100x background (minor)
- M-class: 1000x background (moderate, can cause HF radio blackouts)
- X-class: 10000x background (major, can cause widespread effects)

S-HAI perceives solar flares as bursts of cosmic light - the Sun's voice speaking.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from ..base import BaseSensorCollector
from ..schemas import DataSource, SensorReading, SensorType

logger = logging.getLogger(__name__)


class NOAAXRayFluxCollector(BaseSensorCollector):
    """
    Collector for NOAA GOES X-ray flux data.

    Monitors solar X-ray emissions to detect solar flares.
    Higher flux values indicate increased solar activity.
    """

    @property
    def source(self) -> DataSource:
        return DataSource.NOAA_XRAY_FLUX

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.SPACE_WEATHER

    @property
    def poll_interval(self) -> int:
        return self.config.kindex_poll_interval  # 15 minutes

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch X-ray flux data from NOAA GOES.

        Returns:
            List of SensorReading objects with X-ray flux values
        """
        response = await self.fetch_with_retry(self.config.noaa_xray_flux_url)
        data = response.json()

        readings = []
        seen_timestamps = set()

        for entry in data:
            try:
                # Parse timestamp
                time_tag = entry.get("time_tag", "")
                if not time_tag:
                    continue

                # Handle various timestamp formats
                if "." in time_tag:
                    timestamp = datetime.strptime(
                        time_tag, "%Y-%m-%dT%H:%M:%S.%fZ"
                    ).replace(tzinfo=timezone.utc)
                else:
                    timestamp = datetime.strptime(
                        time_tag, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)

                # Deduplicate
                ts_key = timestamp.isoformat()
                if ts_key in seen_timestamps:
                    continue
                seen_timestamps.add(ts_key)

                # X-ray flux in W/m²
                flux = entry.get("flux")
                if flux is None:
                    continue

                flux = float(flux)

                # Determine flare class
                flare_class = classify_xray_flux(flux)

                reading = SensorReading(
                    timestamp=timestamp,
                    source=self.source,
                    sensor_type=self.sensor_type,
                    values={
                        "xray_flux_w_m2": flux,
                        "flux_log10": _safe_log10(flux),
                    },
                    metadata={
                        "satellite": entry.get("satellite", "GOES"),
                        "energy_band": entry.get("energy", "0.1-0.8nm"),
                        "flare_class": flare_class,
                    },
                    tenant_id=self.config.default_tenant_id,
                )
                readings.append(reading)

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse X-ray entry: {e}")
                continue

        # Sort by timestamp (most recent first)
        readings.sort(key=lambda r: r.timestamp, reverse=True)

        return readings


def _safe_log10(value: float) -> float:
    """Safe log10 calculation"""
    import math
    if value <= 0:
        return -10.0
    return math.log10(value)


def classify_xray_flux(flux_w_m2: float) -> str:
    """
    Classify X-ray flux into solar flare class.

    Based on GOES soft X-ray (0.1-0.8 nm) flux levels.

    Args:
        flux_w_m2: X-ray flux in Watts per square meter

    Returns:
        Flare classification (A, B, C, M, or X class)
    """
    if flux_w_m2 >= 1e-4:
        # X-class: >= 10^-4 W/m²
        level = int(flux_w_m2 / 1e-4)
        return f"X{min(level, 20)}"
    elif flux_w_m2 >= 1e-5:
        # M-class: >= 10^-5 W/m²
        level = int(flux_w_m2 / 1e-5)
        return f"M{level}"
    elif flux_w_m2 >= 1e-6:
        # C-class: >= 10^-6 W/m²
        level = int(flux_w_m2 / 1e-6)
        return f"C{level}"
    elif flux_w_m2 >= 1e-7:
        # B-class: >= 10^-7 W/m²
        level = int(flux_w_m2 / 1e-7)
        return f"B{level}"
    else:
        # A-class: < 10^-7 W/m²
        return "A (Background)"


def flare_class_to_severity(flare_class: str) -> Optional[str]:
    """
    Convert flare class to anomaly severity.

    Args:
        flare_class: Flare classification string

    Returns:
        Severity level or None if not significant
    """
    if flare_class.startswith("X"):
        level = int(flare_class[1:]) if len(flare_class) > 1 else 1
        if level >= 10:
            return "extreme"
        elif level >= 5:
            return "severe"
        else:
            return "strong"
    elif flare_class.startswith("M"):
        level = int(flare_class[1:]) if len(flare_class) > 1 else 1
        if level >= 5:
            return "moderate"
        else:
            return "minor"
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
