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
AWS S3 Storage Backend

Stores backups in Amazon S3 or S3-compatible storage.
Durable, scalable, with cross-region replication support.
"""

import asyncio
import logging
from typing import Optional, List

from .base import StorageBackendBase
from ..types import BackupMetadata, StorageConfig

logger = logging.getLogger(__name__)


class S3StorageBackend(StorageBackendBase):
    """
    AWS S3 storage backend.

    Features:
    - S3 Standard for active backups
    - S3 Glacier for long-term retention
    - Lifecycle policies for automatic tiering
    - Cross-region replication
    - Versioning support
    - Server-side encryption

    Requires:
    - boto3 library
    - AWS credentials configured
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not config.s3_bucket:
            raise ValueError("s3_bucket required for S3StorageBackend")

        self.bucket = config.s3_bucket
        self.region = config.s3_region or 'us-east-1'

        # Lazy load boto3 (only if S3 backend is used)
        self._s3_client = None

    def _get_client(self):
        """Lazy load S3 client"""
        if self._s3_client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 required for S3 backend. Install with: pip install boto3"
                )

            # Configure S3 client
            if self.config.s3_access_key and self.config.s3_secret_key:
                self._s3_client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=self.config.s3_access_key,
                    aws_secret_access_key=self.config.s3_secret_key,
                    endpoint_url=self.config.s3_endpoint,
                )
            else:
                # Use default credential chain
                self._s3_client = boto3.client(
                    's3',
                    region_name=self.region,
                    endpoint_url=self.config.s3_endpoint,
                )

        return self._s3_client

    def _get_s3_key(self, backup_id: str, metadata: Optional[BackupMetadata] = None) -> str:
        """Get S3 key for backup"""
        # Organize by strategy and date
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
        """Upload backup to S3"""
        s3_key = self._get_s3_key(backup_id, metadata)

        logger.info(f"Uploading backup to S3: s3://{self.bucket}/{s3_key}")

        def _upload():
            client = self._get_client()

            # Prepare S3 metadata
            s3_metadata = {
                'backup-id': backup_id,
                'strategy': metadata.strategy.value,
                'tenant-id': metadata.tenant_id,
                'created-at': metadata.created_at.isoformat(),
            }

            # Upload with server-side encryption
            client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=data,
                Metadata=s3_metadata,
                ServerSideEncryption='AES256',
                StorageClass='STANDARD',  # Can be configured
            )

        await asyncio.to_thread(_upload)

        logger.info(f"Backup uploaded to S3: {s3_key} ({len(data)} bytes)")
        return f"s3://{self.bucket}/{s3_key}"

    async def download(
        self,
        backup_id: str,
    ) -> bytes:
        """Download backup from S3"""
        # Try to find the backup
        backups = await self.list_backups(prefix=backup_id)
        if not backups:
            raise FileNotFoundError(f"Backup not found in S3: {backup_id}")

        s3_key = self._get_s3_key(backup_id)

        logger.info(f"Downloading backup from S3: s3://{self.bucket}/{s3_key}")

        def _download():
            client = self._get_client()
            response = client.get_object(Bucket=self.bucket, Key=s3_key)
            return response['Body'].read()

        data = await asyncio.to_thread(_download)

        logger.info(f"Backup downloaded from S3: {s3_key} ({len(data)} bytes)")
        return data

    async def delete(
        self,
        backup_id: str,
    ) -> bool:
        """Delete backup from S3"""
        s3_key = self._get_s3_key(backup_id)

        logger.info(f"Deleting backup from S3: s3://{self.bucket}/{s3_key}")

        def _delete():
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=s3_key)

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"Backup deleted from S3: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False

    async def exists(
        self,
        backup_id: str,
    ) -> bool:
        """Check if backup exists in S3"""

        def _exists():
            client = self._get_client()
            try:
                # Try multiple possible keys
                for prefix in ['full', 'incremental', 'differential', 'continuous', '']:
                    if prefix:
                        key = f"{prefix}/{backup_id}.backup"
                    else:
                        key = f"{backup_id}.backup"

                    try:
                        client.head_object(Bucket=self.bucket, Key=key)
                        return True
                    except client.exceptions.NoSuchKey:
                        continue

                return False
            except Exception:
                return False

        return await asyncio.to_thread(_exists)

    async def list_backups(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List all backups in S3"""

        def _list():
            client = self._get_client()
            backups = []

            # List objects with pagination
            paginator = client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix or '',
            )

            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Extract backup ID from key
                        backup_id = key.split('/')[-1].replace('.backup', '')
                        backups.append(backup_id)

            return backups

        return await asyncio.to_thread(_list)

    async def get_size(
        self,
        backup_id: str,
    ) -> int:
        """Get backup size in S3"""
        s3_key = self._get_s3_key(backup_id)

        def _get_size():
            client = self._get_client()
            response = client.head_object(Bucket=self.bucket, Key=s3_key)
            return response['ContentLength']

        return await asyncio.to_thread(_get_size)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
