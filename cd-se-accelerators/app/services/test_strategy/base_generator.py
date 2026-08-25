"""
Base Strategy Generator ABC – Module 5.

Defines the contract for strategy generators. Subclasses inspect parts of
the FrameworkAgnosticIR and generate specialized TestStrategy objects.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import TestStrategy


class BaseStrategyGenerator(ABC):
    """Abstract strategy generator interface."""

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Category name targeted by this strategy generator."""
        ...

    @abstractmethod
    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        """Inspect the IR and generate category-specific TestStrategy instances.

        Args:
            ir: Validated FrameworkAgnosticIR.

        Returns:
            List of generated ``TestStrategy`` objects.
        """
        ...
