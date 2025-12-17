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
Google Cloud Storage Backend

Stores backups in Google Cloud Storage.
Similar features to S3 with Google's infrastructure.
"""

import asyncio
import logging
from typing import Optional, List

from .base import StorageBackendBase
from ..types import BackupMetadata, StorageConfig

logger = logging.getLogger(__name__)


class GCSStorageBackend(StorageBackendBase):
    """
    Google Cloud Storage backend.

    Features:
    - Standard storage for active backups
    - Nearline/Coldline for archival
    - Automatic lifecycle management
    - Object versioning
    - Customer-managed encryption keys

    Requires:
    - google-cloud-storage library
    - GCP credentials configured
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not config.gcs_bucket:
            raise ValueError("gcs_bucket required for GCSStorageBackend")

        self.bucket_name = config.gcs_bucket
        self.project = config.gcs_project

        # Lazy load GCS client
        self._storage_client = None
        self._bucket = None

    def _get_client(self):
        """Lazy load GCS client"""
        if self._storage_client is None:
            try:
                from google.cloud import storage
            except ImportError:
                raise ImportError(
                    "google-cloud-storage required for GCS backend. "
                    "Install with: pip install google-cloud-storage"
                )

            if self.config.gcs_credentials_path:
                self._storage_client = storage.Client.from_service_account_json(
                    str(self.config.gcs_credentials_path)
                )
            else:
                # Use application default credentials
                self._storage_client = storage.Client(project=self.project)

            self._bucket = self._storage_client.bucket(self.bucket_name)

        return self._storage_client

    def _get_blob_name(self, backup_id: str, metadata: Optional[BackupMetadata] = None) -> str:
        """Get GCS blob name for backup"""
        if metadata:
            date_prefix = metadata.created_at.strftime("%Y/%m/%d")
            return f"{metadata.strategy.value}/{date_prefix}/{backup_id}.backup"
        else:
            return f"{backup_id}.backup"

    async def upload(
        self,
        backup_id: str,
        data: bytes,
        metadata: BackupMetadata,
    ) -> str:
        """Upload backup to GCS"""
        blob_name = self._get_blob_name(backup_id, metadata)

        logger.info(f"Uploading backup to GCS: gs://{self.bucket_name}/{blob_name}")

        def _upload():
            self._get_client()
            blob = self._bucket.blob(blob_name)

            # Set metadata
            blob.metadata = {
                'backup-id': backup_id,
                'strategy': metadata.strategy.value,
                'tenant-id': metadata.tenant_id,
                'created-at': metadata.created_at.isoformat(),
            }

            # Upload
            blob.upload_from_string(data)

        await asyncio.to_thread(_upload)

        logger.info(f"Backup uploaded to GCS: {blob_name} ({len(data)} bytes)")
        return f"gs://{self.bucket_name}/{blob_name}"

    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """Download backup from GCS"""
        blob_name = self._get_blob_name(backup_id)

        logger.info(f"Downloading backup from GCS: gs://{self.bucket_name}/{blob_name}")

        def _download():
            self._get_client()
            blob = self._bucket.blob(blob_name)
            return blob.download_as_bytes()

        data = await asyncio.to_thread(_download)

        logger.info(f"Backup downloaded from GCS: {blob_name} ({len(data)} bytes)")
        return data

    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """Delete backup from GCS"""
        blob_name = self._get_blob_name(backup_id)

        logger.info(f"Deleting backup from GCS: gs://{self.bucket_name}/{blob_name}")

        def _delete():
            self._get_client()
            blob = self._bucket.blob(blob_name)
            blob.delete()

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"Backup deleted from GCS: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from GCS: {e}")
            return False

    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """Check if backup exists in GCS"""

        def _exists():
            self._get_client()
            blob_name = self._get_blob_name(backup_id)
            blob = self._bucket.blob(blob_name)
            return blob.exists()

        return await asyncio.to_thread(_exists)

    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List all backups in GCS"""

        def _list():
            self._get_client()
            blobs = self._bucket.list_blobs(prefix=prefix)
            backups = []

            for blob in blobs:
                # Extract backup ID from blob name
                backup_id = blob.name.split('/')[-1].replace('.backup', '')
                backups.append(backup_id)

            return backups

        return await asyncio.to_thread(_list)

    async def get_size(
        self,
        backup_id: str,
    ) -> int:
        """Get backup size in GCS"""

        def _get_size():
            self._get_client()
            blob_name = self._get_blob_name(backup_id)
            blob = self._bucket.blob(blob_name)
            blob.reload()
            return blob.size

        return await asyncio.to_thread(_get_size)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
