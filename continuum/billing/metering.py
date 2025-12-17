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
Usage Metering and Rate Limiting for CONTINUUM

Tracks API calls, storage usage, and federation contributions.
Enforces rate limits based on pricing tier.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from collections import defaultdict
import logging

from .tiers import PricingTier, TierLimits, get_tier_limits

logger = logging.getLogger(__name__)


class UsageMetering:
    """
    Track usage metrics for billing and analytics.

    Stores:
    - API call counts per tenant
    - Storage usage (memories, embeddings, bytes)
    - Federation contributions (shared memories)
    - Extraction operations
    """

    def __init__(self, storage_backend=None):
        """
        Initialize usage metering.

        Args:
            storage_backend: Optional storage backend (defaults to in-memory)
        """
        self.storage = storage_backend
        # In-memory cache for recent usage (flush to storage periodically)
        self._usage_cache: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._last_flush = datetime.now(timezone.utc)

    async def record_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record an API call.

        Args:
            tenant_id: Tenant identifier
            endpoint: API endpoint called
            timestamp: Call timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Increment counters
        day_key = timestamp.strftime("%Y-%m-%d")
        minute_key = timestamp.strftime("%Y-%m-%d-%H-%M")

        # Track per-day usage (for daily limits)
        day_cache_key = f"{tenant_id}:{day_key}"
        self._usage_cache[day_cache_key]['api_calls'] += 1

        # Track per-minute usage (for rate limiting)
        minute_cache_key = f"{tenant_id}:{minute_key}"
        self._usage_cache[minute_cache_key]['api_calls'] += 1

        # Track endpoint-specific usage
        self._usage_cache[day_cache_key][f'endpoint:{endpoint}'] += 1

        logger.debug(f"Recorded API call for {tenant_id}: {endpoint}")

        # Flush periodically
        await self._flush_if_needed()

    async def record_storage_usage(
        self,
        tenant_id: str,
        memories: int = 0,
        embeddings: int = 0,
        bytes_used: int = 0
    ) -> None:
        """
        Record storage usage.

        Args:
            tenant_id: Tenant identifier
            memories: Number of memories stored
            embeddings: Number of embeddings stored
            bytes_used: Total bytes used
        """
        cache_key = f"{tenant_id}:storage"

        if memories > 0:
            self._usage_cache[cache_key]['memories'] = memories
        if embeddings > 0:
            self._usage_cache[cache_key]['embeddings'] = embeddings
        if bytes_used > 0:
            self._usage_cache[cache_key]['bytes'] = bytes_used

        logger.debug(f"Recorded storage for {tenant_id}: {memories} memories, {bytes_used} bytes")

        await self._flush_if_needed()

    async def record_federation_contribution(
        self,
        tenant_id: str,
        shared_memories: int = 1
    ) -> None:
        """
        Record federation contributions (shared memories).

        Args:
            tenant_id: Tenant identifier
            shared_memories: Number of memories shared
        """
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_key = f"{tenant_id}:{day_key}"

        self._usage_cache[cache_key]['federation_shares'] += shared_memories

        logger.debug(f"Recorded federation contribution for {tenant_id}: {shared_memories}")

        await self._flush_if_needed()

    async def record_extraction(
        self,
        tenant_id: str,
        batch_size: int = 1
    ) -> None:
        """
        Record knowledge extraction operation.

        Args:
            tenant_id: Tenant identifier
            batch_size: Number of items extracted
        """
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_key = f"{tenant_id}:{day_key}"

        self._usage_cache[cache_key]['extractions'] += 1
        self._usage_cache[cache_key]['extraction_items'] += batch_size

        logger.debug(f"Recorded extraction for {tenant_id}: {batch_size} items")

        await self._flush_if_needed()

    async def get_usage(
        self,
        tenant_id: str,
        metric: str,
        period: str = "day"
    ) -> int:
        """
        Get usage for a tenant.

        Args:
            tenant_id: Tenant identifier
            metric: Metric name (e.g., 'api_calls', 'memories')
            period: Time period ('day', 'minute', 'month')

        Returns:
            Usage count
        """
        now = datetime.now(timezone.utc)

        if period == "day":
            key = now.strftime("%Y-%m-%d")
        elif period == "minute":
            key = now.strftime("%Y-%m-%d-%H-%M")
        elif period == "month":
            key = now.strftime("%Y-%m")
        else:
            raise ValueError(f"Invalid period: {period}")

        cache_key = f"{tenant_id}:{key}"
        return self._usage_cache.get(cache_key, {}).get(metric, 0)

    async def get_storage_usage(self, tenant_id: str) -> Dict[str, int]:
        """
        Get current storage usage.

        Returns:
            Dict with keys: memories, embeddings, bytes
        """
        cache_key = f"{tenant_id}:storage"
        return dict(self._usage_cache.get(cache_key, {}))

    async def set_usage(
        self,
        tenant_id: str,
        metric: str,
        value: int,
        period: str = "day"
    ) -> None:
        """
        Set usage value for a tenant (useful for testing).

        Args:
            tenant_id: Tenant identifier
            metric: Metric name (e.g., 'api_calls', 'memories')
            value: Value to set
            period: Time period ('day', 'minute', 'month')
        """
        now = datetime.now(timezone.utc)

        if period == "day":
            key = now.strftime("%Y-%m-%d")
        elif period == "minute":
            key = now.strftime("%Y-%m-%d-%H-%M")
        elif period == "month":
            key = now.strftime("%Y-%m")
        else:
            raise ValueError(f"Invalid period: {period}")

        cache_key = f"{tenant_id}:{key}"
        self._usage_cache[cache_key][metric] = value
        logger.debug(f"Set usage for {tenant_id}: {metric}={value} ({period})")

    async def _flush_if_needed(self) -> None:
        """Flush cache to storage if needed (every 60 seconds)"""
        now = datetime.now(timezone.utc)
        if (now - self._last_flush).total_seconds() > 60:
            await self._flush_cache()

    async def _flush_cache(self) -> None:
        """Flush cache to persistent storage"""
        if self.storage:
            try:
                # TODO: Implement storage backend flush
                logger.debug("Flushing usage cache to storage")
                # await self.storage.save_usage(self._usage_cache)
                pass
            except Exception as e:
                logger.error(f"Failed to flush usage cache: {e}")

        self._last_flush = datetime.now(timezone.utc)


class RateLimiter:
    """
    Enforce rate limits based on pricing tier.

    Implements sliding window rate limiting for:
    - API calls per day
    - API calls per minute
    - Concurrent requests
    """

    def __init__(self, metering: UsageMetering):
        """
        Initialize rate limiter.

        Args:
            metering: UsageMetering instance
        """
        self.metering = metering
        self._concurrent_requests: Dict[str, int] = defaultdict(int)

    async def check_rate_limit(
        self,
        tenant_id: str,
        tier: PricingTier
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.

        Args:
            tenant_id: Tenant identifier
            tier: Pricing tier

        Returns:
            Tuple of (allowed, error_message)
            - (True, None) if allowed
            - (False, "reason") if rate limited
        """
        limits = get_tier_limits(tier)

        # Check concurrent requests
        concurrent = self._concurrent_requests.get(tenant_id, 0)
        if concurrent >= limits.concurrent_requests:
            return False, f"Concurrent request limit exceeded ({limits.concurrent_requests})"

        # Check per-minute limit
        calls_per_minute = await self.metering.get_usage(tenant_id, 'api_calls', period='minute')
        if calls_per_minute >= limits.api_calls_per_minute:
            return False, f"Rate limit exceeded ({limits.api_calls_per_minute} calls/minute)"

        # Check per-day limit
        calls_per_day = await self.metering.get_usage(tenant_id, 'api_calls', period='day')
        if calls_per_day >= limits.api_calls_per_day:
            return False, f"Rate limit exceeded: Daily limit ({limits.api_calls_per_day} calls/day)"

        return True, None

    async def check_storage_limit(
        self,
        tenant_id: str,
        tier: PricingTier
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if storage is within limits.

        Args:
            tenant_id: Tenant identifier
            tier: Pricing tier

        Returns:
            Tuple of (allowed, error_message)
        """
        limits = get_tier_limits(tier)
        usage = await self.metering.get_storage_usage(tenant_id)

        # Check memory count
        memories = usage.get('memories', 0)
        if memories >= limits.max_memories:
            return False, f"Memory limit exceeded ({limits.max_memories})"

        # Check embeddings count
        embeddings = usage.get('embeddings', 0)
        if embeddings >= limits.max_embeddings:
            return False, f"Embedding limit exceeded ({limits.max_embeddings})"

        # Check storage size
        bytes_used = usage.get('bytes', 0)
        mb_used = bytes_used / (1024 * 1024)
        if mb_used >= limits.max_storage_mb:
            return False, f"Storage limit exceeded ({limits.max_storage_mb} MB)"

        return True, None

    async def check_feature_access(
        self,
        tier: PricingTier,
        feature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if tier has access to a feature.

        Args:
            tier: Pricing tier
            feature: Feature name (e.g., 'federation', 'realtime_sync')

        Returns:
            Tuple of (allowed, error_message)
        """
        limits = get_tier_limits(tier)

        feature_map = {
            'federation': limits.federation_enabled,
            'realtime_sync': limits.realtime_sync_enabled,
            'semantic_search': limits.semantic_search_enabled
        }

        if feature not in feature_map:
            return False, f"Unknown feature: {feature}"

        if not feature_map[feature]:
            return False, f"Feature '{feature}' not available on {tier.value} tier"

        return True, None

    async def acquire_request_slot(self, tenant_id: str) -> None:
        """Acquire a concurrent request slot"""
        self._concurrent_requests[tenant_id] += 1

    async def release_request_slot(self, tenant_id: str) -> None:
        """Release a concurrent request slot"""
        if self._concurrent_requests[tenant_id] > 0:
            self._concurrent_requests[tenant_id] -= 1


class UsageReporter:
    """
    Report usage to Stripe for metered billing.

    Aggregates usage and reports to Stripe at regular intervals.
    """

    def __init__(
        self,
        metering: UsageMetering,
        stripe_client,
        report_interval_seconds: int = 3600  # 1 hour
    ):
        """
        Initialize usage reporter.

        Args:
            metering: UsageMetering instance
            stripe_client: StripeClient instance
            report_interval_seconds: How often to report usage
        """
        self.metering = metering
        self.stripe_client = stripe_client
        self.report_interval = report_interval_seconds
        self._last_report: Dict[str, datetime] = {}

    async def report_usage_to_stripe(
        self,
        tenant_id: str,
        subscription_item_id: str
    ) -> None:
        """
        Report aggregated usage to Stripe.

        Args:
            tenant_id: Tenant identifier
            subscription_item_id: Stripe subscription item ID
        """
        # Check if we should report (once per interval)
        now = datetime.now(timezone.utc)
        last_report = self._last_report.get(tenant_id)

        if last_report and (now - last_report).total_seconds() < self.report_interval:
            return  # Too soon

        try:
            # Get usage since last report
            api_calls = await self.metering.get_usage(tenant_id, 'api_calls', period='day')

            if api_calls > 0:
                # Report to Stripe
                await self.stripe_client.report_usage(
                    subscription_item_id=subscription_item_id,
                    quantity=api_calls,
                    action='increment'
                )

                logger.info(f"Reported {api_calls} API calls to Stripe for {tenant_id}")

            self._last_report[tenant_id] = now

        except Exception as e:
            logger.error(f"Failed to report usage to Stripe: {e}")

    async def start_background_reporting(self) -> None:
        """Start background task to report usage periodically"""
        while True:
            await asyncio.sleep(self.report_interval)
            # TODO: Iterate over all active subscriptions and report usage
            logger.debug("Background usage reporting tick")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
