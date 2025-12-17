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
DataLoaders for Memory entities.
"""

from typing import List, Optional
from strawberry.dataloader import DataLoader
import aiosqlite


class MemoryLoader(DataLoader):
    """Batch load memories by ID"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, keys: List[str]) -> List[Optional[dict]]:
        """Batch load memories by IDs"""
        from ..types import Memory, MemoryType
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            # Build placeholders for IN clause
            placeholders = ",".join("?" * len(keys))
            query = f"""
                SELECT
                    id, content, memory_type, importance, embedding,
                    access_count, created_at, updated_at, last_accessed_at,
                    tenant_id, metadata
                FROM memories
                WHERE id IN ({placeholders})
            """

            cursor = await conn.execute(query, keys)
            rows = await cursor.fetchall()

            # Create lookup dictionary
            memory_dict = {}
            for row in rows:
                memory_dict[row["id"]] = Memory(
                    id=str(row["id"]),
                    content=row["content"],
                    memory_type=MemoryType(row["memory_type"]),
                    importance=row["importance"],
                    embedding=row["embedding"],
                    access_count=row["access_count"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_accessed_at=(
                        datetime.fromisoformat(row["last_accessed_at"])
                        if row["last_accessed_at"]
                        else None
                    ),
                    tenant_id=row["tenant_id"],
                    metadata=row["metadata"],
                )

            # Return in same order as keys
            return [memory_dict.get(key) for key in keys]


class ConceptsByMemoryLoader(DataLoader):
    """Batch load concepts for memories"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, memory_ids: List[str]) -> List[List[dict]]:
        """Batch load concepts for multiple memories"""
        from ..types import Concept
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            placeholders = ",".join("?" * len(memory_ids))
            query = f"""
                SELECT
                    mc.memory_id,
                    c.id, c.name, c.description, c.confidence,
                    c.concept_type, c.created_at, c.updated_at, c.tenant_id, c.metadata
                FROM memory_concepts mc
                JOIN concepts c ON mc.concept_id = c.id
                WHERE mc.memory_id IN ({placeholders})
                ORDER BY mc.memory_id, c.created_at DESC
            """

            cursor = await conn.execute(query, memory_ids)
            rows = await cursor.fetchall()

            # Group by memory_id
            concepts_by_memory = {mid: [] for mid in memory_ids}
            for row in rows:
                concept = Concept(
                    id=str(row["id"]),
                    name=row["name"],
                    description=row["description"],
                    confidence=row["confidence"],
                    concept_type=row["concept_type"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    tenant_id=row["tenant_id"],
                    metadata=row["metadata"],
                )
                concepts_by_memory[row["memory_id"]].append(concept)

            return [concepts_by_memory.get(mid, []) for mid in memory_ids]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
