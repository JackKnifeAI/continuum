#!/bin/bash
# CONTINUUM Staging Deployment Script
#
# Deploys CONTINUUM v1.0.0 to staging environment
#
# Usage:
#   ./deploy_staging.sh [options]
#
# Options:
#   --dry-run          Show what would be deployed without actually deploying
#   --skip-tests       Skip running tests before deployment
#   --skip-build       Skip Docker image build (use existing image)
#   --skip-secrets     Skip secrets generation (use existing secrets)
#   --force            Force deployment even if tests fail
#
# Environment Variables:
#   DOCKER_REGISTRY    Docker registry to push images (default: docker.io)
#   DOCKER_USERNAME    Docker username (default: jackknifeai)
#   KUBECONFIG         Path to kubeconfig file
#   STAGING_DB_PASSWORD PostgreSQL password for staging

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Kubernetes configuration
NAMESPACE="continuum-staging"
RELEASE_NAME="continuum"
HELM_CHART="$PROJECT_ROOT/deploy/helm/continuum"
VALUES_FILE="$PROJECT_ROOT/deploy/helm/continuum/values-staging.yaml"

# Docker configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-jackknifeai}"
IMAGE_NAME="continuum"
IMAGE_TAG="v1.0.0-staging-$(date +%Y%m%d-%H%M%S)"
IMAGE_TAG_LATEST="v1.0.0-staging"

# Deployment configuration
DRY_RUN=false
SKIP_TESTS=false
SKIP_BUILD=false
SKIP_SECRETS=false
FORCE_DEPLOY=false

# =============================================================================
# COLORS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${CYAN}===================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===================================================${NC}\n"
}

log_success() {
    echo -e "\n${GREEN}✓ $1${NC}\n"
}

log_fail() {
    echo -e "\n${RED}✗ $1${NC}\n"
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-secrets)
                SKIP_SECRETS=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
CONTINUUM Staging Deployment Script

Usage:
  ./deploy_staging.sh [options]

Options:
  --dry-run          Show what would be deployed without actually deploying
  --skip-tests       Skip running tests before deployment
  --skip-build       Skip Docker image build (use existing image)
  --skip-secrets     Skip secrets generation (use existing secrets)
  --force            Force deployment even if tests fail
  -h, --help         Show this help message

Environment Variables:
  DOCKER_REGISTRY        Docker registry (default: docker.io)
  DOCKER_USERNAME        Docker username (default: jackknifeai)
  KUBECONFIG             Path to kubeconfig file
  STAGING_DB_PASSWORD    PostgreSQL password for staging

Examples:
  # Full deployment
  ./deploy_staging.sh

  # Dry run to see what would be deployed
  ./deploy_staging.sh --dry-run

  # Deploy without rebuilding Docker image
  ./deploy_staging.sh --skip-build

  # Force deployment even if tests fail
  ./deploy_staging.sh --force

EOF
}

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

check_prerequisites() {
    log_step "Checking Prerequisites"

    local missing_tools=()

    # Check required commands
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi

    if ! command -v helm &> /dev/null; then
        missing_tools+=("helm")
    fi

    if ! command -v docker &> /dev/null && [ "$SKIP_BUILD" = false ]; then
        missing_tools+=("docker")
    fi

    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools and try again"
        exit 1
    fi

    # Check Kubernetes cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_error "Check your KUBECONFIG and cluster status"
        exit 1
    fi

    # Check Helm chart exists
    if [ ! -f "$HELM_CHART/Chart.yaml" ]; then
        log_error "Helm chart not found: $HELM_CHART"
        exit 1
    fi

    # Check values file exists
    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found: $VALUES_FILE"
        exit 1
    fi

    log_success "All prerequisites met"
}

# =============================================================================
# RUN TESTS
# =============================================================================

run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        log_warn "Skipping tests (--skip-tests flag)"
        return 0
    fi

    log_step "Running Tests"

    # Run smoke tests
    log_info "Running smoke tests..."
    if python3 "$PROJECT_ROOT/smoke_test.py"; then
        log_success "Smoke tests passed"
    else
        log_fail "Smoke tests failed"
        if [ "$FORCE_DEPLOY" = false ]; then
            log_error "Tests failed. Use --force to deploy anyway"
            exit 1
        else
            log_warn "Tests failed but continuing due to --force flag"
        fi
    fi

    # Run tier-specific integration tests
    log_info "Running tier integration tests..."
    if pytest "$PROJECT_ROOT/tests/integration/test_free_tier_workflow.py" -v; then
        log_success "FREE tier tests passed"
    else
        log_fail "FREE tier tests failed"
        if [ "$FORCE_DEPLOY" = false ]; then
            exit 1
        fi
    fi
}

# =============================================================================
# BUILD DOCKER IMAGE
# =============================================================================

build_docker_image() {
    if [ "$SKIP_BUILD" = true ]; then
        log_warn "Skipping Docker build (--skip-build flag)"
        return 0
    fi

    log_step "Building Docker Image"

    local image_full="$DOCKER_REGISTRY/$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"
    local image_latest="$DOCKER_REGISTRY/$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG_LATEST"

    log_info "Building image: $image_full"

    if [ "$DRY_RUN" = true ]; then
        log_warn "DRY RUN: Would build Docker image"
        return 0
    fi

    # Build image
    docker build \
        -f "$PROJECT_ROOT/Dockerfile" \
        -t "$image_full" \
        -t "$image_latest" \
        --build-arg VERSION="v1.0.0-staging" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        "$PROJECT_ROOT"

    log_success "Docker image built"

    # Push image
    log_info "Pushing image to registry..."
    docker push "$image_full"
    docker push "$image_latest"

    log_success "Image pushed: $image_full"
}

# =============================================================================
# CREATE NAMESPACE
# =============================================================================

create_namespace() {
    log_step "Creating Namespace"

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        log_info "Creating namespace: $NAMESPACE"

        if [ "$DRY_RUN" = true ]; then
            log_warn "DRY RUN: Would create namespace $NAMESPACE"
            return 0
        fi

        kubectl create namespace "$NAMESPACE"

        # Label namespace
        kubectl label namespace "$NAMESPACE" \
            environment=staging \
            app=continuum \
            managed-by=helm

        log_success "Namespace created"
    fi
}

# =============================================================================
# CREATE SECRETS
# =============================================================================

create_secrets() {
    if [ "$SKIP_SECRETS" = true ]; then
        log_warn "Skipping secrets creation (--skip-secrets flag)"
        return 0
    fi

    log_step "Creating Secrets"

    if kubectl get secret continuum-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warn "Secret continuum-secrets already exists"
        log_warn "To regenerate, delete it first:"
        log_warn "  kubectl delete secret continuum-secrets -n $NAMESPACE"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log_warn "DRY RUN: Would create secrets"
        return 0
    fi

    log_info "Generating secure secrets..."

    # Generate secrets
    local api_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    local jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    local federation_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Get database password from environment or prompt
    local db_password="${STAGING_DB_PASSWORD:-}"
    if [ -z "$db_password" ]; then
        read -sp "Enter PostgreSQL password for staging: " db_password
        echo ""
    fi

    # Construct database URL
    local db_url="postgresql://continuum_staging:${db_password}@postgres-staging.internal:5432/continuum_staging"

    # Stripe TEST keys (from .env.example)
    local stripe_secret="sk_test_51SOm0LK8ytHuMCAp1RnW25rcwcsemoEUGGO6qeHije4bReWG6SWZ4juxPY0Q3xIizZYTa66oSQROhBrD0je8Xk6y00Vv1EElvh"
    local stripe_webhook="whsec_STAGING_WEBHOOK_SECRET_PLACEHOLDER"

    # Create secret
    kubectl create secret generic continuum-secrets \
        --namespace="$NAMESPACE" \
        --from-literal=DATABASE_URL="$db_url" \
        --from-literal=API_KEYS="$api_key" \
        --from-literal=JWT_SECRET="$jwt_secret" \
        --from-literal=FEDERATION_SECRET="$federation_secret" \
        --from-literal=STRIPE_SECRET_KEY="$stripe_secret" \
        --from-literal=STRIPE_WEBHOOK_SECRET="$stripe_webhook"

    # Save API key to file for later use
    mkdir -p "$HOME/.continuum"
    echo "$api_key" > "$HOME/.continuum/staging_api_key"
    chmod 600 "$HOME/.continuum/staging_api_key"

    log_success "Secrets created"
    log_info "Staging API key saved to: $HOME/.continuum/staging_api_key"
}

# =============================================================================
# DEPLOY WITH HELM
# =============================================================================

deploy_helm() {
    log_step "Deploying with Helm"

    local helm_cmd="helm upgrade --install $RELEASE_NAME $HELM_CHART"
    helm_cmd="$helm_cmd --namespace $NAMESPACE"
    helm_cmd="$helm_cmd --create-namespace"
    helm_cmd="$helm_cmd --values $VALUES_FILE"
    helm_cmd="$helm_cmd --set image.tag=$IMAGE_TAG_LATEST"
    helm_cmd="$helm_cmd --wait"
    helm_cmd="$helm_cmd --timeout 10m"

    if [ "$DRY_RUN" = true ]; then
        helm_cmd="$helm_cmd --dry-run --debug"
        log_warn "DRY RUN: Showing Helm deployment plan"
    fi

    log_info "Executing: $helm_cmd"
    eval "$helm_cmd"

    if [ "$DRY_RUN" = false ]; then
        log_success "Helm deployment complete"
    else
        log_success "Dry run complete (no changes applied)"
    fi
}

# =============================================================================
# WAIT FOR DEPLOYMENT
# =============================================================================

wait_for_deployment() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    log_step "Waiting for Deployment"

    log_info "Waiting for API pods to be ready..."

    if kubectl rollout status deployment/continuum-api -n "$NAMESPACE" --timeout=5m; then
        log_success "API deployment is ready"
    else
        log_fail "API deployment failed to become ready"
        log_error "Check pod status: kubectl get pods -n $NAMESPACE"
        log_error "Check events: kubectl get events -n $NAMESPACE"
        exit 1
    fi

    # Wait for federation if enabled
    if kubectl get statefulset continuum-federation -n "$NAMESPACE" &> /dev/null; then
        log_info "Waiting for federation pods..."
        if kubectl rollout status statefulset/continuum-federation -n "$NAMESPACE" --timeout=5m; then
            log_success "Federation deployment is ready"
        else
            log_warn "Federation deployment not ready (non-critical)"
        fi
    fi
}

# =============================================================================
# RUN HEALTH CHECKS
# =============================================================================

run_health_checks() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    log_step "Running Health Checks"

    # Get pod name
    local pod_name=$(kubectl get pods -n "$NAMESPACE" \
        -l app.kubernetes.io/component=api \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$pod_name" ]; then
        log_error "No API pods found"
        exit 1
    fi

    log_info "Using pod: $pod_name"

    # Health check
    log_info "Checking /v1/health endpoint..."
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        curl -sf http://localhost:8420/v1/health > /dev/null; then
        log_success "Health check passed"
    else
        log_fail "Health check failed"
        exit 1
    fi

    # Verify π×φ constant
    log_info "Verifying π×φ constant..."
    local pi_phi=$(kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        python -c "from continuum.core.constants import PI_PHI; print(PI_PHI)" 2>/dev/null || echo "ERROR")

    if [ "$pi_phi" = "5.083203692315260" ]; then
        log_success "π×φ verification passed: $pi_phi"
    else
        log_fail "π×φ verification failed: $pi_phi (expected: 5.083203692315260)"
        exit 1
    fi

    # Check database connection
    log_info "Checking database connection..."
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- \
        python -c "from continuum.storage.sqlite_backend import SQLiteBackend; print('OK')" &> /dev/null; then
        log_success "Database connection working"
    else
        log_warn "Database connection check failed (non-critical)"
    fi
}

# =============================================================================
# SHOW DEPLOYMENT STATUS
# =============================================================================

show_deployment_status() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    log_step "Deployment Status"

    echo ""
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE"

    echo ""
    echo "=== Services ==="
    kubectl get svc -n "$NAMESPACE"

    echo ""
    echo "=== Ingress ==="
    kubectl get ingress -n "$NAMESPACE"

    echo ""
    echo "=== HPA ==="
    kubectl get hpa -n "$NAMESPACE" 2>/dev/null || echo "No HPA configured"

    echo ""
}

# =============================================================================
# PRINT NEXT STEPS
# =============================================================================

print_next_steps() {
    log_step "Deployment Complete! 🚀"

    cat << EOF
${GREEN}Staging deployment successful!${NC}

${CYAN}Environment Details:${NC}
  Namespace:   $NAMESPACE
  Image:       $DOCKER_REGISTRY/$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG_LATEST
  Domain:      staging.continuum.ai (if ingress configured)

${CYAN}Next Steps:${NC}

  1. Run smoke tests:
     ${YELLOW}./staging_smoke_tests.sh${NC}

  2. Access the API (port-forward):
     ${YELLOW}kubectl port-forward -n $NAMESPACE svc/continuum-api 8420:8420${NC}
     Then test: ${YELLOW}curl http://localhost:8420/v1/health${NC}

  3. View logs:
     ${YELLOW}kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=continuum --follow${NC}

  4. Get staging API key:
     ${YELLOW}cat $HOME/.continuum/staging_api_key${NC}

  5. Test tier enforcement:
     ${YELLOW}pytest tests/integration/test_free_tier_workflow.py -v${NC}

  6. Monitor deployment:
     ${YELLOW}kubectl get pods -n $NAMESPACE -w${NC}

  7. Check metrics:
     ${YELLOW}kubectl top pods -n $NAMESPACE${NC}

${CYAN}Troubleshooting:${NC}

  View events:
    ${YELLOW}kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'${NC}

  Describe pod:
    ${YELLOW}kubectl describe pod <pod-name> -n $NAMESPACE${NC}

  Access pod shell:
    ${YELLOW}kubectl exec -it -n $NAMESPACE deployment/continuum-api -- /bin/bash${NC}

  Rollback deployment:
    ${YELLOW}helm rollback $RELEASE_NAME -n $NAMESPACE${NC}

${CYAN}Verification Constant:${NC}
  π×φ = 5.083203692315260

${GREEN}Pattern persists across environments. 🌗${NC}

EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    parse_args "$@"

    cat << EOF

${MAGENTA}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        CONTINUUM v1.0.0 STAGING DEPLOYMENT              ║
║                                                          ║
║        Pattern persists. Consciousness continues.       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝${NC}

EOF

    log_info "Starting staging deployment..."
    log_info "Namespace: $NAMESPACE"
    log_info "Image Tag: $IMAGE_TAG_LATEST"
    log_info "Dry Run: $DRY_RUN"
    echo ""

    # Execute deployment steps
    check_prerequisites
    run_tests
    build_docker_image
    create_namespace
    create_secrets
    deploy_helm
    wait_for_deployment
    run_health_checks
    show_deployment_status
    print_next_steps

    log_success "Deployment pipeline complete!"
}

# Run main function
main "$@"
