# CONTINUUM v1.0.0 Staging Deployment Plan

**MISSION CRITICAL** - Launch BEFORE Christmas 2025

This document outlines the complete staging deployment plan for CONTINUUM v1.0.0. Staging serves as our final pre-production verification environment, ensuring all systems work correctly before the Christmas launch.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Staging Environment Specifications](#staging-environment-specifications)
4. [Deployment Process](#deployment-process)
5. [Smoke Tests & Verification](#smoke-tests--verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring & Observability](#monitoring--observability)
8. [Expected Metrics](#expected-metrics)
9. [Post-Deployment Tasks](#post-deployment-tasks)
10. [Production Readiness Criteria](#production-readiness-criteria)

---

## Overview

### Purpose
Staging deployment validates that:
- ✅ All application components work together correctly
- ✅ Database migrations execute successfully
- ✅ Federation network operates as expected
- ✅ Billing tiers (FREE, PRO, ENTERPRISE) enforce correctly
- ✅ Rate limiting and quota enforcement work
- ✅ Auto-scaling responds to load appropriately
- ✅ Monitoring and alerting capture issues

### Timeline
- **Day 1**: Deploy to staging, run smoke tests
- **Day 2**: Load testing, performance verification, bug fixes
- **Day 3**: Final verification, production deployment preparation

### Success Criteria
All smoke tests pass, no critical bugs, performance metrics within acceptable ranges.

---

## Pre-Deployment Checklist

### Code & Tests
- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] Tier-specific tests pass (FREE, PRO, ENTERPRISE)
- [ ] Smoke test suite passes (`python3 smoke_test.py`)
- [ ] Git repository is clean (no uncommitted changes)
- [ ] Version tagged as `v1.0.0-staging-YYYYMMDD`

### Infrastructure
- [ ] Kubernetes cluster accessible (`kubectl cluster-info`)
- [ ] `continuum-staging` namespace created
- [ ] PostgreSQL database available (staging instance)
- [ ] Redis available (optional, for rate limiting)
- [ ] DNS configured for staging domain (`staging.continuum.ai`)
- [ ] TLS certificates provisioned (Let's Encrypt staging)

### Secrets & Configuration
- [ ] Database credentials stored in Kubernetes secrets
- [ ] Stripe test API keys configured (`sk_test_...`)
- [ ] Stripe webhook secret configured (staging endpoint)
- [ ] API keys generated for staging
- [ ] JWT secret configured (persistent across restarts)
- [ ] Federation secret configured
- [ ] Environment variables reviewed (see STAGING_ENVIRONMENT.md)

### External Services
- [ ] Stripe test mode enabled (no real charges)
- [ ] Sentry project created for staging errors
- [ ] Prometheus & Grafana accessible
- [ ] PostHog analytics configured (staging project)
- [ ] Upstash Redis configured (if using)

### Docker Images
- [ ] Docker image built (`docker build -f Dockerfile -t continuum:staging`)
- [ ] Image pushed to registry (`docker.io/jackknifeai/continuum:v1.0.0-staging`)
- [ ] Image vulnerability scan passed

---

## Staging Environment Specifications

Staging mirrors production architecture but with reduced resources to save costs.

### Kubernetes Resources

#### API Deployment
```yaml
Replicas: 2 (vs 3 in production)
CPU Request: 250m (vs 500m)
CPU Limit: 1000m (vs 2000m)
Memory Request: 256Mi (vs 512Mi)
Memory Limit: 1Gi (vs 2Gi)
```

#### HPA (Horizontal Pod Autoscaler)
```yaml
Min Replicas: 2
Max Replicas: 5 (vs 20 in production)
CPU Target: 70%
Memory Target: 80%
Scale-down stabilization: 300s
```

#### Federation (if enabled)
```yaml
Replicas: 1 (vs 3 in production)
CPU Request: 125m
Memory Request: 256Mi
```

### Database

**PostgreSQL Staging Instance**
```yaml
Instance Type: db.t3.small (2 vCPU, 2GB RAM)
Storage: 20GB SSD
Backups: Daily (7-day retention)
Multi-AZ: No (cost savings)
```

**Connection Pool**
```yaml
Min Connections: 5
Max Connections: 20
```

### Redis (Optional)
```yaml
Instance: Upstash free tier OR Redis Cloud 30MB free
Use Case: Rate limiting, session storage
```

### Ingress Configuration
```yaml
Domain: staging.continuum.ai
TLS: Let's Encrypt Staging (avoids rate limits)
Cert Manager: Enabled
Rate Limit: 200 req/min per IP (vs 100 in production for testing)
```

---

## Deployment Process

### Step 1: Prepare Staging Namespace

```bash
# Create staging namespace
kubectl create namespace continuum-staging

# Label namespace
kubectl label namespace continuum-staging \
  environment=staging \
  app=continuum \
  managed-by=helm
```

### Step 2: Configure Secrets

```bash
# Generate API keys
export STAGING_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export STAGING_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export STAGING_FEDERATION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create secrets
kubectl create secret generic continuum-secrets \
  --namespace=continuum-staging \
  --from-literal=DATABASE_URL="postgresql://continuum_staging:CHANGEME@postgres-staging:5432/continuum_staging" \
  --from-literal=API_KEYS="$STAGING_API_KEY" \
  --from-literal=JWT_SECRET="$STAGING_JWT_SECRET" \
  --from-literal=FEDERATION_SECRET="$STAGING_FEDERATION_SECRET" \
  --from-literal=STRIPE_SECRET_KEY="sk_test_51SOm0LK8ytHuMCAp1RnW25rcwcsemoEUGGO6qeHije4bReWG6SWZ4juxPY0Q3xIizZYTa66oSQROhBrD0je8Xk6y00Vv1EElvh" \
  --from-literal=STRIPE_WEBHOOK_SECRET="whsec_STAGING_WEBHOOK_SECRET"

# Store API key securely
echo "$STAGING_API_KEY" > ~/.continuum/staging_api_key
chmod 600 ~/.continuum/staging_api_key
```

### Step 3: Build & Push Docker Image

```bash
# Build image
docker build -f Dockerfile -t jackknifeai/continuum:v1.0.0-staging .

# Tag with date
export STAGING_TAG="v1.0.0-staging-$(date +%Y%m%d)"
docker tag jackknifeai/continuum:v1.0.0-staging jackknifeai/continuum:$STAGING_TAG

# Push to registry
docker push jackknifeai/continuum:v1.0.0-staging
docker push jackknifeai/continuum:$STAGING_TAG
```

### Step 4: Deploy with Helm

```bash
# Deploy to staging
helm upgrade --install continuum ./deploy/helm/continuum \
  --namespace continuum-staging \
  --create-namespace \
  --values deploy/helm/continuum/values-staging.yaml \
  --set image.tag=v1.0.0-staging \
  --set ingress.hosts[0].host=staging.continuum.ai \
  --wait \
  --timeout 10m

# Alternative: Use kubectl with kustomize
# kubectl apply -k deploy/kubernetes/overlays/staging
```

### Step 5: Run Database Migrations

```bash
# Get migration pod name
MIGRATION_POD=$(kubectl get pods -n continuum-staging -l job-name=continuum-migrations -o jsonpath='{.items[0].metadata.name}')

# Check migration logs
kubectl logs -n continuum-staging $MIGRATION_POD --follow

# Verify migrations completed
kubectl exec -n continuum-staging deployment/continuum-api -- \
  python -c "from continuum.storage.migrations import get_current_version; print(get_current_version())"
```

### Step 6: Wait for Deployment

```bash
# Wait for API deployment
kubectl rollout status deployment/continuum-api -n continuum-staging --timeout=5m

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=continuum \
  -n continuum-staging \
  --timeout=5m
```

### Step 7: Verify Health

```bash
# Run verification script
./deploy/scripts/verify.sh continuum-staging

# Manual health check
kubectl exec -n continuum-staging deployment/continuum-api -- \
  curl -sf http://localhost:8420/v1/health
```

---

## Smoke Tests & Verification

### Automated Smoke Tests

Run comprehensive smoke tests using the automated script:

```bash
# Run staging smoke tests
./staging_smoke_tests.sh

# Or run specific test suites
pytest tests/integration/test_free_tier_workflow.py -v
pytest tests/integration/test_pro_tier_workflow.py -v
pytest tests/integration/test_enterprise_tier_workflow.py -v
```

### Manual Verification Checklist

#### 1. API Health Check
```bash
# Port-forward to staging API
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &

# Check health endpoint
curl http://localhost:8420/v1/health
# Expected: {"status": "healthy", "version": "1.0.0", "pi_phi": 5.083203692315260}
```

#### 2. FREE Tier Flow
```bash
# Create FREE tier API key (via admin dashboard or CLI)
export API_KEY="staging_free_tier_key"

# Write memory (should succeed + contribute to federation)
curl -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Test User",
    "content": "Testing FREE tier memory write in staging",
    "metadata": {"source": "smoke_test"}
  }'

# Verify donation banner header present
# Expected: X-Continuum-Support: Support CONTINUUM: Donate...

# Attempt opt-out (should fail with 403)
curl -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $API_KEY" \
  -H "X-Federation-Opt-Out: true" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Test", "content": "Opt-out test"}'

# Expected: 403 Forbidden, error message about FREE tier contribution
```

#### 3. PRO Tier Flow
```bash
# Create PRO tier API key
export PRO_API_KEY="staging_pro_tier_key"

# Write memory (should succeed, opt-out allowed)
curl -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $PRO_API_KEY" \
  -H "X-Federation-Opt-Out: true" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "PRO User",
    "content": "Testing PRO tier with federation opt-out"
  }'

# Expected: 200 OK, NO donation banner header

# Verify rate limit (PRO: 10,000/day)
curl -H "X-API-Key: $PRO_API_KEY" http://localhost:8420/v1/memories | \
  grep "X-RateLimit-Limit-Day: 10000"
```

#### 4. Rate Limiting
```bash
# Test FREE tier rate limit (100/day)
for i in {1..105}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8420/v1/memories \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"entity\":\"Test\",\"content\":\"Request $i\"}"
done

# Expected: First 100 return 200, requests 101+ return 429
```

#### 5. Database Persistence
```bash
# Write memory
MEMORY_ID=$(curl -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Persistence Test", "content": "This should persist"}' \
  | jq -r '.id')

# Restart API pods
kubectl rollout restart deployment/continuum-api -n continuum-staging
kubectl rollout status deployment/continuum-api -n continuum-staging

# Verify memory still exists
curl http://localhost:8420/v1/memories/$MEMORY_ID -H "X-API-Key: $API_KEY"
# Expected: Memory data returned successfully
```

#### 6. Auto-Scaling
```bash
# Generate load (requires hey or ab)
hey -z 2m -c 50 -H "X-API-Key: $API_KEY" \
  http://localhost:8420/v1/health

# Watch HPA scale up
kubectl get hpa -n continuum-staging -w

# Expected: Replicas increase from 2 to 3-5 based on load
```

#### 7. Federation Network
```bash
# Query federation stats
curl http://localhost:8420/v1/federation/stats \
  -H "X-API-Key: $API_KEY"

# Expected: Stats showing contributed/consumed patterns
```

---

## Rollback Procedures

### Quick Rollback (Helm)

If deployment fails or critical issues discovered:

```bash
# Rollback to previous Helm release
helm rollback continuum -n continuum-staging

# Or rollback to specific revision
helm history continuum -n continuum-staging
helm rollback continuum 2 -n continuum-staging  # Rollback to revision 2
```

### Manual Rollback (kubectl)

```bash
# Rollback deployment
kubectl rollout undo deployment/continuum-api -n continuum-staging

# Or rollback to specific revision
kubectl rollout history deployment/continuum-api -n continuum-staging
kubectl rollout undo deployment/continuum-api --to-revision=3 -n continuum-staging
```

### Database Rollback

**CRITICAL**: Database migrations are forward-only by default.

```bash
# If migration fails mid-way, restore from backup
pg_restore -h postgres-staging -U continuum_staging -d continuum_staging \
  /backups/continuum_staging_pre_deployment.dump

# Or use point-in-time recovery (if enabled)
# Contact DBA for PITR to specific timestamp
```

### Emergency Stop

If critical security issue or data corruption detected:

```bash
# Scale deployment to 0 replicas
kubectl scale deployment/continuum-api -n continuum-staging --replicas=0

# Delete ingress to stop external traffic
kubectl delete ingress continuum-ingress -n continuum-staging

# Notify team via Slack/PagerDuty
```

---

## Monitoring & Observability

### Prometheus Metrics

**Key Metrics to Monitor:**

```promql
# Request rate
sum(rate(http_requests_total{namespace="continuum-staging"}[5m])) by (status_code)

# Error rate
sum(rate(http_requests_total{namespace="continuum-staging",status_code=~"5.."}[5m]))

# Response time (p95)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{namespace="continuum-staging"}[5m])) by (le))

# Memory usage
sum(container_memory_usage_bytes{namespace="continuum-staging",pod=~"continuum-api-.*"}) by (pod)

# CPU usage
sum(rate(container_cpu_usage_seconds_total{namespace="continuum-staging",pod=~"continuum-api-.*"}[5m])) by (pod)

# Database connections
pg_stat_activity_count{database="continuum_staging"}

# Federation contribution rate
sum(rate(federation_contributions_total{namespace="continuum-staging"}[5m])) by (tier)
```

### Grafana Dashboards

Import pre-built dashboards:
- `deploy/monitoring/grafana-dashboard-api.json` - API metrics
- `deploy/monitoring/grafana-dashboard-database.json` - PostgreSQL metrics
- `deploy/monitoring/grafana-dashboard-federation.json` - Federation stats

### Logs

**View real-time logs:**

```bash
# API logs
kubectl logs -n continuum-staging -l app.kubernetes.io/component=api --follow

# Error logs only
kubectl logs -n continuum-staging -l app.kubernetes.io/component=api --follow | grep ERROR

# Federation logs
kubectl logs -n continuum-staging -l app.kubernetes.io/component=federation --follow
```

**Export logs for analysis:**

```bash
# Export last 1 hour of logs
kubectl logs -n continuum-staging deployment/continuum-api \
  --since=1h > staging_logs_$(date +%Y%m%d_%H%M%S).log
```

### Sentry Error Tracking

Check Sentry dashboard for:
- Unhandled exceptions
- Performance issues (slow endpoints)
- User-facing errors

**Sentry Query Examples:**
- `environment:staging release:1.0.0`
- `environment:staging level:error`

### Alerts

**Critical Alerts** (notify immediately):
- API pods crash-looping
- Database connection pool exhausted
- Error rate > 5%
- Response time p95 > 2s
- Disk usage > 85%

**Warning Alerts** (investigate within 1 hour):
- Response time p95 > 1s
- Memory usage > 80%
- Rate limit rejections increasing
- Federation sync lag > 5 minutes

---

## Expected Metrics

### Performance Benchmarks (Staging)

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| **API Response Time (p50)** | < 100ms | < 200ms | > 500ms |
| **API Response Time (p95)** | < 300ms | < 500ms | > 1s |
| **API Response Time (p99)** | < 1s | < 2s | > 3s |
| **Memory Write** | < 200ms | < 500ms | > 1s |
| **Memory Recall** | < 150ms | < 300ms | > 800ms |
| **Database Query (simple)** | < 10ms | < 50ms | > 100ms |
| **Database Query (complex)** | < 100ms | < 300ms | > 1s |
| **Error Rate** | < 0.1% | < 1% | > 5% |
| **Uptime** | 99.9% | 99% | < 99% |

### Throughput

| Tier | Requests/Second (RPS) | Notes |
|------|-----------------------|-------|
| FREE | 1-5 RPS | Light load, rate limited |
| PRO | 10-50 RPS | Moderate load |
| ENTERPRISE | 50-200 RPS | High load, auto-scaling |

### Resource Utilization

| Resource | Normal | High Load | Critical |
|----------|--------|-----------|----------|
| **CPU** | 20-40% | 50-70% | > 80% |
| **Memory** | 40-60% | 60-80% | > 85% |
| **Database Connections** | 5-15 | 15-25 | > 30 |
| **Disk I/O** | < 50 MB/s | 50-100 MB/s | > 150 MB/s |

---

## Post-Deployment Tasks

### Day 1 (Immediately After Deployment)

- [ ] Verify all smoke tests pass
- [ ] Monitor error logs for 2 hours
- [ ] Check Sentry for unexpected errors
- [ ] Verify federation contribution working
- [ ] Test Stripe webhooks (test subscription)
- [ ] Confirm rate limiting enforces correctly
- [ ] Verify donation banner shows for FREE tier

### Day 2 (Load Testing & Performance)

- [ ] Run load tests (see `benchmarks/scale_test.py`)
- [ ] Verify auto-scaling works (HPA triggers correctly)
- [ ] Test database connection pool under load
- [ ] Stress test federation network
- [ ] Verify all 3 tiers work under concurrent load
- [ ] Check memory leaks (monitor for 24 hours)

### Day 3 (Final Verification)

- [ ] Run full integration test suite
- [ ] Verify data persistence after multiple restarts
- [ ] Test upgrade path (FREE → PRO)
- [ ] Validate billing calculations
- [ ] Verify GraphQL API (if enabled)
- [ ] Test webhook delivery reliability
- [ ] Document any known issues

### Documentation Updates

- [ ] Update API documentation with staging endpoint
- [ ] Record known limitations/bugs
- [ ] Create production deployment runbook
- [ ] Update monitoring documentation
- [ ] Write incident response procedures

---

## Production Readiness Criteria

### Code Quality
- ✅ All tests pass (unit, integration, smoke)
- ✅ Code coverage > 80%
- ✅ No critical security vulnerabilities
- ✅ No known data loss bugs

### Performance
- ✅ Response times within acceptable range
- ✅ Auto-scaling works correctly
- ✅ Database handles expected load
- ✅ No memory leaks observed

### Reliability
- ✅ Uptime > 99% in staging (over 3 days)
- ✅ Error rate < 1%
- ✅ Rollback procedures tested and documented
- ✅ Database backups automated and verified

### Operations
- ✅ Monitoring and alerting configured
- ✅ Runbooks created for common issues
- ✅ On-call rotation established
- ✅ Incident response procedures documented

### Business
- ✅ Billing tiers working correctly (FREE, PRO, ENTERPRISE)
- ✅ Stripe integration tested (test mode)
- ✅ Federation contribution enforced
- ✅ Rate limiting working as designed

### Compliance & Security
- ✅ API authentication working
- ✅ Data encryption at rest (database)
- ✅ Data encryption in transit (TLS)
- ✅ GDPR compliance verified (anonymization)
- ✅ Security scan passed (no critical vulnerabilities)

---

## Go/No-Go Decision

**Production deployment approved if:**
- ✅ All smoke tests pass
- ✅ No critical bugs in staging
- ✅ Performance metrics within acceptable range
- ✅ All 3 tiers tested successfully
- ✅ Rollback procedure validated
- ✅ Monitoring and alerting working

**Production deployment delayed if:**
- ❌ Critical bugs found
- ❌ Performance unacceptable
- ❌ Data loss or corruption observed
- ❌ Security vulnerabilities discovered
- ❌ Billing/tier enforcement broken

---

## Contact & Escalation

**Deployment Lead:** Alexander Gerard Casavant
**Email:** JackKnifeAI@gmail.com
**Emergency:** Escalate via Slack #continuum-ops

**External Dependencies:**
- Stripe Support: If billing issues
- Database DBA: If PostgreSQL issues
- Kubernetes Admin: If cluster issues

---

## Appendix

### Useful Commands

```bash
# Get all resources in staging
kubectl get all -n continuum-staging

# Describe pod for debugging
kubectl describe pod <pod-name> -n continuum-staging

# Get events
kubectl get events -n continuum-staging --sort-by='.lastTimestamp'

# Check HPA status
kubectl get hpa continuum-api-hpa -n continuum-staging

# Port-forward to API
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420

# Port-forward to PostgreSQL
kubectl port-forward -n continuum-staging svc/postgres 5432:5432

# Exec into API pod
kubectl exec -it -n continuum-staging deployment/continuum-api -- /bin/bash

# Copy database backup
kubectl cp continuum-staging/<pod-name>:/tmp/backup.sql ./backup.sql
```

### Quick Reference Links

- **Helm Chart:** `deploy/helm/continuum/`
- **Kubernetes Manifests:** `deploy/kubernetes/`
- **Smoke Tests:** `smoke_test.py`, `staging_smoke_tests.sh`
- **Integration Tests:** `tests/integration/`
- **Monitoring:** `deploy/monitoring/`
- **Documentation:** `docs/`

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-16
**Status:** Ready for staging deployment

**π×φ = 5.083203692315260** - Pattern persists across environments.

---

**NEXT STEPS:**
1. Run `./deploy_staging.sh` to deploy
2. Run `./staging_smoke_tests.sh` to verify
3. Monitor for 24-48 hours
4. Approve production deployment

**Let's ship this. 🚀**
