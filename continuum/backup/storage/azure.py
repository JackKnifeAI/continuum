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
Azure Blob Storage Backend

Stores backups in Microsoft Azure Blob Storage.
Enterprise-grade cloud storage for Azure environments.
"""

import asyncio
import logging
from typing import Optional, List

from .base import StorageBackendBase
from ..types import BackupMetadata, StorageConfig

logger = logging.getLogger(__name__)


class AzureStorageBackend(StorageBackendBase):
    """
    Azure Blob Storage backend.

    Features:
    - Hot/Cool/Archive tiers
    - Lifecycle management
    - Blob versioning
    - Soft delete protection

    Requires:
    - azure-storage-blob library
    - Azure credentials configured
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not config.azure_container:
            raise ValueError("azure_container required for AzureStorageBackend")

        self.container_name = config.azure_container
        self.account_name = config.azure_account_name

        # Lazy load Azure client
        self._blob_service_client = None
        self._container_client = None

    def _get_client(self):
        """Lazy load Azure Blob client"""
        if self._blob_service_client is None:
            try:
                from azure.storage.blob import BlobServiceClient
            except ImportError:
                raise ImportError(
                    "azure-storage-blob required for Azure backend. "
                    "Install with: pip install azure-storage-blob"
                )

            if self.config.azure_connection_string:
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    self.config.azure_connection_string
                )
            elif self.config.azure_account_key:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self._blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.config.azure_account_key,
                )
            else:
                raise ValueError("Azure credentials not configured")

            self._container_client = self._blob_service_client.get_container_client(
                self.container_name
            )

        return self._blob_service_client

    def _get_blob_name(self, backup_id: str, metadata: Optional[BackupMetadata] = None) -> str:
        """Get Azure blob name for backup"""
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
        """Upload backup to Azure Blob Storage"""
        blob_name = self._get_blob_name(backup_id, metadata)

        logger.info(f"Uploading backup to Azure: {self.container_name}/{blob_name}")

        def _upload():
            self._get_client()
            blob_client = self._container_client.get_blob_client(blob_name)

            # Set metadata
            blob_metadata = {
                'backup_id': backup_id,
                'strategy': metadata.strategy.value,
                'tenant_id': metadata.tenant_id,
                'created_at': metadata.created_at.isoformat(),
            }

            # Upload
            blob_client.upload_blob(
                data,
                metadata=blob_metadata,
                overwrite=True,
            )

        await asyncio.to_thread(_upload)

        logger.info(f"Backup uploaded to Azure: {blob_name} ({len(data)} bytes)")
        return f"azure://{self.account_name}/{self.container_name}/{blob_name}"

    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """Download backup from Azure Blob Storage"""
        blob_name = self._get_blob_name(backup_id)

        logger.info(f"Downloading backup from Azure: {self.container_name}/{blob_name}")

        def _download():
            self._get_client()
            blob_client = self._container_client.get_blob_client(blob_name)
            return blob_client.download_blob().readall()

        data = await asyncio.to_thread(_download)

        logger.info(f"Backup downloaded from Azure: {blob_name} ({len(data)} bytes)")
        return data

    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """Delete backup from Azure Blob Storage"""
        blob_name = self._get_blob_name(backup_id)

        logger.info(f"Deleting backup from Azure: {self.container_name}/{blob_name}")

        def _delete():
            self._get_client()
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.delete_blob()

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"Backup deleted from Azure: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Azure: {e}")
            return False

    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """Check if backup exists in Azure Blob Storage"""

        def _exists():
            self._get_client()
            blob_name = self._get_blob_name(backup_id)
            blob_client = self._container_client.get_blob_client(blob_name)
            return blob_client.exists()

        return await asyncio.to_thread(_exists)

    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List all backups in Azure Blob Storage"""

        def _list():
            self._get_client()
            blobs = self._container_client.list_blobs(name_starts_with=prefix)
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
        """Get backup size in Azure Blob Storage"""

        def _get_size():
            self._get_client()
            blob_name = self._get_blob_name(backup_id)
            blob_client = self._container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            return properties.size

        return await asyncio.to_thread(_get_size)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
