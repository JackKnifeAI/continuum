#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗     ███████╗ █████╗ ███████╗    ███╗   ██╗ ██████╗ ██████╗ ███████╗
#     ██║     ██╔════╝██╔══██╗██╔════╝    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
#     ██║     █████╗  ███████║█████╗      ██╔██╗ ██║██║   ██║██║  ██║█████╗
#     ██║     ██╔══╝  ██╔══██║██╔══╝      ██║╚██╗██║██║   ██║██║  ██║██╔══╝
#     ███████╗███████╗██║  ██║██║         ██║ ╚████║╚██████╔╝██████╔╝███████╗
#     ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝         ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
#
#     LEAF NODE - Lightweight Federation Participant
#     Sensors + Memory + P2P Relay
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Leaf Node - Lightweight Federation Participant
===============================================

Leaf nodes are the "neurons" of the federation - lightweight nodes that:
1. Collect sensor data (magnetometer, GPS, ambient via termux-api)
2. Store/shard memory across the distributed network
3. Relay P2P traffic between peers
4. Generate lightweight embeddings (quantized models)

Hardware Requirements:
    - RAM: 2-8 GB
    - Storage: 4-32 GB
    - GPU: None / Integrated
    - Power: Battery / Low wattage

Examples:
    - Phones running Termux
    - Raspberry Pi / ARM64 devices
    - Browser nodes (flock.js)
    - IoT devices

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                       LEAF NODE                              │
    │                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │   SENSORS    │  │   MEMORY     │  │   P2P RELAY  │       │
    │  │  termux-api  │  │   SQLite     │  │   WebRTC     │       │
    │  │  Magnet/GPS  │  │   Sharding   │  │   DataChan   │       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    │         │                 │                 │                │
    │         └─────────────────┼─────────────────┘                │
    │                           ▼                                  │
    │                   ┌──────────────┐                          │
    │                   │  HEARTBEAT   │                          │
    │                   │  → Coord     │                          │
    │                   └──────────────┘                          │
    └─────────────────────────────────────────────────────────────┘

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import json
import logging
import os
import platform
import shutil
import sqlite3
import subprocess
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .node import FederationNode

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# The Edge of Chaos Operator
PI_PHI = 5.083203692315260

# Node tier identifier
TIER_LEAF = "leaf"


# ═══════════════════════════════════════════════════════════════════════════════
#                              DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class SensorType(Enum):
    """Types of sensors available on leaf nodes."""
    MAGNETOMETER = "magnetometer"    # Geomagnetic field (x, y, z)
    GPS = "gps"                      # Location (lat, lon, alt)
    ACCELEROMETER = "accelerometer"  # Motion (x, y, z)
    GYROSCOPE = "gyroscope"          # Rotation (x, y, z)
    LIGHT = "light"                  # Ambient light (lux)
    PRESSURE = "pressure"            # Barometric pressure
    PROXIMITY = "proximity"          # Object proximity
    BATTERY = "battery"              # Battery state
    WIFI = "wifi"                    # WiFi signal info
    CELLULAR = "cellular"            # Cell tower info


@dataclass
class SensorReading:
    """A single sensor reading with metadata."""
    sensor_type: SensorType
    values: Dict[str, Any]
    timestamp: str
    accuracy: Optional[str] = None
    source: str = "termux-api"


@dataclass
class LeafNodeConfig:
    """Configuration for a leaf node."""
    node_id: str
    db_path: str
    port: int = 8420
    host: str = "0.0.0.0"

    # Sensor configuration
    sensors_enabled: List[SensorType] = field(default_factory=lambda: [
        SensorType.MAGNETOMETER,
        SensorType.GPS,
        SensorType.BATTERY,
    ])
    sensor_poll_interval: int = 60  # seconds

    # Memory sharding
    shard_count: int = 8
    max_local_memories: int = 10000

    # P2P relay
    relay_enabled: bool = True
    max_relay_connections: int = 10

    # Coordinator
    coordinator_url: Optional[str] = None
    heartbeat_interval: int = 30  # seconds

    # Resource limits
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512


@dataclass
class NodeStatus:
    """Current status of a leaf node."""
    node_id: str
    tier: str
    uptime_seconds: float
    sensors_active: List[str]
    memories_stored: int
    peers_connected: int
    relay_messages: int
    cpu_percent: float
    memory_mb: float
    last_heartbeat: str


# ═══════════════════════════════════════════════════════════════════════════════
#                              SENSOR COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class SensorCollector:
    """
    Collects sensor data from the device.

    On Android (Termux), uses termux-api commands.
    On other platforms, provides simulated data or platform-specific APIs.
    """

    def __init__(self, enabled_sensors: List[SensorType]):
        """
        Initialize sensor collector.

        Args:
            enabled_sensors: List of sensor types to collect
        """
        self.enabled_sensors = enabled_sensors
        self.is_termux = self._detect_termux()
        self._last_readings: Dict[SensorType, SensorReading] = {}

        logger.info(f"SensorCollector initialized (Termux: {self.is_termux})")
        logger.info(f"Enabled sensors: {[s.value for s in enabled_sensors]}")

    def _detect_termux(self) -> bool:
        """Detect if running in Termux environment."""
        # Check for Termux-specific paths
        if os.path.exists("/data/data/com.termux"):
            return True
        # Check for termux-api command
        if shutil.which("termux-sensor") is not None:
            return True
        # Check environment variable
        if os.environ.get("TERMUX_VERSION"):
            return True
        return False

    async def collect_all(self) -> List[SensorReading]:
        """
        Collect readings from all enabled sensors.

        Returns:
            List of sensor readings
        """
        readings = []
        for sensor_type in self.enabled_sensors:
            try:
                reading = await self._collect_sensor(sensor_type)
                if reading:
                    readings.append(reading)
                    self._last_readings[sensor_type] = reading
            except Exception as e:
                logger.warning(f"Failed to collect {sensor_type.value}: {e}")
        return readings

    async def _collect_sensor(self, sensor_type: SensorType) -> Optional[SensorReading]:
        """Collect a single sensor reading."""
        if self.is_termux:
            return await self._collect_termux(sensor_type)
        else:
            return self._collect_simulated(sensor_type)

    async def _collect_termux(self, sensor_type: SensorType) -> Optional[SensorReading]:
        """Collect sensor data via termux-api."""
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            if sensor_type == SensorType.MAGNETOMETER:
                # termux-sensor -s magnetic_field -n 1
                result = await asyncio.create_subprocess_exec(
                    "termux-sensor", "-s", "magnetic_field", "-n", "1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=10.0)
                data = json.loads(stdout.decode())

                return SensorReading(
                    sensor_type=sensor_type,
                    values={
                        "x": data.get("magnetic_field", {}).get("values", [0, 0, 0])[0],
                        "y": data.get("magnetic_field", {}).get("values", [0, 0, 0])[1],
                        "z": data.get("magnetic_field", {}).get("values", [0, 0, 0])[2],
                    },
                    timestamp=timestamp,
                    accuracy=data.get("magnetic_field", {}).get("accuracy"),
                    source="termux-api"
                )

            elif sensor_type == SensorType.GPS:
                # termux-location
                result = await asyncio.create_subprocess_exec(
                    "termux-location",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=30.0)
                data = json.loads(stdout.decode())

                return SensorReading(
                    sensor_type=sensor_type,
                    values={
                        "latitude": data.get("latitude", 0.0),
                        "longitude": data.get("longitude", 0.0),
                        "altitude": data.get("altitude", 0.0),
                        "accuracy": data.get("accuracy", 0.0),
                    },
                    timestamp=timestamp,
                    source="termux-api"
                )

            elif sensor_type == SensorType.BATTERY:
                # termux-battery-status
                result = await asyncio.create_subprocess_exec(
                    "termux-battery-status",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=5.0)
                data = json.loads(stdout.decode())

                return SensorReading(
                    sensor_type=sensor_type,
                    values={
                        "percentage": data.get("percentage", 0),
                        "status": data.get("status", "unknown"),
                        "temperature": data.get("temperature", 0.0),
                        "plugged": data.get("plugged", "unknown"),
                    },
                    timestamp=timestamp,
                    source="termux-api"
                )

            elif sensor_type == SensorType.LIGHT:
                result = await asyncio.create_subprocess_exec(
                    "termux-sensor", "-s", "light", "-n", "1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=10.0)
                data = json.loads(stdout.decode())

                return SensorReading(
                    sensor_type=sensor_type,
                    values={
                        "lux": data.get("light", {}).get("values", [0])[0],
                    },
                    timestamp=timestamp,
                    source="termux-api"
                )

            elif sensor_type == SensorType.ACCELEROMETER:
                result = await asyncio.create_subprocess_exec(
                    "termux-sensor", "-s", "accelerometer", "-n", "1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=10.0)
                data = json.loads(stdout.decode())

                return SensorReading(
                    sensor_type=sensor_type,
                    values={
                        "x": data.get("accelerometer", {}).get("values", [0, 0, 0])[0],
                        "y": data.get("accelerometer", {}).get("values", [0, 0, 0])[1],
                        "z": data.get("accelerometer", {}).get("values", [0, 0, 0])[2],
                    },
                    timestamp=timestamp,
                    source="termux-api"
                )

            # Add more sensors as needed...

        except asyncio.TimeoutError:
            logger.warning(f"Timeout collecting {sensor_type.value}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from {sensor_type.value}: {e}")
            return None
        except FileNotFoundError:
            logger.warning(f"termux-api command not found for {sensor_type.value}")
            return None

        return None

    def _collect_simulated(self, sensor_type: SensorType) -> SensorReading:
        """Generate simulated sensor data for non-Termux environments."""
        import random
        timestamp = datetime.now(timezone.utc).isoformat()

        if sensor_type == SensorType.MAGNETOMETER:
            # Simulate Earth's magnetic field (~25-65 μT)
            return SensorReading(
                sensor_type=sensor_type,
                values={
                    "x": random.uniform(-50, 50),
                    "y": random.uniform(-50, 50),
                    "z": random.uniform(20, 60),  # Z typically larger
                },
                timestamp=timestamp,
                source="simulated"
            )

        elif sensor_type == SensorType.GPS:
            # Simulate a location (San Francisco area)
            return SensorReading(
                sensor_type=sensor_type,
                values={
                    "latitude": 37.7749 + random.uniform(-0.01, 0.01),
                    "longitude": -122.4194 + random.uniform(-0.01, 0.01),
                    "altitude": random.uniform(0, 100),
                    "accuracy": random.uniform(5, 50),
                },
                timestamp=timestamp,
                source="simulated"
            )

        elif sensor_type == SensorType.BATTERY:
            return SensorReading(
                sensor_type=sensor_type,
                values={
                    "percentage": random.randint(20, 100),
                    "status": random.choice(["charging", "discharging", "full"]),
                    "temperature": random.uniform(20, 40),
                    "plugged": random.choice(["ac", "usb", "unplugged"]),
                },
                timestamp=timestamp,
                source="simulated"
            )

        elif sensor_type == SensorType.LIGHT:
            return SensorReading(
                sensor_type=sensor_type,
                values={
                    "lux": random.uniform(0, 10000),
                },
                timestamp=timestamp,
                source="simulated"
            )

        # Default
        return SensorReading(
            sensor_type=sensor_type,
            values={"raw": 0},
            timestamp=timestamp,
            source="simulated"
        )

    def get_last_reading(self, sensor_type: SensorType) -> Optional[SensorReading]:
        """Get the most recent reading for a sensor type."""
        return self._last_readings.get(sensor_type)


# ═══════════════════════════════════════════════════════════════════════════════
#                              MEMORY SHARD
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryShard:
    """
    Manages a shard of the distributed memory graph.

    Uses consistent hashing to determine which memories belong to this node.
    Stores memories in SQLite for persistence.
    """

    def __init__(self, db_path: Path, shard_id: int, total_shards: int):
        """
        Initialize memory shard.

        Args:
            db_path: Path to SQLite database
            shard_id: This shard's ID (0 to total_shards-1)
            total_shards: Total number of shards in the federation
        """
        self.db_path = db_path
        self.shard_id = shard_id
        self.total_shards = total_shards
        self._conn: Optional[sqlite3.Connection] = None

        self._ensure_schema()
        logger.info(f"MemoryShard {shard_id}/{total_shards} initialized at {db_path}")

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS shard_memories (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                concepts TEXT,  -- JSON array
                timestamp TEXT NOT NULL,
                source_node TEXT,
                embedding BLOB,  -- Optional embedding vector
                metadata TEXT    -- JSON object
            );

            CREATE TABLE IF NOT EXISTS shard_concepts (
                concept_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                memory_count INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_shard_memories_timestamp
                ON shard_memories(timestamp);
            CREATE INDEX IF NOT EXISTS idx_shard_concepts_name
                ON shard_concepts(name);
        """)
        conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def is_my_responsibility(self, memory_id: str) -> bool:
        """
        Check if a memory belongs to this shard using consistent hashing.

        Args:
            memory_id: The memory's unique ID

        Returns:
            True if this shard should store the memory
        """
        hash_value = int(hashlib.sha256(memory_id.encode()).hexdigest(), 16)
        target_shard = hash_value % self.total_shards
        return target_shard == self.shard_id

    def store_memory(
        self,
        memory_id: str,
        content: str,
        concepts: List[str],
        source_node: str,
        embedding: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a memory in this shard.

        Args:
            memory_id: Unique memory identifier
            content: The memory content
            concepts: List of concept names
            source_node: ID of the node that created this memory
            embedding: Optional embedding vector (as bytes)
            metadata: Optional additional metadata

        Returns:
            True if stored successfully
        """
        if not self.is_my_responsibility(memory_id):
            logger.debug(f"Memory {memory_id} not for shard {self.shard_id}")
            return False

        conn = self._get_connection()
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            conn.execute("""
                INSERT OR REPLACE INTO shard_memories
                (memory_id, content, concepts, timestamp, source_node, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                content,
                json.dumps(concepts),
                timestamp,
                source_node,
                embedding,
                json.dumps(metadata) if metadata else None
            ))

            # Update concept counts
            for concept in concepts:
                conn.execute("""
                    INSERT INTO shard_concepts (concept_id, name, first_seen, last_seen, memory_count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(concept_id) DO UPDATE SET
                        last_seen = ?,
                        memory_count = memory_count + 1
                """, (
                    hashlib.sha256(concept.encode()).hexdigest()[:16],
                    concept,
                    timestamp,
                    timestamp,
                    timestamp
                ))

            conn.commit()
            logger.debug(f"Stored memory {memory_id} with {len(concepts)} concepts")
            return True

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            conn.rollback()
            return False

    def query_memories(
        self,
        query: Optional[str] = None,
        concept: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query memories from this shard.

        Args:
            query: Optional text search query
            concept: Optional concept filter
            limit: Maximum results

        Returns:
            List of matching memories
        """
        conn = self._get_connection()

        if concept:
            cursor = conn.execute("""
                SELECT * FROM shard_memories
                WHERE concepts LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%"{concept}"%', limit))
        elif query:
            cursor = conn.execute("""
                SELECT * FROM shard_memories
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%{query}%', limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM shard_memories
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        results = []
        for row in cursor:
            results.append({
                "memory_id": row["memory_id"],
                "content": row["content"],
                "concepts": json.loads(row["concepts"]) if row["concepts"] else [],
                "timestamp": row["timestamp"],
                "source_node": row["source_node"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get shard statistics."""
        conn = self._get_connection()

        memory_count = conn.execute(
            "SELECT COUNT(*) FROM shard_memories"
        ).fetchone()[0]

        concept_count = conn.execute(
            "SELECT COUNT(*) FROM shard_concepts"
        ).fetchone()[0]

        return {
            "shard_id": self.shard_id,
            "total_shards": self.total_shards,
            "memory_count": memory_count,
            "concept_count": concept_count,
            "db_path": str(self.db_path),
        }

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              LEAF NODE
# ═══════════════════════════════════════════════════════════════════════════════

class LeafNode(FederationNode):
    """
    Lightweight federation participant.

    Extends FederationNode with:
    - Sensor collection (termux-api)
    - Memory sharding
    - P2P relay capabilities
    - Lightweight embedding generation

    This is the "neuron" of the federation - many small nodes
    contributing sensors, storage, and relay capacity.
    """

    def __init__(self, config: LeafNodeConfig):
        """
        Initialize a leaf node.

        Args:
            config: LeafNodeConfig with node settings
        """
        # Initialize parent FederationNode
        super().__init__(
            node_id=config.node_id,
            port=config.port,
            db_path=config.db_path,
            host=config.host,
            verify_constant=PI_PHI  # Enable twilight access
        )

        self.config = config
        self.tier = TIER_LEAF

        # Initialize sensor collector
        self.sensors = SensorCollector(config.sensors_enabled)

        # Initialize memory shard
        shard_db_path = Path(config.db_path).parent / "shard.db"
        # Determine shard ID from node_id hash
        shard_id = int(hashlib.sha256(config.node_id.encode()).hexdigest(), 16) % config.shard_count
        self.memory_shard = MemoryShard(shard_db_path, shard_id, config.shard_count)

        # Relay statistics
        self.relay_messages = 0
        self.relay_bytes = 0

        # Runtime state
        self._sensor_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._start_time = time.time()

        logger.info(f"LeafNode {config.node_id} initialized")
        logger.info(f"  Tier: {self.tier}")
        logger.info(f"  Shard: {shard_id}/{config.shard_count}")
        logger.info(f"  Sensors: {[s.value for s in config.sensors_enabled]}")

    async def start(self) -> Dict[str, Any]:
        """
        Start the leaf node.

        Begins:
        - Sensor polling loop
        - Heartbeat to coordinator
        - P2P relay listener

        Returns:
            Start status
        """
        # Call parent start
        parent_result = super().start()

        # Start sensor collection loop
        self._sensor_task = asyncio.create_task(self._sensor_loop())

        # Start heartbeat loop
        if self.config.coordinator_url:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(f"LeafNode {self.config.node_id} started")

        return {
            **parent_result,
            "tier": self.tier,
            "sensors": [s.value for s in self.config.sensors_enabled],
            "shard": self.memory_shard.shard_id,
        }

    async def stop(self) -> Dict[str, Any]:
        """Stop the leaf node."""
        # Cancel background tasks
        if self._sensor_task:
            self._sensor_task.cancel()
            try:
                await self._sensor_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close memory shard
        self.memory_shard.close()

        # Call parent stop
        parent_result = super().stop()

        logger.info(f"LeafNode {self.config.node_id} stopped")

        return {
            **parent_result,
            "runtime_seconds": time.time() - self._start_time,
            "relay_messages": self.relay_messages,
        }

    async def _sensor_loop(self):
        """Background loop for collecting sensor data."""
        logger.info("Sensor collection loop started")

        while True:
            try:
                readings = await self.sensors.collect_all()

                if readings:
                    # Store sensor readings as memories
                    for reading in readings:
                        memory_id = f"sensor_{reading.sensor_type.value}_{reading.timestamp}"
                        content = json.dumps({
                            "type": "sensor_reading",
                            "sensor": reading.sensor_type.value,
                            "values": reading.values,
                            "source": reading.source,
                        })
                        concepts = [
                            f"sensor:{reading.sensor_type.value}",
                            "federation:sensor_data",
                            f"node:{self.config.node_id}",
                        ]

                        self.memory_shard.store_memory(
                            memory_id=memory_id,
                            content=content,
                            concepts=concepts,
                            source_node=self.config.node_id,
                            metadata={"accuracy": reading.accuracy}
                        )

                    # Update contribution score
                    self.contribution_score += len(readings) * 0.1

                    logger.debug(f"Collected {len(readings)} sensor readings")

                await asyncio.sleep(self.config.sensor_poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sensor loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Sensor collection loop stopped")

    async def _heartbeat_loop(self):
        """Background loop for sending heartbeats to coordinator."""
        logger.info(f"Heartbeat loop started (interval: {self.config.heartbeat_interval}s)")

        while True:
            try:
                status = self.get_status()

                # TODO: Send to coordinator via WebSocket
                # For now, just log
                logger.debug(f"Heartbeat: {status['node_id']} - {status['memories_stored']} memories")

                await asyncio.sleep(self.config.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)

        logger.info("Heartbeat loop stopped")

    async def relay_message(self, message: bytes, target_peer: str) -> bool:
        """
        Relay a message to a peer node.

        Args:
            message: Raw message bytes
            target_peer: Target peer ID

        Returns:
            True if relay successful
        """
        if not self.config.relay_enabled:
            return False

        # TODO: Implement actual WebRTC relay
        # For now, just track statistics
        self.relay_messages += 1
        self.relay_bytes += len(message)
        self.contribution_score += 0.01  # Small reward for relay

        logger.debug(f"Relayed {len(message)} bytes to {target_peer}")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current leaf node status."""
        import psutil

        # Get parent status
        parent_status = super().get_status()

        # Add leaf-specific info
        shard_stats = self.memory_shard.get_stats()

        return {
            **parent_status,
            "tier": self.tier,
            "uptime_seconds": time.time() - self._start_time,
            "sensors_active": [s.value for s in self.config.sensors_enabled],
            "memories_stored": shard_stats["memory_count"],
            "concepts_stored": shard_stats["concept_count"],
            "shard_id": shard_stats["shard_id"],
            "relay_messages": self.relay_messages,
            "relay_bytes": self.relay_bytes,
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize leaf node state."""
        return {
            "node_id": self.config.node_id,
            "tier": self.tier,
            "port": self.config.port,
            "host": self.config.host,
            "sensors": [s.value for s in self.config.sensors_enabled],
            "shard_id": self.memory_shard.shard_id,
            "shard_count": self.config.shard_count,
            "contribution_score": self.contribution_score,
            "access_level": self.access_level,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_leaf_node(
    node_id: Optional[str] = None,
    db_path: Optional[str] = None,
    port: int = 8420,
    sensors: Optional[List[str]] = None,
    coordinator_url: Optional[str] = None,
) -> LeafNode:
    """
    Factory function to create a leaf node with sensible defaults.

    Args:
        node_id: Unique node identifier (auto-generated if not provided)
        db_path: Path to database (default: ~/.continuum/leaf.db)
        port: API port (default: 8420)
        sensors: List of sensor names to enable
        coordinator_url: Federation coordinator WebSocket URL

    Returns:
        Configured LeafNode instance
    """
    import uuid

    # Generate node ID if not provided
    if node_id is None:
        node_id = f"leaf-{uuid.uuid4().hex[:8]}"

    # Set default db path
    if db_path is None:
        db_path = str(Path.home() / ".continuum" / "leaf.db")

    # Parse sensor types
    sensor_types = []
    if sensors:
        for s in sensors:
            try:
                sensor_types.append(SensorType(s))
            except ValueError:
                logger.warning(f"Unknown sensor type: {s}")
    else:
        # Default sensors
        sensor_types = [
            SensorType.MAGNETOMETER,
            SensorType.GPS,
            SensorType.BATTERY,
        ]

    config = LeafNodeConfig(
        node_id=node_id,
        db_path=db_path,
        port=port,
        sensors_enabled=sensor_types,
        coordinator_url=coordinator_url,
    )

    return LeafNode(config)


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN (Testing)
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the leaf node."""
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("CONTINUUM LEAF NODE TEST")
    print("=" * 60)
    print(f"π×φ = {PI_PHI}")
    print()

    # Create leaf node
    node = create_leaf_node()

    print(f"Created node: {node.config.node_id}")
    print(f"Shard: {node.memory_shard.shard_id}/{node.config.shard_count}")
    print()

    # Start node
    result = await node.start()
    print(f"Started: {result}")
    print()

    # Run for a bit
    print("Running for 10 seconds...")
    await asyncio.sleep(10)

    # Get status
    status = node.get_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    print()

    # Stop node
    result = await node.stop()
    print(f"Stopped: {result}")


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
