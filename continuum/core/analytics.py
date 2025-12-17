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
CONTINUUM Analytics Module

PostHog integration for product analytics with privacy-first design.
Tracks usage patterns while respecting GDPR and user privacy.

Events tracked:
- User lifecycle: signup, login, session
- Memory operations: create, read, update, delete, search
- Federation: join, sync, disconnect
- API requests and errors
- CLI command execution

Privacy guarantees:
- No PII in events
- Anonymized user IDs (SHA-256 hashed)
- Opt-out mechanism
- GDPR compliant
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsConfig:
    """Configuration for PostHog analytics"""

    # PostHog settings
    api_key: str = ""
    host: str = "https://app.posthog.com"
    enabled: bool = True

    # Privacy settings
    anonymize_users: bool = True
    opt_out: bool = False
    capture_ip: bool = False
    capture_user_agent: bool = True

    # Performance settings
    batch_size: int = 10
    flush_interval: float = 10.0  # seconds

    # Feature flags
    enable_feature_flags: bool = True
    poll_interval: int = 300  # 5 minutes

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AnalyticsConfig":
        """Load analytics configuration from file or environment"""
        config = cls()

        # Load from file if exists
        if config_path and config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except Exception as e:
                logger.warning(f"Failed to load analytics config: {e}")

        # Override with environment variables
        if os.environ.get("POSTHOG_API_KEY"):
            config.api_key = os.environ["POSTHOG_API_KEY"]
        if os.environ.get("POSTHOG_HOST"):
            config.host = os.environ["POSTHOG_HOST"]
        if os.environ.get("CONTINUUM_ANALYTICS_ENABLED"):
            config.enabled = os.environ["CONTINUUM_ANALYTICS_ENABLED"].lower() == "true"
        if os.environ.get("CONTINUUM_ANALYTICS_OPT_OUT"):
            config.opt_out = os.environ["CONTINUUM_ANALYTICS_OPT_OUT"].lower() == "true"

        # Disable if opted out or no API key
        if config.opt_out or not config.api_key:
            config.enabled = False

        return config


class Analytics:
    """
    PostHog analytics client with privacy-first design.

    Handles event tracking, user identification, feature flags,
    and user properties while respecting privacy.
    """

    def __init__(self, config: Optional[AnalyticsConfig] = None):
        self.config = config or AnalyticsConfig.load()
        self._client = None
        self._user_cache = {}
        self._session_id = None
        self._session_start = None

        if self.config.enabled:
            self._init_client()

    def _init_client(self):
        """Initialize PostHog client"""
        try:
            import posthog

            posthog.api_key = self.config.api_key
            posthog.host = self.config.host
            posthog.disabled = not self.config.enabled

            # Configure privacy settings
            if not self.config.capture_ip:
                posthog.geoip_disable = True

            self._client = posthog
            logger.info("PostHog analytics initialized")
        except ImportError:
            logger.warning("posthog-python not installed. Analytics disabled.")
            self.config.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize PostHog: {e}")
            self.config.enabled = False

    def _anonymize_user_id(self, user_id: str) -> str:
        """
        Anonymize user ID using SHA-256 hash.

        Args:
            user_id: Original user ID

        Returns:
            str: Anonymized user ID
        """
        if not self.config.anonymize_users:
            return user_id

        # Use SHA-256 for one-way anonymization
        return hashlib.sha256(user_id.encode()).hexdigest()

    def _get_session_id(self) -> str:
        """Get or create current session ID"""
        if not self._session_id or not self._session_start:
            self._session_id = hashlib.sha256(
                f"{time.time()}{os.getpid()}".encode()
            ).hexdigest()[:16]
            self._session_start = datetime.utcnow()

        return self._session_id

    def identify(
        self,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """
        Identify a user with properties.

        Args:
            user_id: User identifier (will be anonymized if configured)
            properties: User properties (plan, account_age, etc.)
        """
        if not self.config.enabled or not self._client:
            return

        try:
            distinct_id = self._anonymize_user_id(user_id)
            props = properties or {}

            # Remove any PII from properties
            sanitized_props = self._sanitize_properties(props)

            self._client.identify(distinct_id, sanitized_props)
            self._user_cache[user_id] = distinct_id
        except Exception as e:
            logger.error(f"Failed to identify user: {e}")

    def track(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """
        Track an event.

        Args:
            user_id: User identifier
            event_name: Event name (e.g., "memory_create")
            properties: Event properties
        """
        if not self.config.enabled or not self._client:
            return

        try:
            distinct_id = self._user_cache.get(user_id) or self._anonymize_user_id(
                user_id
            )
            props = properties or {}

            # Add session context
            props["session_id"] = self._get_session_id()
            props["timestamp"] = datetime.utcnow().isoformat()

            # Sanitize properties
            sanitized_props = self._sanitize_properties(props)

            self._client.capture(distinct_id, event_name, sanitized_props)
        except Exception as e:
            logger.error(f"Failed to track event {event_name}: {e}")

    def track_page(
        self,
        user_id: str,
        page_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """
        Track a page view.

        Args:
            user_id: User identifier
            page_name: Page/screen name
            properties: Additional properties
        """
        props = properties or {}
        props["page_name"] = page_name
        self.track(user_id, "$pageview", props)

    def get_feature_flag(
        self,
        user_id: str,
        flag_key: str,
        default: bool = False,
    ) -> bool:
        """
        Get feature flag value for user.

        Args:
            user_id: User identifier
            flag_key: Feature flag key
            default: Default value if flag not found

        Returns:
            bool: Feature flag value
        """
        if not self.config.enabled or not self.config.enable_feature_flags:
            return default

        try:
            distinct_id = self._anonymize_user_id(user_id)
            return self._client.is_feature_enabled(flag_key, distinct_id) or default
        except Exception as e:
            logger.error(f"Failed to get feature flag {flag_key}: {e}")
            return default

    def get_feature_flags(self, user_id: str) -> Dict[str, bool]:
        """
        Get all feature flags for user.

        Args:
            user_id: User identifier

        Returns:
            Dict[str, bool]: Feature flags
        """
        if not self.config.enabled or not self.config.enable_feature_flags:
            return {}

        try:
            distinct_id = self._anonymize_user_id(user_id)
            return self._client.get_all_flags(distinct_id) or {}
        except Exception as e:
            logger.error(f"Failed to get feature flags: {e}")
            return {}

    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII from properties.

        Args:
            properties: Raw properties

        Returns:
            Dict[str, Any]: Sanitized properties
        """
        # List of keys that might contain PII
        pii_keys = {
            "email",
            "name",
            "phone",
            "address",
            "ip",
            "ip_address",
            "first_name",
            "last_name",
            "full_name",
            "ssn",
            "credit_card",
            "password",
        }

        sanitized = {}
        for key, value in properties.items():
            # Skip PII keys
            if key.lower() in pii_keys:
                continue

            # Recursively sanitize nested dicts
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_properties(value)
            else:
                sanitized[key] = value

        return sanitized

    def flush(self):
        """Flush pending events"""
        if self.config.enabled and self._client:
            try:
                self._client.flush()
            except Exception as e:
                logger.error(f"Failed to flush analytics: {e}")

    def shutdown(self):
        """Shutdown analytics client"""
        if self.config.enabled and self._client:
            try:
                self._client.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown analytics: {e}")


# Global analytics instance
_analytics: Optional[Analytics] = None


def get_analytics(config: Optional[AnalyticsConfig] = None) -> Analytics:
    """
    Get or create global analytics instance.

    Args:
        config: Optional analytics configuration

    Returns:
        Analytics: Global analytics instance
    """
    global _analytics
    if _analytics is None:
        _analytics = Analytics(config)
    return _analytics


def set_analytics(analytics: Analytics):
    """
    Set global analytics instance.

    Args:
        analytics: Analytics instance
    """
    global _analytics
    _analytics = analytics


# Convenience tracking functions


def track_user_signup(user_id: str, plan: str = "free"):
    """Track user signup event"""
    analytics = get_analytics()
    analytics.identify(user_id, {"plan": plan, "signup_date": datetime.utcnow().isoformat()})
    analytics.track(user_id, "user_signup", {"plan": plan})


def track_user_login(user_id: str):
    """Track user login event"""
    analytics = get_analytics()
    analytics.track(user_id, "user_login", {})


def track_session_start(user_id: str):
    """Track session start event"""
    analytics = get_analytics()
    analytics.track(user_id, "session_start", {})


def track_session_end(user_id: str, duration_seconds: float):
    """Track session end event"""
    analytics = get_analytics()
    analytics.track(user_id, "session_end", {"duration_seconds": duration_seconds})


def track_memory_create(user_id: str, memory_type: str, size_bytes: int = 0):
    """Track memory creation event"""
    analytics = get_analytics()
    analytics.track(
        user_id, "memory_create", {"memory_type": memory_type, "size_bytes": size_bytes}
    )


def track_memory_read(user_id: str, memory_type: str):
    """Track memory read event"""
    analytics = get_analytics()
    analytics.track(user_id, "memory_read", {"memory_type": memory_type})


def track_memory_update(user_id: str, memory_type: str):
    """Track memory update event"""
    analytics = get_analytics()
    analytics.track(user_id, "memory_update", {"memory_type": memory_type})


def track_memory_delete(user_id: str, memory_type: str):
    """Track memory delete event"""
    analytics = get_analytics()
    analytics.track(user_id, "memory_delete", {"memory_type": memory_type})


def track_memory_search(user_id: str, query: str, results_count: int, duration_ms: float):
    """Track memory search event"""
    analytics = get_analytics()
    # Don't include actual query to avoid PII
    analytics.track(
        user_id,
        "memory_search",
        {
            "query_length": len(query),
            "results_count": results_count,
            "duration_ms": duration_ms,
        },
    )


def track_federation_join(user_id: str, node_id: str):
    """Track federation join event"""
    analytics = get_analytics()
    analytics.track(user_id, "federation_join", {"node_id": node_id})


def track_federation_sync(user_id: str, pushed: int, pulled: int, duration_ms: float):
    """Track federation sync event"""
    analytics = get_analytics()
    analytics.track(
        user_id,
        "federation_sync",
        {"pushed": pushed, "pulled": pulled, "duration_ms": duration_ms},
    )


def track_federation_disconnect(user_id: str, node_id: str):
    """Track federation disconnect event"""
    analytics = get_analytics()
    analytics.track(user_id, "federation_disconnect", {"node_id": node_id})


def track_api_request(
    user_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
):
    """Track API request event"""
    analytics = get_analytics()
    analytics.track(
        user_id,
        "api_request",
        {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )


def track_cli_command(user_id: str, command: str, success: bool, duration_ms: float):
    """Track CLI command execution"""
    analytics = get_analytics()
    analytics.track(
        user_id,
        "cli_command",
        {"command": command, "success": success, "duration_ms": duration_ms},
    )


def track_error(user_id: str, error_type: str, context: str, fatal: bool = False):
    """Track error event"""
    analytics = get_analytics()
    analytics.track(
        user_id,
        "error",
        {"error_type": error_type, "context": context, "fatal": fatal},
    )


def track_decorator(event_name: str, extract_properties: Optional[callable] = None):
    """
    Decorator for automatic event tracking.

    Args:
        event_name: Event name to track
        extract_properties: Function to extract properties from args/kwargs

    Example:
        @track_decorator("memory_search", lambda args, kwargs: {"query": kwargs.get("query")})
        def search(query: str):
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_type = None

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Extract properties
                props = {"success": success, "duration_ms": duration_ms}
                if error_type:
                    props["error_type"] = error_type
                if extract_properties:
                    try:
                        custom_props = extract_properties(args, kwargs)
                        props.update(custom_props)
                    except Exception:
                        pass

                # Track event (user_id should be in kwargs)
                user_id = kwargs.get("user_id") or kwargs.get("tenant_id") or "anonymous"
                analytics = get_analytics()
                analytics.track(user_id, event_name, props)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    config = AnalyticsConfig(
        api_key="your_api_key_here",
        enabled=True,
        anonymize_users=True,
    )

    analytics = Analytics(config)

    # Identify user
    analytics.identify("user_123", {"plan": "pro", "account_age": 30})

    # Track events
    track_user_login("user_123")
    track_memory_create("user_123", "concept", 1024)
    track_memory_search("user_123", "warp drive", 10, 45.2)

    # Get feature flags
    beta_enabled = analytics.get_feature_flag("user_123", "beta_features", False)
    print(f"Beta features enabled: {beta_enabled}")

    # Flush and shutdown
    analytics.flush()
    analytics.shutdown()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
