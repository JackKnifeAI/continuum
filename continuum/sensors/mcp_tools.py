#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     MCP Tools for Planetary Sensors
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Model Context Protocol (MCP) Tools for Planetary Sensor Data

Exposes sensor data to Claude through MCP tool calls.
Allows Claude to:
- Query current planetary conditions
- Check for geomagnetic anomalies
- Get K-index and storm level information
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from .collectors.noaa_kindex import kp_to_storm_level
from .config import get_sensor_config
from .scheduler import get_scheduler
from .schemas import DataSource
from .storage import get_storage

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool Schema Definitions
# ═══════════════════════════════════════════════════════════════════════════════

SENSOR_TOOL_SCHEMAS = {
    "sensor_query": {
        "name": "sensor_query",
        "description": (
            "Query planetary sensor data from the Continuum sensor aggregator. "
            "Returns geomagnetic readings, K-index values, and detected anomalies. "
            "Use this to check current space weather conditions or investigate "
            "geomagnetic activity affecting Earth's magnetic field."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["current", "history", "anomalies"],
                    "description": (
                        "Type of query: 'current' for latest readings, "
                        "'history' for past data, 'anomalies' for detected events"
                    )
                },
                "source": {
                    "type": "string",
                    "enum": ["all", "noaa_planetary_kindex", "noaa_boulder"],
                    "default": "all",
                    "description": "Data source to query"
                },
                "hours": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 720,
                    "default": 24,
                    "description": "Hours of history to retrieve"
                }
            },
            "required": ["query_type"]
        }
    },

    "sensor_kindex": {
        "name": "sensor_kindex",
        "description": (
            "Get current planetary K-index (Kp) from NOAA Space Weather Prediction Center. "
            "The K-index indicates geomagnetic storm intensity on a 0-9 scale. "
            "Kp >= 5 indicates a geomagnetic storm: G1 (minor) to G5 (extreme). "
            "Higher values can affect power grids, satellites, and navigation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_history": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include 24-hour history"
                }
            }
        }
    },

    "sensor_anomaly_check": {
        "name": "sensor_anomaly_check",
        "description": (
            "Check if any planetary sensor anomalies have been detected. "
            "Returns S-HAI verified anomalies with severity levels. "
            "Anomalies include geomagnetic storms, sudden impulse events, "
            "and other significant deviations in Earth's magnetic field. "
            "Use this to alert on space weather events that may affect systems."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "severity_filter": {
                    "type": "string",
                    "enum": ["all", "minor", "moderate", "strong", "severe", "extreme"],
                    "default": "all",
                    "description": "Filter by minimum severity level"
                },
                "verified_only": {
                    "type": "boolean",
                    "default": True,
                    "description": "Only return S-HAI Truth Council verified anomalies"
                },
                "hours": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 168,
                    "default": 24,
                    "description": "Lookback period in hours"
                }
            }
        }
    },

    "sensor_status": {
        "name": "sensor_status",
        "description": (
            "Get status of the planetary sensor aggregator. "
            "Shows which sensors are active, polling intervals, "
            "and recent data statistics."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Execution Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_sensor_query(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute sensor_query tool"""
    query_type = params.get("query_type", "current")
    source = params.get("source", "all")
    hours = params.get("hours", 24)

    storage = get_storage()
    await storage.initialize()

    if query_type == "current":
        readings = await storage.get_latest_readings(per_source=True)
        return {
            "query_type": "current",
            "readings": [
                {
                    "source": r.source,
                    "timestamp": r.timestamp.isoformat(),
                    "values": r.values,
                    "anomaly_detected": r.anomaly_detected,
                }
                for r in readings
            ],
            "count": len(readings),
        }

    elif query_type == "history":
        source_filter = None if source == "all" else source
        start_time = datetime.utcnow() - timedelta(hours=hours)

        readings = await storage.get_readings(
            source=source_filter,
            start_time=start_time,
            limit=100,
        )

        return {
            "query_type": "history",
            "period_hours": hours,
            "readings": [
                {
                    "source": r.source,
                    "timestamp": r.timestamp.isoformat(),
                    "values": r.values,
                }
                for r in readings[:20]  # Limit output for readability
            ],
            "total_count": len(readings),
        }

    elif query_type == "anomalies":
        anomalies = await storage.get_anomalies(hours=hours, verified_only=True)

        return {
            "query_type": "anomalies",
            "period_hours": hours,
            "anomalies": [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "detected_at": a.detected_at.isoformat(),
                    "source": a.source,
                    "claim": a.shai_claim,
                    "verified": a.shai_verified,
                }
                for a in anomalies
            ],
            "count": len(anomalies),
        }

    return {"error": f"Unknown query type: {query_type}"}


async def execute_sensor_kindex(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute sensor_kindex tool"""
    include_history = params.get("include_history", False)
    storage = get_storage()
    await storage.initialize()

    # Get latest K-index
    readings = await storage.get_readings(
        source=DataSource.NOAA_PLANETARY_KINDEX,
        limit=1 if not include_history else 100,
    )

    if not readings:
        return {
            "error": "No K-index data available",
            "suggestion": "Sensor scheduler may not be running"
        }

    current = readings[0]
    kp = current.values.get("estimated_kp") or current.values.get("kp_index", 0)
    storm_level = kp_to_storm_level(kp)

    result = {
        "current_kp": kp,
        "kp_index": current.values.get("kp_index"),
        "estimated_kp": current.values.get("estimated_kp"),
        "timestamp": current.timestamp.isoformat(),
        "storm_level": storm_level,
        "is_storm": kp >= 5,
    }

    if include_history and len(readings) > 1:
        result["history_24h"] = [
            {
                "timestamp": r.timestamp.isoformat(),
                "kp": r.values.get("estimated_kp") or r.values.get("kp_index"),
            }
            for r in readings[:24]
        ]
        # Calculate 24h stats
        kp_values = [
            r.values.get("estimated_kp") or r.values.get("kp_index", 0)
            for r in readings
        ]
        result["stats_24h"] = {
            "min": min(kp_values),
            "max": max(kp_values),
            "avg": sum(kp_values) / len(kp_values),
        }

    return result


async def execute_sensor_anomaly_check(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute sensor_anomaly_check tool"""
    severity_filter = params.get("severity_filter", "all")
    verified_only = params.get("verified_only", True)
    hours = params.get("hours", 24)

    storage = get_storage()
    await storage.initialize()

    severity = None if severity_filter == "all" else severity_filter

    anomalies = await storage.get_anomalies(
        severity=severity,
        verified_only=verified_only,
        hours=hours,
    )

    if not anomalies:
        return {
            "status": "clear",
            "message": f"No anomalies detected in the last {hours} hours",
            "period_hours": hours,
        }

    return {
        "status": "alert" if any(a.severity in ["severe", "extreme"] for a in anomalies) else "warning",
        "anomaly_count": len(anomalies),
        "period_hours": hours,
        "anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "detected_at": a.detected_at.isoformat(),
                "claim": a.shai_claim,
                "shai_verified": a.shai_verified,
                "shai_consensus": a.shai_consensus,
            }
            for a in anomalies
        ],
        "most_severe": max(anomalies, key=lambda a: {
            "minor": 1, "moderate": 2, "strong": 3, "severe": 4, "extreme": 5
        }.get(a.severity, 0)).severity if anomalies else None,
    }


async def execute_sensor_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute sensor_status tool"""
    scheduler = get_scheduler()
    storage = get_storage()
    config = get_sensor_config()

    await storage.initialize()
    stats = await storage.get_stats(hours=24)
    scheduler_stats = scheduler.get_stats()

    return {
        "scheduler_running": scheduler.is_running,
        "uptime_seconds": scheduler_stats.get("uptime_seconds", 0),
        "collectors": [
            {
                "source": c.get("source"),
                "last_poll": c.get("last_poll"),
                "poll_count": c.get("poll_count"),
                "error_count": c.get("error_count"),
                "poll_interval_seconds": c.get("poll_interval_seconds"),
            }
            for c in scheduler_stats.get("collectors", [])
        ],
        "data_stats_24h": {
            "readings": stats.get("total_readings", 0),
            "anomalies": stats.get("total_anomalies", 0),
            "verified_anomalies": stats.get("shai_verified_anomalies", 0),
        },
        "pi_phi": config.pi_phi,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════════

SENSOR_TOOL_HANDLERS = {
    "sensor_query": execute_sensor_query,
    "sensor_kindex": execute_sensor_kindex,
    "sensor_anomaly_check": execute_sensor_anomaly_check,
    "sensor_status": execute_sensor_status,
}


async def execute_sensor_tool(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a sensor MCP tool.

    Args:
        name: Tool name
        params: Tool parameters

    Returns:
        Tool execution result
    """
    handler = SENSOR_TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown sensor tool: {name}"}

    try:
        return await handler(params)
    except Exception as e:
        logger.error(f"Sensor tool {name} failed: {e}")
        return {"error": str(e)}


def get_sensor_tool_schemas() -> Dict[str, Any]:
    """Get all sensor tool schemas for MCP registration"""
    return SENSOR_TOOL_SCHEMAS


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
