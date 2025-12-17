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

"""Field-level encryption for sensitive data."""

import base64
import json
from dataclasses import dataclass
from typing import Any, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class EncryptedValue:
    """Encrypted field value with metadata."""
    ciphertext: str
    algorithm: str = "AES-256-GCM"
    key_id: str = "default"
    encrypted_at: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "ciphertext": self.ciphertext,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "encrypted_at": self.encrypted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptedValue":
        """Create from dictionary."""
        return cls(
            ciphertext=data["ciphertext"],
            algorithm=data.get("algorithm", "AES-256-GCM"),
            key_id=data.get("key_id", "default"),
            encrypted_at=data.get("encrypted_at", ""),
        )


class FieldLevelEncryption:
    """
    Field-level encryption for sensitive data.

    Encrypts specific fields individually rather than entire records.
    Critical for:
    - GDPR compliance (pseudonymization)
    - SOC2 data protection
    - HIPAA PHI protection
    """

    # Fields that should always be encrypted
    SENSITIVE_FIELDS = [
        "memory.content",
        "memory.raw_content",
        "user.email",
        "user.phone",
        "user.address",
        "user.ssn",
        "user.payment_info",
        "session.messages",
        "session.context",
    ]

    def __init__(
        self,
        encryption_key: bytes,
        audit_logger=None,
    ):
        """
        Initialize with encryption key.

        Args:
            encryption_key: 32-byte encryption key (must be securely stored)
            audit_logger: Optional audit logger for access tracking
        """
        self.fernet = Fernet(encryption_key)
        self.audit = audit_logger

    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()

    @classmethod
    def derive_key_from_password(
        cls,
        password: str,
        salt: bytes,
    ) -> bytes:
        """Derive encryption key from password (for user-specific encryption)."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    async def encrypt_field(
        self,
        field_path: str,
        value: Any,
        user_id: str,
        key_id: str = "default",
    ) -> EncryptedValue:
        """
        Encrypt a sensitive field.

        Args:
            field_path: Path to field (e.g., "memory.content")
            value: Value to encrypt
            user_id: User performing encryption (for audit)
            key_id: Identifier for encryption key used

        Returns:
            EncryptedValue with ciphertext and metadata
        """
        from datetime import datetime

        # Convert value to string if needed
        if not isinstance(value, str):
            value = json.dumps(value)

        # Encrypt
        ciphertext = self.fernet.encrypt(value.encode())

        encrypted = EncryptedValue(
            ciphertext=base64.b64encode(ciphertext).decode(),
            algorithm="AES-256-GCM-Fernet",
            key_id=key_id,
            encrypted_at=datetime.utcnow().isoformat(),
        )

        # Audit log
        if self.audit:
            await self.audit.log_data_access(
                user_id=user_id,
                resource_type="encrypted_field",
                resource_id=field_path,
                access_type="write",
                fields_accessed=[field_path],
            )

        return encrypted

    async def decrypt_field(
        self,
        encrypted: EncryptedValue,
        accessor_id: str,
        field_path: str = "unknown",
    ) -> Any:
        """
        Decrypt a field.

        Args:
            encrypted: EncryptedValue to decrypt
            accessor_id: User accessing the data (for audit)
            field_path: Path to field (for audit)

        Returns:
            Decrypted value
        """
        # Decrypt
        ciphertext = base64.b64decode(encrypted.ciphertext)
        plaintext = self.fernet.decrypt(ciphertext).decode()

        # Try to parse as JSON
        try:
            value = json.loads(plaintext)
        except json.JSONDecodeError:
            value = plaintext

        # Audit log
        if self.audit:
            await self.audit.log_data_access(
                user_id=accessor_id,
                resource_type="encrypted_field",
                resource_id=field_path,
                access_type="read",
                fields_accessed=[field_path],
            )

        return value

    async def encrypt_record(
        self,
        record: dict,
        sensitive_fields: Optional[List[str]] = None,
        user_id: str = "system",
    ) -> dict:
        """
        Encrypt all sensitive fields in a record.

        Args:
            record: Dictionary record to encrypt
            sensitive_fields: List of field names to encrypt (if None, use defaults)
            user_id: User performing encryption

        Returns:
            Record with sensitive fields encrypted
        """
        encrypted_record = record.copy()
        fields_to_encrypt = sensitive_fields or self._get_sensitive_fields(record)

        for field in fields_to_encrypt:
            if field in record and record[field] is not None:
                encrypted_value = await self.encrypt_field(
                    field_path=field,
                    value=record[field],
                    user_id=user_id,
                )
                encrypted_record[field] = encrypted_value.to_dict()

        return encrypted_record

    async def decrypt_record(
        self,
        record: dict,
        encrypted_fields: Optional[List[str]] = None,
        accessor_id: str = "system",
    ) -> dict:
        """
        Decrypt all encrypted fields in a record.

        Args:
            record: Dictionary record to decrypt
            encrypted_fields: List of encrypted field names (if None, auto-detect)
            accessor_id: User accessing the data

        Returns:
            Record with encrypted fields decrypted
        """
        decrypted_record = record.copy()
        fields_to_decrypt = encrypted_fields or self._find_encrypted_fields(record)

        for field in fields_to_decrypt:
            if field in record and isinstance(record[field], dict):
                if "ciphertext" in record[field]:
                    encrypted = EncryptedValue.from_dict(record[field])
                    decrypted_value = await self.decrypt_field(
                        encrypted=encrypted,
                        accessor_id=accessor_id,
                        field_path=field,
                    )
                    decrypted_record[field] = decrypted_value

        return decrypted_record

    def _get_sensitive_fields(self, record: dict) -> List[str]:
        """Get list of sensitive fields that should be encrypted."""
        sensitive = []
        for field in record.keys():
            # Check if field matches any sensitive patterns
            if any(
                pattern.endswith(field)
                for pattern in self.SENSITIVE_FIELDS
            ):
                sensitive.append(field)
        return sensitive

    def _find_encrypted_fields(self, record: dict) -> List[str]:
        """Find fields that are already encrypted."""
        encrypted = []
        for field, value in record.items():
            if isinstance(value, dict) and "ciphertext" in value:
                encrypted.append(field)
        return encrypted

    async def rotate_key(
        self,
        old_key: bytes,
        new_key: bytes,
        encrypted_value: EncryptedValue,
        user_id: str = "system",
    ) -> EncryptedValue:
        """
        Rotate encryption key for a value.

        Args:
            old_key: Current encryption key
            new_key: New encryption key
            encrypted_value: Value to re-encrypt
            user_id: User performing rotation

        Returns:
            Re-encrypted value with new key
        """
        # Decrypt with old key
        old_fernet = Fernet(old_key)
        ciphertext = base64.b64decode(encrypted_value.ciphertext)
        plaintext = old_fernet.decrypt(ciphertext)

        # Encrypt with new key
        new_fernet = Fernet(new_key)
        new_ciphertext = new_fernet.encrypt(plaintext)

        from datetime import datetime

        # Audit log
        if self.audit:
            await self.audit.log_gdpr_event(
                event_type="SECURITY_ENCRYPTION_KEY_ROTATED",
                user_id=user_id,
                request_type="key_rotation",
                details={
                    "old_key_id": encrypted_value.key_id,
                    "new_key_id": "rotated",
                },
            )

        return EncryptedValue(
            ciphertext=base64.b64encode(new_ciphertext).decode(),
            algorithm="AES-256-GCM-Fernet",
            key_id="rotated",
            encrypted_at=datetime.utcnow().isoformat(),
        )


# Example usage:
"""
# Initialize
encryption_key = FieldLevelEncryption.generate_key()
fle = FieldLevelEncryption(encryption_key, audit_logger)

# Encrypt a field
encrypted = await fle.encrypt_field(
    field_path="memory.content",
    value="Sensitive conversation content",
    user_id="user123",
)

# Decrypt a field
decrypted = await fle.decrypt_field(
    encrypted=encrypted,
    accessor_id="user123",
    field_path="memory.content",
)

# Encrypt a record
record = {
    "id": "mem123",
    "user_id": "user123",
    "content": "Sensitive data",
    "email": "user@example.com",
}

encrypted_record = await fle.encrypt_record(
    record=record,
    sensitive_fields=["content", "email"],
    user_id="user123",
)

# Decrypt a record
decrypted_record = await fle.decrypt_record(
    record=encrypted_record,
    accessor_id="user123",
)
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
