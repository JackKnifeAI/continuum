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

"""Anomaly detection for compliance monitoring."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AnomalyType(Enum):
    """Types of anomalies."""
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    BULK_OPERATION = "bulk_operation"
    OFF_HOURS_ACCESS = "off_hours_access"
    FAILED_AUTH_SPIKE = "failed_auth_spike"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_IP = "suspicious_ip"
    RAPID_SUCCESSION = "rapid_succession"


@dataclass
class Anomaly:
    """Detected anomaly."""
    # Required fields first
    type: AnomalyType
    severity: str  # low, medium, high, critical

    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AnomalyDetector:
    """
    Detect anomalous behavior for compliance and security.

    Uses:
    - Statistical analysis
    - Rule-based detection
    - Machine learning (future)
    """

    def __init__(self, db_pool, audit_search):
        self.db = db_pool
        self.audit_search = audit_search

    async def detect_unusual_access(
        self,
        user_id: str,
        window: timedelta = timedelta(hours=24),
    ) -> List[Anomaly]:
        """
        Detect unusual data access patterns.

        Checks:
        - Access volume spike
        - Unusual time patterns
        - New resource types accessed
        - Unusual query patterns
        """
        anomalies = []

        # Get recent activity
        start_time = datetime.utcnow() - window
        activity = await self.audit_search.get_user_activity(
            user_id=user_id,
            start_time=start_time,
        )

        # Get historical baseline (30 days)
        baseline_start = datetime.utcnow() - timedelta(days=30)
        baseline_activity = await self.audit_search.get_user_activity(
            user_id=user_id,
            start_time=baseline_start,
            end_time=start_time,
        )

        # Calculate baseline rate
        baseline_rate = len(baseline_activity) / 30  # Per day
        current_rate = len(activity) / (window.total_seconds() / 86400)  # Per day

        # Spike detection (3x baseline)
        if current_rate > baseline_rate * 3:
            anomalies.append(
                Anomaly(
                    type=AnomalyType.UNUSUAL_ACCESS_PATTERN,
                    severity="high",
                    user_id=user_id,
                    description=f"Access rate {current_rate:.1f}/day exceeds baseline {baseline_rate:.1f}/day by 3x",
                    details={
                        "current_rate": current_rate,
                        "baseline_rate": baseline_rate,
                        "window_hours": window.total_seconds() / 3600,
                    },
                )
            )

        return anomalies

    async def detect_bulk_operations(
        self,
        hours: int = 24,
        threshold: int = 1000,
    ) -> List[Anomaly]:
        """
        Detect bulk data operations (potential exfiltration).

        Flags:
        - Large exports
        - Mass deletions
        - Rapid queries
        """
        anomalies = []

        bulk_activity = await self.audit_search.get_bulk_operations(
            hours=hours,
            threshold=threshold,
        )

        for activity in bulk_activity:
            anomalies.append(
                Anomaly(
                    type=AnomalyType.BULK_OPERATION,
                    severity="critical",
                    user_id=activity["user_id"],
                    description=f"Bulk {activity['event_type']}: {activity['count']} operations",
                    details=activity,
                )
            )

        return anomalies

    async def detect_off_hours_access(
        self,
        user_id: str,
        business_hours_start: int = 9,
        business_hours_end: int = 17,
    ) -> List[Anomaly]:
        """Detect access outside business hours."""
        anomalies = []

        off_hours = await self.audit_search.get_off_hours_access(
            user_id=user_id,
            business_hours_start=business_hours_start,
            business_hours_end=business_hours_end,
            days=30,
        )

        if len(off_hours) > 10:  # Threshold
            anomalies.append(
                Anomaly(
                    type=AnomalyType.OFF_HOURS_ACCESS,
                    severity="medium",
                    user_id=user_id,
                    description=f"Frequent off-hours access: {len(off_hours)} events in 30 days",
                    details={"count": len(off_hours)},
                )
            )

        return anomalies

    async def detect_failed_auth_spike(
        self,
        hours: int = 24,
        threshold: int = 5,
    ) -> List[Anomaly]:
        """Detect failed authentication spikes."""
        anomalies = []

        failed_attempts = await self.audit_search.get_failed_auth_attempts(
            hours=hours,
            threshold=threshold,
        )

        for user_id, attempts in failed_attempts.items():
            anomalies.append(
                Anomaly(
                    type=AnomalyType.FAILED_AUTH_SPIKE,
                    severity="high",
                    user_id=user_id,
                    description=f"Multiple failed login attempts: {len(attempts)} in {hours} hours",
                    details={
                        "attempts": len(attempts),
                        "window_hours": hours,
                    },
                )
            )

        return anomalies

    async def detect_privilege_escalation(
        self,
        user_id: str,
    ) -> List[Anomaly]:
        """Detect potential privilege escalation."""
        anomalies = []

        # Get role changes
        query = """
            SELECT * FROM role_assignments
            WHERE user_id = $1
            ORDER BY assigned_at DESC
            LIMIT 10
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, user_id)

        # Check for rapid role changes
        if len(rows) > 3:
            time_span = rows[0]["assigned_at"] - rows[-1]["assigned_at"]
            if time_span < timedelta(hours=24):
                anomalies.append(
                    Anomaly(
                        type=AnomalyType.PRIVILEGE_ESCALATION,
                        severity="critical",
                        user_id=user_id,
                        description=f"Multiple role changes ({len(rows)}) in {time_span}",
                        details={"role_changes": len(rows)},
                    )
                )

        return anomalies

    async def detect_all(
        self,
        user_id: Optional[str] = None,
    ) -> List[Anomaly]:
        """Run all anomaly detection checks."""
        anomalies = []

        if user_id:
            # User-specific checks
            anomalies.extend(await self.detect_unusual_access(user_id))
            anomalies.extend(await self.detect_off_hours_access(user_id))
            anomalies.extend(await self.detect_privilege_escalation(user_id))
        else:
            # System-wide checks
            anomalies.extend(await self.detect_bulk_operations())
            anomalies.extend(await self.detect_failed_auth_spike())

        return anomalies


# Example usage:
"""
detector = AnomalyDetector(db_pool, audit_search)

# Detect all anomalies for a user
user_anomalies = await detector.detect_all(user_id="user123")

# Detect system-wide anomalies
system_anomalies = await detector.detect_all()

# Specific detection
bulk_ops = await detector.detect_bulk_operations(hours=24, threshold=500)
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
