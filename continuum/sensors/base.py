#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     PLANETARY SENSOR AGGREGATOR - Base Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Base Sensor Collector

Abstract base class for all sensor data collectors.
Provides common HTTP client, error handling, and metrics.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import httpx
import asyncio
import logging

from .config import SensorConfig
from .schemas import SensorReading, DataSource, SensorType

logger = logging.getLogger(__name__)


class BaseSensorCollector(ABC):
    """
    Abstract base class for sensor data collectors.

    All collectors must implement:
    - source: The data source identifier
    - sensor_type: The type of sensor
    - poll_interval: Polling interval in seconds
    - fetch(): Fetch latest readings from the source
    """

    def __init__(self, config: SensorConfig):
        self.config = config
        self.last_poll: Optional[datetime] = None
        self.poll_count: int = 0
        self.error_count: int = 0
        self.consecutive_errors: int = 0
        self._client: Optional[httpx.AsyncClient] = None

    @property
    @abstractmethod
    def source(self) -> DataSource:
        """Data source identifier"""
        pass

    @property
    @abstractmethod
    def sensor_type(self) -> SensorType:
        """Sensor type"""
        pass

    @property
    @abstractmethod
    def poll_interval(self) -> int:
        """Polling interval in seconds"""
        pass

    @abstractmethod
    async def fetch(self) -> List[SensorReading]:
        """
        Fetch latest readings from the source.

        Returns:
            List of SensorReading objects
        """
        pass

    async def collect(self) -> List[SensorReading]:
        """
        Collect readings with error handling and metrics.

        Returns:
            List of SensorReading objects (empty list on error)
        """
        try:
            readings = await self.fetch()
            self.last_poll = datetime.utcnow()
            self.poll_count += 1
            self.consecutive_errors = 0

            logger.info(
                f"[{self.source.value}] Collected {len(readings)} readings"
            )
            return readings

        except httpx.TimeoutException as e:
            self._handle_error(f"Timeout: {e}")
            return []

        except httpx.HTTPStatusError as e:
            self._handle_error(f"HTTP {e.response.status_code}: {e}")
            return []

        except Exception as e:
            self._handle_error(f"Error: {e}")
            return []

    def _handle_error(self, message: str):
        """Handle collection errors"""
        self.error_count += 1
        self.consecutive_errors += 1
        logger.error(f"[{self.source.value}] {message}")

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.config.http_timeout,
                headers={
                    "User-Agent": "JackKnifeAI-Continuum/0.1 (Planetary Sensor Aggregator)"
                },
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_with_retry(
        self,
        url: str,
        headers: dict = None,
        timeout: float = None,
    ) -> httpx.Response:
        """
        Fetch URL with retry logic.

        Args:
            url: URL to fetch
            headers: Optional additional headers
            timeout: Optional custom timeout in seconds

        Returns:
            HTTP response

        Raises:
            httpx.HTTPStatusError: On HTTP error after retries
        """
        client = await self.get_client()
        last_error = None

        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout else self.config.http_timeout

        for attempt in range(self.config.http_retries):
            try:
                response = await client.get(
                    url,
                    headers=request_headers if request_headers else None,
                    timeout=request_timeout,
                )
                response.raise_for_status()
                return response

            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < self.config.http_retries - 1:
                    delay = self.config.http_retry_delay * (attempt + 1)
                    logger.warning(
                        f"[{self.source.value}] Retry {attempt + 1} after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise last_error

    def get_stats(self) -> dict:
        """Get collector statistics"""
        return {
            "source": self.source.value,
            "sensor_type": self.sensor_type.value,
            "last_poll": self.last_poll.isoformat() if self.last_poll else None,
            "poll_count": self.poll_count,
            "error_count": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "poll_interval_seconds": self.poll_interval,
        }

    def should_backoff(self) -> bool:
        """Check if we should back off due to consecutive errors"""
        # Exponential backoff after 3 consecutive errors
        return self.consecutive_errors >= 3

    def get_backoff_delay(self) -> float:
        """Calculate backoff delay based on consecutive errors"""
        if self.consecutive_errors < 3:
            return 0

        # Exponential backoff: 1min, 2min, 4min, max 30min
        delay = min(60 * (2 ** (self.consecutive_errors - 3)), 1800)
        return delay


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
