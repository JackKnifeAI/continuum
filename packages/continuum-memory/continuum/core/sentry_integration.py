#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
CONTINUUM Sentry Integration

Production error tracking and performance monitoring for CONTINUUM infrastructure.

Features:
- Automatic error tracking with full stack traces
- Performance monitoring (transactions)
- Release tracking (tie errors to git commits)
- Environment separation (dev, staging, prod)
- User context (anonymized user ID)
- Custom tags for CONTINUUM operations
- Sensitive data scrubbing
- Rate limiting to avoid quota issues

Usage:
    from continuum.core.sentry_integration import init_sentry, capture_memory_error

    # Initialize on startup
    init_sentry(environment="production", release="v0.2.0")

    # Capture custom errors
    capture_memory_error(error, operation="recall", tenant_id="user_123")
"""

import os
import sys
from typing import Optional, Dict, Any, Callable
from functools import wraps
from pathlib import Path

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


# =============================================================================
# CONFIGURATION
# =============================================================================

def get_sentry_dsn() -> Optional[str]:
    """
    Get Sentry DSN from environment.

    Returns:
        Sentry DSN or None if not configured
    """
    return os.environ.get("SENTRY_DSN")


def get_environment() -> str:
    """
    Get current environment (dev, staging, prod).

    Returns:
        Environment name
    """
    return os.environ.get("CONTINUUM_ENV", "development")


def get_release() -> Optional[str]:
    """
    Get current release version from environment or git.

    Returns:
        Release version string (e.g., "v0.2.0" or git commit hash)
    """
    # First try environment variable
    release = os.environ.get("CONTINUUM_RELEASE")
    if release:
        return release

    # Try to get git commit hash
    try:
        import subprocess
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent.parent.parent,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return f"git-{git_hash}"
    except Exception:
        pass

    # Fallback to package version
    try:
        from continuum import __version__
        return f"v{__version__}"
    except Exception:
        return None


def get_server_name() -> Optional[str]:
    """
    Get server/instance name for identification.

    Returns:
        Server name or None
    """
    return os.environ.get("CONTINUUM_SERVER_NAME") or os.environ.get("HOSTNAME")


# =============================================================================
# SENSITIVE DATA SCRUBBING
# =============================================================================

def scrub_sensitive_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Before-send hook to scrub sensitive data from Sentry events.

    Removes:
    - Memory content (user messages, AI responses)
    - API keys
    - Passwords
    - Tokens

    Keeps:
    - Metadata (operation type, tenant ID, error type)
    - Stack traces
    - Performance metrics

    Args:
        event: Sentry event dictionary
        hint: Additional context

    Returns:
        Scrubbed event or None to drop the event
    """
    if not event:
        return None

    # Scrub request data
    if "request" in event:
        request = event["request"]

        # Remove body data (may contain messages)
        if "data" in request:
            request["data"] = "[REDACTED]"

        # Scrub sensitive headers
        if "headers" in request:
            headers = request["headers"]
            sensitive_headers = ["X-API-Key", "Authorization", "Cookie", "Set-Cookie"]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[REDACTED]"

    # Scrub extra context
    if "extra" in event:
        extra = event["extra"]

        # Remove memory content but keep metadata
        if "memory_content" in extra:
            del extra["memory_content"]
        if "message" in extra:
            del extra["message"]
        if "user_message" in extra:
            del extra["user_message"]
        if "ai_response" in extra:
            del extra["ai_response"]

    # Scrub exception values containing sensitive data
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            if "value" in exception:
                value = exception["value"]
                # Remove potential API keys or tokens from error messages
                if "api_key" in value.lower() or "token" in value.lower():
                    exception["value"] = "[REDACTED - Contains sensitive data]"

    return event


def should_ignore_error(event: Dict[str, Any], hint: Dict[str, Any]) -> bool:
    """
    Determine if an error should be ignored.

    Args:
        event: Sentry event dictionary
        hint: Additional context

    Returns:
        True if error should be ignored
    """
    # Ignore specific exception types
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            exc_type = exception.get("type", "")

            # Ignore expected errors
            if exc_type in [
                "KeyboardInterrupt",
                "SystemExit",
                "CancelledError",  # asyncio cancellations
                "TimeoutError",    # Expected timeouts
            ]:
                return True

    return False


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    sample_rate: float = 1.0,
    traces_sample_rate: float = 0.1,
    enable_profiling: bool = False,
    profiles_sample_rate: float = 0.1,
) -> bool:
    """
    Initialize Sentry error tracking and performance monitoring.

    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name (dev, staging, prod)
        release: Release version
        sample_rate: Error sampling rate (0.0-1.0, default 1.0 = 100%)
        traces_sample_rate: Performance trace sampling rate (0.0-1.0, default 0.1 = 10%)
        enable_profiling: Enable profiling (requires sentry-sdk[profiling])
        profiles_sample_rate: Profiling sampling rate (0.0-1.0, default 0.1 = 10%)

    Returns:
        True if Sentry initialized successfully, False otherwise
    """
    if not SENTRY_AVAILABLE:
        print("Warning: sentry-sdk not installed. Error tracking disabled.", file=sys.stderr)
        print("Install with: pip install 'sentry-sdk[fastapi]'", file=sys.stderr)
        return False

    # Get configuration
    dsn = dsn or get_sentry_dsn()
    if not dsn:
        print("Warning: SENTRY_DSN not set. Error tracking disabled.", file=sys.stderr)
        return False

    environment = environment or get_environment()
    release = release or get_release()
    server_name = get_server_name()

    # Build integrations list
    integrations = [
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
        RedisIntegration(),
        AsyncioIntegration(),
    ]

    # Initialize Sentry
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            server_name=server_name,
            integrations=integrations,

            # Sampling
            sample_rate=sample_rate,
            traces_sample_rate=traces_sample_rate,

            # Profiling (optional)
            _experiments={
                "profiles_sample_rate": profiles_sample_rate if enable_profiling else 0.0,
            },

            # Hooks
            before_send=lambda event, hint: (
                None if should_ignore_error(event, hint) else scrub_sensitive_data(event, hint)
            ),

            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII
            max_breadcrumbs=50,
            debug=False,
        )

        print(f"Sentry initialized: env={environment}, release={release}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"Error initializing Sentry: {e}", file=sys.stderr)
        return False


# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

def set_user_context(
    tenant_id: Optional[str] = None,
    instance_id: Optional[str] = None,
    anonymize: bool = True,
):
    """
    Set user context for error tracking.

    Args:
        tenant_id: Tenant identifier
        instance_id: Instance identifier
        anonymize: Anonymize tenant ID (hash it)
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    user_data = {}

    if tenant_id:
        if anonymize:
            import hashlib
            user_data["id"] = hashlib.sha256(tenant_id.encode()).hexdigest()[:16]
            user_data["tenant_id_hash"] = user_data["id"]
        else:
            user_data["id"] = tenant_id
            user_data["tenant_id"] = tenant_id

    if instance_id:
        user_data["instance_id"] = instance_id

    sentry_sdk.set_user(user_data)


def set_operation_context(
    operation: str,
    model_type: Optional[str] = None,
    memory_operation: Optional[str] = None,
    federation_peer: Optional[str] = None,
    **extra_tags,
):
    """
    Set operation context with custom tags.

    Args:
        operation: Operation name (e.g., "recall", "learn", "sync")
        model_type: AI model type (e.g., "claude-opus-4.5")
        memory_operation: Memory operation type
        federation_peer: Federation peer identifier
        **extra_tags: Additional custom tags
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    tags = {"operation": operation}

    if model_type:
        tags["model_type"] = model_type
    if memory_operation:
        tags["memory_operation"] = memory_operation
    if federation_peer:
        tags["federation_peer"] = federation_peer

    tags.update(extra_tags)

    for key, value in tags.items():
        sentry_sdk.set_tag(key, value)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """
    Add a breadcrumb for debugging.

    Breadcrumbs are a trail of events leading up to an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "database", "api", "memory")
        level: Level (debug, info, warning, error)
        data: Additional data (will be scrubbed)
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    # Scrub sensitive data from breadcrumb
    if data:
        scrubbed_data = {}
        for key, value in data.items():
            if key.lower() in ["content", "message", "user_message", "ai_response", "api_key", "token"]:
                scrubbed_data[key] = "[REDACTED]"
            else:
                scrubbed_data[key] = value
        data = scrubbed_data

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )


# =============================================================================
# ERROR CAPTURE
# =============================================================================

def capture_exception(
    error: Exception,
    level: str = "error",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        error: Exception to capture
        level: Error level (debug, info, warning, error, fatal)
        extra: Extra context data (will be scrubbed)
        tags: Custom tags

    Returns:
        Event ID or None
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return None

    with sentry_sdk.push_scope() as scope:
        scope.level = level

        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        return sentry_sdk.capture_exception(error)


def capture_memory_error(
    error: Exception,
    operation: str,
    tenant_id: Optional[str] = None,
    instance_id: Optional[str] = None,
    **extra,
) -> Optional[str]:
    """
    Capture a memory operation error.

    Args:
        error: Exception to capture
        operation: Memory operation (recall, learn, turn, sync, etc.)
        tenant_id: Tenant identifier
        instance_id: Instance identifier
        **extra: Additional context

    Returns:
        Event ID or None
    """
    set_user_context(tenant_id=tenant_id, instance_id=instance_id)
    set_operation_context(operation=operation)

    return capture_exception(
        error,
        level="error",
        extra=extra,
        tags={"operation": operation},
    )


def capture_message(
    message: str,
    level: str = "info",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Capture a message (not an exception).

    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error)
        extra: Extra context
        tags: Custom tags

    Returns:
        Event ID or None
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return None

    with sentry_sdk.push_scope() as scope:
        scope.level = level

        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        return sentry_sdk.capture_message(message)


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

class PerformanceTransaction:
    """Context manager for performance transaction tracking."""

    def __init__(
        self,
        operation: str,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize performance transaction.

        Args:
            operation: Operation name
            description: Optional description
            tenant_id: Tenant identifier
        """
        self.operation = operation
        self.description = description or operation
        self.tenant_id = tenant_id
        self.transaction = None

    def __enter__(self):
        """Start transaction."""
        if SENTRY_AVAILABLE and sentry_sdk:
            self.transaction = sentry_sdk.start_transaction(
                op=self.operation,
                name=self.description,
            )
            self.transaction.__enter__()

            if self.tenant_id:
                set_user_context(tenant_id=self.tenant_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End transaction."""
        if self.transaction:
            self.transaction.__exit__(exc_type, exc_val, exc_tb)

    def start_span(self, operation: str, description: Optional[str] = None):
        """
        Start a span within this transaction.

        Args:
            operation: Span operation
            description: Span description

        Returns:
            Span context manager
        """
        if self.transaction and SENTRY_AVAILABLE and sentry_sdk:
            return sentry_sdk.start_span(
                op=operation,
                description=description or operation,
            )
        else:
            # No-op context manager
            from contextlib import nullcontext
            return nullcontext()


def monitor_performance(operation: str, description: Optional[str] = None):
    """
    Decorator for monitoring function performance.

    Args:
        operation: Operation name
        description: Optional description

    Usage:
        @monitor_performance("memory.recall")
        def recall(query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTransaction(operation, description):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with PerformanceTransaction(operation, description):
                return await func(*args, **kwargs)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


# =============================================================================
# UTILITIES
# =============================================================================

def flush(timeout: float = 2.0):
    """
    Flush pending events to Sentry.

    Call this before shutdown to ensure all events are sent.

    Args:
        timeout: Maximum time to wait in seconds
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        sentry_sdk.flush(timeout=timeout)


def close():
    """Close Sentry client and flush events."""
    flush(timeout=5.0)


# =============================================================================
# HEALTH CHECK
# =============================================================================

def is_enabled() -> bool:
    """
    Check if Sentry is enabled and initialized.

    Returns:
        True if Sentry is enabled
    """
    if not SENTRY_AVAILABLE:
        return False

    try:
        client = sentry_sdk.Hub.current.client
        return client is not None and client.dsn is not None
    except Exception:
        return False


def get_status() -> Dict[str, Any]:
    """
    Get Sentry integration status.

    Returns:
        Status dictionary
    """
    status = {
        "available": SENTRY_AVAILABLE,
        "enabled": is_enabled(),
    }

    if is_enabled():
        try:
            client = sentry_sdk.Hub.current.client
            status.update({
                "environment": client.options.get("environment"),
                "release": client.options.get("release"),
                "sample_rate": client.options.get("sample_rate"),
                "traces_sample_rate": client.options.get("traces_sample_rate"),
            })
        except Exception:
            pass

    return status


if __name__ == "__main__":
    # Test initialization
    print("Testing Sentry integration...")
    print(f"Sentry SDK available: {SENTRY_AVAILABLE}")

    if init_sentry():
        print("Sentry initialized successfully")
        print(f"Status: {get_status()}")

        # Test error capture
        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = capture_exception(e)
            print(f"Captured test error: {event_id}")

        flush()
    else:
        print("Sentry initialization failed")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
