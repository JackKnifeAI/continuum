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

import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import httpx

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
        config: Optional backup configuration; when provided, real data is
                read from the metadata store.

    Returns:
        Dictionary of metrics with keys:
        - backup_duration_seconds: list of completed backup durations
        - backup_size_bytes: list of compressed backup sizes
        - backup_success_total: cumulative successful backup count
        - backup_failure_total: cumulative failed backup count
        - restore_duration_seconds: list of completed restore durations
        - retention_deletions_total: cumulative deleted-by-retention count
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

        for b in all_backups:
            if b.compressed_size_bytes:
                metrics["backup_size_bytes"].append(b.compressed_size_bytes)

            if b.completed_at and b.created_at:
                duration = (b.completed_at - b.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

            if b.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif b.status.value == "failed":
                metrics["backup_failure_total"] += 1

        # Restore metrics require a RestoreRecord type; query if available
        try:
            restore_records = store.list_restores()
            for r in restore_records:
                if r.completed_at and r.started_at:
                    duration = (r.completed_at - r.started_at).total_seconds()
                    metrics["restore_duration_seconds"].append(duration)
        except AttributeError:
            pass  # list_restores not yet implemented in MetadataStore

        # Retention deletions are tracked separately if the store supports it
        try:
            metrics["retention_deletions_total"] = store.count_deleted_by_retention()
        except AttributeError:
            pass

    except Exception as e:
        logger.warning(f"Could not collect backup metrics from store: {e}")

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

    channels = config.notification_channels if config.notification_channels else []
    if not channels:
        logger.debug("No notification channels configured")
        return

    timestamp = datetime.utcnow().isoformat()

    for channel in channels:
        try:
            if channel == "email":
                await _send_email_alert(alert_type, message, timestamp)
            elif channel == "slack":
                await _send_slack_alert(alert_type, message, timestamp)
            elif channel == "pagerduty":
                await _send_pagerduty_alert(alert_type, message, timestamp)
            elif channel == "webhook":
                await _send_webhook_alert(alert_type, message, timestamp)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to send alert via {channel}: {e}")

async def _send_email_alert(alert_type: str, message: str, timestamp: str) -> None:
    """Send alert via SMTP email.

    Reads configuration from environment variables:
    BACKUP_SMTP_HOST, BACKUP_SMTP_PORT, BACKUP_SMTP_USER,
    BACKUP_SMTP_PASSWORD, BACKUP_ALERT_EMAIL_FROM, BACKUP_ALERT_EMAIL_TO
    """
    host = os.environ.get("BACKUP_SMTP_HOST", "localhost")
    port = int(os.environ.get("BACKUP_SMTP_PORT", "587"))
    user = os.environ.get("BACKUP_SMTP_USER", "")
    password = os.environ.get("BACKUP_SMTP_PASSWORD", "")
    from_addr = os.environ.get("BACKUP_ALERT_EMAIL_FROM", user)
    to_addrs = os.environ.get("BACKUP_ALERT_EMAIL_TO", "")

    if not to_addrs:
        logger.warning("BACKUP_ALERT_EMAIL_TO not set; skipping email alert")
        return

    subject = f"[Continuum Backup] {alert_type.upper()}: {message[:80]}"
    body = f"Alert type: {alert_type}\nTimestamp: {timestamp}\n\n{message}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addrs

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(from_addr, to_addrs.split(","), msg.as_string())

    logger.info(f"Email alert sent to {to_addrs}")


async def _send_slack_alert(alert_type: str, message: str, timestamp: str) -> None:
    """Send alert to a Slack incoming webhook (env: BACKUP_SLACK_WEBHOOK_URL)."""
    webhook_url = os.environ.get("BACKUP_SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("BACKUP_SLACK_WEBHOOK_URL not set; skipping Slack alert")
        return

    color = {"failure": "#e74c3c", "warning": "#f39c12", "success": "#2ecc71"}.get(
        alert_type, "#95a5a6"
    )
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"Continuum Backup — {alert_type.upper()}",
                "text": message,
                "footer": f"continuum-backup | {timestamp}",
            }
        ]
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()

    logger.info("Slack alert sent")


async def _send_pagerduty_alert(alert_type: str, message: str, timestamp: str) -> None:
    """Trigger or resolve a PagerDuty incident (env: BACKUP_PAGERDUTY_ROUTING_KEY)."""
    routing_key = os.environ.get("BACKUP_PAGERDUTY_ROUTING_KEY", "")
    if not routing_key:
        logger.warning("BACKUP_PAGERDUTY_ROUTING_KEY not set; skipping PagerDuty alert")
        return

    event_action = "resolve" if alert_type == "success" else "trigger"
    severity = "critical" if alert_type == "failure" else "warning"

    payload = {
        "routing_key": routing_key,
        "event_action": event_action,
        "dedup_key": "continuum-backup-alert",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": timestamp,
        },
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://events.pagerduty.com/v2/enqueue", json=payload
        )
        resp.raise_for_status()

    logger.info(f"PagerDuty alert sent (action={event_action})")


async def _send_webhook_alert(alert_type: str, message: str, timestamp: str) -> None:
    """POST alert JSON to a generic webhook (env: BACKUP_WEBHOOK_URL)."""
    webhook_url = os.environ.get("BACKUP_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("BACKUP_WEBHOOK_URL not set; skipping webhook alert")
        return

    payload = {
        "source": "continuum-backup",
        "alert_type": alert_type,
        "message": message,
        "timestamp": timestamp,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()

    logger.info(f"Webhook alert sent to {webhook_url}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
