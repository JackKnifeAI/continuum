"""
CONTINUUM API Middleware

Middleware components for API request handling, analytics, and monitoring.
"""

# Import authentication functions from the old middleware.py file (sibling to this directory)
# This works around Python preferring the middleware/ directory over middleware.py
import sys
from pathlib import Path

# We need to import from the middleware.py file, not this package
# So we'll load it directly
import importlib.util
_middleware_py_path = Path(__file__).parent.parent / "middleware.py"
_spec = importlib.util.spec_from_file_location("_old_middleware", _middleware_py_path)
_old_middleware = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_old_middleware)

# Re-export the needed items
get_tenant_from_key = _old_middleware.get_tenant_from_key
optional_tenant_from_key = _old_middleware.optional_tenant_from_key
validate_api_key = _old_middleware.validate_api_key
verify_api_key = _old_middleware.validate_api_key  # Alias for GraphQL context
verify_key = _old_middleware.verify_key
hash_key = _old_middleware.hash_key
init_api_keys_db = _old_middleware.init_api_keys_db
get_api_keys_db_path = _old_middleware.get_api_keys_db_path
REQUIRE_API_KEY = _old_middleware.REQUIRE_API_KEY

from .analytics_middleware import AnalyticsMiddleware

# Optional Prometheus metrics (requires prometheus_client package)
try:
    from .metrics import PrometheusMiddleware, metrics_endpoint
    __all__ = [
        "AnalyticsMiddleware",
        "PrometheusMiddleware",
        "metrics_endpoint",
        "get_tenant_from_key",
        "optional_tenant_from_key",
        "validate_api_key",
        "verify_api_key",
        "verify_key",
        "hash_key",
        "init_api_keys_db",
        "get_api_keys_db_path",
        "REQUIRE_API_KEY",
    ]
except ImportError:
    # Prometheus client not installed, metrics disabled
    PrometheusMiddleware = None
    metrics_endpoint = None
    __all__ = [
        "AnalyticsMiddleware",
        "get_tenant_from_key",
        "optional_tenant_from_key",
        "validate_api_key",
        "verify_api_key",
        "verify_key",
        "hash_key",
        "init_api_keys_db",
        "get_api_keys_db_path",
        "REQUIRE_API_KEY",
    ]
