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

Phase 1 implements: Logical, Empirical, Adversarial
"""

from .logical import LogicalThrust
from .empirical import EmpiricalThrust
from .adversarial import AdversarialThrust

__all__ = ['LogicalThrust', 'EmpiricalThrust', 'AdversarialThrust']
