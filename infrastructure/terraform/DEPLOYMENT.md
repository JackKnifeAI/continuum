# CONTINUUM Deployment Guide

Step-by-step guide for deploying CONTINUUM infrastructure using Terraform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Development Deployment](#development-deployment)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Post-Deployment](#post-deployment)
7. [Rollback Procedures](#rollback-procedures)

## Prerequisites

### Required Tools

```bash
# Install Terraform
brew install terraform  # macOS
# or
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version  # Should show v1.6.0 or higher

# Install AWS CLI
pip install awscli --upgrade

# Configure AWS credentials
aws configure
```

### AWS Permissions

Required IAM permissions for deploying:

- VPC and networking resources
- RDS databases
- ElastiCache clusters
- ECS Fargate services
- Application Load Balancers
- CloudFront distributions
- Route53 DNS records
- CloudWatch logs and alarms
- Secrets Manager
- KMS keys
- IAM roles and policies

**Recommended**: Use an IAM role with `AdministratorAccess` for initial deployment, then restrict to specific permissions.

### Domain and SSL

1. **Register domain** (or use existing)
2. **Create SSL certificate** in ACM:
   ```bash
   aws acm request-certificate \
     --domain-name example.com \
     --subject-alternative-names "*.example.com" \
     --validation-method DNS \
     --region us-east-1
   ```
3. **Validate certificate** via DNS records

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/continuum.git
cd continuum/infrastructure/terraform
```

### 2. Create State Backend

```bash
# Run the bootstrap script
./scripts/bootstrap-backend.sh

# Or manually:
for env in dev staging production; do
  aws s3api create-bucket \
    --bucket continuum-terraform-state-${env} \
    --region us-east-1

  aws s3api put-bucket-versioning \
    --bucket continuum-terraform-state-${env} \
    --versioning-configuration Status=Enabled

  aws s3api put-bucket-encryption \
    --bucket continuum-terraform-state-${env} \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'

  aws s3api put-public-access-block \
    --bucket continuum-terraform-state-${env} \
    --public-access-block-configuration \
      "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
done

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name continuum-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 3. Build and Push Docker Image

```bash
# Build application image
cd ../../
docker build -t continuum-app:latest .

# Tag for ECR (we'll create ECR in Terraform, but need initial image)
# For first deployment, use a public image or create ECR manually:
aws ecr create-repository --repository-name continuum-dev-app --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag continuum-app:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-dev-app:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-dev-app:latest
```

## Development Deployment

### 1. Configure Variables

```bash
cd infrastructure/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
vim terraform.tfvars
```

Minimum required variables:

```hcl
aws_region      = "us-east-1"
vpc_cidr        = "10.0.0.0/16"
container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-dev-app:latest"
alarm_email     = "dev-team@example.com"
```

### 2. Initialize Terraform

```bash
terraform init

# Expected output:
# Terraform has been successfully initialized!
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan

# Review the plan carefully:
# - 40+ resources will be created
# - No resources destroyed (first deployment)
# - Check for any unexpected changes
```

### 4. Apply Configuration

```bash
terraform apply tfplan

# This will take 15-20 minutes
# Watch for errors during:
# - VPC creation
# - RDS provisioning (longest step)
# - ECS service creation
```

### 5. Verify Deployment

```bash
# Get outputs
terraform output

# Test ALB endpoint
curl http://$(terraform output -raw alb_dns_name)/health

# Expected: {"status": "healthy"}
```

### 6. Access Application

```bash
# Get ALB DNS
ALB_DNS=$(terraform output -raw alb_dns_name)
echo "Application available at: http://${ALB_DNS}"

# Or with custom domain:
echo "Application available at: $(terraform output -raw application_url)"
```

## Staging Deployment

### 1. Configure Staging Variables

```bash
cd ../staging
cp terraform.tfvars.example terraform.tfvars

# Edit with staging-specific values
vim terraform.tfvars
```

Required variables:

```hcl
aws_region      = "us-east-1"
vpc_cidr        = "10.1.0.0/16"  # Different from dev!
container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-staging-app:latest"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
alarm_email     = "staging-alerts@example.com"
domain_name     = "example.com"
hosted_zone_id  = "Z1234567890ABC"
```

### 2. Deploy Staging

```bash
terraform init
terraform plan
terraform apply

# Takes 20-25 minutes (Multi-AZ resources)
```

### 3. Smoke Tests

```bash
# Test HTTPS endpoint
curl https://staging.example.com/health

# Test database connectivity
aws rds describe-db-instances \
  --db-instance-identifier continuum-staging-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Test Redis
aws elasticache describe-replication-groups \
  --replication-group-id continuum-staging-cache \
  --query 'ReplicationGroups[0].Status'
```

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] Staging environment tested and stable
- [ ] Database migration scripts tested
- [ ] SSL certificate validated
- [ ] DNS records prepared
- [ ] Backup procedures documented
- [ ] Rollback plan ready
- [ ] Change approval obtained
- [ ] Team notification sent

### 2. Configure Production Variables

```bash
cd ../production
cp terraform.tfvars.example terraform.tfvars

# Edit with production values
vim terraform.tfvars
```

Production variables:

```hcl
aws_region          = "us-east-1"
vpc_cidr            = "10.2.0.0/16"
container_image     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-prod-app:v1.0.0"
certificate_arn     = "arn:aws:acm:us-east-1:123456789012:certificate/..."
alarm_email         = "ops-team@example.com"
domain_name         = "example.com"
subdomain           = ""  # Empty for apex domain
hosted_zone_id      = "Z1234567890ABC"
cdn_domain_aliases  = ["www.example.com", "example.com"]
cdn_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
cdn_logging_bucket  = "continuum-cdn-logs.s3.amazonaws.com"
waf_web_acl_arn     = "arn:aws:wafv2:us-east-1:123456789012:global/webacl/..."
```

### 3. Create WAF Web ACL (Optional)

```bash
# Create WAF for production
aws wafv2 create-web-acl \
  --name continuum-production-waf \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules file://waf-rules.json \
  --region us-east-1
```

### 4. Deploy Production

```bash
terraform init
terraform plan -out=tfplan

# CRITICAL: Review plan carefully
# - Verify no data resources will be destroyed
# - Check all security groups are restrictive
# - Confirm Multi-AZ and redundancy settings

# Apply with approval
terraform apply tfplan

# Takes 30-40 minutes (largest deployment)
```

### 5. Post-Deployment Validation

```bash
# Health checks
curl https://example.com/health
curl https://www.example.com/health

# Test auto-scaling
ab -n 10000 -c 100 https://example.com/

# Monitor scaling in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=continuum-production-cluster \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Test database replication
aws rds describe-db-instances \
  --filters "Name=db-instance-id,Values=continuum-production-db-replica*" \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]'
```

### 6. Update DNS (If Not Managed by Terraform)

```bash
# Point domain to CloudFront
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://dns-changes.json
```

### 7. Enable Monitoring

```bash
# Subscribe to SNS topic
aws sns subscribe \
  --topic-arn $(terraform output -raw monitoring_sns_topic_arn) \
  --protocol email \
  --notification-endpoint ops-team@example.com

# Confirm subscription in email
```

## Post-Deployment

### 1. Documentation

Update the following:

- Architecture diagrams
- Runbook with new endpoints
- Incident response procedures
- Backup and restore procedures

### 2. Team Access

```bash
# Grant team members access to CloudWatch
aws iam attach-user-policy \
  --user-name developer@example.com \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess

# Grant RDS read-only access
aws rds create-db-security-group \
  --db-security-group-name dev-read-only \
  --db-security-group-description "Developer read-only access"
```

### 3. Monitoring Setup

```bash
# Add CloudWatch dashboard to browser favorites
terraform output cloudwatch_dashboard

# Set up alerts in Slack/PagerDuty (integrate with SNS topic)
# Configure log aggregation (Datadog, Splunk, etc.)
```

### 4. Backup Verification

```bash
# Verify RDS backups
aws rds describe-db-snapshots \
  --db-instance-identifier continuum-production-db \
  --query 'DBSnapshots[0].[DBSnapshotIdentifier,SnapshotCreateTime,Status]'

# Test restore to verify backups work
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier continuum-production-db-restore-test \
  --db-snapshot-identifier <snapshot-id>
```

## Rollback Procedures

### Rollback ECS Deployment

```bash
# List task definition revisions
aws ecs list-task-definitions \
  --family-prefix continuum-production-app \
  --sort DESC

# Update service to previous revision
aws ecs update-service \
  --cluster continuum-production-cluster \
  --service continuum-production-service \
  --task-definition continuum-production-app:42  # Previous revision
```

### Rollback Terraform Changes

```bash
# Revert to previous state version
cd environments/production

# List state versions
aws s3api list-object-versions \
  --bucket continuum-terraform-state-production \
  --prefix production/terraform.tfstate

# Download previous version
aws s3api get-object \
  --bucket continuum-terraform-state-production \
  --key production/terraform.tfstate \
  --version-id <previous-version-id> \
  terraform.tfstate

# Apply previous state
terraform apply
```

### Rollback Database Migration

```bash
# Connect to database
PGPASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id continuum-production-database-master-password \
  --query SecretString --output text | jq -r .password) \
psql -h $(terraform output -raw database_endpoint) \
     -U continuum_admin \
     -d continuum

# Run rollback migration
\i migrations/rollback_v2_to_v1.sql
```

## Troubleshooting

### ECS Tasks Not Starting

```bash
# Check task definition
aws ecs describe-task-definition \
  --task-definition continuum-production-app

# Check service events
aws ecs describe-services \
  --cluster continuum-production-cluster \
  --services continuum-production-service \
  --query 'services[0].events[0:5]'

# Check logs
aws logs tail /aws/ecs/continuum-production/app --follow
```

### Database Connection Issues

```bash
# Check security groups
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw database_security_group_id)

# Test connectivity from ECS task
aws ecs execute-command \
  --cluster continuum-production-cluster \
  --task <task-id> \
  --container app \
  --interactive \
  --command "/bin/bash"

# Inside container:
nc -zv <db-host> 5432
```

### Terraform State Lock

```bash
# Check lock status
aws dynamodb get-item \
  --table-name continuum-terraform-locks \
  --key '{"LockID":{"S":"continuum-terraform-state-production/production/terraform.tfstate"}}'

# Force unlock (use carefully!)
terraform force-unlock <lock-id>
```

## Next Steps

After successful deployment:

1. **Set up CI/CD**: Configure GitHub Actions for automated deployments
2. **Implement Monitoring**: Add custom metrics and dashboards
3. **Load Testing**: Verify auto-scaling works as expected
4. **Disaster Recovery Drill**: Practice restore procedures
5. **Cost Optimization**: Review and optimize resource usage
6. **Security Audit**: Run security scanning tools
7. **Documentation**: Update runbooks and procedures

## Support

For deployment issues:

- **Slack**: #infrastructure channel
- **Email**: devops@example.com
- **On-call**: +1-555-ONCALL
- **GitHub Issues**: https://github.com/yourusername/continuum/issues
