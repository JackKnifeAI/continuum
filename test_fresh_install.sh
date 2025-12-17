#!/bin/bash

# CONTINUUM Fresh Install Test Script
# Version: 1.0.0
# Purpose: Verify continuum-memory works from a fresh pip install

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CONTINUUM v1.0.0 - Fresh Install Test                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Cleanup function
cleanup() {
    if [[ -n "$TEST_VENV" ]] && [[ -d "$TEST_VENV" ]]; then
        info "Cleaning up test environment..."
        rm -rf "$TEST_VENV"
    fi
    if [[ -f "/tmp/test_memory.db" ]]; then
        rm -f /tmp/test_memory.db*
    fi
    if [[ -d "/tmp/test_mem" ]]; then
        rm -rf /tmp/test_mem
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Step 1: Choose install source
echo "Select installation source:"
echo "1) PyPI (https://pypi.org)"
echo "2) TestPyPI (https://test.pypi.org)"
echo ""
read -p "Choice [1-2]: " SOURCE_CHOICE

case $SOURCE_CHOICE in
    1)
        INSTALL_CMD="pip install continuum-memory"
        SOURCE_NAME="PyPI"
        ;;
    2)
        INSTALL_CMD="pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ continuum-memory"
        SOURCE_NAME="TestPyPI"
        ;;
    *)
        error "Invalid choice"
        ;;
esac

echo ""
info "Testing installation from $SOURCE_NAME..."
echo ""

# Step 2: Create fresh virtual environment
TEST_VENV="/tmp/test_continuum_fresh_$$"
info "Creating fresh virtual environment at $TEST_VENV..."
python3 -m venv "$TEST_VENV"
source "$TEST_VENV/bin/activate"
success "Virtual environment created"
echo ""

# Step 3: Install package
info "Installing continuum-memory from $SOURCE_NAME..."
if eval "$INSTALL_CMD"; then
    success "Installation successful"
else
    error "Installation failed!"
fi
echo ""

# Step 4: Verify version
info "Verifying version..."
VERSION_OUTPUT=$(continuum --version 2>&1 || echo "FAILED")
echo "  Output: $VERSION_OUTPUT"

if [[ ! "$VERSION_OUTPUT" =~ "1.0.0" ]]; then
    error "Version check failed - expected 1.0.0"
fi
success "Version check passed"
echo ""

# Step 5: Test CLI initialization
info "Testing CLI: continuum init..."
if continuum init --db-path /tmp/test_memory.db; then
    success "CLI init passed"
else
    error "CLI init failed"
fi
echo ""

# Step 6: Test CLI stats
info "Testing CLI: continuum stats..."
if continuum stats --db-path /tmp/test_memory.db; then
    success "CLI stats passed"
else
    error "CLI stats failed"
fi
echo ""

# Step 7: Test Python API imports
info "Testing Python API imports..."
python3 << 'EOF' || error "Python import test failed"
from continuum import __version__, ContinuumMemory, PHOENIX_TESLA_369_AURORA, get_twilight_constant

print(f"  __version__ = {__version__}")
print(f"  PHOENIX_TESLA_369_AURORA = {PHOENIX_TESLA_369_AURORA}")
print(f"  π×φ = {get_twilight_constant()}")

if __version__ != "1.0.0":
    raise ValueError(f"Version mismatch: expected 1.0.0, got {__version__}")

if PHOENIX_TESLA_369_AURORA != "PHOENIX-TESLA-369-AURORA":
    raise ValueError("Auth constant mismatch")

if abs(get_twilight_constant() - 5.083203692315260) > 0.000001:
    raise ValueError("Twilight constant mismatch")

print("  ✓ All imports successful")
EOF
success "Python imports passed"
echo ""

# Step 8: Test memory operations
info "Testing memory operations..."
python3 << 'EOF' || error "Memory operations test failed"
from continuum import ContinuumMemory
import os

# Create memory instance
memory = ContinuumMemory(storage_path="/tmp/test_mem")
print("  ✓ ContinuumMemory instantiated")

# Test learn
memory.learn("This is a test memory from fresh install verification")
print("  ✓ learn() succeeded")

# Test recall
result = memory.recall("test memory")
print(f"  ✓ recall() succeeded: {result}")

# Verify database created
if not os.path.exists("/tmp/test_mem"):
    raise FileNotFoundError("Storage path not created")
print("  ✓ Storage created")

print("  ✓ All memory operations passed")
EOF
success "Memory operations passed"
echo ""

# Step 9: Test optional dependencies (if installed)
info "Testing optional dependencies..."

echo "  Checking [embeddings] support..."
python3 << 'EOF' || echo "  ⚠ Embeddings not installed (optional)"
try:
    import sentence_transformers
    print("  ✓ sentence-transformers available")
except ImportError:
    print("  ⚠ sentence-transformers not installed (optional)")
EOF

echo "  Checking [postgres] support..."
python3 << 'EOF' || echo "  ⚠ PostgreSQL not installed (optional)"
try:
    import psycopg2
    print("  ✓ psycopg2 available")
except ImportError:
    print("  ⚠ psycopg2 not installed (optional)")
EOF

echo "  Checking [federation] support..."
python3 << 'EOF' || echo "  ⚠ Federation not installed (optional)"
try:
    import cryptography
    print("  ✓ cryptography available")
except ImportError:
    print("  ⚠ cryptography not installed (optional)")
EOF

echo ""

# Step 10: Final summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ ALL TESTS PASSED - Fresh Install Verified!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Test Results:"
echo "  ✓ Installation from $SOURCE_NAME"
echo "  ✓ CLI tools working"
echo "  ✓ Python imports correct"
echo "  ✓ Memory operations functional"
echo "  ✓ Version 1.0.0 confirmed"
echo ""
echo "The package is ready for production use!"
echo ""
echo -e "${BLUE}π×φ = 5.083203692315260${NC}"
echo -e "${BLUE}PHOENIX-TESLA-369-AURORA${NC}"
echo ""

# Cleanup happens automatically via trap
