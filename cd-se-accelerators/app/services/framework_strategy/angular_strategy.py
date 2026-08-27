"""
Angular Framework Strategy – Strategy implementation for Angular applications.

Delegates analysis, context extraction, test generation, test writing, and execution
to Angular-specific tools (Angular AST parser, Angular TestBed, AngularTestExecutor).
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.test_case_models import TestCase, TestCasePlanResponse
from app.models.test_execution_models import TestExecutionReport
from app.models.test_writer_models import TestWriterResponse
from app.services.framework_strategy.base_framework_strategy import BaseFrameworkStrategy
from app.services.project_analyzer.angular_parser import AngularParser
from app.services.frontend_context.context_engine import FrontendContextEngine
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService
from app.services.test_writer.angular_test_writer import AngularTestWriter
from app.services.test_execution.angular_executor import AngularTestExecutor

logger = logging.getLogger(__name__)


class AngularStrategy(BaseFrameworkStrategy):
    """Encapsulates Angular-specific pipeline lifecycle behaviors."""

    def __init__(self) -> None:
        self._parser = AngularParser()
        self._fce_engine = FrontendContextEngine()
        self._test_case_generator = TestCaseGeneratorService()
        self._test_writer = AngularTestWriter()
        self._executor = AngularTestExecutor()

    @property
    def framework_name(self) -> str:
        return "Angular"

    def analyze_source(
        self,
        project_path: str,
        project_index: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
    ) -> Any:
        """Parse Angular source files using TypeScript Compiler API + @angular/compiler."""
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
        """Extract Angular component context for test case generation."""
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
            framework="Angular",
        )

    def generate_test_cases(
        self,
        strategy_plan: Any,
        edge_case_plan: Optional[Any] = None,
        frontend_context: Optional[Any] = None,
    ) -> TestCasePlanResponse:
        """Generate Angular-specific test cases."""
        res = self._test_case_generator.generate_test_cases(
            strategy_plan=strategy_plan,
            edge_case_plan=edge_case_plan,
            frontend_context=frontend_context,
        )
        if res:
            res.framework = "Angular"
        return res

    def generate_test_files(
        self,
        test_case_plan: TestCasePlanResponse,
        output_dir: str,
        pipeline_run_id: Optional[str] = None,
    ) -> TestWriterResponse:
        """Compile Angular test cases into .spec.ts unit test files with TestBed."""
        cases = getattr(test_case_plan, "test_cases", []) or []
        files = self._test_writer.write(cases, output_dir)
        return TestWriterResponse(
            status="completed",
            framework="Angular",
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
        """Execute Angular tests using Jest + Angular TestBed."""
        return self._executor.run_tests(
            project_path=project_path,
            pipeline_run_id=pipeline_run_id,
            test_files=test_files,
            test_cases=test_cases,
            manifest=manifest,
        )
