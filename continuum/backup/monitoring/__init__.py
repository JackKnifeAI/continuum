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

import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

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
        config: Backup configuration (required to read from metadata store)

    Returns:
        Dictionary of metrics with keys:
        - backup_duration_seconds: list of durations for completed backups
        - backup_size_bytes: list of compressed sizes for completed backups
        - backup_success_total: count of successful backups
        - backup_failure_total: count of failed backups
        - last_backup_age_seconds: seconds since last successful backup
        - total_storage_used_bytes: total compressed bytes across all backups
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "last_backup_age_seconds": None,
        "total_storage_used_bytes": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        for b in all_backups:
            if b.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
                metrics["backup_size_bytes"].append(b.compressed_size_bytes)
                if b.completed_at and b.created_at:
                    metrics["backup_duration_seconds"].append(
                        (b.completed_at - b.created_at).total_seconds()
                    )
            elif b.status.value == "failed":
                metrics["backup_failure_total"] += 1

        metrics["total_storage_used_bytes"] = sum(
            b.compressed_size_bytes for b in all_backups
        )

        successful = [b for b in all_backups if b.status.value in ("completed", "verified")]
        if successful:
            latest = max(successful, key=lambda b: b.created_at)
            metrics["last_backup_age_seconds"] = (
                datetime.utcnow() - latest.created_at
            ).total_seconds()

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}", exc_info=True)

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
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            _dispatch_alert(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Failed to send alert to channel {channel!r}: {e}")

def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """
    Dispatch an alert to a single notification channel.

    Channel format determines the delivery method:
    - https://hooks.slack.com/...  → Slack incoming webhook
    - http(s)://...                → Generic JSON webhook (POST)

    Args:
        channel: Channel identifier or URL
        alert_type: "failure", "warning", or "success"
        message: Human-readable alert message
    """
    if channel.startswith("https://hooks.slack.com/") or channel.startswith("http://hooks.slack.com/"):
        _send_slack_webhook(channel, alert_type, message)
    elif channel.startswith("http://") or channel.startswith("https://"):
        _send_generic_webhook(channel, alert_type, message)
    else:
        logger.warning(f"Unknown notification channel format: {channel!r}")


def _send_slack_webhook(url: str, alert_type: str, message: str) -> None:
    """Send alert to a Slack incoming webhook URL."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":information_source:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"Slack alert sent, status={resp.status}")


def _send_generic_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a generic webhook URL."""
    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "continuum-backup",
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info(f"Webhook alert sent to {url!r}, status={resp.status}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
