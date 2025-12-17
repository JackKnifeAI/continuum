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

"""GDPR Data Retention Management (Article 5(1)(e))."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class RetentionPeriod(Enum):
    """Standard retention periods."""
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    YEAR_1 = 365
    YEAR_2 = 730
    YEAR_7 = 2555  # SOC2 requirement
    INDEFINITE = -1  # Requires explicit legal basis


@dataclass
class RetentionPolicy:
    """Data retention policy definition."""
    # Required fields first
    name: str
    resource_type: str
    retention_days: int
    legal_basis: str
    description: str

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    auto_delete: bool = True
    grace_period_days: int = 30  # Soft delete grace period
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetentionResult:
    """Result of retention policy application."""
    policy_id: UUID
    execution_time: datetime
    items_evaluated: int
    items_deleted: int
    items_retained: int
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduledDeletion:
    """Scheduled future deletion."""
    # Required fields first
    resource_type: str
    resource_id: str
    deletion_date: datetime
    reason: str

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed: bool = False
    executed_at: Optional[datetime] = None


class DataRetentionManager:
    """
    GDPR-compliant data retention management.

    Article 5(1)(e): Data must be kept no longer than necessary
    for the purposes for which it is processed.
    """

    # Default retention policies
    DEFAULT_POLICIES = {
        "memories": RetentionPolicy(
            name="AI Memory Retention",
            resource_type="memory",
            retention_days=RetentionPeriod.YEAR_2.value,
            legal_basis="Performance of contract (Art. 6(1)(b))",
            description="AI conversation memories retained for 2 years",
        ),
        "sessions": RetentionPolicy(
            name="Session Data Retention",
            resource_type="session",
            retention_days=RetentionPeriod.DAYS_90.value,
            legal_basis="Legitimate interests (Art. 6(1)(f))",
            description="Session data retained for 90 days",
        ),
        "audit_logs": RetentionPolicy(
            name="Audit Log Retention",
            resource_type="audit_log",
            retention_days=RetentionPeriod.YEAR_7.value,
            legal_basis="Legal obligation (Art. 6(1)(c)) - SOC2 compliance",
            description="Audit logs retained for 7 years",
            auto_delete=False,  # Manual review required
        ),
        "deleted_data": RetentionPolicy(
            name="Soft Delete Grace Period",
            resource_type="deleted_data",
            retention_days=RetentionPeriod.DAYS_30.value,
            legal_basis="Legitimate interests (Art. 6(1)(f))",
            description="Deleted data kept for 30 days for recovery",
        ),
        "backups": RetentionPolicy(
            name="Backup Retention",
            resource_type="backup",
            retention_days=RetentionPeriod.DAYS_90.value,
            legal_basis="Legitimate interests (Art. 6(1)(f))",
            description="Backups retained for 90 days",
        ),
    }

    def __init__(self, db_pool, audit_logger):
        self.db = db_pool
        self.audit = audit_logger

    async def apply_retention_policy(
        self,
        policy: RetentionPolicy,
        dry_run: bool = False,
    ) -> RetentionResult:
        """
        Apply retention policy and delete expired data.

        Args:
            policy: Retention policy to apply
            dry_run: If True, don't actually delete (for testing)

        Returns:
            Result summary
        """
        execution_time = datetime.utcnow()
        cutoff_date = execution_time - timedelta(days=policy.retention_days)

        # Log policy execution
        await self.audit.log_gdpr_event(
            event_type="COMPLIANCE_RETENTION_APPLIED",
            user_id="system",
            request_type="retention",
            details={
                "policy_id": str(policy.id),
                "policy_name": policy.name,
                "resource_type": policy.resource_type,
                "cutoff_date": cutoff_date.isoformat(),
                "dry_run": dry_run,
            },
        )

        # Apply policy based on resource type
        if policy.resource_type == "memory":
            result = await self._apply_memory_retention(
                cutoff_date,
                dry_run,
            )
        elif policy.resource_type == "session":
            result = await self._apply_session_retention(
                cutoff_date,
                dry_run,
            )
        elif policy.resource_type == "audit_log":
            result = await self._apply_audit_retention(
                cutoff_date,
                dry_run,
            )
        elif policy.resource_type == "deleted_data":
            result = await self._apply_deleted_data_retention(
                cutoff_date,
                dry_run,
            )
        else:
            result = RetentionResult(
                policy_id=policy.id,
                execution_time=execution_time,
                items_evaluated=0,
                items_deleted=0,
                items_retained=0,
                errors=[f"Unknown resource type: {policy.resource_type}"],
            )

        return result

    async def apply_all_policies(
        self,
        dry_run: bool = False,
    ) -> Dict[str, RetentionResult]:
        """Apply all retention policies."""
        results = {}

        for policy_name, policy in self.DEFAULT_POLICIES.items():
            if policy.auto_delete:
                result = await self.apply_retention_policy(policy, dry_run)
                results[policy_name] = result

        return results

    async def schedule_deletion(
        self,
        resource_type: str,
        resource_id: str,
        deletion_date: datetime,
        reason: str,
    ) -> ScheduledDeletion:
        """Schedule future deletion of a resource."""
        scheduled = ScheduledDeletion(
            resource_type=resource_type,
            resource_id=resource_id,
            deletion_date=deletion_date,
            reason=reason,
        )

        query = """
            INSERT INTO scheduled_deletions
            (id, resource_type, resource_id, deletion_date, reason, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                str(scheduled.id),
                scheduled.resource_type,
                scheduled.resource_id,
                scheduled.deletion_date,
                scheduled.reason,
                scheduled.created_at,
            )

        return scheduled

    async def process_scheduled_deletions(
        self,
        dry_run: bool = False,
    ) -> List[ScheduledDeletion]:
        """Process all due scheduled deletions."""
        query = """
            SELECT * FROM scheduled_deletions
            WHERE deletion_date <= $1
              AND executed = false
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, datetime.utcnow())

        processed = []

        for row in rows:
            scheduled = self._row_to_scheduled_deletion(row)

            if not dry_run:
                # Execute deletion
                await self._delete_resource(
                    scheduled.resource_type,
                    scheduled.resource_id,
                )

                # Mark as executed
                update_query = """
                    UPDATE scheduled_deletions
                    SET executed = true, executed_at = $1
                    WHERE id = $2
                """

                async with self.db.acquire() as conn:
                    await conn.execute(
                        update_query,
                        datetime.utcnow(),
                        str(scheduled.id),
                    )

            processed.append(scheduled)

        return processed

    async def _apply_memory_retention(
        self,
        cutoff_date: datetime,
        dry_run: bool,
    ) -> RetentionResult:
        """Apply retention to memories."""
        # Find expired memories
        query = """
            SELECT COUNT(*) as count
            FROM memories
            WHERE created_at < $1
              AND deleted_at IS NULL
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, cutoff_date)
            items_evaluated = row["count"]

            items_deleted = 0
            if not dry_run and items_evaluated > 0:
                # Soft delete (move to deleted_memories table)
                delete_query = """
                    WITH deleted AS (
                        DELETE FROM memories
                        WHERE created_at < $1
                          AND deleted_at IS NULL
                        RETURNING *
                    )
                    INSERT INTO deleted_memories
                    SELECT *, NOW() as deleted_at FROM deleted
                """

                result = await conn.execute(delete_query, cutoff_date)
                items_deleted = int(result.split()[-1])

        return RetentionResult(
            policy_id=self.DEFAULT_POLICIES["memories"].id,
            execution_time=datetime.utcnow(),
            items_evaluated=items_evaluated,
            items_deleted=items_deleted,
            items_retained=items_evaluated - items_deleted,
        )

    async def _apply_session_retention(
        self,
        cutoff_date: datetime,
        dry_run: bool,
    ) -> RetentionResult:
        """Apply retention to sessions."""
        query = """
            SELECT COUNT(*) as count
            FROM sessions
            WHERE last_activity < $1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, cutoff_date)
            items_evaluated = row["count"]

            items_deleted = 0
            if not dry_run and items_evaluated > 0:
                delete_query = """
                    DELETE FROM sessions
                    WHERE last_activity < $1
                """

                result = await conn.execute(delete_query, cutoff_date)
                items_deleted = int(result.split()[-1])

        return RetentionResult(
            policy_id=self.DEFAULT_POLICIES["sessions"].id,
            execution_time=datetime.utcnow(),
            items_evaluated=items_evaluated,
            items_deleted=items_deleted,
            items_retained=items_evaluated - items_deleted,
        )

    async def _apply_audit_retention(
        self,
        cutoff_date: datetime,
        dry_run: bool,
    ) -> RetentionResult:
        """
        Apply retention to audit logs.

        Note: Audit logs should generally NOT be deleted
        due to SOC2 requirements (7 years).
        """
        # Just count, don't delete
        query = """
            SELECT COUNT(*) as count
            FROM audit_logs
            WHERE timestamp < $1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, cutoff_date)
            items_evaluated = row["count"]

        return RetentionResult(
            policy_id=self.DEFAULT_POLICIES["audit_logs"].id,
            execution_time=datetime.utcnow(),
            items_evaluated=items_evaluated,
            items_deleted=0,
            items_retained=items_evaluated,
            details={"note": "Audit logs retained for legal compliance"},
        )

    async def _apply_deleted_data_retention(
        self,
        cutoff_date: datetime,
        dry_run: bool,
    ) -> RetentionResult:
        """Permanently delete soft-deleted data after grace period."""
        query = """
            SELECT COUNT(*) as count
            FROM deleted_memories
            WHERE deleted_at < $1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, cutoff_date)
            items_evaluated = row["count"]

            items_deleted = 0
            if not dry_run and items_evaluated > 0:
                # Permanent deletion
                delete_query = """
                    DELETE FROM deleted_memories
                    WHERE deleted_at < $1
                """

                result = await conn.execute(delete_query, cutoff_date)
                items_deleted = int(result.split()[-1])

        return RetentionResult(
            policy_id=self.DEFAULT_POLICIES["deleted_data"].id,
            execution_time=datetime.utcnow(),
            items_evaluated=items_evaluated,
            items_deleted=items_deleted,
            items_retained=0,
            details={"note": "Permanent deletion of soft-deleted data"},
        )

    async def _delete_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> None:
        """Delete a specific resource."""
        if resource_type == "memory":
            query = "DELETE FROM memories WHERE id = $1"
        elif resource_type == "session":
            query = "DELETE FROM sessions WHERE id = $1"
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

        async with self.db.acquire() as conn:
            await conn.execute(query, resource_id)

    def _row_to_scheduled_deletion(self, row) -> ScheduledDeletion:
        """Convert database row to ScheduledDeletion."""
        return ScheduledDeletion(
            id=UUID(row["id"]),
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            deletion_date=row["deletion_date"],
            reason=row["reason"],
            created_at=row["created_at"],
            executed=row["executed"],
            executed_at=row.get("executed_at"),
        )


# SQL Schema for retention management
RETENTION_SCHEMA = """
-- Scheduled deletions
CREATE TABLE IF NOT EXISTS scheduled_deletions (
    id UUID PRIMARY KEY,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    deletion_date TIMESTAMPTZ NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed BOOLEAN NOT NULL DEFAULT FALSE,
    executed_at TIMESTAMPTZ
);

CREATE INDEX idx_scheduled_deletions_date ON scheduled_deletions (deletion_date)
    WHERE NOT executed;

-- Soft-deleted memories (grace period)
CREATE TABLE IF NOT EXISTS deleted_memories (
    LIKE memories INCLUDING ALL,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deleted_memories_date ON deleted_memories (deleted_at);

-- Retention audit log
CREATE TABLE IF NOT EXISTS retention_executions (
    id UUID PRIMARY KEY,
    policy_name TEXT NOT NULL,
    execution_time TIMESTAMPTZ NOT NULL,
    items_evaluated INTEGER NOT NULL,
    items_deleted INTEGER NOT NULL,
    dry_run BOOLEAN NOT NULL,
    details JSONB
);
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
