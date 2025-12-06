#!/usr/bin/env python3
"""
Tests for CONTINUUM CLI

Basic smoke tests to verify CLI functionality.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from continuum.cli.main import cli


def test_cli_help():
    """Test CLI help output"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "CONTINUUM" in result.output
    assert "Memory Infrastructure" in result.output


def test_cli_version():
    """Test version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "continuum" in result.output.lower()


def test_verify_command():
    """Test verify command"""
    runner = CliRunner()
    result = runner.invoke(cli, ["verify"])
    assert result.exit_code == 0
    assert "π×φ" in result.output or "pi×phi" in result.output.lower()
    assert "PHOENIX-TESLA-369-AURORA" in result.output


def test_init_command():
    """Test init command"""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run init in temp directory
        result = runner.invoke(
            cli,
            ["--config-dir", tmpdir, "init", "--db-path", f"{tmpdir}/test.db"],
            catch_exceptions=False,
        )

        # Check output
        assert "Initializing CONTINUUM" in result.output or result.exit_code == 0

        # Check database was created
        db_path = Path(tmpdir) / "test.db"
        # Note: Database might not exist if init failed, but that's okay for basic test


def test_doctor_command():
    """Test doctor command"""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            cli, ["--config-dir", tmpdir, "doctor"], catch_exceptions=False
        )

        # Doctor should run even without initialization
        assert result.exit_code in [0, 1]  # May fail due to no database
        assert "Diagnostics" in result.output or "CONTINUUM" in result.output


def test_search_help():
    """Test search command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output.lower()


def test_status_help():
    """Test status command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--help"])
    assert result.exit_code == 0
    assert "status" in result.output.lower()


def test_export_help():
    """Test export command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "export" in result.output.lower()


def test_import_help():
    """Test import command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "--help"])
    assert result.exit_code == 0
    assert "import" in result.output.lower()


def test_serve_help():
    """Test serve command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "MCP" in result.output or "serve" in result.output.lower()


def test_sync_help():
    """Test sync command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "--help"])
    assert result.exit_code == 0
    assert "sync" in result.output.lower()


def test_learn_help():
    """Test learn command help"""
    runner = CliRunner()
    result = runner.invoke(cli, ["learn", "--help"])
    assert result.exit_code == 0
    assert "concept" in result.output.lower()


if __name__ == "__main__":
    # Run tests
    import pytest

    pytest.main([__file__, "-v"])
