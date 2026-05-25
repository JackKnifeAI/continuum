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
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..types import BackupConfig, BackupHealth

_PAGERDUTY_EVENTS_API = "https://events.pagerduty.com/v2/enqueue"

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
        config: Optional backup configuration; when provided, metrics are
                populated from the metadata store.

    Returns:
        Dictionary of metrics with Prometheus-compatible names.
        Histogram metrics are lists of observed values; counters are ints.
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],     # histogram
        "backup_size_bytes": [],            # histogram
        "backup_success_total": 0,          # counter
        "backup_failure_total": 0,          # counter
        "restore_duration_seconds": [],     # histogram
        "retention_deletions_total": 0,     # counter
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
                if backup.completed_at and backup.created_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    metrics["backup_duration_seconds"].append(duration)
                metrics["backup_size_bytes"].append(backup.compressed_size_bytes)
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

        logger.debug(
            "Collected metrics: %d successful, %d failed backups",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
        )
    except Exception as e:
        logger.error("Failed to collect backup metrics: %s", e)

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

    if not config.notification_channels:
        logger.debug("No notification channels configured")
        return

    results: List[Any] = await asyncio.gather(
        *[_dispatch_alert(ch, alert_type, message) for ch in config.notification_channels],
        return_exceptions=True,
    )

    for channel, result in zip(config.notification_channels, results):
        if isinstance(result, Exception):
            logger.error("Alert dispatch failed for %s: %s", channel, result)

async def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """Route an alert to the appropriate channel implementation.

    Supported channel formats:
      - ``https://hooks.slack.com/...`` or ``slack:<webhook_url>`` → Slack
      - ``pagerduty:<integration_key>``                            → PagerDuty Events API v2
      - ``mailto:<recipient>`` or ``smtp://user:pass@host:port/<to>`` → SMTP email
      - Any other ``http://`` / ``https://`` URL                   → generic webhook
    """
    if "hooks.slack.com" in channel or channel.startswith("slack:"):
        await _send_slack_alert(channel, alert_type, message)
    elif channel.startswith("pagerduty:"):
        await _send_pagerduty_alert(channel, alert_type, message)
    elif channel.startswith("mailto:") or channel.startswith("smtp:"):
        await _send_email_alert(channel, alert_type, message)
    elif channel.startswith("http://") or channel.startswith("https://"):
        await _send_webhook_alert(channel, alert_type, message)
    else:
        logger.warning("Unknown notification channel format: %s", channel)


async def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """POST a JSON payload to *url* using a thread-pool executor."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, urllib.request.urlopen, request)


async def _send_slack_alert(channel: str, alert_type: str, message: str) -> None:
    """Send an alert to Slack via an incoming webhook URL."""
    url = channel[len("slack:"):] if channel.startswith("slack:") else channel
    emoji = {
        "failure": ":rotating_light:",
        "warning": ":warning:",
        "success": ":white_check_mark:",
    }.get(alert_type, ":bell:")
    payload = {"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}
    await _post_json(url, payload)
    logger.info("Slack alert sent")


async def _send_pagerduty_alert(channel: str, alert_type: str, message: str) -> None:
    """Send an alert to PagerDuty via Events API v2."""
    integration_key = channel[len("pagerduty:"):]
    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    payload = {
        "routing_key": integration_key,
        "event_action": "trigger" if alert_type == "failure" else "resolve",
        "payload": {
            "summary": f"Backup {alert_type}: {message}",
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
    await _post_json(_PAGERDUTY_EVENTS_API, payload)
    logger.info("PagerDuty alert sent")


async def _send_email_alert(channel: str, alert_type: str, message: str) -> None:
    """Send an alert via SMTP.

    Channel formats:
      - ``mailto:<recipient>``                            uses localhost:25 relay
      - ``smtp://user:pass@host:port/<recipient>``        authenticated SMTP
    """
    if channel.startswith("mailto:"):
        recipient = channel[len("mailto:"):]
        smtp_host, smtp_port = "localhost", 25
        smtp_user: Optional[str] = None
        smtp_pass: Optional[str] = None
    else:
        parsed = urlparse(channel)
        recipient = (parsed.path or "").lstrip("/")
        smtp_host = parsed.hostname or "localhost"
        smtp_port = parsed.port or 587
        smtp_user = parsed.username
        smtp_pass = parsed.password

    sender = smtp_user or "continuum@localhost"
    subject = f"[Continuum Backup] {alert_type.upper()}"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    def _send() -> None:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _send)
    logger.info("Email alert sent to %s", recipient)


async def _send_webhook_alert(channel: str, alert_type: str, message: str) -> None:
    """POST an alert payload to a generic HTTP webhook URL."""
    payload = {
        "alert_type": alert_type,
        "message": message,
        "source": "continuum-backup",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    await _post_json(channel, payload)
    logger.info("Webhook alert sent to %s", channel)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
