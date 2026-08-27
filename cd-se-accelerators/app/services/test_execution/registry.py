"""
Test Execution Registry – Module 10.

Manages framework test executors registration and retrieval.
"""

from typing import Dict, Optional
from app.services.test_execution.base_executor import BaseTestExecutor
from app.services.test_execution.react_executor import ReactTestExecutor
from app.services.test_execution.angular_executor import AngularTestExecutor


class TestExecutionRegistry:
    """Registry mapping frontend framework names to appropriate test executors."""

    def __init__(self) -> None:
        self._executors: Dict[str, BaseTestExecutor] = {}

    def register(self, executor: BaseTestExecutor) -> None:
        """Register a test executor for its defined framework."""
        self._executors[executor.framework.lower()] = executor

    def get_executor(self, framework: str) -> Optional[BaseTestExecutor]:
        """Retrieve test executor mapped to framework name (case-insensitive)."""
        return self._executors.get(framework.lower())


def build_default_test_execution_registry() -> TestExecutionRegistry:
    """Construct a registry pre-loaded with React and Angular executors."""
    registry = TestExecutionRegistry()
    registry.register(ReactTestExecutor())
    registry.register(AngularTestExecutor())
    return registry
