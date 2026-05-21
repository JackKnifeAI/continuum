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
Backup Monitoring and Alerting

Health checks, metrics, and alerting for backup system.
"""

import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)


async def get_backup_health(config: BackupConfig) -> BackupHealth:
    """
    Get overall backup system health.

    Checks:
    - Last backup time (SLA compliance)
    - Recent backup failures
    - Storage usage
    - RTO/RPO compliance

    Args:
        config: Backup configuration

    Returns:
        BackupHealth status
    """
    logger.info("Checking backup system health")

    health = BackupHealth(healthy=True)

    try:
        # Get metadata store
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)

        # Get all backups
        all_backups = metadata_store.list_backups()
        health.total_backups = len(all_backups)

        if not all_backups:
            health.healthy = False
            health.errors.append("No backups found")
            return health

        # Find last successful backup
        successful_backups = [
            b for b in all_backups
            if b.status.value in ['completed', 'verified']
        ]

        if successful_backups:
            latest_backup = max(successful_backups, key=lambda b: b.created_at)
            health.last_backup_time = latest_backup.created_at
            health.last_successful_backup = latest_backup.backup_id
        else:
            health.healthy = False
            health.errors.append("No successful backups found")

        # Check RPO compliance
        if health.last_backup_time:
            age_minutes = (datetime.utcnow() - health.last_backup_time).total_seconds() / 60

            if age_minutes > config.target_rpo_minutes:
                health.rpo_compliant = False
                health.warnings.append(
                    f"RPO SLA breach: Last backup {age_minutes:.1f} minutes ago "
                    f"(target: {config.target_rpo_minutes} minutes)"
                )
                health.healthy = False

        # Count failed backups in last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        health.failed_backups_24h = len([
            b for b in all_backups
            if b.created_at > cutoff_time and b.status.value == 'failed'
        ])

        if health.failed_backups_24h > 3:
            health.warnings.append(
                f"High failure rate: {health.failed_backups_24h} failed backups in last 24h"
            )

        # Calculate average backup duration
        completed_backups = [
            b for b in all_backups
            if b.completed_at and b.created_at
        ]

        if completed_backups:
            total_duration = sum(
                (b.completed_at - b.created_at).total_seconds()
                for b in completed_backups[-10:]  # Last 10 backups
            )
            health.average_backup_duration_seconds = total_duration / min(10, len(completed_backups))

        # Calculate total storage used
        health.total_storage_used_bytes = sum(
            b.compressed_size_bytes for b in all_backups
        )

        # Check RTO (can we restore within target?)
        # RTO check would require actual restore test
        # For now, estimate based on average restore time
        estimated_restore_minutes = health.average_backup_duration_seconds / 60

        if estimated_restore_minutes > config.target_rto_minutes:
            health.rto_compliant = False
            health.warnings.append(
                f"RTO may not be achievable: Estimated {estimated_restore_minutes:.1f} minutes "
                f"(target: {config.target_rto_minutes} minutes)"
            )

        logger.info(
            f"Backup health: {'healthy' if health.healthy else 'unhealthy'}, "
            f"{health.total_backups} backups, "
            f"{health.total_storage_used_bytes / (1024**3):.2f} GB used"
        )

        return health

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        health.healthy = False
        health.errors.append(str(e))
        return health


def get_backup_metrics(config: Optional[BackupConfig] = None) -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Args:
        config: Optional backup configuration to read live metadata.

    Returns:
        Dictionary of metrics with counters and histograms.
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds": {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None},
        "backup_size_bytes": {"count": 0, "sum": 0, "min": None, "max": None, "avg": None},
        "restore_duration_seconds": {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None},
        "retention_deletions_total": 0,
        "collected_at": datetime.utcnow().isoformat(),
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        store = MetadataStore(config.metadata_db_path)
        all_backups = store.list_backups()

        durations: List[float] = []
        sizes: List[int] = []

        for b in all_backups:
            if b.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif b.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if b.completed_at and b.created_at:
                durations.append((b.completed_at - b.created_at).total_seconds())

            if b.compressed_size_bytes:
                sizes.append(b.compressed_size_bytes)

        def _histogram(values: list) -> Dict[str, Any]:
            if not values:
                return {"count": 0, "sum": 0, "min": None, "max": None, "avg": None}
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        metrics["backup_duration_seconds"] = _histogram(durations)
        metrics["backup_size_bytes"] = _histogram(sizes)

    except Exception as e:
        logger.warning(f"Failed to collect backup metrics: {e}")

    return metrics


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """Blocking HTTP POST used inside a thread executor."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "continuum-backup/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.getcode()
        if status not in (200, 201, 202, 204):
            raise RuntimeError(f"HTTP {status} from {url}")


async def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """
    Dispatch an alert to a single notification channel.

    Channel string formats:
    - ``slack:<webhook_url>``       — Slack Incoming Webhook
    - ``pagerduty:<routing_key>``   — PagerDuty Events API v2
    - ``webhook:<url>``             — Generic JSON webhook
    - ``<url>`` (starts with http)  — Treated as a generic webhook
    - ``log``                       — Write to logger only (useful for testing)
    """
    loop = asyncio.get_event_loop()

    if channel == "log":
        logger.info(f"[alert/{alert_type}] {message}")
        return

    if channel.startswith("slack:"):
        url = channel[len("slack:"):]
        payload: Dict[str, Any] = {
            "text": f"*[{alert_type.upper()}]* {message}",
            "username": "Continuum Backup",
        }
        await loop.run_in_executor(None, _post_json, url, payload)
        logger.debug(f"Slack alert sent to {url[:40]}...")
        return

    if channel.startswith("pagerduty:"):
        routing_key = channel[len("pagerduty:"):]
        severity = "critical" if alert_type == "failure" else "warning"
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        await loop.run_in_executor(
            None, _post_json, "https://events.pagerduty.com/v2/enqueue", payload
        )
        logger.debug("PagerDuty alert sent")
        return

    if channel.startswith("webhook:") or channel.startswith("http"):
        url = channel[len("webhook:"):] if channel.startswith("webhook:") else channel
        payload = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "continuum-backup",
        }
        await loop.run_in_executor(None, _post_json, url, payload)
        logger.debug(f"Webhook alert sent to {url[:40]}...")
        return

    logger.warning(f"Unknown notification channel format: '{channel}'")


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured channels.

    Args:
        alert_type: Type of alert (failure, warning, success)
        message: Alert message
        config: Backup configuration with notification channels
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    # Skip if notifications disabled
    if alert_type == 'success' and not config.notify_on_success:
        return

    if alert_type == 'failure' and not config.notify_on_failure:
        return

    channels = config.notification_channels
    if not channels:
        logger.warning(f"No notification channels configured. Alert dropped: [{alert_type}] {message}")
        return

    results = await asyncio.gather(
        *[_dispatch_channel(ch, alert_type, message) for ch in channels],
        return_exceptions=True,
    )
    for ch, result in zip(channels, results):
        if isinstance(result, Exception):
            logger.error(f"Alert dispatch failed for channel '{ch}': {result}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
