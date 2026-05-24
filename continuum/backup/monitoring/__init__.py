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
from typing import Any, Dict, List

from ..types import BackupConfig, BackupHealth

logger = logging.getLogger(__name__)

# Module-level metrics registry — accumulated across the process lifetime.
_metrics: Dict[str, Any] = {
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "restore_duration_seconds": [],
    "retention_deletions_total": 0,
    "metrics_since": datetime.utcnow().isoformat(),
}


def _histogram_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
    return {
        "count": len(values),
        "sum": sum(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
    }


def record_backup_completed(duration_seconds: float, size_bytes: int) -> None:
    """Record metrics for a completed backup."""
    _metrics["backup_duration_seconds"].append(duration_seconds)
    _metrics["backup_size_bytes"].append(size_bytes)
    _metrics["backup_success_total"] += 1


def record_backup_failed() -> None:
    """Record a failed backup."""
    _metrics["backup_failure_total"] += 1


def record_restore_completed(duration_seconds: float) -> None:
    """Record metrics for a completed restore."""
    _metrics["restore_duration_seconds"].append(duration_seconds)


def record_retention_deletion(count: int = 1) -> None:
    """Record how many backups were deleted by the retention policy."""
    _metrics["retention_deletions_total"] += count


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
        "backup_duration_seconds": _histogram_stats(_metrics["backup_duration_seconds"]),
        "backup_size_bytes": _histogram_stats(_metrics["backup_size_bytes"]),
        "backup_success_total": _metrics["backup_success_total"],
        "backup_failure_total": _metrics["backup_failure_total"],
        "restore_duration_seconds": _histogram_stats(_metrics["restore_duration_seconds"]),
        "retention_deletions_total": _metrics["retention_deletions_total"],
        "metrics_since": _metrics["metrics_since"],
    }


async def _post_json(url: str, payload: Dict[str, Any]) -> bool:
    """POST a JSON payload to a URL; returns True on success."""
    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        await asyncio.to_thread(urllib.request.urlopen, req, timeout=10)
        return True
    except urllib.error.URLError as exc:
        logger.warning(f"Webhook delivery failed ({url}): {exc}")
        return False


async def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """Send a formatted alert to a Slack incoming webhook."""
    color = {"failure": "danger", "warning": "warning", "success": "good"}.get(
        alert_type, "#cccccc"
    )
    payload: Dict[str, Any] = {
        "attachments": [
            {
                "color": color,
                "title": f"Backup {alert_type.upper()}",
                "text": message,
                "footer": "Continuum Backup Monitor",
                "ts": int(datetime.utcnow().timestamp()),
            }
        ]
    }
    if await _post_json(webhook_url, payload):
        logger.info(f"Slack {alert_type} alert delivered")


async def _send_pagerduty_alert(routing_key: str, alert_type: str, message: str) -> None:
    """Send an alert to PagerDuty via the Events API v2.

    Channel format: ``pd:<routing_key>``
    """
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger" if alert_type == "failure" else "resolve",
        "payload": {
            "summary": message,
            "severity": "critical" if alert_type == "failure" else "warning",
            "source": "continuum-backup",
            "custom_details": {"alert_type": alert_type},
        },
    }
    if await _post_json("https://events.pagerduty.com/v2/enqueue", payload):
        logger.info(f"PagerDuty {alert_type} alert delivered")


async def _send_custom_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a generic JSON alert payload to an arbitrary webhook URL."""
    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }
    if await _post_json(url, payload):
        logger.info(f"Custom webhook {alert_type} alert delivered to {url}")


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

    tasks = []
    for channel in config.notification_channels:
        if "hooks.slack.com" in channel:
            tasks.append(_send_slack_alert(channel, alert_type, message))
        elif channel.startswith("pd:"):
            tasks.append(_send_pagerduty_alert(channel[3:], alert_type, message))
        elif channel.startswith(("http://", "https://")):
            tasks.append(_send_custom_webhook(channel, alert_type, message))
        else:
            logger.warning(f"Unsupported notification channel (skipped): {channel!r}")

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        logger.debug("No notification channels configured; alert logged only")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
