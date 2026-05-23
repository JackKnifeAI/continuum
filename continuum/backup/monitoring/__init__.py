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
import urllib.error
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
        config: Backup configuration (required to access metadata store)

    Returns:
        Dictionary of metrics with counters and histogram data
    """
    if config is None:
        return {}

    try:
        from ..metadata import MetadataStore

        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        # Counters
        success_total = sum(
            1 for b in all_backups if b.status.value in ("completed", "verified")
        )
        failure_total = sum(1 for b in all_backups if b.status.value == "failed")

        # Histograms: backup duration in seconds
        backup_duration_seconds: List[float] = [
            (b.completed_at - b.created_at).total_seconds()
            for b in all_backups
            if b.completed_at and b.created_at
        ]

        # Histograms: backup size in bytes (compressed)
        backup_size_bytes: List[int] = [
            b.compressed_size_bytes
            for b in all_backups
            if b.compressed_size_bytes
        ]

        metrics: Dict[str, Any] = {
            "backup_success_total": success_total,
            "backup_failure_total": failure_total,
            "backup_total": len(all_backups),
            "backup_duration_seconds": backup_duration_seconds,
            "backup_size_bytes": backup_size_bytes,
            # restore_duration_seconds and retention_deletions_total require
            # separate event tracking not yet stored in BackupMetadata
            "restore_duration_seconds": [],
            "retention_deletions_total": 0,
        }

        logger.debug(
            "Collected metrics: %d total, %d success, %d failure",
            len(all_backups),
            success_total,
            failure_total,
        )
        return metrics

    except Exception as e:
        logger.error("Metrics collection failed: %s", e)
        return {}


async def _dispatch_channel(alert_type: str, message: str, channel: str) -> None:
    """
    Dispatch an alert to a single notification channel.

    Channel formats supported:
    - ``https://...`` / ``http://...`` — generic JSON webhook (POST)
    - ``slack:https://hooks.slack.com/...`` — Slack incoming webhook
    - ``pagerduty:<routing_key>`` — PagerDuty Events API v2
    """
    if channel.startswith("slack:"):
        url = channel[len("slack:"):]
        payload = {
            "text": f"*[{alert_type.upper()}]* {message}",
        }
        await _post_json(url, payload)

    elif channel.startswith("pagerduty:"):
        routing_key = channel[len("pagerduty:"):]
        event_action = "trigger" if alert_type == "failure" else "resolve"
        payload = {
            "routing_key": routing_key,
            "event_action": event_action,
            "payload": {
                "summary": message,
                "severity": "critical" if alert_type == "failure" else "info",
                "source": "continuum-backup",
            },
        }
        await _post_json("https://events.pagerduty.com/v2/enqueue", payload)

    elif channel.startswith("http://") or channel.startswith("https://"):
        payload = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await _post_json(channel, payload)

    else:
        logger.warning("Unrecognised notification channel format: %r", channel)


async def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """POST a JSON payload to a URL using the standard library."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _send() -> None:
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                logger.debug("Webhook %s responded %s", url, resp.status)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Webhook {url} returned HTTP {exc.code}") from exc

    await asyncio.to_thread(_send)


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

    if not config.notification_channels:
        logger.debug("No notification channels configured")
        return

    results = await asyncio.gather(
        *[
            _dispatch_channel(alert_type, message, channel)
            for channel in config.notification_channels
        ],
        return_exceptions=True,
    )

    for channel, result in zip(config.notification_channels, results):
        if isinstance(result, Exception):
            logger.error("Alert dispatch failed for channel %r: %s", channel, result)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
