#!/usr/bin/env python3
"""
CONTINUUM Backup System Example

Demonstrates comprehensive backup and recovery capabilities.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from continuum.backup import BackupManager, BackupConfig
from continuum.backup.types import (
    BackupStrategy,
    StorageConfig,
    StorageBackend,
    EncryptionConfig,
    RetentionPolicy,
    BackupSchedule,
    RestoreTarget,
    CompressionAlgorithm,
)


async def example_basic_backup():
    """Basic backup example"""
    print("\n=== Basic Backup Example ===\n")

    # Configure local storage
    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    # Create backup configuration
    config = BackupConfig(
        primary_storage=storage,
        db_path=Path("continuum_data/memory.db"),
        compression_enabled=True,
        compression_algorithm=CompressionAlgorithm.ZSTD,
    )

    # Create backup manager
    manager = BackupManager(config)

    # Create a full backup
    print("Creating full backup...")
    result = await manager.create_backup(strategy=BackupStrategy.FULL)

    if result.success:
        print(f"✓ Backup created: {result.backup_id}")
        print(f"  - Size: {result.bytes_backed_up / 1024 / 1024:.2f} MB")
        print(f"  - Records: {result.records_backed_up}")
        print(f"  - Duration: {result.duration_seconds:.2f}s")
    else:
        print(f"✗ Backup failed: {result.error}")


async def example_encrypted_backup():
    """Backup with encryption"""
    print("\n=== Encrypted Backup Example ===\n")

    # Configure encryption
    encryption = EncryptionConfig(
        enabled=True,
        algorithm="AES-256-GCM",
        key_id="production-key-v1",
    )

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        encryption=encryption,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    print("Creating encrypted backup...")
    result = await manager.create_backup(
        strategy=BackupStrategy.FULL,
        encrypt=True,
        compress=True,
    )

    if result.success:
        print(f"✓ Encrypted backup created: {result.backup_id}")
        print(f"  - Encryption: AES-256-GCM")
        print(f"  - Key ID: {result.metadata.encryption_key_id}")
        print(f"  - Compressed: {result.metadata.compression_ratio:.1%}")


async def example_multi_cloud_backup():
    """Multi-cloud redundant backup"""
    print("\n=== Multi-Cloud Backup Example ===\n")

    # Configure multiple storage destinations
    multi_storage = StorageConfig(
        backend=StorageBackend.MULTI,
        destinations=[
            # Primary: AWS S3
            StorageConfig(
                backend=StorageBackend.S3,
                s3_bucket="continuum-backups-primary",
                s3_region="us-east-1",
            ),
            # Secondary: Google Cloud Storage
            StorageConfig(
                backend=StorageBackend.GCS,
                gcs_bucket="continuum-backups-secondary",
                gcs_project="my-project",
            ),
            # Tertiary: Local filesystem
            StorageConfig(
                backend=StorageBackend.LOCAL,
                local_path=Path("/var/backups/continuum"),
            ),
        ],
        require_all_success=False,  # Tolerate single destination failure
    )

    config = BackupConfig(
        primary_storage=multi_storage,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    print("Creating multi-cloud backup...")
    result = await manager.create_backup(strategy=BackupStrategy.FULL)

    if result.success:
        print(f"✓ Multi-cloud backup created: {result.backup_id}")
        print("  - Stored in: S3, GCS, and local filesystem")
        print("  - Redundancy: 3 copies across 2 cloud providers")


async def example_incremental_backup():
    """Incremental backup for frequent protection"""
    print("\n=== Incremental Backup Example ===\n")

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    # Create base full backup
    print("Creating base full backup...")
    full_result = await manager.create_backup(strategy=BackupStrategy.FULL)
    print(f"✓ Full backup: {full_result.backup_id}")

    # Simulate some changes
    print("\n(Simulating database changes...)")
    await asyncio.sleep(1)

    # Create incremental backup (only changes)
    print("\nCreating incremental backup...")
    inc_result = await manager.create_backup(strategy=BackupStrategy.INCREMENTAL)

    if inc_result.success:
        print(f"✓ Incremental backup: {inc_result.backup_id}")
        print(f"  - Base: {full_result.backup_id}")
        print(f"  - Size: {inc_result.bytes_backed_up / 1024:.2f} KB (much smaller!)")
        print(f"  - Changes: {inc_result.records_backed_up} records")


async def example_restore():
    """Restore from backup"""
    print("\n=== Restore Example ===\n")

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    # List available backups
    print("Available backups:")
    backups = await manager.list_backups()

    for backup in backups[:5]:  # Show first 5
        print(f"  - {backup.backup_id}")
        print(f"    Created: {backup.created_at}")
        print(f"    Strategy: {backup.strategy.value}")
        print(f"    Verified: {'✓' if backup.verified else '✗'}")

    if not backups:
        print("  (No backups available)")
        return

    # Restore latest verified backup
    latest_verified = next((b for b in backups if b.verified), backups[0])

    print(f"\nRestoring from: {latest_verified.backup_id}")

    # Define restore target
    target = RestoreTarget(
        database_path=Path("/tmp/restored_memory.db"),
        overwrite=True,
        verify_after_restore=True,
    )

    # Perform restore
    restore_result = await manager.restore(latest_verified.backup_id, target)

    if restore_result.success:
        print(f"✓ Restore completed successfully")
        print(f"  - Duration: {restore_result.duration_seconds:.2f}s")
        print(f"  - Records restored: {restore_result.records_restored}")
        print(f"  - Tables restored: {restore_result.tables_restored}")
        print(f"  - Verified: {'✓' if restore_result.verified else '✗'}")
    else:
        print(f"✗ Restore failed: {restore_result.error}")


async def example_verification():
    """Verify backup integrity"""
    print("\n=== Backup Verification Example ===\n")

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    # Get latest backup
    backups = await manager.list_backups()

    if not backups:
        print("No backups to verify")
        return

    backup_id = backups[0].backup_id

    print(f"Verifying backup: {backup_id}")

    # Verify backup
    verification = await manager.verify_backup(backup_id)

    print("\nVerification Results:")
    print(f"  Overall: {'✓ PASS' if verification.success else '✗ FAIL'}")
    print(f"  Checksum: {'✓' if verification.checksum_valid else '✗'}")
    print(f"  Schema: {'✓' if verification.schema_valid else '✗'}")
    print(f"  Data sample: {'✓' if verification.data_sample_valid else '✗'}")

    if verification.errors:
        print("\nErrors:")
        for error in verification.errors:
            print(f"  - {error}")


async def example_retention_policy():
    """Apply retention policy"""
    print("\n=== Retention Policy Example ===\n")

    # Define retention policy
    retention = RetentionPolicy(
        keep_hourly_for_days=1,
        keep_daily_for_days=7,
        keep_weekly_for_weeks=4,
        keep_monthly_for_months=12,
        min_backups_to_keep=3,
        require_verified=True,
        grace_period_days=7,
    )

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        retention_policy=retention,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    print("Retention Policy:")
    print(f"  - Hourly backups: {retention.keep_hourly_for_days} day(s)")
    print(f"  - Daily backups: {retention.keep_daily_for_days} day(s)")
    print(f"  - Weekly backups: {retention.keep_weekly_for_weeks} week(s)")
    print(f"  - Monthly backups: {retention.keep_monthly_for_months} month(s)")
    print(f"  - Minimum to keep: {retention.min_backups_to_keep}")

    # Apply retention policy
    print("\nApplying retention policy...")
    result = await manager.apply_retention_policy()

    print(f"\nResults:")
    print(f"  - Backups evaluated: {result.backups_evaluated}")
    print(f"  - Backups deleted: {result.backups_deleted}")
    print(f"  - Backups kept: {result.backups_kept}")
    print(f"  - Space freed: {result.bytes_freed / 1024 / 1024:.2f} MB")

    if result.deleted_backup_ids:
        print(f"\nDeleted backups:")
        for backup_id in result.deleted_backup_ids:
            print(f"  - {backup_id}")


async def example_health_check():
    """Check backup system health"""
    print("\n=== Health Check Example ===\n")

    storage = StorageConfig(
        backend=StorageBackend.LOCAL,
        local_path=Path("/tmp/continuum-backups"),
    )

    config = BackupConfig(
        primary_storage=storage,
        target_rpo_minutes=5,
        target_rto_minutes=60,
        db_path=Path("continuum_data/memory.db"),
    )

    manager = BackupManager(config)

    # Get health status
    health = await manager.get_health()

    print(f"Backup System Health: {'✓ HEALTHY' if health.healthy else '✗ UNHEALTHY'}")
    print(f"\nMetrics:")
    print(f"  - Total backups: {health.total_backups}")
    print(f"  - Last backup: {health.last_backup_time}")
    print(f"  - Last successful: {health.last_successful_backup}")
    print(f"  - Failed (24h): {health.failed_backups_24h}")
    print(f"  - Avg duration: {health.average_backup_duration_seconds:.2f}s")
    print(f"  - Storage used: {health.total_storage_used_bytes / 1024 / 1024:.2f} MB")

    print(f"\nSLA Compliance:")
    print(f"  - RPO (< {config.target_rpo_minutes} min): {'✓' if health.rpo_compliant else '✗'}")
    print(f"  - RTO (< {config.target_rto_minutes} min): {'✓' if health.rto_compliant else '✗'}")

    if health.warnings:
        print(f"\nWarnings:")
        for warning in health.warnings:
            print(f"  - {warning}")

    if health.errors:
        print(f"\nErrors:")
        for error in health.errors:
            print(f"  - {error}")


async def main():
    """Run all examples"""
    print("=" * 70)
    print("CONTINUUM Backup System Examples")
    print("=" * 70)

    try:
        # Run examples
        await example_basic_backup()
        await example_encrypted_backup()
        # await example_multi_cloud_backup()  # Requires cloud credentials
        await example_incremental_backup()
        await example_restore()
        await example_verification()
        await example_retention_policy()
        await example_health_check()

        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
