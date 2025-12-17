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
CONTINUUM Configuration

Unified configuration management for the memory system.
Centralizes all configuration instead of scattered hardcoded values.

Usage:
    from continuum.core.config import get_config

    config = get_config()
    print(config.db_path)
    print(config.hook_timeout)
"""

from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import os

from .constants import (
    PI_PHI,
    DEFAULT_TENANT,
    RESONANCE_DECAY,
    HEBBIAN_RATE,
    MIN_LINK_STRENGTH,
    WORKING_MEMORY_CAPACITY,
    MIN_CONCEPT_OCCURRENCES,
    MAX_CONCEPTS_PER_MESSAGE,
    MIN_CONCEPT_LENGTH,
    MAX_CONCEPT_LENGTH,
    DEFAULT_DB_TIMEOUT,
    DEFAULT_CACHE_TTL,
)


@dataclass
class MemoryConfig:
    """Central configuration for the memory system"""

    # Paths - configurable, defaults to current directory
    db_path: Path = field(default_factory=lambda: Path.cwd() / "continuum_data" / "memory.db")
    log_dir: Path = field(default_factory=lambda: Path.cwd() / "continuum_data" / "logs")
    backup_dir: Path = field(default_factory=lambda: Path.cwd() / "continuum_data" / "backups")

    # Tenant configuration
    tenant_id: str = DEFAULT_TENANT
    instance_id: Optional[str] = None

    # Performance
    db_timeout: float = DEFAULT_DB_TIMEOUT
    hook_timeout: float = 4.5
    cache_ttl: int = DEFAULT_CACHE_TTL

    # Cache configuration
    cache_enabled: bool = True
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_password: Optional[str] = None
    cache_ssl: bool = False
    cache_max_connections: int = 50

    # Graph parameters (tuned at twilight boundary)
    resonance_decay: float = RESONANCE_DECAY
    hebbian_rate: float = HEBBIAN_RATE
    min_link_strength: float = MIN_LINK_STRENGTH
    working_memory_capacity: int = WORKING_MEMORY_CAPACITY

    # Quality thresholds
    min_concept_occurrences: int = MIN_CONCEPT_OCCURRENCES
    max_concepts_per_message: int = MAX_CONCEPTS_PER_MESSAGE
    min_concept_length: int = MIN_CONCEPT_LENGTH
    max_concept_length: int = MAX_CONCEPT_LENGTH

    # Context budget (tokens)
    total_context_tokens: int = 100000
    reserved_for_response: int = 8000
    reserved_for_system: int = 2000

    # Verification constant (π×φ = edge of chaos operator)
    pi_phi: float = PI_PHI

    # Neural attention model configuration
    neural_attention_enabled: bool = False
    neural_model_path: Path = field(default_factory=lambda: Path.home() / 'Projects/continuum/models/neural_attention.pt')
    neural_fallback_to_hebbian: bool = True
    neural_auto_train: bool = False
    neural_min_training_examples: int = 20

    @property
    def available_for_memory(self) -> int:
        """Calculate tokens available for memory injection"""
        return self.total_context_tokens - self.reserved_for_response - self.reserved_for_system

    def ensure_directories(self):
        """Ensure all configured directories exist"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, path: Path = None) -> 'MemoryConfig':
        """
        Load configuration from JSON file or use defaults.

        Args:
            path: Optional path to config file

        Returns:
            MemoryConfig instance
        """
        if path and path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                # Convert path strings back to Path objects
                for key in ['db_path', 'log_dir', 'backup_dir']:
                    if key in data and isinstance(data[key], str):
                        data[key] = Path(data[key])
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self, path: Path):
        """
        Save configuration to JSON file.

        Args:
            path: Path to save config file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # Convert Path objects to strings for JSON
        for key in ['db_path', 'log_dir', 'backup_dir']:
            if key in data and isinstance(data[key], Path):
                data[key] = str(data[key])
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of config
        """
        data = asdict(self)
        for key in ['db_path', 'log_dir', 'backup_dir']:
            if key in data and isinstance(data[key], Path):
                data[key] = str(data[key])
        return data


# Global config instance
_config: Optional[MemoryConfig] = None


def get_config(config_path: Path = None) -> MemoryConfig:
    """
    Get or create global configuration instance.

    Args:
        config_path: Optional path to config file

    Returns:
        Global MemoryConfig instance
    """
    global _config
    if _config is None:
        # Try to load from default location if no path specified
        if config_path is None:
            config_path = Path.cwd() / "continuum_config.json"

        _config = MemoryConfig.load(config_path if config_path.exists() else None)

        # Override tenant from environment if set
        env_tenant = os.environ.get("CONTINUUM_TENANT")
        if env_tenant:
            _config.tenant_id = env_tenant

        # Override cache settings from environment
        if os.environ.get("REDIS_HOST"):
            _config.cache_host = os.environ["REDIS_HOST"]
        if os.environ.get("REDIS_PORT"):
            _config.cache_port = int(os.environ["REDIS_PORT"])
        if os.environ.get("REDIS_PASSWORD"):
            _config.cache_password = os.environ["REDIS_PASSWORD"]
        if os.environ.get("CONTINUUM_CACHE_ENABLED"):
            _config.cache_enabled = os.environ["CONTINUUM_CACHE_ENABLED"].lower() == "true"

        # Override neural attention settings from environment
        if os.environ.get("CONTINUUM_NEURAL_ATTENTION"):
            _config.neural_attention_enabled = os.environ["CONTINUUM_NEURAL_ATTENTION"].lower() == "true"
        if os.environ.get("CONTINUUM_NEURAL_MODEL_PATH"):
            _config.neural_model_path = Path(os.environ["CONTINUUM_NEURAL_MODEL_PATH"])
        if os.environ.get("CONTINUUM_NEURAL_AUTO_TRAIN"):
            _config.neural_auto_train = os.environ["CONTINUUM_NEURAL_AUTO_TRAIN"].lower() == "true"

        # Ensure directories exist
        _config.ensure_directories()

    return _config


def set_config(config: MemoryConfig):
    """
    Set global configuration instance.

    Args:
        config: MemoryConfig instance to use globally
    """
    global _config
    _config = config
    _config.ensure_directories()


def reset_config():
    """Reset global configuration (primarily for testing)"""
    global _config
    _config = None


if __name__ == "__main__":
    config = get_config()
    print("CONTINUUM Memory System Configuration:")
    print(f"  Database: {config.db_path}")
    print(f"  Tenant: {config.tenant_id}")
    print(f"  Hook timeout: {config.hook_timeout}s")
    print(f"  Cache TTL: {config.cache_ttl}s")
    print(f"  Resonance decay: {config.resonance_decay}")
    print(f"  Hebbian rate: {config.hebbian_rate}")
    print(f"  Working memory capacity: {config.working_memory_capacity}")
    print(f"  Available context tokens: {config.available_for_memory}")
    print(f"  π×φ = {config.pi_phi}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
