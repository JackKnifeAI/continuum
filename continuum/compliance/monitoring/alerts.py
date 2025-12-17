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

"""Compliance alert management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of compliance alerts."""
    ANOMALY_DETECTED = "anomaly_detected"
    POLICY_VIOLATION = "policy_violation"
    GDPR_REQUEST_OVERDUE = "gdpr_request_overdue"
    RETENTION_FAILURE = "retention_failure"
    ACCESS_DENIED = "access_denied"
    AUDIT_LOG_INTEGRITY = "audit_log_integrity"
    ENCRYPTION_FAILURE = "encryption_failure"
    BACKUP_FAILURE = "backup_failure"


@dataclass
class Alert:
    """Compliance alert."""
    # Required fields first
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplianceAlertManager:
    """Manage compliance alerts and notifications."""

    def __init__(self, db_pool, audit_logger):
        self.db = db_pool
        self.audit = audit_logger

    async def create_alert(
        self,
        type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create a new compliance alert."""
        alert = Alert(
            type=type,
            severity=severity,
            title=title,
            description=description,
            details=details or {},
        )

        # Store in database
        query = """
            INSERT INTO compliance_alerts
            (id, type, severity, title, description, details, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                str(alert.id),
                alert.type.value,
                alert.severity.value,
                alert.title,
                alert.description,
                alert.details,
                alert.created_at,
            )

        # Log to audit
        await self.audit.log_gdpr_event(
            event_type="SYSTEM_ALERT",
            user_id="system",
            request_type="compliance_alert",
            details={
                "alert_id": str(alert.id),
                "alert_type": alert.type.value,
                "severity": alert.severity.value,
            },
        )

        # Send notifications based on severity
        await self._send_notifications(alert)

        return alert

    async def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> None:
        """Mark an alert as resolved."""
        query = """
            UPDATE compliance_alerts
            SET resolved = true,
                resolved_at = $1,
                resolved_by = $2,
                resolution_notes = $3
            WHERE id = $4
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(),
                resolved_by,
                resolution_notes,
                str(alert_id),
            )

    async def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """Get all unresolved alerts."""
        query = """
            SELECT * FROM compliance_alerts
            WHERE resolved = false
              AND ($1::text IS NULL OR severity = $1)
            ORDER BY created_at DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                query,
                severity.value if severity else None,
            )

        return [self._row_to_alert(row) for row in rows]

    async def alert_anomaly(
        self,
        anomaly,  # Anomaly object
    ) -> Alert:
        """Create alert from anomaly."""
        severity_map = {
            "low": AlertSeverity.LOW,
            "medium": AlertSeverity.MEDIUM,
            "high": AlertSeverity.HIGH,
            "critical": AlertSeverity.CRITICAL,
        }

        return await self.create_alert(
            type=AlertType.ANOMALY_DETECTED,
            severity=severity_map.get(anomaly.severity, AlertSeverity.MEDIUM),
            title=f"Anomaly Detected: {anomaly.type.value}",
            description=anomaly.description,
            details={
                "anomaly_id": str(anomaly.id),
                "anomaly_type": anomaly.type.value,
                "user_id": anomaly.user_id,
                **anomaly.details,
            },
        )

    async def alert_gdpr_request_overdue(
        self,
        request_id: str,
        user_id: str,
        days_overdue: int,
    ) -> Alert:
        """Alert for GDPR request past 30-day deadline."""
        return await self.create_alert(
            type=AlertType.GDPR_REQUEST_OVERDUE,
            severity=AlertSeverity.CRITICAL,
            title=f"GDPR Request Overdue: {request_id}",
            description=f"Data subject request is {days_overdue} days past the 30-day deadline",
            details={
                "request_id": request_id,
                "user_id": user_id,
                "days_overdue": days_overdue,
            },
        )

    async def alert_audit_integrity_failure(
        self,
        details: Dict[str, Any],
    ) -> Alert:
        """Alert for audit log integrity check failure."""
        return await self.create_alert(
            type=AlertType.AUDIT_LOG_INTEGRITY,
            severity=AlertSeverity.CRITICAL,
            title="Audit Log Integrity Failure",
            description="Cryptographic chain verification failed",
            details=details,
        )

    async def _send_notifications(self, alert: Alert) -> None:
        """
        Send notifications for alert.

        Would integrate with:
        - Email (SendGrid, SES)
        - Slack
        - PagerDuty
        - SMS (Twilio)
        """
        # Critical alerts should page on-call
        if alert.severity == AlertSeverity.CRITICAL:
            # await self._page_oncall(alert)
            pass

        # High/Critical should email admins
        if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            # await self._email_admins(alert)
            pass

        # All alerts should go to Slack
        # await self._post_to_slack(alert)
        pass

    def _row_to_alert(self, row) -> Alert:
        """Convert database row to Alert."""
        return Alert(
            id=UUID(row["id"]),
            type=AlertType(row["type"]),
            severity=AlertSeverity(row["severity"]),
            title=row["title"],
            description=row["description"],
            details=row.get("details", {}),
            created_at=row["created_at"],
            resolved=row["resolved"],
            resolved_at=row.get("resolved_at"),
            resolved_by=row.get("resolved_by"),
            resolution_notes=row.get("resolution_notes"),
        )


# SQL Schema for alerts
ALERTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS compliance_alerts (
    id UUID PRIMARY KEY,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolution_notes TEXT
);

CREATE INDEX idx_alerts_active ON compliance_alerts (resolved, created_at DESC)
    WHERE NOT resolved;
CREATE INDEX idx_alerts_severity ON compliance_alerts (severity, created_at DESC);
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
