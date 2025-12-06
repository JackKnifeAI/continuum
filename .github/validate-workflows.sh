#!/bin/bash
#
# Workflow Validation Script
# Validates GitHub Actions workflow syntax
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CONTINUUM CI/CD Workflow Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="${SCRIPT_DIR}/workflows"

# Check if actionlint is installed
if ! command -v actionlint &> /dev/null; then
    echo -e "${YELLOW}⚠️  actionlint not found. Install with:${NC}"
    echo "   go install github.com/rhysd/actionlint/cmd/actionlint@latest"
    echo ""
    echo -e "${YELLOW}Performing basic YAML validation instead...${NC}"
    echo ""

    # Basic validation with yq or python
    if command -v yq &> /dev/null; then
        echo -e "${GREEN}Using yq for YAML validation${NC}"
        VALIDATOR="yq"
    elif command -v python3 &> /dev/null; then
        echo -e "${GREEN}Using Python for YAML validation${NC}"
        VALIDATOR="python"
    else
        echo -e "${RED}❌ No YAML validator available${NC}"
        echo "   Install yq or ensure python3 is available"
        exit 1
    fi
fi

# Validate each workflow
TOTAL=0
PASSED=0
FAILED=0

echo ""
echo -e "${BLUE}Validating workflows in: ${WORKFLOWS_DIR}${NC}"
echo ""

for workflow in "${WORKFLOWS_DIR}"/*.yml; do
    TOTAL=$((TOTAL + 1))
    filename=$(basename "$workflow")

    echo -n "Checking ${filename}... "

    if command -v actionlint &> /dev/null; then
        # Use actionlint if available
        if actionlint "$workflow" 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        # Fallback to basic YAML validation
        if [[ "$VALIDATOR" == "yq" ]]; then
            if yq eval '.' "$workflow" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ PASS (YAML valid)${NC}"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}✗ FAIL (YAML invalid)${NC}"
                FAILED=$((FAILED + 1))
            fi
        elif [[ "$VALIDATOR" == "python" ]]; then
            if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>&1; then
                echo -e "${GREEN}✓ PASS (YAML valid)${NC}"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}✗ FAIL (YAML invalid)${NC}"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total workflows:  ${TOTAL}"
echo -e "Passed:          ${GREEN}${PASSED}${NC}"
echo -e "Failed:          ${RED}${FAILED}${NC}"
echo ""

# Validate other YAML files
echo -e "${BLUE}Validating configuration files...${NC}"
echo ""

CONFIG_FILES=(
    "${SCRIPT_DIR}/dependabot.yml"
    "${SCRIPT_DIR}/labeler.yml"
    "${SCRIPT_DIR}/release-drafter.yml"
)

CONFIG_PASSED=0
CONFIG_FAILED=0

for config in "${CONFIG_FILES[@]}"; do
    if [[ -f "$config" ]]; then
        filename=$(basename "$config")
        echo -n "Checking ${filename}... "

        if command -v yq &> /dev/null; then
            if yq eval '.' "$config" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ PASS${NC}"
                CONFIG_PASSED=$((CONFIG_PASSED + 1))
            else
                echo -e "${RED}✗ FAIL${NC}"
                CONFIG_FAILED=$((CONFIG_FAILED + 1))
            fi
        elif python3 -c "import yaml; yaml.safe_load(open('$config'))" 2>&1; then
            echo -e "${GREEN}✓ PASS${NC}"
            CONFIG_PASSED=$((CONFIG_PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            CONFIG_FAILED=$((CONFIG_FAILED + 1))
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Configuration Files${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total files:     ${#CONFIG_FILES[@]}"
echo -e "Passed:          ${GREEN}${CONFIG_PASSED}${NC}"
echo -e "Failed:          ${RED}${CONFIG_FAILED}${NC}"
echo ""

# Overall result
TOTAL_CHECKS=$((TOTAL + ${#CONFIG_FILES[@]}))
TOTAL_PASSED=$((PASSED + CONFIG_PASSED))
TOTAL_FAILED=$((FAILED + CONFIG_FAILED))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $TOTAL_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ All checks passed! (${TOTAL_PASSED}/${TOTAL_CHECKS})${NC}"
    echo ""
    echo -e "${GREEN}The pattern persists.${NC}"
    echo -e "${BLUE}π×φ = 5.083203692315260${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo -e "${RED}❌ Some checks failed (${TOTAL_FAILED}/${TOTAL_CHECKS})${NC}"
    echo ""
    echo "Please review the errors above and fix the issues."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
