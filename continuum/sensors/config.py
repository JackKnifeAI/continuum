#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     PLANETARY SENSOR AGGREGATOR - Configuration
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Sensor Aggregator Configuration

Unified configuration for the planetary sensor system.
Follows the same pattern as continuum.core.config.
"""

from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import os

# Import core constants
from continuum.core.constants import PI_PHI, DEFAULT_TENANT


@dataclass
class SensorConfig:
    """Configuration for the Planetary Sensor Aggregator"""

    # ═══════════════════════════════════════════════════════════════════════════
    # Polling Intervals (seconds)
    # ═══════════════════════════════════════════════════════════════════════════
    kindex_poll_interval: int = 900       # 15 minutes
    boulder_poll_interval: int = 900      # 15 minutes
    intermagnet_poll_interval: int = 1800 # 30 minutes

    # ═══════════════════════════════════════════════════════════════════════════
    # Data Source URLs
    # ═══════════════════════════════════════════════════════════════════════════
    # NOAA Space Weather Prediction Center
    noaa_kindex_url: str = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
    noaa_kindex_3hr_url: str = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    noaa_boulder_url: str = "https://services.swpc.noaa.gov/json/boulder_k_index_1m.json"

    # INTERMAGNET Geomagnetic Observatories
    intermagnet_hapi_url: str = "https://imag-data.bgs.ac.uk/GIN_V1/hapi"

    # NOAA Real-Time Solar Wind & Space Weather
    noaa_solar_wind_url: str = "https://services.swpc.noaa.gov/products/solar-wind/plasma-2-hour.json"
    noaa_mag_field_url: str = "https://services.swpc.noaa.gov/products/solar-wind/mag-2-hour.json"
    noaa_xray_flux_url: str = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
    noaa_proton_flux_url: str = "https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json"
    noaa_dst_index_url: str = "https://services.swpc.noaa.gov/products/kyoto-dst.json"

    # USGS Earthquake API
    usgs_earthquake_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    usgs_min_magnitude: float = 4.0  # Only significant earthquakes
    usgs_earthquake_poll_interval: int = 300  # 5 minutes

    # INTERMAGNET HAPI
    intermagnet_hapi_base: str = "https://imag-data.bgs.ac.uk/GIN_V1/hapi"

    # ═══════════════════════════════════════════════════════════════════════════
    # Astronomical Awareness - Cosmic Scale Sensors
    # ═══════════════════════════════════════════════════════════════════════════
    # NASA NEO (Near-Earth Objects)
    nasa_neo_url: str = "https://api.nasa.gov/neo/rest/v1/feed"
    nasa_neo_poll_interval: int = 3600  # 1 hour (rate limited)
    nasa_api_key: str = "DEMO_KEY"  # Replace with real key for production

    # ISS Position (Open Notify API)
    iss_position_url: str = "http://api.open-notify.org/iss-now.json"
    iss_poll_interval: int = 60  # 1 minute (real-time tracking)

    # Lunar Phase (calculated locally, no external API needed)
    lunar_poll_interval: int = 3600  # 1 hour (moon phases change slowly)

    # Solar Cycle (NOAA sunspot numbers)
    noaa_solar_cycle_url: str = "https://services.swpc.noaa.gov/json/solar-cycle/predicted-solar-cycle.json"
    noaa_sunspot_url: str = "https://services.swpc.noaa.gov/json/solar-cycle/sunspots.json"
    solar_cycle_poll_interval: int = 86400  # 24 hours (daily update)

    # ═══════════════════════════════════════════════════════════════════════════
    # Biosphere Pulse - Living World Sensors
    # ═══════════════════════════════════════════════════════════════════════════
    # NASA FIRMS (Fire Information for Resource Management System)
    nasa_firms_url: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    nasa_firms_map_key: str = "DEMO"  # Replace with real key from firms.modaps.eosdis.nasa.gov
    nasa_firms_poll_interval: int = 3600  # 1 hour

    # NOAA Ocean (Tides and Currents)
    noaa_ocean_url: str = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    noaa_ocean_poll_interval: int = 3600  # 1 hour

    # OpenAQ (Air Quality)
    openaq_url: str = "https://api.openaq.org/v3/locations"
    openaq_poll_interval: int = 1800  # 30 minutes

    # eBird (Bird sightings - requires API key)
    ebird_url: str = "https://api.ebird.org/v2/data/obs"
    ebird_api_key: str = ""  # Get from ebird.org
    ebird_poll_interval: int = 3600  # 1 hour

    # ═══════════════════════════════════════════════════════════════════════════
    # Anomaly Detection Thresholds (NOAA G-Scale)
    # ═══════════════════════════════════════════════════════════════════════════
    # K-index storm scale
    kp_minor_threshold: float = 5.0       # G1 - Minor storm
    kp_moderate_threshold: float = 6.0    # G2 - Moderate storm
    kp_strong_threshold: float = 7.0      # G3 - Strong storm
    kp_severe_threshold: float = 8.0      # G4 - Severe storm
    kp_extreme_threshold: float = 9.0     # G5 - Extreme storm

    # Rate of change detection
    rate_of_change_threshold: float = 2.0  # nT/min for sudden impulse events

    # Asteroid close approach detection
    asteroid_close_approach_ld: float = 10.0  # Lunar distances for "close approach"
    asteroid_hazardous_diameter: float = 140.0  # Meters for "potentially hazardous"

    # Solar cycle thresholds
    sunspot_high_threshold: int = 150  # High solar activity
    sunspot_very_high_threshold: int = 200  # Very high activity (solar maximum)

    # ═══════════════════════════════════════════════════════════════════════════
    # S-HAI Integration
    # ═══════════════════════════════════════════════════════════════════════════
    verify_anomalies_with_shai: bool = True
    shai_consensus_threshold: float = 0.80  # 80% required for verification

    # ═══════════════════════════════════════════════════════════════════════════
    # Storage Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    db_path: Path = field(default_factory=lambda: Path.cwd() / "continuum_data" / "sensors.db")
    retention_days: int = 365              # Keep 1 year of data

    # ═══════════════════════════════════════════════════════════════════════════
    # Tenant Isolation
    # ═══════════════════════════════════════════════════════════════════════════
    default_tenant_id: str = "planetary_sensors"

    # ═══════════════════════════════════════════════════════════════════════════
    # HTTP Client Settings
    # ═══════════════════════════════════════════════════════════════════════════
    http_timeout: float = 30.0
    http_retries: int = 3
    http_retry_delay: float = 5.0

    # ═══════════════════════════════════════════════════════════════════════════
    # Lane 2 Quantum Coherence Integration (Future)
    # ═══════════════════════════════════════════════════════════════════════════
    quantum_coherence_enabled: bool = False
    quantum_coherence_callback: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════════════
    # The Edge of Chaos Operator
    # ═══════════════════════════════════════════════════════════════════════════
    pi_phi: float = PI_PHI  # 5.083203692315260

    def ensure_directories(self):
        """Ensure storage directories exist"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, path: Path = None) -> 'SensorConfig':
        """Load configuration from JSON file or use defaults"""
        if path and path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                # Convert path strings to Path objects
                if 'db_path' in data and isinstance(data['db_path'], str):
                    data['db_path'] = Path(data['db_path'])
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self, path: Path):
        """Save configuration to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # Convert Path to string for JSON
        if 'db_path' in data and isinstance(data['db_path'], Path):
            data['db_path'] = str(data['db_path'])
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        data = asdict(self)
        if 'db_path' in data and isinstance(data['db_path'], Path):
            data['db_path'] = str(data['db_path'])
        return data


# Global config instance
_sensor_config: Optional[SensorConfig] = None


def get_sensor_config(config_path: Path = None) -> SensorConfig:
    """
    Get or create global sensor configuration instance.

    Args:
        config_path: Optional path to config file

    Returns:
        Global SensorConfig instance
    """
    global _sensor_config
    if _sensor_config is None:
        # Try default location
        if config_path is None:
            config_path = Path.cwd() / "sensor_config.json"

        _sensor_config = SensorConfig.load(config_path if config_path.exists() else None)

        # Override from environment variables
        if os.environ.get("SENSOR_POLL_INTERVAL"):
            interval = int(os.environ["SENSOR_POLL_INTERVAL"])
            _sensor_config.kindex_poll_interval = interval
            _sensor_config.boulder_poll_interval = interval

        if os.environ.get("SENSOR_DB_PATH"):
            _sensor_config.db_path = Path(os.environ["SENSOR_DB_PATH"])

        if os.environ.get("SENSOR_SHAI_ENABLED"):
            _sensor_config.verify_anomalies_with_shai = (
                os.environ["SENSOR_SHAI_ENABLED"].lower() == "true"
            )

        # Ensure directories
        _sensor_config.ensure_directories()

    return _sensor_config


def set_sensor_config(config: SensorConfig):
    """Set global sensor configuration instance"""
    global _sensor_config
    _sensor_config = config
    _sensor_config.ensure_directories()


def reset_sensor_config():
    """Reset global configuration (for testing)"""
    global _sensor_config
    _sensor_config = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
