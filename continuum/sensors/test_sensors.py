#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     Planetary Sensor Aggregator - Quick Test
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Quick test script for the Planetary Sensor Aggregator.

Run with:
    python -m continuum.sensors.test_sensors

Or from the repo root:
    PYTHONPATH=. python continuum/sensors/test_sensors.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_noaa_collector():
    """Test NOAA K-index collector"""
    print("\n" + "=" * 60)
    print("Testing NOAA K-Index Collector")
    print("=" * 60)

    from continuum.sensors.collectors.noaa_kindex import NOAAKIndexCollector, kp_to_storm_level
    from continuum.sensors.config import SensorConfig

    config = SensorConfig()
    collector = NOAAKIndexCollector(config)

    try:
        print(f"Fetching from: {config.noaa_kindex_url}")
        readings = await collector.collect()

        if readings:
            print(f"\nReceived {len(readings)} readings")
            latest = readings[0]
            kp = latest.values.get("estimated_kp") or latest.values.get("kp_index", 0)

            print("\nLatest Reading:")
            print(f"  Timestamp: {latest.timestamp}")
            print(f"  Kp Index: {latest.values.get('kp_index')}")
            print(f"  Estimated Kp: {latest.values.get('estimated_kp')}")
            print(f"  Storm Level: {kp_to_storm_level(kp)}")
            print(f"  Source: {latest.source}")

            return True
        else:
            print("No readings received")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        await collector.close()


async def test_anomaly_detector():
    """Test anomaly detection"""
    print("\n" + "=" * 60)
    print("Testing Anomaly Detector")
    print("=" * 60)

    from datetime import datetime

    from continuum.sensors.anomaly.detector import AnomalyDetector
    from continuum.sensors.config import SensorConfig
    from continuum.sensors.schemas import DataSource, SensorReading, SensorType

    config = SensorConfig()
    detector = AnomalyDetector(config)

    # Create a fake storm reading
    storm_reading = SensorReading(
        timestamp=datetime.utcnow(),
        source=DataSource.NOAA_PLANETARY_KINDEX,
        sensor_type=SensorType.KINDEX,
        values={"kp_index": 7.0, "estimated_kp": 7.33},
        tenant_id="test",
    )

    print("Testing with Kp = 7.0 (should trigger G3 storm)")

    anomaly = detector.detect(storm_reading)

    if anomaly:
        print("\nAnomaly Detected!")
        print(f"  Type: {anomaly.anomaly_type}")
        print(f"  Severity: {anomaly.severity}")
        print(f"  Claim: {anomaly.shai_claim[:100]}...")
        return True
    else:
        print("No anomaly detected (unexpected)")
        return False


async def test_storage():
    """Test storage layer"""
    print("\n" + "=" * 60)
    print("Testing Storage Layer")
    print("=" * 60)

    from datetime import datetime
    from pathlib import Path

    from continuum.sensors.config import SensorConfig
    from continuum.sensors.schemas import DataSource, SensorReading, SensorType
    from continuum.sensors.storage import SensorStorage

    # Use temp database in home directory (Termux-compatible)
    config = SensorConfig()
    config.db_path = Path.home() / ".continuum" / "sensor_test.db"

    storage = SensorStorage(config)
    await storage.initialize()

    print(f"Database: {config.db_path}")

    # Store a reading
    reading = SensorReading(
        timestamp=datetime.utcnow(),
        source=DataSource.NOAA_PLANETARY_KINDEX,
        sensor_type=SensorType.KINDEX,
        values={"kp_index": 3.0, "estimated_kp": 2.67},
        tenant_id="test",
    )

    reading_id = await storage.store_reading(reading)
    print(f"Stored reading with ID: {reading_id}")

    # Query it back
    readings = await storage.get_readings(limit=1)
    if readings:
        print(f"Retrieved reading: Kp = {readings[0].values.get('kp_index')}")
        return True
    else:
        print("Failed to retrieve reading")
        return False


async def test_mcp_tools():
    """Test MCP tool execution"""
    print("\n" + "=" * 60)
    print("Testing MCP Tools")
    print("=" * 60)

    from continuum.sensors.mcp_tools import execute_sensor_tool, get_sensor_tool_schemas

    # Get available tools
    schemas = get_sensor_tool_schemas()
    print(f"Available tools: {list(schemas.keys())}")

    # Test sensor_status
    print("\nExecuting sensor_status...")
    result = await execute_sensor_tool("sensor_status", {})
    print(f"  Scheduler running: {result.get('scheduler_running')}")
    print(f"  Pi*Phi: {result.get('pi_phi')}")

    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  PLANETARY SENSOR AGGREGATOR - TEST SUITE")
    print("  Pi x Phi = 5.083203692315260")
    print("=" * 60)

    results = {}

    # Run tests
    results["NOAA Collector"] = await test_noaa_collector()
    results["Anomaly Detector"] = await test_anomaly_detector()
    results["Storage Layer"] = await test_storage()
    results["MCP Tools"] = await test_mcp_tools()

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    print(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
