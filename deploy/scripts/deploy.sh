#!/bin/bash
# CONTINUUM Deployment Script
# Deploys CONTINUUM to Kubernetes using kubectl + kustomize

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
KUBE_DIR="$DEPLOY_DIR/kubernetes"

# Default values
ENVIRONMENT="${1:-production}"
NAMESPACE="continuum"
DRY_RUN="${DRY_RUN:-false}"
SKIP_SECRETS="${SKIP_SECRETS:-false}"

# Function to print colored output
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        warn "kustomize not found. Using kubectl apply -k instead."
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi

    info "Prerequisites check passed."
}

# Function to validate environment
validate_environment() {
    info "Validating environment: $ENVIRONMENT"

    if [[ ! -d "$KUBE_DIR/overlays/$ENVIRONMENT" ]]; then
        error "Environment '$ENVIRONMENT' not found in overlays/"
        error "Available environments: development, staging, production"
        exit 1
    fi

    # Set namespace based on environment
    case "$ENVIRONMENT" in
        development)
            NAMESPACE="continuum-dev"
            ;;
        staging)
            NAMESPACE="continuum-staging"
            ;;
        production)
            NAMESPACE="continuum"
            ;;
        *)
            error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac

    info "Deploying to namespace: $NAMESPACE"
}

# Function to create namespace
create_namespace() {
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        info "Namespace $NAMESPACE already exists."
    else
        info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
}

# Function to create secrets
create_secrets() {
    if [[ "$SKIP_SECRETS" == "true" ]]; then
        warn "Skipping secrets creation (SKIP_SECRETS=true)"
        return
    fi

    if kubectl get secret continuum-secrets -n "$NAMESPACE" &> /dev/null; then
        warn "Secret continuum-secrets already exists. Skipping creation."
        warn "To update secrets, delete the existing secret first:"
        warn "  kubectl delete secret continuum-secrets -n $NAMESPACE"
        return
    fi

    info "Creating secrets..."
    warn "This script creates placeholder secrets. Replace with real values!"

    # Generate random API key
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    FEDERATION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    kubectl create secret generic continuum-secrets \
        --from-literal=DATABASE_URL="postgresql://continuum_user:CHANGEME@postgres:5432/continuum_db" \
        --from-literal=API_KEYS="$API_KEY" \
        --from-literal=FEDERATION_SECRET="$FEDERATION_SECRET" \
        --namespace="$NAMESPACE"

    info "Secrets created. API Key: $API_KEY"
    warn "IMPORTANT: Store this API key securely!"
}

# Function to deploy using kustomize
deploy_kustomize() {
    info "Deploying with kustomize..."

    local overlay_path="$KUBE_DIR/overlays/$ENVIRONMENT"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "Dry run mode - showing what would be applied:"
        kubectl apply -k "$overlay_path" --dry-run=client
    else
        kubectl apply -k "$overlay_path"
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi

    info "Waiting for deployment to be ready..."

    # Wait for API deployment
    if kubectl rollout status deployment/continuum-api -n "$NAMESPACE" --timeout=300s; then
        info "API deployment is ready!"
    else
        error "API deployment failed to become ready."
        exit 1
    fi

    # Wait for federation statefulset (if exists)
    if kubectl get statefulset continuum-federation -n "$NAMESPACE" &> /dev/null; then
        if kubectl rollout status statefulset/continuum-federation -n "$NAMESPACE" --timeout=300s; then
            info "Federation deployment is ready!"
        else
            warn "Federation deployment failed to become ready."
        fi
    fi
}

# Function to show deployment status
show_status() {
    info "Deployment status:"
    echo ""

    # Pods
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE"
    echo ""

    # Services
    echo "=== Services ==="
    kubectl get svc -n "$NAMESPACE"
    echo ""

    # Ingress
    echo "=== Ingress ==="
    kubectl get ingress -n "$NAMESPACE"
    echo ""

    # HPA
    if kubectl get hpa -n "$NAMESPACE" &> /dev/null; then
        echo "=== Horizontal Pod Autoscaler ==="
        kubectl get hpa -n "$NAMESPACE"
        echo ""
    fi
}

# Function to run post-deployment checks
post_deployment_checks() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi

    info "Running post-deployment checks..."

    # Get pod name
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$POD_NAME" ]]; then
        error "No API pods found."
        return
    fi

    # Health check
    info "Checking API health..."
    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -sf http://localhost:8420/v1/health > /dev/null; then
        info "API health check passed!"
    else
        error "API health check failed."
    fi

    # Verify π×φ constant
    info "Verifying π×φ constant..."
    PI_PHI=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -- \
        python -c "from continuum.core.constants import PI_PHI; print(PI_PHI)")

    if [[ "$PI_PHI" == "5.083203692315260" ]]; then
        info "π×φ verification passed: $PI_PHI"
    else
        error "π×φ verification failed: $PI_PHI"
    fi
}

# Main deployment flow
main() {
    echo "========================================="
    echo "CONTINUUM Kubernetes Deployment"
    echo "========================================="
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Namespace:   $NAMESPACE"
    echo "Dry run:     $DRY_RUN"
    echo ""

    check_prerequisites
    validate_environment
    create_namespace
    create_secrets
    deploy_kustomize
    wait_for_deployment
    show_status
    post_deployment_checks

    echo ""
    info "Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify deployment: kubectl get pods -n $NAMESPACE"
    echo "  2. Check logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=continuum"
    echo "  3. Access API: kubectl port-forward -n $NAMESPACE svc/continuum-api 8420:8420"
    echo "  4. Update secrets with real values (DATABASE_URL, API_KEYS, etc.)"
    echo ""
}

# Run main
main
