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

    Returns metrics suitable for Prometheus, CloudWatch, etc.

    Args:
        config: Backup configuration (required to query metadata store)

    Returns:
        Dictionary of metric name → value. Counter metrics end in _total;
        histograms are represented as _avg/_min/_max/_p50 variants.
    """
    if config is None:
        return {}

    try:
        from ..metadata import MetadataStore

        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        recent = [b for b in all_backups if b.created_at > cutoff_24h]

        successful = [b for b in all_backups if b.status.value in ("completed", "verified")]
        failed = [b for b in all_backups if b.status.value == "failed"]
        recent_successful = [b for b in recent if b.status.value in ("completed", "verified")]
        recent_failed = [b for b in recent if b.status.value == "failed"]

        completed_with_duration = [
            b for b in all_backups
            if b.completed_at and b.created_at and b.status.value in ("completed", "verified")
        ]
        durations = [
            (b.completed_at - b.created_at).total_seconds()
            for b in completed_with_duration
        ]
        sizes = [b.compressed_size_bytes for b in successful if b.compressed_size_bytes > 0]

        metrics: Dict[str, Any] = {
            "backup_success_total": len(successful),
            "backup_failure_total": len(failed),
            "backup_success_24h_total": len(recent_successful),
            "backup_failure_24h_total": len(recent_failed),
            "backup_total_storage_bytes": sum(b.compressed_size_bytes for b in all_backups),
        }

        if durations:
            sorted_durations = sorted(durations)
            metrics["backup_duration_seconds_avg"] = sum(durations) / len(durations)
            metrics["backup_duration_seconds_min"] = sorted_durations[0]
            metrics["backup_duration_seconds_max"] = sorted_durations[-1]
            metrics["backup_duration_seconds_p50"] = sorted_durations[len(sorted_durations) // 2]

        if sizes:
            sorted_sizes = sorted(sizes)
            metrics["backup_size_bytes_avg"] = sum(sizes) / len(sizes)
            metrics["backup_size_bytes_min"] = sorted_sizes[0]
            metrics["backup_size_bytes_max"] = sorted_sizes[-1]

        logger.debug("Collected %d backup metrics", len(metrics))
        return metrics

    except Exception as e:
        logger.error("Failed to collect backup metrics: %s", e, exc_info=True)
        return {}


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

    channels: List[str] = config.notification_channels or []
    if not channels:
        logger.debug("No notification channels configured; skipping alert dispatch")
        return

    for channel in channels:
        try:
            if channel.startswith(("http://", "https://")):
                await _send_webhook_alert(channel, alert_type, message)
            elif channel.startswith("mailto:"):
                recipient = channel[len("mailto:"):]
                await asyncio.to_thread(_send_email_alert, recipient, alert_type, message)
            else:
                logger.warning("Unknown notification channel format: %s", channel)
        except Exception as e:
            logger.error("Failed to send alert to channel %s: %s", channel, e)

async def _send_webhook_alert(url: str, alert_type: str, message: str) -> None:
    """POST an alert to an HTTP webhook (Slack or generic JSON)."""
    is_slack = "hooks.slack.com" in url
    if is_slack:
        payload = {"text": f"*[{alert_type.upper()}]* {message}"}
    else:
        payload = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    def _post() -> None:
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Webhook returned HTTP {exc.code}: {exc.reason}") from exc

    await asyncio.to_thread(_post)
    logger.info("Alert sent to webhook: %s", url)


def _send_email_alert(recipient: str, alert_type: str, message: str) -> None:
    """Send an alert via SMTP using environment-variable configuration."""
    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user) or "continuum@localhost"

    msg = MIMEText(message)
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}: Backup Alert"
    msg["From"] = smtp_from
    msg["To"] = recipient

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_user and smtp_pass:
            server.starttls()
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    logger.info("Alert email sent to %s", recipient)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
