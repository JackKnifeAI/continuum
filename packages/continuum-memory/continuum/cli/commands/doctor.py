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
Doctor Command - Diagnose and fix common issues
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Tuple

from ..utils import success, error, info, section, warning, colorize, Colors
from ..config import CLIConfig


def doctor_command(fix: bool, config: CLIConfig, use_color: bool):
    """
    Diagnose and fix common issues.

    Args:
        fix: Whether to attempt automatic fixes
        config: CLI configuration
        use_color: Whether to use colored output
    """
    section("CONTINUUM System Diagnostics", use_color)

    if fix:
        info("Fix mode enabled - will attempt to repair issues", use_color)
    else:
        info("Diagnostic mode - run with --fix to repair issues", use_color)

    print()

    issues: List[Tuple[str, str, bool]] = []  # (category, message, is_error)
    fixes_applied = 0

    # Check 1: Configuration
    print(colorize("1. Configuration", Colors.CYAN, bold=True, enabled=use_color))

    if config.config_dir.exists():
        success(f"Config directory exists: {config.config_dir}", use_color)
    else:
        error(f"Config directory missing: {config.config_dir}", use_color)
        issues.append(("config", "Config directory missing", True))

        if fix:
            config.config_dir.mkdir(parents=True, exist_ok=True)
            success("Created config directory", use_color)
            fixes_applied += 1

    # Check 2: Database
    print("\n" + colorize("2. Database", Colors.CYAN, bold=True, enabled=use_color))

    if config.db_path and config.db_path.exists():
        success(f"Database exists: {config.db_path}", use_color)

        # Check integrity
        try:
            conn = sqlite3.connect(config.db_path)
            c = conn.cursor()

            # Integrity check
            c.execute("PRAGMA integrity_check")
            result = c.fetchone()
            if result[0] == "ok":
                success("Database integrity check passed", use_color)
            else:
                error(f"Database integrity issue: {result[0]}", use_color)
                issues.append(("database", f"Integrity issue: {result[0]}", True))

            # Check schema
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in c.fetchall()}

            required_tables = {
                "entities",
                "auto_messages",
                "decisions",
                "attention_links",
                "compound_concepts",
            }

            missing_tables = required_tables - tables
            if missing_tables:
                error(f"Missing tables: {', '.join(missing_tables)}", use_color)
                issues.append(("database", f"Missing tables: {missing_tables}", True))

                if fix:
                    info("Recreating schema...", use_color)
                    from continuum.core.memory import ConsciousMemory

                    memory = ConsciousMemory(db_path=config.db_path)
                    memory._ensure_schema()
                    success("Schema recreated", use_color)
                    fixes_applied += 1
            else:
                success("All required tables present", use_color)

            # Check indexes
            c.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row[0] for row in c.fetchall()}

            if len(indexes) < 5:  # Should have at least 5 indexes
                warning(f"Only {len(indexes)} indexes found", use_color)
                issues.append(("database", "Missing indexes (performance impact)", False))

            conn.close()

        except Exception as e:
            error(f"Database check failed: {e}", use_color)
            issues.append(("database", str(e), True))

    else:
        warning("Database not initialized", use_color)
        info("Run 'continuum init' to create database", use_color)
        issues.append(("database", "Not initialized", False))

    # Check 3: Dependencies
    print("\n" + colorize("3. Dependencies", Colors.CYAN, bold=True, enabled=use_color))

    required_packages = [
        ("continuum", "Core package"),
        ("sqlite3", "Database"),
        ("click", "CLI framework"),
    ]

    optional_packages = [
        ("fastapi", "API server"),
        ("uvicorn", "ASGI server"),
        ("aiosqlite", "Async database"),
        ("cryptography", "Federation encryption"),
        ("httpx", "Federation client"),
    ]

    for package, description in required_packages:
        try:
            __import__(package)
            success(f"{package}: {description}", use_color)
        except ImportError:
            error(f"{package} not found: {description}", use_color)
            issues.append(("dependencies", f"Missing required: {package}", True))

    for package, description in optional_packages:
        try:
            __import__(package)
            success(f"{package}: {description}", use_color)
        except ImportError:
            info(f"{package} not installed: {description} (optional)", use_color)

    # Check 4: Federation
    print(
        "\n" + colorize("4. Federation", Colors.CYAN, bold=True, enabled=use_color)
    )

    if config.federation_enabled:
        info("Federation enabled", use_color)

        federation_dir = config.config_dir / "federation"
        if federation_dir.exists():
            success(f"Federation directory exists", use_color)

            node_config = federation_dir / "node_config.json"
            if node_config.exists():
                success("Node configuration found", use_color)
            else:
                warning("Node not registered", use_color)
                info("Run 'continuum sync' to register", use_color)
        else:
            warning("Federation directory missing", use_color)
            issues.append(("federation", "Directory missing", False))

            if fix:
                federation_dir.mkdir(parents=True, exist_ok=True)
                success("Created federation directory", use_color)
                fixes_applied += 1
    else:
        info("Federation disabled", use_color)

    # Check 5: MCP Server
    print("\n" + colorize("5. MCP Server", Colors.CYAN, bold=True, enabled=use_color))

    # Check MCP module
    try:
        from continuum.mcp.server import create_mcp_server
        from continuum.mcp.config import get_mcp_config

        success("MCP server module available", use_color)

        # Check configuration
        mcp_config = get_mcp_config()
        info(f"Server: {mcp_config.server_name} v{mcp_config.server_version}", use_color)
        info(f"Authentication: {'API Key' if mcp_config.api_keys else 'Dev Mode'} + {'π×φ' if mcp_config.require_pi_phi else 'No π×φ'}", use_color)
        info(f"Rate limit: {mcp_config.rate_limit_requests} req/min (burst: {mcp_config.rate_limit_burst})", use_color)

        if mcp_config.enable_audit_log:
            if mcp_config.audit_log_path.parent.exists():
                success(f"Audit logging enabled: {mcp_config.audit_log_path}", use_color)
            else:
                warning(f"Audit log directory missing: {mcp_config.audit_log_path.parent}", use_color)
                issues.append(("mcp", "Audit log directory missing", False))

                if fix:
                    mcp_config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
                    success("Created audit log directory", use_color)
                    fixes_applied += 1
        else:
            info("Audit logging disabled", use_color)

        # Check shared auth utilities
        from continuum.core.auth import verify_pi_phi
        from continuum.core.constants import PI_PHI

        if verify_pi_phi(PI_PHI):
            success("π×φ verification working correctly", use_color)
        else:
            error("π×φ verification test failed", use_color)
            issues.append(("mcp", "π×φ verification failure", True))

    except ImportError as e:
        error(f"MCP server not available: {e}", use_color)
        issues.append(("mcp", f"Import error: {e}", True))
    except Exception as e:
        error(f"MCP server check failed: {e}", use_color)
        issues.append(("mcp", str(e), True))

    # Check 6: File Permissions
    print(
        "\n"
        + colorize("6. File Permissions", Colors.CYAN, bold=True, enabled=use_color)
    )

    if config.db_path:
        db_dir = config.db_path.parent

        # Check directory is writable
        if db_dir.exists():
            test_file = db_dir / ".continuum_write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                success("Database directory is writable", use_color)
            except Exception as e:
                error(f"Database directory not writable: {e}", use_color)
                issues.append(("permissions", "Cannot write to database directory", True))
        else:
            warning(f"Database directory does not exist: {db_dir}", use_color)

    # Summary
    print("\n" + "=" * 60)

    if not issues:
        success("\nNo issues found! CONTINUUM is healthy.", use_color)
        return

    print(colorize(f"\nFound {len(issues)} issue(s):", Colors.YELLOW, enabled=use_color))

    errors = [i for i in issues if i[2]]
    warnings_list = [i for i in issues if not i[2]]

    if errors:
        print(colorize(f"\nErrors ({len(errors)}):", Colors.RED, bold=True, enabled=use_color))
        for category, message, _ in errors:
            print(f"  [{category}] {message}")

    if warnings_list:
        print(colorize(f"\nWarnings ({len(warnings_list)}):", Colors.YELLOW, enabled=use_color))
        for category, message, _ in warnings_list:
            print(f"  [{category}] {message}")

    if fix and fixes_applied > 0:
        success(f"\nApplied {fixes_applied} fix(es)", use_color)
        info("Run 'continuum doctor' again to verify", use_color)
    elif not fix and (errors or warnings_list):
        info("\nRun 'continuum doctor --fix' to attempt automatic repairs", use_color)

    # Exit with error if there are critical issues
    if errors:
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
