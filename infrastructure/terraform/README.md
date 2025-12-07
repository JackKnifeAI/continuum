# CONTINUUM Infrastructure as Code

Complete Terraform infrastructure for deploying CONTINUUM across multiple environments (dev, staging, production) on AWS.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront CDN                          │
│                    (Production only, WAF)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Application Load Balancer                    │
│              (Multi-AZ, SSL/TLS, Health Checks)                 │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
    ┌─────────▼─────────┐         ┌──────────▼──────────┐
    │  ECS Fargate      │         │  ECS Fargate        │
    │  (Auto-scaling)   │         │  (Auto-scaling)     │
    │  ┌──────────────┐ │         │  ┌──────────────┐   │
    │  │ Container 1  │ │   ...   │  │ Container N  │   │
    │  └──────────────┘ │         │  └──────────────┘   │
    └─────────┬─────────┘         └──────────┬──────────┘
              │                              │
              └──────────────┬───────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼────────┐   ┌──────▼──────┐
│  PostgreSQL   │   │  Redis Cache    │   │  Secrets    │
│  RDS (Multi-  │   │  ElastiCache    │   │  Manager    │
│  AZ, pgvector)│   │  (Multi-AZ)     │   │             │
└───────────────┘   └─────────────────┘   └─────────────┘
```

## Features

- **Multi-Environment Support**: Separate configurations for dev, staging, and production
- **High Availability**: Multi-AZ deployments for production, single-AZ for dev
- **Auto-Scaling**: ECS services with CPU/memory/request-based scaling
- **Security**: VPC isolation, security groups, encryption at rest and in transit
- **Monitoring**: CloudWatch dashboards, alarms, SNS notifications
- **Cost Optimization**: Environment-specific instance sizing, resource limits
- **Disaster Recovery**: Automated backups, read replicas, snapshot retention
- **GitOps**: GitHub Actions CI/CD with automated plan/apply workflows

## Module Structure

```
terraform/
├── modules/
│   ├── networking/       # VPC, subnets, NAT, VPC endpoints
│   ├── database/         # PostgreSQL RDS with pgvector
│   ├── cache/            # Redis ElastiCache
│   ├── compute/          # ECS Fargate, ALB, auto-scaling
│   ├── cdn/              # CloudFront distribution
│   ├── monitoring/       # CloudWatch, SNS, dashboards
│   ├── secrets/          # Secrets Manager
│   └── dns/              # Route53 records, health checks
├── environments/
│   ├── dev/              # Development environment
│   ├── staging/          # Staging environment
│   └── production/       # Production environment
└── shared/
    ├── versions.tf       # Provider versions
    ├── backend.tf        # S3 backend configuration
    └── locals.tf         # Common local values
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.6.0
3. **AWS CLI** configured with credentials
4. **S3 Bucket** for Terraform state (create manually)
5. **DynamoDB Table** for state locking (create manually)
6. **Domain Name** (optional, for DNS)
7. **SSL Certificate** in ACM (for HTTPS)

## Quick Start

### 1. Create State Backend Resources

```bash
# Create S3 buckets for state
aws s3api create-bucket \
  --bucket continuum-terraform-state-dev \
  --region us-east-1

aws s3api create-bucket \
  --bucket continuum-terraform-state-staging \
  --region us-east-1

aws s3api create-bucket \
  --bucket continuum-terraform-state-production \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket continuum-terraform-state-dev \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name continuum-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. Configure Variables

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Deploy Development Environment

```bash
cd environments/dev

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply changes
terraform apply
```

### 4. Deploy Staging/Production

```bash
cd environments/staging  # or production
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform plan
terraform apply
```

## Environment Comparison

| Resource | Dev | Staging | Production |
|----------|-----|---------|------------|
| **VPC AZs** | 1 | 2 | 3 |
| **NAT Gateways** | 1 | 2 | 3 |
| **RDS Instance** | db.t4g.micro | db.t4g.medium | db.r6g.large |
| **RDS Multi-AZ** | No | Yes | Yes |
| **RDS Read Replicas** | 0 | 1 | 2 |
| **Redis Nodes** | 1 | 2 | 3 (cluster) |
| **ECS Tasks (CPU/Mem)** | 512/1024 | 1024/2048 | 2048/4096 |
| **ECS Desired Count** | 1 | 2 | 3 |
| **Auto-scale Max** | 3 | 5 | 10 |
| **Backup Retention** | 3 days | 14 days | 30 days |
| **CloudFront CDN** | No | No | Yes |
| **WAF** | No | No | Yes |
| **Performance Insights** | No | Yes | Yes |
| **Enhanced Monitoring** | No | Yes | Yes |

## Resource Outputs

After deployment, Terraform outputs:

- **ALB DNS Name**: Load balancer endpoint
- **ECR Repository URL**: Docker image registry
- **Database Endpoint**: PostgreSQL connection string
- **Redis Endpoint**: Cache connection string
- **Application URL**: Full HTTPS URL (if DNS configured)
- **CloudWatch Dashboard**: Monitoring dashboard name

Example:

```bash
terraform output
# alb_dns_name = "continuum-dev-alb-123456789.us-east-1.elb.amazonaws.com"
# application_url = "https://dev.example.com"
# ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/continuum-dev-app"
```

## CI/CD with GitHub Actions

The included GitHub Actions workflow automatically:

1. **On Pull Request**: Run `terraform plan` and comment results
2. **On Push to Main**: Auto-deploy to dev, manual approval for staging/production
3. **Path Filtering**: Only run when Terraform files change

### Setup GitHub Secrets

Required secrets:

```
AWS_ROLE_ARN_DEV
AWS_ROLE_ARN_STAGING
AWS_ROLE_ARN_PRODUCTION
CONTAINER_IMAGE_DEV
CONTAINER_IMAGE_STAGING
CONTAINER_IMAGE_PRODUCTION
CERTIFICATE_ARN_DEV
CERTIFICATE_ARN_STAGING
CERTIFICATE_ARN_PRODUCTION
ALARM_EMAIL
```

### Environment Protection Rules

Configure in GitHub Settings > Environments:

- **dev**: Auto-deploy on push to main
- **staging**: Require approval from 1 reviewer
- **production**: Require approval from 2 reviewers

## Disaster Recovery

### Database Backups

- **Automated Daily Backups**: Retention varies by environment
- **Manual Snapshots**: Create before major changes
- **Point-in-Time Recovery**: Enabled on all environments

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier continuum-production-db \
  --db-snapshot-identifier continuum-prod-manual-$(date +%Y%m%d)
```

### State Backup

Terraform state is versioned in S3. Restore previous version:

```bash
aws s3api list-object-versions \
  --bucket continuum-terraform-state-production \
  --prefix production/terraform.tfstate

aws s3api get-object \
  --bucket continuum-terraform-state-production \
  --key production/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup
```

## Security Best Practices

1. **Least Privilege IAM**: Use specific roles for each service
2. **Encryption**: At rest (KMS) and in transit (TLS) everywhere
3. **Network Isolation**: Private subnets for app/data tiers
4. **Security Groups**: Minimal ingress rules, explicit egress
5. **Secrets Management**: Never commit secrets, use AWS Secrets Manager
6. **WAF**: Enabled for production CloudFront
7. **VPC Flow Logs**: Enabled for audit trails
8. **Access Logging**: ALB logs to S3

## Monitoring & Alerts

### CloudWatch Dashboards

Access via AWS Console or Terraform output:

```bash
terraform output cloudwatch_dashboard
# https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=continuum-production-dashboard
```

### Alarms

Email notifications sent for:

- High CPU (>80% for 10 minutes)
- High Memory (>90% for 10 minutes)
- Low Disk Space (<5GB)
- Health Check Failures
- Error Rate Spikes

## Troubleshooting

### Common Issues

**State Lock Error**

```bash
# Force unlock (use carefully)
terraform force-unlock <LOCK_ID>
```

**Module Not Found**

```bash
# Re-initialize modules
terraform get -update
terraform init -upgrade
```

**Resource Already Exists**

```bash
# Import existing resource
terraform import module.compute.aws_ecs_cluster.main continuum-dev-cluster
```

**Plan Shows Unexpected Changes**

```bash
# Refresh state
terraform refresh
terraform plan
```

## Maintenance

### Update Dependencies

```bash
# Update provider versions
terraform init -upgrade

# Update module versions (if using registry)
terraform get -update
```

### Rotate Secrets

```bash
# Generate new database password
aws secretsmanager rotate-secret \
  --secret-id continuum-production-database-master-password
```

### Scale Resources

Edit `terraform.tfvars`:

```hcl
# Increase ECS task count
desired_count = 5

# Increase RDS size
instance_class = "db.r6g.xlarge"
```

Then apply:

```bash
terraform apply
```

## Cost Optimization

### Dev Environment (~$50-100/month)

- Single AZ, minimal instances
- No read replicas or CDN
- Reduced monitoring

### Staging Environment (~$200-300/month)

- Multi-AZ for reliability
- 1 read replica
- Full monitoring

### Production Environment (~$500-1000/month)

- Full redundancy (3 AZs)
- 2 read replicas
- CDN, WAF, enhanced monitoring
- Reserved instances for savings

### Savings Tips

1. **Use Spot Instances** for dev ECS tasks
2. **Reserved Instances** for production RDS (40% savings)
3. **Auto-scaling** to match demand
4. **S3 Lifecycle Policies** for logs
5. **Right-sizing** based on CloudWatch metrics

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/yourusername/continuum/issues
- **Documentation**: See individual module READMEs
- **AWS Support**: For infrastructure-specific issues

## License

MIT License - See LICENSE file for details
