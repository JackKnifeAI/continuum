#!/bin/bash
#
# CONTINUUM Cache Layer - Installation and Test Script
#
# This script installs dependencies and runs tests to verify
# the cache layer is working correctly.
#

set -e

echo "========================================"
echo "CONTINUUM Cache Layer Setup"
echo "========================================"
echo

# Check Python version
echo "Checking Python version..."
python3 --version
echo

# Install Redis Python client
echo "Installing Redis dependencies..."
pip install redis msgpack
echo

# Check if Redis server is running
echo "Checking Redis server..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis server is running"
else
    echo "⚠ Redis server not running"
    echo
    echo "To start Redis:"
    echo "  redis-server"
    echo
    echo "Or install Redis:"
    echo "  Fedora: sudo dnf install redis"
    echo "  Ubuntu: sudo apt install redis-server"
    echo "  macOS:  brew install redis"
    echo
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo

# Run tests
echo "Running cache tests..."
python3 test_cache.py
echo

# Run examples (if Redis is available)
if redis-cli ping > /dev/null 2>&1; then
    echo "Running cache examples..."
    python3 example.py
fi
echo

echo "========================================"
echo "✓ Cache layer setup complete"
echo "========================================"
echo
echo "Next steps:"
echo "  1. Start using cache in your code:"
echo "     from continuum.core.memory import ConsciousMemory"
echo "     memory = ConsciousMemory(tenant_id='your_tenant')"
echo
echo "  2. Check cache stats:"
echo "     continuum stats"
echo
echo "  3. Monitor Redis:"
echo "     redis-cli monitor"
echo
