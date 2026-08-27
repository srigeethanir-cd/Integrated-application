"""
React Test Executor – Module 10.

Implements Jest + React Testing Library specific test suite executor.
"""

from app.services.test_execution.base_executor import BaseTestExecutor


class ReactTestExecutor(BaseTestExecutor):
    """Executes React unit tests utilizing Jest + React Testing Library (RTL)."""

    def __init__(self) -> None:
        super().__init__(framework="React")
