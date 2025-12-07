#!/bin/bash
#
# Create and upload Sentry release
#
# This script creates a Sentry release, uploads source files,
# and associates git commits for error tracking.
#
# Usage:
#   ./create_release.sh [version]
#
# Examples:
#   ./create_release.sh                    # Auto-detect from git
#   ./create_release.sh v0.2.0             # Explicit version
#   ./create_release.sh git-abc123         # Git commit
#
# Requirements:
#   - sentry-cli installed (curl -sL https://sentry.io/get-cli/ | bash)
#   - SENTRY_AUTH_TOKEN environment variable set
#   - Git repository

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Sentry organization and project
SENTRY_ORG="${SENTRY_ORG:-jackknifeai}"
SENTRY_PROJECT="${SENTRY_PROJECT:-continuum}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNCTIONS
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

check_requirements() {
    # Check sentry-cli
    if ! command -v sentry-cli &> /dev/null; then
        log_error "sentry-cli not found"
        echo "Install with: curl -sL https://sentry.io/get-cli/ | bash"
        exit 1
    fi

    # Check auth token
    if [ -z "${SENTRY_AUTH_TOKEN:-}" ]; then
        log_error "SENTRY_AUTH_TOKEN not set"
        echo "Get token from: https://sentry.io/settings/account/api/auth-tokens/"
        echo "Then run: export SENTRY_AUTH_TOKEN=your-token"
        exit 1
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git not found"
        exit 1
    fi

    # Check we're in a git repo
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi

    log_success "Requirements check passed"
}

get_version() {
    local version="${1:-}"

    if [ -n "$version" ]; then
        echo "$version"
        return
    fi

    # Try to get from CONTINUUM_RELEASE env var
    if [ -n "${CONTINUUM_RELEASE:-}" ]; then
        echo "$CONTINUUM_RELEASE"
        return
    fi

    # Try to get from git
    if git describe --tags --exact-match 2> /dev/null; then
        # We're on a tag
        git describe --tags --exact-match
    else
        # Use short commit hash
        echo "git-$(git rev-parse --short HEAD)"
    fi
}

create_release() {
    local version="$1"

    log_info "Creating Sentry release: $version"

    sentry-cli releases new \
        --org "$SENTRY_ORG" \
        --project "$SENTRY_PROJECT" \
        "$version"

    log_success "Release created: $version"
}

upload_source_files() {
    local version="$1"

    log_info "Uploading source files..."

    cd "$PROJECT_ROOT"

    # Upload Python source files
    sentry-cli releases files "$version" upload-sourcemaps \
        --org "$SENTRY_ORG" \
        --project "$SENTRY_PROJECT" \
        ./continuum \
        --ext py \
        --strip-prefix continuum/

    log_success "Source files uploaded"
}

associate_commits() {
    local version="$1"

    log_info "Associating git commits..."

    sentry-cli releases set-commits \
        --org "$SENTRY_ORG" \
        --project "$SENTRY_PROJECT" \
        "$version" \
        --auto

    log_success "Commits associated"
}

finalize_release() {
    local version="$1"

    log_info "Finalizing release..."

    sentry-cli releases finalize \
        --org "$SENTRY_ORG" \
        --project "$SENTRY_PROJECT" \
        "$version"

    log_success "Release finalized: $version"
}

create_deployment() {
    local version="$1"
    local env="${CONTINUUM_ENV:-production}"

    log_info "Creating deployment for environment: $env"

    sentry-cli releases deploys "$version" new \
        --org "$SENTRY_ORG" \
        --project "$SENTRY_PROJECT" \
        --env "$env"

    log_success "Deployment created for: $env"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local version

    log_info "Sentry Release Creation Tool"
    echo "Organization: $SENTRY_ORG"
    echo "Project: $SENTRY_PROJECT"
    echo ""

    # Check requirements
    check_requirements

    # Get version
    version=$(get_version "${1:-}")
    log_info "Version: $version"
    echo ""

    # Create release
    create_release "$version"

    # Upload source files (optional, but recommended)
    if [ "${SKIP_SOURCE_UPLOAD:-false}" != "true" ]; then
        upload_source_files "$version"
    else
        log_warning "Skipping source file upload (SKIP_SOURCE_UPLOAD=true)"
    fi

    # Associate commits (optional, but recommended)
    if [ "${SKIP_COMMITS:-false}" != "true" ]; then
        associate_commits "$version"
    else
        log_warning "Skipping commit association (SKIP_COMMITS=true)"
    fi

    # Finalize release
    finalize_release "$version"

    # Create deployment (optional)
    if [ "${CREATE_DEPLOYMENT:-true}" == "true" ]; then
        create_deployment "$version"
    else
        log_warning "Skipping deployment creation (CREATE_DEPLOYMENT=false)"
    fi

    echo ""
    log_success "✓ Release created successfully!"
    echo ""
    echo "View release: https://sentry.io/organizations/$SENTRY_ORG/releases/$version/"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy your application with: export CONTINUUM_RELEASE=$version"
    echo "  2. Monitor errors in Sentry dashboard"
    echo "  3. Check that errors are attributed to this release"
}

# Run main
main "$@"
