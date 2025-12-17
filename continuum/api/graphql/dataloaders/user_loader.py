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
DataLoaders for User entities.
"""

from typing import List, Optional
from strawberry.dataloader import DataLoader
import aiosqlite


class UserLoader(DataLoader):
    """Batch load users by ID"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, keys: List[str]) -> List[Optional[dict]]:
        """Batch load users by IDs"""
        from ..types import User, UserRole
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            placeholders = ",".join("?" * len(keys))
            query = f"""
                SELECT
                    id, username, email, display_name, role,
                    memory_count, concept_count, created_at, updated_at, last_login_at
                FROM users
                WHERE id IN ({placeholders})
            """

            cursor = await conn.execute(query, keys)
            rows = await cursor.fetchall()

            user_dict = {}
            for row in rows:
                user_dict[row["id"]] = User(
                    id=str(row["id"]),
                    username=row["username"],
                    email=row["email"],
                    display_name=row["display_name"],
                    role=UserRole(row["role"]),
                    profile=None,  # Loaded separately if needed
                    settings=None,  # Loaded separately if needed
                    memory_count=row["memory_count"] or 0,
                    concept_count=row["concept_count"] or 0,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_login_at=(
                        datetime.fromisoformat(row["last_login_at"])
                        if row["last_login_at"]
                        else None
                    ),
                )

            return [user_dict.get(key) for key in keys]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
