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
        config: Optional backup configuration for metadata access

    Returns:
        Dictionary of metrics with counters and histogram summaries
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds_count": 0,
        "backup_duration_seconds_sum": 0.0,
        "backup_duration_seconds_avg": 0.0,
        "backup_size_bytes_count": 0,
        "backup_size_bytes_sum": 0,
        "backup_size_bytes_avg": 0.0,
        "restore_duration_seconds_count": 0,
        "restore_duration_seconds_sum": 0.0,
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        durations: List[float] = []
        sizes: List[int] = []

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.completed_at and backup.created_at:
                durations.append((backup.completed_at - backup.created_at).total_seconds())

            if backup.compressed_size_bytes > 0:
                sizes.append(backup.compressed_size_bytes)

        if durations:
            metrics["backup_duration_seconds_count"] = len(durations)
            metrics["backup_duration_seconds_sum"] = sum(durations)
            metrics["backup_duration_seconds_avg"] = sum(durations) / len(durations)

        if sizes:
            metrics["backup_size_bytes_count"] = len(sizes)
            metrics["backup_size_bytes_sum"] = sum(sizes)
            metrics["backup_size_bytes_avg"] = sum(sizes) / len(sizes)

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}", exc_info=True)

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
        logger.warning(f"No notification channels configured. Alert dropped: [{alert_type}] {message}")
        return

    for channel in channels:
        try:
            await _dispatch_alert(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Failed to send alert to '{channel}': {e}")

async def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """Route an alert to a single notification channel (format: 'type:config')."""
    if ":" not in channel:
        logger.warning(f"Unrecognized channel format (expected 'type:config'): {channel}")
        return

    channel_type, channel_value = channel.split(":", 1)
    channel_type = channel_type.lower().strip()
    timestamp = datetime.utcnow().isoformat() + "Z"

    if channel_type == "slack":
        payload = json.dumps({"text": f"[{alert_type.upper()}] {message}"}).encode()
        await _post_json(channel_value, payload)

    elif channel_type == "webhook":
        payload = json.dumps({
            "alert_type": alert_type,
            "message": message,
            "timestamp": timestamp,
            "source": "continuum-backup",
        }).encode()
        await _post_json(channel_value, payload)

    elif channel_type == "pagerduty":
        severity = "critical" if alert_type == "failure" else "info"
        payload = json.dumps({
            "routing_key": channel_value,
            "event_action": "trigger",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
                "timestamp": timestamp,
            },
        }).encode()
        await _post_json("https://events.pagerduty.com/v2/enqueue", payload)

    elif channel_type == "email":
        logger.warning(
            f"Email alerting requires SMTP configuration; alert not sent to {channel_value}: {message}"
        )

    else:
        logger.warning(f"Unknown channel type '{channel_type}': {message}")


async def _post_json(url: str, payload: bytes) -> None:
    """POST a JSON payload to a URL via a thread pool executor."""
    def _do_post() -> None:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.debug(f"Alert POST to {url} returned HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} from {url}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach {url}: {e.reason}") from e

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _do_post)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
