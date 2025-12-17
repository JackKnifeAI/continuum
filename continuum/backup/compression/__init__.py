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
Compression Handlers

Multiple compression algorithms optimized for different use cases.
"""

from .gzip import GzipCompressionHandler
from .lz4 import LZ4CompressionHandler
from .zstd import ZstdCompressionHandler
from ..types import CompressionAlgorithm


def get_compression_handler(algorithm: CompressionAlgorithm):
    """
    Get compression handler for specified algorithm.

    Args:
        algorithm: Compression algorithm to use

    Returns:
        Compression handler instance
    """
    handlers = {
        CompressionAlgorithm.GZIP: GzipCompressionHandler,
        CompressionAlgorithm.LZ4: LZ4CompressionHandler,
        CompressionAlgorithm.ZSTD: ZstdCompressionHandler,
        CompressionAlgorithm.NONE: NoCompressionHandler,
    }

    handler_class = handlers.get(algorithm)
    if not handler_class:
        raise ValueError(f"Unknown compression algorithm: {algorithm}")

    return handler_class()


class NoCompressionHandler:
    """No-op compression handler"""

    async def compress(self, data: bytes) -> bytes:
        return data

    async def decompress(self, data: bytes) -> bytes:
        return data


__all__ = [
    'GzipCompressionHandler',
    'LZ4CompressionHandler',
    'ZstdCompressionHandler',
    'get_compression_handler',
]

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
