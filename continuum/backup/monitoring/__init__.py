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
import smtplib
import ssl
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
from urllib.parse import urlparse

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
        config: Optional backup configuration for querying metadata store

    Returns:
        Dictionary of metrics with counters and histogram value lists
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": {"type": "histogram", "values": [], "unit": "seconds"},
        "backup_size_bytes": {"type": "histogram", "values": [], "unit": "bytes"},
        "backup_success_total": {"type": "counter", "value": 0},
        "backup_failure_total": {"type": "counter", "value": 0},
        "restore_duration_seconds": {"type": "histogram", "values": [], "unit": "seconds"},
        "retention_deletions_total": {"type": "counter", "value": 0},
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

            if backup.compressed_size_bytes > 0:
                metrics["backup_size_bytes"]["values"].append(backup.compressed_size_bytes)

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

    if alert_type == "success" and not config.notify_on_success:
        return
    if alert_type == "failure" and not config.notify_on_failure:
        return

    channels = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            await _dispatch_channel(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Alert delivery failed for channel {channel!r}: {e}", exc_info=True)

async def _dispatch_channel(channel: str, alert_type: str, message: str) -> None:
    """Route alert to the appropriate channel handler based on URL scheme."""
    if "hooks.slack.com" in channel or channel.startswith("slack://"):
        await _send_slack_alert(channel, alert_type, message)
    elif channel.startswith(("smtp://", "email://")):
        await _send_email_alert(channel, alert_type, message)
    elif channel.startswith("pagerduty://"):
        await _send_pagerduty_alert(channel, alert_type, message)
    elif channel.startswith(("http://", "https://")):
        await _send_webhook_alert(channel, alert_type, message)
    else:
        logger.warning(f"Unrecognized notification channel scheme: {channel!r}")


async def _send_slack_alert(channel: str, alert_type: str, message: str) -> None:
    """Send alert via Slack incoming webhook.

    Channel format: https://hooks.slack.com/services/... or slack://hooks.slack.com/services/...
    """
    webhook_url = channel.removeprefix("slack://")
    if not webhook_url.startswith("http"):
        webhook_url = f"https://{webhook_url}"

    emoji = {"success": ":white_check_mark:", "warning": ":warning:", "failure": ":red_circle:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*\n{message}"}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=10))
    logger.info(f"Slack alert sent ({alert_type})")


async def _send_webhook_alert(channel: str, alert_type: str, message: str) -> None:
    """Send alert via generic HTTP webhook (POST JSON).

    Channel format: https://example.com/webhook
    """
    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "continuum-backup",
    }).encode()
    req = urllib.request.Request(
        channel,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=10))
    logger.info(f"Webhook alert sent to {channel} ({alert_type})")


async def _send_email_alert(channel: str, alert_type: str, message: str) -> None:
    """Send alert via SMTP email.

    Channel format: smtp://user:pass@host:587/recipient@example.com
    """
    parsed = urlparse(channel.replace("email://", "smtp://", 1))
    host = parsed.hostname or "localhost"
    port = parsed.port or 587
    username = parsed.username or ""
    password = parsed.password or ""
    recipient = parsed.path.lstrip("/")

    if not recipient:
        logger.error(f"No recipient address in email channel: {channel!r}")
        return

    sender = username or "continuum-backup@localhost"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(message, "plain"))

    def _send() -> None:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls(context=ctx)
            if username:
                server.login(username, password)
            server.sendmail(sender, [recipient], msg.as_string())

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send)
    logger.info(f"Email alert sent to {recipient} ({alert_type})")


async def _send_pagerduty_alert(channel: str, alert_type: str, message: str) -> None:
    """Send alert via PagerDuty Events API v2.

    Channel format: pagerduty://ROUTING_KEY
    """
    routing_key = channel.removeprefix("pagerduty://")
    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    event_action = "trigger" if alert_type == "failure" else "resolve"

    payload = json.dumps({
        "routing_key": routing_key,
        "event_action": event_action,
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=10))
    logger.info(f"PagerDuty alert sent ({alert_type})")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
