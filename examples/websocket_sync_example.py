#!/usr/bin/env python3
"""
WebSocket Sync Example
======================

Demonstrates real-time synchronization across multiple Claude instances.

This example shows:
1. Connecting to the WebSocket sync endpoint
2. Broadcasting events when memories are added
3. Receiving events from other instances
4. Handling reconnection on disconnect

Usage:
    # Terminal 1: Start CONTINUUM server
    python -m continuum.api.server

    # Terminal 2: Run first instance
    python examples/websocket_sync_example.py --instance claude-1

    # Terminal 3: Run second instance
    python examples/websocket_sync_example.py --instance claude-2

When one instance learns something, the other will receive the event in real-time.
"""

import asyncio
import json
import argparse
from datetime import datetime
from typing import Optional

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    exit(1)


class SyncClient:
    """Client for connecting to CONTINUUM WebSocket sync"""

    def __init__(
        self,
        url: str = "ws://localhost:8420/ws/sync",
        tenant_id: str = "default",
        instance_id: Optional[str] = None
    ):
        self.url = url
        self.tenant_id = tenant_id
        self.instance_id = instance_id or f"client-{datetime.now().timestamp()}"
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to WebSocket endpoint"""
        uri = f"{self.url}?tenant_id={self.tenant_id}&instance_id={self.instance_id}"
        print(f"[{self.instance_id}] Connecting to {uri}...")

        try:
            self.websocket = await websockets.connect(uri)
            self.running = True
            print(f"[{self.instance_id}] Connected successfully!")
            return True
        except Exception as e:
            print(f"[{self.instance_id}] Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print(f"[{self.instance_id}] Disconnected")

    async def send_event(self, event_type: str, data: dict):
        """Send event to other instances"""
        if not self.websocket:
            print(f"[{self.instance_id}] Not connected")
            return

        event = {
            "event_type": event_type,
            "tenant_id": self.tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "instance_id": self.instance_id,
            "data": data
        }

        try:
            await self.websocket.send(json.dumps(event))
            print(f"[{self.instance_id}] Sent {event_type}: {data}")
        except Exception as e:
            print(f"[{self.instance_id}] Failed to send event: {e}")

    async def receive_loop(self):
        """Receive and handle events from other instances"""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                event = json.loads(message)
                await self.handle_event(event)
            except websockets.exceptions.ConnectionClosed:
                print(f"[{self.instance_id}] Connection closed")
                break
            except Exception as e:
                print(f"[{self.instance_id}] Error receiving: {e}")
                break

    async def handle_event(self, event: dict):
        """Handle received event"""
        event_type = event.get("event_type")
        from_instance = event.get("instance_id", "unknown")
        data = event.get("data", {})

        # Skip events from self
        if from_instance == self.instance_id:
            return

        # Handle different event types
        if event_type == "memory_added":
            print(f"\n[{self.instance_id}] MEMORY from {from_instance}:")
            print(f"  User: {data.get('user_message', 'N/A')[:80]}...")
            print(f"  Concepts: {data.get('concepts_extracted', 0)}")

        elif event_type == "concept_learned":
            print(f"\n[{self.instance_id}] CONCEPT from {from_instance}:")
            print(f"  Name: {data.get('concept_name')}")
            print(f"  Type: {data.get('concept_type')}")

        elif event_type == "decision_made":
            print(f"\n[{self.instance_id}] DECISION from {from_instance}:")
            print(f"  Decision: {data.get('decision')}")

        elif event_type == "instance_joined":
            print(f"\n[{self.instance_id}] Instance {from_instance} joined")

        elif event_type == "instance_left":
            print(f"\n[{self.instance_id}] Instance {from_instance} left")

        elif event_type == "heartbeat":
            # Don't spam with heartbeats
            pass

        else:
            print(f"\n[{self.instance_id}] Event {event_type} from {from_instance}")

    async def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            await asyncio.sleep(25)  # Send before server's 30s interval
            if self.running:
                await self.send_event("heartbeat", {"status": "active"})

    async def run(self):
        """Run client with receive and heartbeat loops"""
        if not await self.connect():
            return

        # Start receive and heartbeat tasks
        receive_task = asyncio.create_task(self.receive_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())

        try:
            # Wait for receive loop to finish (on disconnect)
            await receive_task
        finally:
            # Cancel heartbeat
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            await self.disconnect()


async def demo_interaction(client: SyncClient):
    """Simulate some memory operations"""
    await asyncio.sleep(2)  # Let connection stabilize

    # Simulate learning a concept
    await client.send_event(
        "concept_learned",
        {
            "concept_name": "WebSocket Synchronization",
            "concept_type": "technology",
            "description": "Real-time event broadcasting across instances",
            "confidence": 0.95
        }
    )

    await asyncio.sleep(3)

    # Simulate adding a memory
    await client.send_event(
        "memory_added",
        {
            "message_id": 12345,
            "user_message": "How does WebSocket sync work?",
            "ai_response": "WebSocket sync enables real-time coordination...",
            "concepts_extracted": 3
        }
    )

    await asyncio.sleep(3)

    # Simulate making a decision
    await client.send_event(
        "decision_made",
        {
            "decision": "Use WebSocket for real-time sync",
            "context": "Multi-instance coordination",
            "rationale": "Enables instant state synchronization"
        }
    )


async def main():
    parser = argparse.ArgumentParser(description="WebSocket Sync Example")
    parser.add_argument(
        "--instance",
        default=None,
        help="Instance identifier (default: auto-generated)"
    )
    parser.add_argument(
        "--url",
        default="ws://localhost:8420/ws/sync",
        help="WebSocket URL"
    )
    parser.add_argument(
        "--tenant",
        default="default",
        help="Tenant ID"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo interaction after connecting"
    )

    args = parser.parse_args()

    # Create client
    client = SyncClient(
        url=args.url,
        tenant_id=args.tenant,
        instance_id=args.instance
    )

    # Run demo interaction if requested
    if args.demo:
        demo_task = asyncio.create_task(demo_interaction(client))

    # Run client (will run until disconnected or Ctrl+C)
    try:
        await client.run()
    except KeyboardInterrupt:
        print(f"\n[{client.instance_id}] Interrupted by user")
        await client.disconnect()

    if args.demo:
        try:
            await demo_task
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
