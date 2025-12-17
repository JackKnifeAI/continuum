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
Resolvers for Session type fields.
"""

from typing import List
from strawberry.types import Info


async def resolve_session_user(session, info: Info):
    """Resolve user for a session"""
    import aiosqlite

    db_path = info.context.get("db_path")
    if not db_path:
        return None

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        cursor = await conn.execute(
            "SELECT user_id FROM sessions WHERE id = ?",
            [session.id]
        )
        row = await cursor.fetchone()

        if not row:
            return None

        user_loader = info.context["loaders"]["user"]
        return await user_loader.load(row["user_id"])


async def resolve_session_memories(session, info: Info, pagination):
    """Resolve memories for a session"""
    from ..types import MemoryConnection, MemoryEdge, PageInfo
    import aiosqlite

    db_path = info.context.get("db_path")
    if not db_path:
        return MemoryConnection(edges=[], page_info=PageInfo(
            has_next_page=False, has_previous_page=False,
            start_cursor=None, end_cursor=None
        ), total_count=0)

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        first = pagination.first if pagination else 20

        # Query memories with session_id in metadata
        query = """
            SELECT id
            FROM memories
            WHERE json_extract(metadata, '$.session_id') = ?
            ORDER BY created_at DESC
            LIMIT ?
        """

        cursor = await conn.execute(query, [session.id, first + 1])
        rows = await cursor.fetchall()

        memory_ids = [row["id"] for row in rows[:first]]
        has_next = len(rows) > first

        # Load memories using DataLoader
        memory_loader = info.context["loaders"]["memory"]
        memories = await memory_loader.load_many(memory_ids)

        edges = [
            MemoryEdge(
                cursor=str(i),
                node=memory,
                score=None
            )
            for i, memory in enumerate(memories) if memory
        ]

        return MemoryConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=False,
                start_cursor="0" if edges else None,
                end_cursor=str(len(edges) - 1) if edges else None,
            ),
            total_count=len(edges),
        )


async def resolve_session_concepts(session, info: Info, limit: int) -> List:
    """Resolve concepts discovered in a session"""
    import aiosqlite

    db_path = info.context.get("db_path")
    if not db_path:
        return []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Get unique concepts from session memories
        query = """
            SELECT DISTINCT c.id
            FROM concepts c
            JOIN memory_concepts mc ON c.id = mc.concept_id
            JOIN memories m ON mc.memory_id = m.id
            WHERE json_extract(m.metadata, '$.session_id') = ?
            ORDER BY c.created_at DESC
            LIMIT ?
        """

        cursor = await conn.execute(query, [session.id, limit])
        rows = await cursor.fetchall()

        concept_ids = [row["id"] for row in rows]

        # Load concepts using DataLoader
        concept_loader = info.context["loaders"]["concept"]
        concepts = await concept_loader.load_many(concept_ids)

        return [c for c in concepts if c]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
