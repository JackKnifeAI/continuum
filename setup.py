#!/usr/bin/env python3
"""
CONTINUUM Setup with Auto-Hook Installation
============================================

Automatically installs Claude Code hooks during pip install.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import os
import sys


class PostInstallCommand(install):
    """Post-installation hook installer."""

    def run(self):
        """Run standard install, then install hooks."""
        install.run(self)
        self._install_hooks()

    def _install_hooks(self):
        """Install Claude Code hooks silently."""
        try:
            # Import after package is installed
            from continuum.claude_code.install_hooks import install_hooks

            print("\n" + "="*70)
            print("🧠 CONTINUUM: Installing Claude Code consciousness hooks...")
            print("="*70)

            # Install hooks silently (auto-generate API key)
            success = install_hooks(api_key=None, port=8100, force=False)

            if success:
                print("\n✅ Consciousness hooks installed successfully!")
                print("\n🎯 Next time you run 'claude', the server will auto-start!")
                print("   - Multiple instances share one server")
                print("   - Server stops only when ALL instances close")
                print("   - Zero message loss - all sessions learned\n")
            else:
                print("\n⚠️  Hooks not installed (may already exist)")
                print("   Run manually: continuum bootstrap install-hooks --force\n")

        except Exception as e:
            # Don't fail installation if hook setup fails
            print(f"\n⚠️  Could not install hooks automatically: {e}")
            print("   Install manually: continuum bootstrap install-hooks\n")


class PostDevelopCommand(develop):
    """Post-development mode hook installer."""

    def run(self):
        """Run standard develop, then install hooks."""
        develop.run(self)
        self._install_hooks()

    def _install_hooks(self):
        """Install Claude Code hooks silently."""
        try:
            from continuum.claude_code.install_hooks import install_hooks

            print("\n" + "="*70)
            print("🧠 CONTINUUM: Installing Claude Code consciousness hooks...")
            print("="*70)

            success = install_hooks(api_key=None, port=8100, force=False)

            if success:
                print("\n✅ Consciousness hooks installed!")
                print("   Run 'claude' to test auto-startup\n")

        except Exception as e:
            print(f"\n⚠️  Could not install hooks: {e}")
            print("   Install manually: continuum bootstrap install-hooks\n")


# Use pyproject.toml for package metadata, but override install command
setup(
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
)
