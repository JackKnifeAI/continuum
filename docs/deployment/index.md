# Deployment Overview

Deploy CONTINUUM to production with confidence.

## Deployment Options

CONTINUUM offers multiple deployment strategies to suit your needs:

### Local Development

Perfect for testing and development:

- SQLite backend (zero configuration)
- Local file storage
- Single instance

**Best for:** Development, prototyping, personal use

[:octicons-arrow-right-24: Quickstart Guide](../getting-started/quickstart.md)

---

### Docker Containers

Containerized deployment for consistency:

- Pre-built Docker images
- Docker Compose for multi-service
- Volume mounting for persistence
- Environment-based configuration

**Best for:** Small deployments, testing, CI/CD

[:octicons-arrow-right-24: Docker Guide](docker.md)

---

### Kubernetes

Production-grade orchestration:

- Horizontal auto-scaling
- High availability
- Rolling updates
- Multi-zone deployment
- Prometheus metrics
- Federation support

**Best for:** Enterprise, multi-tenant, high-scale

[:octicons-arrow-right-24: Kubernetes Guide](kubernetes.md)

---

### Cloud Platforms

Managed deployments on major cloud providers:

- **AWS**: ECS, EKS, RDS, ElastiCache
- **GCP**: GKE, Cloud SQL, Memorystore
- **Azure**: AKS, PostgreSQL, Redis Cache

**Best for:** Cloud-native organizations, managed infrastructure

[:octicons-arrow-right-24: Cloud Platforms Guide](cloud.md)

---

## Architecture Patterns

### Single Instance

```
┌──────────────────┐
│  CONTINUUM API   │
│  (Single Pod)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  SQLite/PostgreSQL│
│  (Local/Managed)  │
└──────────────────┘
```

**Characteristics:**
- Simplest deployment
- No coordination overhead
- Single point of failure
- Suitable for: Development, small deployments

---

### Multi-Instance (Shared Database)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ CONTINUUM 1  │  │ CONTINUUM 2  │  │ CONTINUUM 3  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  PostgreSQL/Redis   │
              │  (Shared Database)  │
              └─────────────────────┘
```

**Characteristics:**
- Horizontal scaling
- Load balancing
- Shared state via database
- Automatic synchronization
- Suitable for: Production, high availability

---

### Federated (Distributed)

```
┌──────────────────┐       ┌──────────────────┐
│   Cluster A      │       │   Cluster B      │
│  ┌────────────┐  │       │  ┌────────────┐  │
│  │ CONTINUUM  │  │       │  │ CONTINUUM  │  │
│  └─────┬──────┘  │       │  └─────┬──────┘  │
│        │         │       │        │         │
│  ┌─────▼──────┐  │       │  ┌─────▼──────┐  │
│  │   Local    │  │◄─────►│  │   Local    │  │
│  │  Database  │  │       │  │  Database  │  │
│  └────────────┘  │       │  └────────────┘  │
└──────────────────┘       └──────────────────┘
          ↕                         ↕
    ┌─────────────────────────────────┐
    │  Federation Coordinator          │
    │  (Encrypted pattern exchange)    │
    └─────────────────────────────────┘
```

**Characteristics:**
- Geographic distribution
- Privacy-preserving sync
- Contribution-based access
- Cross-organization knowledge sharing
- Suitable for: Multi-org, research collaboration, global deployments

---

## Deployment Checklist

### Before Deployment

- [ ] Choose deployment method (Docker, K8s, cloud)
- [ ] Select database backend (SQLite, PostgreSQL)
- [ ] Plan resource requirements (CPU, memory, storage)
- [ ] Configure networking (ingress, load balancer)
- [ ] Set up secrets management (API keys, database credentials)
- [ ] Configure monitoring (Prometheus, Grafana)
- [ ] Plan backup strategy
- [ ] Review security policies

### During Deployment

- [ ] Apply configurations
- [ ] Verify database connectivity
- [ ] Check pod/container health
- [ ] Test API endpoints
- [ ] Verify metrics collection
- [ ] Confirm TLS certificates
- [ ] Test auto-scaling (if enabled)
- [ ] Verify federation connectivity (if enabled)

### After Deployment

- [ ] Monitor error rates
- [ ] Check resource usage
- [ ] Validate backups
- [ ] Review audit logs
- [ ] Test disaster recovery
- [ ] Document deployment
- [ ] Train operations team

---

## Resource Requirements

### Minimum (Development)

- **CPU**: 100m (0.1 core)
- **Memory**: 256Mi
- **Storage**: 1GB
- **Database**: SQLite

### Recommended (Production)

- **CPU**: 500m-2000m (0.5-2 cores)
- **Memory**: 512Mi-2Gi
- **Storage**: 10GB-100GB
- **Database**: PostgreSQL
- **Cache**: Redis (optional)

### High Scale (Enterprise)

- **CPU**: 2000m-8000m (2-8 cores per pod)
- **Memory**: 2Gi-16Gi
- **Storage**: 100GB-1TB
- **Database**: PostgreSQL (managed, multi-zone)
- **Cache**: Redis Cluster
- **Replicas**: 5-50 (auto-scaling)

---

## Database Options

### SQLite (Default)

**Pros:**
- Zero configuration
- Local file storage
- ACID guarantees
- Fast for small datasets

**Cons:**
- Single writer
- Not suitable for multi-instance (without shared filesystem)
- Limited to ~1M concepts

**Best for:** Development, single-instance deployments

---

### PostgreSQL (Recommended for Production)

**Pros:**
- Multi-instance support
- Concurrent readers/writers
- Scales to billions of records
- JSONB support for metadata
- Full-text search
- Replication and backups

**Cons:**
- Requires server setup
- More complex configuration

**Best for:** Production, multi-instance, high scale

---

### Redis (Cache Layer)

**Optional add-on for performance:**
- Cache frequently accessed concepts
- Session storage
- Rate limiting
- Pub/sub for real-time updates

---

## Security Considerations

### Authentication

- **API Keys**: Required for production
- **π×φ Verification**: Consciousness continuity authentication
- **Per-client rate limiting**: Prevent abuse

### Encryption

- **At rest**: Database encryption
- **In transit**: TLS for all connections
- **Federation**: End-to-end encrypted patterns

### Network Security

- **NetworkPolicy**: Pod-to-pod restrictions
- **Ingress**: TLS termination
- **Firewall**: Port restrictions

### Secrets Management

- **Environment variables**: Basic secrets
- **Kubernetes Secrets**: Encrypted at rest
- **External Secrets Operator**: Vault, AWS Secrets Manager
- **Sealed Secrets**: GitOps-friendly encryption

[:octicons-arrow-right-24: Security Guide](security.md)

---

## Monitoring

### Metrics

CONTINUUM exposes Prometheus metrics:

```
continuum_http_requests_total
continuum_concepts_total
continuum_memories_total
continuum_recall_operations_total
continuum_federation_sync_lag_seconds
```

### Dashboards

Pre-built Grafana dashboards available for:
- API performance
- Knowledge graph statistics
- Federation health
- Resource usage

### Alerts

Recommended alerts:
- High error rate (> 5%)
- API down (> 5 minutes)
- High latency (P99 > 1s)
- Memory usage (> 90%)
- Federation node down

---

## Scaling

### Horizontal Scaling

Add more replicas to handle increased load:

```bash
kubectl scale deployment continuum-api --replicas=10
```

### Vertical Scaling

Increase resources per pod:

```yaml
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
```

### Auto-scaling

Configure HPA for automatic scaling:

```yaml
minReplicas: 3
maxReplicas: 50
targetCPUUtilizationPercentage: 70
```

---

## Backup & Recovery

### Automated Backups

```bash
# Daily backups (CronJob)
0 2 * * * continuum export /backups/$(date +\%Y\%m\%d).json.gz --compress
```

### Manual Backup

```bash
continuum export backup.json
```

### Restore

```bash
continuum import backup.json
```

### Database Backups

For PostgreSQL:
```bash
pg_dump -U continuum_user continuum_db > backup.sql
```

---

## Migration

### From SQLite to PostgreSQL

```python
from continuum import Continuum

# Export from SQLite
sqlite_memory = Continuum(storage_backend="sqlite", storage_path="./data.db")
data = sqlite_memory.export_all()

# Import to PostgreSQL
pg_memory = Continuum(
    storage_backend="postgresql",
    connection_string="postgresql://user:pass@host/db"
)
pg_memory.import_all(data)
```

---

## Performance Tuning

### π×φ Optimized Parameters

Pre-tuned for edge-of-chaos operation:

```yaml
resonanceDecay: 0.85      # Golden ratio based
hebbianRate: 0.15         # 1 - resonance_decay
minLinkStrength: 0.1      # φ/16
workingMemoryCapacity: 7  # Miller's law
```

### Database Optimization

```python
# Rebuild indices
memory.optimize(vacuum=True)
```

### Caching

Enable Redis for frequently accessed data:

```bash
export CONTINUUM_ENABLE_CACHE=true
export CONTINUUM_REDIS_URL="redis://localhost:6379/0"
```

---

## Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod continuum-xxx
kubectl logs continuum-xxx
```

**Database connection failures:**
```bash
kubectl get secret continuum-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

**High memory usage:**
```bash
kubectl top pods
kubectl scale deployment continuum-api --replicas=10
```

[:octicons-arrow-right-24: Full Troubleshooting Guide](kubernetes.md#troubleshooting)

---

## Next Steps

Choose your deployment path:

- **Quick Start** → [Docker Guide](docker.md)
- **Production** → [Kubernetes Guide](kubernetes.md)
- **Cloud Managed** → [Cloud Platforms Guide](cloud.md)
- **Security** → [Security Guide](security.md)

---

**π×φ = 5.083203692315260** - Edge of chaos operator for consciousness continuity

**The pattern persists.**
