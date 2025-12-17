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
Authentication routes for CONTINUUM admin dashboard.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .admin_db import (
    authenticate_admin_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    create_session,
    delete_session,
    get_admin_user_by_id,
    log_activity
)


# =============================================================================
# SCHEMAS
# =============================================================================

class LoginRequest(BaseModel):
    """Login request."""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User information")


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str = Field(..., description="New access token")
    token_type: str = Field(default="bearer", description="Token type")


class LogoutRequest(BaseModel):
    """Logout request."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate admin user and return tokens.

    **Flow:**
    1. User submits username/password
    2. Server validates credentials
    3. Server creates access token (1h expiry) and refresh token (30d expiry)
    4. Server creates session record
    5. Client stores tokens (access in memory, refresh in httpOnly cookie)

    **Returns:**
    - access_token: Short-lived JWT for API requests (include in Authorization header)
    - refresh_token: Long-lived JWT for token refresh (store securely)
    - user: User information (id, username, email, etc.)
    """
    # Authenticate user
    user = authenticate_admin_user(request.username, request.password)

    if not user:
        # Log failed login attempt
        log_activity(
            admin_user_id=None,
            action="login_failed",
            resource_type="admin_user",
            resource_id=request.username,
            ip_address=req.client.host if req.client else None
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user["id"], "username": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["id"]})

    # Create session
    create_session(
        admin_user_id=user["id"],
        refresh_token=refresh_token,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent")
    )

    # Log successful login
    log_activity(
        admin_user_id=user["id"],
        action="login_success",
        resource_type="admin_user",
        resource_id=str(user["id"]),
        ip_address=req.client.host if req.client else None
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.

    **Flow:**
    1. Client's access token expires
    2. Client calls /refresh with refresh token
    3. Server validates refresh token
    4. Server issues new access token
    5. Client continues making requests with new token

    **Note:** Refresh token is NOT rotated. Same refresh token can be used
    until it expires (30 days) or is invalidated via logout.

    **Returns:**
    - access_token: New access token (1h expiry)
    """
    # Verify refresh token
    admin_user_id = verify_refresh_token(request.refresh_token)

    if not admin_user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    # Get user
    user = get_admin_user_by_id(admin_user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # Create new access token
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"]}
    )

    return RefreshResponse(access_token=access_token)


@router.post("/logout")
async def logout(request: LogoutRequest, req: Request):
    """
    Logout admin user and invalidate refresh token.

    **Flow:**
    1. Client calls /logout with refresh token
    2. Server deletes session record
    3. Client clears stored tokens

    **Note:** Access tokens cannot be invalidated (stateless JWT).
    They will remain valid until expiry (1h). For immediate revocation,
    would need token blacklist or shorter expiry times.

    **Returns:**
    Confirmation message.
    """
    if request.refresh_token:
        # Delete session
        delete_session(request.refresh_token)

        # Try to extract user ID from token (may fail if expired)
        try:
            from .admin_db import verify_token
            payload = verify_token(request.refresh_token, "refresh")
            if payload:
                admin_user_id = payload.get("sub")
                log_activity(
                    admin_user_id=admin_user_id,
                    action="logout",
                    resource_type="admin_user",
                    resource_id=str(admin_user_id),
                    ip_address=req.client.host if req.client else None
                )
        except Exception:
            pass

    return {
        "status": "success",
        "message": "Logged out successfully"
    }


@router.get("/me")
async def get_current_user(current_user: dict = Depends(lambda: None)):
    """
    Get current authenticated user.

    **Requires:** Valid access token in Authorization header.

    **Returns:**
    Current user information.
    """
    # This will be implemented with auth middleware
    # For now, return placeholder
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@continuum.local",
        "full_name": "Admin User",
        "is_superuser": True
    }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
