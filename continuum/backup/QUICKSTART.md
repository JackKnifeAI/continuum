# CONTINUUM Backup System - Quick Start Guide

## Installation

```bash
# Install CONTINUUM with backup support
pip install continuum[backup]

# Or install optional dependencies manually
pip install cryptography zstandard boto3 google-cloud-storage azure-storage-blob
```

## 5-Minute Setup

### 1. Basic Configuration

```python
from pathlib import Path
from continuum.backup import BackupManager, BackupConfig
from continuum.backup.types import StorageConfig, StorageBackend

# Configure local storage
storage = StorageConfig(
    backend=StorageBackend.LOCAL,
    local_path=Path("/var/backups/continuum"),
)

# Create backup configuration
config = BackupConfig(
    primary_storage=storage,
    db_path=Path("continuum_data/memory.db"),
)

# Initialize backup manager
manager = BackupManager(config)
```

### 2. Create Your First Backup

```python
from continuum.backup.types import BackupStrategy

# Create a full backup
result = await manager.create_backup(strategy=BackupStrategy.FULL)

if result.success:
    print(f"Backup created: {result.backup_id}")
else:
    print(f"Backup failed: {result.error}")
```

### 3. List Backups

```python
# List all backups
backups = await manager.list_backups()

for backup in backups:
    print(f"{backup.backup_id} - {backup.created_at} - {backup.strategy.value}")
```

### 4. Restore from Backup

```python
from continuum.backup.types import RestoreTarget

# Define restore target
target = RestoreTarget(
    database_path=Path("restored_memory.db"),
    overwrite=True,
)

# Restore
result = await manager.restore("backup-id", target)

if result.success:
    print(f"Restored {result.records_restored} records")
```

## Common Operations

### Create Different Backup Types

```python
# Full backup (weekly baseline)
await manager.create_backup(strategy=BackupStrategy.FULL)

# Incremental backup (every 5 minutes)
await manager.create_backup(strategy=BackupStrategy.INCREMENTAL)

# Differential backup (daily)
await manager.create_backup(strategy=BackupStrategy.DIFFERENTIAL)
```

### Enable Encryption

```python
from continuum.backup.types import EncryptionConfig

config = BackupConfig(
    primary_storage=storage,
    encryption=EncryptionConfig(
        enabled=True,
        key_id="my-backup-key",
    ),
)
```

### Use Cloud Storage

```python
# AWS S3
s3_storage = StorageConfig(
    backend=StorageBackend.S3,
    s3_bucket="my-continuum-backups",
    s3_region="us-east-1",
)

# Google Cloud Storage
gcs_storage = StorageConfig(
    backend=StorageBackend.GCS,
    gcs_bucket="my-continuum-backups",
    gcs_project="my-project",
)

# Multi-cloud redundancy
multi_storage = StorageConfig(
    backend=StorageBackend.MULTI,
    destinations=[s3_storage, gcs_storage, local_storage],
)
```

### Verify Backup Integrity

```python
# Verify specific backup
verification = await manager.verify_backup("backup-id")

print(f"Checksum: {'✓' if verification.checksum_valid else '✗'}")
print(f"Schema: {'✓' if verification.schema_valid else '✗'}")
print(f"Data: {'✓' if verification.data_sample_valid else '✗'}")
```

### Check System Health

```python
# Get health status
health = await manager.get_health()

print(f"Healthy: {health.healthy}")
print(f"Last backup: {health.last_backup_time}")
print(f"RPO compliant: {health.rpo_compliant}")
print(f"RTO compliant: {health.rto_compliant}")
```

### Apply Retention Policy

```python
from continuum.backup.types import RetentionPolicy

# Configure retention
config = BackupConfig(
    primary_storage=storage,
    retention_policy=RetentionPolicy(
        keep_daily_for_days=7,
        keep_weekly_for_weeks=4,
        keep_monthly_for_months=12,
    ),
)

# Apply retention
result = await manager.apply_retention_policy()
print(f"Deleted {result.backups_deleted} old backups")
print(f"Freed {result.bytes_freed / 1e9:.2f} GB")
```

## Production Checklist

### Before Going Live

- [ ] **Storage configured** - Choose cloud provider or multi-cloud
- [ ] **Encryption enabled** - AES-256-GCM or KMS
- [ ] **Compression enabled** - Zstd recommended
- [ ] **Retention policy set** - GFS or custom
- [ ] **Verification enabled** - Checksum + restore tests
- [ ] **Monitoring configured** - Health checks and alerts
- [ ] **Schedule defined** - Cron jobs or daemon
- [ ] **Test restore performed** - Verify you can actually restore
- [ ] **Runbook reviewed** - Emergency procedures documented
- [ ] **Team trained** - Everyone knows recovery process

### Recommended Production Config

```python
from continuum.backup.types import (
    BackupConfig,
    StorageConfig,
    StorageBackend,
    EncryptionConfig,
    RetentionPolicy,
    CompressionAlgorithm,
)

production_config = BackupConfig(
    # Multi-cloud storage
    primary_storage=StorageConfig(
        backend=StorageBackend.MULTI,
        destinations=[
            StorageConfig(
                backend=StorageBackend.S3,
                s3_bucket="prod-backups",
                s3_region="us-east-1",
            ),
            StorageConfig(
                backend=StorageBackend.GCS,
                gcs_bucket="prod-backups",
                gcs_project="my-project",
            ),
        ],
    ),

    # Security
    encryption=EncryptionConfig(
        enabled=True,
        use_kms=True,
        kms_provider="aws",
        kms_key_id="arn:aws:kms:...",
    ),

    # Performance
    compression_enabled=True,
    compression_algorithm=CompressionAlgorithm.ZSTD,
    compression_level=3,

    # Retention (GFS)
    retention_policy=RetentionPolicy(
        keep_hourly_for_days=1,
        keep_daily_for_days=7,
        keep_weekly_for_weeks=4,
        keep_monthly_for_months=12,
        min_backups_to_keep=3,
        require_verified=True,
    ),

    # Verification
    verify_after_backup=True,
    weekly_restore_test=True,

    # SLA targets
    target_rpo_minutes=5,
    target_rto_minutes=60,

    # Notifications
    notify_on_failure=True,
    notification_channels=["email", "slack"],
)
```

## Scheduled Backups (Cron)

```bash
# /etc/cron.d/continuum-backup

# Full backup - Weekly Sunday 1 AM
0 1 * * 0 continuum-backup full

# Differential - Daily 2 AM
0 2 * * * continuum-backup differential

# Incremental - Every 5 minutes
*/5 * * * * continuum-backup incremental

# Verification - Daily 3 AM
0 3 * * * continuum-backup verify-recent

# Retention - Daily 4 AM
0 4 * * * continuum-backup apply-retention
```

## Disaster Recovery

### Quick Recovery Steps

1. **Identify last good backup**
   ```python
   backups = await manager.list_backups(verified_only=True)
   latest = backups[0]
   ```

2. **Restore to production**
   ```python
   target = RestoreTarget(
       database_path=Path("/var/lib/continuum/memory.db"),
       overwrite=True,
       verify_after_restore=True,
   )
   await manager.restore(latest.backup_id, target)
   ```

3. **Verify and resume**
   ```python
   health = await manager.get_health()
   assert health.healthy
   ```

## Troubleshooting

### Backup Fails

```python
# Check logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Retry with debugging
result = await manager.create_backup(strategy=BackupStrategy.FULL)
print(result.error)
print(result.warnings)
```

### Storage Issues

```python
# Test storage connectivity
storage = manager._get_storage()
exists = await storage.exists("test-backup-id")

# List backups
backup_ids = await storage.list_backups()
```

### Verify Backup

```python
# Full verification with restore test
from continuum.backup.verification import test_restore

result = await test_restore("backup-id", config)
print(f"Restore test: {'PASS' if result.success else 'FAIL'}")
```

## Getting Help

- **Documentation**: See `README.md` for full documentation
- **Runbook**: See `RUNBOOK.md` for emergency procedures
- **Examples**: See `examples/backup_example.py` for code examples
- **Issues**: GitHub issues or support contact

## Next Steps

1. **Set up scheduled backups** - Automate with cron or daemon
2. **Test restore procedure** - Verify you can actually recover
3. **Configure monitoring** - Set up health checks and alerts
4. **Review runbook** - Understand emergency procedures
5. **Train team** - Ensure everyone knows the process

## Key Commands Reference

```python
# Create backup
await manager.create_backup(strategy=BackupStrategy.FULL)

# List backups
await manager.list_backups(verified_only=True)

# Restore backup
await manager.restore(backup_id, target)

# Verify backup
await manager.verify_backup(backup_id)

# Delete backup
await manager.delete_backup(backup_id)

# Apply retention
await manager.apply_retention_policy()

# Check health
await manager.get_health()
```

---

**Remember:** The best backup is one you've tested restoring from. Always verify your backups work!
