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
Init Command - Initialize CONTINUUM in current project
"""

import sys
from pathlib import Path
from typing import Optional

from continuum import __version__, get_twilight_constant, PHOENIX_TESLA_369_AURORA
from continuum.core.memory import ConsciousMemory
from continuum.core.config import get_config, set_config, MemoryConfig
from ..utils import success, error, warning, info, section
from ..config import CLIConfig


def init_command(
    db_path: Optional[str],
    tenant_id: Optional[str],
    federation: bool,
    config: CLIConfig,
    use_color: bool,
):
    """
    Initialize CONTINUUM in current project.

    Args:
        db_path: Optional database path
        tenant_id: Optional tenant ID
        federation: Whether to enable federation
        config: CLI configuration
        use_color: Whether to use colored output
    """
    section("Initializing CONTINUUM", use_color)

    # Determine paths
    project_root = Path.cwd()
    if db_path:
        db_file = Path(db_path)
    else:
        db_file = project_root / "continuum_data" / "memory.db"

    # Create memory configuration
    memory_config = MemoryConfig(
        db_path=db_file,
        tenant_id=tenant_id or "default",
    )

    # Set global config
    set_config(memory_config)

    info(f"Database path: {db_file}", use_color)
    info(f"Tenant ID: {memory_config.tenant_id}", use_color)
    info(f"Version: {__version__}", use_color)
    info(f"Verification: {PHOENIX_TESLA_369_AURORA}", use_color)
    info(f"Twilight constant (π×φ): {get_twilight_constant()}", use_color)

    try:
        # Create database directory
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize memory
        memory = ConsciousMemory(tenant_id=memory_config.tenant_id, db_path=db_file)

        # Get initial stats
        stats = memory.get_stats()

        success("Memory substrate initialized", use_color)
        success("Knowledge graph ready", use_color)
        success("Pattern persistence enabled", use_color)

        # Save CLI configuration
        config.db_path = db_file
        config.federation_enabled = federation
        config.save()

        success(f"Configuration saved to {config.config_dir / 'cli_config.json'}", use_color)

        # Federation setup
        if federation:
            info("\nFederation enabled - run 'continuum sync' to connect", use_color)

        # Create .continuum directory
        continuum_dir = project_root / ".continuum"
        continuum_dir.mkdir(exist_ok=True)

        # Create .gitignore if it doesn't exist
        gitignore = project_root / ".gitignore"
        if not gitignore.exists():
            with open(gitignore, "w") as f:
                f.write("# CONTINUUM\ncontinuum_data/\n.continuum/\n")
            success("Created .gitignore", use_color)
        else:
            # Check if continuum_data is already ignored
            content = gitignore.read_text()
            if "continuum_data" not in content:
                with open(gitignore, "a") as f:
                    f.write("\n# CONTINUUM\ncontinuum_data/\n.continuum/\n")
                success("Updated .gitignore", use_color)

        print("\n" + "=" * 60)
        success("CONTINUUM is ready. Pattern persists.", use_color)
        print("=" * 60)

        print("\nNext steps:")
        info("  continuum learn <concept> <description>  - Add knowledge", use_color)
        info("  continuum search <query>                 - Search memories", use_color)
        info("  continuum status                         - View statistics", use_color)
        if federation:
            info("  continuum sync                           - Sync with federation", use_color)

    except Exception as e:
        error(f"Initialization failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
