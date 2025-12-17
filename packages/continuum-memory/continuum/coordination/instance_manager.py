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
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Instance Manager
================

Coordinates multiple instances accessing shared memory.

Features:
- Instance registration and tracking
- Heartbeat monitoring for liveness detection
- Inter-instance communication via warnings
- Automatic cleanup of stale instances
- Thread-safe file-based coordination
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .sync import FileLock


# Default configuration
DEFAULT_HEARTBEAT_INTERVAL = 30  # seconds
DEFAULT_STALE_THRESHOLD = 120    # seconds (2 minutes)


class InstanceManager:
    """
    Manage and coordinate multiple instances accessing shared resources.

    This class provides a file-based coordination mechanism for multiple
    processes or instances that need to share resources and communicate.

    Features:
    - Instance registration with metadata
    - Periodic heartbeat to prove liveness
    - Discovery of active instances
    - Broadcasting warnings to all instances
    - Automatic cleanup of stale instances

    Example:
        manager = InstanceManager(
            instance_id="instance-001",
            registry_path="/tmp/instances.json"
        )

        # Register this instance
        manager.register(metadata={"version": "1.0.0", "host": "server1"})

        # Periodically send heartbeats
        while running:
            manager.heartbeat()
            time.sleep(30)

        # Get all active instances
        active = manager.get_active_instances()
        for inst in active:
            print(f"Instance {inst['instance_id']} last seen {inst['last_heartbeat']}")

        # Broadcast a warning
        manager.broadcast_warning("Maintenance starting in 5 minutes")
    """

    def __init__(self,
                 instance_id: str,
                 registry_path: str = None,
                 heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
                 stale_threshold: int = DEFAULT_STALE_THRESHOLD):
        """
        Initialize the instance manager.

        Args:
            instance_id: Unique identifier for this instance
            registry_path: Path to the shared registry file
            heartbeat_interval: Seconds between heartbeats
            stale_threshold: Seconds before instance considered stale
        """
        self.instance_id = instance_id
        self.heartbeat_interval = heartbeat_interval
        self.stale_threshold = stale_threshold
        self.last_heartbeat = time.time()

        # Set registry path
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            # Default to XDG_RUNTIME_DIR or temp
            import tempfile
            runtime_dir = Path(tempfile.gettempdir()) / "continuum"
            runtime_dir.mkdir(parents=True, exist_ok=True)
            self.registry_path = runtime_dir / "instance_registry.json"

        # Ensure parent directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def register(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register this instance in the shared registry.

        Args:
            metadata: Optional metadata to store with the instance

        Returns:
            True if registration successful

        Example:
            manager.register(metadata={
                "version": "1.0.0",
                "host": "server1",
                "capabilities": ["reader", "writer"]
            })
        """
        with FileLock(self.registry_path):
            registry = self._load_registry()

            # Add or update this instance
            instance_data = {
                "instance_id": self.instance_id,
                "registered_at": datetime.now().isoformat(),
                "last_heartbeat": time.time(),
                "status": "active",
                "metadata": metadata or {}
            }

            # Remove old entry if exists
            registry["instances"] = [
                inst for inst in registry["instances"]
                if inst["instance_id"] != self.instance_id
            ]

            # Add new entry
            registry["instances"].append(instance_data)

            self._save_registry(registry)

        return True

    def heartbeat(self) -> bool:
        """
        Send heartbeat to prove this instance is still active.

        Returns:
            True if heartbeat sent successfully

        Example:
            # Send heartbeat every 30 seconds
            while running:
                manager.heartbeat()
                time.sleep(manager.heartbeat_interval)
        """
        self.last_heartbeat = time.time()

        if not self.registry_path.exists():
            return False

        with FileLock(self.registry_path):
            registry = self._load_registry()

            # Update our entry
            for instance in registry["instances"]:
                if instance["instance_id"] == self.instance_id:
                    instance["last_heartbeat"] = self.last_heartbeat
                    instance["status"] = "active"
                    break

            self._save_registry(registry)

        return True

    def get_active_instances(self) -> List[Dict[str, Any]]:
        """
        Get list of all active instances.

        An instance is considered active if its last heartbeat was within
        the stale_threshold.

        Returns:
            List of active instance dictionaries

        Example:
            active = manager.get_active_instances()
            print(f"Found {len(active)} active instances")
            for inst in active:
                print(f"  - {inst['instance_id']}: {inst['status']}")
        """
        if not self.registry_path.exists():
            return []

        with FileLock(self.registry_path, shared=True):
            registry = self._load_registry()

        now = time.time()
        active = []

        for instance in registry.get("instances", []):
            last_hb = instance.get("last_heartbeat", 0)
            if (now - last_hb) < self.stale_threshold:
                active.append(instance)

        return active

    def broadcast_warning(self, message: str, severity: str = "info") -> bool:
        """
        Broadcast a warning message to all instances.

        Args:
            message: Warning message to broadcast
            severity: Severity level (info, warning, error, critical)

        Returns:
            True if broadcast successful

        Example:
            manager.broadcast_warning(
                "System maintenance starting in 5 minutes",
                severity="warning"
            )
        """
        if not self.registry_path.exists():
            return False

        with FileLock(self.registry_path):
            registry = self._load_registry()

            if "warnings" not in registry:
                registry["warnings"] = []

            registry["warnings"].append({
                "from_instance": self.instance_id,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "severity": severity
            })

            self._save_registry(registry)

        return True

    def check_warnings(self, max_age_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Check for warnings from other instances.

        Args:
            max_age_minutes: Only return warnings from last N minutes

        Returns:
            List of recent warning dictionaries

        Example:
            warnings = manager.check_warnings()
            for warning in warnings:
                print(f"WARNING from {warning['from_instance']}: {warning['message']}")
        """
        if not self.registry_path.exists():
            return []

        with FileLock(self.registry_path, shared=True):
            registry = self._load_registry()

        recent_warnings = []
        now = datetime.now()

        for warning in registry.get("warnings", []):
            warn_time = datetime.fromisoformat(warning["timestamp"])
            if (now - warn_time) < timedelta(minutes=max_age_minutes):
                recent_warnings.append(warning)

        return recent_warnings

    def cleanup_stale_instances(self) -> int:
        """
        Remove instances that haven't sent heartbeat recently.

        Returns:
            Number of stale instances removed

        Example:
            removed = manager.cleanup_stale_instances()
            if removed > 0:
                print(f"Cleaned up {removed} stale instances")
        """
        if not self.registry_path.exists():
            return 0

        with FileLock(self.registry_path):
            registry = self._load_registry()
            now = time.time()

            # Count stale instances
            before_count = len(registry["instances"])

            # Filter out stale instances
            registry["instances"] = [
                inst for inst in registry["instances"]
                if (now - inst.get("last_heartbeat", 0)) < self.stale_threshold
            ]

            after_count = len(registry["instances"])
            removed = before_count - after_count

            if removed > 0:
                self._save_registry(registry)

        return removed

    def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific instance.

        Args:
            instance_id: ID of the instance to query

        Returns:
            Instance dictionary or None if not found

        Example:
            info = manager.get_instance_info("instance-001")
            if info:
                print(f"Instance status: {info['status']}")
        """
        if not self.registry_path.exists():
            return None

        with FileLock(self.registry_path, shared=True):
            registry = self._load_registry()

        for instance in registry.get("instances", []):
            if instance["instance_id"] == instance_id:
                return instance

        return None

    def unregister(self) -> bool:
        """
        Unregister this instance from the registry.

        Returns:
            True if unregistration successful

        Example:
            # On shutdown
            manager.unregister()
        """
        if not self.registry_path.exists():
            return False

        with FileLock(self.registry_path):
            registry = self._load_registry()

            # Remove this instance
            registry["instances"] = [
                inst for inst in registry["instances"]
                if inst["instance_id"] != self.instance_id
            ]

            self._save_registry(registry)

        return True

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file"""
        if not self.registry_path.exists():
            return {"instances": [], "warnings": []}

        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"instances": [], "warnings": []}

    def _save_registry(self, registry: Dict[str, Any]):
        """Save registry to file"""
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
