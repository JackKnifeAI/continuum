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
System management routes for CONTINUUM admin dashboard.
"""

import os
import sqlite3
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from continuum.core.memory import TenantManager

from .admin_middleware import get_current_admin_user

# =============================================================================
# SCHEMAS
# =============================================================================

class HealthResponse(BaseModel):
    """System health response."""
    status: str = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    database: Dict[str, Any] = Field(..., description="Database status")
    memory: Dict[str, Any] = Field(..., description="Memory usage")


class SystemMetrics(BaseModel):
    """System metrics response."""
    platform: Dict[str, Any] = Field(..., description="Platform information")
    resources: Dict[str, Any] = Field(..., description="Resource usage")
    tenants: Dict[str, Any] = Field(..., description="Tenant statistics")
    api: Dict[str, Any] = Field(..., description="API statistics")


class SystemConfig(BaseModel):
    """System configuration response."""
    api: Dict[str, Any] = Field(..., description="API configuration")
    database: Dict[str, Any] = Field(..., description="Database configuration")
    features: Dict[str, Any] = Field(..., description="Feature flags")
    limits: Dict[str, Any] = Field(..., description="System limits")


class UpdateConfigRequest(BaseModel):
    """Update configuration request."""
    key: str = Field(..., description="Configuration key (dot notation)")
    value: Any = Field(..., description="Configuration value")


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/system", tags=["System"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Track server start time
import time

_SERVER_START_TIME = time.time()


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    from .admin_db import get_admin_db_path
    db_path = get_admin_db_path()

    if not db_path.exists():
        return {
            "status": "not_initialized",
            "path": str(db_path)
        }

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Get table counts
        c.execute("SELECT COUNT(*) FROM users")
        users_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM admin_users")
        admins_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM system_logs")
        logs_count = c.fetchone()[0]

        # Get database size
        db_size = db_path.stat().st_size

        conn.close()

        return {
            "status": "healthy",
            "path": str(db_path),
            "size_bytes": db_size,
            "size_mb": round(db_size / 1024 / 1024, 2),
            "tables": {
                "users": users_count,
                "admins": admins_count,
                "logs": logs_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_memory_stats() -> Dict[str, Any]:
    """Get memory statistics."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "rss_bytes": memory_info.rss,
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_bytes": memory_info.vms,
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_platform_info() -> Dict[str, Any]:
    """Get platform information."""
    import platform
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def get_resource_usage() -> Dict[str, Any]:
    """Get resource usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "percent": disk.percent
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_tenant_stats() -> Dict[str, Any]:
    """Get tenant statistics."""
    try:
        tenant_manager = TenantManager()
        tenants = tenant_manager.list_tenants()

        total_memories = 0
        total_entities = 0

        for tenant_id in tenants:
            try:
                tenant_manager.get_tenant(tenant_id)
                # This would require sync call, skip for now
                # stats = await memory.aget_stats()
                # total_memories += stats.get('messages', 0)
                # total_entities += stats.get('entities', 0)
            except Exception:
                pass

        return {
            "total_tenants": len(tenants),
            "total_memories": total_memories,
            "total_entities": total_entities
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def count_api_endpoints(app) -> int:
    """Count registered HTTP route handlers in the FastAPI app."""
    from fastapi.routing import APIRoute
    return sum(1 for r in app.routes if isinstance(r, APIRoute))


def get_request_counts() -> tuple[int, int]:
    """Return (requests_total, errors_total) from the Prometheus registry."""
    try:
        from prometheus_client import REGISTRY
        requests_total = 0
        errors_total = 0
        for metric in REGISTRY.collect():
            if metric.name == 'continuum_api_requests_total':
                for sample in metric.samples:
                    if sample.name.endswith('_total'):
                        requests_total += int(sample.value)
            elif metric.name == 'continuum_api_errors_total':
                for sample in metric.samples:
                    if sample.name.endswith('_total'):
                        errors_total += int(sample.value)
        return requests_total, errors_total
    except Exception:
        return 0, 0


def is_graphql_available() -> bool:
    """Return True if the strawberry GraphQL package is installed."""
    import importlib.util
    return importlib.util.find_spec("strawberry") is not None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def system_health(admin_user: dict = Depends(get_current_admin_user)):
    """
    Get system health status.

    **Returns:**
    - Overall system status
    - Database health
    - Memory usage
    - Uptime

    **Authentication:** Required
    """
    uptime = time.time() - _SERVER_START_TIME

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime_seconds=round(uptime, 2),
        database=get_database_stats(),
        memory=get_memory_stats()
    )


@router.get("/metrics", response_model=SystemMetrics)
async def system_metrics(request: Request, admin_user: dict = Depends(get_current_admin_user)):
    """
    Get comprehensive system metrics.

    **Returns:**
    - Platform information
    - Resource usage (CPU, memory, disk)
    - Tenant statistics
    - API statistics

    **Authentication:** Required
    """
    requests_total, errors_total = get_request_counts()
    return SystemMetrics(
        platform=get_platform_info(),
        resources=get_resource_usage(),
        tenants=get_tenant_stats(),
        api={
            "endpoints": count_api_endpoints(request.app),
            "requests_total": requests_total,
            "errors_total": errors_total,
        }
    )


@router.get("/config", response_model=SystemConfig)
async def system_config(admin_user: dict = Depends(get_current_admin_user)):
    """
    Get system configuration.

    **Returns:**
    Current system configuration including:
    - API settings
    - Database settings
    - Feature flags
    - System limits

    **Authentication:** Required
    """
    return SystemConfig(
        api={
            "base_url": os.environ.get("CONTINUUM_API_URL", "http://localhost:8420"),
            "cors_origins": os.environ.get("CONTINUUM_CORS_ORIGINS", "http://localhost:3000").split(","),
            "require_api_key": os.environ.get("CONTINUUM_REQUIRE_API_KEY", "true").lower() == "true",
            "rate_limit_enabled": os.environ.get("CONTINUUM_RATE_LIMIT_ENABLED", "true").lower() == "true",
        },
        database={
            "type": "sqlite",
            "path": str(get_database_stats().get("path", "")),
            "size_mb": get_database_stats().get("size_mb", 0)
        },
        features={
            "graphql": is_graphql_available(),
            "websockets": True,
            "semantic_search": True,
            "federation": True,
            "billing": True
        },
        limits={
            "max_memories_per_tenant": 1000000,
            "max_api_calls_per_minute": 100,
            "max_concurrent_requests": 10
        }
    )


@router.patch("/config")
async def update_system_config(
    request: UpdateConfigRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Update system configuration.

    **Note:** Most configuration changes require server restart.

    **Authentication:** Required (superuser)

    **Returns:**
    Confirmation message.
    """
    # This would require a configuration management system
    # For now, return not implemented

    if not admin_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Superuser privileges required"
        )

    return {
        "status": "not_implemented",
        "message": "Configuration updates not yet implemented. Use environment variables."
    }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
