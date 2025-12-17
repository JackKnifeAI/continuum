"""
CONTINUUM Coordination Module
==============================

Multi-instance coordination and synchronization.

Features:
- Instance registration and discovery
- Heartbeat monitoring
- Inter-instance communication
- Conflict detection and resolution
- Stale instance cleanup

Usage:
    from continuum.coordination import InstanceManager

    manager = InstanceManager(
        instance_id="my-instance-123",
        registry_path="/path/to/registry.json"
    )

    # Register this instance
    manager.register()

    # Send periodic heartbeats
    manager.heartbeat()

    # Check for other active instances
    active = manager.get_active_instances()
    print(f"Active instances: {len(active)}")

    # Broadcast warning to all instances
    manager.broadcast_warning("System maintenance in 5 minutes")

    # Check for warnings from others
    warnings = manager.check_warnings()
"""

from .instance_manager import InstanceManager
from .sync import FileLock, synchronized

__all__ = ['InstanceManager', 'FileLock', 'synchronized']
