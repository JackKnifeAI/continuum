# CONTINUUM Compliance - Quick Reference

## Imports

```python
# Audit logging
from continuum.compliance.audit import (
    AuditLogger,
    AuditEventType,
    Actor,
    ActorType,
    Resource,
    Action,
    Outcome,
    AccessType,
)

# GDPR
from continuum.compliance.gdpr import (
    DataSubjectRights,
    ConsentManager,
    ConsentType,
    LegalBasis,
    DataRetentionManager,
)

# Encryption
from continuum.compliance.encryption import (
    FieldLevelEncryption,
    EncryptedValue,
    TLSConfig,
)

# Access Control
from continuum.compliance.access_control import (
    RBACManager,
    AccessEnforcer,
    PolicyEngine,
)

# Reports & Monitoring
from continuum.compliance.reports import ComplianceReportGenerator
from continuum.compliance.monitoring import (
    AnomalyDetector,
    ComplianceAlertManager,
)
```

## Common Patterns

### 1. Log User Action

```python
await audit_logger.log(
    event_type=AuditEventType.MEMORY_CREATE,
    actor=Actor(id=user_id, type=ActorType.USER),
    resource=Resource(type="memory", id=memory_id),
    action=Action(type="create"),
    outcome=Outcome.SUCCESS,
    ip_address=request.client.host,
)
```

### 2. Check Permission

```python
can_read = await rbac.check_permission(
    user_id=user_id,
    permission="read",
    resource_type="memory",
    resource_id=memory_id,
)
```

### 3. Protect Endpoint

```python
@enforcer.enforce_permission("read", "memory")
async def get_memory(memory_id: str, user_id: str):
    return await fetch_memory(memory_id)
```

### 4. Encrypt Field

```python
encrypted = await fle.encrypt_field(
    field_path="memory.content",
    value=content,
    user_id=user_id,
)
```

### 5. Handle GDPR Request

```python
# Access request
response = await dsr.handle_access_request(user_id)

# Erasure request
result = await dsr.handle_erasure_request(user_id, verification)

# Export request
export = await dsr.handle_portability_request(user_id)
```

### 6. Record Consent

```python
await consent.record_consent(
    user_id=user_id,
    consent_type=ConsentType.DATA_PROCESSING,
    granted=True,
    purpose="AI memory processing",
)
```

### 7. Detect Anomalies

```python
anomalies = await detector.detect_all(user_id=user_id)
for anomaly in anomalies:
    await alert_manager.alert_anomaly(anomaly)
```

## Event Types Cheat Sheet

| Category | Events |
|----------|--------|
| **Auth** | LOGIN_SUCCESS, LOGIN_FAILURE, LOGOUT, PASSWORD_CHANGE, MFA_ENABLED, TOKEN_ISSUED |
| **Data** | READ, CREATE, UPDATE, DELETE, EXPORT, BULK_READ, BULK_UPDATE, BULK_DELETE |
| **Memory** | CREATE, READ, UPDATE, DELETE, SEARCH, CONSOLIDATE, EXPORT, SHARE, UNSHARE |
| **GDPR** | ACCESS_REQUEST, ERASURE_REQUEST, EXPORTED, ERASED, CONSENT_GIVEN, CONSENT_WITHDRAWN |
| **Security** | ACCESS_DENIED, ANOMALY_DETECTED, RATE_LIMIT_EXCEEDED, INTRUSION_ATTEMPT |

## Roles & Permissions

| Role | Permissions |
|------|-------------|
| **admin** | All (*) |
| **operator** | System read/write, no user data |
| **analyst** | Read logs and reports |
| **user** | Read/write own data |
| **viewer** | Read own data |

## Response Times

| Action | Target | Deadline |
|--------|--------|----------|
| GDPR Access Request | 30 days | Legal requirement |
| GDPR Erasure Request | 30 days | Legal requirement |
| Anomaly Detection | Real-time | Best practice |
| Audit Log Write | <5s | Performance |
| Permission Check | <100ms | Performance |

## Storage Backends

| Backend | Use Case | Retention |
|---------|----------|-----------|
| **PostgreSQL** | Primary audit storage | 7 years |
| **Elasticsearch** | Fast search, analytics | 90 days |
| **S3** | Long-term archival | Indefinite |

## Encryption Keys

| Type | Algorithm | Usage |
|------|-----------|-------|
| **Field-level** | AES-256-GCM | Sensitive data |
| **At rest** | AES-256 | Database/files |
| **In transit** | TLS 1.3 | API/network |

## Database Tables

| Table | Purpose | Retention |
|-------|---------|-----------|
| `audit_logs` | Immutable audit trail | 7 years |
| `consents` | GDPR consent records | Indefinite |
| `role_assignments` | RBAC assignments | Until revoked |
| `compliance_alerts` | Alerts & incidents | 1 year |
| `scheduled_deletions` | Retention queue | Until executed |

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Success |
| 403 | Forbidden | Access denied |
| 429 | Too Many Requests | Rate limit |
| 500 | Internal Error | System error |

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...
FIELD_ENCRYPTION_KEY=<base64-key>

# Optional
ELASTICSEARCH_URL=http://localhost:9200
S3_BUCKET=continuum-audit-logs
AUDIT_LOG_BATCH_SIZE=100
GDPR_REQUEST_DEADLINE_DAYS=30
```

## Common SQL Queries

```sql
-- Recent audit logs
SELECT * FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC LIMIT 100;

-- User activity
SELECT event_type, COUNT(*)
FROM audit_logs
WHERE actor_id = 'user123'
GROUP BY event_type;

-- Failed logins
SELECT actor_id, COUNT(*)
FROM audit_logs
WHERE event_type = 'auth.login.failure'
AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY actor_id
HAVING COUNT(*) > 5;

-- Active alerts
SELECT * FROM compliance_alerts
WHERE resolved = false
ORDER BY created_at DESC;
```

## Testing Commands

```bash
# Run tests
pytest tests/compliance/

# Run with coverage
pytest --cov=continuum.compliance tests/compliance/

# Run specific test
pytest tests/compliance/test_audit.py::test_audit_logging

# Run integration tests
pytest tests/compliance/integration/
```

## Monitoring Queries

```python
# Prometheus metrics
continuum_audit_logs_total{event_type="memory.create", outcome="success"}
continuum_gdpr_requests_total{request_type="erasure"}
continuum_anomalies_total{anomaly_type="bulk_operation", severity="critical"}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Audit logs not saving | Check storage backend, batch settings |
| GDPR request timeout | Check data volume, increase timeout |
| Permission denied | Verify role assignments, check audit logs |
| Encryption error | Verify encryption key, check key rotation |
| Alert not triggered | Check severity threshold, notification config |

## Performance Tips

1. **Enable batching** for audit logs (default: 100 events/5s)
2. **Use Elasticsearch** for frequent searches
3. **Partition tables** by month for large datasets
4. **Cache permissions** for frequently accessed resources
5. **Async operations** for non-blocking audit logging
6. **Index optimization** for common query patterns
7. **Compress old logs** to S3 Glacier after 1 year

## Security Checklist

- [ ] Enable TLS 1.3 for all connections
- [ ] Rotate encryption keys quarterly
- [ ] Review audit logs weekly
- [ ] Monitor anomaly alerts daily
- [ ] Test GDPR workflows monthly
- [ ] Verify chain integrity weekly
- [ ] Backup databases daily
- [ ] Update dependencies monthly
- [ ] Review access control quarterly
- [ ] Train staff on compliance annually

## Links

- [README.md](./README.md) - Full documentation
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Integration guide
- [SUMMARY.md](./SUMMARY.md) - Build summary
