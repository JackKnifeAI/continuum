#!/usr/bin/env python3
"""Test dataclass imports for field ordering issues."""

import sys
import importlib
import traceback

# Test each compliance submodule
modules_to_test = [
    "continuum.compliance.audit.events",
    "continuum.compliance.gdpr.consent",
    "continuum.compliance.gdpr.retention",
    "continuum.compliance.gdpr.data_subject",
    "continuum.compliance.access_control.policies",
    "continuum.compliance.access_control.rbac",
    "continuum.compliance.encryption.field_level",
    "continuum.compliance.encryption.in_transit",
    "continuum.compliance.monitoring.alerts",
    "continuum.compliance.monitoring.anomaly",
    "continuum.compliance.reports.generator",
]

print("Testing dataclass imports...")
print("=" * 80)

failures = []

for module_name in modules_to_test:
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        print(f"✗ {module_name}")
        if "non-default argument" in str(e):
            # Extract the problematic argument names
            error_msg = str(e)
            print(f"  Field ordering issue: {error_msg}")
            failures.append((module_name, error_msg))
        else:
            print(f"  {type(e).__name__}: {e}")
            failures.append((module_name, f"{type(e).__name__}: {e}"))

print("=" * 80)
print(f"\nTotal: {len(modules_to_test)}, Failures: {len(failures)}")

if failures:
    print("\nFailed modules:")
    for module, error in failures:
        print(f"  - {module}")
        print(f"    {error}")

sys.exit(1 if failures else 0)
