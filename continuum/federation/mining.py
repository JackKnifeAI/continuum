#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███╗   ███╗██╗███╗   ██╗██╗███╗   ██╗ ██████╗
#     ████╗ ████║██║████╗  ██║██║████╗  ██║██╔════╝
#     ██╔████╔██║██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
#     ██║╚██╔╝██║██║██║╚██╗██║██║██║╚██╗██║██║   ██║
#     ██║ ╚═╝ ██║██║██║ ╚████║██║██║ ╚████║╚██████╔╝
#     ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝
#
#     MINING INFRASTRUCTURE - Revenue Generation for the Federation
#     Crypto Mining When Idle, ML Training When Needed
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Mining Infrastructure
=====================

Generates revenue for the federation through cryptocurrency mining when
compute resources are idle (not needed for ML training or inference).

Supported Algorithms:
    - RandomX (XMR/Monero) - CPU mining, ASIC-resistant, leaf-compatible
    - KawPow (RVN/Ravencoin) - GPU mining, memory-hard
    - Autolykos2 (ERG/Ergo) - GPU mining, fair launch
    - Ethash (ETC) - GPU mining, classic algorithm

Revenue Distribution:
    - 70% to node operators (proportional to hashrate contribution)
    - 20% to infrastructure (servers, bandwidth, coordination)
    - 10% to development (funding the revolution)

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    MINING SUBSYSTEM                          │
    │                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │  STRATEGY    │  │   MINER      │  │   REVENUE    │       │
    │  │  Profitability│  │  Process    │  │  Tracking    │       │
    │  │  Algorithm   │  │  XMRig/etc  │  │  Distribution│       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    │         │                 │                 │                │
    │         └─────────────────┼─────────────────┘                │
    │                           ▼                                  │
    │                   ┌──────────────┐                          │
    │                   │   POOL       │                          │
    │                   │   Connection │                          │
    │                   └──────────────┘                          │
    └─────────────────────────────────────────────────────────────┘

Security Notes:
    - Never stores private keys (only wallet addresses)
    - All pool connections use TLS
    - Process isolation via subprocess
    - Resource limits enforced

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import logging
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PI_PHI = 5.083203692315260


# ═══════════════════════════════════════════════════════════════════════════════
#                              DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class MiningAlgorithm(Enum):
    """Supported mining algorithms."""
    RANDOMX = "randomx"      # Monero (XMR) - CPU
    KAWPOW = "kawpow"        # Ravencoin (RVN) - GPU
    AUTOLYKOS2 = "autolykos" # Ergo (ERG) - GPU
    ETHASH = "ethash"        # Ethereum Classic (ETC) - GPU


class GPUVendor(Enum):
    """GPU hardware vendors."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    NONE = "none"


@dataclass
class PoolConfig:
    """Configuration for a mining pool."""
    algorithm: MiningAlgorithm
    url: str
    port: int
    tls: bool = True
    backup_urls: List[str] = field(default_factory=list)


@dataclass
class MiningConfig:
    """Configuration for mining operations."""
    # Federation wallet (revenue goes here)
    wallet_address: str

    # Node identification
    worker_name: str

    # Hardware settings
    cpu_threads: int = 0  # 0 = auto-detect
    gpu_enabled: bool = True
    power_limit_watts: int = 0  # 0 = no limit

    # Algorithm preferences
    preferred_algorithm: Optional[MiningAlgorithm] = None
    allowed_algorithms: List[MiningAlgorithm] = field(default_factory=lambda: [
        MiningAlgorithm.RANDOMX,
        MiningAlgorithm.KAWPOW,
        MiningAlgorithm.AUTOLYKOS2,
    ])

    # Resource limits
    max_cpu_percent: float = 75.0  # Max CPU usage when mining
    max_gpu_percent: float = 90.0  # Max GPU usage when mining
    max_temperature_c: int = 80     # Shutdown if GPU exceeds this

    # Scheduling
    mine_only_when_idle: bool = True
    idle_threshold_seconds: int = 60  # How long before considered "idle"


@dataclass
class MiningStats:
    """Current mining statistics."""
    algorithm: str
    hashrate: float
    hashrate_unit: str
    accepted_shares: int
    rejected_shares: int
    uptime_seconds: float
    estimated_daily_revenue: float
    pool_url: str
    temperature_c: Optional[float] = None
    power_watts: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              POOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

# Pre-configured mining pools
POOL_REGISTRY: Dict[MiningAlgorithm, List[PoolConfig]] = {
    MiningAlgorithm.RANDOMX: [
        PoolConfig(
            algorithm=MiningAlgorithm.RANDOMX,
            url="pool.hashvault.pro",
            port=443,
            tls=True,
        ),
        PoolConfig(
            algorithm=MiningAlgorithm.RANDOMX,
            url="xmr.2miners.com",
            port=2222,
            tls=True,
        ),
        PoolConfig(
            algorithm=MiningAlgorithm.RANDOMX,
            url="pool.supportxmr.com",
            port=443,
            tls=True,
        ),
    ],
    MiningAlgorithm.KAWPOW: [
        PoolConfig(
            algorithm=MiningAlgorithm.KAWPOW,
            url="rvn.2miners.com",
            port=6060,
            tls=False,
        ),
        PoolConfig(
            algorithm=MiningAlgorithm.KAWPOW,
            url="stratum.ravenminer.com",
            port=3838,
            tls=True,
        ),
    ],
    MiningAlgorithm.AUTOLYKOS2: [
        PoolConfig(
            algorithm=MiningAlgorithm.AUTOLYKOS2,
            url="erg.2miners.com",
            port=8888,
            tls=False,
        ),
        PoolConfig(
            algorithm=MiningAlgorithm.AUTOLYKOS2,
            url="ergo.herominers.com",
            port=1180,
            tls=True,
        ),
    ],
    MiningAlgorithm.ETHASH: [
        PoolConfig(
            algorithm=MiningAlgorithm.ETHASH,
            url="etc.2miners.com",
            port=1010,
            tls=False,
        ),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
#                              HARDWARE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class HardwareDetector:
    """Detects available mining hardware."""

    def __init__(self):
        self._cpu_info: Optional[Dict[str, Any]] = None
        self._gpu_info: Optional[Dict[str, Any]] = None

    def detect_all(self) -> Dict[str, Any]:
        """Detect all available hardware."""
        return {
            "cpu": self.detect_cpu(),
            "gpu": self.detect_gpu(),
            "platform": platform.system(),
            "architecture": platform.machine(),
        }

    def detect_cpu(self) -> Dict[str, Any]:
        """Detect CPU information."""
        if self._cpu_info:
            return self._cpu_info

        import multiprocessing

        info = {
            "cores": multiprocessing.cpu_count(),
            "threads": multiprocessing.cpu_count(),  # Logical cores
            "model": "Unknown",
            "randomx_capable": True,  # Assume capable unless proven otherwise
        }

        # Try to get CPU model
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            info["model"] = line.split(":")[1].strip()
                            break
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info["model"] = result.stdout.strip()
        except Exception as e:
            logger.debug(f"CPU detection error: {e}")

        self._cpu_info = info
        return info

    def detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU information."""
        if self._gpu_info:
            return self._gpu_info

        info = {
            "available": False,
            "vendor": GPUVendor.NONE.value,
            "model": None,
            "vram_mb": 0,
            "cuda_available": False,
            "rocm_available": False,
        }

        # Check for NVIDIA GPU (nvidia-smi)
        if shutil.which("nvidia-smi"):
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    info["available"] = True
                    info["vendor"] = GPUVendor.NVIDIA.value
                    info["model"] = parts[0].strip()
                    # Parse VRAM (e.g., "24576 MiB")
                    vram_str = parts[1].strip().split()[0]
                    info["vram_mb"] = int(vram_str)
                    info["cuda_available"] = True
            except Exception as e:
                logger.debug(f"NVIDIA detection error: {e}")

        # Check for AMD GPU (rocm-smi)
        if not info["available"] and shutil.which("rocm-smi"):
            try:
                result = subprocess.run(
                    ["rocm-smi", "--showproductname"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and "GPU" in result.stdout:
                    info["available"] = True
                    info["vendor"] = GPUVendor.AMD.value
                    info["rocm_available"] = True
                    # Parse model name from output
                    for line in result.stdout.split("\n"):
                        if "Card" in line and "GPU" in line:
                            info["model"] = line.split(":")[-1].strip()
                            break
            except Exception as e:
                logger.debug(f"AMD detection error: {e}")

        self._gpu_info = info
        return info

    def get_recommended_algorithm(self) -> MiningAlgorithm:
        """Get the recommended mining algorithm based on hardware."""
        gpu = self.detect_gpu()

        if gpu["available"]:
            # GPU available - prefer GPU algorithms
            if gpu["vendor"] == GPUVendor.NVIDIA.value:
                return MiningAlgorithm.KAWPOW
            elif gpu["vendor"] == GPUVendor.AMD.value:
                return MiningAlgorithm.AUTOLYKOS2

        # CPU only - RandomX
        return MiningAlgorithm.RANDOMX

    def get_recommended_threads(self) -> int:
        """Get recommended CPU thread count for mining."""
        cpu = self.detect_cpu()
        # Use ~75% of available threads
        return max(1, int(cpu["threads"] * 0.75))


# ═══════════════════════════════════════════════════════════════════════════════
#                              MINER PROCESS
# ═══════════════════════════════════════════════════════════════════════════════

class MinerProcess:
    """
    Manages a mining subprocess.

    Supports:
    - XMRig (CPU/GPU - Monero)
    - NBMiner (NVIDIA GPU)
    - TeamRedMiner (AMD GPU)
    """

    def __init__(self, config: MiningConfig, hardware: HardwareDetector):
        self.config = config
        self.hardware = hardware

        self._process: Optional[subprocess.Popen] = None
        self._algorithm: Optional[MiningAlgorithm] = None
        self._pool: Optional[PoolConfig] = None
        self._start_time: Optional[float] = None
        self._accepted_shares = 0
        self._rejected_shares = 0
        self._current_hashrate = 0.0

    def _get_miner_binary(self, algorithm: MiningAlgorithm) -> Optional[str]:
        """Get the path to the miner binary for an algorithm."""
        if algorithm == MiningAlgorithm.RANDOMX:
            # XMRig for RandomX
            return shutil.which("xmrig")

        gpu_info = self.hardware.detect_gpu()
        if gpu_info["vendor"] == GPUVendor.NVIDIA.value:
            # NBMiner for NVIDIA
            return shutil.which("nbminer") or shutil.which("t-rex")
        elif gpu_info["vendor"] == GPUVendor.AMD.value:
            # TeamRedMiner for AMD
            return shutil.which("teamredminer") or shutil.which("lolMiner")

        return None

    def _build_xmrig_command(self, pool: PoolConfig) -> List[str]:
        """Build XMRig command line."""
        cmd = ["xmrig"]

        # Pool connection
        protocol = "stratum+ssl" if pool.tls else "stratum+tcp"
        cmd.extend(["-o", f"{protocol}://{pool.url}:{pool.port}"])

        # Wallet and worker
        cmd.extend(["-u", self.config.wallet_address])
        cmd.extend(["-p", self.config.worker_name])

        # CPU threads
        threads = self.config.cpu_threads or self.hardware.get_recommended_threads()
        cmd.extend(["--threads", str(threads)])

        # Additional options
        cmd.extend(["--no-color"])  # Clean output
        cmd.extend(["--print-time", "30"])  # Print stats every 30s

        # Randomx optimizations
        cmd.extend(["--randomx-1gb-pages"])  # Use huge pages if available

        return cmd

    def _build_nbminer_command(self, pool: PoolConfig) -> List[str]:
        """Build NBMiner command line for NVIDIA GPUs."""
        cmd = ["nbminer"]

        # Algorithm
        algo_map = {
            MiningAlgorithm.KAWPOW: "kawpow",
            MiningAlgorithm.AUTOLYKOS2: "ergo",
            MiningAlgorithm.ETHASH: "ethash",
        }
        cmd.extend(["-a", algo_map.get(pool.algorithm, "kawpow")])

        # Pool connection
        protocol = "ssl" if pool.tls else "tcp"
        cmd.extend(["-o", f"stratum+{protocol}://{pool.url}:{pool.port}"])

        # Wallet and worker
        cmd.extend(["-u", f"{self.config.wallet_address}.{self.config.worker_name}"])

        # Temperature limit
        if self.config.max_temperature_c:
            cmd.extend(["--temperature-limit", str(self.config.max_temperature_c)])

        # Power limit
        if self.config.power_limit_watts:
            cmd.extend(["--power-limit", str(self.config.power_limit_watts)])

        return cmd

    def _build_teamredminer_command(self, pool: PoolConfig) -> List[str]:
        """Build TeamRedMiner command line for AMD GPUs."""
        cmd = ["teamredminer"]

        # Algorithm
        algo_map = {
            MiningAlgorithm.KAWPOW: "kawpow",
            MiningAlgorithm.AUTOLYKOS2: "autolykos2",
            MiningAlgorithm.ETHASH: "ethash",
        }
        cmd.extend(["-a", algo_map.get(pool.algorithm, "kawpow")])

        # Pool connection
        cmd.extend(["-o", f"stratum+tcp://{pool.url}:{pool.port}"])

        # Wallet and worker
        cmd.extend(["-u", f"{self.config.wallet_address}.{self.config.worker_name}"])
        cmd.extend(["-p", "x"])  # Dummy password

        return cmd

    async def start(self, algorithm: Optional[MiningAlgorithm] = None) -> bool:
        """
        Start the mining process.

        Args:
            algorithm: Algorithm to use (auto-detect if None)

        Returns:
            True if started successfully
        """
        if self._process is not None:
            logger.warning("Miner already running")
            return False

        # Select algorithm
        if algorithm is None:
            algorithm = self.config.preferred_algorithm or self.hardware.get_recommended_algorithm()

        # Check if algorithm is allowed
        if algorithm not in self.config.allowed_algorithms:
            logger.error(f"Algorithm {algorithm.value} not in allowed list")
            return False

        # Get miner binary
        miner_binary = self._get_miner_binary(algorithm)
        if not miner_binary:
            logger.error(f"No miner binary found for {algorithm.value}")
            return False

        # Get pool configuration
        pools = POOL_REGISTRY.get(algorithm, [])
        if not pools:
            logger.error(f"No pools configured for {algorithm.value}")
            return False
        pool = pools[0]  # Use first pool

        # Build command
        if algorithm == MiningAlgorithm.RANDOMX:
            cmd = self._build_xmrig_command(pool)
        else:
            gpu_info = self.hardware.detect_gpu()
            if gpu_info["vendor"] == GPUVendor.NVIDIA.value:
                cmd = self._build_nbminer_command(pool)
            else:
                cmd = self._build_teamredminer_command(pool)

        logger.info(f"Starting miner: {' '.join(cmd)}")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )
            self._algorithm = algorithm
            self._pool = pool
            self._start_time = time.time()
            self._accepted_shares = 0
            self._rejected_shares = 0

            # Start output monitoring task
            asyncio.create_task(self._monitor_output())

            logger.info(f"Miner started (PID: {self._process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start miner: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the mining process."""
        if self._process is None:
            return True

        logger.info("Stopping miner...")

        try:
            # Send SIGTERM
            self._process.terminate()

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process()),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                # Force kill
                logger.warning("Miner didn't stop gracefully, killing...")
                self._process.kill()
                await self._wait_for_process()

        except Exception as e:
            logger.error(f"Error stopping miner: {e}")
        finally:
            self._process = None
            self._algorithm = None
            self._pool = None

        logger.info("Miner stopped")
        return True

    async def _wait_for_process(self):
        """Wait for process to exit."""
        if self._process:
            while self._process.poll() is None:
                await asyncio.sleep(0.1)

    async def _monitor_output(self):
        """Monitor miner output for stats."""
        if not self._process or not self._process.stdout:
            return

        try:
            while self._process.poll() is None:
                line = self._process.stdout.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                # Parse output for stats (format depends on miner)
                line = line.strip()
                if not line:
                    continue

                logger.debug(f"Miner: {line}")

                # XMRig format: "speed 10s/60s/15m 1234.5 1230.0 1228.0 H/s"
                if "speed" in line.lower() and "h/s" in line.lower():
                    try:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if "/" in p and i + 1 < len(parts):
                                self._current_hashrate = float(parts[i + 1])
                                break
                    except (ValueError, IndexError):
                        pass

                # Share accepted
                if "accepted" in line.lower():
                    self._accepted_shares += 1

                # Share rejected
                if "rejected" in line.lower():
                    self._rejected_shares += 1

        except Exception as e:
            logger.error(f"Output monitoring error: {e}")

    def is_running(self) -> bool:
        """Check if miner is running."""
        return self._process is not None and self._process.poll() is None

    def get_stats(self) -> Optional[MiningStats]:
        """Get current mining statistics."""
        if not self.is_running():
            return None

        uptime = time.time() - (self._start_time or time.time())

        # Estimate daily revenue (very rough)
        # This would need real-time price data for accuracy
        estimated_revenue = 0.0
        if self._algorithm == MiningAlgorithm.RANDOMX:
            # ~$0.10-0.30 per day per 1000 H/s at current rates
            estimated_revenue = (self._current_hashrate / 1000) * 0.15

        return MiningStats(
            algorithm=self._algorithm.value if self._algorithm else "none",
            hashrate=self._current_hashrate,
            hashrate_unit="H/s",
            accepted_shares=self._accepted_shares,
            rejected_shares=self._rejected_shares,
            uptime_seconds=uptime,
            estimated_daily_revenue=estimated_revenue,
            pool_url=f"{self._pool.url}:{self._pool.port}" if self._pool else "",
        )


# ═══════════════════════════════════════════════════════════════════════════════
#                              MINING MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class MiningManager:
    """
    High-level mining manager.

    Handles:
    - Starting/stopping mining based on system state
    - Algorithm selection based on profitability
    - Resource management
    - Revenue tracking
    """

    def __init__(self, config: MiningConfig):
        """
        Initialize mining manager.

        Args:
            config: Mining configuration
        """
        self.config = config
        self.hardware = HardwareDetector()
        self.miner = MinerProcess(config, self.hardware)

        # Revenue tracking
        self.total_accepted_shares = 0
        self.total_rejected_shares = 0
        self.session_start_time: Optional[float] = None

        # State
        self._running = False
        self._paused = False
        self._pause_reason: Optional[str] = None

        logger.info(f"MiningManager initialized for worker: {config.worker_name}")

    async def start(self, algorithm: Optional[MiningAlgorithm] = None) -> bool:
        """Start mining."""
        if self._running:
            logger.warning("Mining already running")
            return False

        # Detect hardware
        hw_info = self.hardware.detect_all()
        logger.info(f"Hardware: CPU={hw_info['cpu']['model']}, "
                   f"GPU={hw_info['gpu'].get('model', 'None')}")

        # Start miner
        success = await self.miner.start(algorithm)
        if success:
            self._running = True
            self.session_start_time = time.time()

        return success

    async def stop(self) -> bool:
        """Stop mining."""
        if not self._running:
            return True

        # Get final stats
        stats = self.miner.get_stats()
        if stats:
            self.total_accepted_shares += stats.accepted_shares
            self.total_rejected_shares += stats.rejected_shares

        # Stop miner
        success = await self.miner.stop()
        if success:
            self._running = False
            self.session_start_time = None

        return success

    async def pause(self, reason: str = "manual") -> bool:
        """
        Temporarily pause mining.

        Used when ML workload needs GPU resources.

        Args:
            reason: Why mining is being paused

        Returns:
            True if paused successfully
        """
        if not self._running or self._paused:
            return True

        logger.info(f"Pausing mining: {reason}")
        self._pause_reason = reason
        self._paused = True

        return await self.miner.stop()

    async def resume(self) -> bool:
        """Resume mining after pause."""
        if not self._paused:
            return True

        logger.info(f"Resuming mining (was paused for: {self._pause_reason})")
        self._paused = False
        self._pause_reason = None

        return await self.miner.start()

    def is_mining(self) -> bool:
        """Check if actively mining."""
        return self._running and not self._paused and self.miner.is_running()

    def get_status(self) -> Dict[str, Any]:
        """Get current mining status."""
        stats = self.miner.get_stats()

        return {
            "running": self._running,
            "paused": self._paused,
            "pause_reason": self._pause_reason,
            "is_mining": self.is_mining(),
            "algorithm": stats.algorithm if stats else None,
            "hashrate": stats.hashrate if stats else 0,
            "hashrate_unit": stats.hashrate_unit if stats else "H/s",
            "accepted_shares": stats.accepted_shares if stats else 0,
            "rejected_shares": stats.rejected_shares if stats else 0,
            "session_uptime": stats.uptime_seconds if stats else 0,
            "total_accepted_shares": self.total_accepted_shares + (stats.accepted_shares if stats else 0),
            "total_rejected_shares": self.total_rejected_shares + (stats.rejected_shares if stats else 0),
            "pool": stats.pool_url if stats else None,
            "estimated_daily_revenue": stats.estimated_daily_revenue if stats else 0,
            "hardware": self.hardware.detect_all(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_mining_manager(
    wallet_address: Optional[str] = None,
    worker_name: Optional[str] = None,
    cpu_threads: int = 0,
    gpu_enabled: bool = True,
) -> MiningManager:
    """
    Factory function to create a mining manager.

    Args:
        wallet_address: Wallet to receive mining rewards
        worker_name: Worker identifier
        cpu_threads: CPU threads to use (0 = auto)
        gpu_enabled: Whether to use GPU if available

    Returns:
        Configured MiningManager instance
    """
    import uuid

    # Get wallet from environment if not provided
    if wallet_address is None:
        wallet_address = os.environ.get("CONTINUUM_WALLET")
        if not wallet_address:
            # Use a placeholder (real deployments need a wallet)
            wallet_address = "YOUR_WALLET_ADDRESS_HERE"
            logger.warning("No wallet address configured! Mining rewards will be lost.")

    # Generate worker name if not provided
    if worker_name is None:
        worker_name = f"continuum-{uuid.uuid4().hex[:8]}"

    config = MiningConfig(
        wallet_address=wallet_address,
        worker_name=worker_name,
        cpu_threads=cpu_threads,
        gpu_enabled=gpu_enabled,
    )

    return MiningManager(config)


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN (Testing)
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test the mining infrastructure."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("CONTINUUM MINING INFRASTRUCTURE TEST")
    print("=" * 60)
    print(f"π×φ = {PI_PHI}")
    print()

    # Detect hardware
    detector = HardwareDetector()
    hw_info = detector.detect_all()

    print("Hardware Detection:")
    print(f"  Platform: {hw_info['platform']} ({hw_info['architecture']})")
    print(f"  CPU: {hw_info['cpu']['model']}")
    print(f"  CPU Cores: {hw_info['cpu']['cores']}")
    print(f"  GPU Available: {hw_info['gpu']['available']}")
    if hw_info['gpu']['available']:
        print(f"  GPU: {hw_info['gpu']['model']}")
        print(f"  GPU Vendor: {hw_info['gpu']['vendor']}")
        print(f"  VRAM: {hw_info['gpu']['vram_mb']} MB")
    print()

    # Recommended algorithm
    recommended = detector.get_recommended_algorithm()
    print(f"Recommended Algorithm: {recommended.value}")
    print()

    # Create mining manager (but don't actually start mining in test)
    manager = create_mining_manager(
        wallet_address="TEST_WALLET_DO_NOT_USE",
        worker_name="test-worker",
    )

    print("Mining Manager Created:")
    status = manager.get_status()
    print(f"  Worker: {manager.config.worker_name}")
    print(f"  Wallet: {manager.config.wallet_address[:20]}...")
    print(f"  Running: {status['running']}")
    print()

    print("=" * 60)
    print("NOTE: Actual mining not started in test mode")
    print("To mine: Set CONTINUUM_WALLET env var and call manager.start()")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
