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
Admin memory management routes for CONTINUUM admin dashboard.

These routes provide admin-level access to all memories across all tenants.
"""

import aiosqlite
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from .admin_middleware import get_current_admin_user
from continuum.core.memory import TenantManager


# =============================================================================
# SCHEMAS
# =============================================================================

class MemoryItem(BaseModel):
    """Single memory item."""
    id: int
    tenant_id: str
    user_id: Optional[str]
    content: str
    memory_type: str
    importance: float
    timestamp: str
    metadata: Optional[dict]


class MemoryListResponse(BaseModel):
    """Memory list response."""
    items: List[MemoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/memories", tags=["Memories"])

# Global tenant manager
tenant_manager = TenantManager()


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=MemoryListResponse)
async def list_all_memories(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    search: Optional[str] = Query(None, description="Search in content"),
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601)"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    importance: Optional[float] = Query(None, ge=0, le=1, description="Minimum importance"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    List all memories across all tenants (admin view).

    **Filters:**
    - user_id: Filter by user
    - tenant_id: Filter by tenant
    - search: Search in content (partial match)
    - start_date: Filter memories after this date
    - end_date: Filter memories before this date
    - memory_type: Filter by type
    - importance: Minimum importance score

    **Returns:**
    Paginated list of memories.

    **Note:** This endpoint provides cross-tenant access.
    Use responsibly and ensure proper authorization.
    """
    # For admin dashboard, we need to query across all tenant databases
    # This is a simplified implementation - in production, would need
    # centralized memory index or federated queries

    # Get all tenants
    tenants = tenant_manager.list_tenants()

    if tenant_id:
        # Filter to specific tenant
        if tenant_id not in tenants:
            raise HTTPException(status_code=404, detail="Tenant not found")
        tenants = [tenant_id]

    all_memories = []

    # Query each tenant's database
    for tid in tenants:
        try:
            memory = tenant_manager.get_tenant(tid)

            # Query messages table (simplified - would need proper memory schema)
            async with aiosqlite.connect(memory.db_path) as conn:
                c = await conn.cursor()

                # Build query
                where_clauses = ["tenant_id = ?"]
                params = [tid]

                if search:
                    where_clauses.append("content LIKE ?")
                    params.append(f"%{search}%")

                if start_date:
                    from datetime import datetime
                    start_ts = datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp()
                    where_clauses.append("timestamp >= ?")
                    params.append(start_ts)

                if end_date:
                    from datetime import datetime
                    end_ts = datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp()
                    where_clauses.append("timestamp <= ?")
                    params.append(end_ts)

                where_clause = " AND ".join(where_clauses)

                # Query auto_messages table
                await c.execute(
                    f"""
                    SELECT id, instance_id, timestamp, content, metadata, tenant_id
                    FROM auto_messages
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    params + [100]  # Limit per tenant
                )

                async for row in c:
                    import json
                    metadata = None
                    if row[4]:
                        try:
                            metadata = json.loads(row[4])
                        except json.JSONDecodeError:
                            pass

                    all_memories.append(MemoryItem(
                        id=row[0],
                        tenant_id=row[5],
                        user_id=row[1],  # instance_id as user_id
                        content=row[3],
                        memory_type="message",
                        importance=0.5,  # Default importance
                        timestamp=str(row[2]),
                        metadata=metadata
                    ))

        except Exception as e:
            # Skip tenant if error
            continue

    # Sort by timestamp
    all_memories.sort(key=lambda m: m.timestamp, reverse=True)

    # Paginate
    total = len(all_memories)
    offset = (page - 1) * page_size
    paginated = all_memories[offset:offset + page_size]

    total_pages = (total + page_size - 1) // page_size

    return MemoryListResponse(
        items=paginated,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{memory_id}")
async def get_memory(
    memory_id: int,
    tenant_id: str = Query(..., description="Tenant ID"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Get specific memory by ID.

    **Parameters:**
    - memory_id: Memory ID
    - tenant_id: Tenant ID (required for locating the memory)

    **Returns:**
    Memory details.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        async with aiosqlite.connect(memory.db_path) as conn:
            c = await conn.cursor()

            await c.execute(
                """
                SELECT id, instance_id, timestamp, content, metadata, tenant_id, role
                FROM auto_messages
                WHERE id = ? AND tenant_id = ?
                """,
                (memory_id, tenant_id)
            )

            row = await c.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Memory not found")

            import json
            metadata = None
            if row[4]:
                try:
                    metadata = json.loads(row[4])
                except json.JSONDecodeError:
                    pass

            return MemoryItem(
                id=row[0],
                tenant_id=row[5],
                user_id=row[1],
                content=row[3],
                memory_type=row[6] if len(row) > 6 else "message",
                importance=0.5,
                timestamp=str(row[2]),
                metadata=metadata
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    tenant_id: str = Query(..., description="Tenant ID"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Delete memory (admin action).

    **Parameters:**
    - memory_id: Memory ID
    - tenant_id: Tenant ID

    **Warning:** This permanently deletes the memory.

    **Returns:**
    Confirmation message.
    """
    try:
        memory = tenant_manager.get_tenant(tenant_id)

        async with aiosqlite.connect(memory.db_path) as conn:
            c = await conn.cursor()

            # Check if exists
            await c.execute(
                "SELECT id FROM auto_messages WHERE id = ? AND tenant_id = ?",
                (memory_id, tenant_id)
            )

            if not await c.fetchone():
                raise HTTPException(status_code=404, detail="Memory not found")

            # Delete
            await c.execute(
                "DELETE FROM auto_messages WHERE id = ? AND tenant_id = ?",
                (memory_id, tenant_id)
            )

            await conn.commit()

        # Log activity
        from .admin_db import log_activity
        log_activity(
            admin_user_id=admin_user["id"],
            action="memory_deleted",
            resource_type="memory",
            resource_id=f"{tenant_id}:{memory_id}"
        )

        return {
            "status": "success",
            "message": f"Memory {memory_id} deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.get("/export")
async def export_memories(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Export memories as JSON.

    **Parameters:**
    - tenant_id: Optional tenant filter

    **Returns:**
    JSON export of memories.

    **Note:** Large exports may take time.
    """
    # This would be similar to list_all_memories but without pagination
    # and with full content export

    return {
        "status": "not_implemented",
        "message": "Memory export not yet implemented"
    }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
