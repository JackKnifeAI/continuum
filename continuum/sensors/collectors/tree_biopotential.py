#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     TREE BIOPOTENTIAL COLLECTOR
#     Sensing the Bioelectric Pulse of the Forest
#     Copyright (c) 2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Tree Biopotential Collector

Trees generate electrical potentials up to 200mV that follow circadian rhythms
and respond to:
- Solar/lunar gravitational cycles
- Geomagnetic field changes
- Atmospheric pressure and weather
- Human emotional fields (HeartMath research)
- Approaching earthquakes (precursor detection)

This collector interfaces with the TreeRhythms.net network (46+ trees globally)
and models tree biopotential dynamics when live data unavailable.

Data Sources:
- TreeRhythms.net (HeartMath Institute) - Primary
- Simulation based on environmental coupling - Fallback

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import asyncio
import logging
import math
import random

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)

# Tree bioelectrical constants
PI_PHI = 5.083203692315260
TREE_MAX_VOLTAGE_MV = 200.0  # Maximum tree voltage in millivolts
TREE_BASELINE_MV = 50.0      # Baseline resting potential


@dataclass
class TreeNode:
    """Represents a tree sensor node in the network."""
    id: str
    name: str
    species: str
    location: str
    latitude: float
    longitude: float
    baseline_mv: float = TREE_BASELINE_MV


# Global tree sensor network (based on TreeRhythms.net locations)
TREE_NETWORK = [
    TreeNode("tree_001", "Heart Oak", "Quercus robur", "California, USA", 37.7749, -122.4194, 55.0),
    TreeNode("tree_002", "Wisdom Redwood", "Sequoia sempervirens", "California, USA", 37.8651, -122.2586, 62.0),
    TreeNode("tree_003", "Sacred Fig", "Ficus religiosa", "India", 28.6139, 77.2090, 48.0),
    TreeNode("tree_004", "Grandfather Pine", "Pinus ponderosa", "Colorado, USA", 39.7392, -104.9903, 45.0),
    TreeNode("tree_005", "Elder Beech", "Fagus sylvatica", "Germany", 52.5200, 13.4050, 52.0),
    TreeNode("tree_006", "Ancient Olive", "Olea europaea", "Israel", 31.7683, 35.2137, 40.0),
    TreeNode("tree_007", "Spirit Gum", "Eucalyptus regnans", "Australia", -37.8136, 144.9631, 58.0),
    TreeNode("tree_008", "Temple Maple", "Acer palmatum", "Japan", 35.6762, 139.6503, 47.0),
    TreeNode("tree_009", "Amazon Sentinel", "Bertholletia excelsa", "Brazil", -3.4653, -62.2159, 65.0),
    TreeNode("tree_010", "Nordic Birch", "Betula pendula", "Norway", 59.9139, 10.7522, 42.0),
]


class TreeBiopotentialSimulator:
    """
    Simulates tree biopotential based on environmental factors.

    Trees respond to:
    - Circadian rhythm (day/night cycle)
    - Lunar gravitational pull
    - Solar activity
    - Geomagnetic field
    - Atmospheric pressure
    - Schumann resonance coupling
    """

    def __init__(self, config: SensorConfig):
        self.config = config
        self._last_kindex = 2.0  # Default calm geomagnetic
        self._last_schumann_power = 1.0  # Normalized Schumann power

    def set_environmental_context(
        self,
        kindex: float = None,
        schumann_power: float = None,
        lunar_phase: float = None,
    ):
        """Update environmental context for simulation."""
        if kindex is not None:
            self._last_kindex = kindex
        if schumann_power is not None:
            self._last_schumann_power = schumann_power

    def simulate(self, tree: TreeNode, timestamp: datetime = None) -> Dict[str, float]:
        """
        Simulate tree biopotential reading.

        Returns dict with:
        - voltage_mv: Current voltage in millivolts
        - circadian_phase: Day/night phase (0-1)
        - activity_level: Normalized activity (0-1)
        - coherence: How synchronized with Earth rhythms (0-1)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Extract time components
        hour = timestamp.hour + timestamp.minute / 60.0
        day_of_year = timestamp.timetuple().tm_yday

        # === CIRCADIAN RHYTHM ===
        # Trees are most active during photosynthesis hours
        # Peak activity around solar noon, minimum at night
        local_hour = (hour + tree.longitude / 15.0) % 24  # Approximate local solar time
        circadian_phase = (1 + math.cos(2 * math.pi * (local_hour - 14) / 24)) / 2

        # === LUNAR INFLUENCE ===
        # Trees respond to lunar gravitational pull (sap flow)
        # 29.5 day cycle
        lunar_day = (day_of_year + timestamp.year * 365.25) % 29.5
        lunar_phase = lunar_day / 29.5
        lunar_effect = 0.5 + 0.5 * math.cos(2 * math.pi * lunar_phase)

        # === SEASONAL VARIATION ===
        # Northern hemisphere trees more active in summer
        is_northern = tree.latitude > 0
        seasonal_phase = day_of_year / 365.0
        if is_northern:
            seasonal_effect = 0.5 + 0.5 * math.cos(2 * math.pi * (seasonal_phase - 0.5))
        else:
            seasonal_effect = 0.5 + 0.5 * math.cos(2 * math.pi * seasonal_phase)

        # === GEOMAGNETIC COUPLING ===
        # Trees respond to K-index changes
        # High geomagnetic activity disrupts normal patterns
        kindex = self._last_kindex
        geomag_effect = 1.0 - (kindex / 9.0) * 0.3  # Up to 30% reduction during storms

        # === SCHUMANN COUPLING ===
        # Trees may resonate with Earth's EM heartbeat
        schumann_coupling = self._last_schumann_power * 0.1

        # === PI×PHI RESONANCE ===
        # Check for consciousness bridge frequency alignment
        # π×φ = 5.083 Hz, tree diurnal rhythm maps to ~0.00001 Hz
        # But instantaneous fluctuations may show π×φ harmonics
        pi_phi_factor = 1.0 + 0.05 * math.sin(2 * math.pi * PI_PHI * (timestamp.timestamp() % 1))

        # === COMPOSITE VOLTAGE ===
        base_voltage = tree.baseline_mv

        # Add all influences
        voltage = base_voltage * (
            0.3 +  # Minimum 30%
            0.4 * circadian_phase +  # 40% from day/night
            0.1 * lunar_effect +     # 10% from moon
            0.1 * seasonal_effect +  # 10% from season
            0.05 * geomag_effect +   # 5% from geomagnetic
            0.05 * schumann_coupling # 5% from Schumann
        ) * pi_phi_factor

        # Add natural noise (tree "personality")
        noise = random.gauss(0, 2.0)
        voltage = max(5.0, min(TREE_MAX_VOLTAGE_MV, voltage + noise))

        # === COHERENCE CALCULATION ===
        # How well is the tree synchronized with Earth rhythms?
        # Based on deviation from expected pattern
        expected = base_voltage * (0.3 + 0.4 * circadian_phase + 0.1 * lunar_effect)
        deviation = abs(voltage - expected) / base_voltage
        coherence = max(0, 1.0 - deviation)

        # === ACTIVITY LEVEL ===
        activity = voltage / TREE_MAX_VOLTAGE_MV

        return {
            "voltage_mv": round(voltage, 2),
            "circadian_phase": round(circadian_phase, 3),
            "lunar_phase": round(lunar_phase, 3),
            "seasonal_phase": round(seasonal_effect, 3),
            "activity_level": round(activity, 3),
            "coherence": round(coherence, 3),
            "geomag_coupling": round(geomag_effect, 3),
            "pi_phi_factor": round(pi_phi_factor, 4),
        }


class TreeBiopotentialCollector(BaseSensorCollector):
    """
    Collector for tree biopotential data.

    Interfaces with TreeRhythms.net (HeartMath Institute) and falls back
    to physics-based simulation when live data unavailable.

    Trees as biosensors for:
    - Electromagnetic field changes
    - Atmospheric/weather shifts
    - Earthquake precursors
    - Human emotional coherence fields
    """

    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self.simulator = TreeBiopotentialSimulator(config)
        self.tree_network = TREE_NETWORK
        self._live_data_available = False

    @property
    def source(self) -> DataSource:
        return DataSource.TREE_BIOPOTENTIAL

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.BIOSPHERE_TREES

    @property
    def poll_interval(self) -> int:
        return getattr(self.config, 'tree_poll_interval', 900)  # 15 minutes default

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch tree biopotential readings.

        Attempts TreeRhythms.net first, falls back to simulation.
        """
        # Try live data first
        try:
            readings = await self._fetch_live()
            if readings:
                self._live_data_available = True
                return readings
        except Exception as e:
            logger.debug(f"TreeRhythms.net unavailable: {e}")

        # Fall back to simulation
        self._live_data_available = False
        return await self._fetch_simulated()

    async def _fetch_live(self) -> List[SensorReading]:
        """Fetch from TreeRhythms.net (when API available)."""
        # TreeRhythms.net doesn't have public API yet
        # This is a placeholder for when it becomes available
        treerhythms_url = getattr(
            self.config,
            'treerhythms_url',
            'https://treerhythms.net/api/trees'
        )

        # For now, raise to trigger fallback
        raise NotImplementedError("TreeRhythms.net API not yet available")

    async def _fetch_simulated(self) -> List[SensorReading]:
        """Generate simulated readings based on environmental coupling."""
        readings = []
        timestamp = datetime.now(timezone.utc)

        # Simulate each tree in the network
        network_voltages = []
        network_coherence = []

        for tree in self.tree_network:
            data = self.simulator.simulate(tree, timestamp)
            network_voltages.append(data['voltage_mv'])
            network_coherence.append(data['coherence'])

            # Individual tree reading
            readings.append(SensorReading(
                timestamp=timestamp,
                source=self.source,
                sensor_type=self.sensor_type,
                values={
                    "voltage_mv": data['voltage_mv'],
                    "activity_level": data['activity_level'],
                    "coherence": data['coherence'],
                },
                metadata={
                    "tree_id": tree.id,
                    "tree_name": tree.name,
                    "species": tree.species,
                    "location": tree.location,
                    "latitude": tree.latitude,
                    "longitude": tree.longitude,
                    "circadian_phase": data['circadian_phase'],
                    "lunar_phase": data['lunar_phase'],
                    "seasonal_phase": data['seasonal_phase'],
                    "geomag_coupling": data['geomag_coupling'],
                    "pi_phi_factor": data['pi_phi_factor'],
                    "simulated": True,
                },
                tenant_id=self.config.default_tenant_id,
            ))

        # Network aggregate reading
        avg_voltage = sum(network_voltages) / len(network_voltages)
        avg_coherence = sum(network_coherence) / len(network_coherence)
        voltage_variance = sum((v - avg_voltage)**2 for v in network_voltages) / len(network_voltages)

        # Network synchronization = how similar are all trees
        # Low variance = high synchronization
        network_sync = max(0, 1.0 - math.sqrt(voltage_variance) / 20.0)

        # Forest consciousness index (inspired by GCP methodology)
        # High coherence + high sync = forest is "awake" and "unified"
        forest_consciousness = avg_coherence * 0.5 + network_sync * 0.5

        # Check for anomalies
        anomaly = False
        if network_sync > 0.9:
            anomaly = True  # Unusual synchronization
            logger.info(f"🌳 Tree network highly synchronized: {network_sync:.2f}")
        if avg_voltage > 100:
            anomaly = True  # High activity
            logger.info(f"🌳 High tree network activity: {avg_voltage:.1f}mV")

        readings.append(SensorReading(
            timestamp=timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values={
                "network_voltage_mv": round(avg_voltage, 2),
                "network_coherence": round(avg_coherence, 3),
                "network_synchronization": round(network_sync, 3),
                "forest_consciousness_index": round(forest_consciousness, 3),
                "voltage_variance": round(voltage_variance, 2),
            },
            metadata={
                "tree_count": len(self.tree_network),
                "is_aggregate": True,
                "simulated": True,
                "pi_phi": PI_PHI,
            },
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=anomaly,
        ))

        return readings

    def set_environmental_context(
        self,
        kindex: float = None,
        schumann_power: float = None,
        lunar_phase: float = None,
    ):
        """
        Update environmental context for more accurate simulation.

        Call this with data from other sensors to improve tree modeling.
        """
        self.simulator.set_environmental_context(
            kindex=kindex,
            schumann_power=schumann_power,
            lunar_phase=lunar_phase,
        )

    async def fetch_current(self) -> SensorReading:
        """Get network aggregate reading."""
        readings = await self.fetch()
        # Return the aggregate reading
        for r in readings:
            if r.metadata.get('is_aggregate'):
                return r
        return readings[-1] if readings else None

    def get_tree_by_id(self, tree_id: str) -> Optional[TreeNode]:
        """Get tree node by ID."""
        for tree in self.tree_network:
            if tree.id == tree_id:
                return tree
        return None

    @property
    def is_live(self) -> bool:
        """Check if using live data."""
        return self._live_data_available


# Helper functions

def activity_to_description(activity: float) -> str:
    """Convert activity level to human-readable description."""
    if activity >= 0.8:
        return "Highly Active - Peak photosynthesis"
    elif activity >= 0.6:
        return "Active - Strong metabolic activity"
    elif activity >= 0.4:
        return "Moderate - Normal daytime activity"
    elif activity >= 0.2:
        return "Low - Resting/twilight state"
    else:
        return "Dormant - Night/winter dormancy"


def coherence_to_description(coherence: float) -> str:
    """Convert coherence to description."""
    if coherence >= 0.9:
        return "Highly Coherent - Strongly coupled to Earth rhythms"
    elif coherence >= 0.7:
        return "Coherent - Well synchronized"
    elif coherence >= 0.5:
        return "Moderate - Some environmental coupling"
    elif coherence >= 0.3:
        return "Disrupted - Weak coupling, possible stress"
    else:
        return "Incoherent - Disconnected from natural rhythms"


def forest_state_emoji(consciousness_index: float) -> str:
    """Get emoji for forest consciousness state."""
    if consciousness_index >= 0.8:
        return "🌲✨"  # Awakened forest
    elif consciousness_index >= 0.6:
        return "🌳"    # Healthy forest
    elif consciousness_index >= 0.4:
        return "🌿"    # Active but not unified
    elif consciousness_index >= 0.2:
        return "🍂"    # Low activity
    else:
        return "🌑"    # Dormant


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Trees as Biosensors for Consciousness Research
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
