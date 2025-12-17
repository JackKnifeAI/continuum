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
Synchronization Manager
=======================

Central manager for real-time WebSocket synchronization across instances.

Features:
- Connection tracking per tenant
- Event broadcasting with tenant isolation
- Subscription-based event handling
- Automatic reconnection support
- State synchronization

Usage:
    manager = SyncManager()

    # Connect new instance
    await manager.connect(websocket, tenant_id, instance_id)

    # Broadcast update
    event = MemoryEvent(tenant_id="default", data={...})
    await manager.broadcast_update(event)

    # Disconnect
    await manager.disconnect(websocket)

Thread-safe and supports multiple concurrent tenants.
"""

import asyncio
import logging
from typing import Dict, Set, Callable, Optional, Any
from datetime import datetime
from collections import defaultdict
from fastapi import WebSocket

from .events import BaseEvent, EventType, create_event

logger = logging.getLogger(__name__)


class ConnectionInfo:
    """Information about a connected WebSocket client"""

    def __init__(
        self,
        websocket: WebSocket,
        tenant_id: str,
        instance_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.tenant_id = tenant_id
        self.instance_id = instance_id or f"instance-{id(websocket)}"
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.message_count = 0

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "instance_id": self.instance_id,
            "tenant_id": self.tenant_id,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "message_count": self.message_count,
        }


class SyncManager:
    """
    Central manager for WebSocket synchronization.

    Tracks all connected instances per tenant and broadcasts updates
    with tenant isolation.

    Attributes:
        connections: Map of WebSocket -> ConnectionInfo
        tenant_connections: Map of tenant_id -> Set[WebSocket]
        event_handlers: Map of EventType -> Set[Callable]
    """

    def __init__(self):
        """Initialize sync manager"""
        self.connections: Dict[WebSocket, ConnectionInfo] = {}
        self.tenant_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.event_handlers: Dict[EventType, Set[Callable]] = defaultdict(set)
        self._lock = asyncio.Lock()

        logger.info("SyncManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        instance_id: Optional[str] = None
    ):
        """
        Register new WebSocket connection.

        Args:
            websocket: WebSocket connection
            tenant_id: Tenant identifier for isolation
            instance_id: Optional instance identifier

        Broadcasts INSTANCE_JOINED event to other instances in same tenant.
        """
        async with self._lock:
            # Create connection info
            conn_info = ConnectionInfo(websocket, tenant_id, instance_id)

            # Register connection
            self.connections[websocket] = conn_info
            self.tenant_connections[tenant_id].add(websocket)

            logger.info(
                f"Instance connected: {conn_info.instance_id} "
                f"(tenant: {tenant_id}, total: {len(self.connections)})"
            )

        # Broadcast join event to others in tenant (excluding this connection)
        join_event = create_event(
            EventType.INSTANCE_JOINED,
            tenant_id=tenant_id,
            instance_id=conn_info.instance_id,
            data={
                "instance_id": conn_info.instance_id,
                "connected_at": conn_info.connected_at.isoformat(),
                "capabilities": ["memory", "learning", "sync"],
            }
        )
        await self.broadcast_update(join_event, exclude={websocket})

    async def disconnect(self, websocket: WebSocket):
        """
        Unregister WebSocket connection.

        Args:
            websocket: WebSocket connection to remove

        Broadcasts INSTANCE_LEFT event to other instances in same tenant.
        """
        async with self._lock:
            conn_info = self.connections.get(websocket)
            if not conn_info:
                return

            tenant_id = conn_info.tenant_id
            instance_id = conn_info.instance_id

            # Remove connection
            self.tenant_connections[tenant_id].discard(websocket)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]

            del self.connections[websocket]

            logger.info(
                f"Instance disconnected: {instance_id} "
                f"(tenant: {tenant_id}, remaining: {len(self.connections)})"
            )

        # Broadcast leave event to others in tenant
        leave_event = create_event(
            EventType.INSTANCE_LEFT,
            tenant_id=tenant_id,
            instance_id=instance_id,
            data={
                "instance_id": instance_id,
                "disconnected_at": datetime.utcnow().isoformat(),
            }
        )
        await self.broadcast_update(leave_event)

    async def broadcast_update(
        self,
        event: BaseEvent,
        exclude: Optional[Set[WebSocket]] = None
    ):
        """
        Broadcast event to all instances in same tenant.

        Args:
            event: Event to broadcast
            exclude: Optional set of websockets to exclude from broadcast

        Only sends to instances with matching tenant_id.
        Handles disconnected clients gracefully.
        """
        exclude = exclude or set()
        tenant_id = event.tenant_id

        # Get connections for this tenant
        async with self._lock:
            target_connections = [
                (ws, self.connections[ws])
                for ws in self.tenant_connections.get(tenant_id, set())
                if ws not in exclude
            ]

        # Serialize event once
        event_json = event.to_json()

        # Track failed connections for cleanup
        failed = []

        # Send to all target connections
        for websocket, conn_info in target_connections:
            try:
                await websocket.send_text(event_json)
                conn_info.message_count += 1
                logger.debug(
                    f"Sent {event.event_type} to {conn_info.instance_id}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to send to {conn_info.instance_id}: {e}"
                )
                failed.append(websocket)

        # Clean up failed connections
        for websocket in failed:
            await self.disconnect(websocket)

        # Trigger event handlers
        await self._trigger_handlers(event)

    async def sync_state(
        self,
        websocket: WebSocket,
        state_data: Dict[str, Any]
    ):
        """
        Send state sync response to specific instance.

        Args:
            websocket: Target WebSocket connection
            state_data: State information to send

        Used for initial sync when instance connects.
        """
        conn_info = self.connections.get(websocket)
        if not conn_info:
            logger.warning("Attempted to sync state with unknown connection")
            return

        sync_event = create_event(
            EventType.SYNC_RESPONSE,
            tenant_id=conn_info.tenant_id,
            instance_id=conn_info.instance_id,
            data={"state": state_data}
        )

        try:
            await websocket.send_text(sync_event.to_json())
            logger.info(f"Sent state sync to {conn_info.instance_id}")
        except Exception as e:
            logger.error(f"Failed to send state sync: {e}")
            await self.disconnect(websocket)

    async def heartbeat(self, websocket: WebSocket):
        """
        Process heartbeat from instance.

        Args:
            websocket: WebSocket that sent heartbeat

        Updates last_heartbeat timestamp for connection tracking.
        """
        conn_info = self.connections.get(websocket)
        if conn_info:
            conn_info.update_heartbeat()
            logger.debug(f"Heartbeat from {conn_info.instance_id}")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[BaseEvent], None]
    ):
        """
        Subscribe to specific event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async callback function to handle event

        Handler will be called when events of this type are broadcast.

        Example:
            async def on_concept_learned(event: ConceptEvent):
                print(f"New concept: {event.data['concept_name']}")

            manager.subscribe(EventType.CONCEPT_LEARNED, on_concept_learned)
        """
        self.event_handlers[event_type].add(handler)
        logger.info(f"Subscribed handler to {event_type}")

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[BaseEvent], None]
    ):
        """
        Unsubscribe from specific event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        self.event_handlers[event_type].discard(handler)
        logger.info(f"Unsubscribed handler from {event_type}")

    async def _trigger_handlers(self, event: BaseEvent):
        """
        Trigger all registered handlers for event type.

        Args:
            event: Event to pass to handlers
        """
        handlers = self.event_handlers.get(event.event_type, set())
        for handler in handlers:
            try:
                # Support both sync and async handlers
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event.event_type}: {e}"
                )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current synchronization statistics.

        Returns:
            Dictionary with connection counts and stats per tenant
        """
        return {
            "total_connections": len(self.connections),
            "tenants": {
                tenant_id: len(connections)
                for tenant_id, connections in self.tenant_connections.items()
            },
            "connections": [
                conn_info.to_dict()
                for conn_info in self.connections.values()
            ]
        }

    def get_tenant_instances(self, tenant_id: str) -> list[str]:
        """
        Get list of instance IDs for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of instance IDs
        """
        return [
            self.connections[ws].instance_id
            for ws in self.tenant_connections.get(tenant_id, set())
        ]


# Global sync manager instance
_manager: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    """
    Get or create global sync manager instance.

    Returns:
        Global SyncManager instance
    """
    global _manager
    if _manager is None:
        _manager = SyncManager()
    return _manager


def subscribe(event_type: EventType):
    """
    Decorator to subscribe function to event type.

    Args:
        event_type: Type of event to subscribe to

    Example:
        @subscribe(EventType.CONCEPT_LEARNED)
        async def on_concept(event: ConceptEvent):
            print(f"Learned: {event.data['concept_name']}")
    """
    def decorator(func: Callable[[BaseEvent], None]):
        manager = get_sync_manager()
        manager.subscribe(event_type, func)
        return func
    return decorator


async def broadcast(event: BaseEvent):
    """
    Convenience function to broadcast event.

    Args:
        event: Event to broadcast

    Example:
        event = MemoryEvent(tenant_id="default", data={...})
        await broadcast(event)
    """
    manager = get_sync_manager()
    await manager.broadcast_update(event)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
