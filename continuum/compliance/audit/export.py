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

"""Audit log export for compliance and legal requirements."""

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from .events import AuditLogEntry
from .storage import AuditLogStorage


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"  # JSON Lines for streaming
    PDF = "pdf"  # For compliance reports


class AuditLogExporter:
    """
    Export audit logs for:
    - Legal discovery
    - Compliance audits
    - Forensic investigation
    - Data subject access requests
    """

    def __init__(self, storage: AuditLogStorage):
        self.storage = storage

    async def export_user_data(
        self,
        user_id: str,
        format: ExportFormat = ExportFormat.JSON,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bytes:
        """
        Export all audit logs for a user (GDPR Article 15).

        Used for data subject access requests.
        """
        filters = {"actor_id": user_id}

        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time

        entries = await self.storage.query(filters, limit=100000)

        return self._format_export(entries, format)

    async def export_tenant_data(
        self,
        tenant_id: str,
        format: ExportFormat = ExportFormat.JSON,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bytes:
        """Export all audit logs for a tenant."""
        filters = {"tenant_id": tenant_id}

        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time

        entries = await self.storage.query(filters, limit=100000)

        return self._format_export(entries, format)

    async def export_compliance_logs(
        self,
        compliance_tag: str,
        start_time: datetime,
        end_time: datetime,
        format: ExportFormat = ExportFormat.JSON,
    ) -> bytes:
        """
        Export logs for specific compliance framework.

        Examples:
        - compliance_tag="soc2_cc6.1" for SOC2 access control
        - compliance_tag="gdpr" for GDPR processing
        - compliance_tag="hipaa_164.312" for HIPAA security
        """
        filters = {
            "compliance_tag": compliance_tag,
            "start_time": start_time,
            "end_time": end_time,
        }

        entries = await self.storage.query(filters, limit=100000)

        return self._format_export(entries, format)

    async def export_security_events(
        self,
        start_time: datetime,
        end_time: datetime,
        format: ExportFormat = ExportFormat.JSON,
    ) -> bytes:
        """Export security-related events for incident response."""
        # Get all entries and filter for security events
        filters = {
            "start_time": start_time,
            "end_time": end_time,
        }

        all_entries = await self.storage.query(filters, limit=100000)

        security_events = [
            entry
            for entry in all_entries
            if entry.event_type.value.startswith("security.")
            or entry.event_type.value.startswith("auth.")
            or "security_alert" in entry.compliance_tags
        ]

        return self._format_export(security_events, format)

    async def export_range(
        self,
        start_time: datetime,
        end_time: datetime,
        format: ExportFormat = ExportFormat.JSONL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Export logs for a time range with optional filters."""
        query_filters = filters or {}
        query_filters["start_time"] = start_time
        query_filters["end_time"] = end_time

        entries = await self.storage.query(query_filters, limit=1000000)

        return self._format_export(entries, format)

    def _format_export(
        self,
        entries: List[AuditLogEntry],
        format: ExportFormat,
    ) -> bytes:
        """Format entries according to requested format."""
        if format == ExportFormat.JSON:
            return self._to_json(entries)
        elif format == ExportFormat.CSV:
            return self._to_csv(entries)
        elif format == ExportFormat.JSONL:
            return self._to_jsonl(entries)
        elif format == ExportFormat.PDF:
            return self._to_pdf(entries)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_json(self, entries: List[AuditLogEntry]) -> bytes:
        """Export as JSON array."""
        data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }
        return json.dumps(data, indent=2).encode("utf-8")

    def _to_csv(self, entries: List[AuditLogEntry]) -> bytes:
        """Export as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "id",
            "timestamp",
            "event_type",
            "outcome",
            "actor_id",
            "actor_type",
            "actor_email",
            "resource_type",
            "resource_id",
            "action",
            "tenant_id",
            "session_id",
            "request_id",
            "ip_address",
            "user_agent",
            "fields_accessed",
            "is_sensitive",
            "compliance_tags",
        ])

        # Rows
        for entry in entries:
            writer.writerow([
                str(entry.id),
                entry.timestamp.isoformat(),
                entry.event_type.value,
                entry.outcome.value,
                entry.actor_id or "",
                entry.actor_type.value,
                entry.actor_email or "",
                entry.resource_type or "",
                entry.resource_id or "",
                entry.action,
                entry.tenant_id or "",
                entry.session_id or "",
                entry.request_id or "",
                entry.ip_address or "",
                entry.user_agent or "",
                ",".join(entry.fields_accessed) if entry.fields_accessed else "",
                str(entry.is_sensitive),
                ",".join(entry.compliance_tags),
            ])

        return output.getvalue().encode("utf-8")

    def _to_jsonl(self, entries: List[AuditLogEntry]) -> bytes:
        """Export as JSON Lines (one JSON object per line)."""
        lines = [json.dumps(entry.to_dict()) for entry in entries]
        return "\n".join(lines).encode("utf-8")

    def _to_pdf(self, entries: List[AuditLogEntry]) -> bytes:
        """
        Export as PDF report.

        This would require a PDF library like reportlab.
        For now, raise not implemented.
        """
        raise NotImplementedError(
            "PDF export requires reportlab library. "
            "Use JSON/CSV export and convert externally."
        )

    async def create_legal_hold_export(
        self,
        case_id: str,
        user_ids: List[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, bytes]:
        """
        Create comprehensive export for legal hold/discovery.

        Returns dict of filename -> content for each user.
        """
        exports = {}

        for user_id in user_ids:
            content = await self.export_user_data(
                user_id=user_id,
                format=ExportFormat.JSON,
                start_time=start_time,
                end_time=end_time,
            )

            filename = f"legal_hold_{case_id}_{user_id}_{datetime.utcnow().isoformat()}.json"
            exports[filename] = content

        # Add summary
        summary = {
            "case_id": case_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "users": user_ids,
            "total_files": len(exports),
        }

        exports["_summary.json"] = json.dumps(summary, indent=2).encode("utf-8")

        return exports

    async def create_gdpr_export(
        self,
        user_id: str,
        include_all_data: bool = True,
    ) -> bytes:
        """
        Create GDPR Article 15 compliant export.

        Must include:
        - All personal data processed
        - Purposes of processing
        - Categories of data
        - Recipients
        - Retention periods
        """
        # Get all audit logs for user
        entries = await self.storage.query(
            {"actor_id": user_id},
            limit=100000,
        )

        # Analyze data
        gdpr_export = {
            "export_type": "GDPR Article 15 - Right of Access",
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_subject_id": user_id,
            "personal_data": {
                "audit_logs": [entry.to_dict() for entry in entries],
                "total_events": len(entries),
            },
            "processing_purposes": self._extract_purposes(entries),
            "data_categories": self._extract_categories(entries),
            "recipients": self._extract_recipients(entries),
            "retention_periods": {
                "audit_logs": "7 years (SOC2 compliance)",
                "memories": "2 years (default)",
                "sessions": "90 days",
            },
            "rights_information": {
                "right_to_rectification": "You can request corrections via API or support",
                "right_to_erasure": "You can request deletion via API or support",
                "right_to_restriction": "You can request processing restrictions",
                "right_to_portability": "This export fulfills your portability right",
                "right_to_object": "You can object to processing via support",
            },
        }

        return json.dumps(gdpr_export, indent=2).encode("utf-8")

    def _extract_purposes(self, entries: List[AuditLogEntry]) -> List[str]:
        """Extract processing purposes from entries."""
        purposes = set()

        for entry in entries:
            event = entry.event_type.value
            if event.startswith("auth."):
                purposes.add("Authentication and access control")
            elif event.startswith("data."):
                purposes.add("Data processing and storage")
            elif event.startswith("memory."):
                purposes.add("AI memory management")
            elif event.startswith("session."):
                purposes.add("Session management")

        return sorted(list(purposes))

    def _extract_categories(self, entries: List[AuditLogEntry]) -> List[str]:
        """Extract data categories from entries."""
        categories = set()

        for entry in entries:
            if entry.actor_email:
                categories.add("Email address")
            if entry.ip_address:
                categories.add("IP address")
            if entry.user_agent:
                categories.add("Browser information")
            if entry.resource_type == "memory":
                categories.add("AI conversation memory")
            if entry.resource_type == "session":
                categories.add("Session data")

        return sorted(list(categories))

    def _extract_recipients(self, entries: List[AuditLogEntry]) -> List[str]:
        """Extract data recipients from entries."""
        return [
            "CONTINUUM AI Memory System (Data Controller)",
            "Cloud infrastructure providers (Data Processors)",
            "No third-party sharing without consent",
        ]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
