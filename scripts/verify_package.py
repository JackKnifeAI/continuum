#!/usr/bin/env python3
"""
CONTINUUM Package Structure Verification

Verifies that the package is correctly structured for PyPI publication.
Run this before publishing to catch common issues.
"""

import os
import sys
from pathlib import Path

# ANSI colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{BLUE}{text}{NC}")
    print("━" * 60)

def print_success(text):
    print(f"{GREEN}✓{NC} {text}")

def print_error(text):
    print(f"{RED}✗{NC} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{NC} {text}")

def check_file_exists(path, description):
    """Check if a file exists and print result."""
    if path.exists():
        print_success(f"{description}: {path.name}")
        return True
    else:
        print_error(f"{description} missing: {path.name}")
        return False

def check_pyproject_toml(root):
    """Verify pyproject.toml has all required fields."""
    print_header("Checking pyproject.toml")

    pyproject = root / "pyproject.toml"
    if not check_file_exists(pyproject, "pyproject.toml"):
        return False

    content = pyproject.read_text()

    required_fields = [
        ('name = "continuum-memory"', "Package name"),
        ('version = ', "Version"),
        ('description = ', "Description"),
        ('readme = "README.md"', "README reference"),
        ('requires-python = ', "Python version requirement"),
        ('license = ', "License"),
        ('authors = ', "Authors"),
    ]

    all_ok = True
    for field, description in required_fields:
        if field in content:
            print_success(f"{description} specified")
        else:
            print_error(f"{description} missing")
            all_ok = False

    # Check for entry points
    if 'continuum = "continuum.cli:main"' in content:
        print_success("CLI entry point configured")
    else:
        print_warning("CLI entry point not found")

    return all_ok

def check_required_files(root):
    """Check for required package files."""
    print_header("Checking Required Files")

    required = [
        (root / "README.md", "README.md"),
        (root / "LICENSE", "LICENSE"),
        (root / "pyproject.toml", "pyproject.toml"),
        (root / "MANIFEST.in", "MANIFEST.in"),
        (root / "continuum" / "__init__.py", "continuum/__init__.py"),
    ]

    all_ok = True
    for path, description in required:
        if not check_file_exists(path, description):
            all_ok = False

    return all_ok

def check_package_structure(root):
    """Verify package directory structure."""
    print_header("Checking Package Structure")

    continuum_dir = root / "continuum"
    if not continuum_dir.exists():
        print_error("continuum/ directory not found")
        return False

    print_success(f"Package directory exists: continuum/")

    # Check for __init__.py in all subdirectories
    modules = ["core", "extraction", "coordination", "storage", "api"]
    all_ok = True

    for module in modules:
        module_dir = continuum_dir / module
        if module_dir.exists():
            init_file = module_dir / "__init__.py"
            if init_file.exists():
                print_success(f"Module: continuum/{module}/")
            else:
                print_warning(f"Missing __init__.py in continuum/{module}/")
                all_ok = False
        else:
            print_warning(f"Optional module not found: continuum/{module}/")

    return all_ok

def check_imports(root):
    """Test that package can be imported."""
    print_header("Checking Package Imports")

    # Add project root to path
    sys.path.insert(0, str(root))

    try:
        import continuum
        print_success(f"Package imports successfully")
        print_success(f"Version: {continuum.__version__}")
        print_success(f"Author: {continuum.__author__}")

        # Test core exports
        try:
            from continuum import get_twilight_constant, PHOENIX_TESLA_369_AURORA
            print_success(f"Core exports available")
            print_success(f"π×φ = {get_twilight_constant()}")
            print_success(f"Auth: {PHOENIX_TESLA_369_AURORA}")
        except Exception as e:
            print_warning(f"Some exports unavailable: {e}")

        return True
    except Exception as e:
        print_error(f"Package import failed: {e}")
        return False

def check_no_sensitive_data(root):
    """Check for common sensitive data patterns."""
    print_header("Checking for Sensitive Data")

    sensitive_patterns = [
        ("*.db", "SQLite databases"),
        ("*.db-journal", "SQLite journals"),
        (".env", "Environment files"),
        ("credentials.json", "Credentials"),
        ("*_SECRET*", "Secret files"),
        ("*_TOKEN*", "Token files"),
    ]

    all_ok = True
    for pattern, description in sensitive_patterns:
        matches = list(root.rglob(pattern))
        # Filter out .git directory
        matches = [m for m in matches if '.git' not in m.parts]

        if matches:
            print_warning(f"Found {description}: {len(matches)} file(s)")
            for match in matches[:3]:  # Show first 3
                rel_path = match.relative_to(root)
                print(f"  - {rel_path}")
            if len(matches) > 3:
                print(f"  ... and {len(matches) - 3} more")
        else:
            print_success(f"No {description} found")

    return all_ok

def check_manifest(root):
    """Verify MANIFEST.in is properly configured."""
    print_header("Checking MANIFEST.in")

    manifest = root / "MANIFEST.in"
    if not manifest.exists():
        print_error("MANIFEST.in not found")
        return False

    content = manifest.read_text()

    important_includes = [
        ("include LICENSE", "LICENSE file"),
        ("include README.md", "README"),
        ("include CHANGELOG.md", "CHANGELOG"),
        ("recursive-include docs", "Documentation"),
    ]

    all_ok = True
    for pattern, description in important_includes:
        if pattern in content:
            print_success(f"{description} included")
        else:
            print_warning(f"{description} not explicitly included")

    # Check for important excludes
    if "global-exclude *.pyc" in content:
        print_success("Excludes compiled Python files")
    if "exclude *.db" in content:
        print_success("Excludes database files")

    return all_ok

def check_readme_rendering(root):
    """Check if README will render on PyPI."""
    print_header("Checking README Rendering")

    readme = root / "README.md"
    if not readme.exists():
        print_error("README.md not found")
        return False

    content = readme.read_text()

    # Check for common issues
    issues = []

    if len(content) < 100:
        issues.append("README is very short (< 100 chars)")

    if "```" in content and content.count("```") % 2 != 0:
        issues.append("Unmatched code fence (```)")

    if "<script" in content.lower():
        issues.append("Contains <script> tags (not allowed on PyPI)")

    if issues:
        for issue in issues:
            print_warning(issue)
        return False
    else:
        print_success(f"README looks good ({len(content)} chars)")
        return True

def main():
    """Run all verification checks."""
    print(f"{BLUE}")
    print("   ___________________  ___   ______________  ____  ____  ___")
    print("  / ____/ __ \\/ ___/ / / / | / /_  __/  _/ / / / / / / / / /")
    print(" / /   / / / /\\__ \\/ /_/ /  |/ / / /  / // / / / / / / / / /")
    print("/ /___/ /_/ /___/ / __  / /|  / / / _/ // /_/ / /_/ / /_/ /")
    print("\\____/\\____//____/_/ /_/_/ |_/ /_/ /___/\\____/\\____/\\____/")
    print()
    print("                    ∞ CONTINUUM ∞")
    print(f"{NC}")
    print()
    print(f"{GREEN}Package Structure Verification{NC}")
    print("━" * 60)

    # Get project root
    root = Path(__file__).parent.parent.resolve()
    print(f"Project root: {root}")

    # Run all checks
    checks = [
        ("Required Files", lambda: check_required_files(root)),
        ("pyproject.toml", lambda: check_pyproject_toml(root)),
        ("Package Structure", lambda: check_package_structure(root)),
        ("MANIFEST.in", lambda: check_manifest(root)),
        ("README Rendering", lambda: check_readme_rendering(root)),
        ("Package Imports", lambda: check_imports(root)),
        ("Sensitive Data", lambda: check_no_sensitive_data(root)),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} check failed with exception: {e}")
            results.append((name, False))

    # Summary
    print_header("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print()
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print()
        print(f"{GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print(f"{GREEN}✓ Package structure verified - Ready for publishing!{NC}")
        print(f"{GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print()
        print("Next steps:")
        print(f"  1. Review {BLUE}scripts/PUBLISH_CHECKLIST.md{NC}")
        print(f"  2. Test publish: {BLUE}./scripts/publish.sh test{NC}")
        print(f"  3. Production publish: {BLUE}./scripts/publish.sh prod{NC}")
        return 0
    else:
        print()
        print(f"{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print(f"{RED}✗ Issues found - Please fix before publishing{NC}")
        print(f"{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
