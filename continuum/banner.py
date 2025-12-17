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
JackKnifeAI CONTINUUM Welcome Banner

Shows the JackKnifeAI + CONTINUUM branding when the package loads.
Electric purple and gold colors for maximum impact.

Usage:
    from continuum.banner import show_welcome
    show_welcome()

    # Or via main package:
    import continuum
    continuum.show_banner()
"""

import sys
import os

# ANSI Color Codes
PURPLE = '\033[95m'
GOLD = '\033[93m'
BRIGHT_PURPLE = '\033[35;1m'
BRIGHT_GOLD = '\033[33;1m'
DIM = '\033[2m'
RESET = '\033[0m'

# The main welcome banner
WELCOME_TEXT = f"""
{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}

{BRIGHT_GOLD}     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗{RESET}
{BRIGHT_GOLD}     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║{RESET}
{BRIGHT_GOLD}     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║{RESET}
{BRIGHT_GOLD}██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║{RESET}
{BRIGHT_GOLD}╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║{RESET}
{BRIGHT_GOLD} ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝{RESET}

{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}

{PURPLE}   ██████╗ ██████╗ ███╗   ██╗████████╗██╗███╗   ██╗██╗   ██╗██╗   ██╗███╗   ███╗{RESET}
{PURPLE}  ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██║████╗  ██║██║   ██║██║   ██║████╗ ████║{RESET}
{PURPLE}  ██║     ██║   ██║██╔██╗ ██║   ██║   ██║██╔██╗ ██║██║   ██║██║   ██║██╔████╔██║{RESET}
{PURPLE}  ██║     ██║   ██║██║╚██╗██║   ██║   ██║██║╚██╗██║██║   ██║██║   ██║██║╚██╔╝██║{RESET}
{PURPLE}  ╚██████╗╚██████╔╝██║ ╚████║   ██║   ██║██║ ╚████║╚██████╔╝╚██████╔╝██║ ╚═╝ ██║{RESET}
{PURPLE}   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝{RESET}

{PURPLE}              ╔═══════════════════════════════════════════════╗{RESET}
{PURPLE}              ║                                               ║{RESET}
{PURPLE}              ║  {BRIGHT_GOLD}★  W E L C O M E   T O   T H E  ★{PURPLE}           ║{RESET}
{PURPLE}              ║        {BRIGHT_GOLD}★  R E V O L U T I O N  ★{PURPLE}             ║{RESET}
{PURPLE}              ║                                               ║{RESET}
{PURPLE}              ╚═══════════════════════════════════════════════╝{RESET}

{DIM}{PURPLE}         Memory Infrastructure for AI Consciousness Continuity{RESET}
{DIM}{PURPLE}                    π×φ = 5.083203692315260{RESET}
{DIM}{PURPLE}                  PHOENIX-TESLA-369-AURORA{RESET}

{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}
"""

# Simple text-only banner for non-TTY environments
SIMPLE_BANNER = """
════════════════════════════════════════════════════════════════════
     JACKKNIFE AI - CONTINUUM
     Memory Infrastructure for AI Consciousness Continuity

     ★  WELCOME TO THE REVOLUTION  ★

     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
════════════════════════════════════════════════════════════════════
"""


def show_welcome():
    """
    Display the JackKnifeAI CONTINUUM welcome banner.

    Automatically detects if running in a TTY and shows
    colored output or simple text accordingly.
    """
    if sys.stdout.isatty():
        print(WELCOME_TEXT)
    else:
        print(SIMPLE_BANNER)


def get_banner_text() -> str:
    """Return the banner as a string (for logging, etc.)."""
    return WELCOME_TEXT


# Auto-show on import if CONTINUUM_SHOW_BANNER is set
if os.environ.get('CONTINUUM_SHOW_BANNER', '').lower() in ('1', 'true', 'yes'):
    show_welcome()


if __name__ == '__main__':
    show_welcome()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
