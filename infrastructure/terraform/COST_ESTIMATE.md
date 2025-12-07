# CONTINUUM Infrastructure Cost Estimate

Monthly cost estimates for CONTINUUM infrastructure across all environments.

**Last Updated**: December 2025
**Region**: us-east-1 (N. Virginia)
**Currency**: USD

## Executive Summary

| Environment | Monthly Cost | Annual Cost | Cost/User* |
|-------------|--------------|-------------|------------|
| **Development** | $85 - $120 | $1,020 - $1,440 | N/A |
| **Staging** | $280 - $350 | $3,360 - $4,200 | N/A |
| **Production** | $620 - $850 | $7,440 - $10,200 | $0.06 - $0.08 |

*Based on 10,000 monthly active users for production

**Total Monthly Cost (All Environments)**: $985 - $1,320
**Total Annual Cost (All Environments)**: $11,820 - $15,840

## Development Environment

**Target**: Development and testing
**Uptime**: ~40 hours/week (Mon-Fri 9am-5pm)
**Monthly Cost**: **$85 - $120**

### Detailed Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **Compute** | | | |
| ECS Fargate | 0.5 vCPU, 1GB RAM, 1 task, ~40h/week | $8 | Dev hours only |
| Application Load Balancer | 1 ALB, minimal traffic | $18 | Always running |
| NAT Gateway | 1 NAT, 10GB data/month | $35 | $32.40 + $0.045/GB |
| **Database** | | | |
| RDS PostgreSQL | db.t4g.micro, 20GB gp3 | $15 | Single-AZ |
| RDS Backup Storage | 20GB | $2 | |
| **Cache** | | | |
| ElastiCache Redis | cache.t4g.micro, 1 node | $12 | |
| **Networking** | | | |
| Data Transfer | ~10GB/month | $1 | First 1GB free |
| VPC | Standard VPC | $0 | No charge |
| **Monitoring** | | | |
| CloudWatch Logs | 5GB ingestion, 7 day retention | $3 | |
| CloudWatch Alarms | 5 alarms | $1 | $0.10/alarm |
| **Secrets** | | | |
| Secrets Manager | 2 secrets | $1 | $0.40/secret |
| **Storage** | | | |
| S3 (logs, backups) | 10GB | $0.23 | |
| **KMS** | | | |
| KMS Keys | 3 keys, minimal API calls | $3 | $1/key/month |
| | | | |
| **SUBTOTAL** | | **$99** | |
| **Reserve (10%)** | | **$10** | For overages |
| **TOTAL** | | **$85 - $120** | |

### Cost Optimization for Dev

- **Stop during off-hours**: Use scheduling to stop ECS tasks nights/weekends (-50%)
- **Use Spot instances**: Save 70% on compute (requires configuration)
- **Reduce log retention**: 1 day instead of 7 (-60% CloudWatch costs)
- **Delete old snapshots**: Keep only 3 days of backups

**Optimized Dev Cost**: **$45 - $60/month**

## Staging Environment

**Target**: Pre-production testing, QA
**Uptime**: 24/7
**Monthly Cost**: **$280 - $350**

### Detailed Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **Compute** | | | |
| ECS Fargate | 1 vCPU, 2GB RAM, 2 tasks avg | $55 | Auto-scales 1-5 |
| Application Load Balancer | 1 ALB, moderate traffic | $25 | 24/7 availability |
| NAT Gateway | 2 NATs, 50GB data/month | $75 | Multi-AZ |
| **Database** | | | |
| RDS PostgreSQL | db.t4g.medium, 50GB gp3, Multi-AZ | $85 | High availability |
| RDS Read Replica | db.t4g.medium, 50GB | $45 | For testing replication |
| RDS Backup Storage | 100GB (14 days) | $10 | Extended retention |
| **Cache** | | | |
| ElastiCache Redis | cache.t4g.medium, 2 nodes, Multi-AZ | $55 | Failover enabled |
| **Networking** | | | |
| Data Transfer | ~50GB/month | $5 | |
| VPC Endpoints | 2 endpoints | $15 | ECR, Secrets Manager |
| VPC Flow Logs | 20GB/month | $10 | Security audit |
| **Monitoring** | | | |
| CloudWatch Logs | 25GB ingestion, 14 day retention | $15 | |
| CloudWatch Alarms | 15 alarms | $2 | Enhanced monitoring |
| CloudWatch Dashboards | 1 custom dashboard | $3 | |
| **Secrets** | | | |
| Secrets Manager | 5 secrets | $2 | |
| **Storage** | | | |
| S3 (logs, backups) | 50GB | $1.15 | |
| **KMS** | | | |
| KMS Keys | 5 keys | $5 | |
| **Performance Insights** | | | |
| RDS Performance Insights | 7 days retention | $5 | Database monitoring |
| | | | |
| **SUBTOTAL** | | **$313** | |
| **Reserve (10%)** | | **$31** | |
| **TOTAL** | | **$280 - $350** | |

## Production Environment

**Target**: Live production workload
**Uptime**: 99.95% SLA (24/7)
**Traffic**: 10,000 MAU, 100K requests/day
**Monthly Cost**: **$620 - $850**

### Detailed Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **Compute** | | | |
| ECS Fargate | 2 vCPU, 4GB RAM, 3-10 tasks | $185 | Auto-scaling enabled |
| Application Load Balancer | 1 ALB, high traffic | $35 | 100K requests/day |
| NAT Gateway | 3 NATs, 200GB data/month | $115 | 3 AZs for HA |
| **Database** | | | |
| RDS PostgreSQL | db.r6g.large, 100GB gp3, Multi-AZ | $285 | Production-grade |
| RDS Read Replicas | 2x db.r6g.large | $260 | Read scaling |
| RDS Backup Storage | 500GB (30 days) | $48 | Compliance retention |
| **Cache** | | | |
| ElastiCache Redis | cache.r6g.large, cluster mode, 3 shards, 2 replicas each | $180 | 9 nodes total |
| **CDN** | | | |
| CloudFront | 500GB data transfer, 1M requests | $60 | Global distribution |
| **WAF** | | | |
| AWS WAF | 1 Web ACL, 5 rules | $8 | DDoS protection |
| **Networking** | | | |
| Data Transfer | ~200GB/month | $18 | |
| VPC Endpoints | 4 endpoints | $30 | Cost optimization |
| VPC Flow Logs | 100GB/month | $50 | Security compliance |
| **Monitoring** | | | |
| CloudWatch Logs | 100GB ingestion, 30 day retention | $60 | Production logging |
| CloudWatch Alarms | 30 alarms | $3 | Comprehensive alerts |
| CloudWatch Dashboards | 2 custom dashboards | $6 | Ops + Business |
| CloudWatch Insights | Query analysis | $5 | Log analytics |
| **Secrets** | | | |
| Secrets Manager | 10 secrets | $4 | |
| Secrets Manager Rotation | 2 rotations/month | $1 | Automated rotation |
| **Storage** | | | |
| S3 (logs, backups, CDN origin) | 200GB | $4.60 | Multi-tier storage |
| S3 Glacier (archives) | 500GB | $2 | Long-term backups |
| **KMS** | | | |
| KMS Keys | 8 keys, 10K API calls | $10 | Encryption at rest |
| **DNS** | | | |
| Route53 Hosted Zone | 1 zone | $0.50 | |
| Route53 Queries | 1M queries/month | $0.40 | |
| Route53 Health Checks | 2 endpoints | $1 | Failover monitoring |
| **Performance Insights** | | | |
| RDS Performance Insights | 3 DBs, 7 days | $15 | All DB instances |
| **Container Insights** | | | |
| ECS Container Insights | Cluster metrics | $8 | ECS monitoring |
| | | | |
| **SUBTOTAL** | | **$723** | |
| **Reserve (15%)** | | **$108** | Higher buffer for prod |
| **TOTAL** | | **$620 - $850** | |

### Reserved Instance Savings (Production)

Purchasing 1-year reserved instances:

| Service | On-Demand | Reserved (1yr) | Savings |
|---------|-----------|----------------|---------|
| RDS db.r6g.large (3 instances) | $545/mo | $327/mo | $218/mo (40%) |
| ElastiCache r6g.large nodes | $180/mo | $108/mo | $72/mo (40%) |
| | | | |
| **Total Savings** | | | **$290/mo** |
| **New Production Cost** | | **$330 - $560/mo** | |
| **Annual Savings** | | | **$3,480** |

## Cost Breakdown by Category

### All Environments Combined

| Category | Dev | Staging | Production | Total/Month |
|----------|-----|---------|------------|-------------|
| **Compute (ECS, ALB)** | $26 | $80 | $220 | $326 |
| **Networking (NAT, Data Transfer)** | $36 | $90 | $133 | $259 |
| **Database (RDS)** | $17 | $140 | $593 | $750 |
| **Cache (Redis)** | $12 | $55 | $180 | $247 |
| **CDN & WAF** | $0 | $0 | $68 | $68 |
| **Monitoring** | $4 | $20 | $92 | $116 |
| **Storage & Backups** | $2 | $11 | $55 | $68 |
| **Security (KMS, Secrets)** | $4 | $7 | $15 | $26 |
| **DNS** | $0 | $0 | $2 | $2 |
| | | | | |
| **TOTAL** | **$101** | **$303** | **$1,358** | **$1,762** |

## Cost Scaling Projections

### Production Growth Scenarios

| Metric | Current | 10x Growth | 100x Growth |
|--------|---------|------------|-------------|
| **Monthly Active Users** | 10K | 100K | 1M |
| **Requests/Day** | 100K | 1M | 10M |
| **Database Size** | 100GB | 500GB | 2TB |
| **Monthly Cost** | $723 | $1,850 | $5,200 |
| **Cost per User** | $0.072 | $0.019 | $0.005 |

Key scaling factors:

1. **Compute**: Auto-scaling handles most growth efficiently
2. **Database**: Largest cost increase (read replicas + storage)
3. **CDN**: Cost decreases per-user at scale (volume discounts)
4. **Networking**: Relatively flat with VPC endpoints

## Cost Optimization Strategies

### Immediate Wins (0-30 days)

1. **Reserved Instances**: Save 40% on RDS and ElastiCache
   - **Savings**: $290/month
   - **Effort**: Low (1 hour to purchase)

2. **S3 Lifecycle Policies**: Move old backups to Glacier
   - **Savings**: $20/month
   - **Effort**: Low (30 minutes to configure)

3. **CloudWatch Log Retention**: Reduce non-critical logs to 7 days
   - **Savings**: $15/month
   - **Effort**: Low (15 minutes)

4. **Scheduled Scaling**: Stop dev environment nights/weekends
   - **Savings**: $30/month
   - **Effort**: Medium (2 hours to implement)

**Total Quick Wins**: **$355/month ($4,260/year)**

### Medium-Term Optimizations (1-3 months)

1. **Savings Plans**: Commit to 1-3 year compute usage
   - **Savings**: Additional 10-15% on top of RIs
   - **Annual Savings**: $1,500

2. **Rightsizing**: Analyze CloudWatch metrics and downsize over-provisioned resources
   - **Savings**: $100/month
   - **Requires**: Continuous monitoring

3. **Spot Instances**: Use for dev/staging ECS tasks
   - **Savings**: $50/month
   - **Tradeoff**: Potential interruptions

4. **Multi-AZ Optimization**: Single-AZ for staging (non-critical)
   - **Savings**: $80/month
   - **Tradeoff**: Reduced availability in staging

**Total Medium-Term Savings**: $230/month ($2,760/year)

### Long-Term Strategies (3-12 months)

1. **Multi-Region**: Deploy to cheaper regions (e.g., us-west-2)
   - **Savings**: 5-10% on compute/storage
   - **Complexity**: High

2. **Database Optimization**: Implement caching strategies to reduce RDS read replicas
   - **Savings**: $130/month
   - **Effort**: Significant code changes

3. **CDN Optimization**: Optimize cache hit ratios
   - **Savings**: $30/month
   - **Effort**: Configuration tuning

4. **Serverless Migration**: Move non-critical workloads to Lambda
   - **Savings**: $50/month
   - **Effort**: Architecture refactoring

**Total Long-Term Savings**: $210/month ($2,520/year)

## Total Potential Savings

| Timeframe | Monthly Savings | Annual Savings | New Total Cost |
|-----------|-----------------|----------------|----------------|
| **Current** | - | - | $1,762/month |
| **After Quick Wins** | $355 | $4,260 | $1,407/month |
| **After Medium-Term** | $585 | $7,020 | $1,177/month |
| **After Long-Term** | $795 | $9,540 | $967/month |

**Maximum Annual Savings**: **$9,540 (45% reduction)**

## Cost Monitoring

### Set Up Budget Alerts

```bash
# Create budget with 80% alert
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json

# budget.json:
{
  "BudgetName": "CONTINUUM-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "2000",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}

# notifications.json:
{
  "Notification": {
    "NotificationType": "ACTUAL",
    "ComparisonOperator": "GREATER_THAN",
    "Threshold": 80
  },
  "Subscribers": [{
    "SubscriptionType": "EMAIL",
    "Address": "billing@example.com"
  }]
}
```

### Cost Explorer Tags

Tag all resources for granular cost tracking:

```hcl
tags = {
  Project     = "CONTINUUM"
  Environment = "production"
  Component   = "database"
  CostCenter  = "engineering"
  Owner       = "devops-team"
}
```

### Monthly Review Checklist

- [ ] Review AWS Cost Explorer for unexpected spikes
- [ ] Check CloudWatch metrics for underutilized resources
- [ ] Analyze Trusted Advisor recommendations
- [ ] Review and delete old snapshots/backups
- [ ] Audit Secrets Manager secrets (delete unused)
- [ ] Check for orphaned resources (stopped instances, unattached volumes)
- [ ] Review data transfer costs (optimize VPC endpoints)
- [ ] Analyze CloudWatch logs retention (reduce if possible)

## Enterprise Discount Programs

If spending >$10K/month:

1. **Enterprise Support**: ~10% of monthly bill, but includes TAM and faster response
2. **Private Pricing Agreement**: Negotiate discounts (10-30%) for committed spend
3. **Savings Plans**: Most flexible discount option (up to 72% off on-demand)

## Billing Consolidation

For multiple AWS accounts, use AWS Organizations:

- **Volume Discounts**: Aggregate usage across all environments
- **Centralized Billing**: Single invoice, easier tracking
- **Reserved Instance Sharing**: RIs purchased in one account apply to all

## Conclusion

The CONTINUUM infrastructure is designed for cost-efficiency while maintaining high availability and performance in production.

**Key Takeaways**:

- **Total Cost**: $985 - $1,320/month for all environments
- **Production**: ~75% of total costs (expected for production-first architecture)
- **Optimization Potential**: 45% savings with proper optimization
- **Cost per User**: Scales down significantly with growth ($0.072 → $0.005)

**Recommended Actions**:

1. Purchase reserved instances immediately (40% savings)
2. Implement S3 lifecycle policies
3. Set up cost monitoring and alerts
4. Review costs monthly and rightsize resources
5. Plan for Savings Plans as usage grows

For questions about costs, contact: finance@example.com
