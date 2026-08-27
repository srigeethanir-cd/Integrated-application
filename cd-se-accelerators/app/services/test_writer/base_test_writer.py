"""
Base Test Writer – Module 8.

Defines the abstract interface that all concrete framework-specific test
writers must implement.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.test_case_models import TestCase
from app.models.test_writer_models import GeneratedTestFile


class BaseTestWriter(ABC):
    """Abstract base class for React and Angular test file generators."""

    @property
    @abstractmethod
    def framework(self) -> str:
        """Name of the framework supported by this writer (e.g. 'React')."""
        pass

    @abstractmethod
    def write(self, test_cases: List[TestCase], output_dir: str) -> List[GeneratedTestFile]:
        """Compile test cases and write them to output directories.

        Args:
            test_cases: List of TestCase models to compile.
            output_dir: Root output directory path.

        Returns:
            List[GeneratedTestFile] compiled code models.
        """
        pass
