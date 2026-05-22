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
        config: Backup configuration (required to access metadata store)

    Returns:
        Dictionary of metrics with histogram lists and counters
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],   # histogram: duration of each completed backup
        "backup_size_bytes": [],         # histogram: compressed size of each backup
        "backup_success_total": 0,       # counter: total successful backups
        "backup_failure_total": 0,       # counter: total failed backups
        "restore_duration_seconds": [],  # histogram: duration of each restore (not yet tracked)
        "retention_deletions_total": 0,  # counter: total backups deleted by retention (not yet tracked)
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
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.compressed_size_bytes:
                metrics["backup_size_bytes"].append(backup.compressed_size_bytes)

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

        logger.debug(
            f"Collected metrics: {metrics['backup_success_total']} successes, "
            f"{metrics['backup_failure_total']} failures, "
            f"{len(metrics['backup_duration_seconds'])} duration samples"
        )
    except Exception as e:
        logger.warning(f"Failed to collect backup metrics: {e}")

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
            logger.error(f"Failed to send alert to channel '{channel}': {e}")

async def _dispatch_alert(channel: str, alert_type: str, message: str) -> None:
    """Route an alert to the correct handler based on channel URL scheme/host."""
    parsed = urllib.parse.urlparse(channel)
    scheme = parsed.scheme.lower()

    if scheme in ("http", "https"):
        host = parsed.netloc.lower()
        if "hooks.slack.com" in host:
            await _send_slack_alert(channel, alert_type, message)
        elif "pagerduty.com" in host:
            await _send_pagerduty_alert(channel, alert_type, message)
        else:
            await _send_webhook_alert(channel, alert_type, message)
    elif scheme == "smtp":
        await _send_smtp_alert(parsed, alert_type, message)
    else:
        logger.warning(f"Unknown notification channel scheme '{scheme}' in: {channel}")


async def _send_slack_alert(url: str, alert_type: str, message: str) -> None:
    """Send alert to a Slack incoming webhook URL."""
    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":bell:"
    )
    payload = {"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}
    await _post_json(url, payload)
    logger.info(f"Slack alert sent ({alert_type})")


async def _send_pagerduty_alert(url: str, alert_type: str, message: str) -> None:
    """Send event to PagerDuty Events API v2."""
    severity = {"failure": "critical", "warning": "warning"}.get(alert_type, "info")
    payload = {
        "event_action": "trigger",
        "payload": {
            "summary": f"Backup {alert_type}: {message}",
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
    await _post_json(url, payload)
    logger.info(f"PagerDuty alert sent (severity={severity})")


async def _send_webhook_alert(url: str, alert_type: str, message: str) -> None:
    """Send alert as JSON POST to a generic webhook URL."""
    payload = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "continuum-backup",
    }
    await _post_json(url, payload)
    logger.info(f"Webhook alert sent ({alert_type}) to {url[:60]}")


async def _send_smtp_alert(parsed: urllib.parse.ParseResult, alert_type: str, message: str) -> None:
    """Send alert via SMTP email.

    Channel URL format: smtp://user:pass@host:port?to=recipient@example.com
    """
    to_addr = urllib.parse.parse_qs(parsed.query).get("to", [""])[0]
    if not to_addr:
        logger.warning("SMTP channel missing 'to' query parameter — skipping")
        return

    host = parsed.hostname or "localhost"
    port = parsed.port or 587
    username = urllib.parse.unquote(parsed.username or "")
    password = urllib.parse.unquote(parsed.password or "")
    from_addr = username or "continuum-backup@localhost"

    msg = MIMEText(message)
    msg["Subject"] = f"[Continuum Backup] {alert_type.upper()}: Backup Alert"
    msg["From"] = from_addr
    msg["To"] = to_addr

    def _send_email() -> None:
        with smtplib.SMTP(host, port) as smtp:
            if username and password:
                smtp.starttls()
                smtp.login(username, password)
            smtp.send_message(msg)

    await asyncio.to_thread(_send_email)
    logger.info(f"Email alert sent ({alert_type}) to {to_addr}")


async def _post_json(url: str, payload: Dict[str, Any]) -> None:
    """POST a JSON payload to a URL, run in a thread to stay non-blocking."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _do_request() -> bytes:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.read()

    await asyncio.to_thread(_do_request)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
