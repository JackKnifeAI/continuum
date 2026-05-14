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
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# In-process metrics store — counters and histogram data points accumulated at runtime.
_metrics: Dict[str, Any] = {
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "restore_duration_seconds": [],
    "retention_deletions_total": 0,
    "last_updated": None,
}

_HISTOGRAM_METRICS = {"backup_duration_seconds", "backup_size_bytes", "restore_duration_seconds"}
_COUNTER_METRICS = {"backup_success_total", "backup_failure_total", "retention_deletions_total"}


def record_backup_metric(metric: str, value: float) -> None:
    """Increment a counter or append to a histogram by name."""
    if metric in _HISTOGRAM_METRICS:
        _metrics[metric].append(value)
    elif metric in _COUNTER_METRICS:
        _metrics[metric] += value
    else:
        return
    _metrics["last_updated"] = datetime.utcnow().isoformat()


def _histogram_summary(data: List[float]) -> Dict[str, float]:
    if not data:
        return {"count": 0, "sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": len(data),
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
    }


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


def get_backup_metrics() -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Returns:
        Dictionary of metrics
    """
    return {
        "backup_duration_seconds": _histogram_summary(_metrics["backup_duration_seconds"]),
        "backup_size_bytes": _histogram_summary(_metrics["backup_size_bytes"]),
        "backup_success_total": _metrics["backup_success_total"],
        "backup_failure_total": _metrics["backup_failure_total"],
        "restore_duration_seconds": _histogram_summary(_metrics["restore_duration_seconds"]),
        "retention_deletions_total": _metrics["retention_deletions_total"],
        "last_updated": _metrics["last_updated"],
    }


def _post_slack_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a Slack-formatted message to a webhook URL."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug(f"Slack webhook response: {resp.status}")


def _post_generic_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a JSON payload to a generic webhook URL."""
    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug(f"Webhook response: {resp.status}")


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

    channels: List[str] = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            if channel.startswith("https://hooks.slack.com/"):
                _post_slack_webhook(channel, alert_type, message)
            elif channel.startswith("http://") or channel.startswith("https://"):
                _post_generic_webhook(channel, alert_type, message)
            else:
                logger.warning(f"Unsupported notification channel: {channel!r}")
        except Exception as e:
            logger.error(f"Failed to deliver alert to {channel!r}: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
