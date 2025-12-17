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
CONTINUUM Supabase Client

Python wrapper for Supabase database operations.
Provides high-level interface for memory storage, retrieval, and knowledge graph operations.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
import logging

try:
    from supabase import create_client, Client
    from postgrest.exceptions import APIError
except ImportError:
    raise ImportError(
        "supabase-py not installed. Install with: pip install supabase-py"
    )

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    High-level client for CONTINUUM's Supabase database.

    Handles:
    - Memory CRUD operations
    - Semantic search
    - Knowledge graph operations
    - Session management
    - Federation sync
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        service_key: Optional[str] = None
    ):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL (or SUPABASE_URL env var)
            key: Supabase anon/public key (or SUPABASE_ANON_KEY env var)
            service_key: Supabase service role key (or SUPABASE_SERVICE_KEY env var)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.anon_key = key or os.getenv("SUPABASE_ANON_KEY")
        self.service_key = service_key or os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url:
            raise ValueError("SUPABASE_URL must be set")
        if not self.anon_key:
            raise ValueError("SUPABASE_ANON_KEY must be set")

        # Create client with anon key (for authenticated users)
        self.client: Client = create_client(self.url, self.anon_key)

        # Create admin client with service key (for admin operations)
        if self.service_key:
            self.admin_client: Client = create_client(self.url, self.service_key)
        else:
            self.admin_client = None
            logger.warning("Service key not provided - admin operations unavailable")

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    def set_auth(self, access_token: str) -> None:
        """
        Set authentication token for user operations.

        Args:
            access_token: JWT access token from Supabase auth
        """
        self.client.postgrest.auth(access_token)

    def sign_up(self, email: str, password: str, **metadata) -> Dict[str, Any]:
        """
        Sign up a new user.

        Args:
            email: User email
            password: User password
            **metadata: Additional user metadata

        Returns:
            Auth response with user and session
        """
        response = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": metadata}
        })
        return response

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in an existing user.

        Args:
            email: User email
            password: User password

        Returns:
            Auth response with user and session
        """
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response

    def sign_out(self) -> None:
        """Sign out current user."""
        self.client.auth.sign_out()

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def create_user_profile(
        self,
        user_id: UUID,
        username: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create or update user profile.

        Args:
            user_id: User UUID from auth.users
            username: Unique username
            display_name: Display name
            email: Email address
            **kwargs: Additional fields (metadata, settings, federation_id)

        Returns:
            Created user profile
        """
        data = {
            "id": str(user_id),
            "username": username,
            "display_name": display_name or username,
            "email": email,
            **kwargs
        }

        response = self.client.table("users").upsert(data).execute()
        return response.data[0] if response.data else {}

    def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user.

        Args:
            user_id: User UUID

        Returns:
            Statistics dictionary
        """
        response = self.client.rpc(
            "get_user_stats",
            {"user_id": str(user_id)}
        ).execute()
        return response.data[0] if response.data else {}

    # ========================================================================
    # MEMORY OPERATIONS
    # ========================================================================

    def create_memory(
        self,
        user_id: UUID,
        content: str,
        embedding: Optional[List[float]] = None,
        memory_type: str = "episodic",
        importance: float = 0.5,
        session_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "user"
    ) -> Dict[str, Any]:
        """
        Create a new memory.

        Args:
            user_id: User UUID
            content: Memory content text
            embedding: 1536-dimensional vector embedding
            memory_type: Type of memory (episodic, semantic, procedural)
            importance: Importance score (0-1)
            session_id: Optional session UUID
            metadata: Additional metadata
            source: Source of memory (user, inference, federation)

        Returns:
            Created memory
        """
        data = {
            "user_id": str(user_id),
            "content": content,
            "embedding": embedding,
            "memory_type": memory_type,
            "importance": importance,
            "session_id": str(session_id) if session_id else None,
            "metadata": metadata or {},
            "source": source
        }

        response = self.client.table("memories").insert(data).execute()
        return response.data[0] if response.data else {}

    def get_memory(self, memory_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory UUID

        Returns:
            Memory data or None
        """
        response = self.client.table("memories")\
            .select("*")\
            .eq("id", str(memory_id))\
            .eq("is_deleted", False)\
            .single()\
            .execute()
        return response.data if response.data else None

    def update_memory(
        self,
        memory_id: UUID,
        **updates
    ) -> Dict[str, Any]:
        """
        Update a memory.

        Args:
            memory_id: Memory UUID
            **updates: Fields to update

        Returns:
            Updated memory
        """
        response = self.client.table("memories")\
            .update(updates)\
            .eq("id", str(memory_id))\
            .execute()
        return response.data[0] if response.data else {}

    def delete_memory(self, memory_id: UUID, soft: bool = True) -> bool:
        """
        Delete a memory (soft or hard delete).

        Args:
            memory_id: Memory UUID
            soft: If True, mark as deleted; if False, permanently delete

        Returns:
            Success status
        """
        if soft:
            response = self.client.table("memories")\
                .update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()})\
                .eq("id", str(memory_id))\
                .execute()
        else:
            response = self.client.table("memories")\
                .delete()\
                .eq("id", str(memory_id))\
                .execute()

        return bool(response.data)

    def list_memories(
        self,
        user_id: UUID,
        memory_type: Optional[str] = None,
        session_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List memories for a user.

        Args:
            user_id: User UUID
            memory_type: Filter by memory type
            session_id: Filter by session
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of memories
        """
        query = self.client.table("memories")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .eq("is_deleted", False)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)

        if memory_type:
            query = query.eq("memory_type", memory_type)
        if session_id:
            query = query.eq("session_id", str(session_id))

        response = query.execute()
        return response.data or []

    # ========================================================================
    # SEMANTIC SEARCH
    # ========================================================================

    def semantic_search(
        self,
        query_embedding: List[float],
        user_id: Optional[UUID] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search memories using vector similarity.

        Args:
            query_embedding: 1536-dimensional query vector
            user_id: Optional user UUID (None for all users)
            limit: Maximum results
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of similar memories with similarity scores
        """
        response = self.client.rpc(
            "semantic_search",
            {
                "query_embedding": query_embedding,
                "search_user_id": str(user_id) if user_id else None,
                "result_limit": limit,
                "similarity_threshold": threshold
            }
        ).execute()
        return response.data or []

    def hybrid_search(
        self,
        query_embedding: List[float],
        user_id: UUID,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic similarity and metadata filters.

        Args:
            query_embedding: 1536-dimensional query vector
            user_id: User UUID
            memory_types: Filter by memory types
            min_importance: Minimum importance score
            metadata_filter: JSONB metadata filter
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of memories with combined scores
        """
        response = self.client.rpc(
            "hybrid_memory_search",
            {
                "query_embedding": query_embedding,
                "search_user_id": str(user_id),
                "memory_types": memory_types,
                "min_importance": min_importance,
                "metadata_filter": metadata_filter,
                "result_limit": limit,
                "similarity_threshold": threshold
            }
        ).execute()
        return response.data or []

    def search_concepts(
        self,
        query_embedding: List[float],
        user_id: Optional[UUID] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search concepts using vector similarity.

        Args:
            query_embedding: 1536-dimensional query vector
            user_id: Optional user UUID (None includes system concepts)
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of similar concepts
        """
        response = self.client.rpc(
            "search_concepts",
            {
                "query_embedding": query_embedding,
                "search_user_id": str(user_id) if user_id else None,
                "result_limit": limit,
                "similarity_threshold": threshold
            }
        ).execute()
        return response.data or []

    # ========================================================================
    # CONCEPT OPERATIONS
    # ========================================================================

    def create_concept(
        self,
        name: str,
        description: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        user_id: Optional[UUID] = None,
        concept_type: str = "general",
        confidence: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        is_system: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new concept.

        Args:
            name: Concept name
            description: Concept description
            embedding: 1536-dimensional vector embedding
            user_id: User UUID (None for system concepts)
            concept_type: Type of concept
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            is_system: Whether this is a system-wide concept

        Returns:
            Created concept
        """
        data = {
            "name": name,
            "description": description,
            "embedding": embedding,
            "user_id": str(user_id) if user_id else None,
            "concept_type": concept_type,
            "confidence": confidence,
            "metadata": metadata or {},
            "is_system": is_system
        }

        response = self.client.table("concepts").insert(data).execute()
        return response.data[0] if response.data else {}

    def get_concept(
        self,
        concept_id: Optional[UUID] = None,
        name: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a concept by ID or name.

        Args:
            concept_id: Concept UUID
            name: Concept name
            user_id: User UUID for user-specific concepts

        Returns:
            Concept data or None
        """
        query = self.client.table("concepts").select("*")

        if concept_id:
            query = query.eq("id", str(concept_id))
        elif name:
            query = query.eq("name", name)
            if user_id:
                query = query.eq("user_id", str(user_id))
        else:
            return None

        response = query.single().execute()
        return response.data if response.data else None

    def create_edge(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
        weight: float = 0.5,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an edge between two concepts.

        Args:
            source_id: Source concept UUID
            target_id: Target concept UUID
            relationship_type: Type of relationship
            weight: Edge weight (0-1)
            user_id: User UUID (None for system edges)
            metadata: Additional metadata

        Returns:
            Created edge
        """
        data = {
            "source_id": str(source_id),
            "target_id": str(target_id),
            "relationship_type": relationship_type,
            "weight": weight,
            "user_id": str(user_id) if user_id else None,
            "metadata": metadata or {}
        }

        response = self.client.table("edges").insert(data).execute()
        return response.data[0] if response.data else {}

    # ========================================================================
    # KNOWLEDGE GRAPH TRAVERSAL
    # ========================================================================

    def get_related_concepts(
        self,
        concept_id: UUID,
        max_depth: int = 2,
        min_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get concepts related to a given concept via graph traversal.

        Args:
            concept_id: Starting concept UUID
            max_depth: Maximum traversal depth
            min_weight: Minimum edge weight to follow

        Returns:
            List of related concepts with relationship info
        """
        response = self.client.rpc(
            "get_related_concepts",
            {
                "concept_id": str(concept_id),
                "max_depth": max_depth,
                "min_weight": min_weight
            }
        ).execute()
        return response.data or []

    def get_concept_neighbors(
        self,
        concept_id: UUID,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get direct neighbors of a concept.

        Args:
            concept_id: Concept UUID
            relationship_types: Filter by relationship types

        Returns:
            List of neighboring concepts
        """
        response = self.client.rpc(
            "get_concept_neighbors",
            {
                "concept_id": str(concept_id),
                "relationship_types": relationship_types
            }
        ).execute()
        return response.data or []

    # ========================================================================
    # SESSION OPERATIONS
    # ========================================================================

    def create_session(
        self,
        user_id: UUID,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new session.

        Args:
            user_id: User UUID
            title: Session title
            metadata: Additional metadata

        Returns:
            Created session
        """
        data = {
            "user_id": str(user_id),
            "title": title,
            "metadata": metadata or {},
            "is_active": True
        }

        response = self.client.table("sessions").insert(data).execute()
        return response.data[0] if response.data else {}

    def end_session(
        self,
        session_id: UUID,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a session.

        Args:
            session_id: Session UUID
            summary: Optional session summary

        Returns:
            Updated session
        """
        data = {
            "ended_at": datetime.utcnow().isoformat(),
            "is_active": False
        }
        if summary:
            data["summary"] = summary

        response = self.client.table("sessions")\
            .update(data)\
            .eq("id", str(session_id))\
            .execute()
        return response.data[0] if response.data else {}

    def get_session_memories(
        self,
        session_id: UUID,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a session.

        Args:
            session_id: Session UUID
            memory_types: Filter by memory types
            min_importance: Minimum importance threshold

        Returns:
            List of session memories
        """
        response = self.client.rpc(
            "get_session_memories",
            {
                "session_id": str(session_id),
                "memory_types": memory_types,
                "min_importance": min_importance
            }
        ).execute()
        return response.data or []

    # ========================================================================
    # FEDERATION OPERATIONS
    # ========================================================================

    def sync_to_federation(
        self,
        memory_ids: List[UUID],
        target_instance: Optional[str] = None
    ) -> int:
        """
        Queue memories for federation sync.

        Args:
            memory_ids: List of memory UUIDs to sync
            target_instance: Target instance ID (None for broadcast)

        Returns:
            Number of memories queued
        """
        response = self.client.rpc(
            "sync_to_federation",
            {
                "memory_ids": [str(mid) for mid in memory_ids],
                "target_instance": target_instance
            }
        ).execute()
        return response.data if isinstance(response.data, int) else 0

    def get_pending_sync_events(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get pending sync events (admin only).

        Args:
            limit: Maximum events to retrieve

        Returns:
            List of pending sync events
        """
        if not self.admin_client:
            raise PermissionError("Admin client required for sync operations")

        response = self.admin_client.table("sync_events")\
            .select("*")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .limit(limit)\
            .execute()
        return response.data or []

    # ========================================================================
    # ADMIN OPERATIONS
    # ========================================================================

    def merge_memories(
        self,
        source_ids: List[UUID],
        user_id: UUID,
        merged_content: str,
        merged_embedding: Optional[List[float]] = None
    ) -> UUID:
        """
        Merge multiple memories into one (admin operation).

        Args:
            source_ids: List of source memory UUIDs
            user_id: Target user UUID
            merged_content: Content of merged memory
            merged_embedding: Optional embedding for merged memory

        Returns:
            UUID of new merged memory
        """
        response = self.client.rpc(
            "merge_memories",
            {
                "source_ids": [str(sid) for sid in source_ids],
                "target_user_id": str(user_id),
                "merged_content": merged_content,
                "merged_embedding": merged_embedding
            }
        ).execute()
        return UUID(response.data) if response.data else None

    def get_popular_memories(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most accessed memories for a user.

        Args:
            user_id: User UUID
            limit: Maximum results

        Returns:
            List of popular memories
        """
        response = self.client.rpc(
            "get_popular_memories",
            {
                "search_user_id": str(user_id),
                "result_limit": limit
            }
        ).execute()
        return response.data or []

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_table_counts(self) -> Dict[str, int]:
        """
        Get row counts for all tables (admin only).

        Returns:
            Dictionary of table names to row counts
        """
        if not self.admin_client:
            raise PermissionError("Admin client required")

        tables = ["users", "memories", "concepts", "edges", "sessions", "sync_events"]
        counts = {}

        for table in tables:
            try:
                response = self.admin_client.table(table)\
                    .select("id", count="exact")\
                    .execute()
                counts[table] = response.count
            except Exception as e:
                logger.error(f"Failed to count {table}: {e}")
                counts[table] = -1

        return counts


# Convenience function for creating a client
def get_client(
    url: Optional[str] = None,
    key: Optional[str] = None,
    service_key: Optional[str] = None
) -> SupabaseClient:
    """
    Create a SupabaseClient instance.

    Args:
        url: Supabase project URL
        key: Supabase anon key
        service_key: Supabase service role key

    Returns:
        Initialized SupabaseClient
    """
    return SupabaseClient(url=url, key=key, service_key=service_key)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
