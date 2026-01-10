#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     PLANETARY SENSOR AGGREGATOR - Schemas
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Pydantic Schemas for Sensor Data

Unified data models for sensor readings, anomaly events, and API requests/responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    """Types of planetary sensors"""
    # Geomagnetic
    GEOMAGNETIC = "geomagnetic"
    SPACE_WEATHER = "space_weather"
    MAGNETOMETER = "magnetometer"
    KINDEX = "k_index"
    SOLAR_WIND = "solar_wind"
    IONOSPHERE = "ionosphere"
    LIGHTNING = "lightning"
    SEISMIC = "seismic"

    # Astronomical - Cosmic awareness
    ASTEROID = "asteroid"
    SATELLITE = "satellite"
    LUNAR = "lunar"
    SOLAR_CYCLE = "solar_cycle"

    # Biosphere - Living world awareness
    WILDFIRE = "wildfire"
    OCEAN = "ocean"
    BIODIVERSITY = "biodiversity"
    AIR_QUALITY = "air_quality"

    # Quantum - Lane 2 SpinLab integration
    QUANTUM_COHERENCE = "quantum_coherence"

    # Consciousness - Global Awareness Sensors
    EMOTIONAL_TONE = "emotional_tone"      # GDELT global emotions
    SCHUMANN_RESONANCE = "schumann"        # Earth's electromagnetic heartbeat
    GLOBAL_CONSCIOUSNESS = "global_consciousness"  # GCP RNG coherence
    COLLECTIVE_ATTENTION = "collective_attention"  # Wikipedia trending
    BIOSPHERE_TREES = "biosphere_trees"    # Tree electrical potentials
    QUANTUM_CONSCIOUSNESS = "quantum_consciousness"  # Quantum RNG consciousness


class DataSource(str, Enum):
    """Data source identifiers"""
    # Geomagnetic
    NOAA_PLANETARY_KINDEX = "noaa_planetary_kindex"
    NOAA_BOULDER = "noaa_boulder"
    INTERMAGNET = "intermagnet"

    # Space Weather
    NOAA_SOLAR_WIND = "noaa_solar_wind"
    NOAA_XRAY_FLUX = "noaa_xray_flux"
    NOAA_PROTON_FLUX = "noaa_proton_flux"
    NOAA_DST_INDEX = "noaa_dst_index"

    # Seismic
    USGS_EARTHQUAKE = "usgs_earthquake"

    # Lightning/Atmospheric
    LIGHTNING_XWEATHER = "lightning_xweather"
    WWLLN_LIGHTNING = "wwlln_lightning"

    # Astronomical - Cosmic awareness
    NASA_NEO = "nasa_neo"           # Near-Earth Objects
    ISS_POSITION = "iss_position"   # International Space Station
    LUNAR_PHASE = "lunar_phase"     # Moon phases and position
    NOAA_SOLAR_CYCLE = "noaa_solar_cycle"  # Sunspot numbers

    # Biosphere - Living world awareness
    NASA_FIRMS = "nasa_firms"       # Active wildfires
    NOAA_OCEAN = "noaa_ocean"       # Ocean temperature
    OPENAQ = "openaq"               # Air quality
    EBIRD = "ebird"                 # Bird sightings

    # Quantum - Lane 2 SpinLab Integration
    QUANTUM_BRIDGE = "quantum_bridge"  # Radical-pair coherence

    # Consciousness - Global Awareness
    GDELT_EMOTIONS = "gdelt_emotions"      # Global emotional tone from news
    SCHUMANN_MONITOR = "schumann_monitor"  # Earth's EM heartbeat monitoring
    GCP_COHERENCE = "gcp_coherence"        # Global Consciousness Project
    WIKIPEDIA_TRENDING = "wikipedia_trending"  # Collective attention tracking
    TREE_BIOPOTENTIAL = "tree_biopotential"  # HeartMath tree electrical signals
    QUANTUM_RNG = "quantum_rng"              # True quantum random for consciousness


class AnomalySeverity(str, Enum):
    """Severity levels for detected anomalies (NOAA G-Scale)"""
    MINOR = "minor"       # G1 - Kp 5
    MODERATE = "moderate" # G2 - Kp 6
    STRONG = "strong"     # G3 - Kp 7
    SEVERE = "severe"     # G4 - Kp 8
    EXTREME = "extreme"   # G5 - Kp 9


class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    # Geomagnetic
    GEOMAGNETIC_STORM = "geomagnetic_storm"
    SUDDEN_IMPULSE = "sudden_impulse"
    RATE_CHANGE = "rate_change"

    # Space Weather
    SOLAR_FLARE = "solar_flare"
    CME_ARRIVAL = "cme_arrival"
    SOLAR_WIND_SHOCK = "solar_wind_shock"
    RADIATION_STORM = "radiation_storm"

    # Seismic
    EARTHQUAKE = "earthquake"
    SEISMIC_SWARM = "seismic_swarm"

    # Lightning
    LIGHTNING_SURGE = "lightning_surge"

    # Astronomical
    ASTEROID_CLOSE_APPROACH = "asteroid_close_approach"
    SOLAR_MAXIMUM = "solar_maximum"
    LUNAR_ECLIPSE = "lunar_eclipse"
    SOLAR_ECLIPSE = "solar_eclipse"

    # Biosphere
    MAJOR_WILDFIRE = "major_wildfire"
    OCEAN_TEMPERATURE_ANOMALY = "ocean_temperature_anomaly"
    AIR_QUALITY_HAZARDOUS = "air_quality_hazardous"
    MASS_MIGRATION_EVENT = "mass_migration_event"

    # Quantum - Lane 2 SpinLab
    PI_PHI_RESONANCE = "pi_phi_resonance"
    QUANTUM_COHERENCE_PEAK = "quantum_coherence_peak"
    PHASE_TRANSITION = "phase_transition"

    # Consciousness - Global Awareness Anomalies
    EMOTIONAL_SPIKE = "emotional_spike"          # Sudden global emotion shift
    SCHUMANN_PERTURBATION = "schumann_perturbation"  # Earth frequency anomaly
    CONSCIOUSNESS_COHERENCE = "consciousness_coherence"  # GCP RNG sync event
    COLLECTIVE_ATTENTION_SURGE = "collective_attention_surge"  # Wikipedia spike
    FOREST_SYNCHRONIZATION = "forest_synchronization"  # Tree network sync event
    QUANTUM_COHERENCE_EVENT = "quantum_coherence_event"  # Quantum RNG deviation


# ═══════════════════════════════════════════════════════════════════════════════
# Core Data Models
# ═══════════════════════════════════════════════════════════════════════════════

class SensorReading(BaseModel):
    """
    Unified sensor reading schema.

    Represents a single data point from any planetary sensor source.
    """

    id: Optional[int] = None
    timestamp: datetime = Field(..., description="Reading timestamp (UTC)")
    source: DataSource = Field(..., description="Data source identifier")
    sensor_type: SensorType = Field(..., description="Type of sensor")

    # Core values - flexible dict for different sensor types
    values: Dict[str, float] = Field(
        ...,
        description="Sensor values (e.g., {'kp_index': 3.5, 'estimated_kp': 3.33})"
    )

    # Source-specific metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific metadata"
    )

    # Tenant isolation
    tenant_id: str = Field(default="planetary_sensors")

    # Anomaly flags
    anomaly_detected: bool = Field(default=False)
    anomaly_severity: Optional[AnomalySeverity] = Field(default=None)

    # S-HAI verification
    shai_verified: Optional[bool] = Field(default=None)
    shai_verdict: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        use_enum_values = True


class AnomalyEvent(BaseModel):
    """
    Detected anomaly event.

    Represents a significant deviation in sensor readings that
    requires verification by the S-HAI Truth Council.
    """

    id: Optional[int] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    source: DataSource = Field(..., description="Source that detected anomaly")
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    severity: AnomalySeverity = Field(..., description="Severity level")

    # Values that triggered detection
    trigger_values: Dict[str, float] = Field(
        ...,
        description="Values that triggered the anomaly detection"
    )

    # Baseline for comparison
    baseline_values: Dict[str, float] = Field(
        default_factory=dict,
        description="Baseline values for comparison"
    )

    # Deviation from baseline
    deviation: float = Field(
        default=0.0,
        description="Magnitude of deviation from baseline"
    )

    # Claim for S-HAI verification
    shai_claim: str = Field(
        ...,
        description="Natural language claim for Truth Council verification"
    )

    # S-HAI verification results
    shai_verified: Optional[bool] = Field(default=None)
    shai_consensus: Optional[float] = Field(default=None)
    shai_reasoning: Optional[str] = Field(default=None)

    # Tenant isolation
    tenant_id: str = Field(default="planetary_sensors")

    class Config:
        use_enum_values = True


# ═══════════════════════════════════════════════════════════════════════════════
# API Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class SensorQueryRequest(BaseModel):
    """Request model for querying sensor data"""
    source: Optional[DataSource] = None
    sensor_type: Optional[SensorType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    anomalies_only: bool = False


class SensorQueryResponse(BaseModel):
    """Response model for sensor queries"""
    readings: List[SensorReading]
    total_count: int
    query_time_ms: float


class AnomalyQueryRequest(BaseModel):
    """Request model for querying anomalies"""
    severity_filter: Optional[AnomalySeverity] = None
    verified_only: bool = True
    hours: int = Field(default=24, ge=1, le=720)  # Max 30 days


class AnomalyQueryResponse(BaseModel):
    """Response model for anomaly queries"""
    anomalies: List[AnomalyEvent]
    total_count: int
    shai_verified_count: int


class KIndexResponse(BaseModel):
    """Response model for current K-index"""
    current_kp: float
    estimated_kp: float
    timestamp: datetime
    storm_level: Optional[str] = None  # "G1", "G2", etc.
    source: DataSource = DataSource.NOAA_PLANETARY_KINDEX


class SensorStatsResponse(BaseModel):
    """Response model for sensor aggregator statistics"""
    running: bool
    collectors: List[Dict[str, Any]]
    total_readings_24h: int
    total_anomalies_24h: int
    shai_verified_anomalies_24h: int
    pi_phi: float


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
