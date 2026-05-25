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
import ssl
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        config: Optional backup configuration for querying metadata store

    Returns:
        Dictionary with counters and histogram sample lists:
        - backup_duration_seconds: list of completed backup durations
        - backup_size_bytes: list of compressed sizes for completed backups
        - backup_success_total: count of completed/verified backups
        - backup_failure_total: count of failed backups
        - restore_duration_seconds: reserved for restore tracking
        - retention_deletions_total: reserved for retention tracking
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

        store = MetadataStore(config.metadata_db_path)
        all_backups = store.list_backups()

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
                if backup.completed_at and backup.created_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    metrics["backup_duration_seconds"].append(duration)
                if backup.compressed_size_bytes:
                    metrics["backup_size_bytes"].append(backup.compressed_size_bytes)
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

        logger.debug(
            "Collected metrics: %d successful, %d failed backups",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
        )
    except Exception as e:
        logger.error("Failed to collect backup metrics: %s", e, exc_info=True)

    return metrics


def _send_slack_notification(webhook_url: str, alert_type: str, message: str) -> None:
    """POST alert to a Slack incoming-webhook URL."""
    emoji = {"failure": ":x:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = json.dumps({"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        if resp.status != 200:
            raise RuntimeError(f"Slack webhook returned HTTP {resp.status}")


def _send_webhook_notification(url: str, alert_type: str, message: str) -> None:
    """POST a JSON alert payload to a generic HTTP webhook."""
    payload = json.dumps(
        {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "continuum-backup",
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        if resp.status not in (200, 201, 202, 204):
            raise RuntimeError(f"Webhook returned HTTP {resp.status}")


def _send_pagerduty_notification(routing_key: str, alert_type: str, message: str) -> None:
    """Trigger a PagerDuty Events API v2 event."""
    severity = "critical" if alert_type == "failure" else "warning"
    payload = json.dumps(
        {
            "routing_key": routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "continuum-backup",
            },
        }
    ).encode()
    req = urllib.request.Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        if resp.status not in (200, 202):
            raise RuntimeError(f"PagerDuty returned HTTP {resp.status}")


def _send_email_notification(recipient: str, alert_type: str, message: str) -> None:
    """Send an alert email via SMTP (credentials from env vars).

    Required env vars: SMTP_HOST (default localhost), SMTP_PORT (default 587).
    Optional: SMTP_USER, SMTP_PASSWORD, SMTP_FROM.
    """
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    smtp_from = os.environ.get("SMTP_FROM", "backup@continuum")

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = recipient
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}"
    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        if smtp_port == 587:
            server.starttls(context=ssl.create_default_context())
        if smtp_user:
            server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from, [recipient], msg.as_string())


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured channels.

    Channels are specified as ``type:target`` strings in
    ``config.notification_channels``.  Supported types:

    - ``slack:<webhook_url>`` — Slack incoming webhook
    - ``webhook:<url>`` — generic HTTP POST webhook (JSON body)
    - ``pagerduty:<routing_key>`` — PagerDuty Events API v2
    - ``email:<recipient>`` — SMTP email (configure via SMTP_* env vars)

    Args:
        alert_type: One of ``failure``, ``warning``, ``success``
        message: Human-readable alert message
        config: Backup configuration with notification channels
    """
    logger.info("Sending %s alert: %s", alert_type, message)

    if alert_type == "success" and not config.notify_on_success:
        return
    if alert_type == "failure" and not config.notify_on_failure:
        return

    if not config.notification_channels:
        logger.debug("No notification channels configured")
        return

    loop = asyncio.get_running_loop()
    _dispatch: Dict[str, Any] = {
        "slack": _send_slack_notification,
        "webhook": _send_webhook_notification,
        "pagerduty": _send_pagerduty_notification,
        "email": _send_email_notification,
    }

    for channel in config.notification_channels:
        if ":" not in channel:
            logger.warning("Invalid notification channel (expected type:target): %s", channel)
            continue

        scheme, target = channel.split(":", 1)
        handler = _dispatch.get(scheme)
        if handler is None:
            logger.warning("Unknown notification channel type '%s' in '%s'", scheme, channel)
            continue

        try:
            await loop.run_in_executor(None, handler, target, alert_type, message)
            logger.info("Alert sent via %s channel", scheme)
        except Exception as e:
            logger.error("Failed to send alert via %s: %s", channel, e, exc_info=True)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
