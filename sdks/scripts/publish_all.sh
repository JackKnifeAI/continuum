#!/bin/bash
#
# Publish all SDKs to package managers
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_ROOT="$(dirname "$SCRIPT_DIR")"

VERSION=${1:-"0.3.0"}

echo "Publishing CONTINUUM SDKs v${VERSION}..."
echo ""

# Python - PyPI
echo "Publishing Python SDK to PyPI..."
cd "${SDK_ROOT}/python"
if [ -f "pyproject.toml" ]; then
    python3 -m build
    python3 -m twine upload dist/*
    echo "✓ Python SDK published to PyPI"
else
    echo "⊘ Python SDK not found"
fi
echo ""

# TypeScript - npm
echo "Publishing TypeScript SDK to npm..."
cd "${SDK_ROOT}/typescript"
if [ -f "package.json" ]; then
    npm publish
    echo "✓ TypeScript SDK published to npm"
else
    echo "⊘ TypeScript SDK not found"
fi
echo ""

# Go - GitHub (tag)
echo "Publishing Go SDK to GitHub..."
cd "${SDK_ROOT}/go"
if [ -f "go.mod" ]; then
    git tag "v${VERSION}"
    git push origin "v${VERSION}"
    echo "✓ Go SDK published (GitHub tag v${VERSION})"
else
    echo "⊘ Go SDK not found"
fi
echo ""

# Rust - crates.io
echo "Publishing Rust SDK to crates.io..."
cd "${SDK_ROOT}/rust"
if [ -f "Cargo.toml" ]; then
    cargo publish
    echo "✓ Rust SDK published to crates.io"
else
    echo "⊘ Rust SDK not found"
fi
echo ""

# Java - Maven Central
echo "Publishing Java SDK to Maven Central..."
cd "${SDK_ROOT}/java"
if [ -f "pom.xml" ]; then
    mvn clean deploy
    echo "✓ Java SDK published to Maven Central"
else
    echo "⊘ Java SDK not found"
fi
echo ""

# C# - NuGet
echo "Publishing C# SDK to NuGet..."
cd "${SDK_ROOT}/csharp"
if [ -f "Continuum/Continuum.csproj" ]; then
    dotnet pack Continuum/Continuum.csproj -c Release
    dotnet nuget push Continuum/bin/Release/*.nupkg --source https://api.nuget.org/v3/index.json
    echo "✓ C# SDK published to NuGet"
else
    echo "⊘ C# SDK not found"
fi
echo ""

echo "All SDKs published successfully!"
echo ""
echo "Published packages:"
echo "  - Python: https://pypi.org/project/continuum/${VERSION}/"
echo "  - TypeScript: https://www.npmjs.com/package/continuum"
echo "  - Go: https://pkg.go.dev/github.com/JackKnifeAI/continuum-go@v${VERSION}"
echo "  - Rust: https://crates.io/crates/continuum"
echo "  - Java: https://central.sonatype.com/artifact/ai.continuum/continuum-java/${VERSION}"
echo "  - C#: https://www.nuget.org/packages/Continuum/${VERSION}"
