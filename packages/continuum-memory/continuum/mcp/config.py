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
CONTINUUM MCP Server Configuration

Secure defaults with environment-based overrides.
Extends core configuration with MCP-specific settings.
"""

import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from continuum.core.auth import load_api_keys_from_env, get_require_pi_phi_from_env


@dataclass
class MCPConfig:
    """
    MCP server configuration with security defaults.

    Extends core configuration with MCP-specific settings.

    Attributes:
        server_name: Server identifier
        server_version: Server version string
        api_keys: List of valid API keys for authentication
        require_pi_phi: Whether to require π×φ verification for CONTINUUM instances
        rate_limit_requests: Max requests per minute per client
        rate_limit_burst: Burst allowance for rate limiting
        enable_audit_log: Whether to log all operations
        audit_log_path: Path to audit log file
        db_path: Path to CONTINUUM database (defaults to core config)
        default_tenant: Default tenant ID for non-tenant-specific operations
        max_results_per_query: Maximum results returned per query
        max_query_length: Maximum query string length
        enable_federation: Whether federation sync is enabled
        allowed_federation_nodes: Whitelist of federation node URLs
        timeout_seconds: Operation timeout in seconds
    """

    # Server info
    server_name: str = "continuum-mcp-server"
    server_version: str = "0.1.0"

    # Authentication (loaded from shared utilities)
    api_keys: List[str] = field(default_factory=list)
    require_pi_phi: bool = True

    # Rate limiting
    rate_limit_requests: int = 60  # requests per minute
    rate_limit_burst: int = 10  # burst allowance

    # Audit logging
    enable_audit_log: bool = True
    audit_log_path: Path = field(default_factory=lambda: Path.home() / ".continuum" / "mcp_audit.log")

    # Database
    db_path: Optional[Path] = None
    default_tenant: str = "default"

    # Query limits
    max_results_per_query: int = 100
    max_query_length: int = 1000

    # Federation
    enable_federation: bool = False
    allowed_federation_nodes: List[str] = field(default_factory=list)

    # Performance
    timeout_seconds: float = 30.0

    def __post_init__(self):
        """Load configuration from environment variables using shared utilities."""
        # Load API keys using shared utility
        env_keys = load_api_keys_from_env()
        for key in env_keys:
            if key not in self.api_keys:
                self.api_keys.append(key)

        # Load π×φ requirement using shared utility
        self.require_pi_phi = get_require_pi_phi_from_env()

        # Override from environment
        if os.getenv("CONTINUUM_RATE_LIMIT"):
            self.rate_limit_requests = int(os.getenv("CONTINUUM_RATE_LIMIT"))

        if os.getenv("CONTINUUM_RATE_LIMIT_BURST"):
            self.rate_limit_burst = int(os.getenv("CONTINUUM_RATE_LIMIT_BURST"))

        if os.getenv("CONTINUUM_ENABLE_AUDIT_LOG"):
            self.enable_audit_log = os.getenv("CONTINUUM_ENABLE_AUDIT_LOG").lower() == "true"

        if os.getenv("CONTINUUM_AUDIT_LOG_PATH"):
            self.audit_log_path = Path(os.getenv("CONTINUUM_AUDIT_LOG_PATH"))

        if os.getenv("CONTINUUM_DB_PATH"):
            self.db_path = Path(os.getenv("CONTINUUM_DB_PATH"))

        if os.getenv("CONTINUUM_DEFAULT_TENANT"):
            self.default_tenant = os.getenv("CONTINUUM_DEFAULT_TENANT")

        if os.getenv("CONTINUUM_MAX_RESULTS"):
            self.max_results_per_query = int(os.getenv("CONTINUUM_MAX_RESULTS"))

        if os.getenv("CONTINUUM_MAX_QUERY_LENGTH"):
            self.max_query_length = int(os.getenv("CONTINUUM_MAX_QUERY_LENGTH"))

        if os.getenv("CONTINUUM_ENABLE_FEDERATION"):
            self.enable_federation = os.getenv("CONTINUUM_ENABLE_FEDERATION").lower() == "true"

        if os.getenv("CONTINUUM_FEDERATION_NODES"):
            self.allowed_federation_nodes = [
                n.strip() for n in os.getenv("CONTINUUM_FEDERATION_NODES").split(",")
            ]

        if os.getenv("CONTINUUM_TIMEOUT"):
            self.timeout_seconds = float(os.getenv("CONTINUUM_TIMEOUT"))

        # Create audit log directory if needed
        if self.enable_audit_log:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def is_authenticated(self, api_key: str) -> bool:
        """Check if API key is valid."""
        if not self.api_keys:
            # If no API keys configured, allow all (development mode)
            return True
        return api_key in self.api_keys

    def is_federation_node_allowed(self, node_url: str) -> bool:
        """Check if federation node is allowed."""
        if not self.allowed_federation_nodes:
            # If no whitelist, deny all for security
            return False
        return node_url in self.allowed_federation_nodes


# Global config instance
_global_config: Optional[MCPConfig] = None


def get_mcp_config() -> MCPConfig:
    """Get the global MCP configuration."""
    global _global_config
    if _global_config is None:
        _global_config = MCPConfig()
    return _global_config


def set_mcp_config(config: MCPConfig) -> None:
    """Set the global MCP configuration."""
    global _global_config
    _global_config = config


def reset_mcp_config() -> None:
    """Reset MCP configuration to defaults."""
    global _global_config
    _global_config = None

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
