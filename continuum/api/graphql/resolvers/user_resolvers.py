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
Resolvers for User type fields.
"""

from typing import List
from strawberry.types import Info


async def resolve_user_sessions(user, info: Info, pagination) -> dict:
    """Resolve sessions for a user"""
    from ..types import SessionConnection, SessionConnectionEdge, PageInfo
    import aiosqlite

    db_path = info.context.get("db_path")
    if not db_path:
        return SessionConnection(edges=[], page_info=PageInfo(
            has_next_page=False, has_previous_page=False,
            start_cursor=None, end_cursor=None
        ), total_count=0)

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        first = pagination.first if pagination else 20

        query = """
            SELECT id
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """

        cursor = await conn.execute(query, [user.id, first + 1])
        rows = await cursor.fetchall()

        session_ids = [row["id"] for row in rows[:first]]
        has_next = len(rows) > first

        # Load sessions using DataLoader
        session_loader = info.context["loaders"]["session"]
        sessions = await session_loader.load_many(session_ids)

        edges = [
            SessionConnectionEdge(
                cursor=str(i),
                node=session
            )
            for i, session in enumerate(sessions) if session
        ]

        return SessionConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=False,
                start_cursor="0" if edges else None,
                end_cursor=str(len(edges) - 1) if edges else None,
            ),
            total_count=len(edges),
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
