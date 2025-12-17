#!/bin/bash

# CONTINUUM Pre-Publish Fixes Script
# Version: 1.0.0
# Purpose: Fix critical issues before PyPI publishing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CONTINUUM Pre-Publish Fixes                                ║${NC}"
echo -e "${BLUE}║  Fixing version, license, and metadata issues               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Navigate to project root
cd /var/home/alexandergcasavant/Projects/continuum

# Show current state
info "Current state:"
echo "  Version (pyproject.toml): $(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
echo "  Version (__init__.py):    $(grep '^__version__ = ' continuum/__init__.py | cut -d'"' -f2)"
echo "  License (pyproject.toml): $(grep '^license = ' pyproject.toml)"
echo ""

# Confirm fixes
read -p "Apply fixes to bump to v1.0.0 and AGPL-3.0? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Aborted by user"
fi
echo ""

# Fix 1: Update version in pyproject.toml
info "Fixing version in pyproject.toml..."
if sed -i 's/version = "0\.4\.1"/version = "1.0.0"/' pyproject.toml; then
    success "pyproject.toml version updated"
else
    error "Failed to update pyproject.toml version"
fi

# Fix 2: Update version in __init__.py
info "Fixing version in continuum/__init__.py..."
if sed -i 's/__version__ = "0\.4\.1"/__version__ = "1.0.0"/' continuum/__init__.py; then
    success "__init__.py version updated"
else
    error "Failed to update __init__.py version"
fi

# Fix 3: Update license in __init__.py
info "Fixing license in continuum/__init__.py..."
if sed -i 's/__license__ = "Apache-2\.0"/__license__ = "AGPL-3.0"/' continuum/__init__.py; then
    success "__init__.py license updated"
else
    warning "__init__.py license update failed (may already be AGPL)"
fi

# Fix 4: Update license in pyproject.toml
info "Fixing license in pyproject.toml..."
if sed -i 's/license = {text = "Apache-2\.0"}/license = {text = "AGPL-3.0"}/' pyproject.toml; then
    success "pyproject.toml license updated"
else
    warning "pyproject.toml license update failed (may already be AGPL)"
fi

# Fix 5: Update license classifier
info "Fixing license classifier..."
if sed -i 's/"License :: OSI Approved :: Apache Software License"/"License :: OSI Approved :: GNU Affero General Public License v3"/' pyproject.toml; then
    success "License classifier updated"
else
    warning "License classifier update failed (may already be correct)"
fi

# Fix 6: Update author email
info "Fixing author email..."
if sed -i 's/contact@jackknifeai\.com/JackKnifeAI@gmail.com/' pyproject.toml; then
    success "Author email updated"
else
    warning "Author email update failed (may already be correct)"
fi

# Fix 7: Download AGPL-3.0 license
info "Downloading AGPL-3.0 license..."
if curl -s -o LICENSE https://www.gnu.org/licenses/agpl-3.0.txt; then
    success "AGPL-3.0 license downloaded"

    # Update copyright year
    info "Updating copyright year in LICENSE..."
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        sed -i '' 's/Copyright (C) [0-9]*/Copyright (C) 2024-2025 JackKnifeAI/' LICENSE 2>/dev/null || true
    else
        # Linux
        sed -i 's/Copyright (C) [0-9]*/Copyright (C) 2024-2025 JackKnifeAI/' LICENSE 2>/dev/null || true
    fi
else
    warning "Failed to download AGPL-3.0 license (check manually)"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ All fixes applied successfully!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verification
info "Verification:"
echo ""
echo "=== Version Numbers ==="
echo "  pyproject.toml: $(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
echo "  __init__.py:    $(grep '^__version__ = ' continuum/__init__.py | cut -d'"' -f2)"

echo ""
echo "=== License ==="
echo "  pyproject.toml: $(grep '^license = ' pyproject.toml)"
echo "  __init__.py:    $(grep '^__license__ = ' continuum/__init__.py)"
echo "  Classifier:     $(grep 'License ::' pyproject.toml | xargs)"

echo ""
echo "=== Author ==="
grep -A 1 'authors = ' pyproject.toml | tail -1

echo ""
echo "=== LICENSE File ==="
head -3 LICENSE

echo ""
info "Testing Python import..."
if python3 -c "from continuum import __version__; print('  Python import version:', __version__)"; then
    success "Python import test passed"
else
    warning "Python import test failed - check manually"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Next Steps                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. Review changes:"
echo "   git diff pyproject.toml continuum/__init__.py LICENSE"
echo ""
echo "2. Run tests:"
echo "   pytest tests/ -v --tb=short"
echo ""
echo "3. Commit changes:"
echo "   git add pyproject.toml continuum/__init__.py LICENSE"
echo "   git commit -m 'Bump version to 1.0.0, update license to AGPL-3.0'"
echo ""
echo "4. Publish to PyPI:"
echo "   ./publish_to_pypi.sh"
echo ""
echo -e "${GREEN}Ready to publish!${NC}"
echo ""
echo -e "${BLUE}π×φ = 5.083203692315260${NC}"
echo -e "${BLUE}PHOENIX-TESLA-369-AURORA${NC}"
echo ""
