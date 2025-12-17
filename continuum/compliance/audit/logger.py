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

"""Core audit logger with cryptographic chaining and multiple backends."""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .events import (
    Action,
    AccessType,
    Actor,
    ActorType,
    AuditEventType,
    AuditLogEntry,
    AuthEvent,
    Outcome,
    Resource,
)
from .storage import AuditLogStorage


class AuditLogger:
    """
    Enterprise audit logger with:
    - Cryptographic chaining for tamper detection
    - Multiple storage backends (PostgreSQL, S3, Elasticsearch)
    - Async batching for performance
    - Automatic compliance tagging
    - Chain integrity verification
    """

    def __init__(
        self,
        storage: AuditLogStorage,
        enable_chaining: bool = True,
        batch_size: int = 100,
        batch_timeout_seconds: float = 5.0,
    ):
        self.storage = storage
        self.enable_chaining = enable_chaining
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds

        self._batch: List[AuditLogEntry] = []
        self._batch_lock = asyncio.Lock()
        self._last_hash: Optional[str] = None
        self._flush_task: Optional[asyncio.Task] = None

    async def log(
        self,
        event_type: AuditEventType,
        actor: Actor,
        resource: Resource,
        action: Action,
        outcome: Outcome,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        fields_accessed: Optional[List[str]] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """
        Log an audit event with full context.

        Args:
            event_type: Type of event being logged
            actor: Entity performing the action
            resource: Resource being acted upon
            action: Action being performed
            outcome: Result of the action
            details: Additional event details
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            request_id: Request identifier for tracing
            fields_accessed: List of data fields accessed
            changes: Before/after values for updates

        Returns:
            Created audit log entry
        """
        entry = AuditLogEntry(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            outcome=outcome,
            actor_id=actor.id,
            actor_type=actor.type,
            actor_email=actor.email,
            actor_name=actor.name,
            resource_type=resource.type,
            resource_id=resource.id,
            resource_name=resource.name,
            action=action.type,
            action_description=action.description,
            tenant_id=resource.tenant_id or actor.tenant_id,
            session_id=session_id,
            request_id=request_id or str(uuid4()),
            correlation_id=None,  # Can be set for related events
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            fields_accessed=fields_accessed,
            changes=changes,
            compliance_tags=self._generate_compliance_tags(event_type, resource),
            is_sensitive=self._is_sensitive_event(event_type, resource),
        )

        # Add cryptographic chaining
        if self.enable_chaining:
            entry.previous_hash = self._last_hash
            entry.hash = self._compute_hash(entry)
            self._last_hash = entry.hash

        # Add to batch
        async with self._batch_lock:
            self._batch.append(entry)

            # Flush if batch is full
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()
            elif not self._flush_task or self._flush_task.done():
                # Start flush timer
                self._flush_task = asyncio.create_task(self._auto_flush())

        return entry

    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: AccessType,
        fields_accessed: List[str],
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Log data access for compliance (GDPR Article 30).

        This creates detailed access logs required for:
        - GDPR data processing records
        - SOC2 access control monitoring
        - HIPAA access audit trails
        """
        event_type_map = {
            AccessType.READ: AuditEventType.DATA_READ,
            AccessType.WRITE: AuditEventType.DATA_CREATE,
            AccessType.UPDATE: AuditEventType.DATA_UPDATE,
            AccessType.DELETE: AuditEventType.DATA_DELETE,
            AccessType.SEARCH: AuditEventType.DATA_SEARCH,
            AccessType.EXPORT: AuditEventType.DATA_EXPORT,
        }

        return await self.log(
            event_type=event_type_map.get(access_type, AuditEventType.DATA_READ),
            actor=Actor(
                id=user_id,
                type=ActorType.USER,
                tenant_id=tenant_id,
            ),
            resource=Resource(
                type=resource_type,
                id=resource_id,
                tenant_id=tenant_id,
            ),
            action=Action(
                type=access_type.value,
                description=f"Accessed {len(fields_accessed)} fields",
            ),
            outcome=Outcome.SUCCESS,
            fields_accessed=fields_accessed,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

    async def log_auth_event(
        self,
        event: AuthEvent,
        user_id: Optional[str],
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        email: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Log authentication events.

        Critical for:
        - Security monitoring
        - Breach detection
        - Compliance audits
        """
        event_type_map = {
            AuthEvent.LOGIN: (
                AuditEventType.AUTH_LOGIN_SUCCESS
                if success
                else AuditEventType.AUTH_LOGIN_FAILURE
            ),
            AuthEvent.LOGOUT: AuditEventType.AUTH_LOGOUT,
            AuthEvent.PASSWORD_CHANGE: AuditEventType.AUTH_PASSWORD_CHANGE,
            AuthEvent.PASSWORD_RESET: AuditEventType.AUTH_PASSWORD_RESET,
            AuthEvent.MFA_ENABLE: AuditEventType.AUTH_MFA_ENABLED,
            AuthEvent.MFA_DISABLE: AuditEventType.AUTH_MFA_DISABLED,
            AuthEvent.TOKEN_REFRESH: AuditEventType.AUTH_TOKEN_REFRESH,
        }

        details = {}
        if not success and failure_reason:
            details["failure_reason"] = failure_reason

        return await self.log(
            event_type=event_type_map[event],
            actor=Actor(
                id=user_id,
                type=ActorType.USER,
                email=email,
            ),
            resource=Resource(type="auth", id=None),
            action=Action(type=event.value),
            outcome=Outcome.SUCCESS if success else Outcome.FAILURE,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_memory_access(
        self,
        user_id: str,
        memory_id: str,
        access_type: AccessType,
        fields_accessed: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log memory-specific access (critical for AI memory systems)."""
        event_type_map = {
            AccessType.READ: AuditEventType.MEMORY_READ,
            AccessType.WRITE: AuditEventType.MEMORY_CREATE,
            AccessType.UPDATE: AuditEventType.MEMORY_UPDATE,
            AccessType.DELETE: AuditEventType.MEMORY_DELETE,
            AccessType.SEARCH: AuditEventType.MEMORY_SEARCH,
            AccessType.EXPORT: AuditEventType.MEMORY_EXPORT,
        }

        return await self.log(
            event_type=event_type_map.get(access_type, AuditEventType.MEMORY_READ),
            actor=Actor(id=user_id, type=ActorType.USER, tenant_id=tenant_id),
            resource=Resource(
                type="memory",
                id=memory_id,
                tenant_id=tenant_id,
            ),
            action=Action(type=access_type.value),
            outcome=Outcome.SUCCESS,
            fields_accessed=fields_accessed,
            session_id=session_id,
        )

    async def log_gdpr_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        request_type: str,
        details: Dict[str, Any],
        outcome: Outcome = Outcome.SUCCESS,
    ) -> AuditLogEntry:
        """Log GDPR-related events (data subject requests, etc.)."""
        return await self.log(
            event_type=event_type,
            actor=Actor(id=user_id, type=ActorType.USER),
            resource=Resource(type="gdpr_request", id=None),
            action=Action(type=request_type, description=f"GDPR {request_type}"),
            outcome=outcome,
            details=details,
        )

    async def log_admin_action(
        self,
        admin_id: str,
        action_type: str,
        target_user_id: Optional[str],
        details: Dict[str, Any],
        outcome: Outcome = Outcome.SUCCESS,
    ) -> AuditLogEntry:
        """Log administrative actions."""
        return await self.log(
            event_type=AuditEventType(f"admin.{action_type}"),
            actor=Actor(id=admin_id, type=ActorType.ADMIN),
            resource=Resource(type="user", id=target_user_id),
            action=Action(type=action_type),
            outcome=outcome,
            details=details,
        )

    async def flush(self) -> None:
        """Manually flush the batch."""
        async with self._batch_lock:
            await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Flush current batch to storage."""
        if not self._batch:
            return

        batch = self._batch.copy()
        self._batch.clear()

        try:
            await self.storage.store_batch(batch)
        except Exception as e:
            # Critical: audit logging failure should be logged but not block operations
            print(f"ERROR: Failed to store audit logs: {e}")
            # In production, this should trigger alerts

    async def _auto_flush(self) -> None:
        """Auto-flush after timeout."""
        await asyncio.sleep(self.batch_timeout_seconds)
        async with self._batch_lock:
            await self._flush_batch()

    def _compute_hash(self, entry: AuditLogEntry) -> str:
        """
        Compute cryptographic hash for entry.

        Uses SHA-256 with:
        - Previous hash (chaining)
        - Entry ID
        - Timestamp
        - Event type
        - Actor ID
        - Resource ID
        - Action

        This creates a tamper-evident chain similar to blockchain.
        """
        hash_input = {
            "previous_hash": entry.previous_hash or "",
            "id": str(entry.id),
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type.value,
            "actor_id": entry.actor_id or "",
            "resource_type": entry.resource_type or "",
            "resource_id": entry.resource_id or "",
            "action": entry.action,
        }

        hash_string = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _generate_compliance_tags(
        self,
        event_type: AuditEventType,
        resource: Resource,
    ) -> List[str]:
        """Generate compliance tags for automatic categorization."""
        tags = []

        # GDPR tags
        if event_type.value.startswith("gdpr."):
            tags.append("gdpr")
        if event_type in [
            AuditEventType.DATA_READ,
            AuditEventType.DATA_UPDATE,
            AuditEventType.DATA_DELETE,
            AuditEventType.DATA_EXPORT,
        ]:
            tags.append("gdpr_processing")

        # SOC2 tags
        if event_type.value.startswith("auth."):
            tags.append("soc2_cc6.1")  # Logical access controls
        if event_type.value.startswith("data."):
            tags.append("soc2_cc6.7")  # Data classification

        # HIPAA tags (if applicable)
        if resource.type in ["medical_data", "phi"]:
            tags.append("hipaa_164.312")

        # Security monitoring
        if event_type in [
            AuditEventType.AUTH_LOGIN_FAILURE,
            AuditEventType.SECURITY_ACCESS_DENIED,
            AuditEventType.SECURITY_ANOMALY_DETECTED,
        ]:
            tags.append("security_alert")

        return tags

    def _is_sensitive_event(
        self,
        event_type: AuditEventType,
        resource: Resource,
    ) -> bool:
        """Determine if event involves sensitive data."""
        # Auth events are always sensitive
        if event_type.value.startswith("auth."):
            return True

        # GDPR events are sensitive
        if event_type.value.startswith("gdpr."):
            return True

        # Memory access is sensitive
        if resource.type == "memory":
            return True

        # Admin actions are sensitive
        if event_type.value.startswith("admin."):
            return True

        return False

    async def verify_chain_integrity(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify cryptographic chain integrity.

        Returns:
            dict with:
                - valid: bool
                - entries_checked: int
                - first_invalid: Optional[str]
                - error: Optional[str]
        """
        entries = await self.storage.get_range(start_id, end_id)

        if not entries:
            return {"valid": True, "entries_checked": 0}

        valid = True
        first_invalid = None

        for i, entry in enumerate(entries):
            # Verify hash computation
            expected_hash = self._compute_hash(entry)
            if entry.hash != expected_hash:
                valid = False
                first_invalid = str(entry.id)
                break

            # Verify chain linkage
            if i > 0:
                previous_entry = entries[i - 1]
                if entry.previous_hash != previous_entry.hash:
                    valid = False
                    first_invalid = str(entry.id)
                    break

        return {
            "valid": valid,
            "entries_checked": len(entries),
            "first_invalid": first_invalid,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
