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
import os
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
        config: Backup configuration used to locate the metadata store.
                When omitted, counters default to zero.

    Returns:
        Dictionary of metrics with counter and histogram values.
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "restore_duration_seconds": [],
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        store = MetadataStore(config.metadata_db_path)
        all_backups = store.list_backups()

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

            if backup.compressed_size_bytes:
                metrics["backup_size_bytes"].append(backup.compressed_size_bytes)

        durations: List[float] = metrics["backup_duration_seconds"]
        if durations:
            metrics["backup_duration_seconds_avg"] = sum(durations) / len(durations)
            metrics["backup_duration_seconds_max"] = max(durations)
            metrics["backup_duration_seconds_min"] = min(durations)

        sizes: List[int] = metrics["backup_size_bytes"]
        if sizes:
            metrics["backup_size_bytes_total"] = sum(sizes)
            metrics["backup_size_bytes_avg"] = sum(sizes) / len(sizes)

        logger.debug(
            "Collected backup metrics: %d successful, %d failed",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
        )

    except Exception as e:
        logger.error("Failed to collect backup metrics: %s", e, exc_info=True)

    return metrics


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
        logger.warning("No notification channels configured. Alert [%s]: %s", alert_type, message)
        return

    results = await asyncio.gather(
        *[_dispatch_channel(ch, alert_type, message) for ch in channels],
        return_exceptions=True,
    )
    for channel, result in zip(channels, results):
        if isinstance(result, Exception):
            logger.error("Alert dispatch failed for channel %s: %s", channel, result)

def _http_post(url: str, payload: bytes) -> None:
    """Synchronous HTTP POST used inside an executor."""
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug("HTTP POST %s → %s", url, resp.status)


async def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """
    Dispatch an alert to a single notification channel.

    Supported channels (configured via environment variables):
    - "slack"      – BACKUP_SLACK_WEBHOOK_URL
    - "pagerduty"  – BACKUP_PAGERDUTY_KEY
    - "webhook"    – BACKUP_WEBHOOK_URL  (generic JSON POST)
    """
    loop = asyncio.get_event_loop()

    if channel == "slack":
        url = os.environ.get("BACKUP_SLACK_WEBHOOK_URL")
        if not url:
            logger.warning("BACKUP_SLACK_WEBHOOK_URL not set; skipping Slack alert")
            return
        payload = json.dumps({"text": f"*[{alert_type.upper()}]* {message}"}).encode()
        await loop.run_in_executor(None, _http_post, url, payload)

    elif channel == "pagerduty":
        key = os.environ.get("BACKUP_PAGERDUTY_KEY")
        if not key:
            logger.warning("BACKUP_PAGERDUTY_KEY not set; skipping PagerDuty alert")
            return
        event_action = "trigger" if alert_type == "failure" else "resolve"
        severity = "critical" if alert_type == "failure" else "info"
        payload = json.dumps({
            "routing_key": key,
            "event_action": event_action,
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
            },
        }).encode()
        await loop.run_in_executor(
            None, _http_post, "https://events.pagerduty.com/v2/enqueue", payload
        )

    elif channel == "webhook":
        url = os.environ.get("BACKUP_WEBHOOK_URL")
        if not url:
            logger.warning("BACKUP_WEBHOOK_URL not set; skipping webhook alert")
            return
        payload = json.dumps({"alert_type": alert_type, "message": message}).encode()
        await loop.run_in_executor(None, _http_post, url, payload)

    else:
        logger.warning("Unknown notification channel: %s", channel)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
