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
import smtplib
import urllib.request
from datetime import datetime, timedelta
from email.mime.text import MIMEText
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
        config: Optional backup configuration to query live metrics from the metadata store

    Returns:
        Dictionary of metrics with type, value/values, count, sum, avg, min, max fields
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": {
            "type": "histogram",
            "values": [],
            "description": "Backup operation duration in seconds",
        },
        "backup_size_bytes": {
            "type": "histogram",
            "values": [],
            "description": "Compressed backup size in bytes",
        },
        "backup_success_total": {
            "type": "counter",
            "value": 0,
            "description": "Total number of successful backups",
        },
        "backup_failure_total": {
            "type": "counter",
            "value": 0,
            "description": "Total number of failed backups",
        },
        "restore_duration_seconds": {
            "type": "histogram",
            "values": [],
            "description": "Restore operation duration in seconds",
        },
        "retention_deletions_total": {
            "type": "counter",
            "value": 0,
            "description": "Total backups deleted by retention policy",
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
            elif backup.status.value == "failed":
                metrics["backup_failure_total"]["value"] += 1

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds"]["values"].append(duration)

            if backup.compressed_size_bytes:
                metrics["backup_size_bytes"]["values"].append(backup.compressed_size_bytes)

        for key in ("backup_duration_seconds", "backup_size_bytes", "restore_duration_seconds"):
            values: List[float] = metrics[key]["values"]
            if values:
                metrics[key]["count"] = len(values)
                metrics[key]["sum"] = sum(values)
                metrics[key]["avg"] = sum(values) / len(values)
                metrics[key]["min"] = min(values)
                metrics[key]["max"] = max(values)

        logger.info(
            f"Metrics collected: {metrics['backup_success_total']['value']} successful, "
            f"{metrics['backup_failure_total']['value']} failed backups"
        )

    except Exception as e:
        logger.error(f"Failed to collect backup metrics: {e}")

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

    _channel_handlers = {
        "slack": _send_slack_alert,
        "webhook": _send_webhook_alert,
        "pagerduty": _send_pagerduty_alert,
    }

    for channel in channels:
        try:
            if channel == "email":
                await _send_email_alert(alert_type, message)
            elif channel in _channel_handlers:
                await _channel_handlers[channel](alert_type, message)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to send {alert_type} alert via {channel}: {e}")

async def _send_slack_alert(alert_type: str, message: str) -> None:
    webhook_url = os.environ.get("BACKUP_SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("BACKUP_SLACK_WEBHOOK_URL not set, skipping Slack alert")
        return

    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    await asyncio.to_thread(urllib.request.urlopen, req)
    logger.info("Slack alert sent")


async def _send_webhook_alert(alert_type: str, message: str) -> None:
    webhook_url = os.environ.get("BACKUP_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("BACKUP_WEBHOOK_URL not set, skipping webhook alert")
        return

    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    await asyncio.to_thread(urllib.request.urlopen, req)
    logger.info("Webhook alert sent")


async def _send_email_alert(alert_type: str, message: str) -> None:
    smtp_host = os.environ.get("BACKUP_SMTP_HOST")
    smtp_port = int(os.environ.get("BACKUP_SMTP_PORT", "587"))
    smtp_user = os.environ.get("BACKUP_SMTP_USER")
    smtp_password = os.environ.get("BACKUP_SMTP_PASSWORD")
    smtp_from = os.environ.get("BACKUP_SMTP_FROM") or smtp_user
    smtp_to = os.environ.get("BACKUP_SMTP_TO")

    if not all([smtp_host, smtp_user, smtp_password, smtp_to]):
        logger.warning(
            "SMTP not fully configured (need BACKUP_SMTP_HOST/USER/PASSWORD/TO), skipping email alert"
        )
        return

    msg = MIMEText(message)
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}: Backup Alert"
    msg["From"] = smtp_from
    msg["To"] = smtp_to

    def _send() -> None:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:  # type: ignore[arg-type]
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)  # type: ignore[arg-type]
            smtp.send_message(msg)

    await asyncio.to_thread(_send)
    logger.info("Email alert sent")


async def _send_pagerduty_alert(alert_type: str, message: str) -> None:
    routing_key = os.environ.get("BACKUP_PAGERDUTY_ROUTING_KEY")
    if not routing_key:
        logger.warning("BACKUP_PAGERDUTY_ROUTING_KEY not set, skipping PagerDuty alert")
        return

    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    event_action = "resolve" if alert_type == "success" else "trigger"

    payload = json.dumps({
        "routing_key": routing_key,
        "event_action": event_action,
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    await asyncio.to_thread(urllib.request.urlopen, req)
    logger.info("PagerDuty alert sent")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
