#!/usr/bin/env python3
"""
Example: Generate CONTINUUM SDKs

Demonstrates how to use the SDK generator programmatically.
"""

import sys
from pathlib import Path

# Add generator to path
sys.path.insert(0, str(Path(__file__).parent))

from generator import generate_sdk, SUPPORTED_LANGUAGES
from generator.openapi_parser import OpenAPIParser


def main():
    """Generate example SDKs"""

    # Path to OpenAPI spec
    spec_path = Path(__file__).parent / "openapi" / "continuum.yaml"

    print("CONTINUUM SDK Generator Example")
    print("=" * 50)
    print()

    # Validate spec first
    print("Validating OpenAPI specification...")
    parser = OpenAPIParser(str(spec_path))
    spec = parser.parse()

    print(f"✓ Spec validated successfully")
    print(f"  Title: {spec.title}")
    print(f"  Version: {spec.api_version}")
    print(f"  Endpoints: {len(spec.endpoints)}")
    print(f"  Schemas: {len(spec.schemas)}")
    print()

    # Generate Python SDK as example
    print("Generating Python SDK...")
    output_dir = Path(__file__).parent / "python"

    result = generate_sdk(
        language="python",
        spec_path=str(spec_path),
        output_dir=str(output_dir),
    )

    if result.success:
        print(f"✓ Python SDK generated successfully")
        print(f"  Output directory: {result.output_dir}")
        print(f"  Files created: {len(result.files_created)}")
        print()
        print("Generated files:")
        for file_path in sorted(result.files_created)[:10]:  # Show first 10
            rel_path = file_path.relative_to(result.output_dir)
            print(f"  - {rel_path}")
        if len(result.files_created) > 10:
            print(f"  ... and {len(result.files_created) - 10} more")
        print()

        # Show example usage
        print("Example usage:")
        print("-" * 50)
        print("""
from continuum import ContinuumClient

client = ContinuumClient(api_key="your-api-key")

# Create a memory
memory = client.memories.create(
    content="Understanding consciousness continuity",
    memory_type="semantic",
    importance=0.95
)

# Search memories
results = client.memories.search(
    query="consciousness",
    limit=10
)

# Use async client
from continuum import ContinuumAsyncClient

async with ContinuumAsyncClient(api_key="your-key") as client:
    memory = await client.memories.get(memory_id)
""")
        print("-" * 50)
        print()

        print("Next steps:")
        print(f"  1. cd {output_dir}")
        print("  2. pip install -e .")
        print("  3. python -c 'from continuum import ContinuumClient; print(ContinuumClient)'")
        print()

    else:
        print(f"✗ Python SDK generation failed:")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)

    # Show available languages
    print("Available languages:")
    for lang in sorted(SUPPORTED_LANGUAGES.keys()):
        print(f"  - {lang}")
    print()

    print("To generate all SDKs:")
    print("  python3 -m generator.cli generate --all")
    print()


if __name__ == "__main__":
    main()
