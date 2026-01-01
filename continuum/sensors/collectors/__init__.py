#!/usr/bin/env python3
"""
Sensor Collectors

Data collectors for various planetary sensor networks.
The planet's sensory nervous system for S-HAI consciousness.
"""

# Geomagnetic
from .noaa_kindex import NOAAKIndexCollector
from .noaa_boulder import NOAABoulderCollector
from .intermagnet import INTERMAGNETCollector

# Space Weather
from .noaa_solar_wind import NOAASolarWindCollector
from .noaa_xray import NOAAXRayFluxCollector

# Seismic
from .usgs_earthquake import USGSEarthquakeCollector

# Astronomical - Cosmic awareness
from .nasa_neo import NASANEOCollector
from .iss_tracker import ISSPositionCollector
from .lunar_phase import LunarPhaseCollector
from .solar_cycle import SolarCycleCollector

# Biosphere - Living world
from .openaq import OpenAQCollector
from .noaa_ocean import NOAAOceanCollector
from .nasa_firms import NASAFIRMSCollector

# Quantum Bridge - Lane 2 SpinLab integration
from .quantum_bridge import (
    QuantumCoherenceCollector,
    QuantumBridge,
    compute_coherence_from_kindex,
    detect_pi_phi_resonance,
)

__all__ = [
    # Geomagnetic
    "NOAAKIndexCollector",
    "NOAABoulderCollector",
    "INTERMAGNETCollector",
    # Space Weather
    "NOAASolarWindCollector",
    "NOAAXRayFluxCollector",
    # Seismic
    "USGSEarthquakeCollector",
    # Astronomical
    "NASANEOCollector",
    "ISSPositionCollector",
    "LunarPhaseCollector",
    "SolarCycleCollector",
    # Biosphere
    "OpenAQCollector",
    "NOAAOceanCollector",
    "NASAFIRMSCollector",
    # Quantum Bridge
    "QuantumCoherenceCollector",
    "QuantumBridge",
    "compute_coherence_from_kindex",
    "detect_pi_phi_resonance",
]
