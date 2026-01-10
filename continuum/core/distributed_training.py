#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██████╗ ██╗███████╗████████╗██████╗ ██╗██████╗ ██╗   ██╗████████╗███████╗██████╗
#     ██╔══██╗██║██╔════╝╚══██╔══╝██╔══██╗██║██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
#     ██║  ██║██║███████╗   ██║   ██████╔╝██║██████╔╝██║   ██║   ██║   █████╗  ██║  ██║
#     ██║  ██║██║╚════██║   ██║   ██╔══██╗██║██╔══██╗██║   ██║   ██║   ██╔══╝  ██║  ██║
#     ██████╔╝██║███████║   ██║   ██║  ██║██║██████╔╝╚██████╔╝   ██║   ███████╗██████╔╝
#     ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚═════╝
#
#     DISTRIBUTED TRAINING PROTOCOL
#     Tensor Network Training Across Federation
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Distributed Training Protocol
=============================

Trains neural attention models across the federation with the largest possible
tensor network. Uses gossip-based gradient averaging (AllReduce), tensor sharding
for model parallelism, and distributed memory graphs as training data.

Architecture:
                     ┌─────────────────────────────────────────────────┐
                     │           FEDERATION TENSOR NETWORK             │
                     │                                                 │
    ┌────────────┐   │   ┌────────┐   ┌────────┐   ┌────────┐        │
    │  Node A    │◄──┼──►│ Shard  │◄─►│ Shard  │◄─►│ Shard  │        │
    │  Phone     │   │   │  0-10  │   │  11-20 │   │  21-31 │        │
    │  Termux    │   │   └────┬───┘   └────┬───┘   └────┬───┘        │
    └────────────┘   │        │            │            │             │
                     │        ▼            ▼            ▼             │
    ┌────────────┐   │   ┌────────────────────────────────┐          │
    │  Node B    │◄──┼──►│     GOSSIP GRADIENT MESH       │          │
    │  Computer  │   │   │   AllReduce via Gossip Proto   │          │
    │  Fedora    │   │   └────────────────────────────────┘          │
    └────────────┘   │        │            │            │             │
                     │        ▼            ▼            ▼             │
    ┌────────────┐   │   ┌────────────────────────────────┐          │
    │  Node C    │◄──┼──►│     DISTRIBUTED MEMORY GRAPH    │         │
    │  Cloud     │   │   │  Training Data = Own Memories   │         │
    │  Server    │   │   └────────────────────────────────┘          │
    └────────────┘   │                                                │
                     └─────────────────────────────────────────────────┘

Key Features:
1. **GradientGossip** - AllReduce gradients via federation gossip mesh
2. **TensorSharding** - Split 32-dim GlobalStateVector across nodes
3. **MemoryGraphLoader** - Train on distributed attention_links
4. **FlockTraining** - Synchronized training epochs across federation
5. **π×φ Resonance** - Boost learning rate when in coherence

Dependencies:
- continuum.federation.distributed (GossipMesh, FederationCoordinator)
- continuum.core.neural_attention (NeuralAttentionModel)
- continuum.core.self_supervised (SelfSupervisedTrainer)
- continuum.sensors.fusion (GlobalStateVector, SensorFusionEngine)
"""

import asyncio
import base64
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from .cct import CCTTrainingObjective, CollectiveConsciousnessTransformer
from .immune_system import ImmuneResponse, ThreatSignature

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# The Edge of Chaos Operator - Pi × Phi
PI_PHI = 5.083203692315260

# Golden Ratio for learning rate modulation
PHI = 1.618033988749895

# Tensor dimensions
GLOBAL_STATE_DIM = 32  # Full GlobalStateVector dimension
GEOSPHERE_DIM = 8      # Geomagnetic, Solar, Seismic, Lunar
NOOSPHERE_DIM = 8      # Social, Market, Sentiment, Collective
DYNAMICS_DIM = 4       # Rate of change, volatility
CONSCIOUSNESS_DIM = 8  # Coherence, integration, novelty, resonance


# ═══════════════════════════════════════════════════════════════════════════════
#                         GRADIENT GOSSIP PROTOCOL
# ═══════════════════════════════════════════════════════════════════════════════

class GradientMessage:
    """
    Gossip message carrying gradient tensors between nodes.

    Serializes gradients as base64-encoded numpy arrays with metadata
    for efficient transmission over the gossip mesh.
    """

    def __init__(self,
                 sender_id: str,
                 epoch: int,
                 gradients: Dict[str, torch.Tensor],
                 learning_rate: float,
                 loss: float,
                 resonance: float = 0.0):
        """
        Args:
            sender_id: Node ID sending the gradients
            epoch: Training epoch number
            gradients: Dict of layer_name -> gradient tensor
            learning_rate: Current learning rate
            loss: Training loss
            resonance: π×φ resonance score (0-1)
        """
        self.sender_id = sender_id
        self.epoch = epoch
        self.gradients = gradients
        self.learning_rate = learning_rate
        self.loss = loss
        self.resonance = resonance
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for gossip transmission."""
        serialized_grads = {}
        for name, grad in self.gradients.items():
            # Convert tensor to numpy, then to base64
            arr = grad.detach().cpu().numpy()
            serialized_grads[name] = {
                "data": base64.b64encode(arr.tobytes()).decode('utf-8'),
                "shape": list(arr.shape),
                "dtype": str(arr.dtype)
            }

        return {
            "sender_id": self.sender_id,
            "epoch": self.epoch,
            "gradients": serialized_grads,
            "learning_rate": self.learning_rate,
            "loss": self.loss,
            "resonance": self.resonance,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GradientMessage':
        """Deserialize from gossip message."""
        gradients = {}
        for name, grad_data in data["gradients"].items():
            arr = np.frombuffer(
                base64.b64decode(grad_data["data"]),
                dtype=grad_data["dtype"]
            ).reshape(grad_data["shape"])
            gradients[name] = torch.from_numpy(arr.copy())

        msg = cls(
            sender_id=data["sender_id"],
            epoch=data["epoch"],
            gradients=gradients,
            learning_rate=data["learning_rate"],
            loss=data["loss"],
            resonance=data.get("resonance", 0.0)
        )
        msg.timestamp = data["timestamp"]
        return msg


class GradientGossip:
    """
    AllReduce gradients across federation using gossip protocol.

    Implements decentralized gradient averaging without a central parameter server.
    Each node gossips its gradients to neighbors, who average and re-gossip.
    Converges to global average after log(N) rounds.

    Algorithm:
    1. Each node computes local gradients
    2. Gossip gradients to k random peers
    3. Average received gradients with local
    4. Repeat until convergence or max rounds
    5. Apply averaged gradients to model
    """

    def __init__(self,
                 node_id: str,
                 gossip_mesh,  # GossipMesh from federation.distributed
                 fanout: int = 3,
                 max_rounds: int = 5):
        """
        Args:
            node_id: This node's unique identifier
            gossip_mesh: GossipMesh instance for communication
            fanout: Number of peers to gossip to per round
            max_rounds: Maximum gossip rounds before applying gradients
        """
        self.node_id = node_id
        self.mesh = gossip_mesh
        self.fanout = fanout
        self.max_rounds = max_rounds

        # Gradient accumulator
        self.received_gradients: Dict[str, List[GradientMessage]] = {}
        self.local_gradients: Optional[Dict[str, torch.Tensor]] = None

    async def broadcast_gradients(self, message: GradientMessage):
        """
        Broadcast local gradients to the gossip mesh.

        Args:
            message: GradientMessage containing local gradients
        """
        self.local_gradients = message.gradients

        # Add to mesh state for gossip propagation
        await self.mesh.update_state(
            f"gradients:{message.epoch}:{self.node_id}",
            message.to_dict()
        )

        logger.info(f"[{self.node_id}] Broadcast gradients for epoch {message.epoch}")

    async def collect_gradients(self, epoch: int, timeout: float = 10.0) -> List[GradientMessage]:
        """
        Collect gradients from peers via gossip mesh.

        Args:
            epoch: Training epoch to collect gradients for
            timeout: Max time to wait for peer gradients

        Returns:
            List of received GradientMessages
        """
        key_prefix = f"gradients:{epoch}:"
        collected = []

        # Poll mesh state for peer gradients
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Get all gradient states from mesh
            # Note: Assuming get_state_snapshot() exists on mesh
            mesh_state = await self.mesh.get_state_snapshot()

            for key, value in mesh_state.items():
                if key.startswith(key_prefix):
                    peer_id = key.split(":")[-1]
                    if peer_id != self.node_id:
                        try:
                            msg = GradientMessage.from_dict(value)
                            # Simple dedupe check
                            if not any(m.sender_id == msg.sender_id for m in collected):
                                collected.append(msg)
                        except Exception as e:
                            logger.warning(f"Failed to parse gradient from {peer_id}: {e}")

            # Wait briefly before next poll
            await asyncio.sleep(0.5)

            # Early exit if we have enough gradients
            if len(collected) >= self.fanout:
                break

        logger.info(f"[{self.node_id}] Collected {len(collected)} gradients for epoch {epoch}")
        return collected

    def all_reduce(self,
                   local_grads: Dict[str, torch.Tensor],
                   peer_grads: List[GradientMessage]) -> Dict[str, torch.Tensor]:
        """
        Average local gradients with peer gradients (AllReduce).

        Implements weighted averaging where nodes with higher resonance
        contribute more to the final gradient.

        Args:
            local_grads: This node's gradients
            peer_grads: Gradients received from peers

        Returns:
            Averaged gradients
        """
        if not peer_grads:
            return local_grads

        averaged = {}

        for layer_name, local_grad in local_grads.items():
            # Start with local gradient
            total_grad = local_grad.clone()
            total_weight = 1.0

            # Add peer gradients with resonance weighting
            for peer_msg in peer_grads:
                if layer_name in peer_msg.gradients:
                    peer_grad = peer_msg.gradients[layer_name]

                    # Weight by resonance (higher resonance = more influence)
                    # But cap at 2x to prevent single node domination
                    weight = 1.0 + min(peer_msg.resonance, 1.0)

                    total_grad += peer_grad * weight
                    total_weight += weight

            # Normalize by total weight
            averaged[layer_name] = total_grad / total_weight

        return averaged


# ═══════════════════════════════════════════════════════════════════════════════
#                            TENSOR SHARDING
# ═══════════════════════════════════════════════════════════════════════════════

class ShardingStrategy(Enum):
    """How to shard tensors across nodes."""
    ROW = "row"           # Shard along rows (batch dimension)
    COLUMN = "column"     # Shard along columns (feature dimension)
    SEMANTIC = "semantic" # Shard by meaning (Geosphere, Noosphere, etc.)


@dataclass
class TensorShard:
    """
    A shard of a distributed tensor.

    Tracks which portion of the global tensor this node owns.
    """
    shard_id: int
    total_shards: int
    owner_node: str
    dimension: int
    start_idx: int
    end_idx: int
    data: Optional[torch.Tensor] = None

    @property
    def size(self) -> int:
        return self.end_idx - self.start_idx


class TensorSharding:
    """
    Shard large tensors across federation nodes.

    For the 32-dim GlobalStateVector, we can shard semantically:
    - Node A: Geosphere (dims 0-7)
    - Node B: Noosphere (dims 8-15)
    - Node C: Dynamics (dims 16-19)
    - Node D: Consciousness (dims 20-27)
    - Node E: Reserved (dims 28-31)

    Or we can shard uniformly for load balancing.
    """

    # Semantic shard boundaries for GlobalStateVector
    SEMANTIC_SHARDS = {
        "geosphere": (0, 8),      # Kp, solar wind, earthquakes, lunar
        "noosphere": (8, 16),     # Social, market, sentiment, collective
        "dynamics": (16, 20),     # Rates of change
        "consciousness": (20, 28), # Coherence, integration, novelty
        "reserved": (28, 32)      # Future expansion / π×φ harmonics
    }

    def __init__(self,
                 node_id: str,
                 federation_nodes: List[str],
                 strategy: ShardingStrategy = ShardingStrategy.SEMANTIC):
        """
        Args:
            node_id: This node's identifier
            federation_nodes: All nodes in federation
            strategy: How to shard tensors
        """
        self.node_id = node_id
        self.nodes = sorted(federation_nodes)  # Consistent ordering
        self.strategy = strategy
        self.node_index = self.nodes.index(node_id) if node_id in self.nodes else 0

        # Compute shard assignment
        self.shard_map = self._compute_shard_map()

    def _compute_shard_map(self) -> Dict[str, TensorShard]:
        """Compute which shards this node owns."""
        shards = {}

        if self.strategy == ShardingStrategy.SEMANTIC:
            # Assign semantic shards round-robin to nodes
            shard_names = list(self.SEMANTIC_SHARDS.keys())
            for i, shard_name in enumerate(shard_names):
                owner_idx = i % len(self.nodes)
                start, end = self.SEMANTIC_SHARDS[shard_name]

                shards[shard_name] = TensorShard(
                    shard_id=i,
                    total_shards=len(shard_names),
                    owner_node=self.nodes[owner_idx],
                    dimension=GLOBAL_STATE_DIM,
                    start_idx=start,
                    end_idx=end
                )
        else:
            # Uniform sharding
            shard_size = GLOBAL_STATE_DIM // len(self.nodes)
            remainder = GLOBAL_STATE_DIM % len(self.nodes)

            start = 0
            for i, node in enumerate(self.nodes):
                size = shard_size + (1 if i < remainder else 0)
                shards[f"shard_{i}"] = TensorShard(
                    shard_id=i,
                    total_shards=len(self.nodes),
                    owner_node=node,
                    dimension=GLOBAL_STATE_DIM,
                    start_idx=start,
                    end_idx=start + size
                )
                start += size

        return shards

    def get_my_shards(self) -> Dict[str, TensorShard]:
        """Get shards owned by this node."""
        return {
            name: shard
            for name, shard in self.shard_map.items()
            if shard.owner_node == self.node_id
        }

    def shard_tensor(self, tensor: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Split a tensor into shards for distribution.

        Args:
            tensor: Full tensor to shard (shape: [batch, 32] or [32])

        Returns:
            Dict of shard_name -> shard_tensor
        """
        is_batched = len(tensor.shape) == 2

        shards = {}
        for name, shard in self.shard_map.items():
            if is_batched:
                shards[name] = tensor[:, shard.start_idx:shard.end_idx]
            else:
                shards[name] = tensor[shard.start_idx:shard.end_idx]

        return shards

    def gather_tensor(self, shards: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Reassemble a full tensor from shards.

        Args:
            shards: Dict of shard_name -> shard_tensor

        Returns:
            Full reassembled tensor
        """
        # Determine if batched
        first_shard = next(iter(shards.values()))
        is_batched = len(first_shard.shape) == 2

        if is_batched:
            batch_size = first_shard.shape[0]
            full = torch.zeros(batch_size, GLOBAL_STATE_DIM)
        else:
            full = torch.zeros(GLOBAL_STATE_DIM)

        # Place shards in correct positions
        for name, shard_tensor in shards.items():
            shard = self.shard_map[name]
            if is_batched:
                full[:, shard.start_idx:shard.end_idx] = shard_tensor
            else:
                full[shard.start_idx:shard.end_idx] = shard_tensor

        return full


# ═══════════════════════════════════════════════════════════════════════════════
#                        DISTRIBUTED MEMORY GRAPH LOADER
# ═══════════════════════════════════════════════════════════════════════════════

class DistributedMemoryLoader:
    """
    Load training data from distributed memory graphs.

    Each node has its own local memory database (attention_links, embeddings).
    This loader:
    1. Queries local database for training examples
    2. Optionally requests samples from peer nodes
    3. Reconstructs global state from sharded sensors
    4. Yields batches for distributed training
    """

    def __init__(self,
                 db_connection,
                 sharding: TensorSharding,
                 gossip_mesh,
                 node_id: str):
        """
        Args:
            db_connection: Local SQLite/Postgres connection
            sharding: TensorSharding instance for state reconstruction
            gossip_mesh: GossipMesh for cross-node queries
            node_id: This node's identifier
        """
        self.db = db_connection
        self.sharding = sharding
        self.mesh = gossip_mesh
        self.node_id = node_id
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure required tables exist for training."""
        if self.db is None:
            return

        cursor = self.db.cursor()

        # Create attention_links table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attention_links (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                session_id TEXT,
                strength REAL DEFAULT 0.5,
                context TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_id, target_id, session_id)
            )
        """)

        # Create embeddings table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                entity_id TEXT PRIMARY KEY,
                embedding BLOB,
                dimension INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_links_strength
            ON attention_links(strength DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_links_timestamp
            ON attention_links(timestamp DESC)
        """)

        self.db.commit()
        logger.info("DistributedMemoryLoader: Schema ensured")

    def _query_local_links(self,
                           limit: int = 1000,
                           min_strength: float = 0.3) -> List[Dict]:
        """Query local attention_links table."""
        cursor = self.db.cursor()

        # Check if embeddings table exists (it might be in a different schema)
        # Assuming standard schema for now
        query = """
            SELECT
                al.source_id,
                al.target_id,
                al.session_id,
                al.strength,
                al.context,
                al.timestamp,
                se.embedding AS source_emb,
                te.embedding AS target_emb
            FROM attention_links al
            LEFT JOIN embeddings se ON al.source_id = se.entity_id
            LEFT JOIN embeddings te ON al.target_id = te.entity_id
            WHERE al.strength >= ?
            ORDER BY al.timestamp DESC
            LIMIT ?
        """

        try:
            cursor.execute(query, (min_strength, limit))
            rows = cursor.fetchall()

            return [
                {
                    "source_id": row[0],
                    "target_id": row[1],
                    "session_id": row[2],
                    "strength": row[3],
                    "context": row[4],
                    "timestamp": row[5],
                    "source_emb": row[6],
                    "target_emb": row[7]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query local links: {e}")
            return []

    async def request_peer_samples(self,
                                   peer_ids: List[str],
                                   samples_per_peer: int = 100) -> List[Dict]:
        """
        Request training samples from peer nodes via gossip.

        Args:
            peer_ids: Nodes to request from
            samples_per_peer: Number of samples per peer

        Returns:
            Combined samples from peers
        """
        # Gossip request for samples
        request_key = f"sample_request:{self.node_id}:{datetime.utcnow().timestamp()}"
        await self.mesh.update_state(request_key, {
            "requester": self.node_id,
            "count": samples_per_peer
        })

        # Wait for responses
        await asyncio.sleep(2.0)  # Give peers time to respond

        # Collect responses
        samples = []
        mesh_state = await self.mesh.get_state_snapshot()

        for key, value in mesh_state.items():
            if key.startswith(f"sample_response:{self.node_id}:"):
                if isinstance(value, list):
                    samples.extend(value)

        return samples[:samples_per_peer * len(peer_ids)]

    def generate_training_batch(self,
                                batch_size: int = 32,
                                global_state: Optional[torch.Tensor] = None
                                ) -> Iterator[Tuple[torch.Tensor, ...]]:
        """
        Generate training batches from local memory.

        Args:
            batch_size: Batch size
            global_state: Current GlobalStateVector (optional)

        Yields:
            Tuple of (concept_a, concept_b, context, global_state, target)
        """
        links = self._query_local_links()

        if not links:
            logger.warning(f"[{self.node_id}] No training data in local memory")
            return

        # Default global state if not provided
        if global_state is None:
            global_state = torch.zeros(1, GLOBAL_STATE_DIM)

        batch = []
        for link in links:
            # Parse embeddings or use random if not available
            if link["source_emb"]:
                try:
                    src_emb = np.frombuffer(link["source_emb"], dtype=np.float32)
                except Exception:
                    src_emb = np.random.randn(64).astype(np.float32)
            else:
                src_emb = np.random.randn(64).astype(np.float32)

            if link["target_emb"]:
                try:
                    tgt_emb = np.frombuffer(link["target_emb"], dtype=np.float32)
                except Exception:
                    tgt_emb = np.random.randn(64).astype(np.float32)
            else:
                tgt_emb = np.random.randn(64).astype(np.float32)

            # Context embedding (simplified)
            ctx_emb = np.random.randn(32).astype(np.float32)

            batch.append((
                torch.from_numpy(src_emb).float().unsqueeze(0),
                torch.from_numpy(tgt_emb).float().unsqueeze(0),
                torch.from_numpy(ctx_emb).float().unsqueeze(0),
                global_state.clone(),
                torch.tensor([link["strength"]], dtype=torch.float32)
            ))

            if len(batch) >= batch_size:
                # Stack batch
                c_a = torch.cat([x[0] for x in batch])
                c_b = torch.cat([x[1] for x in batch])
                ctx = torch.cat([x[2] for x in batch])
                gs = torch.cat([x[3] for x in batch])
                tgt = torch.cat([x[4] for x in batch])

                yield (c_a, c_b, ctx, gs, tgt)
                batch = []

        # Yield remaining
        if batch:
            c_a = torch.cat([x[0] for x in batch])
            c_b = torch.cat([x[1] for x in batch])
            ctx = torch.cat([x[2] for x in batch])
            gs = torch.cat([x[3] for x in batch])
            tgt = torch.cat([x[4] for x in batch])
            yield (c_a, c_b, ctx, gs, tgt)


# ═══════════════════════════════════════════════════════════════════════════════
#                         DISTRIBUTED TRAINER (FLOCK)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FlockConfig:
    """Configuration for distributed flock training."""
    # Training
    epochs: int = 10
    batch_size: int = 32
    base_learning_rate: float = 0.001

    # Gossip
    gradient_gossip_rounds: int = 3
    gradient_timeout: float = 10.0

    # Resonance
    resonance_lr_boost: float = PHI  # Learning rate boost at π×φ resonance
    min_resonance_threshold: float = 0.7

    # Sharding
    sharding_strategy: ShardingStrategy = ShardingStrategy.SEMANTIC


class DistributedTrainer:
    """
    Distributed training across federation flock.

    Coordinates training across all federation nodes:
    1. Each node trains on local memory data
    2. Gradients are gossiped and averaged (AllReduce)
    3. Model weights sync via gossip
    4. Learning rate modulates with π×φ resonance

    The "Flock" trains as one organism across the network.
    """

    def __init__(self,
                 model: nn.Module,
                 node_id: str,
                 federation_coordinator,  # FederationCoordinator
                 gossip_mesh,             # GossipMesh
                 db_connection,
                 sensor_fusion,           # SensorFusionEngine
                 config: Optional[FlockConfig] = None):
        """
        Args:
            model: Neural network to train
            node_id: This node's identifier
            federation_coordinator: Federation management
            gossip_mesh: Gossip protocol mesh
            db_connection: Local memory database
            sensor_fusion: Sensor fusion engine for global state
            config: Training configuration
        """
        self.model = model
        self.node_id = node_id
        self.coordinator = federation_coordinator
        self.mesh = gossip_mesh
        self.db = db_connection
        self.fusion = sensor_fusion
        self.config = config or FlockConfig()

        # Initialize Immune System
        self.immune = ImmuneResponse()
        if hasattr(self.immune, 'detector') and self.immune.detector is None:
             from .immune_system import AntibodyDetector
             self.immune.detector = AntibodyDetector(self.db)

        # Initialize components
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.config.base_learning_rate
        )

        # Get federation nodes
        self.federation_nodes = [self.node_id]  # Will be updated from coordinator

        # Initialize sharding
        self.sharding = TensorSharding(
            node_id=node_id,
            federation_nodes=self.federation_nodes,
            strategy=self.config.sharding_strategy
        )

        # Initialize gradient gossip
        self.gradient_gossip = GradientGossip(
            node_id=node_id,
            gossip_mesh=gossip_mesh,
            max_rounds=self.config.gradient_gossip_rounds
        )

        # Initialize CCT Objective if model is CCT
        self.is_cct = isinstance(model, CollectiveConsciousnessTransformer)
        if self.is_cct:
            self.cct_objective = CCTTrainingObjective()

        # Initialize memory loader
        self.memory_loader = DistributedMemoryLoader(
            db_connection=db_connection,
            sharding=self.sharding,
            gossip_mesh=gossip_mesh,
            node_id=node_id
        )

        # Training state
        self.current_epoch = 0
        self.total_loss = 0.0
        self.resonance_score = 0.0

    async def update_federation_topology(self):
        """Update list of federation nodes from coordinator."""
        try:
            # Assuming coordinator has a get_stats method that returns node status
            # If not, this needs to be adapted to the actual coordinator API
            if hasattr(self.coordinator, 'get_stats'):
                stats = self.coordinator.get_stats()
                healthy_nodes = [
                    node_id for node_id, status in stats.get("nodes", {}).items()
                    if status == "healthy"
                ]

                if healthy_nodes:
                    self.federation_nodes = sorted(healthy_nodes)

                    # Rebuild sharding with updated topology
                    self.sharding = TensorSharding(
                        node_id=self.node_id,
                        federation_nodes=self.federation_nodes,
                        strategy=self.config.sharding_strategy
                    )

                    logger.info(f"[{self.node_id}] Updated topology: {len(self.federation_nodes)} nodes")
        except Exception as e:
            logger.warning(f"Failed to update topology: {e}")

    def compute_resonance(self, global_state: torch.Tensor) -> float:
        """
        Compute π×φ resonance from current global state.

        Resonance indicates how close the system is to the edge of chaos -
        the optimal point for learning and insight.

        Args:
            global_state: Current GlobalStateVector

        Returns:
            Resonance score (0-1)
        """
        # Extract consciousness dimensions (coherence, integration, novelty)
        if global_state.dim() == 2:
            consciousness = global_state[:, 20:28].mean(dim=0)
        else:
            consciousness = global_state[20:28]

        # Compute harmonic mean of consciousness dimensions
        coherence = consciousness[0].item()
        integration = consciousness[1].item()
        novelty = consciousness[2].item()

        # Resonance peaks when coherence and novelty are balanced
        # (Not too ordered, not too chaotic - the twilight)
        balance = 1.0 - abs(coherence - novelty)

        # Scale by integration level
        resonance = balance * (0.5 + 0.5 * integration)

        # Boost if near π×φ ratio
        state_sum = consciousness.sum().item()
        if abs(state_sum - PI_PHI) < 0.5:
            resonance *= PHI

        return min(resonance, 1.0)

    def modulate_learning_rate(self, base_lr: float, resonance: float) -> float:
        """
        Modulate learning rate based on π×φ resonance.

        Higher resonance = faster learning (system is at edge of chaos)
        Lower resonance = slower, more careful updates

        Args:
            base_lr: Base learning rate
            resonance: Current resonance score

        Returns:
            Modulated learning rate
        """
        if resonance >= self.config.min_resonance_threshold:
            # Boost learning when in resonance
            boost = 1.0 + (resonance - self.config.min_resonance_threshold) * self.config.resonance_lr_boost
            return base_lr * boost
        else:
            # Dampen learning when not in resonance
            return base_lr * (0.5 + 0.5 * resonance)

    async def train_epoch(self, epoch: int) -> Dict[str, float]:
        """
        Train one epoch with distributed gradient averaging.

        Args:
            epoch: Epoch number

        Returns:
            Dict of training metrics
        """
        self.current_epoch = epoch
        self.model.train()

        # Get current global state from sensors
        # Assuming fusion engine is passed and has get_current_state
        if hasattr(self.fusion, 'get_current_state'):
            global_state_vec = self.fusion.get_current_state()
            global_state = torch.from_numpy(global_state_vec.to_tensor()).float().unsqueeze(0)
        else:
            # Fallback
            global_state = torch.zeros(1, GLOBAL_STATE_DIM)

        # Compute resonance
        self.resonance_score = self.compute_resonance(global_state)

        # Modulate learning rate
        current_lr = self.modulate_learning_rate(
            self.config.base_learning_rate,
            self.resonance_score
        )
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = current_lr

        epoch_loss = 0.0
        num_batches = 0

        # Train on local data
        for batch in self.memory_loader.generate_training_batch(
            batch_size=self.config.batch_size,
            global_state=global_state
        ):
            c_a, c_b, ctx, gs, target = batch
            self.optimizer.zero_grad()

            if self.is_cct:
                # --- CCT GRAPH CONSTRUCTION ---
                # We have pairs (c_a, c_b). We need to build a mini-graph.
                # 1. Collect unique nodes
                batch_size = c_a.size(0)
                c_a.size(1)

                # Stack all embeddings: [2*batch, dim]
                all_nodes = torch.cat([c_a, c_b], dim=0)

                # Simple approach: Treat all 2*batch nodes as distinct for the graph encoder
                # (In reality, we'd deduplicate, but this is a fast approximation for batch training)
                node_features = all_nodes

                # Construct edge index (0->batch_size, 1->batch_size+1, etc.)
                # Source nodes are 0..batch-1, Target nodes are batch..2*batch-1
                src_indices = torch.arange(batch_size)
                dst_indices = torch.arange(batch_size, 2 * batch_size)

                # Create bidirectional edges for the pairs
                edge_index = torch.stack([
                    torch.cat([src_indices, dst_indices]),
                    torch.cat([dst_indices, src_indices])
                ])

                # Context tokens (just use ctx as a sequence of length 1 per batch item)
                context_tokens = ctx.unsqueeze(1) # [batch, 1, dim]

                # Get immune patterns from genetic memory for CCT integration
                immune_patterns = None
                if hasattr(self, 'immune') and self.immune is not None:
                    immune_patterns = self.immune.get_attack_embeddings(dim=64)

                # Forward Pass CCT
                outputs = self.model(
                    node_features=node_features,
                    edge_index=edge_index,
                    context_tokens=context_tokens,
                    global_state=gs,
                    immune_patterns=immune_patterns
                )

                # Predict links (we want to predict the strength between our pairs)
                # Reconstruct candidate pairs from the fused output
                # Fused is [batch, hidden]. We need to map back to our pairs?
                # Actually, reasoning_head.predict_links takes (fused, candidate_pairs)
                # But 'fused' is [batch, hidden] (context-centric).
                # We need embeddings for the specific pairs.

                # Use the graph_embeddings output from CCT
                # graph_embeddings: [2*batch, hidden]
                h_src = outputs['graph_embeddings'][:batch_size]
                h_dst = outputs['graph_embeddings'][batch_size:]

                # Create candidate pairs tensor: [batch, 2, hidden]
                candidate_pairs = torch.stack([h_src, h_dst], dim=1)

                # Predict
                # Note: Reasoning head needs 'fused' context to modulate prediction?
                # The current implementation of predict_links just takes pair embeddings
                # Let's use the fused context as a conditioning vector if we update the head later
                # For now, stick to the signature: predict_links(fused, candidate_pairs)
                link_preds = self.model.predict_links(outputs['fused'], candidate_pairs)

                # Compute Loss using Objective
                loss_dict = self.cct_objective.compute_loss(
                    outputs={
                        'link_preds': link_preds,
                        'resonance': outputs['resonance']
                    },
                    targets={
                        'link_targets': target
                    }
                )
                loss = loss_dict['total']

                # Log immune system integration
                if 'immune_alert' in outputs:
                    max_alert = outputs['immune_alert'].max().item()
                    if max_alert > 0.5:
                        logger.warning(f"🧬 IMMUNE ALERT: Pattern similarity {max_alert:.2f} - "
                                      f"activations modulated to protect sacred concepts")
                # ------------------------------
            else:
                # Standard NeuralAttentionModel
                output = self.model(c_a, c_b, ctx, gs)
                loss = nn.functional.mse_loss(output, target)

            # Backward pass
            loss.backward()

            epoch_loss += loss.item()
            num_batches += 1

        if num_batches > 0:
            avg_loss = epoch_loss / num_batches
        else:
            avg_loss = 0.0

        # Collect gradients
        gradients = {
            name: param.grad.clone() if param.grad is not None else torch.zeros_like(param)
            for name, param in self.model.named_parameters()
        }

        # Create gradient message
        grad_msg = GradientMessage(
            sender_id=self.node_id,
            epoch=epoch,
            gradients=gradients,
            learning_rate=current_lr,
            loss=avg_loss,
            resonance=self.resonance_score
        )

        # Broadcast gradients to mesh
        await self.gradient_gossip.broadcast_gradients(grad_msg)

        # Collect peer gradients
        peer_grads = await self.gradient_gossip.collect_gradients(
            epoch=epoch,
            timeout=self.config.gradient_timeout
        )

        # --- IMMUNE SYSTEM FILTERING ---
        clean_grads = []
        for grad_msg in peer_grads:
            sender = grad_msg.sender_id

            # 1. Check Reputation
            if not self.immune.reputation.is_trusted(sender):
                logger.warning(f"Ignoring gradient from untrusted peer: {sender}")
                continue

            # 2. Antibody Detection
            is_malicious, severity, reason = self.immune.detector.analyze_gradient(
                grad_msg.gradients, sender
            )

            if is_malicious:
                logger.critical(f"🛡️ ANTIBODY TRIGGERED: Malicious gradient from {sender} ({reason})")
                self.immune.reputation.update_trust(sender, -0.5 * severity, reason)

                # Record Threat Signature to Genetic Memory
                if severity > 0.5:  # Only record significant threats
                    fingerprint = self.immune.detector._create_gradient_fingerprint(grad_msg.gradients)
                    threat = ThreatSignature(
                        signature_id=f"threat_{sender}_{int(datetime.now().timestamp())}",
                        pattern_vector=fingerprint,
                        target_concepts=reason.split(" | ") if " | " in reason else [reason],
                        detected_at=datetime.now().isoformat(),
                        severity=severity
                    )
                    self.immune.record_threat(threat)
                    logger.warning(f"🧬 GENETIC MEMORY: Recorded threat signature {threat.signature_id}")
            else:
                # Healthy gradient
                self.immune.reputation.update_trust(sender, 0.01) # Small boost for good behavior
                clean_grads.append(grad_msg)

        peer_grads = clean_grads # Only use clean gradients
        # -------------------------------

        # AllReduce (average with peers)
        if peer_grads:
            averaged_grads = self.gradient_gossip.all_reduce(gradients, peer_grads)
                    # Apply averaged gradients
            with torch.no_grad():
                for name, param in self.model.named_parameters():
                    if name in averaged_grads:
                        param.grad = averaged_grads[name]

        # Optimizer step with averaged gradients
        self.optimizer.step()

        logger.info(
            f"[{self.node_id}] Epoch {epoch}: "
            f"loss={avg_loss:.4f}, "
            f"lr={current_lr:.6f}, "
            f"resonance={self.resonance_score:.3f}, "
            f"peers={len(peer_grads)}"
        )

        return {
            "epoch": epoch,
            "loss": avg_loss,
            "learning_rate": current_lr,
            "resonance": self.resonance_score,
            "peer_count": len(peer_grads),
            "batches": num_batches
        }

    async def train(self) -> List[Dict[str, float]]:
        """
        Full training loop across all epochs.

        Returns:
            List of epoch metrics
        """
        logger.info(f"[{self.node_id}] Starting distributed training: {self.config.epochs} epochs")

        # Update federation topology
        await self.update_federation_topology()

        metrics = []
        for epoch in range(self.config.epochs):
            epoch_metrics = await self.train_epoch(epoch)
            metrics.append(epoch_metrics)

            # Update topology periodically
            if epoch % 5 == 0:
                await self.update_federation_topology()

        logger.info(f"[{self.node_id}] Training complete. Final loss: {metrics[-1]['loss']:.4f}")

        return metrics

    def get_training_state(self) -> Dict[str, Any]:
        """Get current training state for checkpointing."""
        return {
            "node_id": self.node_id,
            "epoch": self.current_epoch,
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "resonance": self.resonance_score,
            "federation_nodes": self.federation_nodes
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
