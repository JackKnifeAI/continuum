# CONTINUUM Compliance System - Implementation Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Database Setup](#database-setup)
3. [Integration Examples](#integration-examples)
4. [API Endpoints](#api-endpoints)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)

## System Overview

The CONTINUUM compliance system provides enterprise-grade compliance for AI memory systems. It implements SOC2, GDPR, and HIPAA requirements with complete audit trails.

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTINUUM Compliance                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Audit Logger │  │     GDPR     │  │     RBAC     │     │
│  │              │  │ Data Subject │  │ Access Ctrl  │     │
│  │ • Events     │  │ • Rights     │  │ • Roles      │     │
│  │ • Storage    │  │ • Consent    │  │ • Policies   │     │
│  │ • Search     │  │ • Retention  │  │ • Enforcement│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Encryption  │  │   Reports    │  │  Monitoring  │     │
│  │              │  │              │  │              │     │
│  │ • Field-level│  │ • SOC2       │  │ • Anomalies  │     │
│  │ • At rest    │  │ • GDPR       │  │ • Alerts     │     │
│  │ • In transit │  │ • Access     │  │ • Dashboards │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │  Storage Backends          │
              ├─────────────────────────────┤
              │ • PostgreSQL (primary)     │
              │ • Elasticsearch (search)   │
              │ • S3 (long-term)          │
              └─────────────────────────────┘
```

## Database Setup

### 1. PostgreSQL Schema

```sql
-- Run migrations in order:

-- 1. Audit logs
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

-- Create monthly partitions
CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Indexes
CREATE INDEX idx_audit_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX idx_audit_actor ON audit_logs (actor_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id, timestamp DESC);
CREATE INDEX idx_audit_tenant ON audit_logs (tenant_id, timestamp DESC);

-- 2. Consents
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    granted BOOLEAN NOT NULL,
    legal_basis TEXT NOT NULL,
    purpose TEXT NOT NULL,
    method TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    consent_text TEXT,
    consent_version TEXT,
    withdrawn_at TIMESTAMPTZ,
    withdrawal_reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_consents_user ON consents (user_id);

-- 3. Role assignments
CREATE TABLE IF NOT EXISTS role_assignments (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    tenant_id TEXT,
    assigned_by TEXT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_role_assignments_user ON role_assignments (user_id);

-- 4. Compliance alerts
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

-- 5. Scheduled deletions
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
```

### 2. Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/continuum
DATABASE_POOL_SIZE=20

# Encryption
FIELD_ENCRYPTION_KEY=<base64-encoded-key>
MASTER_ENCRYPTION_KEY=<base64-encoded-key>

# Audit
AUDIT_LOG_BATCH_SIZE=100
AUDIT_LOG_BATCH_TIMEOUT=5.0
AUDIT_LOG_ENABLE_CHAINING=true

# GDPR
GDPR_REQUEST_DEADLINE_DAYS=30
GDPR_SOFT_DELETE_GRACE_PERIOD_DAYS=30

# Elasticsearch (optional)
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=audit-logs

# S3 (optional)
S3_BUCKET=continuum-audit-logs
S3_REGION=us-east-1
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException
from continuum.compliance.audit import AuditLogger
from continuum.compliance.access_control import RBACManager, AccessEnforcer
from continuum.compliance.gdpr import DataSubjectRights, ConsentManager

app = FastAPI()

# Initialize compliance components
audit_logger = AuditLogger(storage=audit_storage)
rbac = RBACManager(db_pool, audit_logger)
enforcer = AccessEnforcer(rbac)
dsr = DataSubjectRights(db_pool, audit_logger, storage_manager)
consent = ConsentManager(db_pool, audit_logger)

# Middleware for audit logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    # Extract user from JWT/session
    user_id = request.state.user_id if hasattr(request.state, 'user_id') else None

    # Log request
    await audit_logger.log_data_access(
        user_id=user_id or "anonymous",
        resource_type="api",
        resource_id=request.url.path,
        access_type="read" if request.method == "GET" else "write",
        fields_accessed=[],
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    response = await call_next(request)
    return response

# Protected endpoint with RBAC
@app.get("/api/v1/memories/{memory_id}")
@enforcer.enforce_permission("read", "memory")
async def get_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user),
):
    memory = await fetch_memory(memory_id)
    return memory

# GDPR endpoints
@app.post("/api/v1/gdpr/access-request")
async def gdpr_access_request(
    user_id: str = Depends(get_current_user),
):
    response = await dsr.handle_access_request(user_id)
    return {
        "request_id": str(response.request_id),
        "data": response.data,
    }

@app.post("/api/v1/gdpr/erasure-request")
async def gdpr_erasure_request(
    verification: VerificationToken,
    user_id: str = Depends(get_current_user),
):
    result = await dsr.handle_erasure_request(user_id, verification)
    return {
        "request_id": str(result.request_id),
        "deleted_items": result.deleted_items,
        "total_deleted": result.total_deleted,
    }

# Consent management
@app.post("/api/v1/consent")
async def record_consent(
    consent_type: ConsentType,
    granted: bool,
    purpose: str,
    user_id: str = Depends(get_current_user),
    request: Request,
):
    record = await consent.record_consent(
        user_id=user_id,
        consent_type=consent_type,
        granted=granted,
        purpose=purpose,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    return {"consent_id": str(record.id)}

# Admin endpoints
@app.get("/api/v1/admin/audit-logs")
@enforcer.enforce_role("admin")
async def get_audit_logs(
    start_date: datetime,
    end_date: datetime,
    user_id: str = Depends(get_current_user),
):
    filters = {
        "start_time": start_date,
        "end_time": end_date,
    }
    logs = await audit_storage.query(filters, limit=1000)
    return {"logs": [log.to_dict() for log in logs]}
```

### Encryption Integration

```python
from continuum.compliance.encryption import FieldLevelEncryption

# Initialize
encryption_key = FieldLevelEncryption.generate_key()
fle = FieldLevelEncryption(encryption_key, audit_logger)

# In your data model
class Memory(BaseModel):
    id: str
    user_id: str
    content: str  # Will be encrypted
    metadata: dict

    async def save(self):
        # Encrypt sensitive fields before saving
        encrypted_content = await fle.encrypt_field(
            field_path="memory.content",
            value=self.content,
            user_id=self.user_id,
        )

        # Save to database
        await db.execute(
            "INSERT INTO memories (id, user_id, content_encrypted, metadata) "
            "VALUES ($1, $2, $3, $4)",
            self.id,
            self.user_id,
            encrypted_content.to_dict(),
            self.metadata,
        )

    @classmethod
    async def load(cls, memory_id: str, accessor_id: str):
        # Load from database
        row = await db.fetchrow(
            "SELECT * FROM memories WHERE id = $1",
            memory_id,
        )

        # Decrypt content
        encrypted = EncryptedValue.from_dict(row["content_encrypted"])
        content = await fle.decrypt_field(
            encrypted=encrypted,
            accessor_id=accessor_id,
            field_path="memory.content",
        )

        return cls(
            id=row["id"],
            user_id=row["user_id"],
            content=content,
            metadata=row["metadata"],
        )
```

### Monitoring Integration

```python
from continuum.compliance.monitoring import AnomalyDetector, ComplianceAlertManager

# Background task for anomaly detection
async def detect_anomalies_task():
    detector = AnomalyDetector(db_pool, audit_search)
    alert_manager = ComplianceAlertManager(db_pool, audit_logger)

    while True:
        # Run detection every 15 minutes
        await asyncio.sleep(900)

        try:
            # Detect system-wide anomalies
            anomalies = await detector.detect_all()

            # Create alerts
            for anomaly in anomalies:
                await alert_manager.alert_anomaly(anomaly)

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")

# Start background task
asyncio.create_task(detect_anomalies_task())
```

## API Endpoints

### Audit Endpoints (Admin only)

```
GET    /api/v1/audit/logs                  # Query audit logs
GET    /api/v1/audit/logs/{id}             # Get specific log
GET    /api/v1/audit/export                # Export audit logs
GET    /api/v1/audit/user/{user_id}        # User activity
POST   /api/v1/audit/verify-integrity      # Verify chain integrity
```

### GDPR Endpoints

```
POST   /api/v1/gdpr/access-request         # Request data access
POST   /api/v1/gdpr/export-request         # Request data export
POST   /api/v1/gdpr/deletion-request       # Request data deletion
POST   /api/v1/gdpr/rectification-request  # Request data correction
GET    /api/v1/gdpr/consents               # Get consent status
POST   /api/v1/gdpr/consent                # Record/update consent
DELETE /api/v1/gdpr/consent/{type}         # Withdraw consent
```

### Compliance Reports (Admin only)

```
GET    /api/v1/compliance/reports          # List reports
POST   /api/v1/compliance/reports          # Generate report
GET    /api/v1/compliance/reports/{id}     # Download report
GET    /api/v1/compliance/soc2             # SOC2 report
GET    /api/v1/compliance/gdpr             # GDPR report
GET    /api/v1/compliance/access/{user_id} # User access report
```

### Access Control (Admin only)

```
GET    /api/v1/rbac/roles                  # List roles
POST   /api/v1/rbac/assign                 # Assign role
DELETE /api/v1/rbac/revoke/{assignment_id} # Revoke role
GET    /api/v1/rbac/user/{user_id}/roles   # Get user roles
GET    /api/v1/rbac/user/{user_id}/perms   # Get user permissions
```

## Testing

### Unit Tests

```python
import pytest
from continuum.compliance.audit import AuditLogger, AuditEventType

@pytest.mark.asyncio
async def test_audit_logging():
    # Setup
    storage = MockAuditStorage()
    logger = AuditLogger(storage)

    # Log event
    entry = await logger.log(
        event_type=AuditEventType.MEMORY_CREATE,
        actor=Actor(id="user123", type=ActorType.USER),
        resource=Resource(type="memory", id="mem456"),
        action=Action(type="create"),
        outcome=Outcome.SUCCESS,
    )

    # Verify
    assert entry.event_type == AuditEventType.MEMORY_CREATE
    assert entry.actor_id == "user123"
    assert entry.hash is not None

@pytest.mark.asyncio
async def test_gdpr_erasure():
    # Setup
    dsr = DataSubjectRights(db_pool, audit_logger, storage)

    # Create test data
    await create_test_user("user123")
    await create_test_memories("user123", count=10)

    # Erase
    verification = VerificationToken(
        token="test_token",
        user_id="user123",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        purpose="erasure",
    )

    result = await dsr.handle_erasure_request("user123", verification)

    # Verify
    assert result.total_deleted == 10
    assert "memories" in result.deleted_items

    # Check data is gone
    memories = await fetch_user_memories("user123")
    assert len(memories) == 0
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_compliance():
    # 1. Create user and data
    user_id = "test_user_123"
    await create_user(user_id)

    # 2. Record consent
    consent_record = await consent.record_consent(
        user_id=user_id,
        consent_type=ConsentType.DATA_PROCESSING,
        granted=True,
        purpose="Testing",
    )

    # 3. Create memory (triggers audit log)
    memory = await create_memory(user_id, "Test content")

    # 4. Access memory (triggers audit log)
    retrieved = await get_memory(memory.id, user_id)

    # 5. Verify audit trail
    activity = await audit_search.get_user_activity(user_id)
    assert len(activity) >= 2  # Create + read

    # 6. Request data access (GDPR)
    access_response = await dsr.handle_access_request(user_id)
    assert "memories" in access_response.data

    # 7. Request erasure (GDPR)
    erasure_result = await dsr.handle_erasure_request(user_id, verification)
    assert erasure_result.total_deleted > 0
```

## Production Deployment

### 1. Infrastructure

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: continuum
      POSTGRES_USER: continuum
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./compliance/sql:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://continuum:${DB_PASSWORD}@postgres:5432/continuum
      ELASTICSEARCH_URL: http://elasticsearch:9200
      FIELD_ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    depends_on:
      - postgres
      - elasticsearch
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  es_data:
```

### 2. Monitoring

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

audit_log_counter = Counter(
    'continuum_audit_logs_total',
    'Total audit logs',
    ['event_type', 'outcome']
)

gdpr_request_counter = Counter(
    'continuum_gdpr_requests_total',
    'Total GDPR requests',
    ['request_type']
)

anomaly_counter = Counter(
    'continuum_anomalies_total',
    'Total anomalies detected',
    ['anomaly_type', 'severity']
)
```

### 3. Backup Strategy

```bash
# Daily PostgreSQL backup
pg_dump -Fc continuum > /backups/continuum-$(date +%Y%m%d).dump

# Weekly Elasticsearch snapshot
curl -X PUT "localhost:9200/_snapshot/backup/weekly_$(date +%Y%m%d)"

# Monthly S3 backup archive
aws s3 sync /var/lib/postgresql/data s3://continuum-backups/monthly/
```

### 4. Disaster Recovery

```python
# Verify audit log integrity
async def verify_all_logs():
    result = await audit_logger.verify_chain_integrity()
    if not result["valid"]:
        # Alert on-call
        await alert_manager.create_alert(
            type=AlertType.AUDIT_LOG_INTEGRITY,
            severity=AlertSeverity.CRITICAL,
            title="Audit log integrity failure",
            description=f"Chain broken at entry {result['first_invalid']}",
        )

# Restore from backup
async def restore_from_backup(backup_file: str):
    # Restore database
    subprocess.run(["pg_restore", "-d", "continuum", backup_file])

    # Verify integrity
    result = await verify_all_logs()
    return result["valid"]
```

## Performance Tuning

### PostgreSQL

```sql
-- Partition maintenance
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    next_month DATE;
    partition_name TEXT;
BEGIN
    next_month := date_trunc('month', CURRENT_DATE + interval '1 month');
    partition_name := 'audit_logs_' || to_char(next_month, 'YYYY_MM');

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        next_month,
        next_month + interval '1 month'
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT create_monthly_partition()');
```

### Elasticsearch

```json
{
  "index.lifecycle.name": "audit-logs-policy",
  "index.lifecycle.rollover_alias": "audit-logs",
  "index.refresh_interval": "30s",
  "index.number_of_shards": 3,
  "index.number_of_replicas": 1
}
```

## Conclusion

This implementation guide provides complete examples for integrating CONTINUUM's compliance system. Follow these patterns to ensure SOC2, GDPR, and HIPAA compliance for your AI memory application.

For questions or issues, consult the main [README.md](./README.md) or open a GitHub issue.
