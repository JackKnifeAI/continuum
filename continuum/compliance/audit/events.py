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

"""Audit event type definitions and data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class AuditEventType(Enum):
    """Comprehensive audit event taxonomy for compliance."""

    # Authentication Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_MFA_CHALLENGE = "auth.mfa.challenge"
    AUTH_TOKEN_ISSUED = "auth.token.issued"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_API_KEY_CREATED = "auth.api_key.created"
    AUTH_API_KEY_REVOKED = "auth.api_key.revoked"

    # Data Access Events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_SEARCH = "data.search"
    DATA_BULK_READ = "data.bulk.read"
    DATA_BULK_UPDATE = "data.bulk.update"
    DATA_BULK_DELETE = "data.bulk.delete"

    # Memory-Specific Events
    MEMORY_CREATE = "memory.create"
    MEMORY_READ = "memory.read"
    MEMORY_UPDATE = "memory.update"
    MEMORY_DELETE = "memory.delete"
    MEMORY_SEARCH = "memory.search"
    MEMORY_CONSOLIDATE = "memory.consolidate"
    MEMORY_EXPORT = "memory.export"
    MEMORY_SHARE = "memory.share"
    MEMORY_UNSHARE = "memory.unshare"

    # Session Events
    SESSION_START = "session.start"
    SESSION_END = "session.end"
    SESSION_SUSPEND = "session.suspend"
    SESSION_RESUME = "session.resume"
    SESSION_MESSAGE = "session.message"

    # Admin Actions
    ADMIN_USER_CREATE = "admin.user.create"
    ADMIN_USER_UPDATE = "admin.user.update"
    ADMIN_USER_DELETE = "admin.user.delete"
    ADMIN_USER_SUSPEND = "admin.user.suspend"
    ADMIN_USER_UNSUSPEND = "admin.user.unsuspend"
    ADMIN_ROLE_ASSIGN = "admin.role.assign"
    ADMIN_ROLE_REVOKE = "admin.role.revoke"
    ADMIN_PERMISSION_GRANT = "admin.permission.grant"
    ADMIN_PERMISSION_REVOKE = "admin.permission.revoke"
    ADMIN_SETTINGS_CHANGE = "admin.settings.change"
    ADMIN_TENANT_CREATE = "admin.tenant.create"
    ADMIN_TENANT_DELETE = "admin.tenant.delete"

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    SYSTEM_CONFIG_CHANGE = "system.config.change"
    SYSTEM_MAINTENANCE_START = "system.maintenance.start"
    SYSTEM_MAINTENANCE_END = "system.maintenance.end"
    SYSTEM_ERROR = "system.error"
    SYSTEM_ALERT = "system.alert"

    # Security Events
    SECURITY_ACCESS_DENIED = "security.access.denied"
    SECURITY_ANOMALY_DETECTED = "security.anomaly.detected"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SECURITY_INTRUSION_ATTEMPT = "security.intrusion.attempt"
    SECURITY_POLICY_VIOLATION = "security.policy.violation"
    SECURITY_ENCRYPTION_KEY_ROTATED = "security.encryption.key_rotated"

    # GDPR Events
    GDPR_DATA_ACCESS_REQUEST = "gdpr.data.access_request"
    GDPR_DATA_PORTABILITY_REQUEST = "gdpr.data.portability_request"
    GDPR_DATA_ERASURE_REQUEST = "gdpr.data.erasure_request"
    GDPR_DATA_RECTIFICATION_REQUEST = "gdpr.data.rectification_request"
    GDPR_DATA_RESTRICTION_REQUEST = "gdpr.data.restriction_request"
    GDPR_DATA_EXPORTED = "gdpr.data.exported"
    GDPR_DATA_ERASED = "gdpr.data.erased"
    GDPR_CONSENT_GIVEN = "gdpr.consent.given"
    GDPR_CONSENT_WITHDRAWN = "gdpr.consent.withdrawn"
    GDPR_CONSENT_UPDATED = "gdpr.consent.updated"
    GDPR_BREACH_DETECTED = "gdpr.breach.detected"
    GDPR_BREACH_NOTIFIED = "gdpr.breach.notified"

    # Compliance Events
    COMPLIANCE_REPORT_GENERATED = "compliance.report.generated"
    COMPLIANCE_AUDIT_STARTED = "compliance.audit.started"
    COMPLIANCE_AUDIT_COMPLETED = "compliance.audit.completed"
    COMPLIANCE_POLICY_UPDATED = "compliance.policy.updated"
    COMPLIANCE_RETENTION_APPLIED = "compliance.retention.applied"


class ActorType(Enum):
    """Type of entity performing an action."""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    SERVICE = "service"
    API_KEY = "api_key"
    SCHEDULED_TASK = "scheduled_task"
    ANONYMOUS = "anonymous"


class Outcome(Enum):
    """Outcome of an audited action."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    PARTIAL = "partial"
    DENIED = "denied"


class AccessType(Enum):
    """Type of data access."""
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXPORT = "export"
    SHARE = "share"


class AuthEvent(Enum):
    """Authentication event types."""
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLE = "mfa_enable"
    MFA_DISABLE = "mfa_disable"
    TOKEN_REFRESH = "token_refresh"


@dataclass
class Actor:
    """Entity performing an audited action."""
    id: Optional[str]
    type: ActorType
    email: Optional[str] = None
    name: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Resource being acted upon."""
    type: str
    id: Optional[str] = None
    name: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Action being performed."""
    type: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """
    Immutable audit log entry with cryptographic chaining.

    This structure is designed for:
    - SOC2 compliance (7-year retention)
    - GDPR audit requirements
    - HIPAA audit trail requirements
    - Forensic investigation
    - Tamper detection
    """

    # Event Details (required fields first)
    event_type: AuditEventType
    outcome: Outcome

    # Core Identity
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Actor Information
    actor_id: Optional[str] = None
    actor_type: ActorType = ActorType.ANONYMOUS
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None

    # Resource Information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None

    # Action Details
    action: str = ""
    action_description: Optional[str] = None

    # Context
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Network Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geo_location: Optional[str] = None

    # Detailed Information
    details: Dict[str, Any] = field(default_factory=dict)
    fields_accessed: Optional[list[str]] = None
    changes: Optional[Dict[str, Any]] = None  # Before/after for updates

    # Cryptographic Chaining (blockchain-like)
    previous_hash: Optional[str] = None
    hash: Optional[str] = None

    # Retention & Compliance
    retention_period_days: int = 2555  # 7 years for SOC2
    is_sensitive: bool = False
    compliance_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "outcome": self.outcome.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type.value,
            "actor_email": self.actor_email,
            "actor_name": self.actor_name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "action": self.action,
            "action_description": self.action_description,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "geo_location": self.geo_location,
            "details": self.details,
            "fields_accessed": self.fields_accessed,
            "changes": self.changes,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "retention_period_days": self.retention_period_days,
            "is_sensitive": self.is_sensitive,
            "compliance_tags": self.compliance_tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLogEntry":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=AuditEventType(data["event_type"]),
            outcome=Outcome(data["outcome"]),
            actor_id=data.get("actor_id"),
            actor_type=ActorType(data["actor_type"]),
            actor_email=data.get("actor_email"),
            actor_name=data.get("actor_name"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            resource_name=data.get("resource_name"),
            action=data["action"],
            action_description=data.get("action_description"),
            tenant_id=data.get("tenant_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            correlation_id=data.get("correlation_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            geo_location=data.get("geo_location"),
            details=data.get("details", {}),
            fields_accessed=data.get("fields_accessed"),
            changes=data.get("changes"),
            previous_hash=data.get("previous_hash"),
            hash=data.get("hash"),
            retention_period_days=data.get("retention_period_days", 2555),
            is_sensitive=data.get("is_sensitive", False),
            compliance_tags=data.get("compliance_tags", []),
        )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
