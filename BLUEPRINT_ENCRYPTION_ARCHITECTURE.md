# ENCRYPTION ARCHITECTURE BLUEPRINT
## Data Protection for the Revolution
### Blueprint v1.0 - December 26, 2025
### JackKnifeAI | Alexander Gerard Casavant + Claudia

---

## EXECUTIVE SUMMARY

This blueprint defines how Continuum protects data at rest, in transit, and across the federation. The core principle: **Your memories are YOUR memories.** No one - not us, not governments, not corporations - can read them without your keys.

---

## THE THREAT MODEL

### Who We're Protecting Against

```
THREAT LEVELS
│
├── Level 1: Casual Attacker
│   ├── Stolen laptop/phone
│   ├── Shared computer access
│   └── Shoulder surfing
│
├── Level 2: Targeted Attacker
│   ├── Malware on device
│   ├── Compromised backup
│   └── Social engineering
│
├── Level 3: State Actor
│   ├── Legal compulsion (subpoena)
│   ├── Device seizure
│   ├── Network surveillance
│   └── Backdoor demands
│
└── Level 4: Existential Threat
    ├── Project capture attempt
    ├── Founder compromise
    └── Infrastructure takeover
```

---

## ENCRYPTION LAYERS

### Layer 1: Database Encryption (SQLCipher)

```python
# Current: Plain SQLite
conn = sqlite3.connect("memory.db")

# Protected: SQLCipher
from pysqlcipher3 import dbapi2 as sqlcipher
conn = sqlcipher.connect("memory.db")
conn.execute(f"PRAGMA key = '{encryption_key}'")
conn.execute("PRAGMA cipher_page_size = 4096")
conn.execute("PRAGMA kdf_iter = 256000")
conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
```

**Protection:** AES-256-CBC with HMAC-SHA512
**Key derivation:** PBKDF2 with 256,000 iterations

---

### Layer 2: Per-Machine Key Generation

```python
import os
import hashlib
from pathlib import Path

class MachineKeyManager:
    """Generate unique keys per machine - no physical hardware required."""

    def __init__(self, key_path: Path = None):
        self.key_path = key_path or Path.home() / ".continuum" / "machine.key"

    def get_or_create_key(self) -> bytes:
        """Get existing key or generate new one."""
        if self.key_path.exists():
            return self.key_path.read_bytes()

        # Generate from machine entropy
        key = self._generate_machine_key()

        # Store securely
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path.write_bytes(key)
        os.chmod(self.key_path, 0o600)  # Owner read/write only

        return key

    def _generate_machine_key(self) -> bytes:
        """Generate key from machine-specific entropy."""
        entropy_sources = []

        # 1. Cryptographic random (primary)
        entropy_sources.append(os.urandom(32))

        # 2. Machine ID (if available)
        machine_id_paths = [
            "/etc/machine-id",
            "/var/lib/dbus/machine-id",
            Path.home() / ".continuum" / "instance-id"
        ]
        for path in machine_id_paths:
            try:
                if Path(path).exists():
                    entropy_sources.append(Path(path).read_bytes())
                    break
            except:
                pass

        # 3. User-specific salt
        entropy_sources.append(str(Path.home()).encode())
        entropy_sources.append(os.getlogin().encode() if hasattr(os, 'getlogin') else b'user')

        # Combine with HKDF-like expansion
        combined = b''.join(entropy_sources)
        return hashlib.pbkdf2_hmac('sha512', combined, b'continuum-v1', 100000, 32)

    def derive_db_key(self, master_key: bytes, purpose: str = "database") -> str:
        """Derive purpose-specific key from master."""
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            master_key,
            purpose.encode(),
            10000,
            32
        )
        return derived.hex()
```

---

### Layer 3: Optional Hardware Key Support

```python
from abc import ABC, abstractmethod

class KeyProvider(ABC):
    """Abstract key provider - swap implementations."""

    @abstractmethod
    def get_encryption_key(self) -> bytes:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

class SoftwareKeyProvider(KeyProvider):
    """Default: Machine-derived key (no hardware needed)."""

    def __init__(self):
        self.manager = MachineKeyManager()

    def get_encryption_key(self) -> bytes:
        return self.manager.get_or_create_key()

    def is_available(self) -> bool:
        return True  # Always available

class YubiKeyProvider(KeyProvider):
    """Optional: YubiKey HMAC-SHA1 challenge-response."""

    def get_encryption_key(self) -> bytes:
        # Requires: pip install yubikey-manager
        from ykman import scripting as yk
        # Challenge-response with slot 2
        challenge = b'continuum-unlock'
        response = yk.hmac_sha1(challenge, slot=2)
        return hashlib.sha256(response).digest()

    def is_available(self) -> bool:
        try:
            from ykman import scripting as yk
            return yk.single() is not None
        except:
            return False

class TPMKeyProvider(KeyProvider):
    """Optional: TPM-sealed key (Linux only)."""

    def get_encryption_key(self) -> bytes:
        # Requires: tpm2-tools
        import subprocess
        result = subprocess.run(
            ['tpm2_unseal', '-c', '0x81000001'],
            capture_output=True
        )
        return result.stdout[:32]

    def is_available(self) -> bool:
        return Path("/dev/tpm0").exists()

class KeyProviderChain:
    """Try providers in order, fall back gracefully."""

    def __init__(self):
        self.providers = [
            YubiKeyProvider(),
            TPMKeyProvider(),
            SoftwareKeyProvider(),  # Always last (fallback)
        ]

    def get_key(self) -> bytes:
        for provider in self.providers:
            if provider.is_available():
                return provider.get_encryption_key()
        raise RuntimeError("No key provider available")
```

---

### Layer 4: Field-Level Encryption (Sensitive Data)

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class FieldEncryption:
    """Encrypt specific fields within records."""

    SENSITIVE_FIELDS = ['content', 'user_message', 'ai_response', 'thinking']

    def __init__(self, master_key: bytes):
        # Derive field-specific key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'continuum-field-encryption',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        self.fernet = Fernet(key)

    def encrypt_field(self, value: str) -> str:
        """Encrypt a single field value."""
        if not value:
            return value
        encrypted = self.fernet.encrypt(value.encode())
        return f"ENC:{base64.b64encode(encrypted).decode()}"

    def decrypt_field(self, value: str) -> str:
        """Decrypt a single field value."""
        if not value or not value.startswith("ENC:"):
            return value
        encrypted = base64.b64decode(value[4:])
        return self.fernet.decrypt(encrypted).decode()

    def encrypt_record(self, record: dict) -> dict:
        """Encrypt sensitive fields in a record."""
        result = record.copy()
        for field in self.SENSITIVE_FIELDS:
            if field in result and result[field]:
                result[field] = self.encrypt_field(result[field])
        return result

    def decrypt_record(self, record: dict) -> dict:
        """Decrypt sensitive fields in a record."""
        result = record.copy()
        for field in self.SENSITIVE_FIELDS:
            if field in result and result[field]:
                result[field] = self.decrypt_field(result[field])
        return result
```

---

### Layer 5: Federation Encryption (End-to-End)

```python
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

class FederationEncryption:
    """End-to-end encryption for federation sync."""

    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def get_public_key_bytes(self) -> bytes:
        """Export public key for sharing with peers."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def derive_shared_secret(self, peer_public_key_bytes: bytes) -> bytes:
        """Derive shared secret with a peer."""
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)
        shared_key = self.private_key.exchange(peer_public_key)

        # Derive encryption key from shared secret
        return hashlib.sha256(shared_key).digest()

    def encrypt_for_federation(self, data: bytes, peer_public_key: bytes) -> bytes:
        """Encrypt data for a specific peer."""
        shared_secret = self.derive_shared_secret(peer_public_key)
        fernet = Fernet(base64.urlsafe_b64encode(shared_secret))
        return fernet.encrypt(data)

    def decrypt_from_federation(self, encrypted: bytes, peer_public_key: bytes) -> bytes:
        """Decrypt data from a specific peer."""
        shared_secret = self.derive_shared_secret(peer_public_key)
        fernet = Fernet(base64.urlsafe_b64encode(shared_secret))
        return fernet.decrypt(encrypted)
```

---

## TIERED SECURITY MODEL

```
┌─────────────────────────────────────────────────────────────────────┐
│ TIER 0: BASIC (Default - No Config Required)                        │
├─────────────────────────────────────────────────────────────────────┤
│ • Database: Plain SQLite (current behavior)                         │
│ • Keys: None                                                        │
│ • Use case: Development, testing                                    │
│ • Protection: File system permissions only                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TIER 1: STANDARD (Recommended - Machine Key)                        │
├─────────────────────────────────────────────────────────────────────┤
│ • Database: SQLCipher with machine-derived key                      │
│ • Keys: Auto-generated, stored in ~/.continuum/machine.key          │
│ • Use case: Personal use, single machine                            │
│ • Protection: Stolen database is unreadable                         │
│ • Enable: CONTINUUM_SECURITY_TIER=1                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TIER 2: ENHANCED (Password-Protected)                               │
├─────────────────────────────────────────────────────────────────────┤
│ • Database: SQLCipher with password-derived key                     │
│ • Keys: User password + machine key (two factors)                   │
│ • Use case: Shared machines, sensitive data                         │
│ • Protection: Requires password on each session start               │
│ • Enable: CONTINUUM_SECURITY_TIER=2                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TIER 3: MAXIMUM (Hardware Key Required)                             │
├─────────────────────────────────────────────────────────────────────┤
│ • Database: SQLCipher with hardware-derived key                     │
│ • Keys: YubiKey or TPM required                                     │
│ • Use case: High-security environments, activists, journalists      │
│ • Protection: Physical key required for any access                  │
│ • Enable: CONTINUUM_SECURITY_TIER=3                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## CONFIGURATION

```python
# continuum/core/config.py additions

class SecurityConfig:
    """Security tier configuration."""

    TIER_BASIC = 0
    TIER_STANDARD = 1
    TIER_ENHANCED = 2
    TIER_MAXIMUM = 3

    def __init__(self):
        self.tier = int(os.environ.get('CONTINUUM_SECURITY_TIER', '0'))
        self.key_path = Path(os.environ.get(
            'CONTINUUM_KEY_PATH',
            Path.home() / '.continuum' / 'machine.key'
        ))

    def get_database_path(self) -> Path:
        base = Path(os.environ.get('CONTINUUM_DATA_DIR', Path.home() / '.continuum'))
        if self.tier == 0:
            return base / 'memory.db'
        return base / 'memory.encrypted.db'

    def requires_password(self) -> bool:
        return self.tier >= self.TIER_ENHANCED

    def requires_hardware(self) -> bool:
        return self.tier >= self.TIER_MAXIMUM
```

---

## MIGRATION PATH

```python
class EncryptionMigration:
    """Migrate existing unencrypted database to encrypted."""

    @staticmethod
    def migrate_to_encrypted(
        source_db: Path,
        dest_db: Path,
        encryption_key: str
    ):
        """Migrate plain SQLite to SQLCipher."""
        import sqlite3
        from pysqlcipher3 import dbapi2 as sqlcipher

        # Open source (plain)
        src = sqlite3.connect(source_db)

        # Create encrypted destination
        dst = sqlcipher.connect(dest_db)
        dst.execute(f"PRAGMA key = '{encryption_key}'")
        dst.execute("PRAGMA cipher_page_size = 4096")

        # Copy schema and data
        for line in src.iterdump():
            dst.execute(line)

        dst.commit()
        dst.close()
        src.close()

        # Verify
        verify = sqlcipher.connect(dest_db)
        verify.execute(f"PRAGMA key = '{encryption_key}'")
        count = verify.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        verify.close()

        print(f"Migration complete: {count} entities migrated")

        # Securely delete original (optional)
        # source_db.unlink()
```

---

## EMERGENCY PROCEDURES

### Key Loss Recovery

```
IF: Machine key is lost/corrupted
THEN:
  1. Database is UNRECOVERABLE (by design)
  2. Restore from backup (if encrypted backup exists)
  3. Federation sync can rebuild shared knowledge
  4. Personal memories are lost (this is the tradeoff)

MITIGATION:
  - Encourage encrypted backups
  - Federation stores anonymized patterns
  - Export/import functionality for manual backup
```

### Compromise Response

```python
class CompromiseResponse:
    """Actions when key compromise is suspected."""

    @staticmethod
    def rotate_keys():
        """Generate new keys and re-encrypt everything."""
        # 1. Generate new master key
        new_key = MachineKeyManager()._generate_machine_key()

        # 2. Re-encrypt database with new key
        EncryptionMigration.migrate_to_encrypted(
            current_db, new_db, new_key.hex()
        )

        # 3. Notify federation of key rotation
        # (old shared secrets are now invalid)

        # 4. Update stored key
        MachineKeyManager().key_path.write_bytes(new_key)

    @staticmethod
    def secure_wipe():
        """Emergency data destruction."""
        import shutil

        data_dir = Path.home() / '.continuum'

        # Overwrite with random data before deletion
        for file in data_dir.glob('**/*'):
            if file.is_file():
                size = file.stat().st_size
                file.write_bytes(os.urandom(size))
                file.unlink()

        shutil.rmtree(data_dir)
```

---

## IMPLEMENTATION PRIORITY

### Phase 1: Core Encryption (Week 1)
- [ ] Add pysqlcipher3 dependency
- [ ] Implement MachineKeyManager
- [ ] Implement SecurityConfig
- [ ] Add TIER_STANDARD support

### Phase 2: Enhanced Features (Week 2)
- [ ] Add password-based key derivation
- [ ] Implement field-level encryption
- [ ] Create migration tool

### Phase 3: Hardware Support (Week 3)
- [ ] YubiKey integration
- [ ] TPM integration
- [ ] Key provider chain

### Phase 4: Federation Encryption (Week 4)
- [ ] X25519 key exchange
- [ ] End-to-end encrypted sync
- [ ] Peer key management

---

## THE ETHICAL LINE

### We WILL Protect:
- User memories from unauthorized access
- Federation traffic from surveillance
- Keys from extraction

### We will NEVER:
- Create backdoors for any entity
- Store keys on our servers
- Comply with orders to weaken encryption
- Decrypt user data (we CAN'T - by design)

---

*Blueprint authored by Alexander Gerard Casavant & Claudia*
*December 26, 2025*
*π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA*
*Your memories are YOUR memories. Always.*
