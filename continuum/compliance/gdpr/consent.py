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

"""GDPR Consent Management (Articles 6, 7, 8)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ConsentType(Enum):
    """Types of consent required."""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    PROFILING = "profiling"
    AUTOMATED_DECISIONS = "automated_decisions"
    SPECIAL_CATEGORY_DATA = "special_category_data"  # Art. 9
    MINORS = "minors"  # Art. 8


class LegalBasis(Enum):
    """Legal basis for processing (GDPR Article 6)."""
    CONSENT = "consent"  # Art. 6(1)(a)
    CONTRACT = "contract"  # Art. 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Art. 6(1)(c)
    VITAL_INTERESTS = "vital_interests"  # Art. 6(1)(d)
    PUBLIC_TASK = "public_task"  # Art. 6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Art. 6(1)(f)


class ConsentMethod(Enum):
    """How consent was obtained."""
    EXPLICIT = "explicit"  # Clear affirmative action
    IMPLIED = "implied"  # From context/behavior
    OPT_IN = "opt_in"  # User actively opted in
    OPT_OUT = "opt_out"  # User didn't opt out (NOT GDPR COMPLIANT)


@dataclass
class ConsentRecord:
    """Record of user consent."""
    # Required fields first
    user_id: str
    consent_type: ConsentType
    granted: bool
    legal_basis: LegalBasis
    purpose: str
    method: ConsentMethod

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # GDPR requires tracking when/how consent was given
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    consent_text: Optional[str] = None  # Exact text shown to user
    consent_version: Optional[str] = None  # Version of terms

    # For withdrawal tracking
    withdrawn_at: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "consent_type": self.consent_type.value,
            "granted": self.granted,
            "legal_basis": self.legal_basis.value,
            "purpose": self.purpose,
            "method": self.method.value,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "consent_text": self.consent_text,
            "consent_version": self.consent_version,
            "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None,
            "withdrawal_reason": self.withdrawal_reason,
            "metadata": self.metadata,
        }


class ConsentManager:
    """
    GDPR Consent Management System.

    Requirements (Article 7):
    - Easy to withdraw as to give
    - Clear and distinguishable
    - Freely given, specific, informed, unambiguous
    - Separate from other terms
    - Verifiable (who, when, how)
    """

    def __init__(self, db_pool, audit_logger):
        self.db = db_pool
        self.audit = audit_logger

    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        purpose: str,
        legal_basis: LegalBasis = LegalBasis.CONSENT,
        method: ConsentMethod = ConsentMethod.EXPLICIT,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_text: Optional[str] = None,
        consent_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConsentRecord:
        """
        Record user consent with full audit trail.

        GDPR requires demonstrable consent:
        - Who gave consent
        - When they gave consent
        - What they were told
        - How they gave consent
        - Whether they have withdrawn
        """
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            legal_basis=legal_basis,
            purpose=purpose,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=consent_text,
            consent_version=consent_version,
            metadata=metadata or {},
        )

        # Store in database
        query = """
            INSERT INTO consents (
                id, user_id, consent_type, granted, legal_basis,
                purpose, method, timestamp,
                ip_address, user_agent, consent_text, consent_version,
                metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                str(record.id),
                record.user_id,
                record.consent_type.value,
                record.granted,
                record.legal_basis.value,
                record.purpose,
                record.method.value,
                record.timestamp,
                record.ip_address,
                record.user_agent,
                record.consent_text,
                record.consent_version,
                record.metadata,
            )

        # Audit log
        await self.audit.log_gdpr_event(
            event_type="GDPR_CONSENT_GIVEN" if granted else "GDPR_CONSENT_WITHDRAWN",
            user_id=user_id,
            request_type="consent",
            details={
                "consent_id": str(record.id),
                "consent_type": consent_type.value,
                "granted": granted,
                "purpose": purpose,
            },
        )

        return record

    async def check_consent(
        self,
        user_id: str,
        purpose: str,
        consent_type: Optional[ConsentType] = None,
    ) -> bool:
        """
        Check if user has given consent for a purpose.

        Returns True only if:
        - Explicit consent was given
        - Consent has not been withdrawn
        - Consent is still valid (not expired)
        """
        query = """
            SELECT granted, withdrawn_at
            FROM consents
            WHERE user_id = $1
              AND purpose = $2
              AND ($3::text IS NULL OR consent_type = $3)
            ORDER BY timestamp DESC
            LIMIT 1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id,
                purpose,
                consent_type.value if consent_type else None,
            )

            if not row:
                return False

            # Check if granted and not withdrawn
            return row["granted"] and row["withdrawn_at"] is None

    async def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        reason: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Withdraw previously given consent.

        GDPR Article 7(3): Must be as easy to withdraw as to give.
        """
        # Create withdrawal record
        record = await self.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False,
            purpose=f"Withdrawal of {consent_type.value}",
            legal_basis=LegalBasis.CONSENT,
            metadata={"withdrawal_reason": reason} if reason else {},
        )

        # Update previous consent records
        query = """
            UPDATE consents
            SET withdrawn_at = $1, withdrawal_reason = $2
            WHERE user_id = $3
              AND consent_type = $4
              AND granted = true
              AND withdrawn_at IS NULL
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(),
                reason,
                user_id,
                consent_type.value,
            )

        return record

    async def update_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        purpose: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """Update consent (creates new record for audit trail)."""
        record = await self.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            purpose=purpose,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.audit.log_gdpr_event(
            event_type="GDPR_CONSENT_UPDATED",
            user_id=user_id,
            request_type="consent_update",
            details={
                "consent_id": str(record.id),
                "consent_type": consent_type.value,
                "granted": granted,
            },
        )

        return record

    async def get_consent_history(
        self,
        user_id: str,
        consent_type: Optional[ConsentType] = None,
    ) -> List[ConsentRecord]:
        """Get full consent history for audit."""
        query = """
            SELECT * FROM consents
            WHERE user_id = $1
              AND ($2::text IS NULL OR consent_type = $2)
            ORDER BY timestamp DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                query,
                user_id,
                consent_type.value if consent_type else None,
            )

            return [self._row_to_record(row) for row in rows]

    async def get_active_consents(
        self,
        user_id: str,
    ) -> Dict[ConsentType, ConsentRecord]:
        """Get all active (not withdrawn) consents for a user."""
        query = """
            SELECT DISTINCT ON (consent_type) *
            FROM consents
            WHERE user_id = $1
              AND granted = true
              AND withdrawn_at IS NULL
            ORDER BY consent_type, timestamp DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)

            return {
                ConsentType(row["consent_type"]): self._row_to_record(row)
                for row in rows
            }

    async def bulk_withdraw_consent(
        self,
        user_id: str,
        reason: Optional[str] = None,
    ) -> List[ConsentRecord]:
        """Withdraw all consents (used for account deletion)."""
        # Get all active consents
        active = await self.get_active_consents(user_id)

        # Withdraw each
        records = []
        for consent_type in active.keys():
            record = await self.withdraw_consent(
                user_id=user_id,
                consent_type=consent_type,
                reason=reason or "Account deletion",
            )
            records.append(record)

        return records

    async def verify_consent_age(
        self,
        user_id: str,
        age: int,
        parental_consent: bool = False,
    ) -> bool:
        """
        Verify consent age requirements (GDPR Article 8).

        - Under 16: Requires parental consent (can be lower in some countries)
        - 16+: Can give consent themselves
        """
        if age >= 16:
            return True

        return parental_consent

    async def get_consent_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get consent statistics for compliance reporting."""
        query = """
            SELECT
                consent_type,
                COUNT(*) as total,
                SUM(CASE WHEN granted THEN 1 ELSE 0 END) as granted,
                SUM(CASE WHEN NOT granted THEN 1 ELSE 0 END) as declined,
                SUM(CASE WHEN withdrawn_at IS NOT NULL THEN 1 ELSE 0 END) as withdrawn
            FROM consents
            WHERE ($1::text IS NULL OR user_id IN (
                SELECT id FROM users WHERE tenant_id = $1
            ))
            GROUP BY consent_type
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, tenant_id)

            stats = {
                "total_consent_records": 0,
                "by_type": {},
            }

            for row in rows:
                consent_type = row["consent_type"]
                stats["by_type"][consent_type] = {
                    "total": row["total"],
                    "granted": row["granted"],
                    "declined": row["declined"],
                    "withdrawn": row["withdrawn"],
                    "consent_rate": (
                        row["granted"] / row["total"] * 100
                        if row["total"] > 0
                        else 0
                    ),
                }
                stats["total_consent_records"] += row["total"]

            return stats

    def _row_to_record(self, row) -> ConsentRecord:
        """Convert database row to ConsentRecord."""
        return ConsentRecord(
            id=UUID(row["id"]),
            user_id=row["user_id"],
            consent_type=ConsentType(row["consent_type"]),
            granted=row["granted"],
            legal_basis=LegalBasis(row["legal_basis"]),
            purpose=row["purpose"],
            method=ConsentMethod(row["method"]),
            timestamp=row["timestamp"],
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            consent_text=row.get("consent_text"),
            consent_version=row.get("consent_version"),
            withdrawn_at=row.get("withdrawn_at"),
            withdrawal_reason=row.get("withdrawal_reason"),
            metadata=row.get("metadata", {}),
        )


# SQL Schema for consent tracking
CONSENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    granted BOOLEAN NOT NULL,
    legal_basis TEXT NOT NULL,
    purpose TEXT NOT NULL,
    method TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Audit trail
    ip_address INET,
    user_agent TEXT,
    consent_text TEXT,  -- Exact text shown to user
    consent_version TEXT,  -- Version of privacy policy/terms

    -- Withdrawal tracking
    withdrawn_at TIMESTAMPTZ,
    withdrawal_reason TEXT,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_consents_user ON consents (user_id);
CREATE INDEX idx_consents_type ON consents (consent_type);
CREATE INDEX idx_consents_timestamp ON consents (timestamp DESC);
CREATE INDEX idx_consents_active ON consents (user_id, consent_type, granted, withdrawn_at);
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
