#!/usr/bin/env python3
"""
Base Backup Strategy

Abstract base class for all backup strategies.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List


class BackupStrategyBase(ABC):
    """Base class for backup strategies"""

    @abstractmethod
    async def execute(
        self,
        db_path: Path,
        tables: Optional[List[str]] = None,
        temp_dir: Optional[Path] = None,
    ) -> bytes:
        """
        Execute backup strategy.

        Args:
            db_path: Path to database file
            tables: Optional list of tables to backup
            temp_dir: Temporary directory for staging

        Returns:
            Backup data as bytes
        """
        pass

    @abstractmethod
    def get_base_backup_id(self) -> Optional[str]:
        """
        Get base backup ID for incremental/differential backups.

        Returns:
            Base backup ID or None for full backups
        """
        pass

    @abstractmethod
    def supports_pitr(self) -> bool:
        """
        Check if strategy supports point-in-time recovery.

        Returns:
            True if PITR is supported
        """
        pass
