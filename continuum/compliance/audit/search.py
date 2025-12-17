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

"""Advanced audit log search with analytics."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .events import AuditLogEntry, AuditEventType, Outcome
from .storage import AuditLogStorage


class AuditLogSearch:
    """
    Advanced search and analytics for audit logs.

    Features:
    - Compliance-focused queries
    - User activity tracking
    - Anomaly detection patterns
    - Report generation helpers
    """

    def __init__(self, storage: AuditLogStorage):
        self.storage = storage

    async def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[AuditLogEntry]:
        """Get all activity for a user (GDPR Article 15)."""
        filters = {"actor_id": user_id}

        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time

        return await self.storage.query(filters, limit=limit)

    async def get_resource_access_history(
        self,
        resource_type: str,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Get all access to a specific resource."""
        filters = {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time

        return await self.storage.query(filters, limit=10000)

    async def get_failed_auth_attempts(
        self,
        hours: int = 24,
        threshold: int = 5,
    ) -> Dict[str, List[AuditLogEntry]]:
        """
        Find users with multiple failed auth attempts.

        Returns dict of user_id -> failed attempts
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)

        filters = {
            "event_type": AuditEventType.AUTH_LOGIN_FAILURE.value,
            "start_time": start_time,
        }

        entries = await self.storage.query(filters, limit=10000)

        # Group by user
        by_user = defaultdict(list)
        for entry in entries:
            if entry.actor_id:
                by_user[entry.actor_id].append(entry)

        # Filter by threshold
        return {
            user_id: attempts
            for user_id, attempts in by_user.items()
            if len(attempts) >= threshold
        }

    async def get_bulk_operations(
        self,
        hours: int = 24,
        threshold: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Detect bulk data operations (potential data exfiltration).

        Returns list of suspicious activity patterns.
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # Look for bulk reads, exports, deletes
        bulk_events = [
            AuditEventType.DATA_BULK_READ,
            AuditEventType.DATA_BULK_UPDATE,
            AuditEventType.DATA_BULK_DELETE,
            AuditEventType.DATA_EXPORT,
        ]

        suspicious = []

        for event_type in bulk_events:
            filters = {
                "event_type": event_type.value,
                "start_time": start_time,
            }

            entries = await self.storage.query(filters, limit=10000)

            # Group by user and count
            by_user = defaultdict(int)
            for entry in entries:
                if entry.actor_id:
                    by_user[entry.actor_id] += 1

            # Flag users exceeding threshold
            for user_id, count in by_user.items():
                if count >= threshold:
                    suspicious.append({
                        "user_id": user_id,
                        "event_type": event_type.value,
                        "count": count,
                        "time_window_hours": hours,
                    })

        return suspicious

    async def get_off_hours_access(
        self,
        user_id: str,
        business_hours_start: int = 9,  # 9 AM
        business_hours_end: int = 17,  # 5 PM
        days: int = 30,
    ) -> List[AuditLogEntry]:
        """Find off-hours access for a user."""
        start_time = datetime.utcnow() - timedelta(days=days)

        filters = {
            "actor_id": user_id,
            "start_time": start_time,
        }

        entries = await self.storage.query(filters, limit=10000)

        # Filter to off-hours (naive implementation)
        off_hours = [
            entry
            for entry in entries
            if entry.timestamp.hour < business_hours_start
            or entry.timestamp.hour >= business_hours_end
            or entry.timestamp.weekday() >= 5  # Weekend
        ]

        return off_hours

    async def get_gdpr_processing_activities(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Generate GDPR Article 30 record of processing activities.

        Returns summary of all data processing for a tenant.
        """
        filters = {
            "tenant_id": tenant_id,
            "compliance_tag": "gdpr_processing",
            "start_time": start_time,
            "end_time": end_time,
        }

        entries = await self.storage.query(filters, limit=100000)

        # Analyze processing
        summary = {
            "tenant_id": tenant_id,
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_operations": len(entries),
            "by_type": defaultdict(int),
            "by_resource": defaultdict(int),
            "unique_users": set(),
            "data_subjects_affected": set(),
        }

        for entry in entries:
            summary["by_type"][entry.event_type.value] += 1
            if entry.resource_type:
                summary["by_resource"][entry.resource_type] += 1
            if entry.actor_id:
                summary["unique_users"].add(entry.actor_id)
            if entry.resource_id:
                summary["data_subjects_affected"].add(entry.resource_id)

        # Convert sets to counts
        summary["unique_users"] = len(summary["unique_users"])
        summary["data_subjects_affected"] = len(summary["data_subjects_affected"])
        summary["by_type"] = dict(summary["by_type"])
        summary["by_resource"] = dict(summary["by_resource"])

        return summary

    async def get_access_control_violations(
        self,
        hours: int = 24,
    ) -> List[AuditLogEntry]:
        """Get all access denied events."""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        filters = {
            "event_type": AuditEventType.SECURITY_ACCESS_DENIED.value,
            "start_time": start_time,
        }

        return await self.storage.query(filters, limit=10000)

    async def get_sensitive_data_access(
        self,
        user_id: Optional[str] = None,
        hours: int = 24,
    ) -> List[AuditLogEntry]:
        """Get all sensitive data access events."""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        filters = {
            "start_time": start_time,
            # Would need to add is_sensitive to query filters
        }

        if user_id:
            filters["actor_id"] = user_id

        entries = await self.storage.query(filters, limit=10000)

        # Filter to sensitive events
        return [entry for entry in entries if entry.is_sensitive]

    async def get_compliance_report_data(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Get comprehensive compliance report data.

        Includes:
        - Total events
        - Events by type
        - Auth events
        - Data access events
        - Failed operations
        - Anomalies detected
        """
        filters = {
            "tenant_id": tenant_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        entries = await self.storage.query(filters, limit=100000)

        report = {
            "tenant_id": tenant_id,
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_events": len(entries),
            "events_by_type": defaultdict(int),
            "events_by_outcome": defaultdict(int),
            "unique_users": set(),
            "auth_events": {
                "total": 0,
                "successful_logins": 0,
                "failed_logins": 0,
                "password_changes": 0,
                "mfa_enabled": 0,
            },
            "data_events": {
                "total": 0,
                "reads": 0,
                "writes": 0,
                "updates": 0,
                "deletes": 0,
                "exports": 0,
            },
            "security_events": {
                "access_denied": 0,
                "anomalies": 0,
                "rate_limits": 0,
            },
            "gdpr_events": {
                "data_requests": 0,
                "erasures": 0,
                "exports": 0,
                "consents_given": 0,
                "consents_withdrawn": 0,
            },
        }

        for entry in entries:
            report["events_by_type"][entry.event_type.value] += 1
            report["events_by_outcome"][entry.outcome.value] += 1

            if entry.actor_id:
                report["unique_users"].add(entry.actor_id)

            # Categorize events
            event_value = entry.event_type.value

            if event_value.startswith("auth."):
                report["auth_events"]["total"] += 1
                if entry.event_type == AuditEventType.AUTH_LOGIN_SUCCESS:
                    report["auth_events"]["successful_logins"] += 1
                elif entry.event_type == AuditEventType.AUTH_LOGIN_FAILURE:
                    report["auth_events"]["failed_logins"] += 1
                elif entry.event_type == AuditEventType.AUTH_PASSWORD_CHANGE:
                    report["auth_events"]["password_changes"] += 1
                elif entry.event_type == AuditEventType.AUTH_MFA_ENABLED:
                    report["auth_events"]["mfa_enabled"] += 1

            elif event_value.startswith("data."):
                report["data_events"]["total"] += 1
                if "read" in event_value:
                    report["data_events"]["reads"] += 1
                elif "create" in event_value:
                    report["data_events"]["writes"] += 1
                elif "update" in event_value:
                    report["data_events"]["updates"] += 1
                elif "delete" in event_value:
                    report["data_events"]["deletes"] += 1
                elif "export" in event_value:
                    report["data_events"]["exports"] += 1

            elif event_value.startswith("security."):
                if entry.event_type == AuditEventType.SECURITY_ACCESS_DENIED:
                    report["security_events"]["access_denied"] += 1
                elif entry.event_type == AuditEventType.SECURITY_ANOMALY_DETECTED:
                    report["security_events"]["anomalies"] += 1
                elif entry.event_type == AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED:
                    report["security_events"]["rate_limits"] += 1

            elif event_value.startswith("gdpr."):
                if "request" in event_value:
                    report["gdpr_events"]["data_requests"] += 1
                elif entry.event_type == AuditEventType.GDPR_DATA_ERASED:
                    report["gdpr_events"]["erasures"] += 1
                elif entry.event_type == AuditEventType.GDPR_DATA_EXPORTED:
                    report["gdpr_events"]["exports"] += 1
                elif entry.event_type == AuditEventType.GDPR_CONSENT_GIVEN:
                    report["gdpr_events"]["consents_given"] += 1
                elif entry.event_type == AuditEventType.GDPR_CONSENT_WITHDRAWN:
                    report["gdpr_events"]["consents_withdrawn"] += 1

        # Convert sets to counts
        report["unique_users"] = len(report["unique_users"])
        report["events_by_type"] = dict(report["events_by_type"])
        report["events_by_outcome"] = dict(report["events_by_outcome"])

        return report

    async def search_by_correlation_id(
        self,
        correlation_id: str,
    ) -> List[AuditLogEntry]:
        """Find all events in a correlation chain."""
        filters = {"correlation_id": correlation_id}
        return await self.storage.query(filters, limit=1000)

    async def search_by_session(
        self,
        session_id: str,
    ) -> List[AuditLogEntry]:
        """Get all events in a session."""
        filters = {"session_id": session_id}
        return await self.storage.query(filters, limit=10000)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
