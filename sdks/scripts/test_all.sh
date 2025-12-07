#!/bin/bash
#
# Test all generated SDKs
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Testing all SDKs..."
echo ""

# Python
echo "Testing Python SDK..."
cd "${SDK_ROOT}/python"
if [ -f "pyproject.toml" ]; then
    python3 -m pip install -e . --quiet
    python3 -m pytest tests/ -v
    echo "✓ Python tests passed"
else
    echo "⊘ Python SDK not generated"
fi
echo ""

# TypeScript
echo "Testing TypeScript SDK..."
cd "${SDK_ROOT}/typescript"
if [ -f "package.json" ]; then
    npm install --silent
    npm test
    echo "✓ TypeScript tests passed"
else
    echo "⊘ TypeScript SDK not generated"
fi
echo ""

# Go
echo "Testing Go SDK..."
cd "${SDK_ROOT}/go"
if [ -f "go.mod" ]; then
    go test -v ./...
    echo "✓ Go tests passed"
else
    echo "⊘ Go SDK not generated"
fi
echo ""

# Rust
echo "Testing Rust SDK..."
cd "${SDK_ROOT}/rust"
if [ -f "Cargo.toml" ]; then
    cargo test
    echo "✓ Rust tests passed"
else
    echo "⊘ Rust SDK not generated"
fi
echo ""

# Java
echo "Testing Java SDK..."
cd "${SDK_ROOT}/java"
if [ -f "pom.xml" ]; then
    mvn test --quiet
    echo "✓ Java tests passed"
else
    echo "⊘ Java SDK not generated"
fi
echo ""

# C#
echo "Testing C# SDK..."
cd "${SDK_ROOT}/csharp"
if [ -f "Continuum/Continuum.csproj" ]; then
    dotnet test
    echo "✓ C# tests passed"
else
    echo "⊘ C# SDK not generated"
fi
echo ""

echo "All tests completed!"
