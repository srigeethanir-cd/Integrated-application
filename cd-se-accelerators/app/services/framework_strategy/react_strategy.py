"""
React Framework Strategy – Strategy implementation for React & Next.js applications.

Delegates analysis, context extraction, test generation, test writing, and execution
to React-specific tools (Babel AST parser, React Testing Library, ReactTestExecutor).
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.test_case_models import TestCase, TestCasePlanResponse
from app.models.test_execution_models import TestExecutionReport
from app.models.test_writer_models import TestWriterResponse
from app.services.framework_strategy.base_framework_strategy import BaseFrameworkStrategy
from app.services.project_analyzer.react_parser import ReactParser
from app.services.frontend_context.context_engine import FrontendContextEngine
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService
from app.services.test_writer.react_test_writer import ReactTestWriter
from app.services.test_execution.react_executor import ReactTestExecutor

logger = logging.getLogger(__name__)


class ReactStrategy(BaseFrameworkStrategy):
    """Encapsulates React-specific pipeline lifecycle behaviors."""

    def __init__(self) -> None:
        self._parser = ReactParser()
        self._fce_engine = FrontendContextEngine()
        self._test_case_generator = TestCaseGeneratorService()
        self._test_writer = ReactTestWriter()
        self._executor = ReactTestExecutor()

    @property
    def framework_name(self) -> str:
        return "React"

    def analyze_source(
        self,
        project_path: str,
        project_index: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
    ) -> Any:
        """Parse React files using Babel AST parser."""
        from pathlib import Path
        return self._parser.parse(Path(project_path))

    def extract_frontend_context(
        self,
        analysis_result: Any,
        project_path: str,
        project_name: str,
        project_id: str,
        pipeline_run_id: str,
    ) -> Any:
        """Extract React context for test case generation."""
        an_dict = (
            analysis_result.model_dump()
            if hasattr(analysis_result, "model_dump")
            else (analysis_result if isinstance(analysis_result, dict) else {})
        )
        return self._fce_engine.extract_context(
            analysis_result=an_dict,
            project_path=project_path,
            project_name=project_name,
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            framework="React",
        )

    def generate_test_cases(
        self,
        strategy_plan: Any,
        edge_case_plan: Optional[Any] = None,
        frontend_context: Optional[Any] = None,
    ) -> TestCasePlanResponse:
        """Generate React-specific test cases."""
        return self._test_case_generator.generate_test_cases(
            strategy_plan=strategy_plan,
            edge_case_plan=edge_case_plan,
            frontend_context=frontend_context,
        )

    def generate_test_files(
        self,
        test_case_plan: TestCasePlanResponse,
        output_dir: str,
        pipeline_run_id: Optional[str] = None,
    ) -> TestWriterResponse:
        """Compile test cases into React Testing Library .test.jsx/.test.tsx files."""
        cases = getattr(test_case_plan, "test_cases", []) or []
        files = self._test_writer.write(cases, output_dir)
        return TestWriterResponse(
            status="completed",
            framework="React",
            output_directory=output_dir,
            total_files=len(files),
            files=files,
            pipeline_run_id=pipeline_run_id,
        )

    def execute_tests(
        self,
        project_path: str,
        pipeline_run_id: str,
        test_files: List[str],
        test_cases: List[TestCase],
        manifest: Dict[str, Any],
    ) -> TestExecutionReport:
        """Execute React tests using Jest + React Testing Library."""
        return self._executor.run_tests(
            project_path=project_path,
            pipeline_run_id=pipeline_run_id,
            test_files=test_files,
            test_cases=test_cases,
            manifest=manifest,
        )
