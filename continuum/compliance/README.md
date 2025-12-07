# CONTINUUM Compliance System

Enterprise-grade compliance and audit system for SOC2, GDPR, and HIPAA.

## Overview

The CONTINUUM compliance system provides comprehensive audit logging, data protection, and regulatory compliance for AI memory systems handling sensitive data.

### Key Features

- **Audit Logging**: Immutable, cryptographically-chained audit logs with 7-year retention
- **GDPR Compliance**: Full implementation of data subject rights (Articles 15-22)
- **Access Control**: Role-based access control (RBAC) with fine-grained permissions
- **Encryption**: Field-level encryption, encryption at rest, and TLS in transit
- **Compliance Reports**: Automated SOC2 and GDPR reports
- **Anomaly Detection**: Real-time detection of unusual access patterns
- **Alert Management**: Compliance alert system with severity-based routing

## Supported Frameworks

### SOC2 Type II
- **CC6.1**: Logical access controls
- **CC6.2**: Authentication and authorization
- **CC6.3**: Access management
- **CC6.7**: Data classification and encryption
- **CC7**: System operations and availability
- **CC8**: Change management

### GDPR
- **Article 15**: Right of access
- **Article 16**: Right to rectification
- **Article 17**: Right to erasure (right to be forgotten)
- **Article 18**: Right to restriction of processing
- **Article 20**: Right to data portability
- **Article 30**: Records of processing activities

### HIPAA (Considerations)
- **164.312(a)(1)**: Access control
- **164.312(a)(2)(i)**: Unique user identification
- **164.312(b)**: Audit controls
- **164.312(c)(1)**: Integrity controls
- **164.312(e)(1)**: Transmission security

## Architecture

```
compliance/
├── audit/              # Audit logging system
│   ├── logger.py       # Core audit logger
│   ├── events.py       # Event type definitions (85+ event types)
│   ├── storage.py      # Multiple storage backends (PostgreSQL, Elasticsearch, S3)
│   ├── search.py       # Advanced search and analytics
│   └── export.py       # Compliance exports (JSON, CSV, JSONL)
│
├── gdpr/               # GDPR compliance
│   ├── data_subject.py # Data subject rights (Articles 15-22)
│   ├── consent.py      # Consent management (Articles 6-8)
│   ├── retention.py    # Data retention policies
│   └── export.py       # GDPR-specific exports
│
├── encryption/         # Data protection
│   ├── field_level.py  # Field-level encryption (AES-256-GCM)
│   ├── at_rest.py      # Encryption at rest configuration
│   └── in_transit.py   # TLS/SSL configuration
│
├── access_control/     # Access control
│   ├── rbac.py         # Role-based access control
│   ├── policies.py     # Policy-based access control
│   └── enforcement.py  # Decorators and middleware
│
├── reports/            # Compliance reporting
│   └── generator.py    # SOC2, GDPR, and access reports
│
└── monitoring/         # Monitoring and alerting
    ├── anomaly.py      # Anomaly detection
    └── alerts.py       # Alert management
```

## Quick Start

### 1. Initialize Audit Logger

```python
from continuum.compliance.audit import AuditLogger, AuditLogStorage
from continuum.compliance.audit.storage import PostgresAuditStorage

# Initialize storage
storage = PostgresAuditStorage(db_pool)

# Create logger
audit_logger = AuditLogger(
    storage=storage,
    enable_chaining=True,  # Cryptographic chaining
    batch_size=100,
    batch_timeout_seconds=5.0,
)

# Log an event
from continuum.compliance.audit import Actor, Resource, Action, Outcome, ActorType

await audit_logger.log(
    event_type=AuditEventType.MEMORY_CREATE,
    actor=Actor(id="user123", type=ActorType.USER),
    resource=Resource(type="memory", id="mem456"),
    action=Action(type="create"),
    outcome=Outcome.SUCCESS,
    ip_address="192.168.1.1",
)
```

### 2. Implement GDPR Data Subject Rights

```python
from continuum.compliance.gdpr import DataSubjectRights

dsr = DataSubjectRights(db_pool, audit_logger, storage_manager)

# Handle access request (Article 15)
response = await dsr.handle_access_request(
    user_id="user123",
    verification=verification_token,
)

# Handle erasure request (Article 17)
result = await dsr.handle_erasure_request(
    user_id="user123",
    verification=verification_token,
)

print(f"Deleted {result.total_deleted} items")
print(f"Retained items: {result.retained_items}")
```

### 3. Manage Consent

```python
from continuum.compliance.gdpr import ConsentManager, ConsentType, LegalBasis

consent = ConsentManager(db_pool, audit_logger)

# Record consent
await consent.record_consent(
    user_id="user123",
    consent_type=ConsentType.DATA_PROCESSING,
    granted=True,
    purpose="AI memory processing",
    legal_basis=LegalBasis.CONSENT,
    ip_address="192.168.1.1",
)

# Check consent
has_consent = await consent.check_consent(
    user_id="user123",
    purpose="AI memory processing",
)

# Withdraw consent
await consent.withdraw_consent(
    user_id="user123",
    consent_type=ConsentType.DATA_PROCESSING,
    reason="User request",
)
```

### 4. Enforce Access Control

```python
from continuum.compliance.access_control import RBACManager, AccessEnforcer

rbac = RBACManager(db_pool, audit_logger)
enforcer = AccessEnforcer(rbac)

# Check permission
can_read = await rbac.check_permission(
    user_id="user123",
    permission="read",
    resource_type="memory",
    resource_id="mem456",
)

# Use decorator
@enforcer.enforce_permission("read", "memory")
async def get_memory(memory_id: str, user_id: str):
    # Function only executes if user has permission
    return await fetch_memory(memory_id)
```

### 5. Field-Level Encryption

```python
from continuum.compliance.encryption import FieldLevelEncryption

# Initialize
encryption_key = FieldLevelEncryption.generate_key()
fle = FieldLevelEncryption(encryption_key, audit_logger)

# Encrypt a field
encrypted = await fle.encrypt_field(
    field_path="memory.content",
    value="Sensitive conversation data",
    user_id="user123",
)

# Decrypt a field
decrypted = await fle.decrypt_field(
    encrypted=encrypted,
    accessor_id="user123",
    field_path="memory.content",
)
```

### 6. Generate Compliance Reports

```python
from continuum.compliance.reports import ComplianceReportGenerator
from datetime import datetime, timedelta

generator = ComplianceReportGenerator(db_pool, audit_search)

# SOC2 report
soc2_report = await generator.generate_soc2_report(
    start_date=datetime(2025, 10, 1),
    end_date=datetime(2025, 12, 31),
)

# GDPR report
gdpr_report = await generator.generate_gdpr_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
)
```

### 7. Detect Anomalies

```python
from continuum.compliance.monitoring import AnomalyDetector

detector = AnomalyDetector(db_pool, audit_search)

# Detect all anomalies for a user
anomalies = await detector.detect_all(user_id="user123")

# Detect bulk operations (potential data exfiltration)
bulk_ops = await detector.detect_bulk_operations(hours=24, threshold=500)

# Create alerts from anomalies
from continuum.compliance.monitoring import ComplianceAlertManager

alert_manager = ComplianceAlertManager(db_pool, audit_logger)

for anomaly in anomalies:
    await alert_manager.alert_anomaly(anomaly)
```

## Audit Event Types

### Authentication (13 events)
- `AUTH_LOGIN_SUCCESS`
- `AUTH_LOGIN_FAILURE`
- `AUTH_LOGOUT`
- `AUTH_PASSWORD_CHANGE`
- `AUTH_MFA_ENABLED`
- `AUTH_TOKEN_ISSUED`
- And more...

### Data Access (10 events)
- `DATA_READ`
- `DATA_CREATE`
- `DATA_UPDATE`
- `DATA_DELETE`
- `DATA_EXPORT`
- `DATA_BULK_READ`
- And more...

### Memory Operations (9 events)
- `MEMORY_CREATE`
- `MEMORY_READ`
- `MEMORY_UPDATE`
- `MEMORY_DELETE`
- `MEMORY_SEARCH`
- `MEMORY_CONSOLIDATE`
- `MEMORY_EXPORT`
- `MEMORY_SHARE`
- `MEMORY_UNSHARE`

### GDPR (11 events)
- `GDPR_DATA_ACCESS_REQUEST`
- `GDPR_DATA_ERASURE_REQUEST`
- `GDPR_DATA_EXPORTED`
- `GDPR_DATA_ERASED`
- `GDPR_CONSENT_GIVEN`
- `GDPR_CONSENT_WITHDRAWN`
- And more...

### Security (6 events)
- `SECURITY_ACCESS_DENIED`
- `SECURITY_ANOMALY_DETECTED`
- `SECURITY_RATE_LIMIT_EXCEEDED`
- `SECURITY_INTRUSION_ATTEMPT`
- `SECURITY_POLICY_VIOLATION`
- `SECURITY_ENCRYPTION_KEY_ROTATED`

**Total: 85+ audit event types**

## Storage Backends

### PostgreSQL
- Immutable append-only storage
- Monthly partitioning for performance
- 7-year retention with automatic archival
- Full-text search capabilities

### Elasticsearch
- Fast full-text search
- Real-time analytics and dashboards
- Index lifecycle management
- Warm/cold tier support

### S3
- Cost-effective long-term storage
- Object Lock for immutability
- Glacier for cold storage
- Cross-region replication

## Data Retention Policies

| Data Type | Retention Period | Legal Basis |
|-----------|-----------------|-------------|
| Memories | 2 years | Performance of contract (Art. 6(1)(b)) |
| Sessions | 90 days | Legitimate interests (Art. 6(1)(f)) |
| Audit Logs | 7 years | Legal obligation (SOC2) |
| Deleted Data | 30 days | Legitimate interests (recovery) |
| Backups | 90 days | Legitimate interests |

## Security Features

### Encryption
- **At Rest**: AES-256 encryption for all data
- **In Transit**: TLS 1.3 with modern cipher suites
- **Field-Level**: Individual field encryption for sensitive data
- **Key Rotation**: Automatic encryption key rotation

### Access Control
- **RBAC**: 5 system roles (admin, operator, analyst, user, viewer)
- **Fine-grained permissions**: Resource and action-level control
- **Policy-based**: AWS IAM-style policy engine
- **Audit trail**: All access decisions logged

### Audit Trail
- **Cryptographic chaining**: Tamper-evident blockchain-like structure
- **SHA-256 hashing**: Integrity verification
- **Immutable storage**: Prevents modification or deletion
- **7-year retention**: SOC2 compliance

## Compliance Checklists

### GDPR Compliance

- [x] Article 15: Right of access
- [x] Article 16: Right to rectification
- [x] Article 17: Right to erasure
- [x] Article 18: Right to restriction
- [x] Article 20: Right to data portability
- [x] Article 30: Records of processing activities
- [x] Article 32: Security of processing
- [x] Consent management
- [x] Data retention policies
- [x] Breach detection and notification

### SOC2 Compliance

- [x] CC6.1: Logical access controls
- [x] CC6.2: Authentication mechanisms
- [x] CC6.3: Access authorization
- [x] CC6.7: Data encryption
- [x] CC7.1: System operations monitoring
- [x] CC8.1: Change management
- [x] Audit logging (7-year retention)
- [x] Access control enforcement
- [x] Incident response procedures

## Performance Considerations

### Audit Logging
- **Batching**: Configurable batch size (default: 100)
- **Async**: Non-blocking audit operations
- **Partitioning**: Monthly table partitions
- **Indexing**: Optimized for common queries

### Encryption
- **Hardware acceleration**: AES-NI support
- **Caching**: Encrypted values cached
- **Streaming**: Large files encrypted in chunks

### Search
- **Elasticsearch**: Sub-second search on millions of logs
- **Caching**: Frequently accessed data cached
- **Pagination**: Efficient large result sets

## Monitoring and Alerts

### Alert Severities
- **INFO**: Informational events
- **LOW**: Minor issues
- **MEDIUM**: Requires attention
- **HIGH**: Requires immediate attention
- **CRITICAL**: Pages on-call team

### Alert Types
- Anomaly detected
- Policy violation
- GDPR request overdue (30 days)
- Retention policy failure
- Access denied spike
- Audit log integrity failure
- Encryption failure

### Notification Channels
- Email (high/critical alerts)
- Slack (all alerts)
- PagerDuty (critical alerts)
- SMS (critical alerts)

## Best Practices

1. **Enable cryptographic chaining** for audit logs
2. **Encrypt sensitive fields** at the application level
3. **Implement RBAC** for all data access
4. **Monitor anomalies** continuously
5. **Respond to GDPR requests** within 30 days
6. **Rotate encryption keys** quarterly
7. **Review audit logs** regularly
8. **Test disaster recovery** procedures
9. **Document all data processing** activities
10. **Train staff** on compliance requirements

## Troubleshooting

### Audit logging failures
- Check storage backend connectivity
- Verify batch size configuration
- Review error logs for exceptions
- Ensure sufficient storage space

### GDPR request delays
- Check request processing queue
- Verify data export functionality
- Review retention policy execution
- Ensure adequate resources

### Access control issues
- Verify role assignments
- Check permission definitions
- Review policy configurations
- Examine audit logs for denials

## Further Reading

- [SOC2.md](./docs/SOC2.md) - SOC2 compliance mapping
- [GDPR.md](./docs/GDPR.md) - GDPR implementation guide
- [HIPAA.md](./docs/HIPAA.md) - HIPAA considerations
- [AUDIT_LOG.md](./docs/AUDIT_LOG.md) - Audit log schema
- [DATA_RETENTION.md](./docs/DATA_RETENTION.md) - Retention policies

## License

Copyright (c) 2025 CONTINUUM. All rights reserved.
