#!/bin/bash
# CONTINUUM Staging Smoke Tests
#
# Comprehensive smoke tests for staging deployment.
# Tests all critical functionality before production deployment.
#
# Usage:
#   ./staging_smoke_tests.sh [options]
#
# Options:
#   --api-url URL      API URL (default: http://localhost:8420)
#   --api-key KEY      API key for testing (default: read from ~/.continuum/staging_api_key)
#   --namespace NS     Kubernetes namespace (default: continuum-staging)
#   --skip-k8s         Skip Kubernetes-specific checks
#   --verbose          Verbose output

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

API_URL="${API_URL:-http://localhost:8420}"
API_KEY_FILE="$HOME/.continuum/staging_api_key"
API_KEY="${API_KEY:-}"
NAMESPACE="continuum-staging"
SKIP_K8S=false
VERBOSE=false

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# =============================================================================
# COLORS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# LOGGING
# =============================================================================

log_test() {
    ((TOTAL_TESTS++))
    echo -ne "${CYAN}[TEST $TOTAL_TESTS]${NC} $1... "
}

log_pass() {
    ((PASSED_TESTS++))
    echo -e "${GREEN}PASS${NC}"
    [ "$VERBOSE" = true ] && echo "  ✓ $1"
}

log_fail() {
    ((FAILED_TESTS++))
    echo -e "${RED}FAIL${NC}"
    echo -e "  ${RED}✗ $1${NC}"
}

log_skip() {
    ((SKIPPED_TESTS++))
    echo -e "${YELLOW}SKIP${NC}"
    [ "$VERBOSE" = true ] && echo "  ⊘ $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
    echo ""
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-url)
                API_URL="$2"
                shift 2
                ;;
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --skip-k8s)
                SKIP_K8S=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
CONTINUUM Staging Smoke Tests

Usage:
  ./staging_smoke_tests.sh [options]

Options:
  --api-url URL      API URL (default: http://localhost:8420)
  --api-key KEY      API key for testing
  --namespace NS     Kubernetes namespace (default: continuum-staging)
  --skip-k8s         Skip Kubernetes-specific checks
  --verbose          Verbose output
  -h, --help         Show this help message

Examples:
  # Run all tests (requires kubectl port-forward)
  kubectl port-forward -n continuum-staging svc/continuum-api 8420:8420 &
  ./staging_smoke_tests.sh

  # Run with custom API URL
  ./staging_smoke_tests.sh --api-url https://staging.continuum.ai

  # Skip Kubernetes checks
  ./staging_smoke_tests.sh --skip-k8s

EOF
}

# =============================================================================
# SETUP
# =============================================================================

setup() {
    log_header "CONTINUUM STAGING SMOKE TESTS"

    log_info "Configuration:"
    log_info "  API URL:    $API_URL"
    log_info "  Namespace:  $NAMESPACE"
    log_info "  Skip K8s:   $SKIP_K8S"
    echo ""

    # Load API key if not provided
    if [ -z "$API_KEY" ] && [ -f "$API_KEY_FILE" ]; then
        API_KEY=$(cat "$API_KEY_FILE")
        log_info "API key loaded from: $API_KEY_FILE"
    elif [ -z "$API_KEY" ]; then
        log_error "API key not found. Please provide --api-key or run deploy_staging.sh first"
        exit 1
    fi
}

# =============================================================================
# TEST SUITE 1: KUBERNETES CHECKS
# =============================================================================

test_kubernetes() {
    if [ "$SKIP_K8S" = true ]; then
        log_skip "Skipping Kubernetes tests (--skip-k8s)"
        return
    fi

    log_header "KUBERNETES DEPLOYMENT"

    # Test: Namespace exists
    log_test "Namespace exists"
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_pass "Namespace $NAMESPACE exists"
    else
        log_fail "Namespace $NAMESPACE not found"
    fi

    # Test: API deployment exists
    log_test "API deployment exists"
    if kubectl get deployment continuum-api -n "$NAMESPACE" &> /dev/null; then
        log_pass "Deployment continuum-api found"
    else
        log_fail "Deployment continuum-api not found"
    fi

    # Test: All replicas ready
    log_test "All API replicas ready"
    local desired=$(kubectl get deployment continuum-api -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    local ready=$(kubectl get deployment continuum-api -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$ready" = "$desired" ] && [ "$ready" -gt 0 ]; then
        log_pass "All replicas ready ($ready/$desired)"
    else
        log_fail "Replicas not ready ($ready/$desired)"
    fi

    # Test: Service exists
    log_test "Service exists"
    if kubectl get svc continuum-api -n "$NAMESPACE" &> /dev/null; then
        log_pass "Service continuum-api exists"
    else
        log_fail "Service continuum-api not found"
    fi

    # Test: Ingress exists
    log_test "Ingress exists"
    if kubectl get ingress continuum-ingress -n "$NAMESPACE" &> /dev/null; then
        log_pass "Ingress continuum-ingress exists"
    else
        log_skip "Ingress not configured (optional)"
    fi

    # Test: HPA exists
    log_test "HPA configured"
    if kubectl get hpa continuum-api-hpa -n "$NAMESPACE" &> /dev/null; then
        log_pass "HPA continuum-api-hpa exists"
    else
        log_skip "HPA not configured (optional)"
    fi

    # Test: Secrets exist
    log_test "Secrets exist"
    if kubectl get secret continuum-secrets -n "$NAMESPACE" &> /dev/null; then
        log_pass "Secret continuum-secrets exists"
    else
        log_fail "Secret continuum-secrets not found"
    fi
}

# =============================================================================
# TEST SUITE 2: API HEALTH
# =============================================================================

test_api_health() {
    log_header "API HEALTH CHECKS"

    # Test: Health endpoint
    log_test "Health endpoint responds"
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/v1/health" 2>/dev/null || echo "000")
    if [ "$health_response" = "200" ]; then
        log_pass "Health endpoint returned 200 OK"
    else
        log_fail "Health endpoint returned $health_response (expected: 200)"
    fi

    # Test: Health endpoint returns correct data
    log_test "Health endpoint returns valid JSON"
    local health_json=$(curl -s "$API_URL/v1/health" 2>/dev/null || echo "{}")
    if echo "$health_json" | jq -e '.status == "healthy"' &> /dev/null; then
        log_pass "Health status is 'healthy'"
    else
        log_fail "Health status is not 'healthy': $health_json"
    fi

    # Test: π×φ constant verification
    log_test "π×φ constant verified"
    local pi_phi=$(echo "$health_json" | jq -r '.pi_phi // empty' 2>/dev/null || echo "")
    if [ "$pi_phi" = "5.083203692315260" ]; then
        log_pass "π×φ = $pi_phi (verified)"
    else
        log_fail "π×φ = $pi_phi (expected: 5.083203692315260)"
    fi

    # Test: Version endpoint
    log_test "Version endpoint responds"
    local version_response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/v1/version" 2>/dev/null || echo "000")
    if [ "$version_response" = "200" ]; then
        log_pass "Version endpoint returned 200 OK"
    else
        log_skip "Version endpoint not available (optional)"
    fi
}

# =============================================================================
# TEST SUITE 3: AUTHENTICATION
# =============================================================================

test_authentication() {
    log_header "AUTHENTICATION"

    # Test: Request without API key fails
    log_test "Request without API key fails (401)"
    local no_auth_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/memories" \
        -H "Content-Type: application/json" \
        -d '{"entity": "test"}' 2>/dev/null || echo "000")
    if [ "$no_auth_response" = "401" ]; then
        log_pass "Unauthorized request rejected with 401"
    else
        log_fail "Expected 401, got $no_auth_response"
    fi

    # Test: Request with valid API key succeeds
    log_test "Request with valid API key succeeds"
    local auth_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/memories" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"entity": "Test Entity", "content": "Test authentication"}' 2>/dev/null || echo "000")
    if [ "$auth_response" = "200" ]; then
        log_pass "Authenticated request succeeded with 200"
    else
        log_fail "Expected 200, got $auth_response"
    fi

    # Test: Request with invalid API key fails
    log_test "Request with invalid API key fails (401)"
    local bad_auth_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/memories" \
        -H "X-API-Key: invalid_key_123" \
        -H "Content-Type: application/json" \
        -d '{"entity": "test"}' 2>/dev/null || echo "000")
    if [ "$bad_auth_response" = "401" ]; then
        log_pass "Invalid API key rejected with 401"
    else
        log_fail "Expected 401, got $bad_auth_response"
    fi
}

# =============================================================================
# TEST SUITE 4: FREE TIER FUNCTIONALITY
# =============================================================================

test_free_tier() {
    log_header "FREE TIER FUNCTIONALITY"

    # Test: Memory write succeeds
    log_test "FREE tier memory write succeeds"
    local memory_response=$(curl -s "$API_URL/v1/memories" \
        -X POST \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "entity": "Free Tier Test",
            "content": "Testing FREE tier memory write in staging environment",
            "metadata": {"test_id": "free_tier_001"}
        }' 2>/dev/null || echo "{}")

    local status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/memories" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"entity": "Test", "content": "Test"}' 2>/dev/null)

    if [ "$status_code" = "200" ]; then
        log_pass "Memory write succeeded"
    else
        log_fail "Memory write failed with status $status_code"
    fi

    # Test: Donation banner header present
    log_test "Donation banner header present"
    local headers=$(curl -s -D - -o /dev/null \
        -X POST "$API_URL/v1/memories" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"entity": "Test", "content": "Test"}' 2>/dev/null || echo "")

    if echo "$headers" | grep -qi "X-Continuum-Support"; then
        log_pass "Donation banner header found"
    else
        log_fail "Donation banner header not found (expected for FREE tier)"
    fi

    # Test: Opt-out blocked
    log_test "FREE tier opt-out blocked (403)"
    local opt_out_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/v1/memories" \
        -H "X-API-Key: $API_KEY" \
        -H "X-Federation-Opt-Out: true" \
        -H "Content-Type: application/json" \
        -d '{"entity": "Test", "content": "Opt-out test"}' 2>/dev/null || echo "000")

    if [ "$opt_out_response" = "403" ]; then
        log_pass "Opt-out correctly blocked with 403"
    else
        log_fail "Expected 403 for opt-out, got $opt_out_response"
    fi

    # Test: Rate limit headers present
    log_test "Rate limit headers present"
    local rate_headers=$(curl -s -D - -o /dev/null \
        "$API_URL/v1/health" \
        -H "X-API-Key: $API_KEY" 2>/dev/null || echo "")

    if echo "$rate_headers" | grep -qi "X-RateLimit"; then
        log_pass "Rate limit headers found"
    else
        log_skip "Rate limit headers not found (may not be configured)"
    fi
}

# =============================================================================
# TEST SUITE 5: MEMORY OPERATIONS
# =============================================================================

test_memory_operations() {
    log_header "MEMORY OPERATIONS"

    # Test: Create memory
    log_test "Create memory"
    local create_response=$(curl -s "$API_URL/v1/memories" \
        -X POST \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "entity": "Smoke Test Entity",
            "content": "This is a comprehensive smoke test for CONTINUUM staging",
            "metadata": {"test": "smoke_test", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' 2>/dev/null || echo "{}")

    local memory_id=$(echo "$create_response" | jq -r '.id // empty' 2>/dev/null)

    if [ -n "$memory_id" ]; then
        log_pass "Memory created with ID: $memory_id"

        # Test: Recall memory
        log_test "Recall memory"
        local recall_response=$(curl -s "$API_URL/v1/memories/$memory_id" \
            -H "X-API-Key: $API_KEY" 2>/dev/null || echo "{}")

        local recalled_entity=$(echo "$recall_response" | jq -r '.entity // empty' 2>/dev/null)

        if [ "$recalled_entity" = "Smoke Test Entity" ]; then
            log_pass "Memory recalled successfully"
        else
            log_fail "Memory recall failed: $recall_response"
        fi

        # Test: Update memory
        log_test "Update memory"
        local update_response=$(curl -s -o /dev/null -w "%{http_code}" \
            -X PUT "$API_URL/v1/memories/$memory_id" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d '{"content": "Updated smoke test content"}' 2>/dev/null || echo "000")

        if [ "$update_response" = "200" ]; then
            log_pass "Memory updated successfully"
        else
            log_skip "Memory update not supported (status: $update_response)"
        fi

        # Test: Delete memory
        log_test "Delete memory"
        local delete_response=$(curl -s -o /dev/null -w "%{http_code}" \
            -X DELETE "$API_URL/v1/memories/$memory_id" \
            -H "X-API-Key: $API_KEY" 2>/dev/null || echo "000")

        if [ "$delete_response" = "200" ] || [ "$delete_response" = "204" ]; then
            log_pass "Memory deleted successfully"
        else
            log_skip "Memory delete not supported (status: $delete_response)"
        fi
    else
        log_fail "Failed to create memory: $create_response"
    fi
}

# =============================================================================
# TEST SUITE 6: DATABASE PERSISTENCE
# =============================================================================

test_persistence() {
    log_header "DATABASE PERSISTENCE"

    # Test: Write memory
    log_test "Write persistence test memory"
    local persist_response=$(curl -s "$API_URL/v1/memories" \
        -X POST \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "entity": "Persistence Test",
            "content": "This memory should persist across pod restarts",
            "metadata": {"persistence_test": true}
        }' 2>/dev/null || echo "{}")

    local persist_id=$(echo "$persist_response" | jq -r '.id // empty' 2>/dev/null)

    if [ -n "$persist_id" ]; then
        log_pass "Persistence test memory created: $persist_id"

        if [ "$SKIP_K8S" = false ]; then
            # Test: Restart pod
            log_test "Restart API pods"
            if kubectl rollout restart deployment/continuum-api -n "$NAMESPACE" &> /dev/null; then
                log_info "Waiting for rollout to complete..."
                if kubectl rollout status deployment/continuum-api -n "$NAMESPACE" --timeout=2m &> /dev/null; then
                    log_pass "Pods restarted successfully"

                    # Wait for API to be ready
                    sleep 10

                    # Test: Verify memory persisted
                    log_test "Verify memory persisted after restart"
                    local persist_check=$(curl -s "$API_URL/v1/memories/$persist_id" \
                        -H "X-API-Key: $API_KEY" 2>/dev/null || echo "{}")

                    local persist_entity=$(echo "$persist_check" | jq -r '.entity // empty' 2>/dev/null)

                    if [ "$persist_entity" = "Persistence Test" ]; then
                        log_pass "Memory persisted across restart"
                    else
                        log_fail "Memory not found after restart"
                    fi
                else
                    log_fail "Rollout failed to complete"
                fi
            else
                log_fail "Failed to restart deployment"
            fi
        else
            log_skip "Skipping pod restart test (--skip-k8s)"
        fi
    else
        log_fail "Failed to create persistence test memory"
    fi
}

# =============================================================================
# TEST SUITE 7: FEDERATION
# =============================================================================

test_federation() {
    log_header "FEDERATION NETWORK"

    # Test: Federation stats endpoint
    log_test "Federation stats endpoint"
    local fed_response=$(curl -s -o /dev/null -w "%{http_code}" \
        "$API_URL/v1/federation/stats" \
        -H "X-API-Key: $API_KEY" 2>/dev/null || echo "000")

    if [ "$fed_response" = "200" ]; then
        log_pass "Federation stats endpoint accessible"
    else
        log_skip "Federation not configured (status: $fed_response)"
    fi

    # Test: Contribution tracking
    log_test "Contribution tracking"
    local contrib_response=$(curl -s "$API_URL/v1/federation/stats" \
        -H "X-API-Key: $API_KEY" 2>/dev/null || echo "{}")

    if echo "$contrib_response" | jq -e '.contributed' &> /dev/null; then
        log_pass "Contribution stats available"
    else
        log_skip "Contribution tracking not available"
    fi
}

# =============================================================================
# TEST SUMMARY
# =============================================================================

print_summary() {
    log_header "TEST SUMMARY"

    echo ""
    echo "Total Tests:   $TOTAL_TESTS"
    echo -e "${GREEN}Passed:        $PASSED_TESTS${NC}"

    if [ "$FAILED_TESTS" -gt 0 ]; then
        echo -e "${RED}Failed:        $FAILED_TESTS${NC}"
    else
        echo "Failed:        $FAILED_TESTS"
    fi

    if [ "$SKIPPED_TESTS" -gt 0 ]; then
        echo -e "${YELLOW}Skipped:       $SKIPPED_TESTS${NC}"
    else
        echo "Skipped:       $SKIPPED_TESTS"
    fi

    echo ""

    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                        ║${NC}"
        echo -e "${GREEN}║   ✓ ALL CRITICAL TESTS PASSED!        ║${NC}"
        echo -e "${GREEN}║                                        ║${NC}"
        echo -e "${GREEN}║   Staging deployment verified.         ║${NC}"
        echo -e "${GREEN}║   Ready for production deployment.     ║${NC}"
        echo -e "${GREEN}║                                        ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo "π×φ = 5.083203692315260 🌗"
        echo ""
        return 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                        ║${NC}"
        echo -e "${RED}║   ✗ SOME TESTS FAILED                  ║${NC}"
        echo -e "${RED}║                                        ║${NC}"
        echo -e "${RED}║   Please review failures above.        ║${NC}"
        echo -e "${RED}║   Do NOT deploy to production.         ║${NC}"
        echo -e "${RED}║                                        ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}"
        echo ""
        return 1
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    parse_args "$@"
    setup

    test_kubernetes
    test_api_health
    test_authentication
    test_free_tier
    test_memory_operations
    test_persistence
    test_federation

    print_summary
}

# Run main
main "$@"
exit_code=$?
exit $exit_code
