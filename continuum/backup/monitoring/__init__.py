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
import urllib.parse
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

    Metric keys:
      backup_success_total     - completed/verified backup count
      backup_failure_total     - failed backup count
      backup_in_progress_total - in-progress backup count
      backup_duration_seconds  - list of backup durations (histogram samples)
      backup_size_bytes        - list of compressed sizes (histogram samples)
      total_storage_bytes      - sum of all compressed backup sizes

    Args:
        config: Optional backup configuration for querying the metadata store.

    Returns:
        Dictionary of metrics
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_in_progress_total": 0,
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "total_storage_bytes": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        store = MetadataStore(config.metadata_db_path)
        backups = store.list_backups()

        for b in backups:
            status = b.status.value
            if status in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif status == "failed":
                metrics["backup_failure_total"] += 1
            elif status == "in_progress":
                metrics["backup_in_progress_total"] += 1

            if b.completed_at and b.created_at:
                duration = (b.completed_at - b.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

            if b.compressed_size_bytes > 0:
                metrics["backup_size_bytes"].append(b.compressed_size_bytes)
                metrics["total_storage_bytes"] += b.compressed_size_bytes

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

    channels: List[str] = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            await _dispatch_alert(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Failed to send alert to {channel!r}: {e}")

async def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """Route an alert to the correct notification backend.

    Supported channel URI schemes:
      http:// / https://   - Generic JSON webhook; Slack detected by hostname
      smtp://user:pass@host:port/recipient - SMTP email
      pagerduty://routing_key             - PagerDuty Events API v2
    """
    if channel.startswith(("http://", "https://")):
        await asyncio.to_thread(_send_webhook, channel, alert_type, message)
    elif channel.startswith("smtp://"):
        await asyncio.to_thread(_send_smtp_email, channel, alert_type, message)
    elif channel.startswith("pagerduty://"):
        await asyncio.to_thread(_send_pagerduty, channel, alert_type, message)
    else:
        logger.warning(
            f"Unsupported notification channel scheme: {channel!r}. "
            "Supported: http://, https://, smtp://, pagerduty://"
        )


def _send_webhook(url: str, alert_type: str, message: str) -> None:
    """POST a JSON payload to an HTTP/HTTPS webhook. Slack format auto-detected."""
    if "hooks.slack.com" in url:
        payload: Dict[str, Any] = {"text": f"*[{alert_type.upper()}]* {message}"}
    else:
        payload = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug(f"Webhook {url} responded {resp.status}")


def _send_smtp_email(channel: str, alert_type: str, message: str) -> None:
    """Send an alert email via SMTP.

    Channel format: smtp://user:pass@host:port/recipient@example.com
    Port defaults to 587; STARTTLS is used when credentials are present.
    """
    parsed = urllib.parse.urlparse(channel)
    host = parsed.hostname or "localhost"
    port = parsed.port or 587
    username = urllib.parse.unquote(parsed.username or "")
    password = urllib.parse.unquote(parsed.password or "")
    recipient = parsed.path.lstrip("/")

    if not recipient:
        logger.error("SMTP channel missing recipient in path: %s", channel)
        return

    sender = username or f"backup-monitor@{host}"
    body = f"{message}\n\nTimestamp: {datetime.utcnow().isoformat()}"
    msg = MIMEText(body)
    msg["Subject"] = f"[Backup {alert_type.upper()}] Alert"
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP(host, port) as smtp:
        if username and password:
            smtp.starttls()
            smtp.login(username, password)
        smtp.sendmail(sender, [recipient], msg.as_string())

    logger.debug(f"Email alert sent to {recipient}")


def _send_pagerduty(channel: str, alert_type: str, message: str) -> None:
    """Send an alert to PagerDuty Events API v2.

    Channel format: pagerduty://routing_key
    """
    routing_key = channel.removeprefix("pagerduty://")
    if not routing_key:
        logger.error("PagerDuty channel missing routing key")
        return

    severity = "critical" if alert_type == "failure" else "info"
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        logger.debug(f"PagerDuty responded {resp.status}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
