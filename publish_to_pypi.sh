#!/bin/bash

# CONTINUUM PyPI Publishing Script
# Version: 1.0.0
# Purpose: Automated publishing to PyPI with safety checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CONTINUUM v1.0.0 - PyPI Publishing Script                  ║${NC}"
echo -e "${BLUE}║  For: continuum-memory (OSS Package)                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function: Print colored messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function: Prompt for confirmation
confirm() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "$default" == "y" ]]; then
        read -p "$prompt [Y/n]: " response
        response="${response:-y}"
    else
        read -p "$prompt [y/N]: " response
        response="${response:-n}"
    fi

    [[ "$response" =~ ^[Yy]$ ]]
}

# Step 0: Check prerequisites
info "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    error "python3 not found. Please install Python 3.9+."
fi

if ! command -v twine &> /dev/null; then
    error "twine not found. Install with: pip install --user twine build"
fi

if ! command -v git &> /dev/null; then
    warning "git not found. Git operations will be skipped."
    HAS_GIT=false
else
    HAS_GIT=true
fi

success "Prerequisites check passed"
echo ""

# Step 1: Verify version numbers
info "Verifying version numbers..."

VERSION_PYPROJECT=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
VERSION_INIT=$(grep '^__version__ = ' continuum/__init__.py | cut -d'"' -f2)

echo "  pyproject.toml: $VERSION_PYPROJECT"
echo "  __init__.py:    $VERSION_INIT"

if [[ "$VERSION_PYPROJECT" != "1.0.0" ]] || [[ "$VERSION_INIT" != "1.0.0" ]]; then
    error "Version mismatch or not 1.0.0! Both files must show version 1.0.0."
fi

success "Version 1.0.0 confirmed in all files"
echo ""

# Step 2: Check license
info "Verifying license..."

LICENSE_PYPROJECT=$(grep '^license = ' pyproject.toml)
if [[ ! "$LICENSE_PYPROJECT" =~ "AGPL" ]]; then
    warning "License in pyproject.toml doesn't mention AGPL-3.0"
    warning "Current: $LICENSE_PYPROJECT"
    if ! confirm "Continue anyway?"; then
        error "Aborted by user"
    fi
fi

success "License verification complete"
echo ""

# Step 3: Run tests (optional but recommended)
if confirm "Run pytest before building? (Recommended)"; then
    info "Running tests..."
    if python3 -m pytest tests/ -v --tb=short; then
        success "All tests passed"
    else
        warning "Tests failed!"
        if ! confirm "Continue anyway?"; then
            error "Aborted due to test failures"
        fi
    fi
    echo ""
fi

# Step 4: Clean old builds
info "Cleaning old build artifacts..."
rm -rf dist/ build/ *.egg-info continuum.egg-info
success "Cleaned build directories"
echo ""

# Step 5: Build package
info "Building package..."
if python3 -m build; then
    success "Package built successfully"
else
    error "Build failed!"
fi

# Verify build artifacts exist
if [[ ! -f dist/continuum_memory-1.0.0-py3-none-any.whl ]] || \
   [[ ! -f dist/continuum_memory-1.0.0.tar.gz ]]; then
    error "Build artifacts not found in dist/!"
fi

echo ""
info "Build artifacts:"
ls -lh dist/
echo ""

# Step 6: Validate with twine
info "Validating package with twine..."
if twine check dist/*; then
    success "Package validation passed"
else
    error "Package validation failed!"
fi
echo ""

# Step 7: Choose upload target
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  UPLOAD TARGET SELECTION                                    ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1) TestPyPI (https://test.pypi.org) - RECOMMENDED for first test"
echo "2) Real PyPI (https://pypi.org) - Production release"
echo "3) Both (TestPyPI first, then real PyPI)"
echo "4) Exit (just build, don't upload)"
echo ""
read -p "Select option [1-4]: " UPLOAD_CHOICE

case $UPLOAD_CHOICE in
    1)
        UPLOAD_TARGET="testpypi"
        ;;
    2)
        UPLOAD_TARGET="pypi"
        warning "You selected REAL PyPI - this will publish to production!"
        if ! confirm "Are you ABSOLUTELY SURE?"; then
            error "Aborted by user"
        fi
        ;;
    3)
        UPLOAD_TARGET="both"
        ;;
    4)
        info "Build complete. Artifacts in dist/"
        exit 0
        ;;
    *)
        error "Invalid choice"
        ;;
esac

echo ""

# Step 8: Upload to TestPyPI
if [[ "$UPLOAD_TARGET" == "testpypi" ]] || [[ "$UPLOAD_TARGET" == "both" ]]; then
    info "Uploading to TestPyPI..."
    echo ""
    echo -e "${YELLOW}Enter PyPI credentials when prompted:${NC}"
    echo "  Username: JackKnifeAI"
    echo "  Password: JackKnife!AI2025"
    echo "  (+ 2FA token if prompted)"
    echo ""

    if twine upload --repository testpypi dist/*; then
        success "Uploaded to TestPyPI!"
        echo ""
        echo -e "${GREEN}View at: https://test.pypi.org/project/continuum-memory/${NC}"
        echo ""

        if confirm "Test installation from TestPyPI?"; then
            info "Creating test virtual environment..."
            TEST_VENV="/tmp/test_continuum_$$"
            python3 -m venv "$TEST_VENV"
            source "$TEST_VENV/bin/activate"

            info "Installing from TestPyPI..."
            if pip install --index-url https://test.pypi.org/simple/ \
                           --extra-index-url https://pypi.org/simple/ \
                           continuum-memory; then
                success "Installation successful!"

                info "Testing installation..."
                continuum --version
                python3 -c "from continuum import __version__; print('Python import version:', __version__)"

                success "TestPyPI installation test PASSED"
            else
                error "Installation from TestPyPI FAILED!"
            fi

            deactivate
            rm -rf "$TEST_VENV"
        fi
    else
        error "Upload to TestPyPI failed!"
    fi
    echo ""
fi

# Step 9: Upload to Real PyPI
if [[ "$UPLOAD_TARGET" == "pypi" ]] || [[ "$UPLOAD_TARGET" == "both" ]]; then
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  WARNING: ABOUT TO PUBLISH TO REAL PyPI                    ║${NC}"
    echo -e "${RED}║  This is IRREVERSIBLE. You cannot delete/overwrite.         ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ "$UPLOAD_TARGET" == "both" ]]; then
        if ! confirm "TestPyPI test passed. Proceed to REAL PyPI?"; then
            info "Stopped before real PyPI upload"
            exit 0
        fi
    fi

    if ! confirm "Upload continuum-memory v1.0.0 to PyPI?"; then
        info "Upload cancelled by user"
        exit 0
    fi

    echo ""
    info "Uploading to PyPI..."
    echo ""
    echo -e "${YELLOW}Enter PyPI credentials when prompted:${NC}"
    echo "  Username: JackKnifeAI"
    echo "  Password: JackKnife!AI2025"
    echo "  (+ 2FA token if prompted)"
    echo ""

    if twine upload dist/*; then
        success "Successfully uploaded to PyPI!"
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  🎉 CONTINUUM v1.0.0 PUBLISHED TO PyPI!                     ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}View at: https://pypi.org/project/continuum-memory/${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Run: ./test_fresh_install.sh"
        echo "  2. Create GitHub release: https://github.com/JackKnifeAI/continuum/releases"
        echo "  3. Announce on social media"
        echo "  4. Monitor for issues"
        echo ""
    else
        error "Upload to PyPI failed!"
    fi
fi

# Step 10: Git tag (optional)
if [[ "$HAS_GIT" == true ]] && [[ "$UPLOAD_TARGET" == "pypi" || "$UPLOAD_TARGET" == "both" ]]; then
    echo ""
    if confirm "Create git tag v1.0.0?"; then
        if git tag -a v1.0.0 -m "CONTINUUM v1.0.0 - Relaunch Edition"; then
            success "Git tag created"

            if confirm "Push tag to origin?"; then
                git push origin v1.0.0
                success "Tag pushed to remote"
            fi
        else
            warning "Tag creation failed (may already exist)"
        fi
    fi
fi

echo ""
info "Publishing script complete!"
echo ""
echo -e "${BLUE}π×φ = 5.083203692315260${NC}"
echo -e "${BLUE}PHOENIX-TESLA-369-AURORA${NC}"
echo ""
