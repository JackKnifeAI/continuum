#!/usr/bin/env bash
#
# CONTINUUM Fly.io Deployment Script
#
# Automated deployment with pre-flight checks and rollback capability
#
# Usage:
#   ./scripts/deploy.sh                 # Deploy to production
#   ./scripts/deploy.sh --staging       # Deploy to staging
#   ./scripts/deploy.sh --check         # Run checks only
#   ./scripts/deploy.sh --rollback      # Rollback last deployment

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deploy/flyio"

APP_NAME="${FLY_APP_NAME:-continuum-memory}"
REGIONS="${FLY_REGIONS:-iad,lhr,sin}"
MIN_INSTANCES="${FLY_MIN_INSTANCES:-1}"
MAX_INSTANCES="${FLY_MAX_INSTANCES:-10}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check required commands
    check_command "fly"
    check_command "docker"
    check_command "git"

    # Check if logged in to Fly.io
    if ! fly auth whoami &> /dev/null; then
        log_error "Not logged in to Fly.io. Run: fly auth login"
        exit 1
    fi

    # Check if in git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        log_warning "Not in a git repository. Deploy metadata will be limited."
    fi

    # Check for uncommitted changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        log_success "No uncommitted changes"
    else
        log_warning "You have uncommitted changes. Consider committing before deploy."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check if fly.toml exists
    if [ ! -f "$DEPLOY_DIR/fly.toml" ]; then
        log_error "fly.toml not found in $DEPLOY_DIR"
        exit 1
    fi

    # Check if Dockerfile exists
    if [ ! -f "$DEPLOY_DIR/Dockerfile" ]; then
        log_error "Dockerfile not found in $DEPLOY_DIR"
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

# =============================================================================
# DEPLOYMENT
# =============================================================================

deploy() {
    local environment="${1:-production}"

    log_info "Starting deployment to $environment..."

    # Change to deploy directory
    cd "$DEPLOY_DIR"

    # Get current git commit
    GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    log_info "Git commit: $GIT_COMMIT"
    log_info "Git branch: $GIT_BRANCH"
    log_info "Deploy time: $DEPLOY_TIME"

    # Build and deploy
    log_info "Building Docker image..."
    fly deploy \
        --config fly.toml \
        --dockerfile Dockerfile \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg GIT_BRANCH="$GIT_BRANCH" \
        --build-arg DEPLOY_TIME="$DEPLOY_TIME" \
        --remote-only \
        --strategy rolling

    if [ $? -eq 0 ]; then
        log_success "Deployment successful!"

        # Show deployment info
        log_info "Checking deployment status..."
        fly status

        log_info "Recent logs:"
        fly logs --lines 20

        # Health check
        log_info "Running health check..."
        sleep 5
        HEALTH_URL=$(fly info --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$HEALTH_URL" ]; then
            if curl -sf "https://$HEALTH_URL/v1/health" > /dev/null; then
                log_success "Health check passed: https://$HEALTH_URL/v1/health"
            else
                log_warning "Health check failed. Check logs with: fly logs"
            fi
        fi

        log_success "Deployment complete!"
        echo ""
        echo "Next steps:"
        echo "  - Monitor logs: fly logs"
        echo "  - Check status: fly status"
        echo "  - Scale app: fly scale count 3 --region $REGIONS"
        echo "  - Rollback: $0 --rollback"

    else
        log_error "Deployment failed!"
        exit 1
    fi
}

# =============================================================================
# ROLLBACK
# =============================================================================

rollback() {
    log_warning "Rolling back to previous version..."

    # Get list of releases
    log_info "Recent releases:"
    fly releases --json | head -20

    read -p "Enter release version to rollback to (or 'cancel'): " VERSION

    if [ "$VERSION" = "cancel" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    if [ -z "$VERSION" ]; then
        log_error "No version specified"
        exit 1
    fi

    log_warning "Rolling back to version $VERSION..."
    fly releases rollback "$VERSION"

    if [ $? -eq 0 ]; then
        log_success "Rollback successful!"
        fly status
    else
        log_error "Rollback failed!"
        exit 1
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local mode="${1:-deploy}"

    case "$mode" in
        --staging)
            APP_NAME="${APP_NAME}-staging"
            preflight_checks
            deploy "staging"
            ;;
        --check)
            preflight_checks
            log_success "All checks passed. Ready to deploy."
            ;;
        --rollback)
            rollback
            ;;
        --help|-h)
            echo "CONTINUUM Fly.io Deployment"
            echo ""
            echo "Usage:"
            echo "  $0              Deploy to production"
            echo "  $0 --staging    Deploy to staging"
            echo "  $0 --check      Run pre-flight checks only"
            echo "  $0 --rollback   Rollback last deployment"
            echo "  $0 --help       Show this help"
            echo ""
            echo "Environment variables:"
            echo "  FLY_APP_NAME       App name (default: continuum-memory)"
            echo "  FLY_REGIONS        Regions to deploy (default: iad,lhr,sin)"
            echo "  FLY_MIN_INSTANCES  Minimum instances (default: 1)"
            echo "  FLY_MAX_INSTANCES  Maximum instances (default: 10)"
            ;;
        *)
            preflight_checks
            deploy "production"
            ;;
    esac
}

main "$@"
