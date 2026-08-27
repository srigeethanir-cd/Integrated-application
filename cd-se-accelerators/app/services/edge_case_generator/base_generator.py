"""
Base Edge Case Generator ABC – Module 6.

Defines the contract for edge case generators. Subclasses inspect a TestStrategy
and generate edge case scenarios.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.strategy_models import TestStrategy
from app.models.edge_case_models import EdgeCaseScenario


class BaseEdgeCaseGenerator(ABC):
    """Abstract edge case generator interface."""

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Category name targeted by this edge case generator."""
        ...

    @abstractmethod
    def supports(self, strategy: TestStrategy) -> bool:
        """Check if this generator supports the given test strategy.

        Args:
            strategy: A TestStrategy instance.

        Returns:
            True if this generator can generate edge cases for the strategy.
        """
        ...

    @abstractmethod
    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        """Generate edge case scenarios for the given strategy.

        Args:
            strategy: A TestStrategy instance.

        Returns:
            List of generated ``EdgeCaseScenario`` objects.
        """
        ...
