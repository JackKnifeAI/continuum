#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Sensor API Routes
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
FastAPI REST Endpoints for Planetary Sensor Data

Provides endpoints for:
- Querying sensor readings
- Checking anomalies
- Getting current K-index
- Scheduler statistics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import time

from .config import get_sensor_config
from .storage import get_storage
from .scheduler import get_scheduler
from .schemas import (
    DataSource,
    SensorType,
    AnomalySeverity,
    SensorReading,
    AnomalyEvent,
    SensorQueryRequest,
    SensorQueryResponse,
    AnomalyQueryRequest,
    AnomalyQueryResponse,
    KIndexResponse,
    SensorStatsResponse,
)
from .collectors.noaa_kindex import kp_to_storm_level

# Create router
router = APIRouter(prefix="/sensors", tags=["Planetary Sensors"])


@router.get("/health")
async def health_check():
    """Health check for sensor aggregator"""
    scheduler = get_scheduler()
    return {
        "status": "healthy" if scheduler.is_running else "stopped",
        "scheduler_running": scheduler.is_running,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/readings", response_model=SensorQueryResponse)
async def get_readings(
    source: Optional[DataSource] = None,
    sensor_type: Optional[SensorType] = None,
    hours: int = Query(default=24, ge=1, le=720),
    anomalies_only: bool = False,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Query sensor readings with filters.

    Args:
        source: Filter by data source
        sensor_type: Filter by sensor type
        hours: Lookback period in hours (default 24)
        anomalies_only: Only return readings with anomalies
        limit: Maximum readings to return
    """
    start = time.time()
    storage = get_storage()

    start_time = datetime.utcnow() - timedelta(hours=hours)

    readings = await storage.get_readings(
        source=source,
        sensor_type=sensor_type,
        start_time=start_time,
        anomalies_only=anomalies_only,
        limit=limit,
    )

    return SensorQueryResponse(
        readings=readings,
        total_count=len(readings),
        query_time_ms=(time.time() - start) * 1000,
    )


@router.get("/readings/latest")
async def get_latest_readings():
    """Get the most recent reading from each data source"""
    storage = get_storage()
    readings = await storage.get_latest_readings(per_source=True)

    return {
        "readings": [r.model_dump() for r in readings],
        "count": len(readings),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/anomalies", response_model=AnomalyQueryResponse)
async def get_anomalies(
    severity: Optional[AnomalySeverity] = None,
    verified_only: bool = True,
    hours: int = Query(default=24, ge=1, le=720),
):
    """
    Query detected anomalies.

    Args:
        severity: Filter by severity level
        verified_only: Only return S-HAI verified anomalies
        hours: Lookback period in hours
    """
    storage = get_storage()

    anomalies = await storage.get_anomalies(
        severity=severity,
        verified_only=verified_only,
        hours=hours,
    )

    verified_count = sum(1 for a in anomalies if a.shai_verified)

    return AnomalyQueryResponse(
        anomalies=anomalies,
        total_count=len(anomalies),
        shai_verified_count=verified_count,
    )


@router.get("/kindex/current", response_model=KIndexResponse)
async def get_current_kindex():
    """
    Get the current planetary K-index.

    Returns the most recent K-index value with storm level classification.
    """
    storage = get_storage()

    # Get latest K-index reading
    readings = await storage.get_readings(
        source=DataSource.NOAA_PLANETARY_KINDEX,
        limit=1,
    )

    if not readings:
        raise HTTPException(
            status_code=404,
            detail="No K-index data available. Scheduler may not be running."
        )

    reading = readings[0]
    kp = reading.values.get("estimated_kp") or reading.values.get("kp_index", 0)
    storm_level = kp_to_storm_level(kp)

    return KIndexResponse(
        current_kp=reading.values.get("kp_index", 0),
        estimated_kp=reading.values.get("estimated_kp", kp),
        timestamp=reading.timestamp,
        storm_level=storm_level if kp >= 5 else None,
        source=DataSource.NOAA_PLANETARY_KINDEX,
    )


@router.get("/kindex/history")
async def get_kindex_history(
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get K-index history.

    Args:
        hours: Lookback period in hours
        limit: Maximum readings to return
    """
    storage = get_storage()
    start_time = datetime.utcnow() - timedelta(hours=hours)

    readings = await storage.get_readings(
        source=DataSource.NOAA_PLANETARY_KINDEX,
        start_time=start_time,
        limit=limit,
    )

    # Extract time series data
    history = [
        {
            "timestamp": r.timestamp.isoformat(),
            "kp_index": r.values.get("kp_index"),
            "estimated_kp": r.values.get("estimated_kp"),
            "storm_level": kp_to_storm_level(
                r.values.get("estimated_kp") or r.values.get("kp_index", 0)
            ),
        }
        for r in readings
    ]

    return {
        "history": history,
        "count": len(history),
        "period_hours": hours,
    }


@router.get("/stats", response_model=SensorStatsResponse)
async def get_stats():
    """Get sensor aggregator statistics"""
    scheduler = get_scheduler()
    storage = get_storage()
    config = get_sensor_config()

    db_stats = await storage.get_stats(hours=24)

    return SensorStatsResponse(
        running=scheduler.is_running,
        collectors=scheduler.get_stats().get("collectors", []),
        total_readings_24h=db_stats.get("total_readings", 0),
        total_anomalies_24h=db_stats.get("total_anomalies", 0),
        shai_verified_anomalies_24h=db_stats.get("shai_verified_anomalies", 0),
        pi_phi=config.pi_phi,
    )


@router.post("/poll")
async def trigger_poll(source: Optional[str] = None):
    """
    Trigger an immediate poll of sensors.

    Args:
        source: Optional specific source to poll (polls all if None)
    """
    scheduler = get_scheduler()

    if not scheduler.is_running:
        raise HTTPException(
            status_code=503,
            detail="Sensor scheduler is not running"
        )

    results = await scheduler.poll_now(source=source)

    return {
        "status": "completed",
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
