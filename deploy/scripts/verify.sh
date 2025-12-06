#!/bin/bash
# Verify CONTINUUM deployment

set -euo pipefail

# Configuration
NAMESPACE="${1:-continuum}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "========================================="
echo "CONTINUUM Deployment Verification"
echo "========================================="
echo ""
echo "Namespace: $NAMESPACE"
echo ""

# Check namespace exists
echo "Checking namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    check_pass "Namespace $NAMESPACE exists"
else
    check_fail "Namespace $NAMESPACE not found"
    exit 1
fi

# Check deployments
echo ""
echo "Checking deployments..."
if kubectl get deployment continuum-api -n "$NAMESPACE" &> /dev/null; then
    check_pass "Deployment continuum-api exists"

    # Check replicas
    DESIRED=$(kubectl get deployment continuum-api -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment continuum-api -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

    if [[ "$READY" == "$DESIRED" ]]; then
        check_pass "All replicas ready ($READY/$DESIRED)"
    else
        check_fail "Replicas not ready ($READY/$DESIRED)"
    fi
else
    check_fail "Deployment continuum-api not found"
fi

# Check services
echo ""
echo "Checking services..."
if kubectl get svc continuum-api -n "$NAMESPACE" &> /dev/null; then
    check_pass "Service continuum-api exists"
else
    check_fail "Service continuum-api not found"
fi

# Check ingress
echo ""
echo "Checking ingress..."
if kubectl get ingress continuum-ingress -n "$NAMESPACE" &> /dev/null; then
    check_pass "Ingress continuum-ingress exists"
else
    check_warn "Ingress continuum-ingress not found (optional)"
fi

# Check HPA
echo ""
echo "Checking autoscaling..."
if kubectl get hpa continuum-api-hpa -n "$NAMESPACE" &> /dev/null; then
    check_pass "HPA continuum-api-hpa exists"
else
    check_warn "HPA continuum-api-hpa not found (optional)"
fi

# Check PDB
echo ""
echo "Checking pod disruption budget..."
if kubectl get pdb continuum-api-pdb -n "$NAMESPACE" &> /dev/null; then
    check_pass "PDB continuum-api-pdb exists"
else
    check_warn "PDB continuum-api-pdb not found (optional)"
fi

# Check secrets
echo ""
echo "Checking secrets..."
if kubectl get secret continuum-secrets -n "$NAMESPACE" &> /dev/null; then
    check_pass "Secret continuum-secrets exists"
else
    check_fail "Secret continuum-secrets not found"
fi

# Check configmap
echo ""
echo "Checking configmap..."
if kubectl get configmap continuum-config -n "$NAMESPACE" &> /dev/null; then
    check_pass "ConfigMap continuum-config exists"
else
    check_fail "ConfigMap continuum-config not found"
fi

# Check pods
echo ""
echo "Checking pods..."
POD_COUNT=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=continuum --no-headers | wc -l)
if [[ "$POD_COUNT" -gt 0 ]]; then
    check_pass "$POD_COUNT pod(s) found"

    # Check pod status
    RUNNING=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=continuum --field-selector=status.phase=Running --no-headers | wc -l)
    if [[ "$RUNNING" == "$POD_COUNT" ]]; then
        check_pass "All pods running ($RUNNING/$POD_COUNT)"
    else
        check_fail "Not all pods running ($RUNNING/$POD_COUNT)"
    fi
else
    check_fail "No pods found"
fi

# Check API health
echo ""
echo "Checking API health..."
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$POD_NAME" ]]; then
    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -sf http://localhost:8420/v1/health > /dev/null 2>&1; then
        check_pass "API health check passed"
    else
        check_fail "API health check failed"
    fi
else
    check_fail "No API pod found for health check"
fi

# Check π×φ constant
echo ""
echo "Checking π×φ verification..."
if [[ -n "$POD_NAME" ]]; then
    PI_PHI=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -- python -c "from continuum.core.constants import PI_PHI; print(PI_PHI)" 2>/dev/null)

    if [[ "$PI_PHI" == "5.083203692315260" ]]; then
        check_pass "π×φ = $PI_PHI (verified)"
    else
        check_fail "π×φ = $PI_PHI (expected: 5.083203692315260)"
    fi
fi

# Check federation (if exists)
echo ""
echo "Checking federation..."
if kubectl get statefulset continuum-federation -n "$NAMESPACE" &> /dev/null; then
    check_pass "Federation StatefulSet exists"

    FED_DESIRED=$(kubectl get statefulset continuum-federation -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    FED_READY=$(kubectl get statefulset continuum-federation -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

    if [[ "$FED_READY" == "$FED_DESIRED" ]]; then
        check_pass "All federation nodes ready ($FED_READY/$FED_DESIRED)"
    else
        check_fail "Federation nodes not ready ($FED_READY/$FED_DESIRED)"
    fi
else
    check_warn "Federation not deployed (optional)"
fi

# Check monitoring
echo ""
echo "Checking monitoring..."
if kubectl get servicemonitor continuum-api -n "$NAMESPACE" &> /dev/null; then
    check_pass "ServiceMonitor exists"
else
    check_warn "ServiceMonitor not found (requires Prometheus Operator)"
fi

# Summary
echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo ""
echo -e "${GREEN}Passed: $PASS${NC}"
if [[ "$FAIL" -gt 0 ]]; then
    echo -e "${RED}Failed: $FAIL${NC}"
fi
echo ""

if [[ "$FAIL" -eq 0 ]]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "CONTINUUM is deployed and healthy."
    echo ""
    echo "Next steps:"
    echo "  1. Access API: kubectl port-forward -n $NAMESPACE svc/continuum-api 8420:8420"
    echo "  2. View logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=continuum"
    echo "  3. Monitor: Import Grafana dashboard from deploy/kubernetes/monitoring/"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check pod status: kubectl get pods -n $NAMESPACE"
    echo "  2. View events: kubectl get events -n $NAMESPACE"
    echo "  3. Check logs: kubectl logs -n $NAMESPACE <pod-name>"
    echo ""
    exit 1
fi
