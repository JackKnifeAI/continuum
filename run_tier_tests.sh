#!/bin/bash
# Run integration tests for FREE, PRO, ENTERPRISE tier workflows
# This script will show which tests pass, fail, or are skipped

cd /var/home/alexandergcasavant/Projects/continuum

echo "========================================================================="
echo "CONTINUUM v1.0.0 - Tier Integration Test Runner"
echo "========================================================================="
echo ""

# Run tests with verbose output and capture results
PYTHONPATH=. pytest \
    tests/integration/test_free_tier_workflow.py \
    tests/integration/test_pro_tier_workflow.py \
    tests/integration/test_enterprise_tier_workflow.py \
    tests/integration/test_tier_upgrades.py \
    -v \
    --tb=short \
    --color=yes \
    2>&1 | tee tier_test_results.txt

echo ""
echo "========================================================================="
echo "Test Results Summary"
echo "========================================================================="
echo ""

# Count results
PASSED=$(grep -c "PASSED" tier_test_results.txt || echo "0")
FAILED=$(grep -c "FAILED" tier_test_results.txt || echo "0")
SKIPPED=$(grep -c "SKIPPED" tier_test_results.txt || echo "0")

echo "PASSED:  $PASSED"
echo "FAILED:  $FAILED"
echo "SKIPPED: $SKIPPED"
echo ""

# Show percentage
if [ "$SKIPPED" -gt 0 ]; then
    echo "WARNING: $SKIPPED tests are still skipped!"
    echo ""
    echo "Skipped tests:"
    grep "SKIPPED" tier_test_results.txt
fi

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "Failed tests:"
    grep "FAILED" tier_test_results.txt
fi

echo ""
echo "Full results saved to: tier_test_results.txt"
