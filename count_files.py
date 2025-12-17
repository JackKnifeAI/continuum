#!/usr/bin/env python3
"""Count files in restructured packages."""

from pathlib import Path

def count_python_files(directory):
    """Count Python files in a directory."""
    return len(list(Path(directory).rglob("*.py")))

def list_modules(directory):
    """List immediate subdirectories (modules)."""
    return sorted([d.name for d in Path(directory).iterdir() if d.is_dir() and not d.name.startswith("_")])

# Paths
oss_pkg = Path("/var/home/alexandergcasavant/Projects/continuum/packages/continuum-memory/continuum")
cloud_pkg = Path("/var/home/alexandergcasavant/Projects/continuum/packages/continuum-cloud/continuum_cloud")

# Count files
oss_count = count_python_files(oss_pkg)
cloud_count = count_python_files(cloud_pkg)

# List modules
oss_modules = list_modules(oss_pkg)
cloud_modules = list_modules(cloud_pkg)

print("CONTINUUM Package Restructure - File Counts")
print("=" * 60)
print()
print(f"OSS Package (continuum-memory):")
print(f"  Location: {oss_pkg}")
print(f"  Python files: {oss_count}")
print(f"  Modules: {', '.join(oss_modules)}")
print()
print(f"Cloud Package (continuum-cloud):")
print(f"  Location: {cloud_pkg}")
print(f"  Python files: {cloud_count}")
print(f"  Modules: {', '.join(cloud_modules)}")
print()
print(f"Total: {oss_count + cloud_count} Python files")
print()

# Check for key files
print("Key Files Check:")
print()

key_files = {
    "OSS": [
        (oss_pkg / "__init__.py", "__init__.py"),
        (oss_pkg / "core" / "memory.py", "core/memory.py"),
        (oss_pkg / "cli" / "main.py", "cli/main.py"),
        (oss_pkg / "mcp" / "server.py", "mcp/server.py"),
        (oss_pkg.parent / "pyproject.toml", "pyproject.toml"),
        (oss_pkg.parent / "README.md", "README.md"),
    ],
    "Cloud": [
        (cloud_pkg / "__init__.py", "__init__.py"),
        (cloud_pkg / "api" / "server.py", "api/server.py"),
        (cloud_pkg / "billing" / "stripe_client.py", "billing/stripe_client.py"),
        (cloud_pkg / "federation" / "server.py", "federation/server.py"),
        (cloud_pkg.parent / "pyproject.toml", "pyproject.toml"),
        (cloud_pkg.parent / "README.md", "README.md"),
    ],
}

for package, files in key_files.items():
    print(f"{package} Package:")
    for file_path, label in files:
        exists = "✓" if file_path.exists() else "✗"
        print(f"  {exists} {label}")
    print()
