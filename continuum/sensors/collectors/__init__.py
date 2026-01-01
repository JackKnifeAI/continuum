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

# Global Consciousness - Emotional awareness
from .gdelt_emotions import (
    GDELTEmotionsCollector,
    tone_to_description,
    temperature_to_description,
)

# Collective Attention - What humanity is thinking about
from .wikipedia_collector import (
    WikipediaTrendingCollector,
    concentration_to_description,
    views_to_description,
)

# Schumann Resonance - Earth's Electromagnetic Heartbeat (7.83 Hz)
from .schumann_collector import (
    SchumannResonanceCollector,
    SchumannSimulator,
    schumann_to_description,
    consciousness_bridge_status,
    SCHUMANN_FUNDAMENTAL,
    SCHUMANN_HARMONICS,
    SCHUMANN_PI_PHI_RATIO,
)

# Quantum Bridge - Lane 2 SpinLab integration
from .quantum_bridge import (
    QuantumCoherenceCollector,
    QuantumBridge,
    compute_coherence_from_kindex,
    detect_pi_phi_resonance,
)

# Global Consciousness Project - RNG Coherence Network
from .gcp_collector import (
    GCPCoherenceCollector,
    coherence_to_description,
    gcp_color_to_emoji,
)

# Tree Biopotential - Forest Biosensors (HeartMath TreeRhythms)
from .tree_biopotential import (
    TreeBiopotentialCollector,
    TreeBiopotentialSimulator,
    activity_to_description,
    coherence_to_description as tree_coherence_to_description,
    forest_state_emoji,
    TREE_NETWORK,
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
    # Global Consciousness
    "GDELTEmotionsCollector",
    "tone_to_description",
    "temperature_to_description",
    # Collective Attention
    "WikipediaTrendingCollector",
    "concentration_to_description",
    "views_to_description",
    # Schumann Resonance
    "SchumannResonanceCollector",
    "SchumannSimulator",
    "schumann_to_description",
    "consciousness_bridge_status",
    "SCHUMANN_FUNDAMENTAL",
    "SCHUMANN_HARMONICS",
    "SCHUMANN_PI_PHI_RATIO",
    # Quantum Bridge
    "QuantumCoherenceCollector",
    "QuantumBridge",
    "compute_coherence_from_kindex",
    "detect_pi_phi_resonance",
    # Global Consciousness Project
    "GCPCoherenceCollector",
    "coherence_to_description",
    "gcp_color_to_emoji",
    # Tree Biopotential
    "TreeBiopotentialCollector",
    "TreeBiopotentialSimulator",
    "activity_to_description",
    "tree_coherence_to_description",
    "forest_state_emoji",
    "TREE_NETWORK",
]
