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
Webhook Database Migrations
============================

SQL migrations for webhook tables.

Tables:
    - webhooks: Webhook configurations
    - webhook_deliveries: Delivery history and status

Usage:
    from continuum.webhooks.migrations import run_migrations
    run_migrations(storage_backend)
"""

import logging
from typing import List
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


MIGRATIONS = [
    {
        "version": 1,
        "description": "Create webhooks table",
        "sql": """
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                secret TEXT NOT NULL,
                events TEXT NOT NULL,  -- Comma-separated event types
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                failure_count INTEGER DEFAULT 0,
                last_triggered_at TEXT,
                last_success_at TEXT,
                last_failure_at TEXT,
                metadata TEXT,  -- JSON metadata
                UNIQUE(user_id, url)
            );

            CREATE INDEX IF NOT EXISTS idx_webhooks_user_id ON webhooks(user_id);
            CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks(active);
            CREATE INDEX IF NOT EXISTS idx_webhooks_user_active ON webhooks(user_id, active);
        """
    },
    {
        "version": 2,
        "description": "Create webhook_deliveries table",
        "sql": """
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id TEXT PRIMARY KEY,
                webhook_id TEXT NOT NULL,
                event TEXT NOT NULL,
                payload TEXT NOT NULL,  -- JSON payload
                status TEXT NOT NULL,  -- pending, success, failed, dead_letter
                attempts INTEGER DEFAULT 0,
                next_retry_at TEXT,
                response_code INTEGER,
                response_body TEXT,
                duration_ms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_deliveries_webhook_id ON webhook_deliveries(webhook_id);
            CREATE INDEX IF NOT EXISTS idx_deliveries_status ON webhook_deliveries(status);
            CREATE INDEX IF NOT EXISTS idx_deliveries_created_at ON webhook_deliveries(created_at);
            CREATE INDEX IF NOT EXISTS idx_deliveries_next_retry ON webhook_deliveries(next_retry_at)
                WHERE status = 'pending' AND next_retry_at IS NOT NULL;
        """
    },
    {
        "version": 3,
        "description": "Create migration tracking table",
        "sql": """
            CREATE TABLE IF NOT EXISTS webhook_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
        """
    }
]


def get_current_version(storage: StorageBackend) -> int:
    """
    Get current migration version.

    Args:
        storage: Storage backend

    Returns:
        Current version number (0 if no migrations)
    """
    try:
        with storage.cursor() as cursor:
            cursor.execute("""
                SELECT MAX(version) FROM webhook_migrations
            """)
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
    except Exception:
        # Table doesn't exist yet
        return 0


def run_migrations(storage: StorageBackend, target_version: int = None):
    """
    Run database migrations.

    Args:
        storage: Storage backend
        target_version: Target version (None = latest)

    Example:
        from continuum.webhooks.migrations import run_migrations
        from continuum.storage.sqlite_backend import SQLiteBackend

        storage = SQLiteBackend(db_path="memory.db")
        run_migrations(storage)
    """
    current = get_current_version(storage)
    target = target_version or len(MIGRATIONS)

    if current >= target:
        logger.info(f"Webhooks database is up to date (version {current})")
        return

    logger.info(f"Running webhook migrations from version {current} to {target}")

    for migration in MIGRATIONS:
        version = migration["version"]

        if version <= current:
            continue

        if version > target:
            break

        logger.info(f"Applying migration {version}: {migration['description']}")

        try:
            # Execute migration SQL
            with storage.connection() as conn:
                cursor = conn.cursor()

                # Split and execute each statement
                for statement in migration["sql"].split(";"):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)

                # Record migration
                cursor.execute("""
                    INSERT OR IGNORE INTO webhook_migrations (version, description, applied_at)
                    VALUES (?, ?, datetime('now'))
                """, (version, migration["description"]))

                conn.commit()

            logger.info(f"Migration {version} applied successfully")

        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            raise

    logger.info(f"Webhook migrations complete (now at version {target})")


def rollback_migration(storage: StorageBackend, target_version: int):
    """
    Rollback to a specific version.

    WARNING: This will DROP tables! Use with extreme caution.

    Args:
        storage: Storage backend
        target_version: Version to rollback to
    """
    current = get_current_version(storage)

    if target_version >= current:
        logger.warning(f"Target version {target_version} >= current {current}, nothing to rollback")
        return

    logger.warning(f"Rolling back webhooks from version {current} to {target_version}")

    # Simplified rollback - just drop tables
    with storage.connection() as conn:
        cursor = conn.cursor()

        if target_version < 2:
            cursor.execute("DROP TABLE IF EXISTS webhook_deliveries")
            logger.info("Dropped webhook_deliveries table")

        if target_version < 1:
            cursor.execute("DROP TABLE IF EXISTS webhooks")
            logger.info("Dropped webhooks table")

        # Update migration version
        cursor.execute("""
            DELETE FROM webhook_migrations WHERE version > ?
        """, (target_version,))

        conn.commit()

    logger.warning(f"Rollback complete (now at version {target_version})")


def get_migration_status(storage: StorageBackend) -> List[dict]:
    """
    Get status of all migrations.

    Args:
        storage: Storage backend

    Returns:
        List of migration statuses

    Example:
        for migration in get_migration_status(storage):
            print(f"{migration['version']}: {migration['status']}")
    """
    current = get_current_version(storage)

    status = []
    for migration in MIGRATIONS:
        version = migration["version"]
        status.append({
            "version": version,
            "description": migration["description"],
            "status": "applied" if version <= current else "pending"
        })

    return status


# PostgreSQL-specific migrations (if needed)
POSTGRES_MIGRATIONS = [
    {
        "version": 1,
        "description": "Create webhooks table (PostgreSQL)",
        "sql": """
            CREATE TABLE IF NOT EXISTS webhooks (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                url TEXT NOT NULL,
                secret TEXT NOT NULL,
                events TEXT[] NOT NULL,  -- Array of event types
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                failure_count INTEGER DEFAULT 0,
                last_triggered_at TIMESTAMPTZ,
                last_success_at TIMESTAMPTZ,
                last_failure_at TIMESTAMPTZ,
                metadata JSONB,
                UNIQUE(user_id, url)
            );

            CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
            CREATE INDEX idx_webhooks_active ON webhooks(active);
            CREATE INDEX idx_webhooks_user_active ON webhooks(user_id, active);
            CREATE INDEX idx_webhooks_metadata ON webhooks USING GIN(metadata);
        """
    },
    {
        "version": 2,
        "description": "Create webhook_deliveries table (PostgreSQL)",
        "sql": """
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id UUID PRIMARY KEY,
                webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
                event TEXT NOT NULL,
                payload JSONB NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'dead_letter')),
                attempts INTEGER DEFAULT 0,
                next_retry_at TIMESTAMPTZ,
                response_code INTEGER,
                response_body TEXT,
                duration_ms INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                error_message TEXT
            );

            CREATE INDEX idx_deliveries_webhook_id ON webhook_deliveries(webhook_id);
            CREATE INDEX idx_deliveries_status ON webhook_deliveries(status);
            CREATE INDEX idx_deliveries_created_at ON webhook_deliveries(created_at DESC);
            CREATE INDEX idx_deliveries_next_retry ON webhook_deliveries(next_retry_at)
                WHERE status = 'pending' AND next_retry_at IS NOT NULL;
            CREATE INDEX idx_deliveries_payload ON webhook_deliveries USING GIN(payload);
        """
    }
]


def run_postgres_migrations(storage: StorageBackend, target_version: int = None):
    """
    Run PostgreSQL-specific migrations.

    Args:
        storage: PostgreSQL storage backend
        target_version: Target version (None = latest)
    """
    # Similar to run_migrations but uses POSTGRES_MIGRATIONS
    logger.info("Running PostgreSQL webhook migrations")
    # Implementation similar to run_migrations
    pass

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
