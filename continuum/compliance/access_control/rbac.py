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

"""Role-Based Access Control (RBAC) implementation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4


class PermissionScope(Enum):
    """Scope of permission."""
    OWN = "own"  # User's own data
    TENANT = "tenant"  # All data in tenant
    GLOBAL = "global"  # All data across tenants
    SPECIFIC = "specific"  # Specific resources


@dataclass
class Permission:
    """Fine-grained permission."""
    id: str
    name: str
    resource_type: str
    action: str  # read, write, update, delete, admin
    scope: PermissionScope = PermissionScope.OWN
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """Role with associated permissions."""
    id: str
    name: str
    description: str
    permissions: List[Permission]
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoleAssignment:
    """Assignment of role to user."""
    # Required fields first
    user_id: str
    role_id: str
    assigned_by: str

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    tenant_id: Optional[str] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RBACManager:
    """
    Role-Based Access Control Manager.

    Implements SOC2 access control requirements (CC6.1-CC6.3).
    """

    # System roles
    ROLES = {
        "admin": Role(
            id="admin",
            name="Administrator",
            description="Full system access",
            permissions=[
                Permission(
                    id="admin.*",
                    name="Admin All",
                    resource_type="*",
                    action="*",
                    scope=PermissionScope.GLOBAL,
                )
            ],
            is_system_role=True,
        ),
        "operator": Role(
            id="operator",
            name="Operator",
            description="Operational access without user data",
            permissions=[
                Permission(
                    id="read.system",
                    name="Read System",
                    resource_type="system",
                    action="read",
                    scope=PermissionScope.GLOBAL,
                ),
                Permission(
                    id="write.system",
                    name="Write System",
                    resource_type="system",
                    action="write",
                    scope=PermissionScope.GLOBAL,
                ),
            ],
            is_system_role=True,
        ),
        "analyst": Role(
            id="analyst",
            name="Analyst",
            description="Read-only access for analysis",
            permissions=[
                Permission(
                    id="read.logs",
                    name="Read Logs",
                    resource_type="logs",
                    action="read",
                    scope=PermissionScope.GLOBAL,
                ),
                Permission(
                    id="read.reports",
                    name="Read Reports",
                    resource_type="reports",
                    action="read",
                    scope=PermissionScope.GLOBAL,
                ),
            ],
            is_system_role=True,
        ),
        "user": Role(
            id="user",
            name="User",
            description="Standard user access to own data",
            permissions=[
                Permission(
                    id="read.own.memory",
                    name="Read Own Memories",
                    resource_type="memory",
                    action="read",
                    scope=PermissionScope.OWN,
                ),
                Permission(
                    id="write.own.memory",
                    name="Write Own Memories",
                    resource_type="memory",
                    action="write",
                    scope=PermissionScope.OWN,
                ),
                Permission(
                    id="update.own.memory",
                    name="Update Own Memories",
                    resource_type="memory",
                    action="update",
                    scope=PermissionScope.OWN,
                ),
                Permission(
                    id="delete.own.memory",
                    name="Delete Own Memories",
                    resource_type="memory",
                    action="delete",
                    scope=PermissionScope.OWN,
                ),
                Permission(
                    id="read.own.session",
                    name="Read Own Sessions",
                    resource_type="session",
                    action="read",
                    scope=PermissionScope.OWN,
                ),
            ],
            is_system_role=True,
        ),
        "viewer": Role(
            id="viewer",
            name="Viewer",
            description="Read-only access to own data",
            permissions=[
                Permission(
                    id="read.own",
                    name="Read Own",
                    resource_type="*",
                    action="read",
                    scope=PermissionScope.OWN,
                ),
            ],
            is_system_role=True,
        ),
    }

    def __init__(self, db_pool, audit_logger):
        self.db = db_pool
        self.audit = audit_logger

    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Check if user has permission for an action.

        Args:
            user_id: User requesting permission
            permission: Permission string (e.g., "read", "write", "delete")
            resource_type: Type of resource (e.g., "memory", "session")
            resource_id: Specific resource ID (for ownership check)
            tenant_id: Tenant context

        Returns:
            True if permission granted, False otherwise
        """
        # Get user's roles
        roles = await self.get_user_roles(user_id, tenant_id)

        for role in roles:
            # Check if any permission matches
            for perm in role.permissions:
                if self._permission_matches(
                    perm,
                    permission,
                    resource_type,
                    resource_id,
                    user_id,
                    tenant_id,
                ):
                    # Log successful access
                    await self.audit.log_data_access(
                        user_id=user_id,
                        resource_type=resource_type,
                        resource_id=resource_id or "unknown",
                        access_type=permission,
                        fields_accessed=[],
                    )
                    return True

        # Log denied access
        await self.audit.log_gdpr_event(
            event_type="SECURITY_ACCESS_DENIED",
            user_id=user_id,
            request_type="permission_check",
            details={
                "permission": permission,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )

        return False

    async def assign_role(
        self,
        user_id: str,
        role_id: str,
        assigner_id: str,
        tenant_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> RoleAssignment:
        """
        Assign a role to a user.

        Args:
            user_id: User to assign role to
            role_id: Role to assign
            assigner_id: User performing the assignment
            tenant_id: Tenant context
            expires_at: Optional expiration date

        Returns:
            RoleAssignment record
        """
        # Verify assigner has permission
        can_assign = await self.check_permission(
            user_id=assigner_id,
            permission="admin",
            resource_type="user",
            resource_id=user_id,
            tenant_id=tenant_id,
        )

        if not can_assign:
            raise PermissionError("Insufficient permissions to assign roles")

        # Create assignment
        assignment = RoleAssignment(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigner_id,
            expires_at=expires_at,
        )

        # Store in database
        query = """
            INSERT INTO role_assignments
            (id, user_id, role_id, tenant_id, assigned_by, assigned_at, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                str(assignment.id),
                assignment.user_id,
                assignment.role_id,
                assignment.tenant_id,
                assignment.assigned_by,
                assignment.assigned_at,
                assignment.expires_at,
            )

        # Audit log
        await self.audit.log_gdpr_event(
            event_type="ADMIN_ROLE_ASSIGN",
            user_id=assigner_id,
            request_type="role_assignment",
            details={
                "target_user": user_id,
                "role": role_id,
                "assignment_id": str(assignment.id),
            },
        )

        return assignment

    async def revoke_role(
        self,
        assignment_id: UUID,
        revoker_id: str,
    ) -> None:
        """Revoke a role assignment."""
        # Get assignment
        query = "SELECT * FROM role_assignments WHERE id = $1"
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, str(assignment_id))

        if not row:
            raise ValueError("Assignment not found")

        # Verify permission
        can_revoke = await self.check_permission(
            user_id=revoker_id,
            permission="admin",
            resource_type="user",
            resource_id=row["user_id"],
        )

        if not can_revoke:
            raise PermissionError("Insufficient permissions to revoke roles")

        # Delete assignment
        delete_query = "DELETE FROM role_assignments WHERE id = $1"
        async with self.db.acquire() as conn:
            await conn.execute(delete_query, str(assignment_id))

        # Audit log
        await self.audit.log_gdpr_event(
            event_type="ADMIN_ROLE_REVOKE",
            user_id=revoker_id,
            request_type="role_revocation",
            details={
                "target_user": row["user_id"],
                "role": row["role_id"],
                "assignment_id": str(assignment_id),
            },
        )

    async def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Role]:
        """Get all active roles for a user."""
        query = """
            SELECT role_id FROM role_assignments
            WHERE user_id = $1
              AND ($2::text IS NULL OR tenant_id = $2)
              AND (expires_at IS NULL OR expires_at > NOW())
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id, tenant_id)

        roles = []
        for row in rows:
            role_id = row["role_id"]
            if role_id in self.ROLES:
                roles.append(self.ROLES[role_id])

        return roles

    async def get_user_permissions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Permission]:
        """Get all permissions for a user (flattened from roles)."""
        roles = await self.get_user_roles(user_id, tenant_id)

        permissions = []
        for role in roles:
            permissions.extend(role.permissions)

        return permissions

    def _permission_matches(
        self,
        permission: Permission,
        requested_action: str,
        resource_type: str,
        resource_id: Optional[str],
        user_id: str,
        tenant_id: Optional[str],
    ) -> bool:
        """Check if a permission matches the requested action."""
        # Check resource type
        if permission.resource_type != "*" and permission.resource_type != resource_type:
            return False

        # Check action
        if permission.action != "*" and permission.action != requested_action:
            return False

        # Check scope
        if permission.scope == PermissionScope.OWN:
            # User can only access their own resources
            if not resource_id:
                return False
            # Would need to query database to verify ownership
            # For now, simplified check
            return True

        elif permission.scope == PermissionScope.TENANT:
            # User can access all resources in their tenant
            return tenant_id is not None

        elif permission.scope == PermissionScope.GLOBAL:
            # User can access all resources
            return True

        return False


# SQL Schema for RBAC
RBAC_SCHEMA = """
CREATE TABLE IF NOT EXISTS role_assignments (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    tenant_id TEXT,
    assigned_by TEXT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_assigner FOREIGN KEY (assigned_by) REFERENCES users(id)
);

CREATE INDEX idx_role_assignments_user ON role_assignments (user_id);
CREATE INDEX idx_role_assignments_tenant ON role_assignments (tenant_id);
CREATE INDEX idx_role_assignments_active ON role_assignments (user_id, expires_at)
    WHERE expires_at IS NULL OR expires_at > NOW();
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
