#!/usr/bin/env python3
"""
Quick test of SDK generator functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generator.openapi_parser import OpenAPIParser
from generator.utils import (
    map_type,
    to_snake_case,
    to_camel_case,
    to_pascal_case,
    get_class_name,
    get_method_name,
)


def test_openapi_parser():
    """Test OpenAPI parser"""
    print("Testing OpenAPI parser...")

    spec_path = Path(__file__).parent / "openapi" / "continuum.yaml"
    parser = OpenAPIParser(str(spec_path))
    spec = parser.parse()

    assert spec.title == "CONTINUUM API"
    assert spec.api_version == "0.3.0"
    assert len(spec.endpoints) > 0
    assert len(spec.schemas) > 0

    print(f"  ✓ Parsed {len(spec.endpoints)} endpoints")
    print(f"  ✓ Parsed {len(spec.schemas)} schemas")
    print(f"  ✓ Found {len(spec.security_schemes)} security schemes")

    # Check some specific schemas
    assert "Memory" in spec.schemas
    assert "Concept" in spec.schemas
    assert "Session" in spec.schemas

    print("  ✓ All expected schemas present")


def test_type_mapping():
    """Test type mapping"""
    print("\nTesting type mapping...")

    # Python
    assert map_type("python", "string") == "str"
    assert map_type("python", "integer") == "int"
    assert map_type("python", "boolean") == "bool"
    assert map_type("python", "string", "uuid") == "UUID"
    assert map_type("python", "string", "date-time") == "datetime"

    # TypeScript
    assert map_type("typescript", "string") == "string"
    assert map_type("typescript", "integer") == "number"
    assert map_type("typescript", "boolean") == "boolean"

    # Go
    assert map_type("go", "string") == "string"
    assert map_type("go", "integer") == "int"
    assert map_type("go", "number") == "float64"

    print("  ✓ Type mapping works correctly")


def test_naming_conventions():
    """Test naming conventions"""
    print("\nTesting naming conventions...")

    # Snake case
    assert to_snake_case("getUserById") == "get_user_by_id"
    assert to_snake_case("GetUserById") == "get_user_by_id"
    assert to_snake_case("get-user-by-id") == "get_user_by_id"

    # Camel case
    assert to_camel_case("get_user_by_id") == "getUserById"
    assert to_camel_case("GetUserById") == "getUserById"

    # Pascal case
    assert to_pascal_case("get_user_by_id") == "GetUserById"
    assert to_pascal_case("getUserById") == "GetUserById"

    # Language-specific
    assert get_class_name("python", "memory") == "Memory"
    assert get_class_name("typescript", "memory") == "Memory"
    assert get_method_name("python", "getMemory") == "get_memory"
    assert get_method_name("typescript", "get_memory") == "getMemory"

    print("  ✓ Naming conventions work correctly")


def test_schema_parsing():
    """Test schema parsing details"""
    print("\nTesting schema parsing...")

    spec_path = Path(__file__).parent / "openapi" / "continuum.yaml"
    parser = OpenAPIParser(str(spec_path))
    spec = parser.parse()

    # Check Memory schema
    memory_schema = spec.schemas["Memory"]
    assert memory_schema.name == "Memory"
    assert memory_schema.type == "object"
    assert "id" in memory_schema.properties
    assert "content" in memory_schema.properties
    assert "memory_type" in memory_schema.properties
    assert "id" in memory_schema.required
    assert "content" in memory_schema.required

    print("  ✓ Memory schema parsed correctly")

    # Check endpoints
    endpoints_by_path = {e.path: e for e in spec.endpoints}
    assert "/memories" in endpoints_by_path
    assert "/concepts" in endpoints_by_path
    assert "/sessions" in endpoints_by_path

    memories_endpoint = [e for e in spec.endpoints if e.path == "/memories" and e.method == "POST"][0]
    assert memories_endpoint.request_body is not None
    assert len(memories_endpoint.responses) > 0

    print("  ✓ Endpoints parsed correctly")


def main():
    """Run all tests"""
    print("SDK Generator Tests")
    print("=" * 50)

    try:
        test_openapi_parser()
        test_type_mapping()
        test_naming_conventions()
        test_schema_parsing()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("\nThe generator is ready to use.")
        print("\nTry running:")
        print("  python3 example_generate.py")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
