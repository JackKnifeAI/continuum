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
Main GraphQL schema with Query, Mutation, and Subscription classes.
"""

import strawberry
from typing import List, Optional, AsyncGenerator
from datetime import datetime

from .types import (
    Memory, MemoryConnection, MemoryFilter, CreateMemoryInput, UpdateMemoryInput,
    SearchResult, SearchType,
    Concept, ConceptConnection, ConceptFilter, CreateConceptInput, ConceptGraph,
    ConceptRelationship, ConceptEdge,
    User, UserConnection, UserFilter, UpdateProfileInput, SettingsInput, Settings,
    Session, SessionConnection, SessionStatus,
    FederationPeer, FederationStatus, SyncResult,
    ConversationInput, LearnResult,
    HealthStatus, SystemStats,
    PaginationInput,
    SessionEvent, SyncEvent,
)
from .auth.permissions import admin_only, authenticated


@strawberry.type
class Query:
    """GraphQL queries"""

    # ==========================================================================
    # MEMORY QUERIES
    # ==========================================================================

    @strawberry.field
    @authenticated
    async def memory(self, info, id: strawberry.ID) -> Optional[Memory]:
        """Get a single memory by ID"""
        loader = info.context["loaders"]["memory"]
        return await loader.load(id)

    @strawberry.field
    @authenticated
    async def memories(
        self,
        info,
        filter: Optional[MemoryFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> MemoryConnection:
        """List memories with filtering and pagination"""
        from .resolvers.query_resolvers import resolve_memories
        return await resolve_memories(info, filter, pagination)

    @strawberry.field
    @authenticated
    async def search_memories(
        self,
        info,
        query: str,
        type: SearchType = SearchType.SEMANTIC,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[SearchResult]:
        """Search memories"""
        from .resolvers.query_resolvers import resolve_search_memories
        return await resolve_search_memories(info, query, type, limit, threshold)

    # ==========================================================================
    # CONCEPT QUERIES
    # ==========================================================================

    @strawberry.field
    @authenticated
    async def concept(self, info, id: strawberry.ID) -> Optional[Concept]:
        """Get a single concept by ID"""
        loader = info.context["loaders"]["concept"]
        return await loader.load(id)

    @strawberry.field
    @authenticated
    async def concepts(
        self,
        info,
        filter: Optional[ConceptFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> ConceptConnection:
        """List concepts"""
        from .resolvers.query_resolvers import resolve_concepts
        return await resolve_concepts(info, filter, pagination)

    @strawberry.field
    @authenticated
    async def concept_graph(
        self,
        info,
        root_id: strawberry.ID,
        depth: int = 2,
        relationship: Optional[ConceptRelationship] = None,
    ) -> Optional[ConceptGraph]:
        """Get concept graph"""
        from .resolvers.query_resolvers import resolve_concept_graph
        return await resolve_concept_graph(info, root_id, depth, relationship)

    # ==========================================================================
    # USER QUERIES
    # ==========================================================================

    @strawberry.field
    @authenticated
    async def me(self, info) -> User:
        """Get current authenticated user"""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")

        loader = info.context["loaders"]["user"]
        user = await loader.load(user_id)
        if not user:
            raise Exception("User not found")
        return user

    @strawberry.field
    @admin_only
    async def user(self, info, id: strawberry.ID) -> Optional[User]:
        """Get a user by ID (admin only)"""
        loader = info.context["loaders"]["user"]
        return await loader.load(id)

    @strawberry.field
    @admin_only
    async def users(
        self,
        info,
        filter: Optional[UserFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> UserConnection:
        """List users (admin only)"""
        from .resolvers.query_resolvers import resolve_users
        return await resolve_users(info, filter, pagination)

    # ==========================================================================
    # SESSION QUERIES
    # ==========================================================================

    @strawberry.field
    @authenticated
    async def session(self, info, id: strawberry.ID) -> Optional[Session]:
        """Get a session by ID"""
        loader = info.context["loaders"]["session"]
        return await loader.load(id)

    @strawberry.field
    @authenticated
    async def sessions(
        self,
        info,
        limit: int = 10,
        status: Optional[SessionStatus] = None,
    ) -> List[Session]:
        """List sessions for current user"""
        from .resolvers.query_resolvers import resolve_sessions
        return await resolve_sessions(info, limit, status)

    @strawberry.field
    @authenticated
    async def current_session(self, info) -> Optional[Session]:
        """Get current active session"""
        from .resolvers.query_resolvers import resolve_current_session
        return await resolve_current_session(info)

    # ==========================================================================
    # FEDERATION QUERIES
    # ==========================================================================

    @strawberry.field
    @authenticated
    async def federation_peers(self, info) -> List[FederationPeer]:
        """List federation peers"""
        from .resolvers.federation_resolvers import resolve_federation_peers
        return await resolve_federation_peers(info)

    @strawberry.field
    @authenticated
    async def federation_status(self, info) -> FederationStatus:
        """Get federation status"""
        from .resolvers.federation_resolvers import resolve_federation_status
        return await resolve_federation_status(info)

    # ==========================================================================
    # SYSTEM QUERIES
    # ==========================================================================

    @strawberry.field
    async def health(self, info) -> HealthStatus:
        """Health check"""
        return HealthStatus(
            status="healthy",
            service="continuum-graphql",
            version="0.1.0",
            timestamp=datetime.now(),
            database=True,
            cache=True,
        )

    @strawberry.field
    @authenticated
    async def stats(self, info) -> SystemStats:
        """System statistics"""
        from .resolvers.query_resolvers import resolve_stats
        return await resolve_stats(info)


@strawberry.type
class Mutation:
    """GraphQL mutations"""

    # ==========================================================================
    # MEMORY MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def create_memory(self, info, input: CreateMemoryInput) -> Memory:
        """Create a new memory"""
        from .resolvers.mutation_resolvers import resolve_create_memory
        return await resolve_create_memory(info, input)

    @strawberry.mutation
    @authenticated
    async def update_memory(
        self, info, id: strawberry.ID, input: UpdateMemoryInput
    ) -> Memory:
        """Update an existing memory"""
        from .resolvers.mutation_resolvers import resolve_update_memory
        return await resolve_update_memory(info, id, input)

    @strawberry.mutation
    @authenticated
    async def delete_memory(self, info, id: strawberry.ID) -> bool:
        """Delete a memory"""
        from .resolvers.mutation_resolvers import resolve_delete_memory
        return await resolve_delete_memory(info, id)

    @strawberry.mutation
    @authenticated
    async def merge_memories(
        self, info, source_ids: List[strawberry.ID], target_id: strawberry.ID
    ) -> Memory:
        """Merge multiple memories into one"""
        from .resolvers.mutation_resolvers import resolve_merge_memories
        return await resolve_merge_memories(info, source_ids, target_id)

    # ==========================================================================
    # CONCEPT MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def create_concept(self, info, input: CreateConceptInput) -> Concept:
        """Create a new concept"""
        from .resolvers.mutation_resolvers import resolve_create_concept
        return await resolve_create_concept(info, input)

    @strawberry.mutation
    @authenticated
    async def link_concepts(
        self,
        info,
        source_id: strawberry.ID,
        target_id: strawberry.ID,
        relationship: ConceptRelationship,
        label: Optional[str] = None,
        strength: float = 0.8,
    ) -> ConceptEdge:
        """Link two concepts"""
        from .resolvers.mutation_resolvers import resolve_link_concepts
        return await resolve_link_concepts(
            info, source_id, target_id, relationship, label, strength
        )

    @strawberry.mutation
    @authenticated
    async def unlink_concepts(
        self, info, source_id: strawberry.ID, target_id: strawberry.ID
    ) -> bool:
        """Unlink two concepts"""
        from .resolvers.mutation_resolvers import resolve_unlink_concepts
        return await resolve_unlink_concepts(info, source_id, target_id)

    # ==========================================================================
    # SESSION MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def start_session(
        self, info, title: Optional[str] = None, metadata: Optional[str] = None
    ) -> Session:
        """Start a new session"""
        from .resolvers.mutation_resolvers import resolve_start_session
        return await resolve_start_session(info, title, metadata)

    @strawberry.mutation
    @authenticated
    async def end_session(
        self, info, id: strawberry.ID, summary: Optional[str] = None
    ) -> Session:
        """End a session"""
        from .resolvers.mutation_resolvers import resolve_end_session
        return await resolve_end_session(info, id, summary)

    # ==========================================================================
    # LEARNING MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def learn(self, info, conversation: ConversationInput) -> LearnResult:
        """Learn from a conversation"""
        from .resolvers.mutation_resolvers import resolve_learn
        return await resolve_learn(info, conversation)

    # ==========================================================================
    # FEDERATION MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def sync_memories(
        self, info, peer_url: str, memory_ids: Optional[List[strawberry.ID]] = None
    ) -> SyncResult:
        """Sync memories with a peer"""
        from .resolvers.mutation_resolvers import resolve_sync_memories
        return await resolve_sync_memories(info, peer_url, memory_ids)

    # ==========================================================================
    # USER MUTATIONS
    # ==========================================================================

    @strawberry.mutation
    @authenticated
    async def update_profile(self, info, input: UpdateProfileInput) -> User:
        """Update user profile"""
        from .resolvers.mutation_resolvers import resolve_update_profile
        return await resolve_update_profile(info, input)

    @strawberry.mutation
    @authenticated
    async def update_settings(self, info, input: SettingsInput) -> Settings:
        """Update user settings"""
        from .resolvers.mutation_resolvers import resolve_update_settings
        return await resolve_update_settings(info, input)


@strawberry.type
class Subscription:
    """GraphQL subscriptions"""

    @strawberry.subscription
    @authenticated
    async def memory_created(
        self,
        info,
        memory_type: Optional[str] = None,
        session_id: Optional[strawberry.ID] = None,
    ) -> AsyncGenerator[Memory, None]:
        """Subscribe to new memories"""
        from .resolvers.subscription_resolvers import subscribe_memory_created
        async for memory in subscribe_memory_created(info, memory_type, session_id):
            yield memory

    @strawberry.subscription
    @authenticated
    async def concept_discovered(self, info, concept_type: Optional[str] = None) -> AsyncGenerator[Concept, None]:
        """Subscribe to newly discovered concepts"""
        from .resolvers.subscription_resolvers import subscribe_concept_discovered
        async for concept in subscribe_concept_discovered(info, concept_type):
            yield concept

    @strawberry.subscription
    @authenticated
    async def federation_sync(self, info, peer_id: Optional[strawberry.ID] = None) -> AsyncGenerator[SyncEvent, None]:
        """Subscribe to federation sync events"""
        from .resolvers.subscription_resolvers import subscribe_federation_sync
        async for event in subscribe_federation_sync(info, peer_id):
            yield event

    @strawberry.subscription
    @authenticated
    async def session_activity(self, info, session_id: Optional[strawberry.ID] = None) -> AsyncGenerator[SessionEvent, None]:
        """Subscribe to session activity"""
        from .resolvers.subscription_resolvers import subscribe_session_activity
        async for event in subscribe_session_activity(info, session_id):
            yield event


# Build the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
