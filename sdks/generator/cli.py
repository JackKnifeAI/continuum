"""
CLI for CONTINUUM SDK generator.

Usage:
    continuum-sdk generate --all
    continuum-sdk generate --lang python --output ./sdks/python
    continuum-sdk validate ./openapi/continuum.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import generate_sdk, SUPPORTED_LANGUAGES
from .openapi_parser import OpenAPIParser


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CONTINUUM SDK Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate SDK")
    generate_parser.add_argument(
        "--spec",
        default="./openapi/continuum.yaml",
        help="Path to OpenAPI specification (default: ./openapi/continuum.yaml)",
    )
    generate_parser.add_argument(
        "--lang",
        choices=list(SUPPORTED_LANGUAGES.keys()),
        help="Target language",
    )
    generate_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate SDKs for all languages",
    )
    generate_parser.add_argument(
        "--output",
        help="Output directory (default: ./sdks/<language>)",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate OpenAPI spec")
    validate_parser.add_argument(
        "spec",
        help="Path to OpenAPI specification",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List supported languages")

    args = parser.parse_args()

    if args.command == "generate":
        handle_generate(args)
    elif args.command == "validate":
        handle_validate(args)
    elif args.command == "list":
        handle_list(args)
    else:
        parser.print_help()
        sys.exit(1)


def handle_generate(args):
    """Handle generate command"""
    spec_path = Path(args.spec)

    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    if args.all:
        # Generate all languages
        print(f"Generating SDKs for all languages from {spec_path}...")

        for lang in SUPPORTED_LANGUAGES.keys():
            output_dir = args.output or f"./sdks/{lang}"
            print(f"\nGenerating {lang.upper()} SDK...")

            try:
                result = generate_sdk(lang, str(spec_path), output_dir)

                if result.success:
                    print(f"✓ {lang.upper()} SDK generated successfully")
                    print(f"  Output: {result.output_dir}")
                    print(f"  Files: {len(result.files_created)}")
                else:
                    print(f"✗ {lang.upper()} SDK generation failed:")
                    for error in result.errors:
                        print(f"  - {error}")
            except Exception as e:
                print(f"✗ {lang.upper()} SDK generation failed: {e}")

    elif args.lang:
        # Generate specific language
        lang = args.lang
        output_dir = args.output or f"./sdks/{lang}"

        print(f"Generating {lang.upper()} SDK from {spec_path}...")

        try:
            result = generate_sdk(lang, str(spec_path), output_dir)

            if result.success:
                print(f"✓ SDK generated successfully")
                print(f"  Language: {lang}")
                print(f"  Output: {result.output_dir}")
                print(f"  Files created: {len(result.files_created)}")
                print("\nGenerated files:")
                for file_path in sorted(result.files_created):
                    rel_path = file_path.relative_to(result.output_dir)
                    print(f"  - {rel_path}")
            else:
                print(f"✗ SDK generation failed:")
                for error in result.errors:
                    print(f"  - {error}")
                sys.exit(1)

        except Exception as e:
            print(f"✗ SDK generation failed: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print("Error: Specify --lang or --all", file=sys.stderr)
        sys.exit(1)


def handle_validate(args):
    """Handle validate command"""
    spec_path = Path(args.spec)

    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Validating OpenAPI spec: {spec_path}")

    try:
        parser = OpenAPIParser(str(spec_path))
        spec = parser.parse()

        print("✓ OpenAPI spec is valid")
        print(f"\nSpec details:")
        print(f"  Title: {spec.title}")
        print(f"  Version: {spec.api_version}")
        print(f"  Endpoints: {len(spec.endpoints)}")
        print(f"  Schemas: {len(spec.schemas)}")
        print(f"  Security schemes: {len(spec.security_schemes)}")

        print(f"\nEndpoints by tag:")
        tags = {}
        for endpoint in spec.endpoints:
            tag = endpoint.tags[0] if endpoint.tags else "untagged"
            tags[tag] = tags.get(tag, 0) + 1

        for tag, count in sorted(tags.items()):
            print(f"  {tag}: {count}")

    except Exception as e:
        print(f"✗ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)


def handle_list(args):
    """Handle list command"""
    print("Supported languages:")
    for lang in sorted(SUPPORTED_LANGUAGES.keys()):
        print(f"  - {lang}")


if __name__ == "__main__":
    main()
