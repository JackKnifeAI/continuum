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
Strawberry GraphQL type definitions for CONTINUUM.

Maps Python dataclasses to GraphQL types using Strawberry decorators.
"""

import strawberry
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# CUSTOM SCALARS
# =============================================================================

# JSON scalar using strawberry.scalars if available, else fallback
try:
    from strawberry.scalars import JSON
except ImportError:
    # Fallback: use Dict[str, Any] as JSON type
    from typing import Dict, Any
    JSON = Dict[str, Any]

Vector = strawberry.scalar(
    List[float],
    name="Vector",
    description="Vector embedding (array of floats)",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

Cursor = strawberry.scalar(
    str,
    name="Cursor",
    description="Opaque cursor for pagination",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


# =============================================================================
# ENUMS
# =============================================================================

@strawberry.enum
class MemoryType(Enum):
    """Type of memory"""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM_EVENT = "system_event"
    DECISION = "decision"
    CONCEPT = "concept"


@strawberry.enum
class SearchType(Enum):
    """Search type"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@strawberry.enum
class ConceptRelationship(Enum):
    """Relationship between concepts"""
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CAUSED_BY = "caused_by"
    SIMILAR_TO = "similar_to"
    CONTRADICTS = "contradicts"
    CUSTOM = "custom"


@strawberry.enum
class OrderDirection(Enum):
    """Order direction"""
    ASC = "asc"
    DESC = "desc"


@strawberry.enum
class UserRole(Enum):
    """User role"""
    USER = "user"
    ADMIN = "admin"
    READONLY = "readonly"


@strawberry.enum
class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"


@strawberry.enum
class PeerStatus(Enum):
    """Federation peer status"""
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    UNREACHABLE = "unreachable"
    BLOCKED = "blocked"


@strawberry.enum
class SessionEventType(Enum):
    """Session event type"""
    CREATED = "created"
    UPDATED = "updated"
    ENDED = "ended"
    MESSAGE_ADDED = "message_added"
    CONCEPT_DISCOVERED = "concept_discovered"


@strawberry.enum
class SyncEventType(Enum):
    """Sync event type"""
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    PEER_CONNECTED = "peer_connected"
    PEER_DISCONNECTED = "peer_disconnected"


# =============================================================================
# INTERFACES
# =============================================================================

@strawberry.interface
class Node:
    """Common fields for all entities"""
    id: strawberry.ID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# PAGINATION TYPES
# =============================================================================

@strawberry.input
class PaginationInput:
    """Pagination input for cursor-based pagination"""
    first: Optional[int] = 20
    after: Optional[Cursor] = None
    last: Optional[int] = None
    before: Optional[Cursor] = None


@strawberry.type
class PageInfo:
    """Page information for pagination"""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[Cursor]
    end_cursor: Optional[Cursor]


# =============================================================================
# MEMORY TYPES
# =============================================================================

@strawberry.type
class Memory(Node):
    """A single memory item"""
    id: strawberry.ID
    content: str
    memory_type: MemoryType
    importance: float
    embedding: Optional[Vector]
    access_count: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime]
    tenant_id: str
    metadata: Optional[JSON] = None

    @strawberry.field
    async def concepts(self, info, limit: int = 10) -> List["Concept"]:
        """Associated concepts"""
        from .resolvers.memory_resolvers import resolve_memory_concepts
        return await resolve_memory_concepts(self, info, limit)

    @strawberry.field
    async def related_memories(
        self, info, limit: int = 10, threshold: float = 0.7
    ) -> List["Memory"]:
        """Related memories (semantic similarity)"""
        from .resolvers.memory_resolvers import resolve_related_memories
        return await resolve_related_memories(self, info, limit, threshold)

    @strawberry.field
    async def session(self, info) -> Optional["Session"]:
        """Session this memory belongs to"""
        from .resolvers.memory_resolvers import resolve_memory_session
        return await resolve_memory_session(self, info)


@strawberry.type
class MemoryEdge:
    """Memory edge"""
    cursor: Cursor
    node: Memory
    score: Optional[float] = None


@strawberry.type
class MemoryConnection:
    """Memory connection for pagination"""
    edges: List[MemoryEdge]
    page_info: PageInfo
    total_count: int


@strawberry.input
class MemoryFilter:
    """Filter options for memories"""
    memory_type: Optional[MemoryType] = None
    min_importance: Optional[float] = None
    concepts: Optional[List[str]] = None
    session_id: Optional[strawberry.ID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None


@strawberry.input
class CreateMemoryInput:
    """Input for creating a memory"""
    content: str
    memory_type: MemoryType
    importance: float = 0.5
    session_id: Optional[strawberry.ID] = None
    metadata: Optional[JSON] = None


@strawberry.input
class UpdateMemoryInput:
    """Input for updating a memory"""
    content: Optional[str] = None
    importance: Optional[float] = None
    metadata: Optional[JSON] = None


@strawberry.type
class SearchResult:
    """Search result for memories"""
    memory: Memory
    score: float
    matched_fields: List[str]
    highlights: List[str]


# =============================================================================
# CONCEPT TYPES
# =============================================================================

@strawberry.type
class Concept(Node):
    """A concept/entity in the knowledge graph"""
    id: strawberry.ID
    name: str
    description: Optional[str]
    confidence: float
    concept_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    tenant_id: str
    metadata: Optional[JSON] = None

    @strawberry.field
    async def memories(
        self, info, pagination: Optional[PaginationInput] = None
    ) -> MemoryConnection:
        """Associated memories"""
        from .resolvers.concept_resolvers import resolve_concept_memories
        return await resolve_concept_memories(self, info, pagination)

    @strawberry.field
    async def related_concepts(
        self,
        info,
        depth: int = 1,
        relationship: Optional[ConceptRelationship] = None,
    ) -> List["ConceptEdge"]:
        """Related concepts"""
        from .resolvers.concept_resolvers import resolve_related_concepts
        return await resolve_related_concepts(self, info, depth, relationship)


@strawberry.type
class ConceptEdge:
    """Edge between concepts"""
    from_concept: Concept = strawberry.field(name="from")
    to_concept: Concept = strawberry.field(name="to")
    relationship: ConceptRelationship
    label: Optional[str]
    strength: float
    metadata: Optional[JSON]
    created_at: datetime


@strawberry.type
class ConceptConnectionEdge:
    """Concept connection edge"""
    cursor: Cursor
    node: Concept


@strawberry.type
class ConceptConnection:
    """Concept connection for pagination"""
    edges: List[ConceptConnectionEdge]
    page_info: PageInfo
    total_count: int


@strawberry.input
class ConceptFilter:
    """Filter options for concepts"""
    concept_type: Optional[str] = None
    min_confidence: Optional[float] = None
    search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class CreateConceptInput:
    """Input for creating a concept"""
    name: str
    description: Optional[str] = None
    confidence: float = 0.8
    concept_type: Optional[str] = None
    metadata: Optional[JSON] = None


@strawberry.type
class ConceptGraph:
    """Concept graph structure"""
    root: Concept
    nodes: List[Concept]
    edges: List[ConceptEdge]
    depth: int
    node_count: int
    edge_count: int


# =============================================================================
# USER TYPES
# =============================================================================

@strawberry.type
class UserProfile:
    """User profile"""
    avatar: Optional[str]
    bio: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    metadata: Optional[JSON]


@strawberry.type
class UserSettings:
    """User settings"""
    realtime_sync: bool
    auto_save_interval: int
    default_search_type: SearchType
    max_results_per_query: int
    embedding_provider: Optional[str]
    custom: Optional[JSON]


@strawberry.type
class User(Node):
    """User account"""
    id: strawberry.ID
    username: str
    email: str
    display_name: Optional[str]
    role: UserRole
    profile: Optional[UserProfile]
    settings: Optional[UserSettings]
    memory_count: int
    concept_count: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    @strawberry.field
    async def sessions(
        self, info, pagination: Optional[PaginationInput] = None
    ) -> "SessionConnection":
        """Sessions"""
        from .resolvers.user_resolvers import resolve_user_sessions
        return await resolve_user_sessions(self, info, pagination)


@strawberry.type
class UserConnectionEdge:
    """User connection edge"""
    cursor: Cursor
    node: User


@strawberry.type
class UserConnection:
    """User connection for pagination"""
    edges: List[UserConnectionEdge]
    page_info: PageInfo
    total_count: int


@strawberry.input
class UserFilter:
    """Filter options for users"""
    role: Optional[UserRole] = None
    search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class UpdateProfileInput:
    """Input for updating user profile"""
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


@strawberry.input
class SettingsInput:
    """Input for updating user settings"""
    realtime_sync: Optional[bool] = None
    auto_save_interval: Optional[int] = None
    default_search_type: Optional[SearchType] = None
    max_results_per_query: Optional[int] = None
    embedding_provider: Optional[str] = None
    custom: Optional[JSON] = None


@strawberry.type
class Settings:
    """Settings type"""
    realtime_sync: bool
    auto_save_interval: int
    default_search_type: SearchType
    max_results_per_query: int
    embedding_provider: Optional[str]
    custom: Optional[JSON]


# =============================================================================
# SESSION TYPES
# =============================================================================

@strawberry.type
class Session(Node):
    """A conversation session"""
    id: strawberry.ID
    title: Optional[str]
    summary: Optional[str]
    status: SessionStatus
    message_count: int
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tenant_id: str
    metadata: Optional[JSON]

    @strawberry.field
    async def user(self, info) -> User:
        """User who owns this session"""
        from .resolvers.session_resolvers import resolve_session_user
        return await resolve_session_user(self, info)

    @strawberry.field
    async def memories(
        self, info, pagination: Optional[PaginationInput] = None
    ) -> MemoryConnection:
        """Memories in this session"""
        from .resolvers.session_resolvers import resolve_session_memories
        return await resolve_session_memories(self, info, pagination)

    @strawberry.field
    async def concepts(self, info, limit: int = 20) -> List[Concept]:
        """Concepts discovered in this session"""
        from .resolvers.session_resolvers import resolve_session_concepts
        return await resolve_session_concepts(self, info, limit)


@strawberry.type
class SessionConnectionEdge:
    """Session connection edge"""
    cursor: Cursor
    node: Session


@strawberry.type
class SessionConnection:
    """Session connection for pagination"""
    edges: List[SessionConnectionEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class SessionEvent:
    """Session event for subscriptions"""
    type: SessionEventType
    session: Session
    timestamp: datetime
    metadata: Optional[JSON]


# =============================================================================
# FEDERATION TYPES
# =============================================================================

@strawberry.type
class FederationPeer:
    """A federation peer node"""
    id: strawberry.ID
    url: str
    name: Optional[str]
    status: PeerStatus
    last_sync: Optional[datetime]
    shared_memories: int
    trust_score: float
    metadata: Optional[JSON]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class FederationStatus:
    """Federation status"""
    enabled: bool
    total_peers: int
    online_peers: int
    last_sync: Optional[datetime]
    synced_memories: int
    pending_sync: int


@strawberry.type
class SyncResult:
    """Sync result"""
    success: bool
    memories_synced: int
    concepts_synced: int
    duration_ms: float
    error: Optional[str]
    timestamp: datetime


@strawberry.type
class SyncEvent:
    """Sync event for subscriptions"""
    type: SyncEventType
    peer: FederationPeer
    result: Optional[SyncResult]
    timestamp: datetime


# =============================================================================
# LEARNING TYPES
# =============================================================================

@strawberry.input
class ConversationInput:
    """Input for learning from a conversation"""
    user_message: str
    ai_response: str
    session_id: Optional[strawberry.ID] = None
    metadata: Optional[JSON] = None


@strawberry.type
class LearnResult:
    """Result of learning operation"""
    concepts_extracted: int
    decisions_detected: int
    links_created: int
    compounds_found: int
    concepts: List[Concept]
    success: bool


# =============================================================================
# SYSTEM TYPES
# =============================================================================

@strawberry.type
class HealthStatus:
    """System health status"""
    status: str
    service: str
    version: str
    timestamp: datetime
    database: bool
    cache: bool


@strawberry.type
class SystemStats:
    """System statistics"""
    total_memories: int
    total_concepts: int
    total_users: int
    total_sessions: int
    api_requests_24h: int
    avg_query_time_ms: float

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
