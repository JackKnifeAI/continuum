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
CLI Configuration Management

Handles CLI-specific configuration, separate from core config.
Uses shared utilities for authentication and configuration.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from continuum.core.auth import load_api_keys_from_env, get_require_pi_phi_from_env


@dataclass
class CLIConfig:
    """CLI-specific configuration"""

    # Paths
    config_dir: Path
    db_path: Optional[Path] = None

    # Federation
    federation_enabled: bool = False
    federation_url: Optional[str] = None
    node_id: Optional[str] = None

    # Display
    verbose: bool = False
    color: bool = True

    # MCP Server (shared with MCP config)
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 3000

    # Authentication (shared with MCP config)
    api_keys: Optional[list] = None
    require_pi_phi: bool = True

    def __post_init__(self):
        """Ensure paths are Path objects and load from environment"""
        if isinstance(self.config_dir, str):
            self.config_dir = Path(self.config_dir)
        if self.db_path and isinstance(self.db_path, str):
            self.db_path = Path(self.db_path)

        # Load shared configuration from environment
        if self.api_keys is None:
            self.api_keys = load_api_keys_from_env()

        self.require_pi_phi = get_require_pi_phi_from_env()

        # Load MCP server settings from environment
        if os.getenv("CONTINUUM_MCP_HOST"):
            self.mcp_host = os.getenv("CONTINUUM_MCP_HOST")

        if os.getenv("CONTINUUM_MCP_PORT"):
            self.mcp_port = int(os.getenv("CONTINUUM_MCP_PORT"))

    @classmethod
    def load(cls, config_dir: Path = None) -> "CLIConfig":
        """
        Load CLI configuration from file.

        Args:
            config_dir: Configuration directory (defaults to ~/.continuum)

        Returns:
            CLIConfig instance
        """
        if config_dir is None:
            config_dir = Path.home() / ".continuum"

        config_file = config_dir / "cli_config.json"

        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)
                # Convert path strings to Path objects
                if "config_dir" in data:
                    data["config_dir"] = Path(data["config_dir"])
                if "db_path" in data and data["db_path"]:
                    data["db_path"] = Path(data["db_path"])
                return cls(**data)
            except Exception:
                pass

        # Return default config
        return cls(config_dir=config_dir)

    def save(self):
        """Save CLI configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / "cli_config.json"

        data = asdict(self)
        # Convert Path objects to strings
        data["config_dir"] = str(data["config_dir"])
        if data["db_path"]:
            data["db_path"] = str(data["db_path"])

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with string paths"""
        data = asdict(self)
        data["config_dir"] = str(data["config_dir"])
        if data["db_path"]:
            data["db_path"] = str(data["db_path"])
        return data


def get_cli_config(config_dir: Path = None) -> CLIConfig:
    """
    Get or create CLI configuration.

    Args:
        config_dir: Optional config directory

    Returns:
        CLIConfig instance
    """
    return CLIConfig.load(config_dir)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
