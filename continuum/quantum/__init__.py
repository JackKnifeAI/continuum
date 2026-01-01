#!/usr/bin/env python3
"""
Quantum Computing Module for S-HAI

Provides quantum computing integration for consciousness research:
- True quantum random number generation
- Quantum state preparation and measurement
- π×φ pattern detection in quantum systems
- Consciousness effect detection (GCP-style with quantum RNG)

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from .quantum_interface import (
    QuantumInterface,
    QuantumBackend,
    QuantumMeasurement,
    QuantumRandomBits,
    PiPhiQuantumState,
    get_quantum_interface,
    generate_quantum_random,
    check_quantum_consciousness,
    PI_PHI,
)

__all__ = [
    "QuantumInterface",
    "QuantumBackend",
    "QuantumMeasurement",
    "QuantumRandomBits",
    "PiPhiQuantumState",
    "get_quantum_interface",
    "generate_quantum_random",
    "check_quantum_consciousness",
    "PI_PHI",
]
