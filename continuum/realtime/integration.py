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
Integration Helpers for Real-Time Sync
=======================================

Helper functions to integrate WebSocket sync with existing memory operations.

Usage:
    from continuum.realtime.integration import broadcast_memory_added

    # After saving a message to memory
    await broadcast_memory_added(
        tenant_id="default",
        instance_id="claude-123",
        user_message="Hello",
        ai_response="Hi there!",
        concepts_extracted=2
    )

This module provides convenience functions to:
- Broadcast when memories are added
- Broadcast when concepts are learned
- Broadcast when decisions are made
- Trigger sync events from memory operations
"""

from typing import Optional, Dict, Any
import logging

from .events import EventType, create_event
from .sync import get_sync_manager

logger = logging.getLogger(__name__)


async def broadcast_memory_added(
    tenant_id: str,
    user_message: str,
    ai_response: str,
    concepts_extracted: int = 0,
    instance_id: Optional[str] = None,
    message_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast MEMORY_ADDED event after storing a message.

    Args:
        tenant_id: Tenant identifier
        user_message: User's message
        ai_response: AI's response
        concepts_extracted: Number of concepts extracted
        instance_id: Optional instance identifier
        message_id: Optional message ID from database
        metadata: Optional additional metadata

    Example:
        from continuum.realtime.integration import broadcast_memory_added

        # After memory.learn()
        await broadcast_memory_added(
            tenant_id="default",
            user_message=request.user_message,
            ai_response=request.ai_response,
            concepts_extracted=result.concepts_extracted,
            instance_id="claude-123"
        )
    """
    try:
        manager = get_sync_manager()

        data = {
            "user_message": user_message[:500],  # Truncate for bandwidth
            "ai_response": ai_response[:500],
            "concepts_extracted": concepts_extracted,
        }

        if message_id is not None:
            data["message_id"] = message_id

        if metadata:
            data["metadata"] = metadata

        event = create_event(
            EventType.MEMORY_ADDED,
            tenant_id=tenant_id,
            instance_id=instance_id,
            data=data
        )

        await manager.broadcast_update(event)
        logger.debug(f"Broadcasted memory_added for tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Failed to broadcast memory_added: {e}")
        # Don't raise - sync failure shouldn't break memory operations


async def broadcast_concept_learned(
    tenant_id: str,
    concept_name: str,
    concept_type: str = "concept",
    description: Optional[str] = None,
    confidence: Optional[float] = None,
    instance_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast CONCEPT_LEARNED event after extracting a concept.

    Args:
        tenant_id: Tenant identifier
        concept_name: Name of the concept
        concept_type: Type of concept (concept/entity/etc)
        description: Optional description
        confidence: Optional confidence score
        instance_id: Optional instance identifier
        metadata: Optional additional metadata

    Example:
        from continuum.realtime.integration import broadcast_concept_learned

        await broadcast_concept_learned(
            tenant_id="default",
            concept_name="Quantum Entanglement",
            concept_type="physics",
            description="Correlation between particles...",
            confidence=0.95
        )
    """
    try:
        manager = get_sync_manager()

        data = {
            "concept_name": concept_name,
            "concept_type": concept_type,
        }

        if description:
            data["description"] = description[:500]  # Truncate

        if confidence is not None:
            data["confidence"] = confidence

        if metadata:
            data["metadata"] = metadata

        event = create_event(
            EventType.CONCEPT_LEARNED,
            tenant_id=tenant_id,
            instance_id=instance_id,
            data=data
        )

        await manager.broadcast_update(event)
        logger.debug(f"Broadcasted concept_learned: {concept_name}")

    except Exception as e:
        logger.error(f"Failed to broadcast concept_learned: {e}")


async def broadcast_decision_made(
    tenant_id: str,
    decision: str,
    context: Optional[str] = None,
    rationale: Optional[str] = None,
    instance_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast DECISION_MADE event after recording a decision.

    Args:
        tenant_id: Tenant identifier
        decision: The decision text
        context: Optional context for decision
        rationale: Optional rationale/reasoning
        instance_id: Optional instance identifier
        metadata: Optional additional metadata

    Example:
        from continuum.realtime.integration import broadcast_decision_made

        await broadcast_decision_made(
            tenant_id="default",
            decision="Implement WebSocket sync",
            context="Multi-instance coordination",
            rationale="Enable real-time synchronization"
        )
    """
    try:
        manager = get_sync_manager()

        data = {
            "decision": decision[:500],  # Truncate
        }

        if context:
            data["context"] = context[:500]

        if rationale:
            data["rationale"] = rationale[:500]

        if metadata:
            data["metadata"] = metadata

        event = create_event(
            EventType.DECISION_MADE,
            tenant_id=tenant_id,
            instance_id=instance_id,
            data=data
        )

        await manager.broadcast_update(event)
        logger.debug(f"Broadcasted decision_made: {decision}")

    except Exception as e:
        logger.error(f"Failed to broadcast decision_made: {e}")


async def broadcast_sync_event(
    tenant_id: str,
    event_type: EventType,
    data: Dict[str, Any],
    instance_id: Optional[str] = None
):
    """
    Generic broadcast helper for custom events.

    Args:
        tenant_id: Tenant identifier
        event_type: Type of event to broadcast
        data: Event data payload
        instance_id: Optional instance identifier

    Example:
        from continuum.realtime.integration import broadcast_sync_event
        from continuum.realtime import EventType

        await broadcast_sync_event(
            tenant_id="default",
            event_type=EventType.SYNC_REQUEST,
            data={"request_type": "full_state"}
        )
    """
    try:
        manager = get_sync_manager()

        event = create_event(
            event_type,
            tenant_id=tenant_id,
            instance_id=instance_id,
            data=data
        )

        await manager.broadcast_update(event)
        logger.debug(f"Broadcasted {event_type}")

    except Exception as e:
        logger.error(f"Failed to broadcast {event_type}: {e}")


def get_connection_stats() -> Dict[str, Any]:
    """
    Get current sync connection statistics.

    Returns:
        Dictionary with connection counts and stats

    Example:
        from continuum.realtime.integration import get_connection_stats

        stats = get_connection_stats()
        print(f"Connected instances: {stats['total_connections']}")
    """
    try:
        manager = get_sync_manager()
        return manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get connection stats: {e}")
        return {
            "total_connections": 0,
            "tenants": {},
            "connections": [],
            "error": str(e)
        }


def get_tenant_instances(tenant_id: str) -> list[str]:
    """
    Get list of connected instance IDs for a tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        List of instance IDs

    Example:
        from continuum.realtime.integration import get_tenant_instances

        instances = get_tenant_instances("default")
        print(f"Connected: {', '.join(instances)}")
    """
    try:
        manager = get_sync_manager()
        return manager.get_tenant_instances(tenant_id)
    except Exception as e:
        logger.error(f"Failed to get tenant instances: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
