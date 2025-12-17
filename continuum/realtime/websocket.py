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
WebSocket Handler for FastAPI
==============================

WebSocket endpoint handler for real-time synchronization.

Features:
- Connection lifecycle management
- Heartbeat/keepalive (30s interval)
- Automatic reconnection support
- Message routing to sync manager
- Error handling and cleanup

Usage in FastAPI:
    from fastapi import WebSocket
    from continuum.realtime import WebSocketHandler

    @app.websocket("/ws/sync")
    async def websocket_endpoint(
        websocket: WebSocket,
        tenant_id: str,
        instance_id: Optional[str] = None
    ):
        handler = WebSocketHandler()
        await handler.handle(websocket, tenant_id, instance_id)

Heartbeat protocol:
- Server sends heartbeat every 30s
- Client should respond with heartbeat
- Connection closed if no response for 90s
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .sync import get_sync_manager, SyncManager
from .events import (
    BaseEvent,
    EventType,
    create_event,
    HeartbeatEvent,
)

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Handles WebSocket connections for real-time sync.

    Manages connection lifecycle, heartbeats, and message routing.
    """

    # Configuration
    HEARTBEAT_INTERVAL = 30.0  # Seconds between heartbeats
    HEARTBEAT_TIMEOUT = 90.0   # Seconds before considering connection dead

    def __init__(self, sync_manager: Optional[SyncManager] = None):
        """
        Initialize WebSocket handler.

        Args:
            sync_manager: Optional SyncManager instance (uses global if None)
        """
        self.sync_manager = sync_manager or get_sync_manager()

    async def handle(
        self,
        websocket: WebSocket,
        tenant_id: str,
        instance_id: Optional[str] = None
    ):
        """
        Handle WebSocket connection lifecycle.

        Args:
            websocket: WebSocket connection
            tenant_id: Tenant identifier for isolation
            instance_id: Optional instance identifier

        Manages:
        - Connection acceptance
        - Registration with sync manager
        - Message receiving and routing
        - Heartbeat monitoring
        - Disconnection cleanup
        """
        # Accept connection
        await websocket.accept()
        logger.info(f"WebSocket accepted for tenant: {tenant_id}")

        # Register with sync manager
        await self.sync_manager.connect(websocket, tenant_id, instance_id)

        # Get connection info
        conn_info = self.sync_manager.connections.get(websocket)
        if not conn_info:
            logger.error("Failed to get connection info after registration")
            await websocket.close()
            return

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(websocket, conn_info.instance_id, tenant_id)
        )

        try:
            # Main message receiving loop
            while True:
                # Receive message
                message = await websocket.receive_text()

                # Parse event
                try:
                    event = BaseEvent.from_json(message)
                    await self._handle_event(websocket, event)
                except ValidationError as e:
                    logger.warning(f"Invalid event format: {e}")
                    # Send error response
                    error_event = create_event(
                        EventType.ERROR,
                        tenant_id=tenant_id,
                        instance_id=conn_info.instance_id,
                        data={
                            "error_type": "invalid_format",
                            "message": str(e),
                            "recoverable": True
                        }
                    )
                    await websocket.send_text(error_event.to_json())
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    continue

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {conn_info.instance_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Cancel heartbeat
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            # Unregister from sync manager
            await self.sync_manager.disconnect(websocket)

            # Close connection if still open
            try:
                await websocket.close()
            except Exception:
                pass

    async def _handle_event(self, websocket: WebSocket, event: BaseEvent):
        """
        Handle received event from client.

        Args:
            websocket: WebSocket connection
            event: Parsed event

        Routes events to appropriate handlers:
        - HEARTBEAT: Update heartbeat timestamp
        - SYNC_REQUEST: Send current state
        - Others: Broadcast to other instances
        """
        conn_info = self.sync_manager.connections.get(websocket)
        if not conn_info:
            return

        logger.debug(
            f"Received {event.event_type} from {conn_info.instance_id}"
        )

        # Handle specific event types
        if event.event_type == EventType.HEARTBEAT:
            await self.sync_manager.heartbeat(websocket)

        elif event.event_type == EventType.SYNC_REQUEST:
            # Send current state
            state_data = await self._get_current_state(conn_info.tenant_id)
            await self.sync_manager.sync_state(websocket, state_data)

        else:
            # Broadcast to other instances (excluding sender)
            await self.sync_manager.broadcast_update(
                event,
                exclude={websocket}
            )

    async def _heartbeat_loop(
        self,
        websocket: WebSocket,
        instance_id: str,
        tenant_id: str
    ):
        """
        Send periodic heartbeat to maintain connection.

        Args:
            websocket: WebSocket connection
            instance_id: Instance identifier
            tenant_id: Tenant identifier

        Sends heartbeat every HEARTBEAT_INTERVAL seconds.
        Monitors last heartbeat from client and closes if timeout exceeded.
        """
        try:
            while True:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                # Check if connection still exists
                conn_info = self.sync_manager.connections.get(websocket)
                if not conn_info:
                    break

                # Check for heartbeat timeout
                time_since_heartbeat = (
                    datetime.utcnow() - conn_info.last_heartbeat
                ).total_seconds()

                if time_since_heartbeat > self.HEARTBEAT_TIMEOUT:
                    logger.warning(
                        f"Heartbeat timeout for {instance_id}, closing connection"
                    )
                    await websocket.close(code=1000, reason="Heartbeat timeout")
                    break

                # Send heartbeat
                heartbeat = HeartbeatEvent(
                    tenant_id=tenant_id,
                    instance_id=instance_id,
                    data={
                        "status": "active",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                try:
                    await websocket.send_text(heartbeat.to_json())
                    logger.debug(f"Sent heartbeat to {instance_id}")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    break

        except asyncio.CancelledError:
            logger.debug(f"Heartbeat loop cancelled for {instance_id}")
            raise
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")

    async def _get_current_state(self, tenant_id: str) -> dict:
        """
        Get current memory state for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dictionary with current state information

        TODO: Integrate with actual memory backend to get real stats
        """
        # Get sync stats
        stats = self.sync_manager.get_stats()
        tenant_instances = self.sync_manager.get_tenant_instances(tenant_id)

        # Build state response
        state = {
            "tenant_id": tenant_id,
            "connected_instances": tenant_instances,
            "total_instances": len(tenant_instances),
            "sync_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # TODO: Add memory stats from storage backend
        # from continuum.core.memory import MemoryCore
        # memory = MemoryCore(tenant_id=tenant_id)
        # state["memory_stats"] = memory.get_stats()

        return state


# Convenience function for FastAPI route
async def handle_websocket(
    websocket: WebSocket,
    tenant_id: str,
    instance_id: Optional[str] = None
):
    """
    Convenience function for FastAPI WebSocket route.

    Args:
        websocket: WebSocket connection
        tenant_id: Tenant identifier
        instance_id: Optional instance identifier

    Usage:
        @app.websocket("/ws/sync")
        async def websocket_endpoint(
            websocket: WebSocket,
            tenant_id: str = "default",
            instance_id: Optional[str] = None
        ):
            await handle_websocket(websocket, tenant_id, instance_id)
    """
    handler = WebSocketHandler()
    await handler.handle(websocket, tenant_id, instance_id)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
