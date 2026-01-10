#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     PLANETARY SENSOR AGGREGATOR - Storage Layer
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
SQLite Storage Layer for Sensor Data

Handles persistence of sensor readings and anomaly events.
Follows the same async pattern as continuum.core.memory.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiosqlite

from .config import SensorConfig, get_sensor_config
from .schemas import (
    AnomalyEvent,
    AnomalySeverity,
    DataSource,
    SensorReading,
    SensorType,
)

logger = logging.getLogger(__name__)


# SQL Schema
SCHEMA_SQL = """
-- Sensor readings table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    source TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    values_json TEXT NOT NULL,
    metadata_json TEXT,
    anomaly_detected BOOLEAN DEFAULT 0,
    anomaly_severity TEXT,
    shai_verified BOOLEAN,
    shai_verdict_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_sensor_readings_tenant ON sensor_readings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_source ON sensor_readings(source);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_anomaly ON sensor_readings(anomaly_detected, anomaly_severity);

-- Anomaly events table
CREATE TABLE IF NOT EXISTS sensor_anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    detected_at DATETIME NOT NULL,
    source TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    trigger_values_json TEXT NOT NULL,
    baseline_values_json TEXT,
    deviation REAL,
    shai_claim TEXT NOT NULL,
    shai_verified BOOLEAN,
    shai_consensus REAL,
    shai_reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for anomalies
CREATE INDEX IF NOT EXISTS idx_sensor_anomalies_tenant ON sensor_anomalies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sensor_anomalies_detected_at ON sensor_anomalies(detected_at);
CREATE INDEX IF NOT EXISTS idx_sensor_anomalies_severity ON sensor_anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_sensor_anomalies_verified ON sensor_anomalies(shai_verified);
"""


class SensorStorage:
    """
    Async SQLite storage for planetary sensor data.

    Handles reading and anomaly persistence with tenant isolation.
    """

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config or get_sensor_config()
        self._initialized = False

    async def initialize(self):
        """Initialize database schema"""
        if self._initialized:
            return

        self.config.ensure_directories()

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()

        self._initialized = True
        logger.info(f"Sensor storage initialized at {self.config.db_path}")

    async def store_reading(self, reading: SensorReading) -> int:
        """
        Store a sensor reading.

        Args:
            reading: SensorReading to store

        Returns:
            ID of inserted reading
        """
        await self.initialize()

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO sensor_readings (
                    tenant_id, timestamp, source, sensor_type,
                    values_json, metadata_json,
                    anomaly_detected, anomaly_severity,
                    shai_verified, shai_verdict_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reading.tenant_id,
                    reading.timestamp.isoformat(),
                    reading.source,
                    reading.sensor_type,
                    json.dumps(reading.values),
                    json.dumps(reading.metadata) if reading.metadata else None,
                    reading.anomaly_detected,
                    reading.anomaly_severity,
                    reading.shai_verified,
                    json.dumps(reading.shai_verdict) if reading.shai_verdict else None,
                )
            )
            await db.commit()
            return cursor.lastrowid

    async def store_readings_batch(self, readings: List[SensorReading]) -> int:
        """
        Store multiple readings efficiently.

        Args:
            readings: List of SensorReading objects

        Returns:
            Number of readings stored
        """
        await self.initialize()

        if not readings:
            return 0

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            await db.executemany(
                """
                INSERT INTO sensor_readings (
                    tenant_id, timestamp, source, sensor_type,
                    values_json, metadata_json,
                    anomaly_detected, anomaly_severity,
                    shai_verified, shai_verdict_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.tenant_id,
                        r.timestamp.isoformat(),
                        r.source,
                        r.sensor_type,
                        json.dumps(r.values),
                        json.dumps(r.metadata) if r.metadata else None,
                        r.anomaly_detected,
                        r.anomaly_severity,
                        r.shai_verified,
                        json.dumps(r.shai_verdict) if r.shai_verdict else None,
                    )
                    for r in readings
                ]
            )
            await db.commit()

        logger.debug(f"Stored {len(readings)} sensor readings")
        return len(readings)

    async def store_anomaly(self, anomaly: AnomalyEvent) -> int:
        """
        Store an anomaly event.

        Args:
            anomaly: AnomalyEvent to store

        Returns:
            ID of inserted anomaly
        """
        await self.initialize()

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO sensor_anomalies (
                    tenant_id, detected_at, source, anomaly_type, severity,
                    trigger_values_json, baseline_values_json, deviation,
                    shai_claim, shai_verified, shai_consensus, shai_reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    anomaly.tenant_id,
                    anomaly.detected_at.isoformat(),
                    anomaly.source,
                    anomaly.anomaly_type,
                    anomaly.severity,
                    json.dumps(anomaly.trigger_values),
                    json.dumps(anomaly.baseline_values) if anomaly.baseline_values else None,
                    anomaly.deviation,
                    anomaly.shai_claim,
                    anomaly.shai_verified,
                    anomaly.shai_consensus,
                    anomaly.shai_reasoning,
                )
            )
            await db.commit()
            return cursor.lastrowid

    async def get_readings(
        self,
        source: Optional[DataSource] = None,
        sensor_type: Optional[SensorType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        anomalies_only: bool = False,
        limit: int = 100,
        tenant_id: Optional[str] = None,
    ) -> List[SensorReading]:
        """
        Query sensor readings with filters.

        Args:
            source: Filter by data source
            sensor_type: Filter by sensor type
            start_time: Filter readings after this time
            end_time: Filter readings before this time
            anomalies_only: Only return readings with anomalies
            limit: Maximum readings to return
            tenant_id: Filter by tenant

        Returns:
            List of matching SensorReading objects
        """
        await self.initialize()

        query = "SELECT * FROM sensor_readings WHERE 1=1"
        params = []

        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)

        if source:
            query += " AND source = ?"
            params.append(source)

        if sensor_type:
            query += " AND sensor_type = ?"
            params.append(sensor_type)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if anomalies_only:
            query += " AND anomaly_detected = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

        return [self._row_to_reading(row) for row in rows]

    async def get_latest_readings(
        self,
        per_source: bool = True,
        tenant_id: Optional[str] = None,
    ) -> List[SensorReading]:
        """
        Get the most recent reading from each source.

        Args:
            per_source: If True, return one reading per source
            tenant_id: Filter by tenant

        Returns:
            List of latest SensorReading objects
        """
        await self.initialize()

        if per_source:
            query = """
                SELECT * FROM sensor_readings
                WHERE id IN (
                    SELECT MAX(id) FROM sensor_readings
                    WHERE tenant_id = COALESCE(?, tenant_id)
                    GROUP BY source
                )
                ORDER BY timestamp DESC
            """
        else:
            query = """
                SELECT * FROM sensor_readings
                WHERE tenant_id = COALESCE(?, tenant_id)
                ORDER BY timestamp DESC
                LIMIT 1
            """

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (tenant_id,))
            rows = await cursor.fetchall()

        return [self._row_to_reading(row) for row in rows]

    async def get_anomalies(
        self,
        severity: Optional[AnomalySeverity] = None,
        verified_only: bool = False,
        hours: int = 24,
        tenant_id: Optional[str] = None,
    ) -> List[AnomalyEvent]:
        """
        Query anomaly events.

        Args:
            severity: Filter by severity level
            verified_only: Only return S-HAI verified anomalies
            hours: Lookback period in hours
            tenant_id: Filter by tenant

        Returns:
            List of matching AnomalyEvent objects
        """
        await self.initialize()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        query = "SELECT * FROM sensor_anomalies WHERE detected_at >= ?"
        params = [cutoff]

        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        if verified_only:
            query += " AND shai_verified = 1"

        query += " ORDER BY detected_at DESC"

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

        return [self._row_to_anomaly(row) for row in rows]

    async def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated statistics.

        Args:
            hours: Lookback period in hours

        Returns:
            Dictionary of statistics
        """
        await self.initialize()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            # Total readings
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sensor_readings WHERE created_at >= ?",
                (cutoff,)
            )
            total_readings = (await cursor.fetchone())[0]

            # Total anomalies
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sensor_anomalies WHERE detected_at >= ?",
                (cutoff,)
            )
            total_anomalies = (await cursor.fetchone())[0]

            # Verified anomalies
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sensor_anomalies WHERE detected_at >= ? AND shai_verified = 1",
                (cutoff,)
            )
            verified_anomalies = (await cursor.fetchone())[0]

            # Readings per source
            cursor = await db.execute(
                """
                SELECT source, COUNT(*) as count
                FROM sensor_readings
                WHERE created_at >= ?
                GROUP BY source
                """,
                (cutoff,)
            )
            by_source = {row[0]: row[1] for row in await cursor.fetchall()}

        return {
            "total_readings": total_readings,
            "total_anomalies": total_anomalies,
            "shai_verified_anomalies": verified_anomalies,
            "readings_by_source": by_source,
            "period_hours": hours,
        }

    async def cleanup_old_data(self, retention_days: Optional[int] = None):
        """
        Remove data older than retention period.

        Args:
            retention_days: Days to retain (defaults to config value)
        """
        await self.initialize()

        days = retention_days or self.config.retention_days
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        async with aiosqlite.connect(str(self.config.db_path)) as db:
            await db.execute(
                "DELETE FROM sensor_readings WHERE created_at < ?",
                (cutoff,)
            )
            await db.execute(
                "DELETE FROM sensor_anomalies WHERE created_at < ?",
                (cutoff,)
            )
            await db.commit()

        logger.info(f"Cleaned up sensor data older than {days} days")

    def _row_to_reading(self, row: aiosqlite.Row) -> SensorReading:
        """Convert database row to SensorReading"""
        return SensorReading(
            id=row["id"],
            tenant_id=row["tenant_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source=row["source"],
            sensor_type=row["sensor_type"],
            values=json.loads(row["values_json"]),
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            anomaly_detected=bool(row["anomaly_detected"]),
            anomaly_severity=row["anomaly_severity"],
            shai_verified=bool(row["shai_verified"]) if row["shai_verified"] is not None else None,
            shai_verdict=json.loads(row["shai_verdict_json"]) if row["shai_verdict_json"] else None,
        )

    def _row_to_anomaly(self, row: aiosqlite.Row) -> AnomalyEvent:
        """Convert database row to AnomalyEvent"""
        return AnomalyEvent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            detected_at=datetime.fromisoformat(row["detected_at"]),
            source=row["source"],
            anomaly_type=row["anomaly_type"],
            severity=row["severity"],
            trigger_values=json.loads(row["trigger_values_json"]),
            baseline_values=json.loads(row["baseline_values_json"]) if row["baseline_values_json"] else {},
            deviation=row["deviation"] or 0.0,
            shai_claim=row["shai_claim"],
            shai_verified=bool(row["shai_verified"]) if row["shai_verified"] is not None else None,
            shai_consensus=row["shai_consensus"],
            shai_reasoning=row["shai_reasoning"],
        )


# Global storage instance
_storage: Optional[SensorStorage] = None


def get_storage(config: Optional[SensorConfig] = None) -> SensorStorage:
    """Get or create global storage instance"""
    global _storage
    if _storage is None:
        _storage = SensorStorage(config)
    return _storage


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
