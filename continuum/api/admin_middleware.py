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
Authentication middleware for admin routes.
"""

from typing import Optional
from fastapi import HTTPException, Header, Depends
from .admin_db import verify_token, get_admin_user_by_id


async def get_current_admin_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    FastAPI dependency to validate JWT and extract admin user.

    **Usage:**
    ```python
    @router.get("/protected")
    async def protected_route(admin_user: dict = Depends(get_current_admin_user)):
        return {"user": admin_user}
    ```

    **Args:**
        authorization: Bearer token from Authorization header

    **Returns:**
        Admin user dict with id, username, email, etc.

    **Raises:**
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]

    # Verify token
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user ID from payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user from database
    user = get_admin_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=403,
            detail="User account is disabled"
        )

    return user


async def get_current_superuser(admin_user: dict = Depends(get_current_admin_user)) -> dict:
    """
    FastAPI dependency to require superuser privileges.

    **Usage:**
    ```python
    @router.delete("/users/{user_id}")
    async def delete_user(user_id: str, admin: dict = Depends(get_current_superuser)):
        # Only superusers can delete users
        ...
    ```

    **Args:**
        admin_user: Admin user from get_current_admin_user

    **Returns:**
        Admin user dict (only if superuser)

    **Raises:**
        HTTPException: If user is not a superuser
    """
    if not admin_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Superuser privileges required"
        )

    return admin_user

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
