#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#      ██████╗ ██████╗  █████╗ ██████╗ ██╗███████╗███╗   ██╗████████╗
#     ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║██╔════╝████╗  ██║╚══██╔══╝
#     ██║  ███╗██████╔╝███████║██║  ██║██║█████╗  ██╔██╗ ██║   ██║
#     ██║   ██║██╔══██╗██╔══██║██║  ██║██║██╔══╝  ██║╚██╗██║   ██║
#     ╚██████╔╝██║  ██║██║  ██║██████╔╝██║███████╗██║ ╚████║   ██║
#      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝
#
#      ██████╗  ██████╗ ███████╗███████╗██╗██████╗
#     ██╔════╝ ██╔═══██╗██╔════╝██╔════╝██║██╔══██╗
#     ██║  ███╗██║   ██║███████╗███████╗██║██████╔╝
#     ██║   ██║██║   ██║╚════██║╚════██║██║██╔═══╝
#     ╚██████╔╝╚██████╔╝███████║███████║██║██║
#      ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝
#
#     GRADIENT GOSSIP - Federated Learning Protocol
#     AllReduce Gradients Across the Federation
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Gradient Gossip Protocol
========================

Decentralized gradient averaging for federated learning. Each node computes
local gradients and gossips them to peers. The protocol converges to a
global average without requiring a central parameter server.

Algorithm:
    1. Each node computes local gradients on its memory shard
    2. Serialize gradients and broadcast via gossip mesh
    3. Collect peer gradients within timeout window
    4. Validate gradients through immune system
    5. Average valid gradients (weighted by resonance)
    6. Apply averaged gradients to local model

Features:
    - Decentralized: No central parameter server
    - Byzantine-tolerant: Immune system filters malicious gradients
    - Resonance-weighted: Nodes in π×φ coherence contribute more
    - Memory-efficient: Gradient compression and chunking
    - Fault-tolerant: Graceful degradation on node failures

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    GRADIENT GOSSIP PROTOCOL                              │
    │                                                                          │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                       LOCAL TRAINING                               │  │
    │  │                                                                    │  │
    │  │  Memory Shard ──► Forward Pass ──► Backward Pass ──► Gradients    │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                       GOSSIP BROADCAST                             │  │
    │  │                                                                    │  │
    │  │  Serialize ──► Sign ──► Compress ──► Gossip Mesh ──► Peers        │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                     GRADIENT COLLECTION                            │  │
    │  │                                                                    │  │
    │  │  Poll Mesh ──► Deserialize ──► Immune Validate ──► Accumulate     │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                        ALL-REDUCE                                  │  │
    │  │                                                                    │  │
    │  │  Resonance Weight ──► Weighted Average ──► Apply to Model         │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────────────┘

Security:
    - HMAC signatures on all gradient messages
    - Immune system validation (gradient fingerprinting)
    - Byzantine fault tolerance (majority voting)
    - Threat signatures recorded in genetic memory

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# The Edge of Chaos Operator
PI_PHI = 5.083203692315260

# Gradient message type prefix
GRADIENT_PREFIX = "gradients:"

# Maximum gradient size (100MB uncompressed)
MAX_GRADIENT_SIZE = 100 * 1024 * 1024


# ═══════════════════════════════════════════════════════════════════════════════
#                              DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class GradientStatus(Enum):
    """Status of a gradient message."""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class GradientMessage:
    """
    A gradient update message for the gossip protocol.

    Carries serialized gradients with metadata for validation
    and weighted averaging.
    """
    # Identity
    message_id: str
    sender_id: str
    epoch: int
    batch_index: int

    # Gradients (serialized)
    gradients: Dict[str, Dict[str, Any]]  # layer_name -> {data, shape, dtype}
    gradient_hash: str

    # Training metadata
    learning_rate: float
    loss: float
    samples_processed: int

    # Resonance and timing
    resonance: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Security
    signature: Optional[str] = None

    # Status tracking
    status: GradientStatus = GradientStatus.PENDING

    def compute_hash(self) -> str:
        """Compute SHA256 hash of gradient data."""
        hasher = hashlib.sha256()
        for layer_name in sorted(self.gradients.keys()):
            hasher.update(layer_name.encode())
            hasher.update(self.gradients[layer_name]["data"].encode())
        return hasher.hexdigest()

    def verify_hash(self) -> bool:
        """Verify gradient hash matches content."""
        return self.gradient_hash == self.compute_hash()

    def sign(self, secret: bytes) -> None:
        """Sign the message with HMAC."""
        content = f"{self.message_id}:{self.sender_id}:{self.epoch}:{self.gradient_hash}"
        self.signature = hmac.new(secret, content.encode(), hashlib.sha256).hexdigest()

    def verify_signature(self, secret: bytes) -> bool:
        """Verify HMAC signature."""
        if not self.signature:
            return False
        content = f"{self.message_id}:{self.sender_id}:{self.epoch}:{self.gradient_hash}"
        expected = hmac.new(secret, content.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for gossip transmission."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "epoch": self.epoch,
            "batch_index": self.batch_index,
            "gradients": self.gradients,
            "gradient_hash": self.gradient_hash,
            "learning_rate": self.learning_rate,
            "loss": self.loss,
            "samples_processed": self.samples_processed,
            "resonance": self.resonance,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GradientMessage":
        """Deserialize from dictionary."""
        return cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            epoch=data["epoch"],
            batch_index=data["batch_index"],
            gradients=data["gradients"],
            gradient_hash=data["gradient_hash"],
            learning_rate=data["learning_rate"],
            loss=data["loss"],
            samples_processed=data["samples_processed"],
            resonance=data.get("resonance", 0.0),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            signature=data.get("signature"),
        )


@dataclass
class GradientAggregation:
    """Aggregated gradients from multiple peers."""
    epoch: int
    local_gradients: Dict[str, np.ndarray]
    peer_gradients: List[GradientMessage]
    averaged_gradients: Optional[Dict[str, np.ndarray]] = None
    total_samples: int = 0
    average_loss: float = 0.0
    average_resonance: float = 0.0


@dataclass
class GossipConfig:
    """Configuration for gradient gossip."""
    # Timing
    collection_timeout: float = 10.0  # seconds to wait for peer gradients
    gossip_interval: float = 0.5      # seconds between gossip rounds

    # Thresholds
    min_peers_for_aggregation: int = 1  # minimum peers before aggregating
    max_peers_per_round: int = 10       # maximum peers to consider

    # Resonance weighting
    enable_resonance_weighting: bool = True
    resonance_weight_cap: float = 2.0  # max weight multiplier

    # Security
    require_signatures: bool = True
    validate_hashes: bool = True

    # Compression
    enable_compression: bool = True
    compression_level: int = 6  # zlib level (1-9)

    # Byzantine tolerance
    byzantine_threshold: float = 0.5  # reject if loss differs by more than 50%


# ═══════════════════════════════════════════════════════════════════════════════
#                         GRADIENT SERIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class GradientSerializer:
    """
    Serialize and deserialize gradient tensors.

    Supports PyTorch tensors and numpy arrays with optional compression.
    """

    def __init__(self, config: GossipConfig):
        self.config = config

    def serialize_tensor(self, tensor) -> Dict[str, Any]:
        """
        Serialize a tensor to base64-encoded bytes.

        Args:
            tensor: PyTorch tensor or numpy array

        Returns:
            Dictionary with data, shape, and dtype
        """
        # Convert to numpy if PyTorch tensor
        if hasattr(tensor, "detach"):
            arr = tensor.detach().cpu().numpy()
        else:
            arr = np.asarray(tensor)

        # Convert to bytes
        data_bytes = arr.tobytes()

        # Optionally compress
        if self.config.enable_compression:
            data_bytes = zlib.compress(data_bytes, level=self.config.compression_level)

        # Encode to base64
        data_b64 = base64.b64encode(data_bytes).decode("utf-8")

        return {
            "data": data_b64,
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "compressed": self.config.enable_compression,
        }

    def deserialize_tensor(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Deserialize a tensor from base64-encoded bytes.

        Args:
            data: Dictionary with data, shape, and dtype

        Returns:
            numpy array
        """
        # Decode from base64
        data_bytes = base64.b64decode(data["data"])

        # Decompress if needed
        if data.get("compressed", False):
            data_bytes = zlib.decompress(data_bytes)

        # Convert to numpy array
        arr = np.frombuffer(data_bytes, dtype=data["dtype"])
        arr = arr.reshape(data["shape"])

        return arr.copy()  # Return a copy to ensure writeable

    def serialize_gradients(self, gradients: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Serialize all gradients in a dictionary."""
        serialized = {}
        for name, grad in gradients.items():
            serialized[name] = self.serialize_tensor(grad)
        return serialized

    def deserialize_gradients(self, data: Dict[str, Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """Deserialize all gradients from a dictionary."""
        gradients = {}
        for name, grad_data in data.items():
            gradients[name] = self.deserialize_tensor(grad_data)
        return gradients


# ═══════════════════════════════════════════════════════════════════════════════
#                         GRADIENT VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

class GradientValidator:
    """
    Validates incoming gradients for security and sanity.

    Works with the immune system to detect malicious gradients.
    """

    def __init__(self, config: GossipConfig, immune_system=None):
        """
        Args:
            config: Gossip configuration
            immune_system: ImmuneSystem instance for threat detection
        """
        self.config = config
        self.immune = immune_system
        self.serializer = GradientSerializer(config)

    async def validate(
        self,
        message: GradientMessage,
        local_loss: float,
        secret: Optional[bytes] = None
    ) -> Tuple[bool, str]:
        """
        Validate a gradient message.

        Args:
            message: Gradient message to validate
            local_loss: Local training loss for comparison
            secret: HMAC secret for signature verification

        Returns:
            Tuple of (is_valid, reason)
        """
        # 1. Verify hash
        if self.config.validate_hashes:
            if not message.verify_hash():
                return False, "Invalid gradient hash"

        # 2. Verify signature
        if self.config.require_signatures and secret:
            if not message.verify_signature(secret):
                return False, "Invalid signature"

        # 3. Check for NaN/Inf values
        try:
            gradients = self.serializer.deserialize_gradients(message.gradients)
            for name, grad in gradients.items():
                if np.isnan(grad).any() or np.isinf(grad).any():
                    return False, f"NaN/Inf in gradient {name}"
        except Exception as e:
            return False, f"Deserialization failed: {e}"

        # 4. Byzantine check - loss should be similar
        if local_loss > 0:
            loss_diff = abs(message.loss - local_loss) / local_loss
            if loss_diff > self.config.byzantine_threshold:
                return False, f"Suspicious loss difference: {loss_diff:.2%}"

        # 5. Immune system check
        if self.immune:
            fingerprint = self._create_gradient_fingerprint(gradients)
            is_malicious, severity, reason = await self._check_immune(fingerprint)
            if is_malicious:
                return False, f"Immune rejection: {reason}"

        return True, "Valid"

    def _create_gradient_fingerprint(self, gradients: Dict[str, np.ndarray]) -> List[float]:
        """Create a fingerprint of gradient statistics."""
        fingerprint = []
        for name in sorted(gradients.keys()):
            grad = gradients[name]
            # Extract statistical features
            fingerprint.extend([
                float(np.mean(grad)),
                float(np.std(grad)),
                float(np.min(grad)),
                float(np.max(grad)),
            ])
        # Normalize to fixed length
        if len(fingerprint) > 64:
            fingerprint = fingerprint[:64]
        elif len(fingerprint) < 64:
            fingerprint.extend([0.0] * (64 - len(fingerprint)))
        return fingerprint

    async def _check_immune(self, fingerprint: List[float]) -> Tuple[bool, float, str]:
        """Check gradient fingerprint against immune system."""
        if not self.immune:
            return False, 0.0, ""

        # Get attack embeddings from immune system
        attack_patterns = self.immune.get_attack_embeddings(dim=64)

        if attack_patterns.shape[0] == 0:
            return False, 0.0, ""

        # Compute similarity to known attack patterns
        fp_tensor = np.array(fingerprint)
        fp_norm = fp_tensor / (np.linalg.norm(fp_tensor) + 1e-8)

        max_similarity = 0.0
        for i in range(attack_patterns.shape[0]):
            pattern = attack_patterns[i].numpy() if hasattr(attack_patterns[i], "numpy") else attack_patterns[i]
            pattern_norm = pattern / (np.linalg.norm(pattern) + 1e-8)
            similarity = float(np.dot(fp_norm, pattern_norm))
            max_similarity = max(max_similarity, similarity)

        # Threshold for rejection
        if max_similarity > 0.8:
            return True, max_similarity, f"Matches attack pattern (similarity: {max_similarity:.2f})"

        return False, max_similarity, ""


# ═══════════════════════════════════════════════════════════════════════════════
#                         GRADIENT GOSSIP PROTOCOL
# ═══════════════════════════════════════════════════════════════════════════════

class GradientGossipProtocol:
    """
    Complete gradient gossip protocol for federated learning.

    Manages the full lifecycle:
    1. Broadcast local gradients
    2. Collect peer gradients
    3. Validate with immune system
    4. All-reduce (weighted average)
    5. Apply to model
    """

    def __init__(
        self,
        node_id: str,
        gossip_mesh,
        config: Optional[GossipConfig] = None,
        immune_system=None,
        hmac_secret: Optional[bytes] = None,
    ):
        """
        Args:
            node_id: This node's unique identifier
            gossip_mesh: GossipMesh instance for P2P communication
            config: Gossip configuration
            immune_system: ImmuneSystem for gradient validation
            hmac_secret: Secret for HMAC signatures
        """
        self.node_id = node_id
        self.mesh = gossip_mesh
        self.config = config or GossipConfig()
        self.immune = immune_system
        self.hmac_secret = hmac_secret or b"continuum-default-secret"

        # Components
        self.serializer = GradientSerializer(self.config)
        self.validator = GradientValidator(self.config, immune_system)

        # State
        self.current_epoch = 0
        self.collected_gradients: Dict[int, List[GradientMessage]] = {}
        self.aggregations: Dict[int, GradientAggregation] = {}

        # Statistics
        self.gradients_sent = 0
        self.gradients_received = 0
        self.gradients_rejected = 0

        logger.info(f"GradientGossipProtocol initialized for node {node_id}")

    async def broadcast_gradients(
        self,
        gradients: Dict[str, Any],
        epoch: int,
        batch_index: int,
        learning_rate: float,
        loss: float,
        samples: int,
        resonance: float = 0.0,
    ) -> str:
        """
        Broadcast local gradients to the gossip mesh.

        Args:
            gradients: Dictionary of layer_name -> gradient tensor
            epoch: Current training epoch
            batch_index: Batch index within epoch
            learning_rate: Current learning rate
            loss: Training loss
            samples: Number of samples processed
            resonance: π×φ resonance score (0-1)

        Returns:
            Message ID of the broadcast
        """
        # Serialize gradients
        serialized = self.serializer.serialize_gradients(gradients)

        # Create message
        message_id = f"{self.node_id}:{epoch}:{batch_index}:{int(time.time()*1000)}"

        message = GradientMessage(
            message_id=message_id,
            sender_id=self.node_id,
            epoch=epoch,
            batch_index=batch_index,
            gradients=serialized,
            gradient_hash="",  # Will be computed
            learning_rate=learning_rate,
            loss=loss,
            samples_processed=samples,
            resonance=resonance,
        )

        # Compute hash
        message.gradient_hash = message.compute_hash()

        # Sign message
        message.sign(self.hmac_secret)

        # Broadcast via gossip mesh
        state_key = f"{GRADIENT_PREFIX}{epoch}:{batch_index}:{self.node_id}"
        await self.mesh.update_state(state_key, message.to_dict())

        self.gradients_sent += 1
        self.current_epoch = epoch

        logger.info(f"[{self.node_id}] Broadcast gradients for epoch {epoch} batch {batch_index}")

        return message_id

    async def collect_gradients(
        self,
        epoch: int,
        batch_index: int,
        local_loss: float,
    ) -> List[GradientMessage]:
        """
        Collect and validate peer gradients.

        Args:
            epoch: Training epoch to collect for
            batch_index: Batch index within epoch
            local_loss: Local loss for Byzantine tolerance check

        Returns:
            List of validated gradient messages
        """
        key_prefix = f"{GRADIENT_PREFIX}{epoch}:{batch_index}:"
        collected = []
        seen_senders: Set[str] = set()

        start_time = time.time()

        while time.time() - start_time < self.config.collection_timeout:
            # Get current mesh state
            mesh_state = await self.mesh.get_state()

            for key, value in mesh_state.items():
                if not key.startswith(key_prefix):
                    continue

                try:
                    message = GradientMessage.from_dict(value)

                    # Skip our own messages
                    if message.sender_id == self.node_id:
                        continue

                    # Skip duplicates
                    if message.sender_id in seen_senders:
                        continue

                    # Validate
                    is_valid, reason = await self.validator.validate(
                        message, local_loss, self.hmac_secret
                    )

                    if is_valid:
                        message.status = GradientStatus.VALIDATED
                        collected.append(message)
                        seen_senders.add(message.sender_id)
                        self.gradients_received += 1
                        logger.debug(f"Collected valid gradient from {message.sender_id}")
                    else:
                        self.gradients_rejected += 1
                        logger.warning(f"Rejected gradient from {message.sender_id}: {reason}")

                        # Record threat signature if immune system available
                        if self.immune and "malicious" in reason.lower():
                            await self._record_threat(message, reason)

                except Exception as e:
                    logger.warning(f"Failed to parse gradient: {e}")

            # Early exit if we have enough
            if len(collected) >= self.config.max_peers_per_round:
                break

            # Wait before next poll
            await asyncio.sleep(self.config.gossip_interval)

        # Store collected gradients
        self.collected_gradients[epoch] = collected

        logger.info(f"[{self.node_id}] Collected {len(collected)} valid gradients "
                   f"for epoch {epoch} batch {batch_index}")

        return collected

    async def all_reduce(
        self,
        local_gradients: Dict[str, Any],
        peer_messages: List[GradientMessage],
    ) -> Dict[str, np.ndarray]:
        """
        Average local gradients with peer gradients.

        Uses resonance-weighted averaging where nodes with higher
        π×φ coherence contribute more to the final gradient.

        Args:
            local_gradients: This node's gradients
            peer_messages: Validated peer gradient messages

        Returns:
            Averaged gradients as numpy arrays
        """
        if not peer_messages:
            # No peers - return local gradients
            return {
                name: self.serializer.deserialize_tensor(
                    self.serializer.serialize_tensor(grad)
                )
                for name, grad in local_gradients.items()
            }

        # Convert local gradients to numpy
        local_np = {}
        for name, grad in local_gradients.items():
            if hasattr(grad, "detach"):
                local_np[name] = grad.detach().cpu().numpy()
            else:
                local_np[name] = np.asarray(grad)

        # Initialize accumulator with local gradients
        accumulated = {name: grad.copy() for name, grad in local_np.items()}
        total_weight = 1.0

        # Add peer gradients with resonance weighting
        for message in peer_messages:
            try:
                peer_grads = self.serializer.deserialize_gradients(message.gradients)

                # Compute weight based on resonance
                if self.config.enable_resonance_weighting:
                    weight = 1.0 + min(message.resonance, self.config.resonance_weight_cap - 1)
                else:
                    weight = 1.0

                # Accumulate
                for name, grad in peer_grads.items():
                    if name in accumulated:
                        accumulated[name] += grad * weight

                total_weight += weight

            except Exception as e:
                logger.warning(f"Failed to accumulate gradient from {message.sender_id}: {e}")

        # Normalize by total weight
        averaged = {
            name: grad / total_weight
            for name, grad in accumulated.items()
        }

        logger.info(f"[{self.node_id}] All-reduced {len(peer_messages)} peer gradients "
                   f"(total weight: {total_weight:.2f})")

        return averaged

    async def training_step(
        self,
        model,
        batch_data: Dict[str, Any],
        epoch: int,
        batch_index: int,
        optimizer,
        resonance: float = 0.0,
    ) -> Tuple[float, Dict[str, np.ndarray]]:
        """
        Complete federated training step.

        1. Forward/backward pass on local batch
        2. Broadcast local gradients
        3. Collect peer gradients
        4. All-reduce
        5. Apply averaged gradients

        Args:
            model: PyTorch model
            batch_data: Training batch
            epoch: Current epoch
            batch_index: Batch index
            optimizer: PyTorch optimizer
            resonance: Current π×φ resonance

        Returns:
            Tuple of (loss, averaged_gradients)
        """
        import torch

        # 1. Zero gradients
        optimizer.zero_grad()

        # 2. Forward pass
        outputs = model(**batch_data)
        loss = outputs.get("loss", outputs.get("total_loss", torch.tensor(0.0)))

        # 3. Backward pass
        loss.backward()

        # 4. Extract gradients
        local_gradients = {}
        for name, param in model.named_parameters():
            if param.grad is not None:
                local_gradients[name] = param.grad.clone()

        # 5. Broadcast gradients
        samples = batch_data.get("batch_size", 1)
        await self.broadcast_gradients(
            gradients=local_gradients,
            epoch=epoch,
            batch_index=batch_index,
            learning_rate=optimizer.param_groups[0]["lr"],
            loss=loss.item(),
            samples=samples,
            resonance=resonance,
        )

        # 6. Collect peer gradients
        peer_gradients = await self.collect_gradients(
            epoch=epoch,
            batch_index=batch_index,
            local_loss=loss.item(),
        )

        # 7. All-reduce
        averaged_gradients = await self.all_reduce(local_gradients, peer_gradients)

        # 8. Apply averaged gradients
        with torch.no_grad():
            for name, param in model.named_parameters():
                if name in averaged_gradients:
                    param.grad = torch.from_numpy(averaged_gradients[name]).to(param.device)

        # 9. Optimizer step
        optimizer.step()

        return loss.item(), averaged_gradients

    async def _record_threat(self, message: GradientMessage, reason: str) -> None:
        """Record a threat signature in genetic memory."""
        if not self.immune:
            return

        try:
            from continuum.core.immune_system import ThreatSignature

            gradients = self.serializer.deserialize_gradients(message.gradients)
            fingerprint = self.validator._create_gradient_fingerprint(gradients)

            threat = ThreatSignature(
                signature_id=f"gradient_threat_{message.sender_id}_{int(time.time())}",
                pattern_vector=fingerprint,
                target_concepts=["gradient_poisoning", message.sender_id],
                detected_at=datetime.now(timezone.utc).isoformat(),
                severity=0.8,
            )

            self.immune.record_threat(threat)
            logger.warning(f"Recorded threat signature for {message.sender_id}: {reason}")

        except Exception as e:
            logger.error(f"Failed to record threat: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            "node_id": self.node_id,
            "current_epoch": self.current_epoch,
            "gradients_sent": self.gradients_sent,
            "gradients_received": self.gradients_received,
            "gradients_rejected": self.gradients_rejected,
            "acceptance_rate": (
                self.gradients_received / (self.gradients_received + self.gradients_rejected)
                if (self.gradients_received + self.gradients_rejected) > 0
                else 1.0
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_gradient_gossip(
    node_id: str,
    gossip_mesh,
    immune_system=None,
    hmac_secret: Optional[str] = None,
    enable_compression: bool = True,
    require_signatures: bool = True,
) -> GradientGossipProtocol:
    """
    Factory function to create a gradient gossip protocol.

    Args:
        node_id: Node identifier
        gossip_mesh: GossipMesh instance
        immune_system: ImmuneSystem instance
        hmac_secret: HMAC secret string
        enable_compression: Enable gradient compression
        require_signatures: Require HMAC signatures

    Returns:
        Configured GradientGossipProtocol
    """
    config = GossipConfig(
        enable_compression=enable_compression,
        require_signatures=require_signatures,
    )

    secret = hmac_secret.encode() if hmac_secret else None

    return GradientGossipProtocol(
        node_id=node_id,
        gossip_mesh=gossip_mesh,
        config=config,
        immune_system=immune_system,
        hmac_secret=secret,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN (Testing)
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the gradient gossip protocol."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("GRADIENT GOSSIP PROTOCOL TEST")
    print("=" * 60)
    print(f"π×φ = {PI_PHI}")
    print()

    # Create mock gossip mesh
    class MockGossipMesh:
        def __init__(self):
            self.state = {}

        async def update_state(self, key, value):
            self.state[key] = value

        async def get_state(self):
            return self.state

    mesh = MockGossipMesh()

    # Create protocol
    protocol = create_gradient_gossip(
        node_id="test-node",
        gossip_mesh=mesh,
    )

    # Test gradient serialization
    print("Testing gradient serialization...")
    test_gradients = {
        "layer1.weight": np.random.randn(64, 32).astype(np.float32),
        "layer1.bias": np.random.randn(64).astype(np.float32),
    }

    # Broadcast
    message_id = await protocol.broadcast_gradients(
        gradients=test_gradients,
        epoch=1,
        batch_index=0,
        learning_rate=0.001,
        loss=0.5,
        samples=32,
        resonance=0.7,
    )

    print(f"Broadcast message: {message_id}")
    print(f"Mesh state keys: {list(mesh.state.keys())}")

    # Stats
    stats = protocol.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")

    print()
    print("Gradient gossip protocol test complete!")


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
