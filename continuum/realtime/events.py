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
Event Definitions for Real-Time Sync
=====================================

Defines event types and data structures for WebSocket synchronization.

Event types:
- MEMORY_ADDED: New memory stored
- CONCEPT_LEARNED: New concept extracted
- DECISION_MADE: New decision recorded
- INSTANCE_JOINED: Instance connected
- INSTANCE_LEFT: Instance disconnected
- SYNC_REQUEST: Request full state sync
- HEARTBEAT: Keepalive ping

All events include:
- event_type: Type of event
- tenant_id: Tenant isolation
- timestamp: Event creation time
- instance_id: Originating instance (optional)
- data: Event-specific payload
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for real-time synchronization"""
    MEMORY_ADDED = "memory_added"
    CONCEPT_LEARNED = "concept_learned"
    DECISION_MADE = "decision_made"
    INSTANCE_JOINED = "instance_joined"
    INSTANCE_LEFT = "instance_left"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class BaseEvent(BaseModel):
    """Base event structure for all sync events"""

    event_type: EventType = Field(
        ...,
        description="Type of event"
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier for isolation"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event creation timestamp (ISO format)"
    )
    instance_id: Optional[str] = Field(
        None,
        description="Originating instance ID"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific payload"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "heartbeat",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {}
            }
        }

    def to_json(self) -> str:
        """Serialize event to JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'BaseEvent':
        """Deserialize event from JSON string"""
        return cls.model_validate_json(json_str)


class MemoryEvent(BaseEvent):
    """Event fired when new memory is added"""

    event_type: EventType = Field(
        default=EventType.MEMORY_ADDED,
        description="Always 'memory_added'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "memory_added",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "message_id": 12345,
                    "user_message": "What is quantum entanglement?",
                    "ai_response": "Quantum entanglement is...",
                    "concepts_extracted": 3
                }
            }
        }


class ConceptEvent(BaseEvent):
    """Event fired when new concept is learned"""

    event_type: EventType = Field(
        default=EventType.CONCEPT_LEARNED,
        description="Always 'concept_learned'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "concept_learned",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "concept_name": "Quantum Entanglement",
                    "concept_type": "physics",
                    "description": "Correlation between particles...",
                    "confidence": 0.95
                }
            }
        }


class DecisionEvent(BaseEvent):
    """Event fired when decision is recorded"""

    event_type: EventType = Field(
        default=EventType.DECISION_MADE,
        description="Always 'decision_made'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "decision_made",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "decision": "Implement WebSocket sync",
                    "context": "Enable real-time coordination",
                    "rationale": "Improve multi-instance coherence"
                }
            }
        }


class InstanceEvent(BaseEvent):
    """Event fired when instance joins or leaves"""

    event_type: EventType = Field(
        ...,
        description="Either 'instance_joined' or 'instance_left'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "instance_joined",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "instance_name": "claude-20251206-100000",
                    "capabilities": ["memory", "learning", "sync"],
                    "version": "0.1.0"
                }
            }
        }


class SyncEvent(BaseEvent):
    """Event for state synchronization requests/responses"""

    event_type: EventType = Field(
        ...,
        description="Either 'sync_request' or 'sync_response'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "sync_response",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "state": {
                        "total_concepts": 12593,
                        "total_messages": 8472,
                        "last_activity": "2025-12-06T09:55:00.000Z"
                    }
                }
            }
        }


class HeartbeatEvent(BaseEvent):
    """Keepalive event to maintain connection"""

    event_type: EventType = Field(
        default=EventType.HEARTBEAT,
        description="Always 'heartbeat'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "heartbeat",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "status": "active",
                    "uptime_seconds": 3600
                }
            }
        }


class ErrorEvent(BaseEvent):
    """Event for error notifications"""

    event_type: EventType = Field(
        default=EventType.ERROR,
        description="Always 'error'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "error",
                "tenant_id": "default",
                "timestamp": "2025-12-06T10:00:00.000Z",
                "instance_id": "claude-20251206-100000",
                "data": {
                    "error_type": "connection_lost",
                    "message": "WebSocket connection dropped",
                    "recoverable": True
                }
            }
        }


def create_event(
    event_type: EventType,
    tenant_id: str,
    data: Dict[str, Any],
    instance_id: Optional[str] = None
) -> BaseEvent:
    """
    Factory function to create appropriate event type.

    Args:
        event_type: Type of event to create
        tenant_id: Tenant identifier
        data: Event-specific payload
        instance_id: Optional instance identifier

    Returns:
        Appropriate event subclass instance
    """
    event_classes = {
        EventType.MEMORY_ADDED: MemoryEvent,
        EventType.CONCEPT_LEARNED: ConceptEvent,
        EventType.DECISION_MADE: DecisionEvent,
        EventType.INSTANCE_JOINED: InstanceEvent,
        EventType.INSTANCE_LEFT: InstanceEvent,
        EventType.SYNC_REQUEST: SyncEvent,
        EventType.SYNC_RESPONSE: SyncEvent,
        EventType.HEARTBEAT: HeartbeatEvent,
        EventType.ERROR: ErrorEvent,
    }

    event_class = event_classes.get(event_type, BaseEvent)
    return event_class(
        event_type=event_type,
        tenant_id=tenant_id,
        instance_id=instance_id,
        data=data
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
