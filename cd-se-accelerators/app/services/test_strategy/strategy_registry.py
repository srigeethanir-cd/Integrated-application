"""
Strategy Registry – Module 5.

Maintains registered ``BaseStrategyGenerator`` implementations.
Eliminates hardcoded if/else logic when executing strategy generation routines.
"""

import logging
from typing import List
from app.services.test_strategy.base_generator import BaseStrategyGenerator

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry maintaining active strategy generators."""

    def __init__(self) -> None:
        self._generators: List[BaseStrategyGenerator] = []

    def register(self, generator: BaseStrategyGenerator) -> None:
        """Register a strategy generator.

        Args:
            generator: BaseStrategyGenerator instance.
        """
        self._generators.append(generator)
        logger.info("Registered Strategy Generator: %s", generator.category_name)

    def get_generators(self) -> List[BaseStrategyGenerator]:
        """Return all registered strategy generators."""
        return list(self._generators)
