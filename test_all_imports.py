#!/usr/bin/env python3
"""
Comprehensive import test for CONTINUUM project.
Tests every module and submodule to identify import errors.
"""

import sys
import traceback
from typing import List, Tuple

def test_import(module_name: str) -> Tuple[bool, str]:
    """Test importing a module and return success status and error message."""
    try:
        __import__(module_name)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

def main():
    """Test all imports in the CONTINUUM project."""

    # All imports to test
    import_tests = [
        # Top-level exports
        ("continuum", "Top-level package"),
        ("continuum.ContinuumMemory", "Main memory class"),

        # Core modules
        ("continuum.core", "Core package"),
        ("continuum.core.memory", "Memory module"),
        ("continuum.core.recall", "Recall module"),
        ("continuum.core.learning", "Learning module"),

        # Storage backends
        ("continuum.storage", "Storage package"),
        ("continuum.storage.sqlite_backend", "SQLite backend"),
        ("continuum.storage.postgres_backend", "PostgreSQL backend"),

        # API
        ("continuum.api", "API package"),
        ("continuum.api.server", "API server"),
        ("continuum.api.middleware", "API middleware"),
        ("continuum.api.graphql", "GraphQL API"),
        ("continuum.api.graphql.schema", "GraphQL schema"),
        ("continuum.api.graphql.resolvers", "GraphQL resolvers"),
        ("continuum.api.graphql.dataloaders", "GraphQL dataloaders"),
        ("continuum.api.graphql.auth", "GraphQL auth"),
        ("continuum.api.graphql.middleware", "GraphQL middleware"),

        # CLI
        ("continuum.cli", "CLI package"),
        ("continuum.cli.main", "CLI main"),
        ("continuum.cli.commands", "CLI commands"),

        # Billing
        ("continuum.billing", "Billing package"),
        ("continuum.billing.stripe_client", "Stripe client"),
        ("continuum.billing.tiers", "Billing tiers"),

        # Federation
        ("continuum.federation", "Federation package"),
        ("continuum.federation.distributed", "Distributed federation"),

        # Bridges
        ("continuum.bridges", "Bridges package"),

        # Cache
        ("continuum.cache", "Cache package"),

        # Webhooks
        ("continuum.webhooks", "Webhooks package"),

        # Backup
        ("continuum.backup", "Backup package"),
        ("continuum.backup.strategies", "Backup strategies"),
        ("continuum.backup.storage", "Backup storage"),
        ("continuum.backup.encryption", "Backup encryption"),
        ("continuum.backup.compression", "Backup compression"),
        ("continuum.backup.verification", "Backup verification"),
        ("continuum.backup.recovery", "Backup recovery"),
        ("continuum.backup.retention", "Backup retention"),
        ("continuum.backup.monitoring", "Backup monitoring"),

        # Compliance
        ("continuum.compliance", "Compliance package"),
        ("continuum.compliance.audit", "Compliance audit"),
        ("continuum.compliance.gdpr", "GDPR compliance"),
        ("continuum.compliance.encryption", "Compliance encryption"),
        ("continuum.compliance.access_control", "Access control"),
        ("continuum.compliance.reports", "Compliance reports"),
        ("continuum.compliance.monitoring", "Compliance monitoring"),

        # Observability
        ("continuum.observability", "Observability package"),

        # Realtime
        ("continuum.realtime", "Realtime package"),

        # Identity
        ("continuum.identity", "Identity package"),

        # Embeddings
        ("continuum.embeddings", "Embeddings package"),

        # Extraction
        ("continuum.extraction", "Extraction package"),

        # Coordination
        ("continuum.coordination", "Coordination package"),

        # MCP
        ("continuum.mcp", "MCP package"),
    ]

    # Results tracking
    successes = []
    failures = []

    print("=" * 80)
    print("CONTINUUM IMPORT TEST SUITE")
    print("=" * 80)
    print()

    # Test each import
    for module_name, description in import_tests:
        success, error = test_import(module_name)

        if success:
            successes.append((module_name, description))
            print(f"✓ {module_name:50s} - {description}")
        else:
            failures.append((module_name, description, error))
            print(f"✗ {module_name:50s} - {description}")
            print(f"  Error: {error.split(':', 1)[0] if ':' in error else error[:100]}")

    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(import_tests)}")
    print(f"Successes:   {len(successes)} ({len(successes)*100//len(import_tests)}%)")
    print(f"Failures:    {len(failures)} ({len(failures)*100//len(import_tests)}%)")
    print()

    # Print detailed failures
    if failures:
        print("=" * 80)
        print("DETAILED FAILURE REPORT")
        print("=" * 80)
        for module_name, description, error in failures:
            print()
            print(f"Module: {module_name}")
            print(f"Description: {description}")
            print(f"Error:")
            print(error)
            print("-" * 80)

    # Exit code
    return 0 if len(failures) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
