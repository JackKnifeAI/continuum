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
CONTINUUM Real-Time Synchronization
====================================

WebSocket-based real-time synchronization for multi-instance memory coordination.

Enables multiple Claude instances to stay synchronized, broadcasting:
- New memories added
- Concepts learned
- Decisions made
- Instance join/leave events

Usage:
    from continuum.realtime import SyncManager, WebSocketHandler, subscribe, broadcast

    # In your FastAPI app:
    manager = SyncManager()
    await manager.connect(websocket, tenant_id)
    await manager.broadcast_update(event)

    # Integration helpers:
    from continuum.realtime import broadcast_memory_added
    await broadcast_memory_added(tenant_id, user_msg, ai_msg, concepts=3)

Exports:
    SyncManager: Central manager for WebSocket connections
    WebSocketHandler: FastAPI WebSocket handler
    MemoryEvent: Memory addition event
    ConceptEvent: Concept learning event
    DecisionEvent: Decision recording event
    SyncEvent: Instance sync event
    subscribe: Decorator for event handlers
    broadcast: Helper to broadcast events
    broadcast_memory_added: Broadcast memory addition
    broadcast_concept_learned: Broadcast concept learning
    broadcast_decision_made: Broadcast decision made
"""

from .sync import SyncManager, subscribe, broadcast
from .websocket import WebSocketHandler
from .events import (
    EventType,
    BaseEvent,
    MemoryEvent,
    ConceptEvent,
    DecisionEvent,
    InstanceEvent,
    SyncEvent,
)
from .integration import (
    broadcast_memory_added,
    broadcast_concept_learned,
    broadcast_decision_made,
    broadcast_sync_event,
    get_connection_stats,
    get_tenant_instances,
)

__all__ = [
    "SyncManager",
    "WebSocketHandler",
    "EventType",
    "BaseEvent",
    "MemoryEvent",
    "ConceptEvent",
    "DecisionEvent",
    "InstanceEvent",
    "SyncEvent",
    "subscribe",
    "broadcast",
    "broadcast_memory_added",
    "broadcast_concept_learned",
    "broadcast_decision_made",
    "broadcast_sync_event",
    "get_connection_stats",
    "get_tenant_instances",
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
