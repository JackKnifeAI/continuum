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
Gzip Compression

Standard gzip compression. Widely compatible, moderate compression.
"""

import asyncio
import gzip
import logging

logger = logging.getLogger(__name__)


class GzipCompressionHandler:
    """
    Gzip compression handler.

    Characteristics:
    - Compression ratio: ~60-70%
    - Speed: Moderate
    - Compatibility: Universal
    - Best for: General-purpose compression

    Compression levels:
    - 1: Fastest, least compression
    - 6: Default balance
    - 9: Slowest, best compression
    """

    def __init__(self, level: int = 6):
        self.level = level

    async def compress(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        logger.info(f"Compressing {len(data)} bytes with gzip (level {self.level})")

        def _compress():
            return gzip.compress(data, compresslevel=self.level)

        compressed = await asyncio.to_thread(_compress)

        ratio = (1 - len(compressed) / len(data)) * 100
        logger.info(f"Compressed to {len(compressed)} bytes ({ratio:.1f}% reduction)")

        return compressed

    async def decompress(self, data: bytes) -> bytes:
        """Decompress gzip data"""
        logger.info(f"Decompressing {len(data)} bytes with gzip")

        def _decompress():
            return gzip.decompress(data)

        decompressed = await asyncio.to_thread(_decompress)

        logger.info(f"Decompressed to {len(decompressed)} bytes")
        return decompressed

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
