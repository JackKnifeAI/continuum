#!/bin/bash
#
# CONTINUUM Load Test Runner
#
# Executes various load testing scenarios and generates reports.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="$RESULTS_DIR/load_test_$TIMESTAMP"

# Default values
HOST="http://localhost:8000"
USERS=100
SPAWN_RATE=10
DURATION="5m"
SCENARIO="all"

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
CONTINUUM Load Test Runner

Usage: $0 [OPTIONS]

Options:
    -h, --host HOST         API host (default: http://localhost:8000)
    -u, --users NUM         Number of users (default: 100)
    -r, --spawn-rate NUM    Spawn rate (users/sec) (default: 10)
    -t, --time DURATION     Test duration (e.g., 5m, 300s) (default: 5m)
    -s, --scenario NAME     Scenario to run (default: all)
                            Options: all, memory, search, federation, api, quick
    --web                   Run with web UI (interactive mode)
    --step                  Use step load pattern
    --spike                 Use spike load pattern
    --help                  Show this help

Examples:
    # Quick smoke test
    $0 --scenario quick

    # Full API test with 1000 users
    $0 --scenario api --users 1000 --time 10m

    # Memory operations only
    $0 --scenario memory --users 500

    # Interactive web UI
    $0 --web

    # Spike test
    $0 --spike --users 1500

Scenarios:
    all         - Full test suite (all scenarios)
    quick       - Quick smoke test (50 users, 2 min)
    memory      - Memory CRUD operations
    search      - Search and retrieval
    federation  - Federation sync
    api         - Realistic API workload

EOF
    exit 0
}

check_dependencies() {
    print_info "Checking dependencies..."

    if ! command -v locust &> /dev/null; then
        print_error "Locust not found. Install with: pip install locust"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi

    print_info "Dependencies OK"
}

check_api_health() {
    print_info "Checking API health at $HOST..."

    if command -v curl &> /dev/null; then
        if curl -s --fail "$HOST/health" > /dev/null 2>&1; then
            print_info "API is healthy"
            return 0
        else
            print_warn "API health check failed - API may not be running"
            print_warn "Start the API with: continuum serve"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_warn "curl not found - skipping health check"
    fi
}

prepare_results_dir() {
    mkdir -p "$RESULTS_DIR"
    print_info "Results will be saved to: $RESULT_FILE.*"
}

run_load_test() {
    local scenario=$1
    local web_mode=$2
    local load_shape=$3

    print_header "Running Load Test: $scenario"

    # Build locust command
    local cmd="locust -f $SCRIPT_DIR/locustfile.py --host $HOST"

    # Add scenario tags if not running all
    if [[ "$scenario" != "all" && "$scenario" != "quick" ]]; then
        cmd="$cmd --tags $scenario"
    fi

    # Web mode or headless
    if [[ "$web_mode" == "true" ]]; then
        print_info "Starting Locust web UI..."
        print_info "Open http://localhost:8089 in your browser"
        $cmd
    else
        # Headless mode
        cmd="$cmd --headless --users $USERS --spawn-rate $SPAWN_RATE --run-time $DURATION"
        cmd="$cmd --html ${RESULT_FILE}.html --csv ${RESULT_FILE}"
        cmd="$cmd --logfile ${RESULT_FILE}.log"

        print_info "Running headless test..."
        print_info "  Users: $USERS"
        print_info "  Spawn rate: $SPAWN_RATE/sec"
        print_info "  Duration: $DURATION"
        print_info "  Scenario: $scenario"

        # Execute
        $cmd

        print_info "Test complete!"
        print_info "Results:"
        print_info "  HTML report: ${RESULT_FILE}.html"
        print_info "  CSV data: ${RESULT_FILE}_stats.csv"
        print_info "  Log file: ${RESULT_FILE}.log"
    fi
}

quick_test() {
    print_header "Quick Smoke Test"
    USERS=50
    SPAWN_RATE=5
    DURATION="2m"
    run_load_test "all" "false" ""
}

# Parse arguments
WEB_MODE=false
LOAD_SHAPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            DURATION="$2"
            shift 2
            ;;
        -s|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --web)
            WEB_MODE=true
            shift
            ;;
        --step)
            LOAD_SHAPE="step"
            shift
            ;;
        --spike)
            LOAD_SHAPE="spike"
            shift
            ;;
        --help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Main execution
print_header "CONTINUUM Load Testing Suite"

check_dependencies
prepare_results_dir
check_api_health

if [[ "$SCENARIO" == "quick" ]]; then
    quick_test
else
    run_load_test "$SCENARIO" "$WEB_MODE" "$LOAD_SHAPE"
fi

print_header "Load Test Complete"

# Summary
if [[ "$WEB_MODE" == "false" ]]; then
    echo ""
    print_info "To view results:"
    print_info "  HTML: open ${RESULT_FILE}.html"
    print_info "  CSV: cat ${RESULT_FILE}_stats.csv"
    print_info "  Log: cat ${RESULT_FILE}.log"
    echo ""
fi

exit 0
