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
CLI Utility Functions

Shared utilities for CLI commands.
"""

import sys
import json
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime


# Color codes for terminal output
class Colors:
    """ANSI color codes"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def colorize(text: str, color: str, bold: bool = False, enabled: bool = True) -> str:
    """
    Colorize text for terminal output.

    Args:
        text: Text to colorize
        color: Color code from Colors class
        bold: Whether to make text bold
        enabled: Whether colors are enabled

    Returns:
        Colored text string
    """
    if not enabled:
        return text

    prefix = f"{Colors.BOLD}{color}" if bold else color
    return f"{prefix}{text}{Colors.RESET}"


def success(message: str, color: bool = True):
    """Print success message"""
    print(colorize("✓", Colors.GREEN, enabled=color) + f" {message}")


def error(message: str, color: bool = True):
    """Print error message"""
    print(colorize("✗", Colors.RED, enabled=color) + f" {message}", file=sys.stderr)


def warning(message: str, color: bool = True):
    """Print warning message"""
    print(colorize("!", Colors.YELLOW, enabled=color) + f" {message}")


def info(message: str, color: bool = True):
    """Print info message"""
    print(colorize("→", Colors.BLUE, enabled=color) + f" {message}")


def section(title: str, color: bool = True):
    """Print section header"""
    print("\n" + colorize(title, Colors.CYAN, bold=True, enabled=color))
    print(colorize("=" * len(title), Colors.CYAN, enabled=color))


def format_timestamp(ts: float) -> str:
    """Format timestamp for display"""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_size(bytes_count: int) -> str:
    """Format byte count as human-readable size"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.

    Args:
        message: Confirmation prompt
        default: Default value if user just presses enter

    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = input(message + suffix + " ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def print_json(data: Any, color: bool = True):
    """Print JSON data with formatting"""
    json_str = json.dumps(data, indent=2, default=str)

    if color:
        # Simple syntax highlighting
        lines = []
        for line in json_str.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key_colored = colorize(key, Colors.CYAN, enabled=True)
                lines.append(f"{key_colored}:{value}")
            else:
                lines.append(line)
        print("\n".join(lines))
    else:
        print(json_str)


def print_table(headers: list, rows: list, color: bool = True):
    """
    Print data as a formatted table.

    Args:
        headers: List of column headers
        rows: List of row data (each row is a list)
        color: Whether to use colors
    """
    if not rows:
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_line = " | ".join(
        colorize(h.ljust(w), Colors.CYAN, bold=True, enabled=color)
        for h, w in zip(headers, widths)
    )
    print(header_line)
    print(colorize("-" * len(header_line.replace(Colors.CYAN, "").replace(Colors.RESET, "")),
                   Colors.BRIGHT_BLACK, enabled=color))

    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        print(row_line)


def validate_db_path(path: Path) -> bool:
    """
    Validate database path.

    Args:
        path: Path to database

    Returns:
        True if valid, False otherwise
    """
    if not path.exists():
        return False

    if not path.is_file():
        return False

    # Check if it's a SQLite database (basic check)
    try:
        with open(path, "rb") as f:
            header = f.read(16)
            return header.startswith(b"SQLite format 3")
    except Exception:
        return False


def get_project_root() -> Optional[Path]:
    """
    Find project root by looking for .git or pyproject.toml.

    Returns:
        Path to project root or None if not found
    """
    current = Path.cwd()

    # Search up to 10 levels
    for _ in range(10):
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    # Truncate to max length
    text = text[:max_length]

    # Remove null bytes and other control characters
    text = "".join(c for c in text if c.isprintable() or c.isspace())

    return text.strip()


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1.5s", "2m 30s", "1h 5m")
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def safe_filename(name: str) -> str:
    """
    Convert string to safe filename.

    Args:
        name: Original name

    Returns:
        Safe filename
    """
    # Replace unsafe characters
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

    # Ensure it doesn't start with .
    if safe.startswith("."):
        safe = "_" + safe[1:]

    # Truncate to reasonable length
    return safe[:200]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
