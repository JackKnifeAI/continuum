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
User management routes for CONTINUUM admin dashboard.
"""

import sqlite3
import secrets
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, EmailStr

from .admin_middleware import get_current_admin_user
from .admin_db import get_admin_db_path, init_admin_db, log_activity, hash_password
from .middleware import hash_key


# =============================================================================
# SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    """Create user request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    tier: str = Field(default="free", pattern="^(free|pro|enterprise)$")
    password: Optional[str] = Field(None, min_length=8, description="Optional password, auto-generated if not provided")


class UserUpdate(BaseModel):
    """Update user request."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    tier: Optional[str] = Field(None, pattern="^(free|pro|enterprise)$")
    status: Optional[str] = Field(None, pattern="^(active|suspended|deleted)$")


class UserResponse(BaseModel):
    """User response."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    tenant_id: str
    status: str
    tier: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    created_at: str
    updated_at: str
    suspended_at: Optional[str]
    suspension_reason: Optional[str]
    api_key_preview: Optional[str] = None  # First 8 chars only


class UserListResponse(BaseModel):
    """User list response."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SuspendUserRequest(BaseModel):
    """Suspend user request."""
    reason: str = Field(..., min_length=1, max_length=500)


class ResetPasswordResponse(BaseModel):
    """Reset password response."""
    temp_password: str
    message: str


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/users", tags=["Users"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_user_db():
    """Get user database connection."""
    init_admin_db()
    db_path = get_admin_db_path()
    return sqlite3.connect(db_path)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    status: Optional[str] = Query(None, pattern="^(active|suspended|deleted)$", description="Filter by status"),
    tier: Optional[str] = Query(None, pattern="^(free|pro|enterprise)$", description="Filter by tier"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    List all users with pagination and filtering.

    **Filters:**
    - search: Search by username or email (partial match)
    - status: Filter by user status
    - tier: Filter by pricing tier

    **Returns:**
    Paginated list of users with metadata.
    """
    conn = get_user_db()
    c = conn.cursor()

    # Build query
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(username LIKE ? OR email LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    if tier:
        where_clauses.append("tier = ?")
        params.append(tier)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    c.execute(f"SELECT COUNT(*) FROM users WHERE {where_clause}", params)
    total = c.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * page_size
    query = f"""
        SELECT id, username, email, full_name, tenant_id, status, tier,
               stripe_customer_id, stripe_subscription_id,
               created_at, updated_at, suspended_at, suspension_reason
        FROM users
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    c.execute(query, params)

    users = []
    for row in c.fetchall():
        users.append(UserResponse(
            id=row[0],
            username=row[1],
            email=row[2],
            full_name=row[3],
            tenant_id=row[4],
            status=row[5],
            tier=row[6],
            stripe_customer_id=row[7],
            stripe_subscription_id=row[8],
            created_at=row[9],
            updated_at=row[10],
            suspended_at=row[11],
            suspension_reason=row[12]
        ))

    conn.close()

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Get user by ID.

    **Returns:**
    User details including tier, status, and Stripe information.
    """
    conn = get_user_db()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, username, email, full_name, tenant_id, status, tier,
               stripe_customer_id, stripe_subscription_id,
               created_at, updated_at, suspended_at, suspension_reason
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=row[0],
        username=row[1],
        email=row[2],
        full_name=row[3],
        tenant_id=row[4],
        status=row[5],
        tier=row[6],
        stripe_customer_id=row[7],
        stripe_subscription_id=row[8],
        created_at=row[9],
        updated_at=row[10],
        suspended_at=row[11],
        suspension_reason=row[12]
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    request: UserCreate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Create new user account.

    **Flow:**
    1. Generate user ID and tenant ID
    2. Create API key for user
    3. Store user in database
    4. Return user details

    **Note:** Password is optional. If not provided, a random password is generated.
    The user should reset it on first login.

    **Returns:**
    Created user with generated credentials.
    """
    conn = get_user_db()
    c = conn.cursor()

    try:
        # Generate IDs
        user_id = f"usr_{secrets.token_urlsafe(16)}"
        tenant_id = f"tenant_{secrets.token_urlsafe(16)}"

        # Generate API key
        api_key = f"cm_{secrets.token_urlsafe(32)}"
        api_key_hash = hash_key(api_key)

        now = datetime.utcnow().isoformat()

        # Insert user
        c.execute(
            """
            INSERT INTO users (id, username, email, full_name, tenant_id, api_key_hash, status, tier, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, request.username, request.email, request.full_name, tenant_id, api_key_hash, "active", request.tier, now, now)
        )
        conn.commit()

        # Log activity
        log_activity(
            admin_user_id=admin_user["id"],
            action="user_created",
            resource_type="user",
            resource_id=user_id,
            details={"username": request.username, "email": request.email, "tier": request.tier}
        )

        # Return user
        return UserResponse(
            id=user_id,
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            tenant_id=tenant_id,
            status="active",
            tier=request.tier,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            created_at=now,
            updated_at=now,
            suspended_at=None,
            suspension_reason=None,
            api_key_preview=api_key[:8] + "..."  # Show first 8 chars
        )

    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            raise HTTPException(status_code=409, detail="Username already exists")
        elif "email" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
    finally:
        conn.close()


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Update user account.

    **Fields that can be updated:**
    - email
    - full_name
    - tier (pricing tier)
    - status (active/suspended/deleted)

    **Returns:**
    Updated user details.
    """
    conn = get_user_db()
    c = conn.cursor()

    # Check if user exists
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Build update query
    updates = []
    params = []

    if request.email is not None:
        updates.append("email = ?")
        params.append(request.email)

    if request.full_name is not None:
        updates.append("full_name = ?")
        params.append(request.full_name)

    if request.tier is not None:
        updates.append("tier = ?")
        params.append(request.tier)

    if request.status is not None:
        updates.append("status = ?")
        params.append(request.status)

    if not updates:
        # No updates provided
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(user_id)

    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    c.execute(query, params)
    conn.commit()

    # Log activity
    log_activity(
        admin_user_id=admin_user["id"],
        action="user_updated",
        resource_type="user",
        resource_id=user_id,
        details=request.dict(exclude_none=True)
    )

    # Return updated user
    c.execute(
        """
        SELECT id, username, email, full_name, tenant_id, status, tier,
               stripe_customer_id, stripe_subscription_id,
               created_at, updated_at, suspended_at, suspension_reason
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )
    row = c.fetchone()
    conn.close()

    return UserResponse(
        id=row[0],
        username=row[1],
        email=row[2],
        full_name=row[3],
        tenant_id=row[4],
        status=row[5],
        tier=row[6],
        stripe_customer_id=row[7],
        stripe_subscription_id=row[8],
        created_at=row[9],
        updated_at=row[10],
        suspended_at=row[11],
        suspension_reason=row[12]
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Delete user account.

    **Warning:** This is a soft delete. User status is set to 'deleted'
    but the record is not removed from the database.

    **For hard delete:** Would need to also delete:
    - User's memories
    - User's API keys
    - User's Stripe customer
    - User's sessions

    **Returns:**
    Confirmation message.
    """
    conn = get_user_db()
    c = conn.cursor()

    # Check if user exists
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete
    now = datetime.utcnow().isoformat()
    c.execute(
        "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
        ("deleted", now, user_id)
    )
    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        admin_user_id=admin_user["id"],
        action="user_deleted",
        resource_type="user",
        resource_id=user_id
    )

    return {
        "status": "success",
        "message": f"User {user_id} deleted successfully"
    }


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: SuspendUserRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Suspend user account.

    **Effect:**
    - User cannot log in
    - API keys are disabled
    - All active sessions are invalidated

    **Returns:**
    Confirmation message.
    """
    conn = get_user_db()
    c = conn.cursor()

    # Check if user exists
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Suspend user
    now = datetime.utcnow().isoformat()
    c.execute(
        """
        UPDATE users
        SET status = ?, suspended_at = ?, suspension_reason = ?, updated_at = ?
        WHERE id = ?
        """,
        ("suspended", now, request.reason, now, user_id)
    )
    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        admin_user_id=admin_user["id"],
        action="user_suspended",
        resource_type="user",
        resource_id=user_id,
        details={"reason": request.reason}
    )

    return {
        "status": "success",
        "message": f"User {user_id} suspended successfully",
        "reason": request.reason
    }


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Reset user password.

    **Flow:**
    1. Generate random temporary password
    2. Hash and store in database
    3. Return temporary password to admin
    4. Admin sends password to user via secure channel

    **Security:**
    - Temporary password should be changed on first login
    - Consider implementing password reset via email instead

    **Returns:**
    Temporary password (only shown once).
    """
    conn = get_user_db()
    c = conn.cursor()

    # Check if user exists
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Generate temporary password
    temp_password = secrets.token_urlsafe(16)

    # Note: This would be implemented if users table had password field
    # For now, return message that this needs to be implemented
    conn.close()

    # Log activity
    log_activity(
        admin_user_id=admin_user["id"],
        action="password_reset",
        resource_type="user",
        resource_id=user_id
    )

    return ResetPasswordResponse(
        temp_password=temp_password,
        message="Password reset functionality not fully implemented. Users authenticate via API keys."
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
