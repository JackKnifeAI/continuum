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
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

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
        config: Optional backup configuration; when provided, metrics are
                populated from the metadata store.

    Returns:
        Dictionary of metrics with counters and histogram summaries.
    """
    metrics: Dict[str, Any] = {
        "backup_success_total": 0,
        "backup_failure_total": 0,
        "backup_duration_seconds": [],
        "backup_size_bytes": [],
        "restore_duration_seconds": [],
        "retention_deletions_total": 0,
    }

    if config is None:
        return metrics

    try:
        from ..metadata import MetadataStore

        store = MetadataStore(config.metadata_db_path)
        backups = store.list_backups()

        for b in backups:
            if b.compressed_size_bytes > 0:
                metrics["backup_size_bytes"].append(b.compressed_size_bytes)

            if b.completed_at and b.created_at:
                duration = (b.completed_at - b.created_at).total_seconds()
                metrics["backup_duration_seconds"].append(duration)

            if b.status.value in ("completed", "verified"):
                metrics["backup_success_total"] += 1
            elif b.status.value == "failed":
                metrics["backup_failure_total"] += 1

        # Summarise histogram samples into scalar stats
        for key in ("backup_duration_seconds", "backup_size_bytes", "restore_duration_seconds"):
            samples: List[float] = metrics[key]
            if samples:
                sorted_samples = sorted(samples)
                metrics[f"{key}_count"] = len(sorted_samples)
                metrics[f"{key}_sum"] = sum(sorted_samples)
                metrics[f"{key}_avg"] = sum(sorted_samples) / len(sorted_samples)
                metrics[f"{key}_p50"] = sorted_samples[len(sorted_samples) // 2]
                metrics[f"{key}_max"] = sorted_samples[-1]

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}", exc_info=True)

    return metrics


async def _dispatch_webhook(url: str, payload: Dict[str, Any]) -> None:
    """POST a JSON payload to a webhook URL using a thread-pool executor."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: urlopen(req, timeout=10))
    except URLError as exc:
        raise RuntimeError(f"Webhook POST failed: {exc.reason}") from exc


async def send_alert(
    alert_type: str,
    message: str,
    config: BackupConfig,
):
    """
    Send alert through configured notification channels.

    Channels are read from ``config.notification_channels``.  Each entry
    that starts with ``http://`` or ``https://`` is treated as a webhook
    URL and receives a JSON POST.  Unknown channel strings are logged as
    warnings so they can be wired up later without losing visibility.

    Args:
        alert_type: Type of alert (``failure``, ``warning``, ``success``)
        message: Alert message
        config: Backup configuration with notification channels
    """
    logger.info(f"Sending {alert_type} alert: {message}")

    if alert_type == "success" and not config.notify_on_success:
        return
    if alert_type == "failure" and not config.notify_on_failure:
        return

    channels = config.notification_channels
    if not channels:
        logger.warning("No notification channels configured — alert not delivered")
        return

    payload: Dict[str, Any] = {
        "type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tenant_id": config.tenant_id,
    }

    for channel in channels:
        try:
            if channel.startswith(("http://", "https://")):
                await _dispatch_webhook(channel, payload)
                logger.info(f"Alert dispatched to webhook: {channel}")
            else:
                logger.warning(
                    f"Unsupported notification channel {channel!r}. "
                    "Supported: HTTP/HTTPS webhook URLs."
                )
        except Exception as exc:
            logger.error(f"Failed to send alert to {channel!r}: {exc}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
