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
LZ4 Compression

Extremely fast compression with decent compression ratio.
Ideal for hot backups where speed is critical.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class LZ4CompressionHandler:
    """
    LZ4 compression handler.

    Characteristics:
    - Compression ratio: ~50-60%
    - Speed: Very fast (500+ MB/s)
    - Compatibility: Good (requires lz4 library)
    - Best for: Frequent backups where speed matters

    Modes:
    - Fast mode: Maximum speed
    - High compression: Better ratio, slower
    """

    def __init__(self, high_compression: bool = False):
        self.high_compression = high_compression

    async def compress(self, data: bytes) -> bytes:
        """Compress data using LZ4"""
        logger.info(f"Compressing {len(data)} bytes with LZ4")

        def _compress():
            try:
                import lz4.frame
            except ImportError:
                raise ImportError(
                    "lz4 required for LZ4 compression. Install with: pip install lz4"
                )

            if self.high_compression:
                return lz4.frame.compress(data, compression_level=lz4.frame.COMPRESSIONLEVEL_MAX)
            else:
                return lz4.frame.compress(data)

        compressed = await asyncio.to_thread(_compress)

        ratio = (1 - len(compressed) / len(data)) * 100
        logger.info(f"Compressed to {len(compressed)} bytes ({ratio:.1f}% reduction)")

        return compressed

    async def decompress(self, data: bytes) -> bytes:
        """Decompress LZ4 data"""
        logger.info(f"Decompressing {len(data)} bytes with LZ4")

        def _decompress():
            try:
                import lz4.frame
            except ImportError:
                raise ImportError(
                    "lz4 required for LZ4 decompression. Install with: pip install lz4"
                )

            return lz4.frame.decompress(data)

        decompressed = await asyncio.to_thread(_decompress)

        logger.info(f"Decompressed to {len(decompressed)} bytes")
        return decompressed

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
