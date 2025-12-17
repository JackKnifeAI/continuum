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
OpenTelemetry Sampling Strategies
==================================

Provides various sampling strategies for controlling trace volume and cost.

Sampling Strategies:
- AlwaysOn: Sample all traces (development)
- AlwaysOff: Sample no traces (testing)
- TraceIdRatio: Sample a percentage of traces
- ParentBased: Respect parent span sampling decision
- ErrorBased: Always sample errors, probabilistically sample success
"""

from typing import Optional, Sequence
from opentelemetry.sdk.trace.sampling import (
    Sampler,
    SamplingResult,
    Decision,
    TraceIdRatioBased,
    ParentBased,
    ALWAYS_ON,
    ALWAYS_OFF,
)
from opentelemetry.trace import Link, SpanKind
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes

from .config import OTelConfig


class ErrorAlwaysSampler(Sampler):
    """
    Custom sampler that always samples errors, probabilistically samples success.

    This is useful for production environments where you want to capture all errors
    while still controlling the volume of successful request traces.
    """

    def __init__(self, success_rate: float = 0.1):
        """
        Initialize error-always sampler.

        Args:
            success_rate: Sampling rate for successful operations (0.0-1.0)
        """
        self.success_rate = success_rate
        self.ratio_sampler = TraceIdRatioBased(success_rate)

    def should_sample(
        self,
        parent_context: Optional["SpanContext"],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Attributes = None,
        links: Sequence[Link] = None,
        trace_state: Optional[TraceState] = None,
    ) -> SamplingResult:
        """
        Determine if trace should be sampled.

        Always samples if:
        - Span has error/exception attributes
        - HTTP status code >= 400
        - Span name contains 'error', 'exception', 'fail'

        Otherwise samples based on success_rate.
        """
        # Check for error indicators
        if attributes:
            # HTTP status code
            http_status = attributes.get("http.status_code")
            if http_status and int(http_status) >= 400:
                return SamplingResult(
                    decision=Decision.RECORD_AND_SAMPLE,
                    attributes=attributes,
                )

            # Error/exception attributes
            if "error" in attributes or "exception" in attributes:
                return SamplingResult(
                    decision=Decision.RECORD_AND_SAMPLE,
                    attributes=attributes,
                )

        # Check span name for error indicators
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in ["error", "exception", "fail", "fault"]):
            return SamplingResult(
                decision=Decision.RECORD_AND_SAMPLE,
                attributes=attributes,
            )

        # For non-errors, use ratio-based sampling
        return self.ratio_sampler.should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state
        )

    def get_description(self) -> str:
        """Get sampler description"""
        return f"ErrorAlwaysSampler(success_rate={self.success_rate})"


class RateLimitedSampler(Sampler):
    """
    Rate-limited sampler that caps the number of traces per second.

    Useful for protecting downstream trace collectors from being overwhelmed.
    """

    def __init__(self, max_traces_per_second: int = 100):
        """
        Initialize rate-limited sampler.

        Args:
            max_traces_per_second: Maximum traces to sample per second
        """
        self.max_traces_per_second = max_traces_per_second
        self._traces_this_second = 0
        self._current_second = 0

    def should_sample(
        self,
        parent_context: Optional["SpanContext"],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Attributes = None,
        links: Sequence[Link] = None,
        trace_state: Optional[TraceState] = None,
    ) -> SamplingResult:
        """
        Determine if trace should be sampled based on rate limit.
        """
        import time

        current_second = int(time.time())

        # Reset counter if we're in a new second
        if current_second != self._current_second:
            self._current_second = current_second
            self._traces_this_second = 0

        # Check if we're under the rate limit
        if self._traces_this_second < self.max_traces_per_second:
            self._traces_this_second += 1
            return SamplingResult(
                decision=Decision.RECORD_AND_SAMPLE,
                attributes=attributes,
            )
        else:
            return SamplingResult(
                decision=Decision.DROP,
                attributes=attributes,
            )

    def get_description(self) -> str:
        """Get sampler description"""
        return f"RateLimitedSampler(max_traces_per_second={self.max_traces_per_second})"


class AdaptiveSampler(Sampler):
    """
    Adaptive sampler that adjusts sampling rate based on traffic volume.

    Increases sampling during low traffic, decreases during high traffic.
    """

    def __init__(
        self,
        min_rate: float = 0.01,
        max_rate: float = 1.0,
        target_traces_per_minute: int = 1000,
    ):
        """
        Initialize adaptive sampler.

        Args:
            min_rate: Minimum sampling rate
            max_rate: Maximum sampling rate
            target_traces_per_minute: Target number of traces per minute
        """
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.target_traces_per_minute = target_traces_per_minute
        self.current_rate = max_rate

        # Tracking
        self._total_requests = 0
        self._sampled_requests = 0
        self._window_start = 0

    def should_sample(
        self,
        parent_context: Optional["SpanContext"],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Attributes = None,
        links: Sequence[Link] = None,
        trace_state: Optional[TraceState] = None,
    ) -> SamplingResult:
        """
        Determine if trace should be sampled, adjusting rate adaptively.
        """
        import time
        import random

        current_time = time.time()

        # Reset window every minute
        if current_time - self._window_start > 60:
            self._adjust_rate()
            self._window_start = current_time
            self._total_requests = 0
            self._sampled_requests = 0

        self._total_requests += 1

        # Sample based on current rate
        if random.random() < self.current_rate:
            self._sampled_requests += 1
            return SamplingResult(
                decision=Decision.RECORD_AND_SAMPLE,
                attributes=attributes,
            )
        else:
            return SamplingResult(
                decision=Decision.DROP,
                attributes=attributes,
            )

    def _adjust_rate(self):
        """Adjust sampling rate based on recent traffic"""
        if self._sampled_requests == 0:
            # No traffic, keep current rate
            return

        # Calculate desired adjustment
        if self._sampled_requests < self.target_traces_per_minute:
            # Increase sampling rate
            self.current_rate = min(self.max_rate, self.current_rate * 1.2)
        elif self._sampled_requests > self.target_traces_per_minute:
            # Decrease sampling rate
            self.current_rate = max(self.min_rate, self.current_rate * 0.8)

    def get_description(self) -> str:
        """Get sampler description"""
        return f"AdaptiveSampler(current_rate={self.current_rate:.3f})"


def get_sampler(config: OTelConfig) -> Sampler:
    """
    Get appropriate sampler based on configuration.

    Args:
        config: OTel configuration

    Returns:
        Sampler instance
    """
    # Development: always sample
    if config.is_dev_environment():
        return ALWAYS_ON

    # Production: use configured strategy
    if config.sample_errors_always:
        # Error-always sampler with parent-based wrapper
        base_sampler = ErrorAlwaysSampler(success_rate=config.sampling_rate)
        return ParentBased(root=base_sampler)
    else:
        # Standard ratio-based sampling with parent-based wrapper
        base_sampler = TraceIdRatioBased(config.sampling_rate)
        return ParentBased(root=base_sampler)


def get_always_on_sampler() -> Sampler:
    """Get always-on sampler"""
    return ALWAYS_ON


def get_always_off_sampler() -> Sampler:
    """Get always-off sampler"""
    return ALWAYS_OFF


def get_ratio_sampler(rate: float) -> Sampler:
    """Get ratio-based sampler"""
    return ParentBased(root=TraceIdRatioBased(rate))


def get_error_sampler(success_rate: float = 0.1) -> Sampler:
    """Get error-always sampler"""
    return ParentBased(root=ErrorAlwaysSampler(success_rate))


def get_rate_limited_sampler(max_per_second: int = 100) -> Sampler:
    """Get rate-limited sampler"""
    return ParentBased(root=RateLimitedSampler(max_per_second))


def get_adaptive_sampler(
    target_per_minute: int = 1000,
    min_rate: float = 0.01,
    max_rate: float = 1.0,
) -> Sampler:
    """Get adaptive sampler"""
    return ParentBased(
        root=AdaptiveSampler(
            min_rate=min_rate,
            max_rate=max_rate,
            target_traces_per_minute=target_per_minute,
        )
    )

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
