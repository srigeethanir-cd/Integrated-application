"""
Test Case Generator Registry – Module 7.

Maintains the set of registered concrete test case generators and
facilitates dispatching strategy & edge case mapping tasks without
hardcoded conditionals.
"""

from typing import List
from app.services.test_case_generator.base_generator import BaseTestCaseGenerator


class TestCaseRegistry:
    """Registry pattern implementation for Module 7 generators."""

    def __init__(self) -> None:
        self._generators: List[BaseTestCaseGenerator] = []

    def register(self, generator: BaseTestCaseGenerator) -> None:
        """Register a new test case generator."""
        self._generators.append(generator)

    def get_generators(self) -> List[BaseTestCaseGenerator]:
        """Retrieve all currently registered generators."""
        return self._generators
