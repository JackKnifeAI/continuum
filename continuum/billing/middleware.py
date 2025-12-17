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
FastAPI Middleware for Billing and Rate Limiting

Integrates billing checks into the request/response cycle.
"""

from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

from .metering import UsageMetering, RateLimiter
from .tiers import PricingTier, get_tier_limits

logger = logging.getLogger(__name__)


class BillingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for billing enforcement.

    - Checks rate limits before processing requests
    - Records API usage after successful requests
    - Enforces tier-based feature access
    - Tracks concurrent requests
    """

    def __init__(
        self,
        app,
        metering: UsageMetering,
        rate_limiter: RateLimiter,
        get_tenant_tier: Optional[Callable] = None,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize billing middleware.

        Args:
            app: FastAPI application
            metering: UsageMetering instance
            rate_limiter: RateLimiter instance
            get_tenant_tier: Async function to get tenant's pricing tier
            exclude_paths: Paths to exclude from billing (e.g., /health, /docs)
        """
        super().__init__(app)
        self.metering = metering
        self.rate_limiter = rate_limiter
        self.get_tenant_tier_func = get_tenant_tier  # Store but don't call _default_get_tenant_tier yet
        self.exclude_paths = exclude_paths or [
            "/health",
            "/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/v1/billing/webhook",  # Don't rate limit Stripe webhooks
            "/billing/webhook"  # Legacy path (just in case)
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with billing checks"""

        # Skip billing for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Extract tenant ID from request
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing or invalid authentication"}
            )

        # Get tenant's pricing tier
        # Check if custom get_tenant_tier function provided, otherwise use default method
        if self.get_tenant_tier_func:
            tier = await self.get_tenant_tier_func(tenant_id)
        else:
            # Call _default_get_tenant_tier method dynamically to allow test mocking
            tier = await self._default_get_tenant_tier(tenant_id)

        # Store tier in request state for downstream middleware (e.g., DonationNagMiddleware)
        request.state.tier = tier.value

        # Check rate limits
        allowed, error_msg = await self.rate_limiter.check_rate_limit(tenant_id, tier)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {tenant_id}: {error_msg}")
            rate_limit_headers = await self._get_rate_limit_headers(tenant_id, tier)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": error_msg,
                    "tier": tier.value,
                    "upgrade_url": "/billing/upgrade"
                },
                headers=rate_limit_headers
            )

        # Acquire concurrent request slot
        await self.rate_limiter.acquire_request_slot(tenant_id)

        try:
            # Process request
            start_time = time.time()
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Record usage (only for successful requests)
            if 200 <= response.status_code < 400:
                await self.metering.record_api_call(
                    tenant_id=tenant_id,
                    endpoint=request.url.path
                )

            # Add billing headers to response
            response.headers.update(await self._get_rate_limit_headers(tenant_id, tier))
            response.headers["X-Request-Duration-Ms"] = str(int(duration_ms))

            return response

        finally:
            # Release concurrent request slot
            await self.rate_limiter.release_request_slot(tenant_id)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from billing"""
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return True
        return False

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from request.

        Checks (in order):
        1. X-Tenant-ID header
        2. Authorization token claims
        3. API key
        """
        # Check header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # Check auth token (if available in request.state)
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id

        # Check API key (stored in request.state by auth middleware)
        if hasattr(request.state, "api_key_tenant_id"):
            return request.state.api_key_tenant_id

        return None

    async def _default_get_tenant_tier(self, tenant_id: str) -> PricingTier:
        """
        Default implementation: get tier from request state or default to FREE.

        In production, this should query the database or subscription service.
        """
        # This is a placeholder - should be overridden with actual tier lookup
        return PricingTier.FREE

    async def _get_rate_limit_headers(
        self,
        tenant_id: str,
        tier: PricingTier
    ) -> dict:
        """
        Generate rate limit headers for response.

        Returns headers like:
        - X-RateLimit-Limit: 10000
        - X-RateLimit-Remaining: 9543
        - X-RateLimit-Reset: 1640000000
        """
        limits = get_tier_limits(tier)

        # Get current usage
        calls_today = await self.metering.get_usage(tenant_id, 'api_calls', period='day')
        calls_minute = await self.metering.get_usage(tenant_id, 'api_calls', period='minute')

        # Calculate remaining
        remaining_day = max(0, limits.api_calls_per_day - calls_today)
        remaining_minute = max(0, limits.api_calls_per_minute - calls_minute)

        # Calculate reset time (next day at midnight UTC)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        reset_timestamp = int(tomorrow.timestamp())

        return {
            "X-RateLimit-Limit-Day": str(limits.api_calls_per_day),
            "X-RateLimit-Limit-Minute": str(limits.api_calls_per_minute),
            "X-RateLimit-Remaining-Day": str(remaining_day),
            "X-RateLimit-Remaining-Minute": str(remaining_minute),
            "X-RateLimit-Reset": str(reset_timestamp),
            "X-Tier": tier.value
        }


class FeatureAccessMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce feature access based on pricing tier.

    Checks if tenant's tier has access to requested features.
    """

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        get_tenant_tier: Callable,
        feature_map: Optional[dict] = None
    ):
        """
        Initialize feature access middleware.

        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            get_tenant_tier: Async function to get tenant's tier
            feature_map: Map of path prefixes to required features
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.get_tenant_tier = get_tenant_tier
        self.feature_map = feature_map or {
            "/api/federation": "federation",
            "/api/realtime": "realtime_sync",
            "/api/search/semantic": "semantic_search"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check feature access before processing request"""

        # Check if path requires feature access
        required_feature = self._get_required_feature(request.url.path)
        if not required_feature:
            # No feature requirement, proceed
            return await call_next(request)

        # Get tenant ID and tier
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required"}
            )

        tier = await self.get_tenant_tier(tenant_id)

        # Check feature access
        allowed, error_msg = await self.rate_limiter.check_feature_access(
            tier=tier,
            feature=required_feature
        )

        if not allowed:
            logger.warning(f"Feature access denied for {tenant_id}: {error_msg}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": error_msg,
                    "feature": required_feature,
                    "current_tier": tier.value,
                    "upgrade_url": "/billing/upgrade"
                }
            )

        # Feature access granted, proceed
        return await call_next(request)

    def _get_required_feature(self, path: str) -> Optional[str]:
        """Get required feature for a path"""
        for prefix, feature in self.feature_map.items():
            if path.startswith(prefix):
                return feature
        return None

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id
        return request.headers.get("X-Tenant-ID")


class StorageLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check storage limits before write operations.

    Prevents writes if storage quota is exceeded.
    """

    def __init__(
        self,
        app,
        metering: UsageMetering,
        rate_limiter: RateLimiter,
        get_tenant_tier: Callable,
        write_endpoints: Optional[list] = None
    ):
        """
        Initialize storage limit middleware.

        Args:
            app: FastAPI application
            metering: UsageMetering instance
            rate_limiter: RateLimiter instance
            get_tenant_tier: Async function to get tenant's tier
            write_endpoints: List of endpoint prefixes that write data
        """
        super().__init__(app)
        self.metering = metering
        self.rate_limiter = rate_limiter
        self.get_tenant_tier = get_tenant_tier
        self.write_endpoints = write_endpoints or [
            "/api/memories",
            "/api/embeddings",
            "/api/extraction"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check storage limits before write operations"""

        # Only check for write operations
        if not self._is_write_operation(request):
            return await call_next(request)

        # Get tenant ID and tier
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required"}
            )

        tier = await self.get_tenant_tier(tenant_id)

        # Check storage limits
        allowed, error_msg = await self.rate_limiter.check_storage_limit(
            tenant_id=tenant_id,
            tier=tier
        )

        if not allowed:
            logger.warning(f"Storage limit exceeded for {tenant_id}: {error_msg}")
            usage = await self.metering.get_storage_usage(tenant_id)
            return JSONResponse(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                content={
                    "error": error_msg,
                    "current_usage": usage,
                    "tier": tier.value,
                    "upgrade_url": "/billing/upgrade"
                }
            )

        # Storage limit OK, proceed
        return await call_next(request)

    def _is_write_operation(self, request: Request) -> bool:
        """Check if request is a write operation"""
        if request.method not in ["POST", "PUT", "PATCH"]:
            return False

        for endpoint in self.write_endpoints:
            if request.url.path.startswith(endpoint):
                return True

        return False

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id
        return request.headers.get("X-Tenant-ID")


class FederationContributionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tier-based federation contribution policies.

    FREE tier: MANDATORY contribution with aggressive anonymization
    PRO tier: OPTIONAL contribution with standard anonymization
    ENTERPRISE tier: OPTIONAL contribution with no anonymization

    This is the MOAT - prevents freeloading and builds network effects.
    """

    def __init__(
        self,
        app,
        get_tenant_tier: Callable,
        write_endpoints: Optional[list] = None
    ):
        """
        Initialize federation contribution middleware.

        Args:
            app: FastAPI application
            get_tenant_tier: Async function to get tenant's tier
            write_endpoints: Memory write endpoints that trigger contribution
        """
        super().__init__(app)
        self.get_tenant_tier = get_tenant_tier
        self.write_endpoints = write_endpoints or [
            "/api/memories",
            "/api/concepts",
            "/api/extraction"
        ]

        # Import here to avoid circular dependency
        from ..federation.tier_enforcer import create_enforcer
        from ..federation.shared import SharedKnowledge

        self.enforcer = create_enforcer()
        self.shared_knowledge = SharedKnowledge()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce contribution policy on memory write operations"""

        # Only check memory write operations
        if not self._is_memory_write(request):
            return await call_next(request)

        # Extract tenant ID
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required"}
            )

        # Get tenant's pricing tier
        tier = await self.get_tenant_tier(tenant_id)

        # Check if opt-out was requested
        opt_out_requested = request.headers.get("X-Federation-Opt-Out", "false").lower() == "true"

        # Enforce contribution policy
        allowed, error_msg, metadata = self.enforcer.enforce_contribution(
            tenant_id=tenant_id,
            tier=tier,
            memory_operation="write",
            opt_out_requested=opt_out_requested
        )

        if not allowed:
            logger.warning(
                f"Federation contribution opt-out blocked for {tenant_id} "
                f"on {tier.value} tier"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": error_msg,
                    "tier": tier.value,
                    "policy": "mandatory",
                    "message": (
                        "FREE tier users must contribute to the federation network. "
                        "Upgrade to PRO ($29/mo) or ENTERPRISE to control contribution preferences."
                    ),
                    "upgrade_url": "/billing/upgrade"
                }
            )

        # Process the request
        response = await call_next(request)

        # If successful write and contribution is required, contribute to federation
        if 200 <= response.status_code < 400 and metadata.get("contribution_required"):
            # Store request body for post-processing
            # In production, this would use background task to avoid blocking response
            if hasattr(request.state, "memory_data"):
                await self._contribute_to_federation(
                    tenant_id=tenant_id,
                    tier=tier,
                    memory_data=request.state.memory_data
                )

        return response

    async def _contribute_to_federation(
        self,
        tenant_id: str,
        tier: PricingTier,
        memory_data: Dict[str, Any]
    ) -> None:
        """
        Contribute memory to federation pool (background task).

        Args:
            tenant_id: Tenant ID
            tier: Pricing tier
            memory_data: Memory data to contribute
        """
        try:
            # Anonymize based on tier
            anonymized = self.enforcer.anonymize_memory(
                memory=memory_data,
                tier=tier,
                embedding=memory_data.get("embedding")
            )

            # Contribute to shared pool
            result = self.shared_knowledge.contribute_concepts(
                node_id=f"tenant:{tenant_id}",
                concepts=[anonymized]
            )

            # Track contribution
            self.enforcer.track_contribution(
                tenant_id=tenant_id,
                contributed=result.get("new_concepts", 0),
                consumed=0
            )

            logger.info(
                f"Federation contribution: tenant={tenant_id}, "
                f"tier={tier.value}, contributed={result.get('new_concepts', 0)}"
            )

        except Exception as e:
            logger.error(f"Federation contribution failed: {e}", exc_info=True)

    def _is_memory_write(self, request: Request) -> bool:
        """Check if request is a memory write operation"""
        if request.method not in ["POST", "PUT", "PATCH"]:
            return False

        for endpoint in self.write_endpoints:
            if request.url.path.startswith(endpoint):
                return True

        return False

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        if hasattr(request.state, "tenant_id"):
            return request.state.tenant_id
        return request.headers.get("X-Tenant-ID")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
