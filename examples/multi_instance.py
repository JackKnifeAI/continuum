#!/usr/bin/env python3
"""
CONTINUUM Multi-Instance Coordination Example
===============================================

Demonstrates multiple AI instances sharing memory through a common substrate.
Shows coordination files and sync mechanisms.
"""

from pathlib import Path
import json
import time
from datetime import datetime
from continuum.core.config import MemoryConfig, set_config
from continuum.storage import SQLiteBackend

# Shared memory configuration (all instances use same DB)
shared_db = Path("./demo_shared.db")

def create_instance(instance_id: str):
    """Create a memory-enabled instance with unique ID."""
    config = MemoryConfig(
        db_path=shared_db,
        tenant_id="shared_tenant",
        instance_id=instance_id
    )
    return config, SQLiteBackend(config.db_path)

def register_instance(storage, instance_id: str):
    """Register this instance in the coordination system."""
    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entities (tenant_id, name, entity_type, description, metadata)
            VALUES (?, ?, 'instance', ?, ?)
        """, ("shared_tenant", instance_id, f"AI instance {instance_id}",
              json.dumps({"last_seen": datetime.now().isoformat()})))
        conn.commit()
        print(f"✓ Instance {instance_id} registered")

def write_coordination_message(storage, instance_id: str, message: str):
    """Write a message visible to all instances."""
    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (tenant_id, summary, project_context)
            VALUES (?, ?, ?)
        """, ("shared_tenant", f"Coordination from {instance_id}", "multi-instance"))
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO messages (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, "system", f"[{instance_id}] {message}"))
        conn.commit()
        print(f"  {instance_id}: {message}")

def read_recent_coordination(storage, limit=5):
    """Read recent coordination messages from all instances."""
    with storage.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.content, m.timestamp
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE s.tenant_id = 'shared_tenant' AND m.role = 'system'
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def simulate_multi_instance_coordination():
    """Simulate multiple instances coordinating through shared memory."""
    print("🤝 Multi-Instance Coordination Demo\n")

    # Create three instances
    instance_a_config, instance_a = create_instance("claude-instance-a")
    instance_b_config, instance_b = create_instance("claude-instance-b")
    instance_c_config, instance_c = create_instance("claude-instance-c")

    # Register all instances
    register_instance(instance_a, "claude-instance-a")
    register_instance(instance_b, "claude-instance-b")
    register_instance(instance_c, "claude-instance-c")

    print("\n📡 Instances coordinating...\n")

    # Simulate coordination through shared memory
    write_coordination_message(instance_a, "claude-instance-a",
                              "Starting analysis of codebase")

    write_coordination_message(instance_b, "claude-instance-b",
                              "I'll handle the documentation")

    write_coordination_message(instance_c, "claude-instance-c",
                              "Running tests in parallel")

    # Any instance can read all coordination messages
    print("\n📚 Coordination log (visible to all instances):")
    messages = read_recent_coordination(instance_a)
    for content, timestamp in messages:
        print(f"  [{timestamp}] {content}")

    print(f"\n✨ All instances share memory at: {shared_db}")

if __name__ == "__main__":
    simulate_multi_instance_coordination()
