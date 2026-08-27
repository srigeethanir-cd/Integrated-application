import os
import json
import logging
from typing import Any, Dict, List
from app.models.test_case_models import TestCase
from app.models.test_execution_models import TestExecutionReport
from app.services.test_execution.base_executor import BaseTestExecutor

logger = logging.getLogger(__name__)


class AngularTestExecutor(BaseTestExecutor):
    """Executes Angular unit tests utilizing Jest + TestBed."""

    def __init__(self) -> None:
        super().__init__(framework="Angular")

    def run_tests(
        self,
        project_path: str,
        pipeline_run_id: str,
        test_files: List[str],
        test_cases: List[TestCase],
        manifest: Dict[str, Any],
    ) -> TestExecutionReport:
        """Inspect Angular project for existing test configuration and run Jest."""
        logger.info("AngularTestExecutor: Inspecting Angular workspace config at %s", project_path)

        # Inspect for existing Angular & Jest configurations
        has_angular_json = os.path.exists(os.path.join(project_path, "angular.json"))
        has_tsconfig = os.path.exists(os.path.join(project_path, "tsconfig.json"))
        has_existing_jest_config = any(
            os.path.exists(os.path.join(project_path, cfg))
            for cfg in ["jest.config.js", "jest.config.ts", "jest.config.json"]
        )

        logger.info(
            "Angular workspace inspection: angular.json=%s, tsconfig.json=%s, existing_jest_config=%s",
            has_angular_json,
            has_tsconfig,
            has_existing_jest_config,
        )

        # Delegate to BaseTestExecutor for subprocess execution & real Jest coverage collection
        return super().run_tests(
            project_path=project_path,
            pipeline_run_id=pipeline_run_id,
            test_files=test_files,
            test_cases=test_cases,
            manifest=manifest,
        )

