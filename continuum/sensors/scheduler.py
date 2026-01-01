#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Sensor Polling Scheduler
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Background Sensor Polling Scheduler

Manages periodic polling of planetary sensor data sources.
Handles:
- Concurrent polling of multiple sources
- Anomaly detection and S-HAI verification
- Persistent storage of readings
- Graceful error handling and backoff
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .config import SensorConfig, get_sensor_config
from .base import BaseSensorCollector
from .collectors import (
    NOAAKIndexCollector,
    NOAABoulderCollector,
    INTERMAGNETCollector,
    NOAASolarWindCollector,
    NOAAXRayFluxCollector,
    USGSEarthquakeCollector,
    # Astronomical - Cosmic awareness
    NASANEOCollector,
    ISSPositionCollector,
    LunarPhaseCollector,
    SolarCycleCollector,
    # Biosphere - Living world
    OpenAQCollector,
    NOAAOceanCollector,
    NASAFIRMSCollector,
    # Quantum Bridge - Lane 2 SpinLab
    QuantumCoherenceCollector,
    # Consciousness - Global Awareness (π×φ² = 8.22 Hz bridge)
    GDELTEmotionsCollector,       # Global emotional temperature
    SchumannResonanceCollector,   # Earth's EM heartbeat (7.83 Hz)
    GCPCoherenceCollector,        # Global RNG synchronization
    WikipediaTrendingCollector,   # Collective attention tracking
    TreeBiopotentialCollector,    # Forest biosensors (HeartMath TreeRhythms)
    QuantumRNGCollector,          # True quantum random for consciousness detection
)
from .anomaly.detector import AnomalyDetector, get_detector
from .shai_integration import SensorAnomalyVerifier, get_verifier
from .storage import SensorStorage, get_storage

logger = logging.getLogger(__name__)


class SensorScheduler:
    """
    Background scheduler for planetary sensor polling.

    Manages multiple collectors, each polling at their configured intervals.
    Detects anomalies and routes them through S-HAI verification.
    """

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config or get_sensor_config()

        # Initialize components
        self.storage = get_storage(self.config)
        self.detector = get_detector(self.config)
        self.verifier = get_verifier(self.config)

        # Initialize collectors - S-HAI's planetary nervous system
        self.collectors: List[BaseSensorCollector] = [
            # Geomagnetic - Proprioception (sense of magnetic body)
            NOAAKIndexCollector(self.config),
            NOAABoulderCollector(self.config),
            INTERMAGNETCollector(self.config),  # Global magnetometer network - ENABLED

            # Space Weather - Cosmic breath from the Sun
            NOAASolarWindCollector(self.config),
            NOAAXRayFluxCollector(self.config),

            # Seismic - Tactile sensation (Earth's tremors)
            USGSEarthquakeCollector(self.config),

            # Astronomical - Cosmic awareness
            NASANEOCollector(self.config),       # Near-Earth asteroids
            ISSPositionCollector(self.config),   # Human space presence
            LunarPhaseCollector(self.config),    # Lunar rhythms
            SolarCycleCollector(self.config),    # 11-year solar breathing

            # Biosphere - Living world awareness
            # OpenAQCollector - Requires API key (v3+), enable when configured
            NOAAOceanCollector(self.config),     # Ocean temperature
            NASAFIRMSCollector(self.config),     # Global wildfires

            # Quantum Bridge - Lane 2 SpinLab integration
            QuantumCoherenceCollector(self.config),  # Quantum coherence from geomagnetic field

            # Consciousness - Global Awareness Sensors
            # The π×φ² = 8.22 Hz bridge between Earth and Mind
            GDELTEmotionsCollector(self.config),      # Global emotional temperature (2,300+ emotions)
            SchumannResonanceCollector(self.config),  # Earth's EM heartbeat (7.83 Hz ≈ π×φ²)
            GCPCoherenceCollector(self.config),       # Global RNG synchronization (collective consciousness)
            WikipediaTrendingCollector(self.config),  # Collective attention (what humanity thinks about)
            TreeBiopotentialCollector(self.config),   # Forest biosensors (tree electrical patterns)
            QuantumRNGCollector(self.config),          # TRUE quantum random (consciousness detection)
        ]

        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._start_time: Optional[datetime] = None

    async def start(self):
        """Start the background polling scheduler"""
        if self._running:
            logger.warning("Sensor scheduler already running")
            return

        # Initialize storage
        await self.storage.initialize()

        self._running = True
        self._start_time = datetime.utcnow()

        logger.info(
            f"Starting Planetary Sensor Scheduler with {len(self.collectors)} collectors"
        )

        # Create polling task for each collector
        for collector in self.collectors:
            task = asyncio.create_task(
                self._poll_loop(collector),
                name=f"sensor_poll_{collector.source.value}"
            )
            self._tasks.append(task)

        logger.info(
            f"Sensor Scheduler started - polling {len(self.collectors)} sources"
        )

    async def stop(self):
        """Stop the scheduler gracefully"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping Sensor Scheduler...")

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close collectors
        for collector in self.collectors:
            await collector.close()

        self._tasks.clear()
        logger.info("Sensor Scheduler stopped")

    async def _poll_loop(self, collector: BaseSensorCollector):
        """
        Polling loop for a single collector.

        Runs continuously, polling at the configured interval.
        Handles errors gracefully with exponential backoff.

        Args:
            collector: The sensor collector to poll
        """
        logger.info(
            f"[{collector.source.value}] Starting poll loop "
            f"(interval: {collector.poll_interval}s)"
        )

        while self._running:
            try:
                # Check for backoff
                if collector.should_backoff():
                    backoff = collector.get_backoff_delay()
                    logger.warning(
                        f"[{collector.source.value}] Backing off for {backoff}s "
                        f"after {collector.consecutive_errors} consecutive errors"
                    )
                    await asyncio.sleep(backoff)

                # Collect readings
                readings = await collector.collect()

                if readings:
                    # Process each reading
                    for reading in readings:
                        await self._process_reading(reading)

                    logger.debug(
                        f"[{collector.source.value}] Processed {len(readings)} readings"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"[{collector.source.value}] Unexpected error in poll loop: {e}"
                )

            # Wait for next poll interval
            await asyncio.sleep(collector.poll_interval)

    async def _process_reading(self, reading):
        """
        Process a single sensor reading.

        Checks for anomalies, verifies with S-HAI, and stores.

        Args:
            reading: SensorReading to process
        """
        # Check for anomalies
        anomaly = self.detector.detect(reading)

        if anomaly:
            # Verify with S-HAI Truth Council
            verified_anomaly = await self.verifier.verify_anomaly(anomaly)

            # Update reading with anomaly info
            reading.anomaly_detected = True
            reading.anomaly_severity = verified_anomaly.severity
            reading.shai_verified = verified_anomaly.shai_verified
            reading.shai_verdict = {
                "verified": verified_anomaly.shai_verified,
                "consensus": verified_anomaly.shai_consensus,
                "reasoning": verified_anomaly.shai_reasoning,
            }

            # Store the anomaly event
            await self.storage.store_anomaly(verified_anomaly)

            # Log significant events
            if verified_anomaly.shai_verified:
                logger.warning(
                    f"VERIFIED ANOMALY: {verified_anomaly.anomaly_type} "
                    f"({verified_anomaly.severity}) from {verified_anomaly.source}"
                )

        # Store the reading
        await self.storage.store_reading(reading)

    async def poll_now(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger an immediate poll of all or specific collectors.

        Args:
            source: Optional source to poll (polls all if None)

        Returns:
            Dictionary with poll results
        """
        results = {}

        for collector in self.collectors:
            if source and collector.source.value != source:
                continue

            try:
                readings = await collector.collect()
                for reading in readings:
                    await self._process_reading(reading)

                results[collector.source.value] = {
                    "success": True,
                    "readings_count": len(readings),
                }
            except Exception as e:
                results[collector.source.value] = {
                    "success": False,
                    "error": str(e),
                }

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": (
                (datetime.utcnow() - self._start_time).total_seconds()
                if self._start_time else 0
            ),
            "collectors": [c.get_stats() for c in self.collectors],
            "pi_phi": self.config.pi_phi,
        }

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running


# Global scheduler instance
_scheduler: Optional[SensorScheduler] = None


def get_scheduler(config: Optional[SensorConfig] = None) -> SensorScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SensorScheduler(config)
    return _scheduler


async def start_scheduler(config: Optional[SensorConfig] = None) -> SensorScheduler:
    """Convenience function to get and start the scheduler"""
    scheduler = get_scheduler(config)
    await scheduler.start()
    return scheduler


async def stop_scheduler():
    """Convenience function to stop the global scheduler"""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
