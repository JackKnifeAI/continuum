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
API Layer Instrumentation
==========================

FastAPI-specific instrumentation for request/response tracing.

Features:
- Request/response span creation
- Route-level spans with endpoint information
- User context injection from JWT/API keys
- Error recording with full stack traces
- Latency histogram metrics
- Request/response size tracking
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes

from .tracer import get_tracer, get_current_span
from .metrics import record_request, increment_counter, record_histogram


class TracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for distributed tracing.

    Automatically creates spans for all HTTP requests and enriches them with:
    - HTTP method, path, status code
    - Request/response headers (configurable)
    - User context (tenant_id, user_id, api_key)
    - Timing information
    - Errors and exceptions
    """

    def __init__(
        self,
        app: ASGIApp,
        tracer_name: str = "continuum.api",
        capture_headers: bool = True,
        capture_body: bool = False,
    ):
        """
        Initialize tracing middleware.

        Args:
            app: ASGI application
            tracer_name: Name for the tracer
            capture_headers: Whether to capture request/response headers
            capture_body: Whether to capture request/response body (use cautiously)
        """
        super().__init__(app)
        self.tracer = get_tracer(tracer_name)
        self.capture_headers = capture_headers
        self.capture_body = capture_body

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Process request with tracing.
        """
        # Extract route information
        route_path = request.url.path
        method = request.method

        # Create span name from route
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope.get("route")
            if hasattr(route, "path"):
                route_path = route.path

        span_name = f"{method} {route_path}"

        # Start span
        with self.tracer.start_as_current_span(
            span_name,
            kind=SpanKind.SERVER,
        ) as span:
            # Set basic HTTP attributes
            span.set_attribute(SpanAttributes.HTTP_METHOD, method)
            span.set_attribute(SpanAttributes.HTTP_URL, str(request.url))
            span.set_attribute(SpanAttributes.HTTP_TARGET, request.url.path)
            span.set_attribute(SpanAttributes.HTTP_SCHEME, request.url.scheme)
            span.set_attribute(SpanAttributes.HTTP_HOST, request.url.hostname or "unknown")

            # Set route attributes
            span.set_attribute("http.route", route_path)
            span.set_attribute("http.flavor", request.scope.get("http_version", "1.1"))

            # Capture headers if enabled
            if self.capture_headers:
                self._capture_request_headers(request, span)

            # Extract tenant context
            tenant_id = self._extract_tenant_id(request)
            if tenant_id:
                span.set_attribute("tenant.id", tenant_id)

            # Extract user context
            user_id = self._extract_user_id(request)
            if user_id:
                span.set_attribute("enduser.id", user_id)

            # Record start time
            start_time = time.time()

            try:
                # Process request
                response = await call_next(request)

                # Set response attributes
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)

                # Set span status based on HTTP status
                if 200 <= response.status_code < 400:
                    span.set_status(Status(StatusCode.OK))
                elif 400 <= response.status_code < 500:
                    span.set_status(Status(StatusCode.ERROR, f"Client error: {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.ERROR, f"Server error: {response.status_code}"))

                # Capture response headers if enabled
                if self.capture_headers:
                    self._capture_response_headers(response, span)

                # Record metrics
                duration = time.time() - start_time
                record_request(
                    method=method,
                    route=route_path,
                    status_code=response.status_code,
                    duration=duration,
                    tenant_id=tenant_id or "unknown",
                )

                return response

            except Exception as e:
                # Record exception
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)

                # Record error metric
                increment_counter(
                    "continuum_errors_total",
                    {
                        "method": method,
                        "route": route_path,
                        "exception_type": type(e).__name__,
                        "tenant_id": tenant_id or "unknown",
                    }
                )

                raise

    def _capture_request_headers(self, request: Request, span: trace.Span):
        """Capture request headers as span attributes"""
        # Capture select headers (avoid sensitive data)
        safe_headers = [
            "content-type",
            "content-length",
            "user-agent",
            "accept",
            "accept-encoding",
        ]

        for header in safe_headers:
            value = request.headers.get(header)
            if value:
                span.set_attribute(f"http.request.header.{header}", value)

    def _capture_response_headers(self, response: Response, span: trace.Span):
        """Capture response headers as span attributes"""
        # Capture select headers
        safe_headers = [
            "content-type",
            "content-length",
        ]

        for header in safe_headers:
            value = response.headers.get(header)
            if value:
                span.set_attribute(f"http.response.header.{header}", value)

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        # Try query parameter
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        # Try header
        tenant_id = request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # Try path parameter
        if hasattr(request, "path_params"):
            tenant_id = request.path_params.get("tenant_id")
            if tenant_id:
                return tenant_id

        return None

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (from JWT or API key)"""
        # Try JWT (would need to decode)
        # For now, try header
        user_id = request.headers.get("x-user-id")
        if user_id:
            return user_id

        # Try API key header
        api_key = request.headers.get("x-api-key")
        if api_key:
            # Use first 8 chars of API key as user identifier
            return api_key[:8]

        return None


def instrument_fastapi_app(app, **kwargs):
    """
    Instrument a FastAPI application with tracing middleware.

    Args:
        app: FastAPI application instance
        **kwargs: Additional arguments for TracingMiddleware

    Example:
        ```python
        from fastapi import FastAPI
        from continuum.observability.api_instrumentation import instrument_fastapi_app

        app = FastAPI()
        instrument_fastapi_app(app)
        ```
    """
    app.add_middleware(TracingMiddleware, **kwargs)


def add_route_span(func: Callable) -> Callable:
    """
    Decorator to add a span for a FastAPI route handler.

    This creates an additional span within the request span for the route handler logic.

    Example:
        ```python
        from continuum.observability.api_instrumentation import add_route_span

        @app.post("/v1/recall")
        @add_route_span
        async def recall_endpoint(request: RecallRequest):
            # Automatically traced with route-specific span
            return response
        ```
    """
    from .tracer import trace_function
    return trace_function(name=f"route.{func.__name__}")(func)


def enrich_span_with_request(request: Request, span: Optional[trace.Span] = None):
    """
    Enrich current or provided span with request information.

    Args:
        request: FastAPI Request object
        span: Optional span to enrich (uses current span if not provided)

    Example:
        ```python
        @app.post("/v1/recall")
        async def recall_endpoint(request: Request):
            enrich_span_with_request(request)
            # Span now has request-specific attributes
        ```
    """
    if span is None:
        span = get_current_span()

    # Add request body size
    if hasattr(request, "headers"):
        content_length = request.headers.get("content-length")
        if content_length:
            span.set_attribute("http.request.body.size", int(content_length))

    # Add query parameters (be careful with sensitive data)
    query_params = dict(request.query_params)
    if query_params:
        # Only add non-sensitive params
        safe_params = {k: v for k, v in query_params.items()
                      if k.lower() not in ["password", "token", "api_key", "secret"]}
        for key, value in safe_params.items():
            span.set_attribute(f"http.query.{key}", value)


def record_api_error(
    error: Exception,
    method: str,
    route: str,
    tenant_id: Optional[str] = None,
):
    """
    Record an API error to metrics and current span.

    Args:
        error: Exception that occurred
        method: HTTP method
        route: Route path
        tenant_id: Optional tenant identifier
    """
    # Get current span
    span = get_current_span()

    # Record exception in span
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)

    # Record metric
    increment_counter(
        "continuum_api_errors_total",
        {
            "method": method,
            "route": route,
            "error_type": type(error).__name__,
            "tenant_id": tenant_id or "unknown",
        }
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
