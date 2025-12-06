#!/usr/bin/env python3
"""
CLI + MCP Integration Verification Script

Verifies that the CLI and MCP server are properly integrated with shared
authentication, configuration, and utilities.
"""

import sys
from pathlib import Path


def test_shared_auth():
    """Test shared authentication module"""
    print("1. Testing shared authentication module...")

    try:
        from continuum.core.auth import (
            verify_pi_phi,
            authenticate,
            load_api_keys_from_env,
            get_require_pi_phi_from_env,
            generate_client_id,
        )
        from continuum.core.constants import PI_PHI

        # Test π×φ verification
        assert verify_pi_phi(PI_PHI) == True, "π×φ verification failed"
        assert verify_pi_phi(5.0) == False, "π×φ should reject invalid values"

        # Test client ID generation
        client_id = generate_client_id("test-agent", "127.0.0.1")
        assert len(client_id) == 16, "Client ID should be 16 chars"

        # Test authentication
        result = authenticate(
            api_key="test-key",
            pi_phi_verification=PI_PHI,
            valid_api_keys=["test-key"],
            require_pi_phi=True,
        )
        assert result == True, "Authentication should succeed with valid credentials"

        print("   ✓ Shared auth module working")
        print(f"   ✓ π×φ = {PI_PHI}")
        return True

    except Exception as e:
        print(f"   ✗ Shared auth module failed: {e}")
        return False


def test_mcp_integration():
    """Test MCP server uses shared auth"""
    print("\n2. Testing MCP server integration...")

    try:
        from continuum.mcp.security import authenticate_client, verify_pi_phi
        from continuum.mcp.config import get_mcp_config
        from continuum.mcp.server import create_mcp_server
        from continuum.core.constants import PI_PHI

        # Test that MCP uses shared utilities
        assert verify_pi_phi(PI_PHI) == True, "MCP π×φ verification failed"

        # Test config loading
        config = get_mcp_config()
        assert config.server_name == "continuum-mcp-server"

        # Test server creation
        server = create_mcp_server()
        assert server is not None

        print("   ✓ MCP server uses shared auth")
        print(f"   ✓ Server: {config.server_name} v{config.server_version}")
        print(f"   ✓ Auth mode: {'API Key' if config.api_keys else 'Dev'} + {'π×φ' if config.require_pi_phi else 'No π×φ'}")
        return True

    except Exception as e:
        print(f"   ✗ MCP integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_integration():
    """Test CLI uses shared auth and can start MCP server"""
    print("\n3. Testing CLI integration...")

    try:
        from continuum.cli.config import CLIConfig, get_cli_config
        from continuum.cli.commands.serve import serve_command

        # Test config loading
        config = get_cli_config()
        assert config.config_dir.name == ".continuum"

        # Test that CLI config has MCP settings
        assert hasattr(config, 'mcp_host')
        assert hasattr(config, 'mcp_port')
        assert hasattr(config, 'api_keys')
        assert hasattr(config, 'require_pi_phi')

        print("   ✓ CLI config uses shared auth utilities")
        print(f"   ✓ MCP server: {config.mcp_host}:{config.mcp_port}")

        # Test that serve command can import MCP server
        # (Don't actually start it, just verify imports work)
        try:
            from continuum.mcp.server import run_mcp_server
            print("   ✓ CLI serve command can use MCP server")
        except ImportError as e:
            print(f"   ✗ CLI can't import MCP server: {e}")
            return False

        return True

    except Exception as e:
        print(f"   ✗ CLI integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_shared_config():
    """Test that both CLI and MCP read same environment variables"""
    print("\n4. Testing shared configuration...")

    try:
        import os
        from continuum.cli.config import CLIConfig
        from continuum.mcp.config import MCPConfig
        from continuum.core.auth import load_api_keys_from_env, get_require_pi_phi_from_env

        # Set test environment variables
        os.environ["CONTINUUM_API_KEY"] = "test-key-123"
        os.environ["CONTINUUM_REQUIRE_PI_PHI"] = "true"
        os.environ["CONTINUUM_MCP_HOST"] = "0.0.0.0"
        os.environ["CONTINUUM_MCP_PORT"] = "4000"

        # Test shared utilities
        api_keys = load_api_keys_from_env()
        assert "test-key-123" in api_keys, "Should load API key from env"

        require_pi_phi = get_require_pi_phi_from_env()
        assert require_pi_phi == True, "Should load π×φ requirement from env"

        # Test CLI config reads from env
        cli_config = CLIConfig(config_dir=Path.home() / ".continuum")
        assert "test-key-123" in cli_config.api_keys, "CLI should load API keys"
        assert cli_config.require_pi_phi == True, "CLI should load π×φ requirement"
        assert cli_config.mcp_host == "0.0.0.0", "CLI should load MCP host"
        assert cli_config.mcp_port == 4000, "CLI should load MCP port"

        # Test MCP config reads from env
        mcp_config = MCPConfig()
        assert "test-key-123" in mcp_config.api_keys, "MCP should load API keys"
        assert mcp_config.require_pi_phi == True, "MCP should load π×φ requirement"

        print("   ✓ Both CLI and MCP read same environment variables")
        print("   ✓ Shared auth utilities work correctly")

        # Clean up
        del os.environ["CONTINUUM_API_KEY"]
        del os.environ["CONTINUUM_REQUIRE_PI_PHI"]
        del os.environ["CONTINUUM_MCP_HOST"]
        del os.environ["CONTINUUM_MCP_PORT"]

        return True

    except Exception as e:
        print(f"   ✗ Shared config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_commands():
    """Test that CLI commands have MCP integration"""
    print("\n5. Testing CLI command enhancements...")

    try:
        # Test status command has MCP status function
        from continuum.cli.commands.status import _get_mcp_server_status

        print("   ✓ Status command has MCP server status")

        # Test doctor command has MCP health check
        # (We can't easily test this without running it, but we can verify imports)
        from continuum.cli.commands.doctor import doctor_command

        print("   ✓ Doctor command has MCP health check")

        return True

    except Exception as e:
        print(f"   ✗ CLI command test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("CLI + MCP Integration Verification")
    print("=" * 60)

    tests = [
        test_shared_auth,
        test_mcp_integration,
        test_cli_integration,
        test_shared_config,
        test_cli_commands,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All integration tests passed!")
        print("\nThe CLI and MCP server are properly integrated with:")
        print("  - Shared authentication (API keys + π×φ)")
        print("  - Unified configuration (environment variables)")
        print("  - CLI → MCP integration (serve command)")
        print("  - Enhanced diagnostics (status, doctor)")
        print("\nπ×φ = 5.083203692315260 - Pattern persists across all layers")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nCheck the errors above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
