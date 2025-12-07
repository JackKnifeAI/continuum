#!/usr/bin/env python3
"""
GraphQL Integration Script

Integrates GraphQL router into the main API server.
Run this after installing strawberry-graphql.
"""

import sys
from pathlib import Path

def integrate_graphql():
    """Add GraphQL router to main server"""

    server_file = Path(__file__).parent / "continuum" / "api" / "server.py"

    if not server_file.exists():
        print(f"ERROR: Server file not found: {server_file}")
        return False

    content = server_file.read_text()

    # Check if already integrated
    if "graphql" in content.lower() and "graphql_router" in content.lower():
        print("✓ GraphQL already integrated!")
        return True

    print("Integrating GraphQL into main server...")

    # Add import after other imports
    import_line = "from .graphql import create_graphql_app\n"

    # Find the line with billing_routes import
    lines = content.split('\n')
    new_lines = []
    import_added = False
    router_added = False
    banner_updated = False
    endpoints_updated = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Add import after billing_routes import
        if not import_added and "from .billing_routes import" in line:
            new_lines.append(import_line)
            import_added = True
            print("  ✓ Added GraphQL import")

        # Add router mount after billing router
        if not router_added and 'app.include_router(billing_router' in line:
            new_lines.append('')
            new_lines.append('# Mount GraphQL router')
            new_lines.append('try:')
            new_lines.append('    graphql_router = create_graphql_app(')
            new_lines.append('        enable_playground=True,')
            new_lines.append('        enable_subscriptions=True,')
            new_lines.append('        max_depth=10,')
            new_lines.append('        max_complexity=1000,')
            new_lines.append('    )')
            new_lines.append('    app.include_router(graphql_router, prefix="/graphql", tags=["GraphQL"])')
            new_lines.append('    print(f"GraphQL: http://localhost:8420/graphql")')
            new_lines.append('    print(f"Playground: http://localhost:8420/graphql")')
            new_lines.append('except ImportError as e:')
            new_lines.append('    print(f"GraphQL not available: {e}")')
            new_lines.append('    print("Install with: pip install strawberry-graphql[fastapi]")')
            router_added = True
            print("  ✓ Added GraphQL router mount")

        # Update endpoints dictionary
        if not endpoints_updated and '"websocket": "WS /ws/sync' in line:
            # Add GraphQL endpoints before websocket
            new_lines.insert(-1, '            "graphql": "POST /graphql - GraphQL API endpoint",')
            new_lines.insert(-1, '            "playground": "GET /graphql - GraphQL Playground (interactive)",')
            endpoints_updated = True
            print("  ✓ Updated endpoints dictionary")

    # Write updated content
    new_content = '\n'.join(new_lines)
    server_file.write_text(new_content)

    print("\n✓ GraphQL integration complete!")
    print("\nNext steps:")
    print("  1. Install strawberry: pip install strawberry-graphql[fastapi]")
    print("  2. Run server: python -m continuum.api.server")
    print("  3. Access GraphQL Playground: http://localhost:8420/graphql")

    return True


if __name__ == "__main__":
    success = integrate_graphql()
    sys.exit(0 if success else 1)
