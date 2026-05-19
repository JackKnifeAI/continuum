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
import smtplib
import ssl
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
        config: Optional backup configuration for metadata access

    Returns:
        Dictionary of metrics with counters and histogram sample lists
    """
    metrics: Dict[str, Any] = {
        "backup_duration_seconds": [],   # histogram samples
        "backup_size_bytes": [],         # histogram samples
        "backup_success_total": 0,       # counter
        "backup_failure_total": 0,       # counter
        "restore_duration_seconds": [],  # histogram samples
        "retention_deletions_total": 0,  # counter
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

            if backup.compressed_size_bytes > 0:
                metrics["backup_size_bytes"].append(backup.compressed_size_bytes)

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

        logger.debug(
            "Metrics collected: %d successes, %d failures, %d size samples",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
            len(metrics["backup_size_bytes"]),
        )

    except Exception as e:
        logger.warning("Failed to collect backup metrics: %s", e)

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
        logger.warning("No notification channels configured, alert not sent: %s", message)
        return

    for channel in channels:
        try:
            await _dispatch_alert(alert_type, message, channel)
        except Exception as e:
            logger.error("Failed to send alert to channel '%s': %s", channel, e)

async def _dispatch_alert(alert_type: str, message: str, channel: str) -> None:
    """
    Route an alert to the appropriate channel handler.

    Channel string format:
      slack:<webhook_url>
      webhook:<url>
      email:<smtp_host>:<port>:<user>:<password>:<to_address>
      pagerduty:<routing_key>
    """
    if channel.startswith("slack:"):
        await _send_slack_alert(alert_type, message, channel[len("slack:"):])
    elif channel.startswith("webhook:"):
        await _send_webhook_alert(alert_type, message, channel[len("webhook:"):])
    elif channel.startswith("email:"):
        await _send_email_alert(alert_type, message, channel[len("email:"):])
    elif channel.startswith("pagerduty:"):
        await _send_pagerduty_alert(alert_type, message, channel[len("pagerduty:"):])
    else:
        logger.warning("Unknown notification channel scheme: %s", channel)


async def _send_slack_alert(alert_type: str, message: str, webhook_url: str) -> None:
    """POST alert to a Slack incoming webhook URL."""
    import aiohttp

    emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
        alert_type, ":information_source:"
    )
    payload = {"text": f"{emoji} *Backup {alert_type.upper()}*: {message}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Slack returned {resp.status}: {body}")

    logger.info("Slack alert sent (%s)", alert_type)


async def _send_webhook_alert(alert_type: str, message: str, url: str) -> None:
    """POST alert payload to a generic webhook URL."""
    import aiohttp

    payload = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "continuum-backup",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status not in (200, 201, 202, 204):
                body = await resp.text()
                raise RuntimeError(f"Webhook returned {resp.status}: {body}")

    logger.info("Webhook alert sent to %s (%s)", url, alert_type)


async def _send_email_alert(alert_type: str, message: str, spec: str) -> None:
    """
    Send alert via SMTP.

    spec format: <host>:<port>:<user>:<password>:<to_address>
    """
    import asyncio

    parts = spec.split(":", 4)
    if len(parts) != 5:
        raise ValueError(
            "email channel spec must be <host>:<port>:<user>:<password>:<to_address>"
        )
    host, port_str, user, password, to_address = parts
    port = int(port_str)

    subject = f"[Continuum Backup] {alert_type.upper()}"
    msg = MIMEText(f"Alert type: {alert_type}\n\n{message}\n\nTimestamp: {datetime.utcnow().isoformat()}")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_address

    def _send() -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(user, password)
            server.sendmail(user, [to_address], msg.as_string())

    await asyncio.get_event_loop().run_in_executor(None, _send)
    logger.info("Email alert sent to %s (%s)", to_address, alert_type)


async def _send_pagerduty_alert(alert_type: str, message: str, routing_key: str) -> None:
    """
    Trigger a PagerDuty event via the Events API v2.

    routing_key: PagerDuty integration routing key
    """
    import aiohttp

    severity = {"failure": "critical", "warning": "warning", "success": "info"}.get(
        alert_type, "info"
    )
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger" if alert_type == "failure" else "resolve",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "continuum-backup",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://events.pagerduty.com/v2/enqueue",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status not in (200, 202):
                body = await resp.text()
                raise RuntimeError(f"PagerDuty returned {resp.status}: {body}")

    logger.info("PagerDuty alert sent (%s)", alert_type)


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
