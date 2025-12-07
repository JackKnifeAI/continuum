# CONTINUUM Operations Runbook

Operational procedures for managing CONTINUUM infrastructure.

## Quick Reference

| Task | Command | Time |
|------|---------|------|
| Deploy to dev | `cd environments/dev && terraform apply` | 15-20 min |
| Scale ECS tasks | `aws ecs update-service --desired-count N` | 1-2 min |
| Database snapshot | `aws rds create-db-snapshot` | 5-10 min |
| View logs | `aws logs tail /aws/ecs/continuum-prod/app --follow` | Instant |
| Rollback deployment | `aws ecs update-service --task-definition <prev>` | 2-3 min |

## Common Operations

### Scaling

#### Manual ECS Scaling

```bash
# Scale up
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --desired-count 5

# Scale down
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --desired-count 2

# Verify
aws ecs describe-services \
  --cluster continuum-production-cluster \
  --services continuum-production-service \
  --query 'services[0].[runningCount,desiredCount]'
```

#### Adjust Auto-Scaling Limits

```bash
cd environments/production
vim terraform.tfvars

# Change:
autoscaling_min_capacity = 5  # Was 3
autoscaling_max_capacity = 15 # Was 10

terraform apply
```

#### Database Scaling

```bash
# Vertical scaling (instance size)
cd environments/production
vim terraform.tfvars

# Change:
instance_class = "db.r6g.xlarge"  # Was db.r6g.large

terraform apply  # Takes 15-30 minutes, has downtime for single-AZ

# Horizontal scaling (add read replica)
vim terraform.tfvars
read_replica_count = 3  # Was 2
terraform apply
```

### Deployments

#### Deploy New Application Version

```bash
# 1. Build and push image
cd /path/to/app
docker build -t continuum-app:v2.0.0 .
docker tag continuum-app:v2.0.0 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-prod-app:v2.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-prod-app:v2.0.0

# 2. Update Terraform variable
cd infrastructure/terraform/environments/production
vim terraform.tfvars
# Change: container_image = "...continuum-prod-app:v2.0.0"

# 3. Apply
terraform apply

# 4. Monitor deployment
aws ecs describe-services \
  --cluster continuum-production-cluster \
  --services continuum-production-service \
  --query 'services[0].events[0:5]'

# 5. Verify
curl https://example.com/health
```

#### Blue-Green Deployment

```bash
# 1. Deploy to staging first
cd environments/staging
# Update container_image to new version
terraform apply

# 2. Run smoke tests
./scripts/smoke-tests.sh staging

# 3. If successful, deploy to production
cd ../production
terraform apply

# 4. Monitor for errors
aws logs tail /aws/ecs/continuum-prod/app --follow --filter-pattern ERROR

# 5. If issues, rollback immediately
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --task-definition continuum-production-app:42  # Previous version
```

### Database Operations

#### Create Manual Backup

```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier continuum-production-db \
  --db-snapshot-identifier continuum-prod-manual-$(date +%Y%m%d-%H%M)

# Verify
aws rds describe-db-snapshots \
  --db-snapshot-identifier continuum-prod-manual-<timestamp> \
  --query 'DBSnapshots[0].[Status,PercentProgress]'
```

#### Restore from Backup

```bash
# 1. List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier continuum-production-db \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]' \
  --output table

# 2. Restore to new instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier continuum-production-db-restore \
  --db-snapshot-identifier <snapshot-id> \
  --db-subnet-group-name continuum-production-db-subnet-group \
  --vpc-security-group-ids <security-group-id>

# 3. Wait for instance to be available (~15 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier continuum-production-db-restore

# 4. Update application to use restored database
# Point connection string to new endpoint

# 5. After verification, optionally rename
# (Requires downtime - not recommended for production)
```

#### Run Database Migration

```bash
# 1. Create pre-migration snapshot
aws rds create-db-snapshot \
  --db-instance-identifier continuum-production-db \
  --db-snapshot-identifier pre-migration-$(date +%Y%m%d)

# 2. Connect to database
PGPASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id continuum-production-database-master-password \
  --query SecretString --output text | jq -r .password) \
psql -h $(terraform output -raw database_endpoint | cut -d: -f1) \
     -U continuum_admin \
     -d continuum

# 3. Run migration
\i migrations/v2_schema.sql

# 4. Verify
SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;

# 5. If issues, rollback
\i migrations/rollback_v2.sql
```

### Monitoring & Debugging

#### View Application Logs

```bash
# Real-time tail
aws logs tail /aws/ecs/continuum-production/app --follow

# Filter for errors
aws logs tail /aws/ecs/continuum-production/app --follow --filter-pattern ERROR

# Search logs for specific pattern
aws logs tail /aws/ecs/continuum-production/app \
  --since 1h \
  --filter-pattern '"user_id=12345"'

# Download logs for analysis
aws logs get-log-events \
  --log-group-name /aws/ecs/continuum-production/app \
  --log-stream-name <stream-name> \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --output json > logs.json
```

#### Access Running Container

```bash
# List running tasks
aws ecs list-tasks \
  --cluster continuum-production-cluster \
  --service-name continuum-production-service

# Execute command in container
aws ecs execute-command \
  --cluster continuum-production-cluster \
  --task <task-id> \
  --container app \
  --interactive \
  --command "/bin/bash"

# Inside container:
# - Check environment variables: env
# - Test database connection: nc -zv $DATABASE_HOST 5432
# - Check application health: curl localhost:8000/health
# - View application logs: tail -f /var/log/app.log
```

#### Check System Health

```bash
# ECS service status
aws ecs describe-services \
  --cluster continuum-production-cluster \
  --services continuum-production-service \
  --query 'services[0].[status,runningCount,desiredCount,deployments[0].rolloutState]'

# Database status
aws rds describe-db-instances \
  --db-instance-identifier continuum-production-db \
  --query 'DBInstances[0].[DBInstanceStatus,MultiAZ,StorageType]'

# Cache status
aws elasticache describe-replication-groups \
  --replication-group-id continuum-production-cache \
  --query 'ReplicationGroups[0].[Status,AutomaticFailover,MultiAZ]'

# ALB health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]'
```

### Security Operations

#### Rotate Secrets

```bash
# Database password rotation
aws secretsmanager rotate-secret \
  --secret-id continuum-production-database-master-password \
  --rotation-lambda-arn <lambda-arn>

# Verify rotation
aws secretsmanager describe-secret \
  --secret-id continuum-production-database-master-password \
  --query '[LastRotatedDate,RotationEnabled]'

# Force ECS to pick up new secret
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --force-new-deployment
```

#### Update SSL Certificate

```bash
# Request new certificate
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names "*.example.com" \
  --validation-method DNS \
  --region us-east-1

# Update Terraform with new ARN
cd environments/production
vim terraform.tfvars
# certificate_arn = "arn:aws:acm:..."

terraform apply
```

#### Review Security Groups

```bash
# List all security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Project,Values=CONTINUUM" \
  --query 'SecurityGroups[*].[GroupName,GroupId]'

# Audit specific group
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --query 'SecurityGroups[0].IpPermissions[*].[FromPort,ToPort,IpProtocol,IpRanges]'

# Check for overly permissive rules (0.0.0.0/0)
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].[GroupName,GroupId]'
```

## Incident Response

### High CPU Usage

```bash
# 1. Check current CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=continuum-production-cluster \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# 2. Scale up immediately if needed
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --desired-count 10

# 3. Investigate root cause
aws logs tail /aws/ecs/continuum-production/app --since 10m

# 4. If application issue, rollback
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --task-definition continuum-production-app:42
```

### Database Connection Pool Exhausted

```bash
# 1. Check current connections
PGPASSWORD=<password> psql -h <db-host> -U continuum_admin -d continuum \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# 2. Identify problematic queries
PGPASSWORD=<password> psql -h <db-host> -U continuum_admin -d continuum \
  -c "SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# 3. Kill long-running queries if needed
PGPASSWORD=<password> psql -h <db-host> -U continuum_admin -d continuum \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <pid>;"

# 4. Temporarily increase max_connections
cd infrastructure/terraform/environments/production
vim terraform.tfvars
# max_connections = "200"  # Was 100
terraform apply
```

### Out of Disk Space

```bash
# 1. Check current storage
aws rds describe-db-instances \
  --db-instance-identifier continuum-production-db \
  --query 'DBInstances[0].[AllocatedStorage,DBInstanceStatus]'

# 2. Check CloudWatch for free storage
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name FreeStorageSpace \
  --dimensions Name=DBInstanceIdentifier,Value=continuum-production-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Minimum

# 3. Emergency increase (if storage autoscaling not enabled)
aws rds modify-db-instance \
  --db-instance-identifier continuum-production-db \
  --allocated-storage 200 \
  --apply-immediately

# 4. Long-term: Enable autoscaling in Terraform
cd infrastructure/terraform/environments/production
vim terraform.tfvars
# max_allocated_storage = 1000
terraform apply
```

### Application Not Responding

```bash
# 1. Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn)

# 2. Check ECS task status
aws ecs describe-tasks \
  --cluster continuum-production-cluster \
  --tasks $(aws ecs list-tasks --cluster continuum-production-cluster --service-name continuum-production-service --query 'taskArns[0]' --output text)

# 3. Check recent events
aws ecs describe-services \
  --cluster continuum-production-cluster \
  --services continuum-production-service \
  --query 'services[0].events[0:10]'

# 4. Force new deployment
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --force-new-deployment
```

## Disaster Recovery

### Full Environment Restore

```bash
# 1. Restore database from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier continuum-production-db-dr \
  --db-snapshot-identifier <latest-snapshot>

# 2. Deploy infrastructure
cd infrastructure/terraform/environments/production
terraform apply

# 3. Update DNS (if needed)
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch file://dns-failover.json

# 4. Verify application
curl https://example.com/health
```

### Cross-Region Failover

```bash
# 1. Ensure RDS snapshot copied to DR region
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier <snapshot-arn> \
  --target-db-snapshot-identifier continuum-prod-dr \
  --source-region us-east-1 \
  --region us-west-2

# 2. Deploy to DR region
cd infrastructure/terraform/environments/production-dr
terraform apply

# 3. Update Route53 to point to DR region
# Use health check-based routing or manual failover
```

## Maintenance Windows

### Planned Database Maintenance

```bash
# 1. Notify users (1 hour before)
# Send email/Slack notification

# 2. Create pre-maintenance snapshot
aws rds create-db-snapshot \
  --db-instance-identifier continuum-production-db \
  --db-snapshot-identifier pre-maintenance-$(date +%Y%m%d)

# 3. Apply maintenance
aws rds modify-db-instance \
  --db-instance-identifier continuum-production-db \
  --apply-immediately \
  --engine-version <new-version>

# 4. Monitor upgrade progress
aws rds describe-db-instances \
  --db-instance-identifier continuum-production-db \
  --query 'DBInstances[0].DBInstanceStatus'

# 5. Verify application functionality
./scripts/smoke-tests.sh production

# 6. Notify users (completion)
```

## Backup Procedures

### Weekly Full Backup

```bash
#!/bin/bash
# weekly-backup.sh

DATE=$(date +%Y%m%d)

# Database snapshot
aws rds create-db-snapshot \
  --db-instance-identifier continuum-production-db \
  --db-snapshot-identifier weekly-backup-$DATE

# Export Terraform state
cd /path/to/terraform/environments/production
terraform state pull > terraform-state-$DATE.json

# Upload to S3
aws s3 cp terraform-state-$DATE.json \
  s3://continuum-backups/terraform-states/

# Backup secrets (encrypted)
aws secretsmanager list-secrets \
  --filters Key=tag-key,Values=Project Key=tag-value,Values=CONTINUUM \
  --query 'SecretList[*].Name' \
  --output text | xargs -I {} aws secretsmanager get-secret-value \
  --secret-id {} --output json > secrets-backup-$DATE.json

# Encrypt and upload
aws kms encrypt \
  --key-id alias/continuum-backups \
  --plaintext fileb://secrets-backup-$DATE.json \
  --output text \
  --query CiphertextBlob | base64 -d > secrets-backup-$DATE.encrypted

aws s3 cp secrets-backup-$DATE.encrypted \
  s3://continuum-backups/secrets/

# Cleanup
rm -f secrets-backup-$DATE.json terraform-state-$DATE.json
```

## Monitoring Checklist (Daily)

- [ ] Check CloudWatch dashboard for anomalies
- [ ] Review error rates in logs
- [ ] Verify all health checks passing
- [ ] Check auto-scaling activities
- [ ] Review cost anomalies in Cost Explorer
- [ ] Verify backups completed successfully
- [ ] Check Trusted Advisor recommendations

## Support Contacts

| Role | Contact | Hours |
|------|---------|-------|
| **On-Call Engineer** | +1-555-ONCALL | 24/7 |
| **DevOps Team** | devops@example.com | 9am-5pm ET |
| **AWS Support** | AWS Console | 24/7 (Enterprise) |
| **Database Admin** | dba@example.com | 9am-6pm ET |
| **Security Team** | security@example.com | 24/7 |

## Escalation Path

1. **Severity 1** (Production down): Page on-call immediately
2. **Severity 2** (Degraded performance): Slack #incidents + email devops
3. **Severity 3** (Non-urgent issues): Create Jira ticket
