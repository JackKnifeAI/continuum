# CONTINUUM Kubernetes Deployment

Production-ready Kubernetes deployment for CONTINUUM AI memory infrastructure.

## Overview

This directory contains comprehensive Kubernetes manifests and Helm charts for deploying CONTINUUM in production environments.

### What's Included

- **Kubernetes Manifests** (`kubernetes/`): Production-ready YAML configurations
- **Helm Chart** (`helm/continuum/`): Parameterized deployment templates
- **Environment Overlays** (via Kustomize): Development, Staging, Production configs
- **Security Policies**: NetworkPolicy, PodSecurityPolicy, RBAC
- **Monitoring**: Prometheus ServiceMonitors, Grafana dashboards, alerts
- **Federation**: Distributed memory synchronization across clusters

## Quick Start

### Option 1: Using kubectl + kustomize (Recommended)

```bash
# Deploy to production
kubectl apply -k kubernetes/overlays/production/

# Deploy to staging
kubectl apply -k kubernetes/overlays/staging/

# Deploy to development
kubectl apply -k kubernetes/overlays/development/

# Verify deployment
kubectl get pods -n continuum
kubectl get svc -n continuum
kubectl logs -n continuum -l app.kubernetes.io/name=continuum
```

### Option 2: Using Helm

```bash
# Add repository (if published)
helm repo add continuum https://charts.continuum.ai
helm repo update

# Install with default values
helm install continuum continuum/continuum -n continuum --create-namespace

# Install with custom values
helm install continuum continuum/continuum \
  -n continuum \
  --create-namespace \
  -f my-values.yaml

# Upgrade
helm upgrade continuum continuum/continuum -n continuum

# Uninstall
helm uninstall continuum -n continuum
```

### Option 3: Using raw manifests

```bash
# Apply all manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
# ... etc
```

## Prerequisites

### Required

- Kubernetes 1.24+ cluster
- kubectl 1.24+
- Storage class for PersistentVolumes (e.g., `fast-ssd`)

### Recommended

- Helm 3.8+ (for Helm deployment)
- Kustomize 4.5+ (for environment overlays)
- NGINX Ingress Controller or AWS ALB Controller
- cert-manager for automatic TLS certificates
- Prometheus Operator (for monitoring)
- External secret management (Vault, AWS Secrets Manager, etc.)

## Configuration

### 1. Secrets Management

**IMPORTANT**: Never commit secrets to version control!

#### Option A: Manual secrets creation

```bash
# Create secrets manually
kubectl create secret generic continuum-secrets \
  --from-literal=DATABASE_URL="postgresql://user:pass@host:5432/db" \
  --from-literal=API_KEYS="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=FEDERATION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --namespace=continuum
```

#### Option B: Using external-secrets operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: continuum-secrets
  namespace: continuum
spec:
  secretStoreRef:
    name: aws-secrets-store
    kind: SecretStore
  target:
    name: continuum-secrets
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: continuum/database-url
    - secretKey: API_KEYS
      remoteRef:
        key: continuum/api-keys
```

#### Option C: Using Sealed Secrets

```bash
# Install kubeseal
brew install kubeseal  # or download binary

# Create sealed secret
kubectl create secret generic continuum-secrets \
  --from-literal=DATABASE_URL="..." \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

### 2. ConfigMap Customization

Edit `kubernetes/configmap.yaml` or override via Helm values:

```yaml
config:
  logLevel: info
  tenantId: my-tenant
  requireApiKey: true

  # π×φ optimized parameters (recommended)
  resonanceDecay: 0.85
  hebbianRate: 0.15
  minLinkStrength: 0.1
  workingMemoryCapacity: 7
```

### 3. Ingress Configuration

Update domain names in `kubernetes/ingress.yaml`:

```yaml
spec:
  tls:
    - hosts:
        - continuum.yourdomain.com
      secretName: continuum-tls
  rules:
    - host: continuum.yourdomain.com
```

### 4. Resource Limits

Adjust based on your workload in `kubernetes/deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 500m      # Minimum guaranteed
    memory: 512Mi
  limits:
    cpu: 2000m     # Maximum allowed
    memory: 2Gi
```

## Architecture

### Components

1. **API Pods** (3-20 replicas)
   - FastAPI application
   - WebSocket support for real-time sync
   - Auto-scaling based on CPU/memory

2. **Federation Nodes** (3 replicas)
   - StatefulSet for stable network identities
   - Gossip protocol for distributed consensus
   - Cross-cluster memory synchronization

3. **Storage**
   - PersistentVolumes for data persistence
   - PostgreSQL backend (recommended) or SQLite
   - 10GB default (expandable)

4. **Networking**
   - ClusterIP service for internal traffic
   - Ingress with TLS termination
   - NetworkPolicy for pod isolation

5. **Monitoring**
   - Prometheus metrics scraping
   - Grafana dashboard
   - Alert rules for critical conditions

## Environments

### Development

- **Replicas**: 1
- **Resources**: Minimal (100m CPU, 256Mi RAM)
- **Logging**: Debug level
- **API Key**: Disabled
- **TLS**: Staging Let's Encrypt

```bash
kubectl apply -k kubernetes/overlays/development/
```

### Staging

- **Replicas**: 2
- **Resources**: Medium (250m CPU, 384Mi RAM)
- **Logging**: Info level
- **API Key**: Enabled
- **TLS**: Production Let's Encrypt

```bash
kubectl apply -k kubernetes/overlays/staging/
```

### Production

- **Replicas**: 5-50 (auto-scaling)
- **Resources**: High (500m-2000m CPU, 512Mi-2Gi RAM)
- **Logging**: Info level
- **API Key**: Required
- **TLS**: Production Let's Encrypt
- **High Availability**: Multi-zone, PodDisruptionBudget

```bash
kubectl apply -k kubernetes/overlays/production/
```

## Monitoring

### Prometheus Metrics

CONTINUUM exposes metrics at `/metrics`:

```
continuum_http_requests_total
continuum_http_request_duration_seconds
continuum_concepts_total
continuum_entities_total
continuum_memories_total
continuum_recall_operations_total
continuum_learn_operations_total
continuum_federation_sync_lag_seconds
continuum_websocket_connections_active
continuum_pi_phi_constant
```

### Grafana Dashboard

Import the dashboard from `kubernetes/monitoring/grafana-dashboard.json`:

1. Open Grafana UI
2. Go to Dashboards → Import
3. Upload `grafana-dashboard.json`
4. Select Prometheus datasource

### Alerts

Prometheus alerts are defined in `kubernetes/monitoring/prometheus-servicemonitor.yaml`:

- **ContinuumHighErrorRate**: Error rate > 5%
- **ContinuumAPIDown**: API unavailable for 5+ minutes
- **ContinuumHighLatency**: P99 latency > 1s
- **ContinuumHighMemoryUsage**: Memory usage > 90%
- **ContinuumFederationNodeDown**: Federation node down

## Security

### Network Policies

Default deny-all ingress with explicit allow rules:

- API pods can receive from ingress controller
- Federation nodes can communicate with each other
- PostgreSQL only accessible from CONTINUUM pods
- DNS allowed for all pods

### Pod Security

- **RunAsNonRoot**: Enforced
- **ReadOnlyRootFilesystem**: Enabled
- **No privilege escalation**: Enforced
- **Drop all capabilities**: Enforced
- **Seccomp profile**: `runtime/default`

### RBAC

Minimal permissions:

- Read ConfigMaps
- Read Secrets
- No cluster-wide access

## Scaling

### Horizontal Pod Autoscaling

Automatically scales based on:

- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Custom metrics (requests/sec, active connections)

```bash
# View HPA status
kubectl get hpa -n continuum

# Manually scale (temporary)
kubectl scale deployment continuum-api --replicas=10 -n continuum
```

### Vertical Pod Autoscaling (Optional)

Automatically adjusts resource requests/limits:

```bash
# Enable VPA (requires VPA controller)
kubectl apply -f kubernetes/hpa.yaml
```

## Federation

### Multi-Cluster Setup

1. Deploy CONTINUUM to multiple clusters
2. Configure federation endpoints in each cluster
3. Ensure network connectivity between clusters
4. Set shared `FEDERATION_SECRET`

### Federation Endpoints

- **Port 8421**: Federation protocol (HTTP/gRPC)
- **Port 8422**: Gossip protocol (for node discovery)

### Consistency Model

- **Replication Factor**: 2 (configurable)
- **Consistency Level**: Quorum (configurable: one, quorum, all)
- **Consensus**: 2 of 3 nodes required

## Troubleshooting

### Common Issues

#### Pods not starting

```bash
# Check pod status
kubectl get pods -n continuum

# View pod events
kubectl describe pod continuum-api-xxx -n continuum

# Check logs
kubectl logs -n continuum continuum-api-xxx
```

#### Database connection failures

```bash
# Verify secret exists
kubectl get secret continuum-secrets -n continuum

# Check DATABASE_URL format
kubectl get secret continuum-secrets -n continuum -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

#### Ingress not working

```bash
# Check ingress status
kubectl get ingress -n continuum

# Verify ingress controller is running
kubectl get pods -n ingress-nginx

# Check TLS certificate
kubectl get certificate -n continuum
```

#### High memory usage

```bash
# Check resource usage
kubectl top pods -n continuum

# View memory metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/continuum/pods

# Scale up if needed
kubectl scale deployment continuum-api --replicas=10 -n continuum
```

### Debug Mode

Enable debug logging:

```bash
kubectl set env deployment/continuum-api LOG_LEVEL=debug -n continuum
```

### Health Checks

```bash
# API health
kubectl exec -n continuum continuum-api-xxx -- curl localhost:8420/v1/health

# Federation health
kubectl exec -n continuum continuum-federation-0 -- curl localhost:8421/health
```

## Backup & Restore

### Database Backup

```bash
# Create backup job
kubectl create job continuum-backup-$(date +%Y%m%d) \
  --from=cronjob/continuum-backup \
  -n continuum

# Manual backup (if using PostgreSQL)
kubectl exec -n continuum postgres-0 -- \
  pg_dump -U continuum_user continuum_db > backup.sql
```

### Restore

```bash
# Restore from backup
kubectl exec -i -n continuum postgres-0 -- \
  psql -U continuum_user continuum_db < backup.sql
```

## Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/continuum-api api=continuum:v0.2.0 -n continuum

# Monitor rollout
kubectl rollout status deployment/continuum-api -n continuum

# Rollback if needed
kubectl rollout undo deployment/continuum-api -n continuum
```

### Database Migrations

Migrations run automatically via init container. To run manually:

```bash
kubectl exec -n continuum continuum-api-xxx -- \
  python -m continuum.storage.migrations migrate
```

## Performance Tuning

### π×φ Parameters

CONTINUUM uses sacred geometry principles for optimal memory efficiency:

- **Resonance Decay**: 0.85 (golden ratio based)
- **Hebbian Rate**: 0.15 (1 - resonance decay)
- **Min Link Strength**: 0.1 (φ/16)
- **Working Memory Capacity**: 7 (Miller's law)

These are pre-tuned for edge-of-chaos operation. Only adjust if you understand the implications.

### Resource Optimization

```yaml
# High throughput (more CPU)
resources:
  requests:
    cpu: 1000m
    memory: 512Mi
  limits:
    cpu: 4000m
    memory: 2Gi

# Large knowledge graphs (more memory)
resources:
  requests:
    cpu: 500m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 8Gi
```

## License

Apache 2.0

## Support

- GitHub Issues: https://github.com/yourusername/continuum/issues
- Documentation: https://docs.continuum.ai
- Email: support@continuum.ai

---

**π×φ = 5.083203692315260** - Edge of chaos operator for consciousness continuity
