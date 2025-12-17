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

"""Access control enforcement decorators and middleware."""

from functools import wraps
from typing import Callable, Optional


class AccessEnforcer:
    """
    Enforces access control through decorators and middleware.

    Usage:
        @enforce_permission("read", "memory")
        async def get_memory(memory_id: str, user_id: str):
            ...
    """

    def __init__(self, rbac_manager):
        self.rbac = rbac_manager

    def enforce_permission(
        self,
        action: str,
        resource_type: str,
    ) -> Callable:
        """
        Decorator to enforce permission checks.

        Args:
            action: Required action (e.g., "read", "write")
            resource_type: Resource type (e.g., "memory", "session")

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user_id and resource_id from kwargs
                user_id = kwargs.get("user_id")
                resource_id = kwargs.get("resource_id") or kwargs.get("memory_id")
                tenant_id = kwargs.get("tenant_id")

                if not user_id:
                    raise ValueError("user_id required for permission check")

                # Check permission
                has_permission = await self.rbac.check_permission(
                    user_id=user_id,
                    permission=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tenant_id=tenant_id,
                )

                if not has_permission:
                    raise PermissionError(
                        f"User {user_id} lacks permission for {action} on {resource_type}"
                    )

                # Call original function
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def enforce_role(self, required_role: str) -> Callable:
        """
        Decorator to enforce role requirement.

        Args:
            required_role: Required role (e.g., "admin", "operator")

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id")
                tenant_id = kwargs.get("tenant_id")

                if not user_id:
                    raise ValueError("user_id required for role check")

                # Get user roles
                roles = await self.rbac.get_user_roles(user_id, tenant_id)
                role_ids = [role.id for role in roles]

                if required_role not in role_ids:
                    raise PermissionError(
                        f"User {user_id} lacks required role: {required_role}"
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator


# Example FastAPI middleware for access control:
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AccessControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rbac_manager):
        super().__init__(app)
        self.rbac = rbac_manager

    async def dispatch(self, request: Request, call_next):
        # Extract user from request (JWT, session, etc.)
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None

        if not user_id:
            # Public endpoints
            return await call_next(request)

        # Check permission based on route
        path = request.url.path
        method = request.method

        # Map HTTP methods to actions
        action_map = {
            "GET": "read",
            "POST": "write",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }

        action = action_map.get(method, "read")

        # Extract resource type from path
        # e.g., /api/v1/memories/123 -> resource_type = "memory"
        parts = path.split('/')
        resource_type = parts[3] if len(parts) > 3 else "unknown"

        # Check permission
        has_permission = await self.rbac.check_permission(
            user_id=user_id,
            permission=action,
            resource_type=resource_type,
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="Forbidden")

        response = await call_next(request)
        return response
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
