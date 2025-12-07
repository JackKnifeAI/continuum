"""
DataLoaders for Session entities.
"""

from typing import List, Optional
from strawberry.dataloader import DataLoader
import aiosqlite


class SessionLoader(DataLoader):
    """Batch load sessions by ID"""

    def __init__(self, db_path: str):
        super().__init__(load_fn=self.batch_load_fn)
        self.db_path = db_path

    async def batch_load_fn(self, keys: List[str]) -> List[Optional[dict]]:
        """Batch load sessions by IDs"""
        from ..types import Session, SessionStatus
        from datetime import datetime

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            placeholders = ",".join("?" * len(keys))
            query = f"""
                SELECT
                    id, title, summary, status, message_count,
                    started_at, ended_at, created_at, updated_at, tenant_id, metadata
                FROM sessions
                WHERE id IN ({placeholders})
            """

            cursor = await conn.execute(query, keys)
            rows = await cursor.fetchall()

            session_dict = {}
            for row in rows:
                session_dict[row["id"]] = Session(
                    id=str(row["id"]),
                    title=row["title"],
                    summary=row["summary"],
                    status=SessionStatus(row["status"]),
                    message_count=row["message_count"] or 0,
                    started_at=datetime.fromisoformat(row["started_at"]),
                    ended_at=(
                        datetime.fromisoformat(row["ended_at"])
                        if row["ended_at"]
                        else None
                    ),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    tenant_id=row["tenant_id"],
                    metadata=row["metadata"],
                )

            return [session_dict.get(key) for key in keys]
