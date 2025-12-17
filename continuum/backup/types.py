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
Backup System Type Definitions

Core types and enums for the backup and recovery system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from decimal import Decimal


class BackupStrategy(str, Enum):
    """Backup strategy types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    CONTINUOUS = "continuous"


class StorageBackend(str, Enum):
    """Storage backend types"""
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    LOCAL = "local"
    MULTI = "multi"


class CompressionAlgorithm(str, Enum):
    """Compression algorithm types"""
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"
    NONE = "none"


class BackupStatus(str, Enum):
    """Backup job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"
    VERIFIED = "verified"


class RestoreStatus(str, Enum):
    """Restore job status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DECOMPRESSING = "decompressing"
    DECRYPTING = "decrypting"
    RESTORING = "restoring"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    strategy: BackupStrategy
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Size information
    original_size_bytes: int = 0
    compressed_size_bytes: int = 0

    # Backup details
    tables: List[str] = field(default_factory=list)
    record_count: int = 0

    # Storage information
    storage_backend: StorageBackend = StorageBackend.LOCAL
    storage_path: str = ""

    # Security
    encrypted: bool = False
    encryption_key_id: Optional[str] = None

    # Compression
    compressed: bool = False
    compression_algorithm: Optional[CompressionAlgorithm] = None
    compression_ratio: Optional[float] = None

    # Verification
    checksum_sha256: Optional[str] = None
    verified: bool = False
    verified_at: Optional[datetime] = None

    # Dependencies (for incremental/differential)
    base_backup_id: Optional[str] = None

    # Metadata
    tenant_id: str = "default"
    instance_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def compression_ratio_percent(self) -> float:
        """Calculate compression ratio as percentage"""
        if self.original_size_bytes == 0:
            return 0.0
        return (1 - self.compressed_size_bytes / self.original_size_bytes) * 100


@dataclass
class BackupResult:
    """Result of a backup operation"""
    success: bool
    backup_id: Optional[str] = None
    metadata: Optional[BackupMetadata] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Statistics
    bytes_backed_up: int = 0
    records_backed_up: int = 0
    tables_backed_up: int = 0


@dataclass
class RestoreTarget:
    """Target for restore operation"""
    database_path: Optional[Path] = None
    connection_string: Optional[str] = None
    tables: Optional[List[str]] = None  # None = all tables
    overwrite: bool = False
    verify_after_restore: bool = True


@dataclass
class RestoreResult:
    """Result of a restore operation"""
    success: bool
    status: RestoreStatus
    duration_seconds: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Statistics
    bytes_restored: int = 0
    records_restored: int = 0
    tables_restored: int = 0

    # Verification
    verified: bool = False
    verification_errors: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of backup verification"""
    success: bool
    backup_id: str
    verified_at: datetime = field(default_factory=datetime.utcnow)

    # Checks performed
    checksum_valid: bool = False
    schema_valid: bool = False
    data_sample_valid: bool = False
    restore_test_passed: bool = False

    # Issues found
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def all_checks_passed(self) -> bool:
        """Check if all verification checks passed"""
        return (
            self.checksum_valid and
            self.schema_valid and
            self.data_sample_valid and
            len(self.errors) == 0
        )


@dataclass
class RetentionPolicy:
    """Backup retention policy configuration"""

    # Time-based retention
    keep_hourly_for_days: int = 1  # Keep hourly backups for X days
    keep_daily_for_days: int = 7  # Keep daily backups for X days
    keep_weekly_for_weeks: int = 4  # Keep weekly backups for X weeks
    keep_monthly_for_months: int = 12  # Keep monthly backups for X months

    # Count-based retention
    min_backups_to_keep: int = 3  # Never delete below this many backups
    max_backups_to_keep: Optional[int] = None  # Hard limit on backup count

    # Strategy-specific retention
    continuous_keep_hours: int = 24
    incremental_keep_days: int = 7
    differential_keep_days: int = 30
    full_keep_count: int = 12

    # Safety
    require_verified: bool = True  # Only count verified backups toward retention
    grace_period_days: int = 7  # Don't delete backups newer than this


@dataclass
class RetentionResult:
    """Result of retention policy application"""
    backups_evaluated: int = 0
    backups_deleted: int = 0
    backups_kept: int = 0
    bytes_freed: int = 0
    deleted_backup_ids: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class StorageConfig:
    """Storage backend configuration"""
    backend: StorageBackend

    # Common settings
    enabled: bool = True
    read_only: bool = False

    # Local storage
    local_path: Optional[Path] = None

    # S3 settings
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_endpoint: Optional[str] = None  # For S3-compatible storage

    # GCS settings
    gcs_bucket: Optional[str] = None
    gcs_project: Optional[str] = None
    gcs_credentials_path: Optional[Path] = None

    # Azure settings
    azure_container: Optional[str] = None
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_connection_string: Optional[str] = None

    # Multi-destination (for MULTI backend)
    destinations: List['StorageConfig'] = field(default_factory=list)
    require_all_success: bool = True  # Require all destinations to succeed

    # Performance
    upload_part_size_mb: int = 5
    max_concurrent_uploads: int = 4
    retry_attempts: int = 3
    retry_delay_seconds: int = 5


@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    enabled: bool = True
    algorithm: str = "AES-256-GCM"

    # Key management
    key_id: Optional[str] = None
    key_rotation_days: int = 90

    # KMS integration
    use_kms: bool = False
    kms_provider: Optional[str] = None  # "aws", "gcp", "azure"
    kms_key_id: Optional[str] = None
    kms_region: Optional[str] = None


@dataclass
class BackupSchedule:
    """Backup schedule configuration"""
    enabled: bool = True

    # Cron-style schedules
    full_cron: str = "0 1 * * 0"  # Weekly Sunday 1 AM
    differential_cron: str = "0 2 * * *"  # Daily 2 AM
    incremental_cron: str = "*/5 * * * *"  # Every 5 minutes

    # Continuous backup settings
    continuous_enabled: bool = True
    continuous_batch_size: int = 100
    continuous_batch_interval_seconds: int = 60

    # Verification schedule
    verify_after_backup: bool = True
    weekly_restore_test_cron: str = "0 3 * * 6"  # Saturday 3 AM

    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_channels: List[str] = field(default_factory=list)


@dataclass
class BackupHealth:
    """Backup system health status"""
    healthy: bool
    last_backup_time: Optional[datetime] = None
    last_successful_backup: Optional[str] = None
    last_failed_backup: Optional[str] = None

    # Metrics
    total_backups: int = 0
    failed_backups_24h: int = 0
    average_backup_duration_seconds: float = 0.0
    total_storage_used_bytes: int = 0

    # SLA compliance
    rpo_compliant: bool = True  # Recovery Point Objective met
    rto_compliant: bool = True  # Recovery Time Objective met

    # Issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class BackupConfig:
    """Central backup system configuration"""

    # Storage
    primary_storage: StorageConfig
    secondary_storage: Optional[StorageConfig] = None

    # Encryption
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)

    # Compression
    compression_enabled: bool = True
    compression_algorithm: CompressionAlgorithm = CompressionAlgorithm.ZSTD
    compression_level: int = 3  # Balance between speed and ratio

    # Retention
    retention_policy: RetentionPolicy = field(default_factory=RetentionPolicy)

    # Schedule
    schedule: BackupSchedule = field(default_factory=BackupSchedule)

    # Verification
    verify_after_backup: bool = True
    weekly_restore_test: bool = True
    checksum_algorithm: str = "sha256"

    # Performance
    max_concurrent_backups: int = 1  # Prevent concurrent backups
    backup_timeout_seconds: int = 3600  # 1 hour
    restore_timeout_seconds: int = 7200  # 2 hours

    # Database settings
    db_path: Path = Path("continuum_data/memory.db")
    temp_dir: Path = Path("continuum_data/backup_temp")

    # Metadata storage
    metadata_db_path: Path = Path("continuum_data/backups/metadata.db")

    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_channels: List[str] = field(default_factory=list)

    # SLA targets
    target_rpo_minutes: int = 5  # Recovery Point Objective
    target_rto_minutes: int = 60  # Recovery Time Objective

    # Tenant configuration
    tenant_id: str = "default"

    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.primary_storage.local_path:
            self.primary_storage.local_path.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
