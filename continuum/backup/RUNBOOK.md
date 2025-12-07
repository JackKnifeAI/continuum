# CONTINUUM Backup & Recovery Runbook

## Emergency Contact Information

### On-Call Schedule
- Primary: [Contact Info]
- Secondary: [Contact Info]
- Manager: [Contact Info]

### Escalation Path
1. Engineer → Senior Engineer (15 min)
2. Senior Engineer → Manager (30 min)
3. Manager → Director (1 hour)

---

## Common Scenarios

### Scenario 1: Database Corruption Detected

**Symptoms:**
- Database integrity check fails
- Application errors reading data
- SQLite corruption errors

**Immediate Actions:**
1. **Stop writes to database** (prevent further corruption)
2. **Assess damage:**
   ```bash
   sqlite3 /var/lib/continuum/memory.db "PRAGMA integrity_check"
   ```
3. **Identify last known good backup:**
   ```bash
   continuum backup list --verified-only
   ```

**Recovery Procedure:**

```bash
# 1. Backup corrupted database (for forensics)
cp /var/lib/continuum/memory.db /tmp/corrupted_$(date +%Y%m%d_%H%M%S).db

# 2. Find latest verified backup
BACKUP_ID=$(continuum backup list --verified-only --limit 1 --format json | jq -r '.[0].backup_id')

# 3. Restore from backup
continuum backup restore $BACKUP_ID \
  --target /var/lib/continuum/memory.db \
  --overwrite \
  --verify

# 4. Verify restored database
sqlite3 /var/lib/continuum/memory.db "PRAGMA integrity_check"

# 5. Check record counts
continuum backup compare-counts $BACKUP_ID /var/lib/continuum/memory.db

# 6. Resume operations
systemctl start continuum
```

**Estimated RTO:** 15-20 minutes

**Post-Incident:**
- Investigate root cause of corruption
- Review backup verification results
- Update monitoring if needed

---

### Scenario 2: Accidental Data Deletion

**Symptoms:**
- User reports missing data
- Records deleted in error
- Table dropped accidentally

**Immediate Actions:**
1. **Stop application** (prevent further changes)
2. **Determine deletion time** (approximate)
3. **Find backup before deletion**

**Recovery Procedure:**

```bash
# 1. Identify deletion time
DELETION_TIME="2025-12-06T14:30:00Z"

# 2. Find backup before deletion
continuum backup list --before $DELETION_TIME

# 3. Point-in-time restore to just before deletion
continuum backup restore \
  --pitr $DELETION_TIME \
  --target /tmp/recovery.db

# 4. Extract deleted data
sqlite3 /tmp/recovery.db ".dump table_name" > /tmp/deleted_data.sql

# 5. Import into current database
sqlite3 /var/lib/continuum/memory.db < /tmp/deleted_data.sql

# 6. Verify recovered data
continuum backup verify-recovery

# 7. Resume operations
systemctl start continuum
```

**Estimated RTO:** 30-45 minutes

---

### Scenario 3: Complete Data Center Failure

**Symptoms:**
- Primary data center unreachable
- All local backups inaccessible
- Need to failover to secondary region

**Immediate Actions:**
1. **Declare disaster** (activate DR plan)
2. **Notify stakeholders**
3. **Failover to cloud backups**

**Recovery Procedure:**

```bash
# 1. Provision new infrastructure
terraform apply -var="region=us-west-2"

# 2. Find latest cloud backup
continuum backup list \
  --storage s3 \
  --verified-only \
  --limit 1

# 3. Restore from cloud
continuum backup restore $BACKUP_ID \
  --storage s3 \
  --target /var/lib/continuum/memory.db \
  --region us-west-2

# 4. Start application
systemctl start continuum

# 5. Verify operation
continuum health-check

# 6. Update DNS
# (Point continuum.example.com to new region)

# 7. Monitor closely
tail -f /var/log/continuum/continuum.log
```

**Estimated RTO:** 45-60 minutes

**Post-Incident:**
- Root cause analysis
- Update DR procedures
- Test restored system thoroughly

---

### Scenario 4: Ransomware Attack

**Symptoms:**
- Files encrypted
- Ransom note present
- Database inaccessible

**Immediate Actions:**
1. **ISOLATE SYSTEMS** (disconnect network)
2. **Do NOT pay ransom**
3. **Assess infection scope**
4. **Engage security team**

**Recovery Procedure:**

```bash
# 1. Identify last clean backup (before infection)
# Check backup timestamps vs infection time
INFECTION_TIME="2025-12-06T12:00:00Z"

continuum backup list --before $INFECTION_TIME --verified-only

# 2. Wipe infected systems
# (Reimage from known-good OS image)

# 3. Restore from pre-infection backup
CLEAN_BACKUP_ID="backup-full-20251206-010000"

continuum backup restore $CLEAN_BACKUP_ID \
  --target /var/lib/continuum/memory.db \
  --verify

# 4. Scan restored system
clamscan -r /var/lib/continuum/

# 5. Harden security
# - Update passwords
# - Patch systems
# - Review access logs

# 6. Resume operations
systemctl start continuum

# 7. Monitor for re-infection
tail -f /var/log/audit/audit.log
```

**Estimated RTO:** 60-90 minutes

**Post-Incident:**
- Full security audit
- Review backup isolation
- Update security controls
- Report to authorities if needed

---

### Scenario 5: Backup Failure

**Symptoms:**
- Backup job fails
- RPO SLA breach alert
- No recent backups

**Immediate Actions:**
1. **Check backup logs**
2. **Verify storage connectivity**
3. **Check disk space**

**Diagnosis:**

```bash
# 1. Check recent backup status
continuum backup list --limit 10

# 2. View backup logs
tail -100 /var/log/continuum/backup.log

# 3. Test storage connectivity
continuum backup test-storage

# 4. Check disk space
df -h /var/backups

# 5. Check permissions
ls -la /var/backups

# 6. Test manual backup
continuum backup create --strategy full --debug
```

**Common Causes & Fixes:**

#### Disk Full
```bash
# Apply retention policy immediately
continuum backup apply-retention

# Increase disk size
lvextend -L +50G /dev/vg/backups
resize2fs /dev/vg/backups
```

#### Permission Denied
```bash
# Fix ownership
chown -R continuum:continuum /var/backups

# Fix permissions
chmod 755 /var/backups
chmod 644 /var/backups/*.backup
```

#### Network Error (Cloud Storage)
```bash
# Test S3 connectivity
aws s3 ls s3://continuum-backups/

# Check credentials
aws sts get-caller-identity

# Verify IAM permissions
aws iam get-user-policy --user-name continuum-backup
```

#### Database Locked
```bash
# Check for long-running queries
sqlite3 /var/lib/continuum/memory.db "PRAGMA busy_timeout=30000"

# Kill hanging processes
ps aux | grep continuum
kill -9 <PID>
```

---

## Verification Procedures

### Daily Verification Checklist

```bash
# 1. Check last backup time
continuum backup health | grep "Last backup"

# 2. Verify recent backups
continuum backup verify $(continuum backup list --limit 1 --format json | jq -r '.[0].backup_id')

# 3. Check storage usage
continuum backup storage-usage

# 4. Review failed backups
continuum backup list --status failed --since 24h

# 5. Test restore (weekly)
continuum backup test-restore --latest
```

### Monthly DR Drill

```bash
# 1. Select random backup
DRILL_BACKUP=$(continuum backup list --verified-only --random 1)

# 2. Restore to test environment
continuum backup restore $DRILL_BACKUP \
  --target /tmp/dr-drill.db \
  --verify

# 3. Run application tests
pytest tests/integration/

# 4. Document results
echo "DR Drill $(date): SUCCESS" >> /var/log/continuum/dr-drills.log

# 5. Clean up
rm /tmp/dr-drill.db
```

---

## Performance Tuning

### Slow Backups

```bash
# 1. Check backup duration trend
continuum backup metrics backup_duration_seconds

# 2. Profile backup
continuum backup create --strategy full --profile

# 3. Optimize compression
# Reduce compression level for speed
continuum backup config set compression_level 1

# 4. Use faster compression
continuum backup config set compression_algorithm lz4

# 5. Parallel uploads
continuum backup config set max_concurrent_uploads 8
```

### Large Backup Size

```bash
# 1. Check compression ratio
continuum backup list --format json | jq '.[] | {id: .backup_id, ratio: .compression_ratio}'

# 2. Increase compression
continuum backup config set compression_level 9
continuum backup config set compression_algorithm zstd

# 3. Analyze data patterns
sqlite3 /var/lib/continuum/memory.db ".schema"

# 4. Consider incremental strategy
continuum backup create --strategy incremental
```

---

## Monitoring & Alerts

### Critical Alerts

#### Backup Failed
```bash
# Investigation
continuum backup logs --level error --since 1h

# Resolution
# Fix underlying issue, then:
continuum backup create --strategy full --force
```

#### RPO SLA Breach
```bash
# Check last successful backup
continuum backup list --status completed --limit 1

# If > 5 minutes ago:
# 1. Check backup scheduler
systemctl status continuum-backup

# 2. Run immediate backup
continuum backup create --strategy incremental --priority high
```

#### Storage Almost Full
```bash
# Apply retention immediately
continuum backup apply-retention --aggressive

# Add storage capacity
# OR
# Configure lifecycle policies to move to cheaper storage
```

---

## Maintenance Windows

### Weekly Maintenance

**When:** Sunday 1:00 AM - 3:00 AM UTC

**Tasks:**
1. Full backup
2. Backup verification
3. Restore test
4. Retention policy application
5. Performance analysis

**Procedure:**
```bash
# 1. Create full backup
continuum backup create --strategy full

# 2. Verify all backups from last week
continuum backup verify-all --since 7d

# 3. Test restore
continuum backup test-restore --latest

# 4. Apply retention
continuum backup apply-retention

# 5. Generate report
continuum backup report --week
```

---

## Security Procedures

### Key Rotation

**Frequency:** Quarterly

**Procedure:**
```bash
# 1. Generate new encryption key
continuum backup key-generate --id backup-key-v2

# 2. Re-encrypt recent backups with new key
continuum backup re-encrypt --since 30d --key-id backup-key-v2

# 3. Update configuration
continuum backup config set encryption_key_id backup-key-v2

# 4. Verify re-encryption
continuum backup verify --since 30d

# 5. Archive old key (do NOT delete yet)
continuum backup key-archive backup-key-v1
```

### Access Audit

**Frequency:** Monthly

**Procedure:**
```bash
# 1. Review backup access logs
continuum backup audit --since 30d

# 2. Check IAM permissions
aws iam get-user-policy --user-name continuum-backup

# 3. Review S3 bucket policy
aws s3api get-bucket-policy --bucket continuum-backups

# 4. Verify MFA enforcement
aws iam get-user-mfa --user-name continuum-backup
```

---

## Appendix

### Useful Commands

```bash
# List all backups
continuum backup list

# Create manual backup
continuum backup create --strategy full

# Restore specific backup
continuum backup restore <backup-id> --target /path/to/restore

# Verify backup
continuum backup verify <backup-id>

# Check system health
continuum backup health

# View logs
continuum backup logs --tail 100

# Apply retention policy
continuum backup apply-retention

# Test storage connectivity
continuum backup test-storage

# Generate report
continuum backup report --month
```

### Log Locations

- Backup logs: `/var/log/continuum/backup.log`
- Application logs: `/var/log/continuum/continuum.log`
- Audit logs: `/var/log/audit/audit.log`

### Configuration Files

- Main config: `/etc/continuum/backup.conf`
- Storage config: `/etc/continuum/storage.conf`
- Retention policy: `/etc/continuum/retention.conf`

### Important Paths

- Database: `/var/lib/continuum/memory.db`
- Local backups: `/var/backups/continuum/`
- Temp directory: `/tmp/continuum-backup/`
- Metadata: `/var/lib/continuum/backups/metadata.db`
