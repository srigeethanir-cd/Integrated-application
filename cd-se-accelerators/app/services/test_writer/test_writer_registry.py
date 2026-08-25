"""
Test Writer Registry – Module 8.

Maintains registrations of concrete framework test writers to decouple
framework lookup from code paths.
"""

from typing import Dict
from app.services.test_writer.base_test_writer import BaseTestWriter


class TestWriterRegistry:
    """Registry to register and fetch test writers dynamically."""

    def __init__(self) -> None:
        self._writers: Dict[str, BaseTestWriter] = {}

    def register(self, writer: BaseTestWriter) -> None:
        """Register a new test writer instance."""
        self._writers[writer.framework.lower()] = writer

    def get_writer(self, framework: str) -> BaseTestWriter | None:
        """Fetch a writer matching the framework name, case-insensitively."""
        return self._writers.get(framework.lower())
