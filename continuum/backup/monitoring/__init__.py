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
import os
import smtplib
import urllib.error
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

    Returns metrics suitable for Prometheus, CloudWatch, etc.  When *config*
    is supplied the values are populated from the metadata store; otherwise
    the metric schema is returned with zero values so callers can register
    metric descriptors before any backup has run.

    Args:
        config: Optional backup configuration used to locate the metadata DB.

    Returns:
        Dictionary keyed by metric name.  Each value is a dict with:
          - ``type``: "counter" or "histogram"
          - ``help``: human-readable description
          - ``value``: scalar (counter) or list of observed samples (histogram)
          - ``sum`` / ``count``: histogram aggregates (histogram only)
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": {
            "type": "histogram",
            "help": "Duration of backup operations in seconds",
            "value": [],
            "sum": 0.0,
            "count": 0,
        },
        "backup_size_bytes": {
            "type": "histogram",
            "help": "Compressed size of completed backups in bytes",
            "value": [],
            "sum": 0,
            "count": 0,
        },
        "backup_success_total": {
            "type": "counter",
            "help": "Total number of successful backups",
            "value": 0,
        },
        "backup_failure_total": {
            "type": "counter",
            "help": "Total number of failed backups",
            "value": 0,
        },
        "restore_duration_seconds": {
            "type": "histogram",
            "help": "Duration of restore operations in seconds",
            "value": [],
            "sum": 0.0,
            "count": 0,
        },
        "retention_deletions_total": {
            "type": "counter",
            "help": "Total backups removed by retention policy",
            "value": 0,
        },
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        store = MetadataStore(config.metadata_db_path)
        all_backups = store.list_backups()

        for backup in all_backups:
            status = backup.status.value

            if status in ("completed", "verified"):
                metrics["backup_success_total"]["value"] += 1
            elif status == "failed":
                metrics["backup_failure_total"]["value"] += 1

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                hist = metrics["backup_duration_seconds"]
                hist["value"].append(duration)
                hist["sum"] += duration
                hist["count"] += 1

            if backup.compressed_size_bytes:
                hist = metrics["backup_size_bytes"]
                hist["value"].append(backup.compressed_size_bytes)
                hist["sum"] += backup.compressed_size_bytes
                hist["count"] += 1

        logger.debug(
            "Collected backup metrics: %d total backups",
            len(all_backups),
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
        logger.warning("Alert fired but no notification channels configured: %s", message)
        return

    for channel in channels:
        try:
            if channel == "slack" or channel.startswith("https://hooks.slack.com"):
                await _send_slack_alert(channel, alert_type, message)
            elif channel == "email":
                _send_email_alert(alert_type, message)
            elif channel == "pagerduty":
                await _send_pagerduty_alert(alert_type, message)
            elif channel.startswith("http"):
                await _send_webhook_alert(channel, alert_type, message)
            else:
                logger.warning("Unknown notification channel type: %s", channel)
        except Exception as e:
            logger.error("Failed to send alert via channel %s: %s", channel, e, exc_info=True)

async def _send_slack_alert(channel: str, alert_type: str, message: str) -> None:
    """Send alert to a Slack incoming-webhook URL.

    The URL is taken from *channel* if it starts with ``https://``, otherwise
    falls back to the ``SLACK_WEBHOOK_URL`` environment variable.
    """
    url = channel if channel.startswith("https://") else os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        logger.warning("Slack webhook URL not configured (set SLACK_WEBHOOK_URL)")
        return

    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(alert_type, ":bell:")
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info("Slack alert sent (HTTP %d)", resp.status)


def _send_email_alert(alert_type: str, message: str) -> None:
    """Send alert via SMTP.

    Reads connection details from environment variables:
      SMTP_HOST (default: localhost), SMTP_PORT (default: 587),
      SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_FROM, ALERT_EMAIL_TO
    """
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    email_from = os.environ.get("ALERT_EMAIL_FROM", smtp_user)
    email_to = os.environ.get("ALERT_EMAIL_TO", "")

    if not email_to:
        logger.warning("Email alert not sent: ALERT_EMAIL_TO not set")
        return

    msg = MIMEText(message)
    msg["Subject"] = f"[Backup {alert_type.upper()}] Continuum Backup Alert"
    msg["From"] = email_from
    msg["To"] = email_to

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        if smtp_port != 25:
            smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.sendmail(email_from, [email_to], msg.as_string())

    logger.info("Email alert sent to %s", email_to)


async def _send_pagerduty_alert(alert_type: str, message: str) -> None:
    """Send alert to PagerDuty Events API v2.

    Requires the ``PAGERDUTY_ROUTING_KEY`` environment variable (integration key).
    """
    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY", "")
    if not routing_key:
        logger.warning("PagerDuty routing key not configured (set PAGERDUTY_ROUTING_KEY)")
        return

    # Map alert_type to PagerDuty event action
    action = "trigger" if alert_type == "failure" else "acknowledge" if alert_type == "warning" else "resolve"
    severity = {"failure": "critical", "warning": "warning", "success": "info"}.get(alert_type, "info")

    payload = json.dumps({
        "routing_key": routing_key,
        "event_action": action,
        "payload": {
            "summary": message,
            "source": "continuum-backup",
            "severity": severity,
        },
    }).encode()

    url = "https://events.pagerduty.com/v2/enqueue"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("PagerDuty alert sent (HTTP %d)", resp.status)
    except urllib.error.HTTPError as exc:
        logger.error("PagerDuty rejected alert (HTTP %d): %s", exc.code, exc.read())
        raise


async def _send_webhook_alert(url: str, alert_type: str, message: str) -> None:
    """POST alert JSON to an arbitrary HTTP webhook URL."""
    payload = json.dumps({
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        logger.info("Webhook alert sent to %s (HTTP %d)", url, resp.status)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
