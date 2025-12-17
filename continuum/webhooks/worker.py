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
Webhook Delivery Worker
========================

Background worker for processing webhook deliveries.

Features:
    - Async worker pool
    - Graceful shutdown
    - Health monitoring
    - Automatic retry scheduling
    - Metrics collection

Usage:
    # Start worker
    worker = WebhookWorker(storage=storage, queue=queue, num_workers=10)
    await worker.start()

    # Or run as standalone process
    python -m continuum.webhooks.worker --workers 10
"""

import asyncio
import signal
import logging
from typing import Optional
from datetime import datetime, timedelta
import sys

from .queue import DeliveryQueue, InMemoryQueue
from .dispatcher import EventDispatcher, CircuitBreakerOpenError
from .manager import WebhookManager
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


class WebhookWorker:
    """
    Background worker for webhook deliveries.

    Processes queued deliveries with:
        - Concurrent processing
        - Automatic retries
        - Circuit breaker handling
        - Graceful shutdown
        - Health checks
    """

    def __init__(
        self,
        storage: StorageBackend,
        queue: Optional[DeliveryQueue] = None,
        num_workers: int = 10,
        poll_interval: int = 5
    ):
        """
        Initialize webhook worker.

        Args:
            storage: Storage backend
            queue: Delivery queue (creates in-memory if not provided)
            num_workers: Number of concurrent workers
            poll_interval: Seconds between queue polls
        """
        self.storage = storage
        self.queue = queue or InMemoryQueue()
        self.num_workers = num_workers
        self.poll_interval = poll_interval

        self.dispatcher = EventDispatcher(storage)
        self.running = False
        self.workers: list[asyncio.Task] = []
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "circuit_breaker_errors": 0,
            "started_at": None
        }

    async def start(self):
        """
        Start the worker pool.

        Spawns worker tasks and begins processing queue.

        Example:
            worker = WebhookWorker(storage, queue, num_workers=10)
            await worker.start()
        """
        if self.running:
            logger.warning("Worker already running")
            return

        self.running = True
        self.stats["started_at"] = datetime.utcnow()

        logger.info(f"Starting {self.num_workers} webhook workers")

        # Connect to queue
        await self.queue.connect()

        # Spawn worker tasks
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)

        # Spawn retry scheduler
        retry_task = asyncio.create_task(self._retry_scheduler())
        self.workers.append(retry_task)

        logger.info(f"Webhook worker pool started with {self.num_workers} workers")

    async def stop(self):
        """
        Stop the worker pool gracefully.

        Waits for current deliveries to complete.

        Example:
            await worker.stop()
        """
        if not self.running:
            return

        logger.info("Stopping webhook worker pool...")
        self.running = False

        # Wait for workers to finish current deliveries
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Disconnect from queue
        await self.queue.disconnect()

        logger.info("Webhook worker pool stopped")

    async def _worker(self, worker_id: int):
        """
        Worker task that processes deliveries.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Dequeue next delivery
                delivery = await self.queue.dequeue(timeout=self.poll_interval)

                if not delivery:
                    continue

                # Get webhook configuration
                # Note: This is simplified - in production, fetch from database
                webhook_id = delivery.webhook_id

                logger.debug(f"Worker {worker_id} processing delivery {delivery.id}")

                # Attempt delivery
                try:
                    # In real implementation, fetch webhook from database
                    # For now, we'll use the dispatcher's retry logic
                    success = await self.dispatcher._attempt_delivery(None, delivery)

                    self.stats["processed"] += 1

                    if success:
                        self.stats["successful"] += 1
                        logger.info(f"Worker {worker_id} delivered {delivery.id} successfully")
                    else:
                        self.stats["failed"] += 1

                        # Re-queue if retries remaining
                        if delivery.next_retry_at:
                            delay = delivery.next_retry_at - datetime.utcnow()
                            if delay.total_seconds() > 0:
                                await self.queue.enqueue(delivery, delay=delay)
                                logger.info(
                                    f"Worker {worker_id} re-queued {delivery.id} "
                                    f"(retry in {delay.total_seconds()}s)"
                                )
                        else:
                            # Max retries exceeded - dead letter queue
                            await self.queue.move_to_dlq(delivery)
                            logger.error(f"Worker {worker_id} moved {delivery.id} to DLQ")

                except CircuitBreakerOpenError:
                    self.stats["circuit_breaker_errors"] += 1
                    # Re-queue for later
                    await self.queue.enqueue(delivery, delay=timedelta(minutes=5))
                    logger.warning(
                        f"Worker {worker_id} circuit breaker open for {delivery.webhook_id}, "
                        f"re-queued {delivery.id}"
                    )

                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing {delivery.id}: {e}")
                    self.stats["failed"] += 1

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break

            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}")
                await asyncio.sleep(1)  # Back off on errors

        logger.info(f"Worker {worker_id} stopped")

    async def _retry_scheduler(self):
        """
        Background task that schedules retries for failed deliveries.

        Polls database for deliveries that need retry.
        """
        logger.info("Retry scheduler started")

        while self.running:
            try:
                # Find deliveries ready for retry
                with self.storage.cursor() as cursor:
                    now = datetime.utcnow().isoformat()
                    cursor.execute("""
                        SELECT id, webhook_id, event, payload, status, attempts,
                               next_retry_at, response_code, response_body, duration_ms,
                               created_at, completed_at, error_message
                        FROM webhook_deliveries
                        WHERE status = 'pending'
                          AND next_retry_at IS NOT NULL
                          AND next_retry_at <= ?
                        LIMIT 100
                    """, (now,))

                    rows = cursor.fetchall()

                # Re-queue for processing
                from .models import WebhookDelivery, WebhookEvent, DeliveryStatus
                from uuid import UUID

                for row in rows:
                    delivery = WebhookDelivery(
                        id=UUID(row[0]),
                        webhook_id=UUID(row[1]),
                        event=WebhookEvent(row[2]),
                        payload=eval(row[3]),
                        status=DeliveryStatus(row[4]),
                        attempts=row[5],
                        next_retry_at=datetime.fromisoformat(row[6]) if row[6] else None,
                        response_code=row[7],
                        response_body=row[8],
                        duration_ms=row[9],
                        created_at=datetime.fromisoformat(row[10]),
                        completed_at=datetime.fromisoformat(row[11]) if row[11] else None,
                        error_message=row[12]
                    )

                    await self.queue.enqueue(delivery, priority="normal")
                    logger.debug(f"Scheduled retry for delivery {delivery.id}")

                # Poll every 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                logger.info("Retry scheduler cancelled")
                break

            except Exception as e:
                logger.error(f"Retry scheduler error: {e}")
                await asyncio.sleep(5)

        logger.info("Retry scheduler stopped")

    def get_stats(self) -> dict:
        """
        Get worker statistics.

        Returns:
            Dictionary of stats

        Example:
            stats = worker.get_stats()
            print(f"Processed: {stats['processed']}")
        """
        uptime = None
        if self.stats["started_at"]:
            uptime = (datetime.utcnow() - self.stats["started_at"]).total_seconds()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "running": self.running,
            "num_workers": self.num_workers
        }

    async def health_check(self) -> dict:
        """
        Health check for monitoring.

        Returns:
            Health status dictionary

        Example:
            health = await worker.health_check()
            if health["status"] != "healthy":
                alert()
        """
        queue_depth = await self.queue.get_queue_depth()
        queue_metrics = await self.queue.get_metrics()

        # Determine health
        total_pending = queue_depth["high"] + queue_depth["normal"] + queue_depth["low"]
        is_healthy = (
            self.running and
            len(self.workers) == self.num_workers + 1 and  # +1 for retry scheduler
            total_pending < 10000  # Arbitrary threshold
        )

        return {
            "status": "healthy" if is_healthy else "degraded",
            "running": self.running,
            "workers": len(self.workers),
            "queue_depth": queue_depth,
            "queue_metrics": queue_metrics,
            "worker_stats": self.get_stats()
        }


async def run_worker(
    storage: StorageBackend,
    redis_url: Optional[str] = None,
    num_workers: int = 10
):
    """
    Run worker with signal handling.

    Args:
        storage: Storage backend
        redis_url: Redis URL (None = in-memory queue)
        num_workers: Number of workers

    Example:
        from continuum.storage.sqlite_backend import SQLiteBackend
        storage = SQLiteBackend(db_path="memory.db")
        await run_worker(storage, num_workers=10)
    """
    # Create queue
    if redis_url:
        queue = DeliveryQueue(redis_url)
    else:
        queue = InMemoryQueue()

    # Create worker
    worker = WebhookWorker(storage, queue, num_workers)

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(worker.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start worker
    await worker.start()

    # Keep running
    try:
        while worker.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, shutting down...")
        await worker.stop()


if __name__ == "__main__":
    """
    Run worker as standalone process.

    Usage:
        python -m continuum.webhooks.worker --workers 10 --redis redis://localhost
    """
    import argparse

    parser = argparse.ArgumentParser(description="CONTINUUM Webhook Worker")
    parser.add_argument("--workers", type=int, default=10, help="Number of workers")
    parser.add_argument("--redis", type=str, help="Redis URL (optional)")
    parser.add_argument("--db", type=str, default="memory.db", help="Database path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Create storage
    from ..storage.sqlite_backend import SQLiteBackend
    storage = SQLiteBackend(db_path=args.db)

    # Run worker
    logger.info(f"Starting webhook worker with {args.workers} workers")
    asyncio.run(run_worker(storage, args.redis, args.workers))

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
