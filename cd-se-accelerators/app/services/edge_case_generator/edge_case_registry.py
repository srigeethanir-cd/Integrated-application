"""
Edge Case Registry – Module 6.

Maintains registered ``BaseEdgeCaseGenerator`` implementations.
Eliminates hardcoded if/else logic when executing edge case generation routines.
"""

import logging
from typing import List
from app.services.edge_case_generator.base_generator import BaseEdgeCaseGenerator

logger = logging.getLogger(__name__)


class EdgeCaseRegistry:
    """Registry maintaining active edge case generators."""

    def __init__(self) -> None:
        self._generators: List[BaseEdgeCaseGenerator] = []

    def register(self, generator: BaseEdgeCaseGenerator) -> None:
        """Register an edge case generator.

        Args:
            generator: BaseEdgeCaseGenerator instance.
        """
        self._generators.append(generator)
        logger.info("Registered Edge Case Generator: %s", generator.category_name)

    def get_generators(self) -> List[BaseEdgeCaseGenerator]:
        """Return all registered edge case generators."""
        return list(self._generators)
