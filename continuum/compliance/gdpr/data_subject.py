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

"""GDPR Data Subject Rights implementation (Articles 15-22)."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class DataSubjectRight(Enum):
    """GDPR Data Subject Rights."""
    ACCESS = "access"  # Article 15
    RECTIFICATION = "rectification"  # Article 16
    ERASURE = "erasure"  # Article 17 (Right to be forgotten)
    RESTRICTION = "restriction"  # Article 18
    PORTABILITY = "portability"  # Article 20
    OBJECTION = "objection"  # Article 21


class RequestStatus(Enum):
    """Status of data subject request."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class RestrictionType(Enum):
    """Types of processing restriction."""
    FULL = "full"  # Stop all processing
    STORAGE_ONLY = "storage_only"  # Only store, no processing
    SPECIFIC_PURPOSE = "specific_purpose"  # Restrict to specific purposes


@dataclass
class VerificationToken:
    """Token for verifying data subject identity."""
    token: str
    user_id: str
    expires_at: datetime
    purpose: str


@dataclass
class DataAccessResponse:
    """Response to data access request (Article 15)."""
    request_id: UUID
    user_id: str
    requested_at: datetime
    completed_at: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErasureResult:
    """Result of data erasure request (Article 17)."""
    request_id: UUID
    user_id: str
    requested_at: datetime
    completed_at: datetime
    deleted_items: Dict[str, int]
    retained_items: Dict[str, List[str]]  # Items retained with legal justification
    total_deleted: int
    errors: List[str] = field(default_factory=list)


@dataclass
class RectificationResult:
    """Result of data rectification request (Article 16)."""
    request_id: UUID
    user_id: str
    requested_at: datetime
    completed_at: datetime
    corrected_fields: List[str]
    errors: List[str] = field(default_factory=list)


@dataclass
class RestrictionResult:
    """Result of processing restriction request (Article 18)."""
    request_id: UUID
    user_id: str
    requested_at: datetime
    completed_at: datetime
    restriction_type: RestrictionType
    restricted_operations: List[str]
    active_until: Optional[datetime] = None


class DataSubjectRights:
    """
    Implementation of GDPR Data Subject Rights (Articles 15-22).

    Must respond within 30 days (1 month) of request.
    """

    def __init__(
        self,
        db_pool,
        audit_logger,
        storage_manager,
    ):
        self.db = db_pool
        self.audit = audit_logger
        self.storage = storage_manager

    async def handle_access_request(
        self,
        user_id: str,
        request_id: Optional[UUID] = None,
        verification: Optional[VerificationToken] = None,
    ) -> DataAccessResponse:
        """
        Handle Right of Access request (GDPR Article 15).

        Must provide:
        - Confirmation of processing
        - Purposes of processing
        - Categories of data
        - Recipients
        - Retention periods
        - Rights information
        - Copy of personal data
        """
        request_id = request_id or uuid4()
        requested_at = datetime.utcnow()

        # Verify identity
        if verification:
            await self._verify_identity(user_id, verification)

        # Log request
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_ACCESS_REQUEST",
            user_id=user_id,
            request_type="access",
            details={"request_id": str(request_id)},
        )

        # Gather all user data
        data = await self._gather_user_data(user_id)

        # Log completion
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_EXPORTED",
            user_id=user_id,
            request_type="access",
            details={
                "request_id": str(request_id),
                "data_categories": list(data.keys()),
            },
        )

        return DataAccessResponse(
            request_id=request_id,
            user_id=user_id,
            requested_at=requested_at,
            completed_at=datetime.utcnow(),
            data=data,
            metadata={
                "response_time_seconds": (
                    datetime.utcnow() - requested_at
                ).total_seconds(),
            },
        )

    async def handle_portability_request(
        self,
        user_id: str,
        format: str = "json",
        verification: Optional[VerificationToken] = None,
    ) -> bytes:
        """
        Handle Right to Data Portability (GDPR Article 20).

        Must provide data in:
        - Structured format
        - Commonly used format
        - Machine-readable format
        """
        request_id = uuid4()

        # Verify identity
        if verification:
            await self._verify_identity(user_id, verification)

        # Log request
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_PORTABILITY_REQUEST",
            user_id=user_id,
            request_type="portability",
            details={"request_id": str(request_id), "format": format},
        )

        # Gather data
        data = await self._gather_user_data(user_id)

        # Export in requested format
        from ..audit.export import AuditLogExporter, ExportFormat

        exporter = AuditLogExporter(storage=None)  # Use GDPR-specific exporter

        export_content = await self._create_portability_export(user_id, data, format)

        # Log completion
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_EXPORTED",
            user_id=user_id,
            request_type="portability",
            details={"request_id": str(request_id)},
        )

        return export_content

    async def handle_erasure_request(
        self,
        user_id: str,
        verification: VerificationToken,
        request_id: Optional[UUID] = None,
    ) -> ErasureResult:
        """
        Handle Right to Erasure (GDPR Article 17 - Right to be Forgotten).

        Must delete unless:
        - Legal obligation requires retention
        - Public interest requires retention
        - Legal claims require retention
        """
        request_id = request_id or uuid4()
        requested_at = datetime.utcnow()

        # Verify identity (CRITICAL for deletion)
        await self._verify_identity(user_id, verification)

        # Log request
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_ERASURE_REQUEST",
            user_id=user_id,
            request_type="erasure",
            details={"request_id": str(request_id)},
        )

        deleted_items = {}
        retained_items = {}
        errors = []

        try:
            # Delete memories
            memory_count = await self._delete_user_memories(user_id)
            deleted_items["memories"] = memory_count

            # Delete sessions
            session_count = await self._delete_user_sessions(user_id)
            deleted_items["sessions"] = session_count

            # Delete user profile (if allowed)
            profile_deleted = await self._delete_user_profile(user_id)
            if profile_deleted:
                deleted_items["profile"] = 1
            else:
                retained_items["profile"] = [
                    "Retained for legal obligation (contract completion)"
                ]

            # Anonymize audit logs (can't delete for legal reasons)
            audit_anonymized = await self._anonymize_audit_logs(user_id)
            deleted_items["audit_logs_anonymized"] = audit_anonymized
            retained_items["audit_logs"] = [
                "Retained for 7 years (SOC2/legal requirement)",
                "Anonymized to remove personal data",
            ]

            # Delete API keys
            api_key_count = await self._delete_user_api_keys(user_id)
            deleted_items["api_keys"] = api_key_count

        except Exception as e:
            errors.append(f"Deletion error: {str(e)}")

        total_deleted = sum(deleted_items.values())

        # Log completion
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_ERASED",
            user_id=user_id,
            request_type="erasure",
            details={
                "request_id": str(request_id),
                "total_deleted": total_deleted,
                "deleted_items": deleted_items,
                "retained_items": list(retained_items.keys()),
            },
        )

        return ErasureResult(
            request_id=request_id,
            user_id=user_id,
            requested_at=requested_at,
            completed_at=datetime.utcnow(),
            deleted_items=deleted_items,
            retained_items=retained_items,
            total_deleted=total_deleted,
            errors=errors,
        )

    async def handle_rectification_request(
        self,
        user_id: str,
        corrections: Dict[str, Any],
        verification: VerificationToken,
    ) -> RectificationResult:
        """
        Handle Right to Rectification (GDPR Article 16).

        Allows users to correct inaccurate personal data.
        """
        request_id = uuid4()
        requested_at = datetime.utcnow()

        # Verify identity
        await self._verify_identity(user_id, verification)

        # Log request
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_RECTIFICATION_REQUEST",
            user_id=user_id,
            request_type="rectification",
            details={
                "request_id": str(request_id),
                "fields_to_correct": list(corrections.keys()),
            },
        )

        corrected_fields = []
        errors = []

        # Apply corrections
        for field, new_value in corrections.items():
            try:
                await self._update_user_field(user_id, field, new_value)
                corrected_fields.append(field)

                # Log each correction
                await self.audit.log_data_access(
                    user_id=user_id,
                    resource_type="user_profile",
                    resource_id=user_id,
                    access_type="update",
                    fields_accessed=[field],
                )

            except Exception as e:
                errors.append(f"Failed to correct {field}: {str(e)}")

        return RectificationResult(
            request_id=request_id,
            user_id=user_id,
            requested_at=requested_at,
            completed_at=datetime.utcnow(),
            corrected_fields=corrected_fields,
            errors=errors,
        )

    async def handle_restriction_request(
        self,
        user_id: str,
        restriction_type: RestrictionType,
        duration: Optional[timedelta] = None,
        verification: VerificationToken = None,
    ) -> RestrictionResult:
        """
        Handle Right to Restriction of Processing (GDPR Article 18).

        Allows users to limit how their data is processed.
        """
        request_id = uuid4()
        requested_at = datetime.utcnow()

        if verification:
            await self._verify_identity(user_id, verification)

        # Log request
        await self.audit.log_gdpr_event(
            event_type="GDPR_DATA_RESTRICTION_REQUEST",
            user_id=user_id,
            request_type="restriction",
            details={
                "request_id": str(request_id),
                "restriction_type": restriction_type.value,
            },
        )

        # Apply restriction
        restricted_operations = await self._apply_restriction(
            user_id,
            restriction_type,
        )

        active_until = None
        if duration:
            active_until = datetime.utcnow() + duration

        # Store restriction in database
        await self._store_restriction(
            user_id=user_id,
            restriction_type=restriction_type,
            active_until=active_until,
        )

        return RestrictionResult(
            request_id=request_id,
            user_id=user_id,
            requested_at=requested_at,
            completed_at=datetime.utcnow(),
            restriction_type=restriction_type,
            restricted_operations=restricted_operations,
            active_until=active_until,
        )

    # Helper methods

    async def _verify_identity(
        self,
        user_id: str,
        verification: VerificationToken,
    ) -> None:
        """Verify data subject identity."""
        if verification.user_id != user_id:
            raise ValueError("Verification token user_id mismatch")

        if verification.expires_at < datetime.utcnow():
            raise ValueError("Verification token expired")

        # Verify token in database
        # Implementation depends on token storage

    async def _gather_user_data(self, user_id: str) -> Dict[str, Any]:
        """Gather all user data for access request."""
        data = {
            "user_profile": await self._get_user_profile(user_id),
            "memories": await self._get_user_memories(user_id),
            "sessions": await self._get_user_sessions(user_id),
            "audit_logs": await self._get_user_audit_logs(user_id),
            "consents": await self._get_user_consents(user_id),
            "api_keys": await self._get_user_api_keys(user_id),
            "metadata": {
                "data_controller": "CONTINUUM AI Memory System",
                "export_timestamp": datetime.utcnow().isoformat(),
                "retention_periods": {
                    "memories": "2 years",
                    "audit_logs": "7 years",
                    "sessions": "90 days",
                },
            },
        }
        return data

    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data."""
        query = "SELECT * FROM users WHERE id = $1"
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else {}

    async def _get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user memories."""
        query = "SELECT * FROM memories WHERE user_id = $1"
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def _get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user sessions."""
        query = "SELECT * FROM sessions WHERE user_id = $1"
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def _get_user_audit_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all audit logs for user."""
        query = "SELECT * FROM audit_logs WHERE actor_id = $1 ORDER BY timestamp DESC LIMIT 10000"
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def _get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consent records."""
        query = "SELECT * FROM consents WHERE user_id = $1"
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def _get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user API keys (hashed)."""
        query = "SELECT id, created_at, last_used, description FROM api_keys WHERE user_id = $1"
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def _delete_user_memories(self, user_id: str) -> int:
        """Delete all user memories."""
        query = "DELETE FROM memories WHERE user_id = $1"
        async with self.db.acquire() as conn:
            result = await conn.execute(query, user_id)
            return int(result.split()[-1])

    async def _delete_user_sessions(self, user_id: str) -> int:
        """Delete all user sessions."""
        query = "DELETE FROM sessions WHERE user_id = $1"
        async with self.db.acquire() as conn:
            result = await conn.execute(query, user_id)
            return int(result.split()[-1])

    async def _delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile (if allowed)."""
        # Check if deletion is allowed (no active subscriptions, etc.)
        # For now, just mark as deleted
        query = "UPDATE users SET deleted_at = $1, email = $2 WHERE id = $3"
        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(),
                f"deleted_{user_id}@example.com",
                user_id,
            )
            return True

    async def _anonymize_audit_logs(self, user_id: str) -> int:
        """Anonymize audit logs (can't delete for legal reasons)."""
        query = """
            UPDATE audit_logs
            SET actor_email = NULL,
                actor_name = 'ANONYMIZED',
                ip_address = NULL,
                user_agent = NULL
            WHERE actor_id = $1
        """
        async with self.db.acquire() as conn:
            result = await conn.execute(query, user_id)
            return int(result.split()[-1])

    async def _delete_user_api_keys(self, user_id: str) -> int:
        """Delete user API keys."""
        query = "DELETE FROM api_keys WHERE user_id = $1"
        async with self.db.acquire() as conn:
            result = await conn.execute(query, user_id)
            return int(result.split()[-1])

    async def _update_user_field(
        self,
        user_id: str,
        field: str,
        value: Any,
    ) -> None:
        """Update a user profile field."""
        # Validate field is allowed to be updated
        allowed_fields = ["email", "name", "phone", "address"]
        if field not in allowed_fields:
            raise ValueError(f"Field {field} cannot be updated")

        query = f"UPDATE users SET {field} = $1 WHERE id = $2"
        async with self.db.acquire() as conn:
            await conn.execute(query, value, user_id)

    async def _apply_restriction(
        self,
        user_id: str,
        restriction_type: RestrictionType,
    ) -> List[str]:
        """Apply processing restriction."""
        if restriction_type == RestrictionType.FULL:
            return ["all_processing"]
        elif restriction_type == RestrictionType.STORAGE_ONLY:
            return ["analysis", "sharing", "automated_decisions"]
        else:
            return []

    async def _store_restriction(
        self,
        user_id: str,
        restriction_type: RestrictionType,
        active_until: Optional[datetime],
    ) -> None:
        """Store restriction in database."""
        query = """
            INSERT INTO processing_restrictions
            (user_id, restriction_type, active_until, created_at)
            VALUES ($1, $2, $3, $4)
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                user_id,
                restriction_type.value,
                active_until,
                datetime.utcnow(),
            )

    async def _create_portability_export(
        self,
        user_id: str,
        data: Dict[str, Any],
        format: str,
    ) -> bytes:
        """Create portability export in requested format."""
        import json

        if format == "json":
            return json.dumps(data, indent=2).encode("utf-8")
        else:
            raise ValueError(f"Unsupported format: {format}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
