#!/bin/bash
#
# CONTINUUM Integration Test Runner
#
# Runs the full integration test suite with appropriate markers and options.
#
# Usage:
#   ./scripts/run_integration_tests.sh [OPTIONS]
#
# Options:
#   --verbose, -v     Increase verbosity
#   --fast            Skip slow tests
#   --coverage        Run with coverage reporting
#   --parallel        Run tests in parallel
#   --help, -h        Show this help message
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
VERBOSE=""
SKIP_SLOW=""
COVERAGE=""
PARALLEL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        --fast)
            SKIP_SLOW='-m "not slow"'
            shift
            ;;
        --coverage)
            COVERAGE="--cov=continuum --cov-report=html --cov-report=term"
            shift
            ;;
        --parallel)
            PARALLEL="-n auto"
            shift
            ;;
        -h|--help)
            echo "CONTINUUM Integration Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Increase verbosity (-vv)"
            echo "  --fast           Skip slow tests"
            echo "  --coverage       Run with coverage reporting"
            echo "  --parallel       Run tests in parallel (requires pytest-xdist)"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio"
    exit 1
fi

# Print header
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CONTINUUM Integration Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Check if tests directory exists
if [ ! -d "tests/integration" ]; then
    echo -e "${RED}ERROR: tests/integration directory not found${NC}"
    exit 1
fi

# Build pytest command
PYTEST_CMD="pytest tests/integration/"

# Add markers
PYTEST_CMD="$PYTEST_CMD -m integration"

# Add options
if [ -n "$VERBOSE" ]; then
    PYTEST_CMD="$PYTEST_CMD $VERBOSE"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ -n "$SKIP_SLOW" ]; then
    PYTEST_CMD="$PYTEST_CMD $SKIP_SLOW"
fi

if [ -n "$COVERAGE" ]; then
    PYTEST_CMD="$PYTEST_CMD $COVERAGE"
fi

if [ -n "$PARALLEL" ]; then
    if ! python -c "import xdist" 2>/dev/null; then
        echo -e "${YELLOW}WARNING: pytest-xdist not installed, skipping parallel execution${NC}"
        echo "Install with: pip install pytest-xdist"
    else
        PYTEST_CMD="$PYTEST_CMD $PARALLEL"
    fi
fi

# Add common options
PYTEST_CMD="$PYTEST_CMD --tb=short --color=yes"

# Print command
echo -e "${YELLOW}Running: $PYTEST_CMD${NC}"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Integration tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    exit $EXIT_CODE
fi
