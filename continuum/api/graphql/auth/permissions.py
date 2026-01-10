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
Permission decorators for GraphQL resolvers.
"""

from functools import wraps
from typing import Any

from strawberry.permission import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    """Permission class requiring authentication"""

    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """Check if user is authenticated"""
        return info.context.user_id is not None


class IsAdmin(BasePermission):
    """Permission class requiring admin role"""

    message = "User is not an admin"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """Check if user is admin"""
        return info.context.is_admin


# Decorator for authenticated access
def authenticated(func):
    """Decorator requiring authentication"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get info from args
        info = None
        for arg in args:
            if isinstance(arg, Info):
                info = arg
                break

        if not info:
            # Try from kwargs
            info = kwargs.get("info")

        if not info or not info.context.user_id:
            raise Exception("Authentication required")

        return await func(*args, **kwargs)

    return wrapper


# Decorator for admin-only access
def admin_only(func):
    """Decorator requiring admin role"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get info from args
        info = None
        for arg in args:
            if isinstance(arg, Info):
                info = arg
                break

        if not info:
            info = kwargs.get("info")

        if not info or not info.context.is_admin:
            raise Exception("Admin access required")

        return await func(*args, **kwargs)

    return wrapper

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
