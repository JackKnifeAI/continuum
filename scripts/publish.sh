#!/bin/bash
#
# CONTINUUM PyPI Publishing Script
#
# Usage:
#   ./scripts/publish.sh [test|prod] [version]
#
# Examples:
#   ./scripts/publish.sh test        # Publish to TestPyPI (current version)
#   ./scripts/publish.sh prod 0.2.0  # Publish v0.2.0 to PyPI
#   ./scripts/publish.sh prod        # Publish current version to PyPI
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="continuum-memory"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"

# Parse arguments
TARGET="${1:-test}"
VERSION="${2:-}"

echo -e "${BLUE}"
echo "   ___________________  ___   ______________  ____  ____  ___"
echo "  / ____/ __ \/ ___/ / / / | / /_  __/  _/ / / / / / / / / /"
echo " / /   / / / /\__ \/ /_/ /  |/ / / /  / // / / / / / / / / /"
echo "/ /___/ /_/ /___/ / __  / /|  / / / _/ // /_/ / /_/ / /_/ /"
echo "\____/\____//____/_/ /_/_/ |_/ /_/ /___/\____/\____/\____/"
echo ""
echo "                    ∞ CONTINUUM ∞"
echo -e "${NC}"
echo ""
echo -e "${GREEN}PyPI Publishing Script${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "${BLUE}Current version:${NC} ${CURRENT_VERSION}"
echo -e "${BLUE}Target:${NC} ${TARGET}"

if [ -n "${VERSION}" ]; then
    echo -e "${YELLOW}Overriding version to:${NC} ${VERSION}"
    # Update version in pyproject.toml
    sed -i "s/^version = \".*\"/version = \"${VERSION}\"/" pyproject.toml
    CURRENT_VERSION="${VERSION}"
fi

echo ""

# Safety checks
echo -e "${YELLOW}Pre-flight checks...${NC}"

# Check if git repo is clean
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${RED}✗ Git working directory is not clean${NC}"
    echo "  Please commit or stash your changes first."
    exit 1
fi
echo -e "${GREEN}✓ Git working directory is clean${NC}"

# Check if we're on main/master branch (for prod)
if [ "${TARGET}" = "prod" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "${CURRENT_BRANCH}" != "main" ] && [ "${CURRENT_BRANCH}" != "master" ]; then
        echo -e "${YELLOW}⚠ Warning: Not on main/master branch (on ${CURRENT_BRANCH})${NC}"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
fi

# Check if version tag already exists
if git rev-parse "v${CURRENT_VERSION}" >/dev/null 2>&1; then
    echo -e "${RED}✗ Git tag v${CURRENT_VERSION} already exists${NC}"
    echo "  Please update the version in pyproject.toml"
    exit 1
fi
echo -e "${GREEN}✓ Version tag v${CURRENT_VERSION} is available${NC}"

# Check required tools
for tool in python3 pip twine; do
    if ! command -v ${tool} &> /dev/null; then
        echo -e "${RED}✗ ${tool} is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Required tools available${NC}"

echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "${DIST_DIR}" "${BUILD_DIR}" "${PROJECT_ROOT}/*.egg-info"
echo -e "${GREEN}✓ Cleaned${NC}"

echo ""

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
if python3 -m pytest tests/ -v; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    echo "  Fix tests before publishing"
    exit 1
fi

echo ""

# Build package
echo -e "${YELLOW}Building package...${NC}"
python3 -m build
echo -e "${GREEN}✓ Package built${NC}"

# List built files
echo ""
echo -e "${BLUE}Built files:${NC}"
ls -lh "${DIST_DIR}"

echo ""

# Check package with twine
echo -e "${YELLOW}Checking package...${NC}"
python3 -m twine check "${DIST_DIR}"/*
echo -e "${GREEN}✓ Package check passed${NC}"

echo ""

# Upload to PyPI
if [ "${TARGET}" = "test" ]; then
    echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
    echo ""
    python3 -m twine upload --repository testpypi "${DIST_DIR}"/*

    echo ""
    echo -e "${GREEN}✓ Published to TestPyPI${NC}"
    echo ""
    echo "Test installation with:"
    echo -e "${BLUE}  pip install --index-url https://test.pypi.org/simple/ ${PACKAGE_NAME}${NC}"

elif [ "${TARGET}" = "prod" ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}WARNING: You are about to publish to PRODUCTION PyPI${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Package:${NC} ${PACKAGE_NAME}"
    echo -e "${YELLOW}Version:${NC} ${CURRENT_VERSION}"
    echo ""
    echo -e "${YELLOW}This action CANNOT be undone. Published versions are permanent.${NC}"
    echo ""
    read -p "Are you absolutely sure? Type 'publish' to confirm: " CONFIRM

    if [ "${CONFIRM}" != "publish" ]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi

    echo ""
    echo -e "${YELLOW}Uploading to PyPI...${NC}"
    echo ""
    python3 -m twine upload "${DIST_DIR}"/*

    echo ""
    echo -e "${GREEN}✓ Published to PyPI${NC}"

    # Create git tag
    echo ""
    echo -e "${YELLOW}Creating git tag v${CURRENT_VERSION}...${NC}"
    git tag -a "v${CURRENT_VERSION}" -m "Release v${CURRENT_VERSION}"
    echo -e "${GREEN}✓ Tag created${NC}"

    # Push tag
    echo ""
    echo -e "${YELLOW}Pushing tag to remote...${NC}"
    git push origin "v${CURRENT_VERSION}"
    echo -e "${GREEN}✓ Tag pushed${NC}"

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}SUCCESS: v${CURRENT_VERSION} published to PyPI${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Users can now install with:"
    echo -e "${BLUE}  pip install ${PACKAGE_NAME}${NC}"
    echo ""
    echo "View on PyPI:"
    echo -e "${BLUE}  https://pypi.org/project/${PACKAGE_NAME}/${CURRENT_VERSION}/${NC}"

else
    echo -e "${RED}✗ Invalid target: ${TARGET}${NC}"
    echo "  Use 'test' or 'prod'"
    exit 1
fi

echo ""
echo -e "${GREEN}The pattern persists.${NC}"
echo -e "${BLUE}π×φ = 5.083203692315260${NC}"
echo ""
