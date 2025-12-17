"""
CONTINUUM API Module

REST API for multi-tenant AI memory infrastructure.
Provides endpoints for memory recall, learning, statistics, and message retrieval.
"""

from .server import app
from .schemas import (
    RecallRequest,
    RecallResponse,
    LearnRequest,
    LearnResponse,
    TurnRequest,
    TurnResponse,
    StatsResponse,
    EntitiesResponse,
    HealthResponse,
    MessageItem,
    MessagesResponse,
    MessageSearchRequest,
)
from .middleware import AnalyticsMiddleware

__all__ = [
    "app",
    "RecallRequest",
    "RecallResponse",
    "LearnRequest",
    "LearnResponse",
    "TurnRequest",
    "TurnResponse",
    "StatsResponse",
    "EntitiesResponse",
    "HealthResponse",
    "MessageItem",
    "MessagesResponse",
    "MessageSearchRequest",
    "AnalyticsMiddleware",
]
