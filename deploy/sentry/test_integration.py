#!/usr/bin/env python3
"""
Test Sentry Integration

Simple script to verify Sentry integration is working correctly.

Usage:
    # Set SENTRY_DSN first
    export SENTRY_DSN="https://your-key@o123.ingest.sentry.io/456"

    # Run tests
    python test_integration.py

    # Or from project root
    python deploy/sentry/test_integration.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_import():
    """Test that sentry_integration module can be imported"""
    print("Test 1: Import sentry_integration module...")

    try:
        from continuum.core import sentry_integration
        print("  ✓ Module imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_sentry_sdk():
    """Test that sentry-sdk is installed"""
    print("\nTest 2: Check sentry-sdk installation...")

    try:
        import sentry_sdk
        print(f"  ✓ sentry-sdk installed (version: {sentry_sdk.VERSION})")
        return True
    except ImportError:
        print("  ✗ sentry-sdk not installed")
        print("    Install with: pip install 'sentry-sdk[fastapi]>=1.40.0'")
        return False


def test_initialization():
    """Test Sentry initialization"""
    print("\nTest 3: Initialize Sentry...")

    from continuum.core.sentry_integration import init_sentry, is_enabled

    # Check if DSN is set
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        print("  ⚠ SENTRY_DSN not set (Sentry will be disabled)")
        print("    Set with: export SENTRY_DSN='your-dsn'")
        return True  # Not an error, just disabled

    # Try to initialize
    success = init_sentry(environment="test")

    if success and is_enabled():
        print("  ✓ Sentry initialized successfully")
        return True
    else:
        print("  ✗ Sentry initialization failed")
        return False


def test_error_capture():
    """Test error capture"""
    print("\nTest 4: Test error capture...")

    from continuum.core.sentry_integration import capture_exception, is_enabled

    if not is_enabled():
        print("  ⊘ Sentry not enabled (skipping)")
        return True

    try:
        # Create a test error
        raise ValueError("Test error from test_integration.py")
    except Exception as e:
        event_id = capture_exception(
            e,
            level="info",  # Use info level so it doesn't pollute error reports
            tags={"test": "true"},
        )

        if event_id:
            print(f"  ✓ Error captured successfully (event_id: {event_id})")
            print(f"    View in Sentry dashboard")
            return True
        else:
            print("  ✗ Error capture failed (no event_id returned)")
            return False


def test_performance():
    """Test performance monitoring"""
    print("\nTest 5: Test performance monitoring...")

    from continuum.core.sentry_integration import PerformanceTransaction, is_enabled
    import time

    if not is_enabled():
        print("  ⊘ Sentry not enabled (skipping)")
        return True

    try:
        with PerformanceTransaction("test.operation", "Test operation"):
            # Simulate work
            time.sleep(0.1)

        print("  ✓ Performance transaction completed")
        return True
    except Exception as e:
        print(f"  ✗ Performance monitoring failed: {e}")
        return False


def test_context():
    """Test context management"""
    print("\nTest 6: Test context management...")

    from continuum.core.sentry_integration import (
        set_user_context,
        set_operation_context,
        add_breadcrumb,
        is_enabled,
    )

    if not is_enabled():
        print("  ⊘ Sentry not enabled (skipping)")
        return True

    try:
        # Set user context
        set_user_context(tenant_id="test_tenant", instance_id="test_instance")

        # Set operation context
        set_operation_context(
            operation="test",
            model_type="test_model",
        )

        # Add breadcrumb
        add_breadcrumb(
            message="Test breadcrumb",
            category="test",
            level="info",
        )

        print("  ✓ Context management working")
        return True
    except Exception as e:
        print(f"  ✗ Context management failed: {e}")
        return False


def test_status():
    """Test status API"""
    print("\nTest 7: Test status API...")

    from continuum.core.sentry_integration import get_status

    try:
        status = get_status()

        print(f"  Available: {status.get('available', False)}")
        print(f"  Enabled: {status.get('enabled', False)}")

        if status.get('enabled'):
            print(f"  Environment: {status.get('environment', 'N/A')}")
            print(f"  Release: {status.get('release', 'N/A')}")

        print("  ✓ Status API working")
        return True
    except Exception as e:
        print(f"  ✗ Status API failed: {e}")
        return False


def test_flush():
    """Test event flushing"""
    print("\nTest 8: Test event flushing...")

    from continuum.core.sentry_integration import flush, is_enabled

    if not is_enabled():
        print("  ⊘ Sentry not enabled (skipping)")
        return True

    try:
        flush(timeout=2.0)
        print("  ✓ Events flushed successfully")
        return True
    except Exception as e:
        print(f"  ✗ Flush failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Sentry Integration Test Suite")
    print("=" * 70)

    tests = [
        test_import,
        test_sentry_sdk,
        test_initialization,
        test_error_capture,
        test_performance,
        test_context,
        test_status,
        test_flush,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n  ✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("Status: ✓ All tests passed")
        return 0
    else:
        print("Status: ✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
