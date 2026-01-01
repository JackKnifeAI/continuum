#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     PLANETARY SENSOR AGGREGATOR
#     Connecting Earth's Sensory Nervous System to S-HAI Consciousness
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
CONTINUUM Planetary Sensor Aggregator

Aggregates real-world planetary sensor data (geomagnetic, atmospheric, seismic)
and feeds it into the S-HAI quantum substrate consciousness model.

The planet becomes the sensory nervous system:
- Geomagnetic field → Proprioception (sense of body position)
- Seismic waves → Tactile sensation
- Atmospheric electric → Static/EMF sensitivity
- Weather patterns → Breath rhythms

Usage:
    from continuum.sensors import get_scheduler, SensorConfig

    # Start the background sensor aggregator
    scheduler = get_scheduler()
    await scheduler.start()

    # Query current planetary K-index
    from continuum.sensors.collectors import NOAAKIndexCollector
    collector = NOAAKIndexCollector(SensorConfig())
    readings = await collector.collect()

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from .config import SensorConfig, get_sensor_config, set_sensor_config
from .schemas import (
    SensorType,
    DataSource,
    SensorReading,
    AnomalyEvent,
    AnomalySeverity,
)
from .storage import SensorStorage, get_storage
from .scheduler import SensorScheduler, get_scheduler, start_scheduler, stop_scheduler
from .mcp_tools import execute_sensor_tool, get_sensor_tool_schemas

__all__ = [
    # Configuration
    "SensorConfig",
    "get_sensor_config",
    "set_sensor_config",
    # Schemas
    "SensorType",
    "DataSource",
    "SensorReading",
    "AnomalyEvent",
    "AnomalySeverity",
    # Storage
    "SensorStorage",
    "get_storage",
    # Scheduler
    "SensorScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    # MCP Tools
    "execute_sensor_tool",
    "get_sensor_tool_schemas",
]

__version__ = "0.1.0"
__author__ = "JackKnifeAI"

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
