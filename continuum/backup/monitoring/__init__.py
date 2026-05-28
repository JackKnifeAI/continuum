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
import logging
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
        config: Optional backup configuration to query live metrics

    Returns:
        Dictionary of metrics with counters and histogram values
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "restore_duration_seconds": [],
        "retention_deletions_total": 0,
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
                if backup.compressed_size_bytes:
                    metrics["backup_size_bytes"].append(backup.compressed_size_bytes)
                if backup.completed_at and backup.created_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    metrics["backup_duration_seconds"].append(duration)
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

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

    if not config.notification_channels:
        logger.debug("No notification channels configured")
        return

    for channel in config.notification_channels:
        try:
            await _dispatch_alert(channel, alert_type, message)
        except Exception as e:
            logger.error(f"Alert delivery failed for channel {channel!r}: {e}")


async def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """Route alert to the appropriate channel handler based on channel URL/prefix."""
    if channel.startswith("https://hooks.slack.com/"):
        await asyncio.to_thread(_send_slack_alert, channel, alert_type, message)
    elif channel.startswith("pagerduty:"):
        routing_key = channel[len("pagerduty:"):]
        await asyncio.to_thread(_send_pagerduty_alert, routing_key, alert_type, message)
    elif channel.startswith("smtp://"):
        await asyncio.to_thread(_send_email_alert, channel, alert_type, message)
    elif channel.startswith("https://") or channel.startswith("http://"):
        await asyncio.to_thread(_send_webhook_alert, channel, alert_type, message)
    else:
        logger.warning(f"Unknown notification channel format: {channel!r}")


def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """Send alert to Slack via incoming webhook."""
    import json
    import urllib.request

    color_map = {"failure": "#FF0000", "warning": "#FFA500", "success": "#36A64F"}
    payload = {
        "attachments": [{
            "color": color_map.get(alert_type, "#808080"),
            "title": f"Backup {alert_type.title()}",
            "text": message,
            "ts": int(datetime.utcnow().timestamp()),
        }]
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url, data=data, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=10)
    logger.info(f"Slack alert sent: {alert_type}")


def _send_pagerduty_alert(routing_key: str, alert_type: str, message: str) -> None:
    """Send alert to PagerDuty via Events API v2."""
    import json
    import urllib.request

    severity_map = {"failure": "critical", "warning": "warning", "success": "info"}
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger" if alert_type == "failure" else "acknowledge",
        "payload": {
            "summary": message,
            "severity": severity_map.get(alert_type, "info"),
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10)
    logger.info(f"PagerDuty alert sent: {alert_type}")


def _send_email_alert(smtp_url: str, alert_type: str, message: str) -> None:
    """
    Send alert via SMTP.

    Channel URL format: smtp://user:password@host:port?to=recipient@example.com
    """
    import smtplib
    import urllib.parse
    from email.mime.text import MIMEText

    parsed = urllib.parse.urlparse(smtp_url)
    params = urllib.parse.parse_qs(parsed.query)

    host = parsed.hostname or "localhost"
    port = parsed.port or 587
    username = urllib.parse.unquote(parsed.username or "")
    password = urllib.parse.unquote(parsed.password or "")
    to_addr = params.get("to", [""])[0]
    from_addr = params.get("from", [username or "backup@continuum"])[0]

    if not to_addr:
        logger.warning("SMTP alert skipped: no 'to' address in channel URL")
        return

    msg = MIMEText(message)
    msg["Subject"] = f"[Continuum Backup] {alert_type.title()} Alert"
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)

    logger.info(f"Email alert sent to {to_addr}: {alert_type}")


def _send_webhook_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """Send alert to a generic HTTP webhook as JSON POST."""
    import json
    import urllib.request

    payload = {
        "alert_type": alert_type,
        "message": message,
        "source": "continuum-backup",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url, data=data, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=10)
    logger.info(f"Webhook alert sent to {webhook_url}: {alert_type}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
