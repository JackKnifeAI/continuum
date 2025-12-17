#!/usr/bin/env python3
"""
Update import paths in continuum-cloud package.

Changes imports from:
  - from continuum.api import X → from continuum_cloud.api import X
  - from continuum.billing import X → from continuum_cloud.billing import X
  etc.

Keeps imports from core modules unchanged:
  - from continuum.core import X (stays the same - dependency)
"""

import re
from pathlib import Path

# Modules that moved to continuum_cloud
CLOUD_MODULES = [
    "api",
    "billing",
    "federation",
    "compliance",
    "webhooks",
    "observability",
    "bridges",
    "realtime",
    "backup",
    "cache",
    "identity",
]

# OSS modules that stay as continuum imports (dependencies)
OSS_MODULES = [
    "core",
    "cli",
    "mcp",
    "extraction",
    "coordination",
    "embeddings",
]


def update_file_imports(file_path: Path) -> int:
    """Update imports in a single Python file. Returns number of changes."""
    content = file_path.read_text()
    original = content
    changes = 0

    # Update imports for cloud modules
    for module in CLOUD_MODULES:
        # Pattern 1: from continuum.MODULE import X
        pattern1 = rf"from continuum\.{module}(\.\S+)? import"
        replacement1 = rf"from continuum_cloud.{module}\1 import"
        content, count = re.subn(pattern1, replacement1, content)
        changes += count

        # Pattern 2: import continuum.MODULE
        pattern2 = rf"import continuum\.{module}(\.\S+)?"
        replacement2 = rf"import continuum_cloud.{module}\1"
        count2 = len(re.findall(pattern2, content))
        content = re.sub(pattern2, replacement2, content)
        changes += count2

    # Write back if changed
    if content != original:
        file_path.write_text(content)
        return changes

    return 0


def main():
    """Update all imports in continuum-cloud package."""
    cloud_pkg = Path("/var/home/alexandergcasavant/Projects/continuum/packages/continuum-cloud/continuum_cloud")

    if not cloud_pkg.exists():
        print(f"ERROR: {cloud_pkg} does not exist!")
        return 1

    print("Updating import paths in continuum-cloud package...")
    print(f"Package path: {cloud_pkg}")
    print()

    total_files = 0
    total_changes = 0

    # Process all Python files
    for py_file in cloud_pkg.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        changes = update_file_imports(py_file)
        if changes > 0:
            total_files += 1
            total_changes += changes
            rel_path = py_file.relative_to(cloud_pkg)
            print(f"  ✓ {rel_path} ({changes} changes)")

    print()
    print(f"Updated {total_changes} imports across {total_files} files")
    print()
    print("Note: Imports from continuum.core, continuum.storage, etc. remain unchanged")
    print("      (these are dependencies from the OSS package)")

    return 0


if __name__ == "__main__":
    exit(main())
