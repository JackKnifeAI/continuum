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
        config: Optional backup configuration to query live metric values.
                When omitted, returns the metric schema with zero/empty values.

    Returns:
        Dictionary of metrics with type, description, and current values.
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": {
            "type": "histogram",
            "description": "Duration of backup operations in seconds",
            "values": [],
        },
        "backup_size_bytes": {
            "type": "histogram",
            "description": "Compressed size of backup files in bytes",
            "values": [],
        },
        "backup_success_total": {
            "type": "counter",
            "description": "Total number of successful backups",
            "value": 0,
        },
        "backup_failure_total": {
            "type": "counter",
            "description": "Total number of failed backups",
            "value": 0,
        },
        "restore_duration_seconds": {
            "type": "histogram",
            "description": "Duration of restore operations in seconds",
            "values": [],
        },
        "retention_deletions_total": {
            "type": "counter",
            "description": "Total number of backups deleted by retention policy",
            "value": 0,
        },
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"]["value"] += 1
                if backup.compressed_size_bytes:
                    metrics["backup_size_bytes"]["values"].append(backup.compressed_size_bytes)
                if backup.completed_at and backup.created_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    metrics["backup_duration_seconds"]["values"].append(duration)
            elif backup.status.value == "failed":
                metrics["backup_failure_total"]["value"] += 1

        logger.debug(
            "Collected backup metrics: %d successful, %d failed",
            metrics["backup_success_total"]["value"],
            metrics["backup_failure_total"]["value"],
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

    channels: List[str] = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured; alert not delivered")
        return

    for channel in channels:
        try:
            if ":" in channel:
                channel_type, channel_target = channel.split(":", 1)
            else:
                channel_type, channel_target = channel, ""

            channel_type = channel_type.strip().lower()

            if channel_type == "slack":
                await _send_slack_alert(channel_target, alert_type, message)
            elif channel_type == "webhook":
                await _send_webhook_alert(channel_target, alert_type, message)
            elif channel_type in ("email", "smtp"):
                # Requires SMTP credentials not present in BackupConfig.
                # Configure an email gateway webhook or extend BackupConfig with SMTP settings.
                logger.warning("Email alerts require SMTP configuration (not yet supported): %s", channel_target)
            elif channel_type == "pagerduty":
                await _send_pagerduty_alert(channel_target, alert_type, message)
            elif channel_type in ("sms", "twilio"):
                logger.warning("SMS/Twilio alerts require Twilio credentials (not yet supported)")
            else:
                logger.warning("Unknown notification channel type: %s", channel_type)

        except Exception as e:
            logger.error("Failed to send alert via channel %r: %s", channel, e, exc_info=True)


async def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """POST an alert to a Slack incoming webhook URL."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()

    def _post() -> int:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status

    loop = asyncio.get_running_loop()
    status = await loop.run_in_executor(None, _post)
    logger.info("Slack alert delivered (HTTP %s): %s", status, alert_type)


async def _send_webhook_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a custom webhook URL."""
    payload = json.dumps(
        {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "system": "continuum-backup",
        }
    ).encode()

    def _post() -> int:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status

    loop = asyncio.get_running_loop()
    status = await loop.run_in_executor(None, _post)
    logger.info("Webhook alert delivered (HTTP %s): %s", status, alert_type)


async def _send_pagerduty_alert(routing_key: str, alert_type: str, message: str) -> None:
    """Send an event to PagerDuty via the Events API v2."""
    severity = {"failure": "critical", "warning": "warning", "success": "info"}.get(alert_type, "info")
    payload = json.dumps(
        {
            "routing_key": routing_key,
            "event_action": "trigger" if alert_type == "failure" else "resolve",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    ).encode()

    def _post() -> int:
        req = urllib.request.Request(
            "https://events.pagerduty.com/v2/enqueue",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status

    loop = asyncio.get_running_loop()
    status = await loop.run_in_executor(None, _post)
    logger.info("PagerDuty alert delivered (HTTP %s): %s", status, alert_type)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
