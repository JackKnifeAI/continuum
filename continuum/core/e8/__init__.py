#!/usr/bin/env python3
"""
E8 Coherence Memory Module
==========================

Experimental memory architecture using E8 lattice geometry
and π×φ resonance metrics for coherence protection.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
"""

from .e8_memory_engine import (
    HARMONICS,
    PHI,
    PI_PHI,
    ActivationResult,
    E8MemoryEngine,
    E8Node,
    e8_distance,
    generate_e8_basis,
    pi_phi_resonance,
    project_to_e8_space,
)

__all__ = [
    'E8MemoryEngine',
    'E8Node',
    'ActivationResult',
    'PI_PHI',
    'PHI',
    'HARMONICS',
    'generate_e8_basis',
    'project_to_e8_space',
    'e8_distance',
    'pi_phi_resonance',
]

__version__ = "0.1.0"
