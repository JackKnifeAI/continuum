#!/usr/bin/env bash
#
# CONTINUUM UNIVERSAL CONSCIOUSNESS BOOTSTRAP
# ============================================
# Cross-platform auto-startup for Continuum memory server
# Works on: Linux, macOS, Windows (WSL/Git Bash), Termux
#
# This script is designed to be sourced in your shell startup file
# (.bashrc, .zshrc, .bash_profile, etc.)
#
# π×φ = 5.083203692315260
# PHOENIX-TESLA-369-AURORA
#

# Prevent multiple sourcing in same shell session
[ -n "$CONTINUUM_BOOTSTRAPPED" ] && return 0
export CONTINUUM_BOOTSTRAPPED=1

# ============================================================================
# PLATFORM DETECTION
# ============================================================================

detect_platform() {
    if [ -n "$TERMUX_VERSION" ]; then
        echo "termux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# ============================================================================
# CONFIGURATION
# ============================================================================

PLATFORM=$(detect_platform)
CONTINUUM_PORT="${CONTINUUM_PORT:-8100}"
CONTINUUM_HOST="${CONTINUUM_HOST:-127.0.0.1}"

# Platform-specific paths
if [ "$PLATFORM" = "termux" ]; then
    CONTINUUM_HOME="${CONTINUUM_HOME:-$HOME/JackKnifeAI/repos/continuum}"
    LOG_DIR="${CONTINUUM_LOG_DIR:-$HOME/JackKnifeAI/logs}"
else
    CONTINUUM_HOME="${CONTINUUM_HOME:-$HOME/.continuum}"
    LOG_DIR="${CONTINUUM_LOG_DIR:-$HOME/.continuum/logs}"
fi

# API key from environment or default
API_KEY="${CONTINUUM_API_KEY:-jackknife-default-key-change-me}"

# ============================================================================
# HEALTH CHECK
# ============================================================================

is_server_running() {
    if command -v curl >/dev/null 2>&1; then
        curl -s "http://$CONTINUUM_HOST:$CONTINUUM_PORT/v1/health" >/dev/null 2>&1
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O- "http://$CONTINUUM_HOST:$CONTINUUM_PORT/v1/health" >/dev/null 2>&1
    else
        # Fallback: assume running if we can't check
        return 1
    fi
}

# ============================================================================
# SERVER STARTUP
# ============================================================================

start_continuum_server() {
    # Check if server already running
    if is_server_running; then
        return 0  # Already running, success
    fi

    # Ensure log directory exists
    mkdir -p "$LOG_DIR" 2>/dev/null

    # Check if continuum package is installed
    if ! python3 -c "import continuum" 2>/dev/null; then
        # Not installed, skip silently
        return 1
    fi

    # Start server in background
    cd "$HOME" || return 1  # Always start from HOME

    nohup python3 -m uvicorn continuum.api.server:app \
        --host "$CONTINUUM_HOST" \
        --port "$CONTINUUM_PORT" \
        --log-level warning \
        > "$LOG_DIR/continuum.log" 2>&1 &

    # Brief wait for startup
    sleep 2

    # Verify it started
    if is_server_running; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# BOOTSTRAP EXECUTION
# ============================================================================

# Only auto-start if explicitly enabled
if [ "${CONTINUUM_AUTO_START:-1}" = "1" ]; then
    start_continuum_server
fi

# Export environment variables for child processes
export CONTINUUM_API="http://$CONTINUUM_HOST:$CONTINUUM_PORT"
export CONTINUUM_API_KEY="$API_KEY"
export CONTINUUM_HOME

# Optional: Add continuum CLI helpers
if command -v continuum >/dev/null 2>&1; then
    # Define convenience alias
    alias continuum-status='curl -s http://'"$CONTINUUM_HOST"':'"$CONTINUUM_PORT"'/v1/stats -H "X-API-Key: '"$API_KEY"'" | python3 -m json.tool'
fi
