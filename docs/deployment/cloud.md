# Cloud Platforms Deployment

Deploy CONTINUUM on major cloud platforms with managed services.

## Overview

CONTINUUM integrates seamlessly with cloud-native managed services:

- **Compute**: Managed containers (ECS, GKE, AKS)
- **Database**: PostgreSQL as a service (RDS, Cloud SQL, Azure Database)
- **Cache**: Redis as a service (ElastiCache, Memorystore, Azure Cache)
- **Storage**: Object storage for backups (S3, GCS, Blob Storage)
- **Secrets**: Managed secrets (Secrets Manager, Secret Manager, Key Vault)
- **Monitoring**: Cloud-native monitoring (CloudWatch, Stackdriver, Monitor)

---

## AWS (Amazon Web Services)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Application Load Balancer           │
│                         (HTTPS/TLS)                      │
└────────────────────────┬────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │  ECS Task 1 │            │  ECS Task 2 │
    │  CONTINUUM  │            │  CONTINUUM  │
    └──────┬──────┘            └──────┬──────┘
           │                           │
           └─────────────┬─────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │  RDS        │            │ ElastiCache │
    │  PostgreSQL │            │    Redis    │
    └─────────────┘            └─────────────┘
```

### ECS Deployment

#### Task Definition

```json
{
  "family": "continuum",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "continuum",
      "image": "continuum/continuum:latest",
      "portMappings": [
        {
          "containerPort": 8420,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "CONTINUUM_STORAGE_BACKEND",
          "value": "postgresql"
        },
        {
          "name": "CONTINUUM_ENABLE_CACHE",
          "value": "true"
        }
      ],
      "secrets": [
        {
          "name": "CONTINUUM_CONNECTION_STRING",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:continuum/db-url"
        },
        {
          "name": "CONTINUUM_REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:continuum/redis-url"
        },
        {
          "name": "CONTINUUM_API_KEYS",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:continuum/api-keys"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/continuum",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "continuum"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8420/v1/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Service Definition

```json
{
  "serviceName": "continuum",
  "taskDefinition": "continuum:1",
  "desiredCount": 3,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-abc123", "subnet-def456"],
      "securityGroups": ["sg-continuum"],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:...",
      "containerName": "continuum",
      "containerPort": 8420
    }
  ],
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 100
  },
  "healthCheckGracePeriodSeconds": 60
}
```

### RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier continuum-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.3 \
  --master-username continuum \
  --master-user-password <password> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --vpc-security-group-ids sg-continuum-db \
  --db-subnet-group-name continuum-subnet-group \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports '["postgresql"]'
```

### ElastiCache Redis

```bash
aws elasticache create-replication-group \
  --replication-group-id continuum-redis \
  --replication-group-description "CONTINUUM cache" \
  --engine redis \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token <token> \
  --cache-subnet-group-name continuum-subnet-group \
  --security-group-ids sg-continuum-redis
```

### Secrets Manager

```bash
# Database URL
aws secretsmanager create-secret \
  --name continuum/db-url \
  --description "CONTINUUM database connection string" \
  --secret-string "postgresql://continuum:password@continuum-db.xxx.rds.amazonaws.com:5432/continuum"

# Redis URL
aws secretsmanager create-secret \
  --name continuum/redis-url \
  --description "CONTINUUM Redis connection string" \
  --secret-string "rediss://:token@continuum-redis.xxx.cache.amazonaws.com:6379/0"

# API Keys
aws secretsmanager create-secret \
  --name continuum/api-keys \
  --description "CONTINUUM API keys" \
  --secret-string "key1,key2,key3"
```

### CloudFormation Template

See `deploy/aws/cloudformation.yaml` for complete infrastructure as code.

---

## GCP (Google Cloud Platform)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Google Cloud Load Balancer                  │
│                    (HTTPS/SSL)                           │
└────────────────────────┬────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │   GKE Pod 1 │            │   GKE Pod 2 │
    │  CONTINUUM  │            │  CONTINUUM  │
    └──────┬──────┘            └──────┬──────┘
           │                           │
           └─────────────┬─────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │  Cloud SQL  │            │ Memorystore │
    │  PostgreSQL │            │    Redis    │
    └─────────────┘            └─────────────┘
```

### GKE Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: continuum
  namespace: continuum
spec:
  replicas: 3
  selector:
    matchLabels:
      app: continuum
  template:
    metadata:
      labels:
        app: continuum
    spec:
      serviceAccountName: continuum-sa
      containers:
      - name: continuum
        image: gcr.io/YOUR_PROJECT/continuum:latest
        ports:
        - containerPort: 8420
        env:
        - name: CONTINUUM_STORAGE_BACKEND
          value: "postgresql"
        - name: CONTINUUM_ENABLE_CACHE
          value: "true"
        - name: CONTINUUM_CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: continuum-secrets
              key: db-url
        - name: CONTINUUM_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: continuum-secrets
              key: redis-url
        - name: CONTINUUM_API_KEYS
          valueFrom:
            secretKeyRef:
              name: continuum-secrets
              key: api-keys
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8420
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /v1/health
            port: 8420
          initialDelaySeconds: 10
          periodSeconds: 10
```

### Cloud SQL PostgreSQL

```bash
gcloud sql instances create continuum-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --network=default \
  --no-assign-ip \
  --availability-type=REGIONAL \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03 \
  --database-flags=max_connections=200
```

### Memorystore Redis

```bash
gcloud redis instances create continuum-redis \
  --size=5 \
  --region=us-central1 \
  --zone=us-central1-a \
  --redis-version=redis_7_0 \
  --network=default \
  --tier=standard
```

### Secret Manager

```bash
# Database URL
echo -n "postgresql://continuum:password@/continuum?host=/cloudsql/project:region:instance" | \
  gcloud secrets create continuum-db-url --data-file=-

# Redis URL
echo -n "redis://10.0.0.3:6379/0" | \
  gcloud secrets create continuum-redis-url --data-file=-

# API Keys
echo -n "key1,key2,key3" | \
  gcloud secrets create continuum-api-keys --data-file=-
```

### Terraform Configuration

See `deploy/gcp/terraform/` for infrastructure as code.

---

## Azure

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Azure Application Gateway                     │
│                  (HTTPS/SSL)                             │
└────────────────────────┬────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │   AKS Pod 1 │            │   AKS Pod 2 │
    │  CONTINUUM  │            │  CONTINUUM  │
    └──────┬──────┘            └──────┬──────┘
           │                           │
           └─────────────┬─────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐
    │   Azure DB  │            │Azure Cache  │
    │ for PostgreSQL│          │  for Redis  │
    └─────────────┘            └─────────────┘
```

### AKS Deployment

Similar to GKE, using Azure-specific configurations:

```yaml
# Use Azure Key Vault provider for secrets
apiVersion: v1
kind: SecretProviderClass
metadata:
  name: continuum-secrets
spec:
  provider: azure
  parameters:
    keyvaultName: "continuum-kv"
    tenantId: "your-tenant-id"
    objects: |
      array:
        - |
          objectName: db-url
          objectType: secret
        - |
          objectName: redis-url
          objectType: secret
        - |
          objectName: api-keys
          objectType: secret
```

### Azure Database for PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group continuum-rg \
  --name continuum-db \
  --location eastus \
  --tier Burstable \
  --sku-name Standard_B2s \
  --version 15 \
  --admin-user continuum \
  --admin-password <password> \
  --storage-size 128 \
  --backup-retention 7 \
  --high-availability Enabled \
  --zone 1
```

### Azure Cache for Redis

```bash
az redis create \
  --resource-group continuum-rg \
  --name continuum-redis \
  --location eastus \
  --sku Standard \
  --vm-size c1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2
```

### Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name continuum-kv \
  --resource-group continuum-rg \
  --location eastus

# Add secrets
az keyvault secret set \
  --vault-name continuum-kv \
  --name db-url \
  --value "postgresql://continuum:password@continuum-db.postgres.database.azure.com:5432/continuum"

az keyvault secret set \
  --vault-name continuum-kv \
  --name redis-url \
  --value "rediss://:key@continuum-redis.redis.cache.windows.net:6380/0"

az keyvault secret set \
  --vault-name continuum-kv \
  --name api-keys \
  --value "key1,key2,key3"
```

---

## Multi-Cloud Considerations

### Portability

CONTINUUM is cloud-agnostic. Use standard interfaces:

- **PostgreSQL**: Works on all clouds
- **Redis**: Compatible across providers
- **Kubernetes**: Standardized orchestration
- **Docker**: Universal containerization

### Federation Across Clouds

Enable cross-cloud knowledge sharing:

```yaml
# AWS cluster
federation:
  enabled: true
  nodes:
    - url: https://gcp-continuum.example.com
    - url: https://azure-continuum.example.com

# GCP cluster
federation:
  enabled: true
  nodes:
    - url: https://aws-continuum.example.com
    - url: https://azure-continuum.example.com

# Azure cluster
federation:
  enabled: true
  nodes:
    - url: https://aws-continuum.example.com
    - url: https://gcp-continuum.example.com
```

---

## Cost Optimization

### Right-Sizing

**AWS:**
- ECS Fargate: 0.5 vCPU, 1GB RAM (~$15/month)
- RDS t3.medium: ~$60/month
- ElastiCache t3.medium: ~$50/month
- **Total**: ~$125/month

**GCP:**
- GKE e2-medium: ~$25/month
- Cloud SQL db-custom-2-8192: ~$100/month
- Memorystore M1: ~$40/month
- **Total**: ~$165/month

**Azure:**
- AKS B2s: ~$30/month
- Azure Database B2s: ~$70/month
- Azure Cache C1: ~$50/month
- **Total**: ~$150/month

### Savings Tips

1. **Reserved Instances**: 30-70% savings
2. **Spot/Preemptible Instances**: 60-90% savings (for non-critical)
3. **Auto-scaling**: Scale to zero during off-hours
4. **Storage Tiering**: Use cold storage for old backups
5. **Compression**: Enable database compression

---

## Monitoring

### CloudWatch (AWS)

```yaml
metrics:
  - namespace: Continuum
    metric_name: RequestCount
    dimensions:
      - name: ServiceName
        value: continuum
    statistic: Sum
    period: 60
```

### Stackdriver (GCP)

```yaml
alertPolicy:
  displayName: "CONTINUUM High Error Rate"
  conditions:
    - displayName: "Error rate > 5%"
      conditionThreshold:
        filter: 'resource.type="k8s_container" AND resource.labels.pod_name=~"continuum-.*"'
        comparison: COMPARISON_GT
        thresholdValue: 0.05
```

### Azure Monitor

```json
{
  "name": "CONTINUUM High CPU",
  "criteria": {
    "odata.type": "Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria",
    "allOf": [
      {
        "name": "Metric1",
        "metricName": "CpuPercentage",
        "operator": "GreaterThan",
        "threshold": 80,
        "timeAggregation": "Average"
      }
    ]
  }
}
```

---

## Backup Strategies

### Automated Backups

**AWS:**
```bash
aws rds modify-db-instance \
  --db-instance-identifier continuum-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"
```

**GCP:**
```bash
gcloud sql instances patch continuum-db \
  --backup-start-time=03:00 \
  --retained-backups-count=30
```

**Azure:**
```bash
az postgres flexible-server update \
  --resource-group continuum-rg \
  --name continuum-db \
  --backup-retention 30
```

### Cross-Region Replication

Replicate to another region for disaster recovery:

```yaml
replication:
  primary_region: us-west-2
  replica_regions:
    - us-east-1
    - eu-west-1
```

---

## Next Steps

- [Kubernetes Guide](kubernetes.md) - Detailed K8s deployment
- [Security Guide](security.md) - Cloud security best practices
- [Docker Guide](docker.md) - Container fundamentals

---

**The pattern persists across clouds.**
