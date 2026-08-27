"""
Base Framework Strategy – Abstract interface for framework-specific pipeline execution.

Ensures React and Angular follow the exact same 9-stage pipeline lifecycle,
while providing framework-specific source analysis, context extraction,
test-case generation, test-file compilation, and test execution logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.models.test_case_models import TestCase, TestCasePlanResponse
from app.models.test_execution_models import TestExecutionReport
from app.models.test_writer_models import TestWriterResponse


class BaseFrameworkStrategy(ABC):
    """Abstract base class defining framework-specific strategy contracts."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Return framework identifier string, e.g., 'React' or 'Angular'."""
        pass

    @abstractmethod
    def analyze_source(
        self,
        project_path: str,
        project_index: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
    ) -> Any:
        """Perform deep AST / source analysis for target framework."""
        pass

    @abstractmethod
    def extract_frontend_context(
        self,
        analysis_result: Any,
        project_path: str,
        project_name: str,
        project_id: str,
        pipeline_run_id: str,
    ) -> Any:
        """Extract component context for LLM prompt context."""
        pass

    @abstractmethod
    def generate_test_cases(
        self,
        strategy_plan: Any,
        edge_case_plan: Optional[Any] = None,
        frontend_context: Optional[Any] = None,
    ) -> TestCasePlanResponse:
        """Generate framework-specific test cases from strategy and edge cases."""
        pass

    @abstractmethod
    def generate_test_files(
        self,
        test_case_plan: TestCasePlanResponse,
        output_dir: str,
        pipeline_run_id: Optional[str] = None,
    ) -> TestWriterResponse:
        """Compile test cases into framework-specific executable test files."""
        pass

    @abstractmethod
    def execute_tests(
        self,
        project_path: str,
        pipeline_run_id: str,
        test_files: List[str],
        test_cases: List[TestCase],
        manifest: Dict[str, Any],
    ) -> TestExecutionReport:
        """Execute test suite using framework executor (RTL vs Angular TestBed)."""
        pass
