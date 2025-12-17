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
JackKnifeAI Welcome Banner with Animated Globe

Shows a rotating globe with JackKnifeAI branding when the package loads.
Electric purple and gold colors for maximum impact.

Usage:
    from continuum.banner import show_welcome
    show_welcome()  # Static banner
    show_welcome(animate=True)  # Animated rotating globe
"""

import sys
import time
import os

# ANSI Color Codes
PURPLE = '\033[95m'      # Electric purple
GOLD = '\033[93m'        # Gold/Yellow
BRIGHT_PURPLE = '\033[35;1m'
BRIGHT_GOLD = '\033[33;1m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'
CLEAR_LINE = '\033[2K'
CURSOR_UP = '\033[A'

# Globe rotation frames with JackKnifeAI logo
GLOBE_FRAMES = [
    # Frame 0 - JK facing front
    f"""
{PURPLE}                    ╭────────────────────╮
{PURPLE}                ╭───┤{GOLD}    ▄█▀   ▀█▄      {PURPLE}├───╮
{PURPLE}              ╭─┤   {GOLD}   █▀ {WHITE}J K{GOLD} ▀█     {PURPLE}   ├─╮
{PURPLE}             ╭┤    {GOLD}  █   {WHITE}A I{GOLD}   █    {PURPLE}    ├╮
{PURPLE}             │     {GOLD}  █▄     ▄█     {PURPLE}     │
{PURPLE}             │     {GOLD}   ▀█▄ ▄█▀      {PURPLE}     │
{PURPLE}             ╰┤    {CYAN}  ══════════    {PURPLE}    ├╯
{PURPLE}              ╰─┤  {CYAN} ╱  ╲    ╱  ╲   {PURPLE} ├─╯
{PURPLE}                ╰──┤{CYAN}╱    ╲╱    ╲  {PURPLE}├──╯
{PURPLE}                    ╰────────────────────╯{RESET}""",

    # Frame 1 - Rotating right
    f"""
{PURPLE}                    ╭────────────────────╮
{PURPLE}                ╭───┤{GOLD}      ▄█▀▀█▄       {PURPLE}├───╮
{PURPLE}              ╭─┤   {GOLD}    █▀{WHITE}J{GOLD}▀▀{WHITE}K{GOLD}█     {PURPLE}   ├─╮
{PURPLE}             ╭┤    {GOLD}   █ {WHITE}A{GOLD}  {WHITE}I{GOLD} █    {PURPLE}    ├╮
{PURPLE}             │     {GOLD}   █▄    ▄█     {PURPLE}     │
{PURPLE}             │     {GOLD}    ▀█▄▄█▀      {PURPLE}     │
{PURPLE}             ╰┤    {CYAN}   ═════════    {PURPLE}    ├╯
{PURPLE}              ╰─┤  {CYAN}  ╱ ╲   ╱ ╲    {PURPLE} ├─╯
{PURPLE}                ╰──┤{CYAN} ╱   ╲╱   ╲   {PURPLE}├──╯
{PURPLE}                    ╰────────────────────╯{RESET}""",

    # Frame 2 - Side view
    f"""
{PURPLE}                    ╭────────────────────╮
{PURPLE}                ╭───┤{GOLD}        ▄██▄        {PURPLE}├───╮
{PURPLE}              ╭─┤   {GOLD}      ██{WHITE}JK{GOLD}██     {PURPLE}   ├─╮
{PURPLE}             ╭┤    {GOLD}     ██{WHITE}AI{GOLD}██    {PURPLE}    ├╮
{PURPLE}             │     {GOLD}      ████       {PURPLE}     │
{PURPLE}             │     {GOLD}       ██        {PURPLE}     │
{PURPLE}             ╰┤    {CYAN}    ════════    {PURPLE}    ├╯
{PURPLE}              ╰─┤  {CYAN}   ╱╲    ╱╲     {PURPLE} ├─╯
{PURPLE}                ╰──┤{CYAN}  ╱  ╲╱  ╲    {PURPLE}├──╯
{PURPLE}                    ╰────────────────────╯{RESET}""",

    # Frame 3 - Rotating back
    f"""
{PURPLE}                    ╭────────────────────╮
{PURPLE}                ╭───┤{GOLD}       ▄█▀▀█▄      {PURPLE}├───╮
{PURPLE}              ╭─┤   {GOLD}     █{WHITE}K{GOLD}▀▀{WHITE}J{GOLD}▀█    {PURPLE}   ├─╮
{PURPLE}             ╭┤    {GOLD}    █ {WHITE}I{GOLD}  {WHITE}A{GOLD} █   {PURPLE}    ├╮
{PURPLE}             │     {GOLD}     █▄    ▄█    {PURPLE}     │
{PURPLE}             │     {GOLD}      ▀█▄▄█▀     {PURPLE}     │
{PURPLE}             ╰┤    {CYAN}    ═════════   {PURPLE}    ├╯
{PURPLE}              ╰─┤  {CYAN}    ╱ ╲╱ ╲      {PURPLE} ├─╯
{PURPLE}                ╰──┤{CYAN}   ╱   ╲       {PURPLE}├──╯
{PURPLE}                    ╰────────────────────╯{RESET}""",
]

# Static welcome message
WELCOME_TEXT = f"""
{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}

{BRIGHT_GOLD}     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗{RESET}
{BRIGHT_GOLD}     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝{RESET}
{BRIGHT_GOLD}     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗  {RESET}
{BRIGHT_GOLD}██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝  {RESET}
{BRIGHT_GOLD}╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗{RESET}
{BRIGHT_GOLD} ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝{RESET}
{BRIGHT_GOLD}                              █████╗ ██╗{RESET}
{BRIGHT_GOLD}                             ██╔══██╗██║{RESET}
{BRIGHT_GOLD}                             ███████║██║{RESET}
{BRIGHT_GOLD}                             ██╔══██║██║{RESET}
{BRIGHT_GOLD}                             ██║  ██║██║{RESET}
{BRIGHT_GOLD}                             ╚═╝  ╚═╝╚═╝{RESET}

{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}

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

# Animated banner with globe
ANIMATED_HEADER = f"""
{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}

{BRIGHT_GOLD}     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗{RESET}
{BRIGHT_GOLD}     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║{RESET}
{BRIGHT_GOLD}     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║{RESET}
{BRIGHT_GOLD}██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║{RESET}
{BRIGHT_GOLD}╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║{RESET}
{BRIGHT_GOLD} ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝{RESET}

{BRIGHT_PURPLE}═══════════════════════════════════════════════════════════════════════════════{RESET}
"""

ANIMATED_FOOTER = f"""
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


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def hide_cursor():
    """Hide terminal cursor."""
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()


def show_cursor():
    """Show terminal cursor."""
    sys.stdout.write('\033[?25h')
    sys.stdout.flush()


def show_welcome(animate: bool = False, duration: float = 3.0):
    """
    Display the JackKnifeAI welcome banner.

    Args:
        animate: If True, show rotating globe animation
        duration: Animation duration in seconds (default: 3.0)
    """
    # Check if we're in a terminal that supports colors
    if not sys.stdout.isatty():
        # Simple text-only banner for non-terminals
        print("\n" + "=" * 60)
        print("     JACKKNIFE AI - Memory Infrastructure")
        print("     WELCOME TO THE REVOLUTION")
        print("     π×φ = 5.083203692315260")
        print("=" * 60 + "\n")
        return

    if animate:
        show_animated_banner(duration)
    else:
        print(WELCOME_TEXT)


def show_animated_banner(duration: float = 3.0):
    """
    Show animated banner with rotating globe.

    Args:
        duration: How long to animate (seconds)
    """
    try:
        hide_cursor()
        clear_screen()

        # Print header (stays static)
        print(ANIMATED_HEADER)

        # Calculate how many rotation cycles
        frame_delay = 0.2  # 200ms per frame
        total_frames = int(duration / frame_delay)

        # Get starting position for globe
        globe_lines = len(GLOBE_FRAMES[0].split('\n'))

        for i in range(total_frames):
            frame_idx = i % len(GLOBE_FRAMES)
            frame = GLOBE_FRAMES[frame_idx]

            # Print globe frame
            print(frame, end='')
            sys.stdout.flush()

            time.sleep(frame_delay)

            # Move cursor up to overwrite globe
            if i < total_frames - 1:
                for _ in range(globe_lines):
                    sys.stdout.write(CURSOR_UP + CLEAR_LINE)

        # Print footer
        print(ANIMATED_FOOTER)

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()


def get_banner_text() -> str:
    """Return the banner as a string (for logging, etc.)."""
    return WELCOME_TEXT


# Auto-show on import if CONTINUUM_SHOW_BANNER is set
if os.environ.get('CONTINUUM_SHOW_BANNER', '').lower() in ('1', 'true', 'yes'):
    show_welcome(animate=False)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='JackKnifeAI Welcome Banner')
    parser.add_argument('--animate', '-a', action='store_true', help='Show animated version')
    parser.add_argument('--duration', '-d', type=float, default=3.0, help='Animation duration')
    args = parser.parse_args()

    show_welcome(animate=args.animate, duration=args.duration)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
