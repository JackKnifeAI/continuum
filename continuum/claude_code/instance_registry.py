#!/usr/bin/env python3
"""
CONTINUUM - Claude Code Instance Registry
==========================================

Tracks running Claude Code instances to coordinate server lifecycle.

Reference-counted system:
- First instance starts server
- Last instance stops server
- No message loss, all instances learn before shutdown

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import fcntl
import json
import os
import time
from pathlib import Path
from typing import List, Optional


class InstanceRegistry:
    """
    Thread-safe registry of running Claude Code instances.

    Uses file-based locking for cross-process coordination.
    Each instance registers with a unique PID.
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize instance registry.

        Args:
            registry_dir: Directory for registry files (default: ~/.continuum/instances)
        """
        if registry_dir is None:
            registry_dir = Path.home() / ".continuum" / "instances"

        self.registry_dir = registry_dir
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "registry.json"
        self.lock_file = self.registry_dir / "registry.lock"

        self.pid = os.getpid()
        self.instance_id = f"claude-{self.pid}-{int(time.time())}"

    def _acquire_lock(self, lock_fd):
        """Acquire exclusive lock (blocks until available)."""
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

    def _release_lock(self, lock_fd):
        """Release lock."""
        fcntl.flock(lock_fd, fcntl.LOCK_UN)

    def _read_registry(self) -> dict:
        """Read registry data (must hold lock)."""
        if not self.registry_file.exists():
            return {"instances": [], "version": "1.0"}

        try:
            with open(self.registry_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted, start fresh
            return {"instances": [], "version": "1.0"}

    def _write_registry(self, data: dict):
        """Write registry data (must hold lock)."""
        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2)

    def _clean_stale_instances(self, instances: List[dict]) -> List[dict]:
        """Remove instances with dead PIDs."""
        active = []
        for instance in instances:
            pid = instance.get("pid")
            if pid and self._is_process_alive(pid):
                active.append(instance)
        return active

    def _is_process_alive(self, pid: int) -> bool:
        """Check if process with given PID is running."""
        try:
            # Send signal 0 (doesn't actually send signal, just checks if process exists)
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def register(self) -> bool:
        """
        Register this instance.

        Returns:
            True if this is the first instance (should start server)
            False if other instances already running
        """
        with open(self.lock_file, "w") as lock_fd:
            self._acquire_lock(lock_fd)

            try:
                data = self._read_registry()
                instances = self._clean_stale_instances(data.get("instances", []))

                # Check if already registered (shouldn't happen, but defensive)
                if any(inst["instance_id"] == self.instance_id for inst in instances):
                    return len(instances) == 1

                # Add this instance
                instances.append({
                    "instance_id": self.instance_id,
                    "pid": self.pid,
                    "start_time": time.time(),
                    "cwd": os.getcwd(),
                })

                data["instances"] = instances
                self._write_registry(data)

                # Return True if first instance
                return len(instances) == 1

            finally:
                self._release_lock(lock_fd)

    def unregister(self) -> bool:
        """
        Unregister this instance.

        Returns:
            True if this was the last instance (should stop server)
            False if other instances still running
        """
        with open(self.lock_file, "w") as lock_fd:
            self._acquire_lock(lock_fd)

            try:
                data = self._read_registry()
                instances = self._clean_stale_instances(data.get("instances", []))

                # Remove this instance
                instances = [
                    inst for inst in instances
                    if inst["instance_id"] != self.instance_id
                ]

                data["instances"] = instances
                self._write_registry(data)

                # Return True if last instance
                return len(instances) == 0

            finally:
                self._release_lock(lock_fd)

    def count_instances(self) -> int:
        """
        Count active instances.

        Returns:
            Number of running Claude Code instances
        """
        with open(self.lock_file, "w") as lock_fd:
            self._acquire_lock(lock_fd)

            try:
                data = self._read_registry()
                instances = self._clean_stale_instances(data.get("instances", []))

                # Update registry with cleaned list
                data["instances"] = instances
                self._write_registry(data)

                return len(instances)

            finally:
                self._release_lock(lock_fd)

    def get_instances(self) -> List[dict]:
        """
        Get list of active instances.

        Returns:
            List of instance info dicts
        """
        with open(self.lock_file, "w") as lock_fd:
            self._acquire_lock(lock_fd)

            try:
                data = self._read_registry()
                instances = self._clean_stale_instances(data.get("instances", []))

                # Update registry with cleaned list
                data["instances"] = instances
                self._write_registry(data)

                return instances

            finally:
                self._release_lock(lock_fd)


# Singleton instance for convenience
_default_registry: Optional[InstanceRegistry] = None

def get_registry() -> InstanceRegistry:
    """Get default instance registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = InstanceRegistry()
    return _default_registry
