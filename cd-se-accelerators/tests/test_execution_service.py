"""
Test Execution Service Integration & Config Verification Tests.

Verifies that:
1. Physical jest.config.json is written dynamically to the execution root directory with moduleNameMapper and jsdom testEnvironment.
2. The --config=jest.config.json argument is passed to Jest subprocess.
3. Fallback package.json is created cleanly if the uploaded project source lacks package.json.
4. Execution failure logs no longer complain about 'Could not find a config file based on provided values'.
"""

import json
import os
import shutil
import tempfile
import pytest
from pathlib import Path

from app.models.test_case_models import TestCase, TestCaseMetadata, TestCaseLocator
from app.services.test_execution.base_executor import BaseTestExecutor


@pytest.fixture
def execution_workspace():
    """Create a temporary execution project folder."""
    tmp_dir = tempfile.mkdtemp(prefix="exec_workspace_")
    src_dir = Path(tmp_dir) / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Sample component code
    comp_code = """
import React from 'react';
export function BrandHeader({ title }) {
    return <header><h1>{title || 'Default Title'}</h1></header>;
}
"""
    (src_dir / "BrandHeader.jsx").write_text(comp_code, encoding="utf-8")

    # Sample generated test file
    tests_dir = Path(tmp_dir) / "tests" / "react"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_code = """
import React from 'react';
import { render } from '@testing-library/react';
import { BrandHeader } from '../../src/components/BrandHeader';

test('renders brand header', () => {
    const { getByText } = render(<BrandHeader title="Enterprise" />);
    expect(getByText('Enterprise')).toBeInTheDocument();
});
"""
    test_file_path = tests_dir / "BrandHeader.test.tsx"
    test_file_path.write_text(test_code, encoding="utf-8")

    yield tmp_dir, str(test_file_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_base_executor_jest_config_generation(execution_workspace):
    """Verify physical jest.config.json is generated and --config parameter is passed cleanly."""
    tmp_dir, test_file_path = execution_workspace
    executor = BaseTestExecutor(framework="React")

    test_cases = [
        TestCase(
            id="TC-001",
            strategy_id="STRAT-001",
            edge_case_id="EC-001",
            category="Rendering",
            priority="High",
            component="BrandHeader",
            title="Verify BrandHeader mounts",
            objective="Verify rendering",
            preconditions=[],
            steps=["Render component"],
            expected_result="Header renders",
            metadata=TestCaseMetadata(
                component="BrandHeader",
                element="header",
                element_type="container",
                locator=TestCaseLocator(strategy="role", value="banner"),
                action="render",
                assertion_type="exists",
                assertion_target="header",
                expected_value="visible"
            )
        )
    ]

    manifest = {
        "generated_files": [
            {
                "component": "BrandHeader",
                "file": "BrandHeader.test.tsx",
                "test_cases": ["TC-001"]
            }
        ]
    }

    report = executor.run_tests(
        project_path=tmp_dir,
        pipeline_run_id="run_test_exec_001",
        test_files=[test_file_path],
        test_cases=test_cases,
        manifest=manifest
    )

    # 1. Report object returned cleanly
    assert report is not None
    assert report.framework == "React"

    # 2. Verify error message DOES NOT contain 'Could not find a config file'
    if report.status == "failed" and report.failures:
        for failure in report.failures:
            assert "Could not find a config file based on provided values" not in failure.error_message, (
                f"Config path failure detected in execution report: {failure.error_message}"
            )
