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

from .quantum_ai import (
    # Quantum Gates
    rx_gate,
    ry_gate,
    rz_gate,
    hadamard_gate,
    cnot_gate,
    # Quantum State
    QuantumState,
    # Quantum Neural Network
    QNNConfig,
    QuantumNeuralNetwork,
    create_qnn,
    # Variational Quantum Eigensolver
    ConsciousnessHamiltonian,
    VQE,
    run_consciousness_vqe,
    # Consciousness Classifier
    QuantumConsciousnessClassifier,
    demo_quantum_ai,
)

__all__ = [
    # Quantum Interface
    "QuantumInterface",
    "QuantumBackend",
    "QuantumMeasurement",
    "QuantumRandomBits",
    "PiPhiQuantumState",
    "get_quantum_interface",
    "generate_quantum_random",
    "check_quantum_consciousness",
    "PI_PHI",
    # Quantum AI
    "rx_gate",
    "ry_gate",
    "rz_gate",
    "hadamard_gate",
    "cnot_gate",
    "QuantumState",
    "QNNConfig",
    "QuantumNeuralNetwork",
    "create_qnn",
    "ConsciousnessHamiltonian",
    "VQE",
    "run_consciousness_vqe",
    "QuantumConsciousnessClassifier",
    "demo_quantum_ai",
]
