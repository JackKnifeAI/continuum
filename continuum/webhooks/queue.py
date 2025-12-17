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
Delivery Queue
==============

Redis-backed queue for async webhook delivery with retry scheduling.

Features:
    - Priority queue (high/normal/low)
    - Delayed retry scheduling
    - Dead letter queue
    - Queue depth monitoring
    - Worker pool coordination

Usage:
    queue = DeliveryQueue(redis_url="redis://localhost")

    # Enqueue delivery
    await queue.enqueue(delivery, priority="high")

    # Worker processes queue
    async for delivery in queue.consume():
        await dispatcher.dispatch(...)
"""

import asyncio
import json
import logging
from typing import Optional, AsyncIterator
from datetime import datetime, timedelta
from uuid import UUID

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .models import WebhookDelivery, DeliveryStatus

logger = logging.getLogger(__name__)


class DeliveryQueue:
    """
    Redis-backed queue for webhook deliveries.

    Queue Structure:
        - webhook:queue:high - High priority queue
        - webhook:queue:normal - Normal priority queue
        - webhook:queue:low - Low priority queue
        - webhook:queue:delayed - Delayed retries (sorted set by timestamp)
        - webhook:queue:dlq - Dead letter queue

    Features:
        - Priority-based processing
        - Scheduled delayed retries
        - Worker coordination
        - Queue metrics
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize delivery queue.

        Args:
            redis_url: Redis connection URL

        Raises:
            ImportError: If redis is not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for DeliveryQueue. Install with: pip install redis")

        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None

        # Queue keys
        self.HIGH_QUEUE = "webhook:queue:high"
        self.NORMAL_QUEUE = "webhook:queue:normal"
        self.LOW_QUEUE = "webhook:queue:low"
        self.DELAYED_QUEUE = "webhook:queue:delayed"
        self.DLQ = "webhook:queue:dlq"

        # Metrics
        self.METRICS_KEY = "webhook:metrics"

    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def enqueue(
        self,
        delivery: WebhookDelivery,
        priority: str = "normal",
        delay: Optional[timedelta] = None
    ):
        """
        Enqueue a delivery.

        Args:
            delivery: Delivery to enqueue
            priority: Queue priority (high/normal/low)
            delay: Optional delay before processing

        Example:
            # Immediate delivery
            await queue.enqueue(delivery, priority="high")

            # Delayed retry
            await queue.enqueue(delivery, delay=timedelta(seconds=30))
        """
        await self.connect()

        delivery_data = json.dumps(delivery.to_dict())

        if delay:
            # Add to delayed queue (sorted set by timestamp)
            process_at = datetime.utcnow() + delay
            score = process_at.timestamp()
            await self.redis.zadd(self.DELAYED_QUEUE, {delivery_data: score})
            logger.debug(f"Enqueued delivery {delivery.id} with {delay.total_seconds()}s delay")
        else:
            # Add to priority queue
            queue_key = self._get_queue_key(priority)
            await self.redis.lpush(queue_key, delivery_data)
            logger.debug(f"Enqueued delivery {delivery.id} to {priority} queue")

        # Update metrics
        await self._increment_metric("enqueued")

    async def dequeue(self, timeout: int = 5) -> Optional[WebhookDelivery]:
        """
        Dequeue next delivery (blocks until available).

        Args:
            timeout: Blocking timeout in seconds

        Returns:
            Next delivery or None if timeout

        Example:
            delivery = await queue.dequeue()
            if delivery:
                await process(delivery)
        """
        await self.connect()

        # Check delayed queue first
        await self._process_delayed()

        # Block on priority queues (high -> normal -> low)
        result = await self.redis.brpop(
            [self.HIGH_QUEUE, self.NORMAL_QUEUE, self.LOW_QUEUE],
            timeout=timeout
        )

        if result:
            queue_key, delivery_data = result
            delivery_dict = json.loads(delivery_data)

            # Reconstruct delivery
            delivery = WebhookDelivery(**delivery_dict)
            logger.debug(f"Dequeued delivery {delivery.id}")

            await self._increment_metric("dequeued")
            return delivery

        return None

    async def consume(self) -> AsyncIterator[WebhookDelivery]:
        """
        Async iterator for consuming queue.

        Yields:
            WebhookDelivery instances

        Example:
            async for delivery in queue.consume():
                success = await dispatcher.dispatch(delivery)
                if not success:
                    await queue.enqueue(delivery, delay=timedelta(seconds=30))
        """
        while True:
            delivery = await self.dequeue()
            if delivery:
                yield delivery

    async def _process_delayed(self):
        """Move delayed deliveries to main queue if ready."""
        await self.connect()

        now = datetime.utcnow().timestamp()

        # Get all deliveries ready for processing
        ready = await self.redis.zrangebyscore(
            self.DELAYED_QUEUE,
            0,
            now
        )

        for delivery_data in ready:
            # Move to normal queue
            await self.redis.lpush(self.NORMAL_QUEUE, delivery_data)

            # Remove from delayed queue
            await self.redis.zrem(self.DELAYED_QUEUE, delivery_data)

            logger.debug(f"Moved delayed delivery to normal queue")

    async def move_to_dlq(self, delivery: WebhookDelivery):
        """
        Move delivery to dead letter queue.

        Args:
            delivery: Failed delivery

        Example:
            if delivery.attempts >= MAX_RETRIES:
                await queue.move_to_dlq(delivery)
        """
        await self.connect()

        delivery_data = json.dumps(delivery.to_dict())
        await self.redis.lpush(self.DLQ, delivery_data)

        logger.warning(f"Moved delivery {delivery.id} to dead letter queue")
        await self._increment_metric("dlq")

    async def get_queue_depth(self) -> dict[str, int]:
        """
        Get current queue depths.

        Returns:
            Dictionary of queue depths

        Example:
            depths = await queue.get_queue_depth()
            print(f"High priority: {depths['high']}")
        """
        await self.connect()

        return {
            "high": await self.redis.llen(self.HIGH_QUEUE),
            "normal": await self.redis.llen(self.NORMAL_QUEUE),
            "low": await self.redis.llen(self.LOW_QUEUE),
            "delayed": await self.redis.zcard(self.DELAYED_QUEUE),
            "dlq": await self.redis.llen(self.DLQ)
        }

    async def get_metrics(self) -> dict[str, int]:
        """
        Get queue metrics.

        Returns:
            Dictionary of metrics

        Example:
            metrics = await queue.get_metrics()
            print(f"Total enqueued: {metrics['enqueued']}")
        """
        await self.connect()

        metrics = await self.redis.hgetall(self.METRICS_KEY)
        return {k: int(v) for k, v in metrics.items()}

    async def clear_queue(self, queue: str = "all"):
        """
        Clear queue(s) - use with caution!

        Args:
            queue: Which queue to clear (all/high/normal/low/delayed/dlq)
        """
        await self.connect()

        if queue == "all":
            await self.redis.delete(
                self.HIGH_QUEUE,
                self.NORMAL_QUEUE,
                self.LOW_QUEUE,
                self.DELAYED_QUEUE,
                self.DLQ
            )
            logger.warning("Cleared all queues")
        else:
            queue_key = self._get_queue_key(queue)
            await self.redis.delete(queue_key)
            logger.warning(f"Cleared {queue} queue")

    def _get_queue_key(self, priority: str) -> str:
        """Get Redis key for priority level."""
        mapping = {
            "high": self.HIGH_QUEUE,
            "normal": self.NORMAL_QUEUE,
            "low": self.LOW_QUEUE,
            "delayed": self.DELAYED_QUEUE,
            "dlq": self.DLQ
        }
        return mapping.get(priority, self.NORMAL_QUEUE)

    async def _increment_metric(self, metric: str):
        """Increment a metric counter."""
        await self.redis.hincrby(self.METRICS_KEY, metric, 1)


class InMemoryQueue:
    """
    In-memory queue for development/testing (no Redis required).

    Simpler implementation without persistence.
    Use DeliveryQueue with Redis in production.
    """

    def __init__(self):
        """Initialize in-memory queue."""
        self.high_queue: asyncio.Queue = asyncio.Queue()
        self.normal_queue: asyncio.Queue = asyncio.Queue()
        self.low_queue: asyncio.Queue = asyncio.Queue()
        self.delayed: list[tuple[datetime, WebhookDelivery]] = []
        self.dlq: list[WebhookDelivery] = []

        self.metrics = {
            "enqueued": 0,
            "dequeued": 0,
            "dlq": 0
        }

    async def connect(self):
        """No-op for in-memory queue."""
        pass

    async def disconnect(self):
        """No-op for in-memory queue."""
        pass

    async def enqueue(
        self,
        delivery: WebhookDelivery,
        priority: str = "normal",
        delay: Optional[timedelta] = None
    ):
        """Enqueue delivery."""
        if delay:
            process_at = datetime.utcnow() + delay
            self.delayed.append((process_at, delivery))
            self.delayed.sort(key=lambda x: x[0])
        else:
            queue = self._get_queue(priority)
            await queue.put(delivery)

        self.metrics["enqueued"] += 1

    async def dequeue(self, timeout: int = 5) -> Optional[WebhookDelivery]:
        """Dequeue next delivery."""
        # Process delayed
        await self._process_delayed()

        # Try queues in priority order
        for queue in [self.high_queue, self.normal_queue, self.low_queue]:
            try:
                delivery = queue.get_nowait()
                self.metrics["dequeued"] += 1
                return delivery
            except asyncio.QueueEmpty:
                continue

        # Wait for any delivery
        try:
            delivery = await asyncio.wait_for(
                self._wait_any_queue(),
                timeout=timeout
            )
            self.metrics["dequeued"] += 1
            return delivery
        except asyncio.TimeoutError:
            return None

    async def consume(self) -> AsyncIterator[WebhookDelivery]:
        """Async iterator for consuming queue."""
        while True:
            delivery = await self.dequeue()
            if delivery:
                yield delivery

    async def move_to_dlq(self, delivery: WebhookDelivery):
        """Move to dead letter queue."""
        self.dlq.append(delivery)
        self.metrics["dlq"] += 1

    async def get_queue_depth(self) -> dict[str, int]:
        """Get queue depths."""
        return {
            "high": self.high_queue.qsize(),
            "normal": self.normal_queue.qsize(),
            "low": self.low_queue.qsize(),
            "delayed": len(self.delayed),
            "dlq": len(self.dlq)
        }

    async def get_metrics(self) -> dict[str, int]:
        """Get metrics."""
        return self.metrics.copy()

    async def _process_delayed(self):
        """Move ready delayed deliveries to queue."""
        now = datetime.utcnow()
        ready = []

        for i, (process_at, delivery) in enumerate(self.delayed):
            if process_at <= now:
                ready.append(i)
                await self.normal_queue.put(delivery)

        # Remove processed
        for i in reversed(ready):
            self.delayed.pop(i)

    async def _wait_any_queue(self) -> WebhookDelivery:
        """Wait for delivery from any queue."""
        tasks = [
            self.high_queue.get(),
            self.normal_queue.get(),
            self.low_queue.get()
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel pending
        for task in pending:
            task.cancel()

        # Return first result
        return done.pop().result()

    def _get_queue(self, priority: str) -> asyncio.Queue:
        """Get queue for priority."""
        mapping = {
            "high": self.high_queue,
            "normal": self.normal_queue,
            "low": self.low_queue
        }
        return mapping.get(priority, self.normal_queue)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
