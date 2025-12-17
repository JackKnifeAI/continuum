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
Logs management routes for CONTINUUM admin dashboard.
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from .admin_middleware import get_current_admin_user
from .admin_db import get_admin_db_path, init_admin_db


# =============================================================================
# SCHEMAS
# =============================================================================

class LogEntry(BaseModel):
    """Single log entry."""
    id: int
    timestamp: str
    level: str
    message: str
    module: Optional[str]
    function: Optional[str]
    line_number: Optional[int]
    tenant_id: Optional[str]
    user_id: Optional[str]
    metadata: Optional[dict]


class LogListResponse(BaseModel):
    """Log list response."""
    items: List[LogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/logs", tags=["Logs"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=LogListResponse)
async def list_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Filter by log level"),
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601)"),
    search: Optional[str] = Query(None, description="Search in message"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    List system logs with pagination and filtering.

    **Filters:**
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    - search: Search in log message (partial match)
    - tenant_id: Filter by tenant

    **Returns:**
    Paginated list of log entries.
    """
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Build query
    where_clauses = []
    params = []

    if level:
        where_clauses.append("level = ?")
        params.append(level)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            where_clauses.append("timestamp >= ?")
            params.append(start_dt.isoformat())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            where_clauses.append("timestamp <= ?")
            params.append(end_dt.isoformat())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if search:
        where_clauses.append("message LIKE ?")
        params.append(f"%{search}%")

    if tenant_id:
        where_clauses.append("tenant_id = ?")
        params.append(tenant_id)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    c.execute(f"SELECT COUNT(*) FROM system_logs WHERE {where_clause}", params)
    total = c.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * page_size
    query = f"""
        SELECT id, timestamp, level, message, module, function, line_number, tenant_id, user_id, metadata
        FROM system_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    c.execute(query, params)

    logs = []
    for row in c.fetchall():
        # Parse metadata JSON
        metadata = None
        if row[9]:
            try:
                metadata = json.loads(row[9])
            except json.JSONDecodeError:
                metadata = None

        logs.append(LogEntry(
            id=row[0],
            timestamp=row[1],
            level=row[2],
            message=row[3],
            module=row[4],
            function=row[5],
            line_number=row[6],
            tenant_id=row[7],
            user_id=row[8],
            metadata=metadata
        ))

    conn.close()

    total_pages = (total + page_size - 1) // page_size

    return LogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/export")
async def export_logs(
    level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Export logs as JSON.

    **Filters:** Same as list_logs

    **Returns:**
    JSON array of log entries (not paginated).

    **Note:** Large exports may take time. Consider pagination for large datasets.
    """
    init_admin_db()
    db_path = get_admin_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Build query (same as list_logs)
    where_clauses = []
    params = []

    if level:
        where_clauses.append("level = ?")
        params.append(level)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            where_clauses.append("timestamp >= ?")
            params.append(start_dt.isoformat())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            where_clauses.append("timestamp <= ?")
            params.append(end_dt.isoformat())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if tenant_id:
        where_clauses.append("tenant_id = ?")
        params.append(tenant_id)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get all matching logs (limit to 10000 for safety)
    query = f"""
        SELECT id, timestamp, level, message, module, function, line_number, tenant_id, user_id, metadata
        FROM system_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT 10000
    """
    c.execute(query, params)

    logs = []
    for row in c.fetchall():
        # Parse metadata JSON
        metadata = None
        if row[9]:
            try:
                metadata = json.loads(row[9])
            except json.JSONDecodeError:
                metadata = None

        logs.append({
            "id": row[0],
            "timestamp": row[1],
            "level": row[2],
            "message": row[3],
            "module": row[4],
            "function": row[5],
            "line_number": row[6],
            "tenant_id": row[7],
            "user_id": row[8],
            "metadata": metadata
        })

    conn.close()

    return {
        "logs": logs,
        "count": len(logs),
        "exported_at": datetime.utcnow().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
