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
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        config: Backup configuration (uses default metadata path if omitted)

    Returns:
        Dictionary of metrics with histogram lists and counters
    """
    from ..metadata import MetadataStore

    db_path = config.metadata_db_path if config else Path("continuum_data/backups/metadata.db")

    try:
        metadata_store = MetadataStore(db_path)
        all_backups = metadata_store.list_backups()
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        return {}

    backup_duration_seconds: List[float] = []
    backup_size_bytes: List[int] = []
    success_total = 0
    failure_total = 0

    for b in all_backups:
        if b.status.value in ("completed", "verified"):
            success_total += 1
            if b.completed_at and b.created_at:
                backup_duration_seconds.append(
                    (b.completed_at - b.created_at).total_seconds()
                )
            if b.compressed_size_bytes:
                backup_size_bytes.append(b.compressed_size_bytes)
        elif b.status.value == "failed":
            failure_total += 1

    return {
        "backup_duration_seconds": backup_duration_seconds,
        "backup_size_bytes": backup_size_bytes,
        "backup_success_total": success_total,
        "backup_failure_total": failure_total,
        # restore_duration_seconds not stored in backup metadata
        "restore_duration_seconds": [],
        # retention deletions not tracked in current schema
        "retention_deletions_total": 0,
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

    channels = config.notification_channels
    if not channels:
        logger.debug("No notification channels configured")
        return

    for channel in channels:
        try:
            if "hooks.slack.com" in channel:
                await _send_slack_alert(channel, alert_type, message)
            elif channel.startswith("pagerduty://"):
                routing_key = channel[len("pagerduty://"):]
                await _send_pagerduty_alert(routing_key, alert_type, message)
            elif "@" in channel and "://" not in channel:
                await _send_email_alert(channel, alert_type, message)
            elif channel.startswith("http://") or channel.startswith("https://"):
                await _send_webhook_alert(channel, alert_type, message)
            else:
                logger.warning(f"Unknown notification channel format: {channel}")
        except Exception as e:
            logger.error(f"Failed to send alert to {channel}: {e}")

async def _send_slack_alert(webhook_url: str, alert_type: str, message: str) -> None:
    """Post alert to a Slack incoming webhook."""
    color = {"failure": "#FF0000", "warning": "#FFA500", "success": "#36A64F"}.get(
        alert_type, "#808080"
    )
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"Continuum Backup — {alert_type.upper()}",
                "text": message,
                "ts": int(datetime.utcnow().timestamp()),
            }
        ]
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
    logger.info(f"Slack alert sent: {alert_type}")


async def _send_pagerduty_alert(routing_key: str, alert_type: str, message: str) -> None:
    """Send event to PagerDuty Events API v2."""
    severity = {"failure": "critical", "warning": "warning", "success": "info"}.get(
        alert_type, "info"
    )
    event_action = "trigger" if alert_type in ("failure", "warning") else "resolve"
    payload = {
        "routing_key": routing_key,
        "event_action": event_action,
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://events.pagerduty.com/v2/enqueue", json=payload
        )
        resp.raise_for_status()
    logger.info(f"PagerDuty alert sent: {alert_type}")


async def _send_email_alert(recipient: str, alert_type: str, message: str) -> None:
    """Send alert via SMTP. Reads config from BACKUP_SMTP_* env vars."""
    smtp_host = os.environ.get("BACKUP_SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("BACKUP_SMTP_PORT", "25"))
    smtp_from = os.environ.get("BACKUP_SMTP_FROM", "backup@continuum.ai")
    smtp_user = os.environ.get("BACKUP_SMTP_USER", "")
    smtp_pass = os.environ.get("BACKUP_SMTP_PASS", "")

    msg = MIMEText(message)
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}"
    msg["From"] = smtp_from
    msg["To"] = recipient

    def _smtp_send() -> None:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [recipient], msg.as_string())

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _smtp_send)
    logger.info(f"Email alert sent to {recipient}: {alert_type}")


async def _send_webhook_alert(url: str, alert_type: str, message: str) -> None:
    """POST alert as JSON to a generic webhook URL."""
    payload = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
    logger.info(f"Webhook alert sent to {url}: {alert_type}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
