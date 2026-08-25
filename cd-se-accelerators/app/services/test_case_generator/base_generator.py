"""
Base Test Case Generator – Module 7.

Defines the abstract interface that all concrete test case generators
must implement.
"""

from abc import ABC, abstractmethod
from app.models.strategy_models import TestStrategy
from app.models.edge_case_models import EdgeCaseScenario
from app.models.test_case_models import TestCase


class BaseTestCaseGenerator(ABC):
    """Abstract base class for all Module 7 test case generators."""

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Return the category identifier for this generator (e.g. 'Forms')."""
        pass

    @abstractmethod
    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        """Determine if this generator can map the given strategy and edge case combination."""
        pass

    @abstractmethod
    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        """Generate a framework-agnostic TestCase from the given strategy and edge case."""
        pass
