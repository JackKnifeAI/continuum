"""
Base class for all S-HAI Thrusts.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging

from ..verdict import Verdict


logger = logging.getLogger(__name__)


class BaseThrust(ABC):
    """
    Abstract base class for Truth Council thrusts.

    Each thrust provides an independent analytical perspective on claims.
    Thrusts must be:
    - Independent: No shared state between thrusts
    - Deterministic: Same input should produce same output
    - Transparent: Full reasoning must be provided
    """

    name: str = "base"
    description: str = "Base thrust class"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize thrust with optional configuration.

        Args:
            config: Thrust-specific configuration options
        """
        self.config = config or {}
        self._evaluation_count = 0
        logger.info(f"Initialized {self.name} thrust")

    @abstractmethod
    def evaluate(self, claim: str, context: Optional[Dict[str, Any]] = None) -> Verdict:
        """
        Evaluate a claim and return a verdict.

        Args:
            claim: The claim to evaluate
            context: Optional additional context for evaluation

        Returns:
            Verdict with support decision, confidence, and reasoning
        """
        pass

    def _log_evaluation(self, claim: str, verdict: Verdict) -> None:
        """Log evaluation for auditing."""
        self._evaluation_count += 1
        logger.debug(
            f"[{self.name}] Evaluated claim #{self._evaluation_count}: "
            f"supports={verdict.supports}, confidence={verdict.confidence:.2f}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get thrust statistics."""
        return {
            "name": self.name,
            "description": self.description,
            "evaluation_count": self._evaluation_count,
            "config": self.config,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(evaluations={self._evaluation_count})"
