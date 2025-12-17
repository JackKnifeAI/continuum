"""
Federation Protocol - Message types, signing, and verification.

Defines the protocol for secure communication between federation nodes.
Includes rate limiting to prevent abuse.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import hmac
import json
from pathlib import Path


class MessageType(str, Enum):
    """Federation message types."""
    CONTRIBUTE = "CONTRIBUTE"
    REQUEST = "REQUEST"
    SYNC = "SYNC"
    HEARTBEAT = "HEARTBEAT"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"


class FederationProtocol:
    """
    Handles federation protocol operations.

    - Message signing/verification for authenticity
    - Rate limiting to prevent abuse
    - Message validation and serialization
    """

    # Rate limits per message type (messages per hour)
    RATE_LIMITS = {
        MessageType.CONTRIBUTE: 100,   # Can contribute up to 100 times/hour
        MessageType.REQUEST: 50,       # Can request up to 50 times/hour
        MessageType.SYNC: 10,          # Can sync up to 10 times/hour
        MessageType.HEARTBEAT: 60,     # Can heartbeat up to 60 times/hour (1/min)
    }

    def __init__(
        self,
        node_id: str,
        secret_key: Optional[str] = None,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize federation protocol handler.

        Args:
            node_id: This node's ID
            secret_key: Secret key for message signing (generated if not provided)
            storage_path: Where to store protocol state
        """
        self.node_id = node_id
        self.secret_key = secret_key or self._generate_secret()
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "protocol"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Rate limiting state (message_type -> list of timestamps)
        self.rate_limit_state: Dict[str, List[datetime]] = {}

    def create_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a signed federation message.

        Args:
            message_type: Type of message
            payload: Message payload
            recipient: Optional recipient node ID

        Returns:
            Signed message ready for transmission
        """
        message = {
            "type": message_type.value,
            "sender": self.node_id,
            "recipient": recipient,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }

        # Sign the message
        signature = self._sign_message(message)
        message["signature"] = signature

        return message

    def verify_message(self, message: Dict[str, Any], sender_key: Optional[str] = None) -> bool:
        """
        Verify a message signature.

        Args:
            message: The message to verify
            sender_key: Sender's secret key (if known)

        Returns:
            True if signature is valid, False otherwise
        """
        if "signature" not in message:
            return False

        # Extract signature
        signature = message.pop("signature")

        # Verify with sender's key or our own key (for loopback)
        key = sender_key or self.secret_key
        expected_signature = self._sign_message(message, key)

        # Restore signature
        message["signature"] = signature

        return hmac.compare_digest(signature, expected_signature)

    def check_rate_limit(self, message_type: MessageType) -> Dict[str, Any]:
        """
        Check if message type is within rate limits.

        Args:
            message_type: Type of message to check

        Returns:
            Rate limit status
        """
        if message_type not in self.RATE_LIMITS:
            return {"allowed": True, "reason": "no_limit"}

        # Get recent timestamps for this message type
        type_key = message_type.value
        if type_key not in self.rate_limit_state:
            self.rate_limit_state[type_key] = []

        # Remove timestamps older than 1 hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        self.rate_limit_state[type_key] = [
            ts for ts in self.rate_limit_state[type_key]
            if ts > cutoff
        ]

        # Check count
        count = len(self.rate_limit_state[type_key])
        limit = self.RATE_LIMITS[message_type]

        if count >= limit:
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "count": count,
                "limit": limit,
                "reset_at": (cutoff + timedelta(hours=1)).isoformat(),
            }

        return {
            "allowed": True,
            "count": count,
            "limit": limit,
            "remaining": limit - count,
        }

    def record_message(self, message_type: MessageType) -> None:
        """
        Record a message for rate limiting.

        Args:
            message_type: Type of message sent
        """
        type_key = message_type.value
        if type_key not in self.rate_limit_state:
            self.rate_limit_state[type_key] = []

        self.rate_limit_state[type_key].append(datetime.now(timezone.utc))

    def validate_payload(
        self,
        message_type: MessageType,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate message payload structure.

        Args:
            message_type: Type of message
            payload: Payload to validate

        Returns:
            Validation result
        """
        if message_type == MessageType.CONTRIBUTE:
            return self._validate_contribute(payload)
        elif message_type == MessageType.REQUEST:
            return self._validate_request(payload)
        elif message_type == MessageType.SYNC:
            return self._validate_sync(payload)
        elif message_type == MessageType.HEARTBEAT:
            return self._validate_heartbeat(payload)
        else:
            return {"valid": True}

    def _validate_contribute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CONTRIBUTE message payload."""
        if "concepts" not in payload:
            return {
                "valid": False,
                "reason": "missing_concepts",
            }

        if not isinstance(payload["concepts"], list):
            return {
                "valid": False,
                "reason": "concepts_must_be_list",
            }

        if len(payload["concepts"]) == 0:
            return {
                "valid": False,
                "reason": "empty_concepts",
            }

        # Check concept size limit (prevent abuse)
        MAX_CONCEPTS = 1000
        if len(payload["concepts"]) > MAX_CONCEPTS:
            return {
                "valid": False,
                "reason": "too_many_concepts",
                "limit": MAX_CONCEPTS,
            }

        return {"valid": True}

    def _validate_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate REQUEST message payload."""
        if "query" not in payload:
            return {
                "valid": False,
                "reason": "missing_query",
            }

        return {"valid": True}

    def _validate_sync(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SYNC message payload."""
        # SYNC can have various payloads
        return {"valid": True}

    def _validate_heartbeat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HEARTBEAT message payload."""
        # HEARTBEAT payloads are simple
        return {"valid": True}

    def _sign_message(self, message: Dict[str, Any], key: Optional[str] = None) -> str:
        """
        Sign a message using HMAC-SHA256.

        Args:
            message: Message to sign (without signature field)
            key: Secret key (uses self.secret_key if not provided)

        Returns:
            Hex-encoded signature
        """
        key_to_use = key or self.secret_key

        # Create canonical representation (sorted keys)
        canonical = json.dumps(message, sort_keys=True)

        # Generate HMAC signature
        signature = hmac.new(
            key_to_use.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _generate_secret(self) -> str:
        """Generate a random secret key."""
        import secrets
        return secrets.token_hex(32)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get protocol statistics.

        Returns:
            Statistics about message counts and rate limits
        """
        stats = {
            "node_id": self.node_id,
            "rate_limits": {},
        }

        for msg_type, limit in self.RATE_LIMITS.items():
            type_key = msg_type.value
            count = len(self.rate_limit_state.get(type_key, []))
            stats["rate_limits"][type_key] = {
                "count": count,
                "limit": limit,
                "remaining": limit - count,
            }

        return stats
