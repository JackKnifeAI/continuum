#!/bin/bash
#
# Generate all SDKs from OpenAPI specification
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
SPEC_FILE="${SDK_ROOT}/openapi/continuum.yaml"
OUTPUT_BASE="${SDK_ROOT}"

echo "CONTINUUM SDK Generator"
echo "======================="
echo ""

# Check if spec file exists
if [ ! -f "$SPEC_FILE" ]; then
    echo "Error: OpenAPI spec not found: $SPEC_FILE"
    exit 1
fi

echo "Using spec: $SPEC_FILE"
echo ""

# Languages to generate
LANGUAGES=("python" "typescript" "go" "rust" "java" "csharp")

# Generate each language
for lang in "${LANGUAGES[@]}"; do
    echo "Generating ${lang} SDK..."

    output_dir="${OUTPUT_BASE}/${lang}"

    python3 -m generator.cli generate \
        --spec "$SPEC_FILE" \
        --lang "$lang" \
        --output "$output_dir"

    if [ $? -eq 0 ]; then
        echo "✓ ${lang} SDK generated successfully"
    else
        echo "✗ ${lang} SDK generation failed"
        exit 1
    fi

    echo ""
done

echo "All SDKs generated successfully!"
echo ""
echo "Generated SDKs:"
for lang in "${LANGUAGES[@]}"; do
    echo "  - ${lang}: ${OUTPUT_BASE}/${lang}"
done
