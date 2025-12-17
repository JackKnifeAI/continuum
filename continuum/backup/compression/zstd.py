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
Zstandard (zstd) Compression

Modern compression algorithm with excellent ratio and speed.
Best choice for most backup scenarios.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class ZstdCompressionHandler:
    """
    Zstandard compression handler.

    Characteristics:
    - Compression ratio: ~65-75% (best)
    - Speed: Fast (200+ MB/s)
    - Compatibility: Modern (requires zstandard library)
    - Best for: Production backups (best ratio + speed)

    Compression levels:
    - 1-3: Fast mode
    - 4-10: Default range
    - 11-19: High compression
    - 20-22: Ultra (very slow)
    """

    def __init__(self, level: int = 3):
        self.level = level

    async def compress(self, data: bytes) -> bytes:
        """Compress data using Zstandard"""
        logger.info(f"Compressing {len(data)} bytes with zstd (level {self.level})")

        def _compress():
            try:
                import zstandard as zstd
            except ImportError:
                raise ImportError(
                    "zstandard required for zstd compression. "
                    "Install with: pip install zstandard"
                )

            cctx = zstd.ZstdCompressor(level=self.level)
            return cctx.compress(data)

        compressed = await asyncio.to_thread(_compress)

        ratio = (1 - len(compressed) / len(data)) * 100
        logger.info(f"Compressed to {len(compressed)} bytes ({ratio:.1f}% reduction)")

        return compressed

    async def decompress(self, data: bytes) -> bytes:
        """Decompress Zstandard data"""
        logger.info(f"Decompressing {len(data)} bytes with zstd")

        def _decompress():
            try:
                import zstandard as zstd
            except ImportError:
                raise ImportError(
                    "zstandard required for zstd decompression. "
                    "Install with: pip install zstandard"
                )

            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(data)

        decompressed = await asyncio.to_thread(_decompress)

        logger.info(f"Decompressed to {len(decompressed)} bytes")
        return decompressed

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
