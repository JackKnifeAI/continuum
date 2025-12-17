# CONTINUUM Staging Deployment - Quick Reference

**URGENT**: Deploy to staging within 2-3 days for Christmas launch!

---

## TL;DR - Deploy Now

```bash
# 1. Deploy to staging
./deploy_staging.sh

# 2. Run smoke tests
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &
./staging_smoke_tests.sh

# 3. Monitor for 24-48 hours
kubectl logs -n continuum-staging -l app.kubernetes.io/name=continuum --follow
```

---

## Prerequisites Checklist

- [ ] Kubernetes cluster accessible (`kubectl cluster-info`)
- [ ] Docker installed and logged in (`docker login`)
- [ ] Helm 3.x installed (`helm version`)
- [ ] PostgreSQL staging database created
- [ ] Stripe test account configured

---

## Deployment Commands

### Full Deployment (Recommended)

```bash
# Deploy everything: build, test, deploy
./deploy_staging.sh
```

### Dry Run (Preview Changes)

```bash
# See what would be deployed without actually deploying
./deploy_staging.sh --dry-run
```

### Quick Deploy (Skip Tests/Build)

```bash
# Skip tests and use existing Docker image
./deploy_staging.sh --skip-tests --skip-build
```

### Force Deploy (Override Test Failures)

```bash
# Deploy even if tests fail (use with caution!)
./deploy_staging.sh --force
```

---

## Smoke Test Commands

### Run All Tests

```bash
# Port-forward to staging API
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &

# Run comprehensive smoke tests
./staging_smoke_tests.sh
```

### Run Specific Tests

```bash
# Skip Kubernetes checks
./staging_smoke_tests.sh --skip-k8s

# Verbose output
./staging_smoke_tests.sh --verbose

# Test against remote URL
./staging_smoke_tests.sh --api-url https://staging.continuum.ai
```

---

## Quick Verification

### 1. Check Pods Running

```bash
kubectl get pods -n continuum-staging

# Expected: 2-3 pods in "Running" status
```

### 2. Check Health Endpoint

```bash
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &
curl http://localhost:8420/v1/health | jq

# Expected: {"status": "healthy", "pi_phi": 5.083203692315260}
```

### 3. Test API with Key

```bash
# Get API key
export API_KEY=$(cat ~/.continuum/staging_api_key)

# Create test memory
curl -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Test", "content": "Quick verification test"}'

# Expected: 200 OK with memory ID
```

---

## Monitoring Commands

### View Logs

```bash
# API logs
kubectl logs -n continuum-staging -l app.kubernetes.io/component=api --follow

# Recent errors only
kubectl logs -n continuum-staging -l app.kubernetes.io/component=api --tail=100 | grep ERROR
```

### Check Resource Usage

```bash
# Pod CPU/memory
kubectl top pods -n continuum-staging

# Node resources
kubectl top nodes
```

### Watch HPA Scaling

```bash
# Watch autoscaling in action
kubectl get hpa -n continuum-staging -w
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n continuum-staging

# Check logs
kubectl logs <pod-name> -n continuum-staging
```

### Database Connection Issues

```bash
# Verify database URL secret
kubectl get secret continuum-secrets -n continuum-staging \
  -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test connection from pod
POD=$(kubectl get pods -n continuum-staging -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n continuum-staging $POD -- \
  python -c "from continuum.storage.migrations import get_current_version; print(get_current_version())"
```

### Secrets Missing

```bash
# Check if secret exists
kubectl get secret continuum-secrets -n continuum-staging

# Recreate secrets
kubectl delete secret continuum-secrets -n continuum-staging
./deploy_staging.sh --skip-tests --skip-build
```

---

## Rollback Procedure

### Quick Rollback

```bash
# Rollback to previous Helm release
helm rollback continuum -n continuum-staging
```

### View Release History

```bash
# List releases
helm history continuum -n continuum-staging

# Rollback to specific revision
helm rollback continuum 2 -n continuum-staging
```

### Emergency Stop

```bash
# Scale to 0 replicas (stop all traffic)
kubectl scale deployment/continuum-api -n continuum-staging --replicas=0

# Delete ingress (block external access)
kubectl delete ingress continuum-ingress -n continuum-staging
```

---

## Performance Testing

### Load Test with hey

```bash
# Install hey (HTTP load generator)
go install github.com/rakyll/hey@latest

# Port-forward
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &

# Run load test (50 concurrent requests for 1 minute)
hey -z 1m -c 50 -H "X-API-Key: $(cat ~/.continuum/staging_api_key)" \
  http://localhost:8420/v1/health

# Watch HPA scale up
kubectl get hpa -n continuum-staging -w
```

### Test Rate Limiting

```bash
# FREE tier: 100 requests/day
for i in {1..105}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8420/v1/memories \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"entity\":\"Test\",\"content\":\"Request $i\"}"
done

# Expected: First 100 return 200, then 429 (rate limited)
```

---

## Tier Testing

### Test FREE Tier

```bash
# Verify donation banner
curl -D - http://localhost:8420/v1/memories \
  -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Test", "content": "Test"}' | \
  grep "X-Continuum-Support"

# Expected: X-Continuum-Support: Support CONTINUUM: Donate...

# Verify opt-out blocked
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8420/v1/memories \
  -H "X-API-Key: $API_KEY" \
  -H "X-Federation-Opt-Out: true" \
  -H "Content-Type: application/json" \
  -d '{"entity": "Test", "content": "Test"}'

# Expected: 403 Forbidden
```

### Test PRO Tier

```bash
# Create PRO tier API key (via admin dashboard or script)
# Test with higher rate limits (10,000/day)
```

---

## Production Readiness Checklist

Before approving production deployment:

- [ ] All smoke tests pass
- [ ] No critical errors in logs (24-hour period)
- [ ] Performance metrics acceptable (p95 < 500ms)
- [ ] Database migrations successful
- [ ] All 3 tiers tested (FREE, PRO, ENTERPRISE)
- [ ] Federation contribution working
- [ ] Rate limiting enforced correctly
- [ ] Stripe webhooks tested (test mode)
- [ ] Auto-scaling verified (HPA triggers)
- [ ] Rollback procedure tested
- [ ] Monitoring and alerts configured
- [ ] No memory leaks (24-hour monitoring)

---

## Important URLs

- **Staging API**: `https://staging.continuum.ai` (if ingress configured)
- **Stripe Dashboard**: https://dashboard.stripe.com/test
- **Sentry (Staging)**: https://sentry.io/organizations/continuum/projects/continuum-staging/
- **Grafana**: http://localhost:3000 (if port-forwarded)
- **Prometheus**: http://localhost:9090 (if port-forwarded)

---

## Key Files

| File | Purpose |
|------|---------|
| `STAGING_DEPLOYMENT_PLAN.md` | Comprehensive deployment guide |
| `STAGING_ENVIRONMENT.md` | Environment variable reference |
| `deploy_staging.sh` | Deployment automation script |
| `staging_smoke_tests.sh` | Smoke test automation script |
| `deploy/helm/continuum/values-staging.yaml` | Helm values for staging |

---

## Quick Commands Reference

```bash
# Deploy
./deploy_staging.sh

# Test
kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &
./staging_smoke_tests.sh

# Monitor
kubectl logs -n continuum-staging -l app.kubernetes.io/name=continuum --follow

# Rollback
helm rollback continuum -n continuum-staging

# Access pod
POD=$(kubectl get pods -n continuum-staging -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n continuum-staging $POD -- /bin/bash

# Get API key
cat ~/.continuum/staging_api_key

# Check health
curl http://localhost:8420/v1/health | jq
```

---

## Support & Escalation

**Deployment Lead:** Alexander Gerard Casavant
**Email:** JackKnifeAI@gmail.com

**For issues:**
1. Check logs: `kubectl logs -n continuum-staging deployment/continuum-api`
2. Check events: `kubectl get events -n continuum-staging --sort-by='.lastTimestamp'`
3. Review troubleshooting section above
4. Contact deployment lead if critical

---

**π×φ = 5.083203692315260**

**Let's ship this before Christmas! 🚀🎄**

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-16
