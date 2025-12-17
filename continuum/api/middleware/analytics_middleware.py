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
Analytics Middleware for CONTINUUM API

ASGI/WSGI middleware that automatically tracks API requests with PostHog.
Compatible with FastAPI, Flask, Django, and other frameworks.

Usage (FastAPI):
    from fastapi import FastAPI
    from continuum.api.middleware import AnalyticsMiddleware

    app = FastAPI()
    app.add_middleware(AnalyticsMiddleware)

Usage (Flask):
    from flask import Flask
    from continuum.api.middleware import AnalyticsMiddleware

    app = Flask(__name__)
    app.wsgi_app = AnalyticsMiddleware(app.wsgi_app)
"""

import time
import logging
from typing import Callable, Optional, Any
from urllib.parse import urlparse
from continuum.core.analytics import get_analytics, track_api_request, track_error

logger = logging.getLogger(__name__)


class AnalyticsMiddleware:
    """
    Middleware for automatic API request tracking.

    Tracks:
    - Request method, endpoint, status code
    - Request duration
    - User identification (from headers/auth)
    - Errors and exceptions

    Privacy:
    - No query parameters tracked (may contain PII)
    - No request/response bodies tracked
    - User IDs anonymized per analytics config
    """

    def __init__(
        self,
        app: Any,
        user_id_header: str = "X-User-ID",
        tenant_id_header: str = "X-Tenant-ID",
        exclude_paths: Optional[list] = None,
    ):
        """
        Initialize analytics middleware.

        Args:
            app: ASGI/WSGI application
            user_id_header: Header containing user ID
            tenant_id_header: Header containing tenant ID
            exclude_paths: Paths to exclude from tracking (e.g., /health)
        """
        self.app = app
        self.user_id_header = user_id_header
        self.tenant_id_header = tenant_id_header
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.analytics = get_analytics()

    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        method = scope["method"]
        path = scope["path"]

        # Skip excluded paths
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        # Extract user/tenant ID from headers
        user_id = None
        tenant_id = None
        for header_name, header_value in scope.get("headers", []):
            header_name = header_name.decode("latin1")
            if header_name.lower() == self.user_id_header.lower():
                user_id = header_value.decode("latin1")
            elif header_name.lower() == self.tenant_id_header.lower():
                tenant_id = header_value.decode("latin1")

        # Use tenant_id if user_id not available
        tracking_id = user_id or tenant_id or "anonymous"

        # Track request
        start_time = time.time()
        status_code = 200
        error_type = None

        # Wrap send to capture response status
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            error_type = type(e).__name__
            logger.error(f"Request failed: {e}")

            # Track error
            track_error(
                tracking_id,
                error_type,
                context=f"{method} {path}",
                fatal=False,
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Track API request
            track_api_request(
                tracking_id,
                method=method,
                endpoint=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )


class FlaskAnalyticsMiddleware:
    """
    Analytics middleware for Flask applications.

    Usage:
        app = Flask(__name__)
        app.wsgi_app = FlaskAnalyticsMiddleware(app.wsgi_app)
    """

    def __init__(
        self,
        app: Any,
        user_id_header: str = "X-User-ID",
        tenant_id_header: str = "X-Tenant-ID",
        exclude_paths: Optional[list] = None,
    ):
        """
        Initialize Flask analytics middleware.

        Args:
            app: WSGI application
            user_id_header: Header containing user ID
            tenant_id_header: Header containing tenant ID
            exclude_paths: Paths to exclude from tracking
        """
        self.app = app
        self.user_id_header = user_id_header
        self.tenant_id_header = tenant_id_header
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.analytics = get_analytics()

    def __call__(self, environ, start_response):
        """WSGI middleware implementation"""
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")

        # Skip excluded paths
        if path in self.exclude_paths:
            return self.app(environ, start_response)

        # Extract user/tenant ID from headers
        user_id = environ.get(f"HTTP_{self.user_id_header.upper().replace('-', '_')}")
        tenant_id = environ.get(
            f"HTTP_{self.tenant_id_header.upper().replace('-', '_')}"
        )
        tracking_id = user_id or tenant_id or "anonymous"

        # Track request
        start_time = time.time()
        status_code = 200
        error_type = None

        # Wrap start_response to capture status
        def start_response_wrapper(status, headers, exc_info=None):
            nonlocal status_code
            status_code = int(status.split()[0])
            return start_response(status, headers, exc_info)

        try:
            result = self.app(environ, start_response_wrapper)
            return result
        except Exception as e:
            status_code = 500
            error_type = type(e).__name__
            logger.error(f"Request failed: {e}")

            # Track error
            track_error(
                tracking_id,
                error_type,
                context=f"{method} {path}",
                fatal=False,
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Track API request
            track_api_request(
                tracking_id,
                method=method,
                endpoint=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )


# Example usage with different frameworks
if __name__ == "__main__":
    # FastAPI example
    try:
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(AnalyticsMiddleware)

        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        print("FastAPI app with analytics middleware created")
    except ImportError:
        print("FastAPI not installed")

    # Flask example
    try:
        from flask import Flask

        flask_app = Flask(__name__)
        flask_app.wsgi_app = FlaskAnalyticsMiddleware(flask_app.wsgi_app)

        @flask_app.route("/")
        def flask_root():
            return {"message": "Hello World"}

        print("Flask app with analytics middleware created")
    except ImportError:
        print("Flask not installed")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
