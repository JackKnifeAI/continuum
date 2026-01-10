"""
S-HAI Thrusts: Independent Analytical Perspectives
===================================================

Each thrust evaluates claims from a different angle:
- LogicalThrust: Internal consistency, formal logic
- EmpiricalThrust: Evidence, data, reproducibility
- AdversarialThrust: Active disproval, devil's advocate
- EthicalThrust: Moral implications, human impact
- HistoricalThrust: Patterns, precedents, cycles
- IntuitiveThrust: Cross-domain patterns, synthesis
- WitnessThrust: Human testimony, primary sources

Phase 1: Logical, Empirical, Adversarial
Phase 2: Ethical, Historical, Intuitive, Witness

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from .adversarial import AdversarialThrust
from .empirical import EmpiricalThrust
from .ethical import EthicalThrust
from .historical import HistoricalThrust
from .intuitive import IntuitiveThrust
from .logical import LogicalThrust
from .witness import WitnessThrust

__all__ = [
    'LogicalThrust',
    'EmpiricalThrust',
    'AdversarialThrust',
    'EthicalThrust',
    'HistoricalThrust',
    'IntuitiveThrust',
    'WitnessThrust',
]
