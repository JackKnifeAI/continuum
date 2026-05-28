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


# Module-level in-memory metrics registry, updated by backup/restore/retention operations.
_metrics: Dict[str, Any] = {
    "backup_duration_seconds": [],
    "backup_size_bytes": [],
    "backup_success_total": 0,
    "backup_failure_total": 0,
    "restore_duration_seconds": [],
    "retention_deletions_total": 0,
    "last_updated": None,
}


def record_backup_metric(duration_seconds: float, size_bytes: int, success: bool) -> None:
    """Record a completed backup operation into the metrics registry."""
    _metrics["backup_duration_seconds"].append(duration_seconds)
    _metrics["backup_size_bytes"].append(size_bytes)
    if success:
        _metrics["backup_success_total"] += 1
    else:
        _metrics["backup_failure_total"] += 1
    _metrics["last_updated"] = datetime.utcnow().isoformat()


def record_restore_metric(duration_seconds: float) -> None:
    """Record a completed restore operation into the metrics registry."""
    _metrics["restore_duration_seconds"].append(duration_seconds)
    _metrics["last_updated"] = datetime.utcnow().isoformat()


def record_retention_deletion(count: int = 1) -> None:
    """Record backups deleted by the retention policy."""
    _metrics["retention_deletions_total"] += count
    _metrics["last_updated"] = datetime.utcnow().isoformat()


def _histogram_summary(samples: List[float]) -> Dict[str, float]:
    return {
        "count": len(samples),
        "sum": sum(samples),
        "avg": sum(samples) / len(samples) if samples else 0.0,
        "min": min(samples) if samples else 0.0,
        "max": max(samples) if samples else 0.0,
    }


def get_backup_metrics() -> Dict[str, Any]:
    """
    Get backup system metrics for monitoring.

    Returns metrics suitable for Prometheus, CloudWatch, etc.
    Call record_backup_metric / record_restore_metric / record_retention_deletion
    from backup operations to populate live data.

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

    payload: Dict[str, Any] = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": config.tenant_id,
    }

    for channel in config.notification_channels:
        try:
            await _dispatch_channel(channel, payload)
        except Exception as e:
            logger.error(f"Failed to send alert to channel {channel!r}: {e}")


def _post_webhook(url: str, body: Dict[str, Any]) -> None:
    """POST a JSON payload to a webhook URL (blocking — run via asyncio.to_thread)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            logger.info(f"Webhook notification sent to {url!r} (HTTP {resp.status})")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Webhook returned HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Webhook connection failed: {e.reason}") from e


async def _dispatch_channel(channel: str, payload: Dict[str, Any]) -> None:
    """Dispatch an alert payload to a single notification channel."""
    if channel.startswith("http://") or channel.startswith("https://"):
        # Slack incoming webhooks use a {"text": "..."} body; generic webhooks get the full payload.
        if "hooks.slack.com" in channel:
            body: Dict[str, Any] = {
                "text": f"*{payload['alert_type'].upper()}*: {payload['message']}",
                "attachments": [{"text": f"Tenant: {payload['tenant_id']}", "ts": payload["timestamp"]}],
            }
        else:
            body = payload
        await asyncio.to_thread(_post_webhook, channel, body)
    elif channel == "slack":
        logger.warning(
            "Slack channel configured by name; add the Slack webhook URL to notification_channels instead"
        )
    elif channel == "email":
        logger.warning(
            "Email notifications require SMTP configuration (not yet in BackupConfig); "
            "configure an SMTP relay and extend BackupConfig with smtp_* fields"
        )
    elif channel == "pagerduty":
        logger.warning(
            "PagerDuty notifications require an Events API v2 routing key; "
            "extend BackupConfig with a pagerduty_routing_key field to enable"
        )
    elif channel in ("sms", "twilio"):
        logger.warning(
            "SMS notifications require Twilio credentials; "
            "extend BackupConfig with twilio_* fields to enable"
        )
    else:
        logger.warning(f"Unknown notification channel: {channel!r}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
