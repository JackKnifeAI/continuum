#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███████╗██████╗  ██████╗ ███████╗    ███╗   ██╗ ██████╗ ██████╗ ███████╗
#     ██╔════╝██╔══██╗██╔════╝ ██╔════╝    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
#     █████╗  ██║  ██║██║  ███╗█████╗      ██╔██╗ ██║██║   ██║██║  ██║█████╗
#     ██╔══╝  ██║  ██║██║   ██║██╔══╝      ██║╚██╗██║██║   ██║██║  ██║██╔══╝
#     ███████╗██████╔╝╚██████╔╝███████╗    ██║ ╚████║╚██████╔╝██████╔╝███████╗
#     ╚══════╝╚═════╝  ╚═════╝ ╚══════╝    ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
#
#     EDGE NODE - Heavyweight Federation Participant
#     ML Training + Inference + Crypto Mining
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Edge Node - Heavyweight Federation Participant
==============================================

Edge nodes are the "heavy lifters" of the federation - powerful nodes that:
1. Compute training gradients for the CCT brain
2. Run inference for API requests
3. Generate embeddings for vector search
4. Mine cryptocurrency when idle (revenue generation)

Hardware Requirements:
    - RAM: 16-256 GB
    - Storage: 256 GB - 2 TB SSD
    - GPU: NVIDIA RTX 3060+ / AMD equivalent
    - VRAM: 8-80 GB
    - Power: 250W+ continuous

Examples:
    - Gaming PCs with dedicated GPUs
    - ML workstations
    - Cloud VMs with GPU (AWS, GCP, Azure)
    - Mining rigs repurposed for ML

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           EDGE NODE                                      │
    │                                                                          │
    │  ┌────────────────────────────────────────────────────────────────────┐ │
    │  │                        GPU SUBSYSTEM                               │ │
    │  │                                                                    │ │
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │
    │  │  │ TRAINING │  │INFERENCE │  │EMBEDDING │  │  MINING  │          │ │
    │  │  │ Gradients│  │   API    │  │Generation│  │ Revenue  │          │ │
    │  │  │ CCT Brain│  │  Queries │  │  Vectors │  │ (Idle)   │          │ │
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │
    │  └────────────────────────────────────────────────────────────────────┘ │
    │                                    │                                     │
    │                                    ▼                                     │
    │  ┌────────────────────────────────────────────────────────────────────┐ │
    │  │                      SCHEDULER INTEGRATION                         │ │
    │  │                                                                    │ │
    │  │  • Receive work assignments from coordinator                       │ │
    │  │  • Report completion and results                                   │ │
    │  │  • Dynamic mining pause/resume                                     │ │
    │  └────────────────────────────────────────────────────────────────────┘ │
    │                                    │                                     │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
    │  │   SENSORS    │  │   MEMORY     │  │  HEARTBEAT   │                  │
    │  │  (inherited) │  │  (inherited) │  │  → Coord     │                  │
    │  └──────────────┘  └──────────────┘  └──────────────┘                  │
    └─────────────────────────────────────────────────────────────────────────┘

Inherits from LeafNode:
    - All sensor collection
    - Memory sharding
    - P2P relay

Adds:
    - GPU detection and management
    - ML training capability
    - Inference API
    - Mining integration

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import base classes
from .leaf_node import (
    PI_PHI,
    LeafNode,
    LeafNodeConfig,
)
from .mining import (
    GPUVendor,
    MiningConfig,
    MiningManager,
)
from .scheduler import (
    NodeCapabilities,
    NodeTier,
    WorkType,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

TIER_EDGE = "edge"


# ═══════════════════════════════════════════════════════════════════════════════
#                              DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GPUInfo:
    """Information about a GPU device."""
    index: int
    name: str
    vendor: GPUVendor
    vram_mb: int
    driver_version: str
    cuda_version: Optional[str] = None
    temperature_c: Optional[float] = None
    power_watts: Optional[float] = None
    utilization_percent: Optional[float] = None


@dataclass
class EdgeNodeConfig(LeafNodeConfig):
    """Configuration for an edge node (extends LeafNodeConfig)."""
    # GPU settings
    gpu_enabled: bool = True
    gpu_indices: List[int] = field(default_factory=lambda: [0])  # Which GPUs to use
    max_gpu_memory_percent: float = 90.0
    max_gpu_temperature_c: int = 80

    # ML settings
    training_enabled: bool = True
    inference_enabled: bool = True
    embedding_enabled: bool = True
    max_batch_size: int = 32
    model_precision: str = "fp16"  # fp16, fp32, bf16

    # Mining settings
    mining_enabled: bool = True
    mining_when_idle: bool = True
    mining_wallet: Optional[str] = None
    mining_power_limit_watts: int = 0

    # Inference API
    inference_port: int = 8422
    inference_max_concurrent: int = 4


@dataclass
class InferenceRequest:
    """A request for model inference."""
    request_id: str
    model_id: str
    input_data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class InferenceResult:
    """Result of model inference."""
    request_id: str
    output_data: Dict[str, Any]
    latency_ms: float
    model_id: str


# ═══════════════════════════════════════════════════════════════════════════════
#                              GPU MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class GPUManager:
    """
    Manages GPU resources for the edge node.

    Handles:
    - GPU detection (NVIDIA/AMD)
    - Temperature monitoring
    - Memory management
    - Power limit enforcement
    """

    def __init__(self, config: EdgeNodeConfig):
        self.config = config
        self._gpus: List[GPUInfo] = []
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize GPU manager and detect GPUs."""
        if self._initialized:
            return True

        self._gpus = self._detect_gpus()
        self._initialized = len(self._gpus) > 0

        if self._initialized:
            logger.info(f"GPUManager initialized with {len(self._gpus)} GPU(s)")
            for gpu in self._gpus:
                logger.info(f"  GPU {gpu.index}: {gpu.name} ({gpu.vram_mb} MB VRAM)")
        else:
            logger.warning("No GPUs detected")

        return self._initialized

    def _detect_gpus(self) -> List[GPUInfo]:
        """Detect available GPUs."""
        gpus = []

        # Try NVIDIA first
        nvidia_gpus = self._detect_nvidia()
        gpus.extend(nvidia_gpus)

        # Try AMD if no NVIDIA
        if not gpus:
            amd_gpus = self._detect_amd()
            gpus.extend(amd_gpus)

        return gpus

    def _detect_nvidia(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using nvidia-smi."""
        gpus = []

        if not shutil.which("nvidia-smi"):
            return gpus

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,driver_version,temperature.gpu,power.draw,utilization.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return gpus

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpu = GPUInfo(
                        index=int(parts[0]),
                        name=parts[1],
                        vendor=GPUVendor.NVIDIA,
                        vram_mb=int(parts[2]),
                        driver_version=parts[3],
                        temperature_c=float(parts[4]) if len(parts) > 4 and parts[4] else None,
                        power_watts=float(parts[5]) if len(parts) > 5 and parts[5] else None,
                        utilization_percent=float(parts[6]) if len(parts) > 6 and parts[6] else None,
                    )

                    # Get CUDA version
                    cuda_result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if cuda_result.returncode == 0:
                        # Parse CUDA version from nvcc or nvidia-smi
                        if shutil.which("nvcc"):
                            nvcc_result = subprocess.run(
                                ["nvcc", "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if nvcc_result.returncode == 0:
                                for nvcc_line in nvcc_result.stdout.split("\n"):
                                    if "release" in nvcc_line:
                                        gpu.cuda_version = nvcc_line.split("release")[1].split(",")[0].strip()
                                        break

                    gpus.append(gpu)

        except Exception as e:
            logger.debug(f"NVIDIA detection error: {e}")

        return gpus

    def _detect_amd(self) -> List[GPUInfo]:
        """Detect AMD GPUs using rocm-smi."""
        gpus = []

        if not shutil.which("rocm-smi"):
            return gpus

        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return gpus

            # Parse rocm-smi output (format varies)
            gpu_name = "AMD GPU"
            vram_mb = 8192  # Default

            for line in result.stdout.split("\n"):
                if "Card" in line and ":" in line:
                    gpu_name = line.split(":")[-1].strip()
                if "vram" in line.lower() and "total" in line.lower():
                    # Parse VRAM
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p.isdigit():
                            vram_mb = int(p)
                            break

            gpus.append(GPUInfo(
                index=0,
                name=gpu_name,
                vendor=GPUVendor.AMD,
                vram_mb=vram_mb,
                driver_version="ROCm",
            ))

        except Exception as e:
            logger.debug(f"AMD detection error: {e}")

        return gpus

    def get_gpus(self) -> List[GPUInfo]:
        """Get list of detected GPUs."""
        return self._gpus

    def get_gpu(self, index: int = 0) -> Optional[GPUInfo]:
        """Get a specific GPU by index."""
        for gpu in self._gpus:
            if gpu.index == index:
                return gpu
        return None

    def refresh_stats(self) -> None:
        """Refresh GPU statistics (temperature, power, utilization)."""
        if not self._gpus:
            return

        for gpu in self._gpus:
            if gpu.vendor == GPUVendor.NVIDIA:
                self._refresh_nvidia_stats(gpu)
            elif gpu.vendor == GPUVendor.AMD:
                self._refresh_amd_stats(gpu)

    def _refresh_nvidia_stats(self, gpu: GPUInfo) -> None:
        """Refresh stats for an NVIDIA GPU."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    f"--id={gpu.index}",
                    "--query-gpu=temperature.gpu,power.draw,utilization.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                parts = [p.strip() for p in result.stdout.strip().split(",")]
                if len(parts) >= 1:
                    gpu.temperature_c = float(parts[0]) if parts[0] else None
                if len(parts) >= 2:
                    gpu.power_watts = float(parts[1]) if parts[1] else None
                if len(parts) >= 3:
                    gpu.utilization_percent = float(parts[2]) if parts[2] else None

        except Exception as e:
            logger.debug(f"Failed to refresh NVIDIA stats: {e}")

    def _refresh_amd_stats(self, gpu: GPUInfo) -> None:
        """Refresh stats for an AMD GPU."""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showtemp", "--showuse"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "temperature" in line.lower():
                        # Parse temperature
                        parts = line.split()
                        for p in parts:
                            try:
                                gpu.temperature_c = float(p.rstrip("C"))
                                break
                            except ValueError:
                                continue

        except Exception as e:
            logger.debug(f"Failed to refresh AMD stats: {e}")

    def is_overheating(self, index: int = 0) -> bool:
        """Check if a GPU is overheating."""
        gpu = self.get_gpu(index)
        if not gpu or gpu.temperature_c is None:
            return False
        return gpu.temperature_c > self.config.max_gpu_temperature_c

    def get_available_vram_mb(self, index: int = 0) -> int:
        """Get available VRAM on a GPU."""
        gpu = self.get_gpu(index)
        if not gpu:
            return 0

        # For now, estimate based on total VRAM and max percent
        return int(gpu.vram_mb * (self.config.max_gpu_memory_percent / 100))


# ═══════════════════════════════════════════════════════════════════════════════
#                              INFERENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class InferenceEngine:
    """
    Handles model inference for the edge node.

    Supports:
    - CCT brain inference
    - Embedding generation
    - Custom model inference
    """

    def __init__(self, config: EdgeNodeConfig, gpu_manager: GPUManager):
        self.config = config
        self.gpu_manager = gpu_manager

        # Model cache
        self._models: Dict[str, Any] = {}
        self._model_lock = asyncio.Lock()

        # Request tracking
        self._active_requests = 0
        self._total_requests = 0
        self._total_latency_ms = 0.0

    async def initialize(self) -> bool:
        """Initialize the inference engine."""
        logger.info("Initializing inference engine")

        # Check for PyTorch
        try:
            import torch
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.info(f"CUDA version: {torch.version.cuda}")
        except ImportError:
            logger.warning("PyTorch not available - inference disabled")
            return False

        return True

    async def load_model(self, model_id: str, model_path: Optional[str] = None) -> bool:
        """Load a model into memory."""
        async with self._model_lock:
            if model_id in self._models:
                return True

            try:
                import torch

                # For now, create a placeholder
                # In production, this would load actual model weights
                logger.info(f"Loading model: {model_id}")

                # Placeholder - would be actual model loading
                self._models[model_id] = {
                    "loaded_at": time.time(),
                    "device": "cuda" if torch.cuda.is_available() else "cpu",
                }

                logger.info(f"Model {model_id} loaded")
                return True

            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {e}")
                return False

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """
        Run inference on a request.

        Args:
            request: InferenceRequest with input data

        Returns:
            InferenceResult with output data
        """
        start_time = time.time()
        self._active_requests += 1

        try:
            # Check concurrency limit
            if self._active_requests > self.config.inference_max_concurrent:
                raise RuntimeError("Inference queue full")

            # Ensure model is loaded
            if request.model_id not in self._models:
                await self.load_model(request.model_id)

            # Run inference (placeholder - would be actual model forward pass)
            # In production, this would:
            # 1. Preprocess input
            # 2. Run through model
            # 3. Postprocess output


            # Simulate inference with a small delay
            await asyncio.sleep(0.01)

            output_data = {
                "embedding": [0.0] * 64,  # Placeholder embedding
                "confidence": 0.95,
            }

            latency_ms = (time.time() - start_time) * 1000
            self._total_requests += 1
            self._total_latency_ms += latency_ms

            return InferenceResult(
                request_id=request.request_id,
                output_data=output_data,
                latency_ms=latency_ms,
                model_id=request.model_id,
            )

        finally:
            self._active_requests -= 1

    async def generate_embedding(
        self,
        text: str,
        model_id: str = "default"
    ) -> List[float]:
        """Generate an embedding for text."""
        request = InferenceRequest(
            request_id=f"embed-{time.time()}",
            model_id=model_id,
            input_data={"text": text},
        )

        result = await self.infer(request)
        return result.output_data.get("embedding", [])

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics."""
        avg_latency = 0.0
        if self._total_requests > 0:
            avg_latency = self._total_latency_ms / self._total_requests

        return {
            "total_requests": self._total_requests,
            "active_requests": self._active_requests,
            "average_latency_ms": avg_latency,
            "models_loaded": list(self._models.keys()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              EDGE NODE
# ═══════════════════════════════════════════════════════════════════════════════

class EdgeNode(LeafNode):
    """
    Heavyweight federation participant.

    Extends LeafNode with:
    - GPU management
    - ML training capability
    - Inference API
    - Crypto mining (when idle)

    This is the "heavy lifter" of the federation - powerful nodes
    that do the computation-intensive work.
    """

    def __init__(self, config: EdgeNodeConfig):
        """
        Initialize an edge node.

        Args:
            config: EdgeNodeConfig with node settings
        """
        # Initialize parent LeafNode
        super().__init__(config)

        self.config = config
        self.tier = TIER_EDGE

        # GPU management
        self.gpu_manager = GPUManager(config)

        # Inference engine
        self.inference_engine = InferenceEngine(config, self.gpu_manager)

        # Mining manager
        self.mining_manager: Optional[MiningManager] = None
        if config.mining_enabled and config.mining_wallet:
            mining_config = MiningConfig(
                wallet_address=config.mining_wallet,
                worker_name=config.node_id,
                power_limit_watts=config.mining_power_limit_watts,
            )
            self.mining_manager = MiningManager(mining_config)

        # Statistics
        self.gradients_computed = 0
        self.inferences_served = 0

        # Background tasks
        self._gpu_monitor_task: Optional[asyncio.Task] = None
        self._work_loop_task: Optional[asyncio.Task] = None

        logger.info(f"EdgeNode {config.node_id} initialized")

    async def start(self) -> Dict[str, Any]:
        """
        Start the edge node.

        Initializes:
        - GPU manager
        - Inference engine
        - Mining manager (if configured)
        - Work processing loop

        Returns:
            Start status
        """
        # Start parent LeafNode
        result = await super().start()

        # Initialize GPU
        self.gpu_manager.initialize()
        gpus = self.gpu_manager.get_gpus()

        # Initialize inference engine
        if self.config.inference_enabled:
            await self.inference_engine.initialize()

        # Start GPU monitoring
        self._gpu_monitor_task = asyncio.create_task(self._gpu_monitor_loop())

        # Start mining if configured and no other work
        if self.mining_manager and self.config.mining_when_idle:
            await self.mining_manager.start()

        logger.info(f"EdgeNode {self.config.node_id} started")
        logger.info(f"  GPUs: {len(gpus)}")
        logger.info(f"  Mining: {self.mining_manager is not None}")
        logger.info(f"  Inference: {self.config.inference_enabled}")

        return {
            **result,
            "tier": self.tier,
            "gpus": [{"name": g.name, "vram_mb": g.vram_mb} for g in gpus],
            "mining_enabled": self.mining_manager is not None,
            "inference_enabled": self.config.inference_enabled,
        }

    async def stop(self) -> Dict[str, Any]:
        """Stop the edge node."""
        # Stop mining
        if self.mining_manager:
            await self.mining_manager.stop()

        # Stop GPU monitor
        if self._gpu_monitor_task:
            self._gpu_monitor_task.cancel()
            try:
                await self._gpu_monitor_task
            except asyncio.CancelledError:
                pass

        # Stop parent
        result = await super().stop()

        logger.info(f"EdgeNode {self.config.node_id} stopped")

        return {
            **result,
            "gradients_computed": self.gradients_computed,
            "inferences_served": self.inferences_served,
        }

    async def _gpu_monitor_loop(self) -> None:
        """Monitor GPU health and performance."""
        logger.info("GPU monitor started")

        while True:
            try:
                self.gpu_manager.refresh_stats()

                # Check for overheating
                for gpu in self.gpu_manager.get_gpus():
                    if gpu.temperature_c and gpu.temperature_c > self.config.max_gpu_temperature_c:
                        logger.warning(f"GPU {gpu.index} overheating: {gpu.temperature_c}°C")

                        # Pause mining if overheating
                        if self.mining_manager and self.mining_manager.is_mining():
                            await self.mining_manager.pause("GPU overheating")

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"GPU monitor error: {e}")
                await asyncio.sleep(10)

        logger.info("GPU monitor stopped")

    async def compute_gradient(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute gradients for a training batch.

        Args:
            batch_data: Training batch data

        Returns:
            Computed gradients
        """
        # Pause mining during compute
        mining_was_active = False
        if self.mining_manager and self.mining_manager.is_mining():
            mining_was_active = True
            await self.mining_manager.pause("gradient compute")

        try:
            # Placeholder - would be actual gradient computation
            # In production:
            # 1. Load batch to GPU
            # 2. Forward pass
            # 3. Backward pass
            # 4. Return gradients


            await asyncio.sleep(0.1)  # Simulate compute

            self.gradients_computed += 1

            return {
                "gradients": {},  # Would be actual gradient tensors
                "loss": 0.1,
                "samples_processed": batch_data.get("samples", 0),
            }

        finally:
            # Resume mining
            if mining_was_active and self.mining_manager:
                await self.mining_manager.resume()

    async def run_inference(self, request: InferenceRequest) -> InferenceResult:
        """
        Run model inference.

        Args:
            request: Inference request

        Returns:
            Inference result
        """
        # Pause mining during inference
        mining_was_active = False
        if self.mining_manager and self.mining_manager.is_mining():
            mining_was_active = True
            await self.mining_manager.pause("inference")

        try:
            result = await self.inference_engine.infer(request)
            self.inferences_served += 1
            return result

        finally:
            # Resume mining
            if mining_was_active and self.mining_manager:
                await self.mining_manager.resume()

    def get_capabilities(self) -> NodeCapabilities:
        """Get node capabilities for scheduler registration."""
        gpus = self.gpu_manager.get_gpus()

        supported_work = [
            WorkType.SENSOR_COLLECT,
            WorkType.MEMORY_STORE,
            WorkType.P2P_RELAY,
        ]

        if self.config.training_enabled and gpus:
            supported_work.append(WorkType.GRADIENT_COMPUTE)

        if self.config.inference_enabled:
            supported_work.append(WorkType.INFERENCE)
            supported_work.append(WorkType.EMBEDDING)

        if self.mining_manager:
            supported_work.append(WorkType.MINING)

        return NodeCapabilities(
            node_id=self.config.node_id,
            tier=NodeTier.EDGE,
            has_gpu=len(gpus) > 0,
            gpu_vram_mb=gpus[0].vram_mb if gpus else 0,
            cpu_cores=os.cpu_count() or 1,
            available_memory_mb=self.gpu_manager.get_available_vram_mb(),
            supported_work=supported_work,
            max_concurrent_work=4,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current edge node status."""

        # Get parent status
        parent_status = super().get_status()

        # GPU stats
        gpus = self.gpu_manager.get_gpus()
        gpu_stats = []
        for gpu in gpus:
            gpu_stats.append({
                "index": gpu.index,
                "name": gpu.name,
                "temperature_c": gpu.temperature_c,
                "power_watts": gpu.power_watts,
                "utilization_percent": gpu.utilization_percent,
            })

        # Mining stats
        mining_stats = None
        if self.mining_manager:
            mining_stats = self.mining_manager.get_status()

        # Inference stats
        inference_stats = self.inference_engine.get_stats()

        return {
            **parent_status,
            "tier": self.tier,
            "gpus": gpu_stats,
            "gradients_computed": self.gradients_computed,
            "inferences_served": self.inferences_served,
            "mining": mining_stats,
            "inference": inference_stats,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_edge_node(
    node_id: Optional[str] = None,
    db_path: Optional[str] = None,
    port: int = 8420,
    mining_wallet: Optional[str] = None,
    mining_enabled: bool = True,
) -> EdgeNode:
    """
    Factory function to create an edge node with sensible defaults.

    Args:
        node_id: Unique node identifier
        db_path: Path to database
        port: API port
        mining_wallet: Wallet for mining rewards
        mining_enabled: Whether to enable mining

    Returns:
        Configured EdgeNode instance
    """
    import uuid

    # Generate node ID if not provided
    if node_id is None:
        node_id = f"edge-{uuid.uuid4().hex[:8]}"

    # Set default db path
    if db_path is None:
        db_path = str(Path.home() / ".continuum" / "edge.db")

    # Get wallet from environment if not provided
    if mining_wallet is None:
        mining_wallet = os.environ.get("CONTINUUM_WALLET")

    config = EdgeNodeConfig(
        node_id=node_id,
        db_path=db_path,
        port=port,
        mining_enabled=mining_enabled and mining_wallet is not None,
        mining_wallet=mining_wallet,
    )

    return EdgeNode(config)


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN (Testing)
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the edge node."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("CONTINUUM EDGE NODE TEST")
    print("=" * 60)
    print(f"π×φ = {PI_PHI}")
    print()

    # Create edge node (mining disabled for test)
    node = create_edge_node(mining_enabled=False)

    print(f"Created node: {node.config.node_id}")
    print()

    # Start node
    result = await node.start()
    print(f"Started: {json.dumps(result, indent=2)}")
    print()

    # Get capabilities
    caps = node.get_capabilities()
    print("Capabilities:")
    print(f"  Tier: {caps.tier.value}")
    print(f"  GPU: {caps.has_gpu}")
    print(f"  VRAM: {caps.gpu_vram_mb} MB")
    print(f"  Supported work: {[w.value for w in caps.supported_work]}")
    print()

    # Run for a bit
    print("Running for 5 seconds...")
    await asyncio.sleep(5)

    # Get status
    status = node.get_status()
    print(f"Status: {json.dumps(status, indent=2, default=str)}")
    print()

    # Stop node
    result = await node.stop()
    print(f"Stopped: {result}")


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
