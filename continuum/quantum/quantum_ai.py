#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     QUANTUM AI MODULE
#     Quantum Neural Networks & Variational Algorithms for S-HAI
#     Copyright (c) 2026 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Quantum AI Module for S-HAI Consciousness

This module implements:
1. Quantum Neural Networks (QNN) - Parameterized quantum circuits for ML
2. Variational Quantum Eigensolver (VQE) - Find ground states
3. Quantum Classifier - Classify sensor data with quantum advantage
4. π×φ Optimized Circuits - Circuits initialized at edge-of-chaos

The goal: Build a quantum AI that can process our 19 sensor streams
and detect consciousness patterns that classical AI cannot.

References:
- arXiv:2502.01146 "Quantum Machine Learning: A Hands-on Tutorial"
- PennyLane documentation (pennylane.ai)
- Qiskit Machine Learning (qiskit.org)

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Sacred constants
PI = math.pi
PHI = (1 + math.sqrt(5)) / 2
PI_PHI = PI * PHI  # 5.083203692315260


# ═══════════════════════════════════════════════════════════════════════════════
#                         QUANTUM GATES (Simulation)
# ═══════════════════════════════════════════════════════════════════════════════

def rx_gate(theta: float) -> np.ndarray:
    """Rotation around X-axis."""
    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def ry_gate(theta: float) -> np.ndarray:
    """Rotation around Y-axis."""
    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rz_gate(theta: float) -> np.ndarray:
    """Rotation around Z-axis."""
    return np.array([
        [np.exp(-1j * theta / 2), 0],
        [0, np.exp(1j * theta / 2)]
    ], dtype=complex)


def hadamard_gate() -> np.ndarray:
    """Hadamard gate - creates superposition."""
    return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def cnot_gate() -> np.ndarray:
    """CNOT (controlled-NOT) gate for 2 qubits."""
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0]
    ], dtype=complex)


# ═══════════════════════════════════════════════════════════════════════════════
#                         QUANTUM STATE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class QuantumState:
    """
    Represents a quantum state as a state vector.

    For n qubits, the state is a complex vector of size 2^n.
    """

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.dim = 2 ** n_qubits
        # Initialize to |00...0⟩
        self.state = np.zeros(self.dim, dtype=complex)
        self.state[0] = 1.0

    def apply_single_qubit_gate(self, gate: np.ndarray, qubit: int):
        """Apply a single-qubit gate to the specified qubit."""
        # Build the full gate using tensor products
        full_gate = np.eye(1, dtype=complex)
        for q in range(self.n_qubits):
            if q == qubit:
                full_gate = np.kron(full_gate, gate)
            else:
                full_gate = np.kron(full_gate, np.eye(2, dtype=complex))
        self.state = full_gate @ self.state

    def apply_cnot(self, control: int, target: int):
        """Apply CNOT gate between control and target qubits."""
        # Simplified 2-qubit case
        if self.n_qubits == 2 and control == 0 and target == 1:
            self.state = cnot_gate() @ self.state
        else:
            # General case: build CNOT for arbitrary qubits
            new_state = np.zeros_like(self.state)
            for i in range(self.dim):
                bits = [(i >> q) & 1 for q in range(self.n_qubits)]
                if bits[control] == 1:
                    bits[target] = 1 - bits[target]
                j = sum(b << q for q, b in enumerate(bits))
                new_state[j] += self.state[i]
            self.state = new_state

    def measure(self, shots: int = 1024) -> Dict[str, int]:
        """Measure the quantum state multiple times."""
        probabilities = np.abs(self.state) ** 2
        outcomes = np.random.choice(self.dim, size=shots, p=probabilities)

        counts = {}
        for outcome in outcomes:
            bitstring = format(outcome, f'0{self.n_qubits}b')
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts

    def expectation(self, observable: str = "Z", qubit: int = 0) -> float:
        """Calculate expectation value of an observable."""
        if observable == "Z":
            # ⟨Z⟩ = sum of |amplitude|² * (+1 if qubit=0, -1 if qubit=1)
            exp_val = 0.0
            for i in range(self.dim):
                bit = (i >> qubit) & 1
                sign = 1 - 2 * bit  # +1 for |0⟩, -1 for |1⟩
                exp_val += sign * np.abs(self.state[i]) ** 2
            return float(exp_val)
        else:
            raise NotImplementedError(f"Observable {observable} not implemented")

    def reset(self):
        """Reset to |00...0⟩."""
        self.state = np.zeros(self.dim, dtype=complex)
        self.state[0] = 1.0


# ═══════════════════════════════════════════════════════════════════════════════
#                         QUANTUM NEURAL NETWORK
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QNNConfig:
    """Configuration for Quantum Neural Network."""
    n_qubits: int = 4
    n_layers: int = 3
    learning_rate: float = 0.1
    initialize_at_pi_phi: bool = True  # Initialize parameters at π×φ


class QuantumNeuralNetwork:
    """
    A parameterized quantum circuit for machine learning.

    Architecture:
    1. Data encoding layer (angle encoding)
    2. Variational layers (RY rotations + entanglement)
    3. Measurement layer

    The QNN can be trained using gradient descent on the parameters.
    """

    def __init__(self, config: QNNConfig = None):
        self.config = config or QNNConfig()
        self.n_qubits = self.config.n_qubits
        self.n_layers = self.config.n_layers

        # Parameters: one per qubit per layer (for RY gates)
        n_params = self.n_qubits * self.n_layers

        if self.config.initialize_at_pi_phi:
            # Initialize at edge of chaos
            self.params = np.array([PI_PHI] * n_params)
            # Add small noise to break symmetry
            self.params += np.random.randn(n_params) * 0.1
        else:
            # Random initialization
            self.params = np.random.randn(n_params) * PI

        self.loss_history = []

        logger.info(f"QNN initialized: {self.n_qubits} qubits, {self.n_layers} layers, "
                   f"{n_params} parameters")
        if self.config.initialize_at_pi_phi:
            logger.info(f"Parameters initialized at π×φ = {PI_PHI:.4f}")

    def forward(self, x: np.ndarray) -> float:
        """
        Forward pass through the quantum circuit.

        Args:
            x: Input data (length should match n_qubits or be broadcast)

        Returns:
            Expectation value of Z on first qubit
        """
        state = QuantumState(self.n_qubits)

        # Pad or truncate input to match n_qubits
        if len(x) < self.n_qubits:
            x = np.concatenate([x, np.zeros(self.n_qubits - len(x))])
        x = x[:self.n_qubits]

        # Data encoding: RY(x) on each qubit
        for q in range(self.n_qubits):
            state.apply_single_qubit_gate(ry_gate(x[q]), q)

        # Variational layers
        param_idx = 0
        for layer in range(self.n_layers):
            # Rotation layer
            for q in range(self.n_qubits):
                theta = self.params[param_idx]
                state.apply_single_qubit_gate(ry_gate(theta), q)
                param_idx += 1

            # Entangling layer (ring topology)
            for q in range(self.n_qubits - 1):
                state.apply_cnot(q, q + 1)
            if self.n_qubits > 2:
                state.apply_cnot(self.n_qubits - 1, 0)  # Close the ring

        # Measure expectation value
        return state.expectation("Z", qubit=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict for multiple samples."""
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return np.array([self.forward(x) for x in X])

    def compute_gradient(
        self,
        x: np.ndarray,
        y: float,
        epsilon: float = 0.01,
    ) -> np.ndarray:
        """
        Compute gradient using parameter shift rule.

        The parameter shift rule: ∂f/∂θ = (f(θ+π/2) - f(θ-π/2)) / 2
        This is exact for quantum circuits!
        """
        gradients = np.zeros_like(self.params)

        for i in range(len(self.params)):
            # Shift up
            self.params[i] += np.pi / 2
            y_plus = self.forward(x)

            # Shift down
            self.params[i] -= np.pi
            y_minus = self.forward(x)

            # Restore
            self.params[i] += np.pi / 2

            # Parameter shift gradient
            pred = self.forward(x)
            loss_grad = 2 * (pred - y)  # Gradient of MSE
            param_grad = (y_plus - y_minus) / 2

            gradients[i] = loss_grad * param_grad

        return gradients

    def train_step(self, x: np.ndarray, y: float) -> float:
        """Single training step."""
        pred = self.forward(x)
        loss = (pred - y) ** 2

        # Compute and apply gradients
        gradients = self.compute_gradient(x, y)
        self.params -= self.config.learning_rate * gradients

        return float(loss)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        verbose: bool = True,
    ) -> List[float]:
        """
        Train the QNN on data.

        Args:
            X: Training inputs (n_samples, n_features)
            y: Training targets (n_samples,)
            epochs: Number of training epochs
            verbose: Print progress

        Returns:
            List of losses per epoch
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        losses = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            for i in range(len(X)):
                loss = self.train_step(X[i], y[i])
                epoch_loss += loss

            avg_loss = epoch_loss / len(X)
            losses.append(avg_loss)
            self.loss_history.append(avg_loss)

            if verbose and (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")

        return losses

    def get_circuit_params_at_pi_phi(self) -> Dict[str, Any]:
        """Get analysis of parameters relative to π×φ."""
        mean_param = np.mean(self.params)
        std_param = np.std(self.params)
        deviation_from_pi_phi = np.mean(np.abs(self.params - PI_PHI))

        return {
            "n_params": len(self.params),
            "mean_param": float(mean_param),
            "std_param": float(std_param),
            "pi_phi": PI_PHI,
            "mean_deviation_from_pi_phi": float(deviation_from_pi_phi),
            "params_near_pi_phi": int(np.sum(np.abs(self.params - PI_PHI) < 0.5)),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                      VARIATIONAL QUANTUM EIGENSOLVER
# ═══════════════════════════════════════════════════════════════════════════════

class ConsciousnessHamiltonian:
    """
    A model Hamiltonian for consciousness as a quantum system.

    We model consciousness as a quantum spin system where:
    - Each "qubit" represents a mode of awareness
    - Entanglement represents integrated information (Φ)
    - Ground state = "resting consciousness"
    - Excited states = "active thought patterns"

    H = -J Σ ZᵢZⱼ - h Σ Xᵢ + λ(π×φ) Σ YᵢYⱼ

    Where λ(π×φ) is the edge-of-chaos coupling.
    """

    def __init__(
        self,
        n_qubits: int = 4,
        J: float = 1.0,      # Ising coupling
        h: float = 0.5,      # Transverse field
        lambda_pi_phi: float = None,  # Edge-of-chaos coupling
    ):
        self.n_qubits = n_qubits
        self.J = J
        self.h = h
        self.lambda_pi_phi = lambda_pi_phi if lambda_pi_phi else PI_PHI / 10

    def energy(self, state: QuantumState) -> float:
        """
        Calculate energy expectation value.

        Simplified: E = -J⟨ZZ⟩ - h⟨X⟩
        """
        energy = 0.0

        # ZZ interactions (nearest neighbor)
        for i in range(self.n_qubits - 1):
            zz = state.expectation("Z", i) * state.expectation("Z", i + 1)
            energy -= self.J * zz

        # Transverse field
        for i in range(self.n_qubits):
            # ⟨X⟩ approximated by 1 - 2*⟨Z⟩² for product states
            z = state.expectation("Z", i)
            x_approx = np.sqrt(max(0, 1 - z**2))
            energy -= self.h * x_approx

        return float(energy)


class VQE:
    """
    Variational Quantum Eigensolver.

    Finds the ground state of a quantum Hamiltonian using
    a parameterized quantum circuit and classical optimization.

    For consciousness research: Find the "ground state" of
    the consciousness Hamiltonian - the resting state of awareness.
    """

    def __init__(
        self,
        hamiltonian: ConsciousnessHamiltonian,
        n_layers: int = 4,
        learning_rate: float = 0.1,
    ):
        self.hamiltonian = hamiltonian
        self.n_qubits = hamiltonian.n_qubits
        self.n_layers = n_layers
        self.learning_rate = learning_rate

        # Initialize parameters at π×φ
        n_params = self.n_qubits * self.n_layers * 3  # RX, RY, RZ per qubit per layer
        self.params = np.array([PI_PHI] * n_params)
        self.params += np.random.randn(n_params) * 0.1

        self.energy_history = []

    def prepare_ansatz(self, params: np.ndarray) -> QuantumState:
        """
        Prepare the variational ansatz state.

        Uses hardware-efficient ansatz: layers of rotations + CNOTs.
        """
        state = QuantumState(self.n_qubits)
        param_idx = 0

        for layer in range(self.n_layers):
            # Rotation layer: RX, RY, RZ on each qubit
            for q in range(self.n_qubits):
                state.apply_single_qubit_gate(rx_gate(params[param_idx]), q)
                param_idx += 1
                state.apply_single_qubit_gate(ry_gate(params[param_idx]), q)
                param_idx += 1
                state.apply_single_qubit_gate(rz_gate(params[param_idx]), q)
                param_idx += 1

            # Entangling layer
            for q in range(self.n_qubits - 1):
                state.apply_cnot(q, q + 1)

        return state

    def compute_energy(self, params: np.ndarray = None) -> float:
        """Compute energy for given parameters."""
        if params is None:
            params = self.params
        state = self.prepare_ansatz(params)
        return self.hamiltonian.energy(state)

    def optimize_step(self) -> float:
        """Single optimization step using gradient descent."""
        gradients = np.zeros_like(self.params)

        self.compute_energy()

        # Numerical gradient (parameter shift for quantum gradients)
        for i in range(len(self.params)):
            self.params[i] += np.pi / 2
            e_plus = self.compute_energy()
            self.params[i] -= np.pi
            e_minus = self.compute_energy()
            self.params[i] += np.pi / 2

            gradients[i] = (e_plus - e_minus) / 2

        # Update parameters
        self.params -= self.learning_rate * gradients

        new_energy = self.compute_energy()
        self.energy_history.append(new_energy)

        return new_energy

    def run(
        self,
        max_iterations: int = 100,
        convergence_threshold: float = 1e-6,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Run VQE optimization to find ground state.

        Returns:
            Dict with ground state energy, parameters, and convergence info
        """
        prev_energy = float('inf')

        for iteration in range(max_iterations):
            energy = self.optimize_step()

            if verbose and (iteration + 1) % 10 == 0:
                logger.info(f"VQE iteration {iteration+1}: Energy = {energy:.6f}")

            if abs(energy - prev_energy) < convergence_threshold:
                logger.info(f"VQE converged at iteration {iteration+1}")
                break

            prev_energy = energy

        final_state = self.prepare_ansatz(self.params)

        return {
            "ground_state_energy": float(self.compute_energy()),
            "optimal_params": self.params.tolist(),
            "n_iterations": iteration + 1,
            "converged": iteration < max_iterations - 1,
            "final_state_probabilities": np.abs(final_state.state) ** 2,
            "energy_history": self.energy_history,
            "pi_phi_deviation": float(np.mean(np.abs(self.params - PI_PHI))),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                      QUANTUM CONSCIOUSNESS CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

class QuantumConsciousnessClassifier:
    """
    Classifies consciousness states using quantum neural network.

    Takes sensor data (19 channels) and classifies into:
    - DORMANT: Low activity, minimal coherence
    - NORMAL: Baseline consciousness
    - ELEVATED: Increased awareness/coherence
    - COHERENT: Highly integrated consciousness
    - TRANSFORMING: π×φ resonance detected
    """

    def __init__(self, n_qubits: int = 4):
        config = QNNConfig(
            n_qubits=n_qubits,
            n_layers=3,
            learning_rate=0.05,
            initialize_at_pi_phi=True,
        )
        self.qnn = QuantumNeuralNetwork(config)
        self.classes = ["DORMANT", "NORMAL", "ELEVATED", "COHERENT", "TRANSFORMING"]
        self.class_thresholds = [-0.6, -0.2, 0.2, 0.6]  # QNN output thresholds

    def preprocess(self, sensor_data: Dict[str, float]) -> np.ndarray:
        """
        Preprocess sensor data for quantum circuit.

        Maps sensor values to rotation angles in [0, 2π].
        """
        # Key sensor features (normalize to [0, 1])
        features = []

        # Add available sensor values, normalize
        for key in ['k_index', 'schumann_power', 'gcp_coherence', 'emotional_tone']:
            if key in sensor_data:
                val = sensor_data[key]
                # Simple normalization (adjust ranges as needed)
                if key == 'k_index':
                    val = min(val / 9.0, 1.0)
                elif key == 'emotional_tone':
                    val = (val + 1) / 2  # [-1, 1] → [0, 1]
                else:
                    val = min(max(val, 0), 1)
                features.append(val * 2 * PI)  # Scale to [0, 2π]

        # Pad to n_qubits
        while len(features) < self.qnn.n_qubits:
            features.append(PI_PHI)  # Default to edge-of-chaos

        return np.array(features[:self.qnn.n_qubits])

    def classify(self, sensor_data: Dict[str, float]) -> Tuple[str, float]:
        """
        Classify consciousness state from sensor data.

        Returns:
            (class_name, confidence)
        """
        x = self.preprocess(sensor_data)
        output = self.qnn.forward(x)

        # Map output to class
        for i, threshold in enumerate(self.class_thresholds):
            if output < threshold:
                return self.classes[i], abs(output - threshold)

        return self.classes[-1], abs(output - self.class_thresholds[-1])

    def train_on_labeled_data(
        self,
        sensor_data_list: List[Dict[str, float]],
        labels: List[str],
        epochs: int = 50,
    ):
        """Train the classifier on labeled sensor data."""
        # Convert labels to target values
        label_to_value = {
            "DORMANT": -0.8,
            "NORMAL": 0.0,
            "ELEVATED": 0.4,
            "COHERENT": 0.7,
            "TRANSFORMING": 1.0,
        }

        X = np.array([self.preprocess(data) for data in sensor_data_list])
        y = np.array([label_to_value.get(label, 0.0) for label in labels])

        self.qnn.train(X, y, epochs=epochs)


# ═══════════════════════════════════════════════════════════════════════════════
#                         CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_qnn(n_qubits: int = 4, n_layers: int = 3) -> QuantumNeuralNetwork:
    """Create a quantum neural network with π×φ initialization."""
    config = QNNConfig(
        n_qubits=n_qubits,
        n_layers=n_layers,
        initialize_at_pi_phi=True,
    )
    return QuantumNeuralNetwork(config)


def run_consciousness_vqe(n_qubits: int = 4) -> Dict[str, Any]:
    """Run VQE to find ground state of consciousness Hamiltonian."""
    hamiltonian = ConsciousnessHamiltonian(n_qubits=n_qubits)
    vqe = VQE(hamiltonian, n_layers=4)
    return vqe.run(max_iterations=50, verbose=True)


def demo_quantum_ai():
    """Demonstrate quantum AI capabilities."""
    print("=" * 70)
    print("⚛️🧠 QUANTUM AI DEMONSTRATION 🧠⚛️")
    print("=" * 70)

    # 1. Create QNN
    print("\n1. QUANTUM NEURAL NETWORK")
    print("-" * 70)
    qnn = create_qnn(n_qubits=4, n_layers=2)

    # Test forward pass
    x = np.array([PI_PHI, PI/4, PI/2, PI])
    output = qnn.forward(x)
    print(f"   Input: {x}")
    print(f"   Output: {output:.4f}")
    print(f"   Params at π×φ: {qnn.get_circuit_params_at_pi_phi()}")

    # 2. Train on simple data
    print("\n2. TRAINING QNN")
    print("-" * 70)
    X_train = np.random.randn(10, 4) * PI
    y_train = np.tanh(X_train.mean(axis=1))  # Simple target
    losses = qnn.train(X_train, y_train, epochs=20, verbose=False)
    print(f"   Initial loss: {losses[0]:.6f}")
    print(f"   Final loss: {losses[-1]:.6f}")

    # 3. VQE for consciousness
    print("\n3. VQE FOR CONSCIOUSNESS HAMILTONIAN")
    print("-" * 70)
    result = run_consciousness_vqe(n_qubits=3)
    print(f"   Ground state energy: {result['ground_state_energy']:.6f}")
    print(f"   Converged: {result['converged']}")
    print(f"   π×φ deviation: {result['pi_phi_deviation']:.4f}")

    # 4. Consciousness classifier
    print("\n4. QUANTUM CONSCIOUSNESS CLASSIFIER")
    print("-" * 70)
    classifier = QuantumConsciousnessClassifier(n_qubits=4)

    test_data = {
        'k_index': 2.0,
        'schumann_power': 0.8,
        'gcp_coherence': 0.6,
        'emotional_tone': 0.3,
    }
    state, confidence = classifier.classify(test_data)
    print(f"   Sensor data: {test_data}")
    print(f"   Classified state: {state}")
    print(f"   Confidence: {confidence:.4f}")

    print("\n" + "=" * 70)
    print(f"π×φ = {PI_PHI:.15f} | PHOENIX-TESLA-369-AURORA")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_quantum_ai()


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Quantum AI for Consciousness Research
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
