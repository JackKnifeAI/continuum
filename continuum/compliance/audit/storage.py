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

"""Audit log storage backends with immutability guarantees."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .events import AuditLogEntry, AuditEventType, Outcome


class AuditLogStorage(ABC):
    """Abstract base class for audit log storage."""

    @abstractmethod
    async def store(self, entry: AuditLogEntry) -> None:
        """Store a single audit log entry."""
        pass

    @abstractmethod
    async def store_batch(self, entries: List[AuditLogEntry]) -> None:
        """Store multiple entries efficiently."""
        pass

    @abstractmethod
    async def get(self, entry_id: str) -> Optional[AuditLogEntry]:
        """Retrieve a specific entry by ID."""
        pass

    @abstractmethod
    async def get_range(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Get range of entries for chain verification."""
        pass

    @abstractmethod
    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """Query audit logs with filters."""
        pass


class PostgresAuditStorage(AuditLogStorage):
    """
    PostgreSQL storage for audit logs.

    Features:
    - Immutable (INSERT only, no UPDATE/DELETE)
    - Partitioned by month for performance
    - Indexed for common queries
    - 7-year retention for SOC2
    """

    def __init__(self, db_pool):
        self.db = db_pool

    async def store(self, entry: AuditLogEntry) -> None:
        """Store single entry."""
        await self.store_batch([entry])

    async def store_batch(self, entries: List[AuditLogEntry]) -> None:
        """Batch insert for performance."""
        if not entries:
            return

        query = """
            INSERT INTO audit_logs (
                id, timestamp, event_type, outcome,
                actor_id, actor_type, actor_email, actor_name,
                resource_type, resource_id, resource_name,
                action, action_description,
                tenant_id, session_id, request_id, correlation_id,
                ip_address, user_agent, geo_location,
                details, fields_accessed, changes,
                previous_hash, hash,
                retention_period_days, is_sensitive, compliance_tags
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10, $11,
                $12, $13,
                $14, $15, $16, $17,
                $18, $19, $20,
                $21, $22, $23,
                $24, $25,
                $26, $27, $28
            )
        """

        async with self.db.acquire() as conn:
            async with conn.transaction():
                for entry in entries:
                    await conn.execute(
                        query,
                        str(entry.id),
                        entry.timestamp,
                        entry.event_type.value,
                        entry.outcome.value,
                        entry.actor_id,
                        entry.actor_type.value,
                        entry.actor_email,
                        entry.actor_name,
                        entry.resource_type,
                        entry.resource_id,
                        entry.resource_name,
                        entry.action,
                        entry.action_description,
                        entry.tenant_id,
                        entry.session_id,
                        entry.request_id,
                        entry.correlation_id,
                        entry.ip_address,
                        entry.user_agent,
                        entry.geo_location,
                        json.dumps(entry.details),
                        entry.fields_accessed,
                        json.dumps(entry.changes) if entry.changes else None,
                        entry.previous_hash,
                        entry.hash,
                        entry.retention_period_days,
                        entry.is_sensitive,
                        entry.compliance_tags,
                    )

    async def get(self, entry_id: str) -> Optional[AuditLogEntry]:
        """Get entry by ID."""
        query = "SELECT * FROM audit_logs WHERE id = $1"

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, entry_id)
            if row:
                return self._row_to_entry(row)
            return None

    async def get_range(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Get range for chain verification."""
        query = """
            SELECT * FROM audit_logs
            WHERE ($1::uuid IS NULL OR id >= $1::uuid)
              AND ($2::uuid IS NULL OR id <= $2::uuid)
            ORDER BY timestamp ASC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, start_id, end_id)
            return [self._row_to_entry(row) for row in rows]

    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """Query with filters."""
        conditions = []
        params = []
        param_idx = 1

        # Build WHERE clause
        if "event_type" in filters:
            conditions.append(f"event_type = ${param_idx}")
            params.append(filters["event_type"])
            param_idx += 1

        if "actor_id" in filters:
            conditions.append(f"actor_id = ${param_idx}")
            params.append(filters["actor_id"])
            param_idx += 1

        if "resource_type" in filters:
            conditions.append(f"resource_type = ${param_idx}")
            params.append(filters["resource_type"])
            param_idx += 1

        if "resource_id" in filters:
            conditions.append(f"resource_id = ${param_idx}")
            params.append(filters["resource_id"])
            param_idx += 1

        if "tenant_id" in filters:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(filters["tenant_id"])
            param_idx += 1

        if "start_time" in filters:
            conditions.append(f"timestamp >= ${param_idx}")
            params.append(filters["start_time"])
            param_idx += 1

        if "end_time" in filters:
            conditions.append(f"timestamp <= ${param_idx}")
            params.append(filters["end_time"])
            param_idx += 1

        if "outcome" in filters:
            conditions.append(f"outcome = ${param_idx}")
            params.append(filters["outcome"])
            param_idx += 1

        if "compliance_tag" in filters:
            conditions.append(f"${param_idx} = ANY(compliance_tags)")
            params.append(filters["compliance_tag"])
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row) -> AuditLogEntry:
        """Convert database row to AuditLogEntry."""
        return AuditLogEntry.from_dict({
            "id": row["id"],
            "timestamp": row["timestamp"].isoformat(),
            "event_type": row["event_type"],
            "outcome": row["outcome"],
            "actor_id": row["actor_id"],
            "actor_type": row["actor_type"],
            "actor_email": row["actor_email"],
            "actor_name": row["actor_name"],
            "resource_type": row["resource_type"],
            "resource_id": row["resource_id"],
            "resource_name": row["resource_name"],
            "action": row["action"],
            "action_description": row["action_description"],
            "tenant_id": row["tenant_id"],
            "session_id": row["session_id"],
            "request_id": row["request_id"],
            "correlation_id": row["correlation_id"],
            "ip_address": row["ip_address"],
            "user_agent": row["user_agent"],
            "geo_location": row["geo_location"],
            "details": json.loads(row["details"]) if row["details"] else {},
            "fields_accessed": row["fields_accessed"],
            "changes": json.loads(row["changes"]) if row["changes"] else None,
            "previous_hash": row["previous_hash"],
            "hash": row["hash"],
            "retention_period_days": row["retention_period_days"],
            "is_sensitive": row["is_sensitive"],
            "compliance_tags": row["compliance_tags"],
        })


class ElasticsearchAuditStorage(AuditLogStorage):
    """
    Elasticsearch storage for audit logs.

    Features:
    - Fast full-text search
    - Real-time analytics
    - Long-term retention in warm/cold tiers
    - Index lifecycle management
    """

    def __init__(self, es_client, index_prefix: str = "audit-logs"):
        self.es = es_client
        self.index_prefix = index_prefix

    def _get_index_name(self, timestamp: datetime) -> str:
        """Get index name with monthly partitioning."""
        return f"{self.index_prefix}-{timestamp.strftime('%Y-%m')}"

    async def store(self, entry: AuditLogEntry) -> None:
        """Store single entry."""
        index = self._get_index_name(entry.timestamp)
        await self.es.index(
            index=index,
            id=str(entry.id),
            document=entry.to_dict(),
        )

    async def store_batch(self, entries: List[AuditLogEntry]) -> None:
        """Bulk insert."""
        if not entries:
            return

        operations = []
        for entry in entries:
            index = self._get_index_name(entry.timestamp)
            operations.extend([
                {"index": {"_index": index, "_id": str(entry.id)}},
                entry.to_dict(),
            ])

        await self.es.bulk(operations=operations)

    async def get(self, entry_id: str) -> Optional[AuditLogEntry]:
        """Get by ID (search across all indices)."""
        result = await self.es.search(
            index=f"{self.index_prefix}-*",
            query={"term": {"id": entry_id}},
            size=1,
        )

        if result["hits"]["total"]["value"] > 0:
            return AuditLogEntry.from_dict(result["hits"]["hits"][0]["_source"])
        return None

    async def get_range(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Get range (implementation depends on use case)."""
        # This would require additional metadata or timestamp-based range
        raise NotImplementedError("Use query with timestamp range instead")

    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """Query with Elasticsearch DSL."""
        must_clauses = []

        # Build query
        for key, value in filters.items():
            if key in ["start_time", "end_time"]:
                continue  # Handled in range query

            must_clauses.append({"term": {key: value}})

        # Add time range
        if "start_time" in filters or "end_time" in filters:
            range_query = {"range": {"timestamp": {}}}
            if "start_time" in filters:
                range_query["range"]["timestamp"]["gte"] = filters["start_time"]
            if "end_time" in filters:
                range_query["range"]["timestamp"]["lte"] = filters["end_time"]
            must_clauses.append(range_query)

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

        result = await self.es.search(
            index=f"{self.index_prefix}-*",
            query=query,
            size=limit,
            from_=offset,
            sort=[{"timestamp": "desc"}],
        )

        return [
            AuditLogEntry.from_dict(hit["_source"])
            for hit in result["hits"]["hits"]
        ]


class S3AuditStorage(AuditLogStorage):
    """
    S3 storage for long-term audit log retention.

    Features:
    - Immutable object storage
    - Cost-effective for 7+ year retention
    - Glacier for cold storage
    - Object Lock for compliance
    """

    def __init__(self, s3_client, bucket: str, prefix: str = "audit-logs"):
        self.s3 = s3_client
        self.bucket = bucket
        self.prefix = prefix

    def _get_object_key(self, entry: AuditLogEntry) -> str:
        """Generate S3 object key with partitioning."""
        date = entry.timestamp.strftime("%Y/%m/%d")
        return f"{self.prefix}/{date}/{entry.id}.json"

    async def store(self, entry: AuditLogEntry) -> None:
        """Store to S3."""
        key = self._get_object_key(entry)
        await self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(entry.to_dict()),
            ContentType="application/json",
            Metadata={
                "event_type": entry.event_type.value,
                "actor_id": entry.actor_id or "",
                "tenant_id": entry.tenant_id or "",
            },
        )

    async def store_batch(self, entries: List[AuditLogEntry]) -> None:
        """Store batch (individual puts for immutability)."""
        for entry in entries:
            await self.store(entry)

    async def get(self, entry_id: str) -> Optional[AuditLogEntry]:
        """Get by ID (requires additional index)."""
        # S3 doesn't support efficient ID lookup without an index
        raise NotImplementedError("Use query with known timestamp range")

    async def get_range(
        self,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Not efficient in S3."""
        raise NotImplementedError("Use Elasticsearch or PostgreSQL for queries")

    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """Not efficient in S3."""
        raise NotImplementedError("Use Elasticsearch or PostgreSQL for queries")


# SQL Schema for PostgreSQL
POSTGRES_SCHEMA = """
-- Audit logs table (immutable, append-only)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    outcome TEXT NOT NULL,

    -- Actor
    actor_id TEXT,
    actor_type TEXT NOT NULL,
    actor_email TEXT,
    actor_name TEXT,

    -- Resource
    resource_type TEXT,
    resource_id TEXT,
    resource_name TEXT,

    -- Action
    action TEXT NOT NULL,
    action_description TEXT,

    -- Context
    tenant_id TEXT,
    session_id TEXT,
    request_id TEXT,
    correlation_id TEXT,

    -- Network
    ip_address INET,
    user_agent TEXT,
    geo_location TEXT,

    -- Details
    details JSONB,
    fields_accessed TEXT[],
    changes JSONB,

    -- Cryptographic chain
    previous_hash TEXT,
    hash TEXT NOT NULL,

    -- Compliance
    retention_period_days INTEGER NOT NULL DEFAULT 2555,
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    compliance_tags TEXT[]
) PARTITION BY RANGE (timestamp);

-- Indexes for common queries
CREATE INDEX idx_audit_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX idx_audit_actor ON audit_logs (actor_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id, timestamp DESC);
CREATE INDEX idx_audit_tenant ON audit_logs (tenant_id, timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_logs (event_type, timestamp DESC);
CREATE INDEX idx_audit_compliance_tags ON audit_logs USING GIN (compliance_tags);
CREATE INDEX idx_audit_chain ON audit_logs (hash, previous_hash);

-- Create monthly partitions (example for 2025)
CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Prevent updates/deletes (immutability)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER prevent_audit_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
