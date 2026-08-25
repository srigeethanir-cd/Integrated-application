"""
Tests for Post-TestCase Generation Workflow:
- TestWriterService & ReactTestWriter
- BaseTestExecutor & Jest parsing
- ReportGeneratorService (Quality Score, Passed Reasons, Failure Analysis, Markdown/JSON reports)
- End-to-end post-testcase pipeline persistence
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest

from app.models.test_case_models import (
    TestCase,
    TestCaseLocator,
    TestCaseMetadata,
    TestCasePlanResponse,
    TestCaseTraceability,
)
from app.models.test_execution_models import (
    CoverageReport,
    TestExecutionReport,
    TestFailure,
    TestFileResult,
)
from app.services.test_writer.test_writer_service import TestWriterService
from app.services.test_writer.react_test_writer import ReactTestWriter
from app.services.report_generator.report_generator_service import ReportGeneratorService


def test_react_test_writer_generates_component_test_files():
    writer = ReactTestWriter()
    test_cases = [
        TestCase(
            id="TC-LOGIN-001",
            strategy_id="STRAT-001",
            edge_case_id="EC-001",
            component="LoginForm",
            category="Forms",
            priority="High",
            title="Verify handleSubmit executes on form submission",
            target_function="handleSubmit()",
            source_file="src/components/LoginForm.jsx",
            objective="Submit login form with valid credentials",
            expected_result="Calls login API and updates token state",
            steps=["Enter email", "Enter password", "Click submit"],
            metadata=TestCaseMetadata(
                component="LoginForm",
                element="form",
                element_type="form",
                locator=TestCaseLocator(strategy="tag", value="form"),
                action="submit",
                assertion_type="validation",
                assertion_target="form",
                mock_required=True,
                mock_services=["AuthService"]
            ),
            traceability=TestCaseTraceability(
                strategy_id="STRAT-001",
                edge_case_id="EC-001",
                component_id="LoginForm"
            )
        ),
        TestCase(
            id="TC-LOGIN-002",
            strategy_id="STRAT-002",
            edge_case_id="EC-002",
            component="LoginForm",
            category="State",
            priority="Medium",
            title="Verify handleEmailChange updates state on input",
            target_function="handleEmailChange()",
            source_file="src/components/LoginForm.jsx",
            objective="User inputs email into text field",
            expected_result="State email is updated",
            steps=["Enter email"],
            metadata=TestCaseMetadata(
                component="LoginForm",
                element="input",
                element_type="input",
                locator=TestCaseLocator(strategy="role", value="textbox"),
                action="type",
                assertion_type="state_value",
                assertion_target="email"
            ),
            traceability=TestCaseTraceability(
                strategy_id="STRAT-002",
                edge_case_id="EC-002",
                component_id="LoginForm"
            )
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = writer.write(test_cases, tmp_dir)
        assert len(generated) == 1
        gf = generated[0]
        assert gf.file_name == "LoginForm.test.jsx"
        assert "TC-LOGIN-001" in gf.content
        assert "TC-LOGIN-002" in gf.content
        assert "LoginForm Tests" in gf.content
        assert "render(<LoginForm" in gf.content


def test_test_writer_service_manifest_and_storage():
    service = TestWriterService()
    test_cases = [
        TestCase(
            id="TC-COUNTER-001",
            strategy_id="STRAT-C1",
            edge_case_id="EC-C1",
            component="Counter",
            category="Events",
            priority="High",
            title="Verify handleIncrement updates count on click",
            target_function="handleIncrement()",
            source_file="src/components/Counter.jsx",
            objective="Click increment button",
            expected_result="Count increments by 1",
            steps=["Click button"],
            metadata=TestCaseMetadata(
                component="Counter",
                element="button",
                element_type="button",
                locator=TestCaseLocator(strategy="role", value="button"),
                action="click",
                assertion_type="exists",
                assertion_target="button"
            ),
            traceability=TestCaseTraceability(
                strategy_id="STRAT-C1",
                edge_case_id="EC-C1",
                component_id="Counter"
            )
        )
    ]

    plan = TestCasePlanResponse(
        pipeline_run_id="run_test_writer_123",
        project_name="CounterApp",
        framework="React",
        total_test_cases=1,
        test_cases=test_cases
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        resp = service.generate_test_suite(plan, output_workspace_dir=tmp_dir, pipeline_run_id="run_test_writer_123")
        assert resp.total_files == 1
        assert os.path.exists(resp.manifest_path)

        with open(resp.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["pipeline_run_id"] == "run_test_writer_123"
        assert manifest["framework"] == "React"
        assert len(manifest["generated_files"]) == 1
        gf_info = manifest["generated_files"][0]
        assert gf_info["component"] == "Counter"
        assert "TC-COUNTER-001" in gf_info["test_case_ids"]
        assert gf_info["source_file"] == "src/components/Counter.jsx"


def test_report_generator_quality_score_and_passed_reasons():
    service = ReportGeneratorService()

    exec_report = TestExecutionReport(
        pipeline_run_id="run_report_456",
        status="completed",
        framework="React",
        total_tests=10,
        passed=9,
        failed=1,
        skipped=0,
        pass_rate=90.0,
        execution_time_ms=2500.0,
        coverage=CoverageReport(
            statements=88.0,
            branches=82.0,
            functions=90.0,
            lines=86.0
        ),
        test_files=[
            TestFileResult(
                file_name="LoginForm.test.jsx",
                file_path="tests/react/LoginForm.test.jsx",
                framework="React",
                component="LoginForm",
                total_tests=10,
                passed=9,
                failed=1,
                skipped=0,
                test_case_ids=["TC-LOGIN-001", "TC-LOGIN-002"]
            )
        ],
        failures=[
            TestFailure(
                test_case_id="TC-LOGIN-002",
                file_name="LoginForm.test.jsx",
                test_name="Verify error banner renders on failure",
                error_message="Expected element with text 'Invalid credentials' not found in document.",
                expected="Invalid credentials",
                received="null",
                line_number="42"
            )
        ]
    )

    test_cases = [
        TestCase(
            id="TC-LOGIN-001",
            strategy_id="STRAT-001",
            edge_case_id="EC-001",
            component="LoginForm",
            category="Forms",
            priority="High",
            title="Verify handleSubmit submits form",
            target_function="handleSubmit()",
            objective="Submit login",
            expected_result="Logs in user",
            steps=["Submit"],
            metadata=TestCaseMetadata(
                component="LoginForm",
                element="form",
                element_type="form",
                locator=TestCaseLocator(strategy="tag", value="form"),
                action="submit",
                assertion_type="validation",
                assertion_target="form"
            ),
            traceability=TestCaseTraceability(
                strategy_id="STRAT-001",
                edge_case_id="EC-001",
                component_id="LoginForm"
            )
        ),
        TestCase(
            id="TC-LOGIN-002",
            strategy_id="STRAT-002",
            edge_case_id="EC-002",
            component="LoginForm",
            category="Services",
            priority="High",
            title="Verify error banner renders on failure",
            target_function="handleSubmit()",
            objective="Failed login",
            expected_result="Shows banner",
            steps=["Submit"],
            metadata=TestCaseMetadata(
                component="LoginForm",
                element="form",
                element_type="form",
                locator=TestCaseLocator(strategy="tag", value="form"),
                action="submit",
                assertion_type="validation",
                assertion_target="form"
            ),
            traceability=TestCaseTraceability(
                strategy_id="STRAT-002",
                edge_case_id="EC-002",
                component_id="LoginForm"
            )
        )
    ]

    plan = TestCasePlanResponse(
        pipeline_run_id="run_report_456",
        project_name="LoginFormApp",
        framework="React",
        total_test_cases=2,
        test_cases=test_cases
    )

    # 1. Quality Score
    q_score = service.calculate_quality_score(exec_report, plan, None)
    assert q_score["overall_score"] > 80
    assert q_score["execution_score"] == 90.0
    assert q_score["coverage_status"] == "available"
    assert q_score["traceability_score"] == 100.0

    # 2. Passed Reasons
    reasons = service.generate_passed_reasons(test_cases, exec_report)
    assert len(reasons) == 1
    assert reasons[0]["test_case_id"] == "TC-LOGIN-001"
    assert "LoginForm" in reasons[0]["reason"]
    assert "meaningless" not in reasons[0]["reason"]

    # 3. Report Generation & Persistence
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = service.generate_report(
            project_path=tmp_dir,
            pipeline_run_id="run_report_456",
            execution_report=exec_report,
            test_case_plan=plan
        )
        assert report["quality_score"]["overall_score"] > 80
        assert len(report["passed_tests"]) == 1
        assert len(report["failures"]) == 1
        assert os.path.exists(os.path.join(tmp_dir, "project-1", "reports", "test_report.json"))
        assert os.path.exists(os.path.join(tmp_dir, "project-1", "reports", "test_report.md"))

        with open(os.path.join(tmp_dir, "project-1", "reports", "test_report.md"), "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "# Test Execution & Quality Report" in md_content
            assert "## TEST EXECUTION SUMMARY" in md_content
            assert "## WHY TESTS PASSED" in md_content
            assert "## FAILURE REPORT" in md_content


def test_framework_and_source_language_aware_generation():
    """Verify component-level source language detection for .jsx, .js, .tsx, .ts."""
    writer = ReactTestWriter()
    service = TestWriterService()

    test_cases = [
        TestCase(
            id="TC-LOGIN-001",
            strategy_id="STRAT-1",
            edge_case_id="EC-1",
            component="LoginForm",
            category="Forms",
            priority="High",
            title="Verify LoginForm jsx behavior",
            target_function="handleSubmit()",
            source_file="src/components/LoginForm.jsx",
            objective="Form submit",
            expected_result="Submits form",
            steps=["Submit"],
            metadata=TestCaseMetadata(
                component="LoginForm",
                element="form",
                element_type="form",
                locator=TestCaseLocator(strategy="tag", value="form"),
                action="submit",
                assertion_type="validation",
                assertion_target="form"
            ),
            traceability=TestCaseTraceability(strategy_id="STRAT-1", edge_case_id="EC-1", component_id="LoginForm")
        ),
        TestCase(
            id="TC-PWD-001",
            strategy_id="STRAT-2",
            edge_case_id="EC-2",
            component="PasswordInput",
            category="Input",
            priority="Medium",
            title="Verify PasswordInput js behavior",
            target_function="handleChange()",
            source_file="src/components/PasswordInput.js",
            objective="Input password",
            expected_result="Updates password state",
            steps=["Type password"],
            metadata=TestCaseMetadata(
                component="PasswordInput",
                element="input",
                element_type="input",
                locator=TestCaseLocator(strategy="role", value="textbox"),
                action="type",
                assertion_type="state_value",
                assertion_target="password"
            ),
            traceability=TestCaseTraceability(strategy_id="STRAT-2", edge_case_id="EC-2", component_id="PasswordInput")
        ),
        TestCase(
            id="TC-USER-001",
            strategy_id="STRAT-3",
            edge_case_id="EC-3",
            component="UserProfile",
            category="Profile",
            priority="High",
            title="Verify UserProfile tsx behavior",
            target_function="render()",
            source_file="src/components/UserProfile.tsx",
            objective="Render user profile",
            expected_result="Displays avatar",
            steps=["Render"],
            metadata=TestCaseMetadata(
                component="UserProfile",
                element="div",
                element_type="div",
                locator=TestCaseLocator(strategy="tag", value="div"),
                action="render",
                assertion_type="exists",
                assertion_target="avatar"
            ),
            traceability=TestCaseTraceability(strategy_id="STRAT-3", edge_case_id="EC-3", component_id="UserProfile")
        ),
        TestCase(
            id="TC-DASH-001",
            strategy_id="STRAT-4",
            edge_case_id="EC-4",
            component="Dashboard",
            category="Analytics",
            priority="Low",
            title="Verify Dashboard ts behavior",
            target_function="calculateMetrics()",
            source_file="src/utils/Dashboard.ts",
            objective="Compute metrics",
            expected_result="Returns metric object",
            steps=["Call metrics"],
            metadata=TestCaseMetadata(
                component="Dashboard",
                element="function",
                element_type="function",
                locator=TestCaseLocator(strategy="tag", value="function"),
                action="render",
                assertion_type="exists",
                assertion_target="metrics"
            ),
            traceability=TestCaseTraceability(strategy_id="STRAT-4", edge_case_id="EC-4", component_id="Dashboard")
        )
    ]

    plan = TestCasePlanResponse(
        pipeline_run_id="run_lang_aware_999",
        project_name="MultiLanguageApp",
        framework="React",
        total_test_cases=4,
        test_cases=test_cases
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        resp = service.generate_test_suite(plan, output_workspace_dir=tmp_dir, pipeline_run_id="run_lang_aware_999")
        assert resp.total_files == 4
        assert os.path.exists(resp.manifest_path)

        with open(resp.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        gen_files = {gf["component"]: gf for gf in manifest["generated_files"]}

        # 1. LoginForm.jsx -> LoginForm.test.jsx
        assert gen_files["LoginForm"]["file_name"] == "LoginForm.test.jsx"
        assert gen_files["LoginForm"]["source_extension"] == ".jsx"
        assert gen_files["LoginForm"]["source_language"] == "JavaScript"
        assert gen_files["LoginForm"]["test_extension"] == ".test.jsx"

        # 2. PasswordInput.js -> PasswordInput.test.js
        assert gen_files["PasswordInput"]["file_name"] == "PasswordInput.test.js"
        assert gen_files["PasswordInput"]["source_extension"] == ".js"
        assert gen_files["PasswordInput"]["source_language"] == "JavaScript"
        assert gen_files["PasswordInput"]["test_extension"] == ".test.js"

        # 3. UserProfile.tsx -> UserProfile.test.tsx
        assert gen_files["UserProfile"]["file_name"] == "UserProfile.test.tsx"
        assert gen_files["UserProfile"]["source_extension"] == ".tsx"
        assert gen_files["UserProfile"]["source_language"] == "TypeScript"
        assert gen_files["UserProfile"]["test_extension"] == ".test.tsx"

        # 4. Dashboard.ts -> Dashboard.test.ts
        assert gen_files["Dashboard"]["file_name"] == "Dashboard.test.ts"
        assert gen_files["Dashboard"]["source_extension"] == ".ts"
        assert gen_files["Dashboard"]["source_language"] == "TypeScript"
        assert gen_files["Dashboard"]["test_extension"] == ".test.ts"

