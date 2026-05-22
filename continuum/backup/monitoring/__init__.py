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
        config: Optional backup config to read metrics from metadata store

    Returns:
        Dictionary of metrics with counters and histogram summaries
    """
    def _histogram(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_size_bytes": _histogram([]),
        "backup_duration_seconds": _histogram([]),
        "restore_duration_seconds": _histogram([]),
        "retention_deletions_total": 0,
        "total_backups": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore
        metadata_store = MetadataStore(config.metadata_db_path)
        all_backups = metadata_store.list_backups()

        metrics["total_backups"] = len(all_backups)

        sizes: List[float] = []
        durations: List[float] = []

        for backup in all_backups:
            if backup.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif backup.status.value == "failed":
                metrics["backup_failure_total"] += 1

            if backup.compressed_size_bytes > 0:
                sizes.append(float(backup.compressed_size_bytes))

            if backup.completed_at and backup.created_at:
                duration = (backup.completed_at - backup.created_at).total_seconds()
                durations.append(duration)

        metrics["backup_size_bytes"] = _histogram(sizes)
        metrics["backup_duration_seconds"] = _histogram(durations)

        logger.debug(
            "Metrics collected: %d successful, %d failed, %d total backups",
            metrics["backup_success_total"],
            metrics["backup_failure_total"],
            metrics["total_backups"],
        )

    except Exception as e:
        logger.error("Failed to collect backup metrics: %s", e, exc_info=True)

    return metrics


def _post_webhook(url: str, payload: Dict[str, Any], timeout: int = 10) -> bool:
    """POST JSON payload to a webhook URL. Returns True on success."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "continuum-backup/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except urllib.error.URLError as exc:
        logger.error("Webhook POST to %s failed: %s", url, exc)
        return False


def _send_email(channel: str, subject: str, body: str) -> bool:
    """
    Send email via SMTP.

    Channel format: smtp://user:password@host:port/recipient@example.com
    """
    try:
        # Parse smtp://user:pass@host:port/to
        rest = channel[len("smtp://"):]
        credentials, rest = rest.rsplit("@", 1)
        user, password = credentials.split(":", 1)
        host_port, recipient = rest.split("/", 1)
        host, port_str = (host_port.rsplit(":", 1) if ":" in host_port else (host_port, "587"))
        port = int(port_str)

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = recipient

        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(user, [recipient], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Email send failed for channel %s: %s", channel, exc)
        return False


async def _dispatch_to_channels(
    alert_type: str,
    message: str,
    channels: List[str],
) -> Dict[str, bool]:
    """Dispatch alert to all configured notification channels."""
    import asyncio

    results: Dict[str, bool] = {}
    subject = f"[Continuum Backup] {alert_type.upper()}: Alert"

    for channel in channels:
        if channel.startswith(("http://", "https://")):
            if "hooks.slack.com" in channel:
                # Slack incoming webhook format
                emoji = {"failure": ":red_circle:", "warning": ":warning:", "success": ":white_check_mark:"}.get(
                    alert_type, ":information_source:"
                )
                payload: Dict[str, Any] = {
                    "text": f"{emoji} *Backup {alert_type.upper()}*: {message}"
                }
            else:
                # Generic JSON webhook
                payload = {
                    "alert_type": alert_type,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "continuum-backup",
                }
            ok = await asyncio.to_thread(_post_webhook, channel, payload)
            results[channel] = ok

        elif channel.startswith("smtp://"):
            ok = await asyncio.to_thread(_send_email, channel, subject, message)
            results[channel] = ok

        else:
            logger.warning(
                "Unsupported notification channel format %r — "
                "use http(s):// for webhooks or smtp:// for email",
                channel,
            )
            results[channel] = False

    return results


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
        logger.debug("No notification channels configured; skipping alert")
        return

    results = await _dispatch_to_channels(alert_type, message, channels)
    failed = [ch for ch, ok in results.items() if not ok]
    if failed:
        logger.error("Alert delivery failed for channels: %s", failed)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
