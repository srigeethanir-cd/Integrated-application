import importlib.util
import uuid
from collections import deque
from unittest.mock import Mock

import pytest

from app.database.models.runtime_validation import RuntimeValidationStatus
from app.schemas.runtime_preparation import (
    RuntimeExecutionPlan,
    RuntimeExecutionTarget,
    RuntimePreparationIssue,
)
from app.schemas.test_case import TestCase as Case, UnitTestSpecification
from app.services.runtime.execution_manager import ExecutionManager
from app.services.runtime.dependency_preparer import DependencyPreparationResult
from app.services.runtime.pytest_runner import PytestRunResult, PytestRunner
from app.services.runtime.report_generator import ReportGenerator
from app.services.runtime.result_collector import ResultCollector
from app.services.runtime.runtime_validation_service import (
    RuntimeArtifactNotReadyError,
    RuntimeValidationService,
)
from app.services.runtime.sut_backend_manager import (
    SUT_BASE_URL,
    SUTBackendLease,
    SUTBackendStartupError,
)
from app.services.runtime.test_file_builder import (
    ExecutableTest,
    TestBuildResult as BuildResult,
    TestFileBuilder,
)


def _case(case_id="TC-1", **trace):
    return Case.model_validate({
        "id": case_id,
        "title": "Get health",
        "description": "Check health endpoint",
        "category": "positive",
        "priority": "medium",
        "severity": "minor",
        "steps": ["GET /health"],
        "expected_results": ["HTTP 200"],
        "traceability": {"route": "/health", "method": "GET", "expected_status": 200, **trace},
    })


def test_file_builder_compiles_http_and_marks_missing_runtime_data(tmp_path) -> None:
    result = TestFileBuilder().build(
        [_case(), _case("TC-2", route=None, method=None)],
        workspace=tmp_path,
        base_url="http://127.0.0.1:9999",
    )

    assert result.test_file is not None
    assert "def test_tc_1" in result.test_file.read_text(encoding="utf-8")
    assert result.executable[0].url == "http://127.0.0.1:9999/health"
    assert result.not_executable[0]["runtime_status"] == "NotExecutable"
    assert "route" in result.not_executable[0]["assertion_failure"]


def test_file_builder_compiles_executable_runtime_plan(tmp_path) -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-PLAN",
        route="/projects/{project_id}",
        http_method="PATCH",
        expected_http_status=200,
        path_parameters={"project_id": 7},
        query_parameters={"notify": True},
        request_payload={"name": "Updated"},
        expected_response={"id": 7, "name": "Updated"},
        executable=True,
    )

    result = TestFileBuilder().build(
        [target], workspace=tmp_path, base_url="http://example"
    )

    assert len(result.executable) == 1
    assert result.executable[0].case_id == "TC-PLAN"
    assert result.executable[0].url == (
        "http://example/projects/7?notify=True"
    )
    assert result.not_executable == []


def _unit_case(symbol: str, file: str = "users.py") -> Case:
    return Case(
        id="UT-SYMBOL",
        title="Unit symbol",
        description="Resolve the canonical unit symbol",
        category="positive",
        priority="medium",
        severity="major",
        steps=["Invoke target"],
        expected_results=["Target executes"],
        unit_test=UnitTestSpecification(
            module="users",
            symbol=symbol,
            file=file,
            generated_code=(
                "module = importlib.import_module('users')\n"
                f"target = _resolve_unit_target(module, {symbol!r})\n"
                "args, kwargs = _unit_arguments(target)\n"
                "result = target(*args, **kwargs)"
            ),
        ),
    )


def test_file_builder_repairs_bare_symbol_to_canonical_owner_method(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "users.py").write_text(
        "class UserService:\n"
        "    def create_user(self, email: str):\n"
        "        return email\n",
        encoding="utf-8",
    )

    result = TestFileBuilder().build(
        [_unit_case("create_user")], workspace=tmp_path
    )

    assert len(result.executable) == 1
    generated = result.test_file.read_text(encoding="utf-8")
    assert "_resolve_unit_target(module, 'UserService.create_user')" in generated


def test_file_builder_rejects_unresolved_executable_symbol(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "users.py").write_text(
        "def existing_user():\n    return True\n", encoding="utf-8"
    )

    result = TestFileBuilder().build(
        [_unit_case("create_user")], workspace=tmp_path
    )

    assert result.test_file is None
    assert result.executable == []
    assert result.not_executable[0]["runtime_status"] == "NotExecutable"
    assert "Unresolved executable target" in (
        result.not_executable[0]["assertion_failure"]
    )


def test_semantic_unit_values_are_valid_and_variant_specific(tmp_path) -> None:
    result = TestFileBuilder().build(
        [_case()], workspace=tmp_path, base_url="http://example"
    )
    spec = importlib.util.spec_from_file_location(
        "generated_semantic_values", result.test_file
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module._unit_value(str, "email", "positive") == "user@example.com"
    assert module._unit_value(str, "phone", "boundary") == "4155552671"
    assert module._unit_value(str, "email", "negative") == "invalid-email"
    assert module._unit_value(
        module.inspect.Signature.empty, "email", "positive"
    ) == "user@example.com"
    assert str(module._unit_value(module.UUID, "user_uuid", "positive")) == (
        "00000000-0000-0000-0000-000000000001"
    )
    generated = result.test_file.read_text(encoding="utf-8")
    assert "if isinstance(model_fields, dict)" in generated
    assert 'else getattr(owner, "__fields__", None)' in generated


def test_file_builder_orders_resource_creation_before_dependent_request(
    tmp_path,
) -> None:
    dependent = RuntimeExecutionTarget(
        test_case_id="TC-GET-USER",
        route="/users/{user_id}",
        http_method="GET",
        expected_http_status=200,
        path_parameters={"user_id": 1},
        executable=True,
    )
    creator = RuntimeExecutionTarget(
        test_case_id="TC-CREATE-USER",
        route="/users",
        http_method="POST",
        expected_http_status=201,
        request_payload={"email": "user@example.com"},
        executable=True,
    )

    result = TestFileBuilder().build(
        [dependent, creator],
        workspace=tmp_path,
        base_url="http://example",
    )

    assert [item.case_id for item in result.executable] == [
        "TC-CREATE-USER",
        "TC-GET-USER",
    ]
    generated = result.test_file.read_text(encoding="utf-8")
    assert generated.index("def test_tc_create_user") < generated.index(
        "def test_tc_get_user"
    )


def test_generated_runtime_tests_capture_and_substitute_created_identifier(
    tmp_path,
) -> None:
    creator = RuntimeExecutionTarget(
        test_case_id="TC-CREATE-USER",
        route="/users",
        http_method="POST",
        expected_http_status=201,
        request_payload={"email": "user@example.com"},
        executable=True,
    )
    dependent = RuntimeExecutionTarget(
        test_case_id="TC-GET-USER",
        route="/users/{user_id}",
        http_method="GET",
        expected_http_status=200,
        path_parameters={"user_id": 1},
        executable=True,
    )
    result = TestFileBuilder().build(
        [creator, dependent],
        workspace=tmp_path,
        base_url="http://example",
    )
    spec = importlib.util.spec_from_file_location(
        "generated_runtime_dependency_test", result.test_file
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    create_response = Mock(
        status=201,
        read=Mock(return_value=b'{"id":73,"email":"user@example.com"}'),
    )
    dependent_response = Mock(
        status=200,
        read=Mock(return_value=b'{"id":73,"email":"user@example.com"}'),
    )
    module.urlopen = Mock(side_effect=[create_response, dependent_response])

    getattr(module, result.executable[0].function_name)()
    getattr(module, result.executable[1].function_name)()

    requests = [call.args[0] for call in module.urlopen.call_args_list]
    assert requests[0].full_url == "http://example/users"
    assert requests[1].full_url == "http://example/users/73"
    assert "/users/1" not in requests[1].full_url
    assert module.CAPTURED_IDENTIFIERS["id"] == 73
    assert module.CAPTURED_IDENTIFIERS["user_id"] == 73


def test_generated_runtime_dependency_fails_without_created_identifier(
    tmp_path,
) -> None:
    creator = RuntimeExecutionTarget(
        test_case_id="TC-CREATE-ACCOUNT",
        route="/accounts",
        http_method="POST",
        expected_http_status=201,
        request_payload={"name": "Primary"},
        executable=True,
    )
    dependent = RuntimeExecutionTarget(
        test_case_id="TC-GET-ACCOUNT",
        route="/accounts/{account_id}",
        http_method="GET",
        expected_http_status=200,
        path_parameters={"account_id": 1},
        executable=True,
    )
    result = TestFileBuilder().build(
        [creator, dependent],
        workspace=tmp_path,
        base_url="http://example",
    )
    spec = importlib.util.spec_from_file_location(
        "generated_runtime_missing_identifier_test", result.test_file
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.urlopen = Mock(return_value=Mock(
        status=201,
        read=Mock(return_value=b'{"name":"Primary"}'),
    ))

    with pytest.raises(AssertionError, match="account_id"):
        getattr(module, result.executable[0].function_name)()


def test_pytest_runner_captures_machine_readable_result(tmp_path) -> None:
    test_file = tmp_path / "test_runtime_generated.py"
    test_file.write_text("def test_passes():\n    assert True\n", encoding="utf-8")

    result = PytestRunner().run(test_file, timeout_seconds=30)

    assert result.exit_code == 0
    assert result.junit_path.is_file()
    assert result.duration_ms > 0


def test_result_collector_parses_failure_and_actual_response(tmp_path) -> None:
    junit = tmp_path / "result.xml"
    junit.write_text(
        '<testsuite><testcase name="test_tc_1" time="0.125">'
        '<failure message="status mismatch">details</failure>'
        '</testcase></testsuite>',
        encoding="utf-8",
    )
    sidecars = tmp_path / "runtime-results"
    sidecars.mkdir()
    (sidecars / "test_tc_1.json").write_text(
        '{"actual_result":{"status_code":500},"execution_time_ms":100}',
        encoding="utf-8",
    )
    run = PytestRunResult(1, "stdout", "stderr", 130, junit)
    executable = [ExecutableTest(
        "TC-1", "test_tc_1", "test_tc_1", "GET", "http://example/health",
        {"status_code": 200, "body": None},
    )]

    result = ResultCollector().collect(run, executable, sidecars)[0]

    assert result["runtime_status"] == "Failed"
    assert result["actual_result"] == {"status_code": 500}
    assert "details" in result["assertion_failure"]
    assert result["execution_time_ms"] == 125


def test_execution_manager_coordinates_builder_runner_collector_and_cleanup(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    builder, runner, collector = Mock(), Mock(), Mock()
    executable = [ExecutableTest(
        "TC-1", "test_tc_1", "test_tc_1", "GET", "http://example/health",
        {"status_code": 200},
    )]
    test_file = tmp_path / "placeholder.py"
    builder.build.return_value = BuildResult(test_file, executable, [], tmp_path)
    pytest_result = Mock()
    runner.run.return_value = pytest_result
    collector.collect.return_value = [{
        "test_case_id": "TC-1", "runtime_status": "Passed",
        "expected_result": {}, "actual_result": {}, "assertion_failure": None,
        "logs": None, "execution_time_ms": 1,
    }]
    manager = ExecutionManager(builder, runner, collector, ReportGenerator())

    outcome = manager.execute(
        source_directory=source, test_cases=[_case()],
        base_url="http://example", timeout_seconds=10,
    )

    assert outcome.summary["passed"] == 1
    builder.build.assert_called_once()
    runner.run.assert_called_once()
    collector.collect.assert_called_once()


def test_execution_manager_classifies_dependency_preparation_failure(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    builder, runner, collector, preparer = Mock(), Mock(), Mock(), Mock()
    preparer.prepare.return_value = DependencyPreparationResult(
        success=False,
        error="Dependency preparation failed: email-validator unavailable",
    )
    manager = ExecutionManager(
        builder, runner, collector, ReportGenerator(), preparer
    )

    outcome = manager.execute(
        source_directory=source,
        test_cases=[_case()],
        base_url="http://example",
        timeout_seconds=10,
    )

    assert outcome.results[0]["runtime_status"] == "NotExecutable"
    assert outcome.results[0]["expected_result"]["kind"] == (
        "dependency_preparation"
    )
    assert outcome.summary["runtime_preparation_failures"] == 1
    builder.build.assert_not_called()
    runner.run.assert_not_called()


def _obsolete_runtime_validation_service_loads_stage_six_and_persists_results(tmp_path) -> None:
    project_id, source_run_id = uuid.uuid4(), uuid.uuid4()
    source = tmp_path / "project" / "source"
    source.mkdir(parents=True)
    project = Mock(id=project_id, storage_path=str(tmp_path / "project"))
    source_run = Mock(
        id=source_run_id,
        project_id=project_id,
        status="completed",
        result={"quality_optimization": {"optimized_test_suite": [_case().model_dump(mode="json")]}},
    )
    projects, code_runs, runtime_runs, storage, execution = (
        Mock(), Mock(), Mock(), Mock(), Mock()
    )
    projects.get_by_id.return_value = project
    code_runs.get_by_id.return_value = source_run
    run = Mock(id=uuid.uuid4(), status=RuntimeValidationStatus.PENDING)
    runtime_runs.create_run.return_value = run
    storage.resolve_project_directory.return_value = tmp_path / "project"
    execution.execute.return_value = Mock(
        results=[{"test_case_id": "TC-1", "runtime_status": "Passed"}],
        summary={"passed": 1, "failed": 0, "skipped": 0, "not_executable": 0, "total": 1, "pass_rate": 100},
        duration_ms=10,
    )
    openapi = Mock()
    openapi.load_document.return_value = ({}, None)
    sut = Mock()
    sut.ensure_running.return_value = SUTBackendLease({})
    service = RuntimeValidationService(
        projects, code_runs, runtime_runs, storage, execution, openapi, sut
    )

    result = service.run(
        project_id=project_id,
        code_understanding_run_id=source_run_id,
        base_url="http://127.0.0.1:8001",
        test_case_ids=None,
        timeout_seconds=30,
    )

    assert result is run
    runtime_runs.mark_running.assert_called_once_with(run)
    runtime_runs.complete.assert_called_once()
    execution.execute.assert_called_once()


def _obsolete_runtime_validation_attaches_sut_traceback_to_http_500(caplog) -> None:
    results = [{
        "test_case_id": "TC-500",
        "runtime_status": "Failed",
        "actual_result": {"status_code": 500, "body": "Internal Server Error"},
        "logs": "pytest failure details",
    }]
    output = [
        "INFO: Application startup complete.",
        "ERROR: Exception in ASGI application",
        "Traceback (most recent call last):",
        '  File "app/routers/items.py", line 42, in get_item',
        "sqlalchemy.exc.OperationalError: no such table: items",
    ]

    with caplog.at_level("ERROR"):
        enriched = RuntimeValidationService._attach_sut_tracebacks(
            results, output
        )

    assert "pytest failure details" in enriched[0]["logs"]
    assert "SUT traceback:" in enriched[0]["logs"]
    assert "OperationalError: no such table: items" in enriched[0]["logs"]
    assert "SUT traceback:" in enriched[0]["assertion_failure"]
    assert "OperationalError: no such table: items" in (
        enriched[0]["assertion_failure"]
    )
    assert "OperationalError: no such table: items" in caplog.text
    assert "Application startup complete" not in enriched[0]["logs"]


def _obsolete_runtime_validation_does_not_change_successful_result(caplog) -> None:
    results = [{
        "test_case_id": "TC-200",
        "runtime_status": "Passed",
        "actual_result": {"status_code": 200},
        "logs": None,
    }]

    with caplog.at_level("ERROR"):
        enriched = RuntimeValidationService._attach_sut_tracebacks(
            results,
            [
                "ERROR: Exception in ASGI application",
                "Traceback (most recent call last):",
                "RuntimeError: unrelated historical error",
            ],
        )

    assert enriched is results
    assert enriched[0]["logs"] is None
    assert "Runtime HTTP 500" not in caplog.text


def _obsolete_runtime_validation_persists_sut_traceback_at_repository_boundary(
    tmp_path,
) -> None:
    runtime_runs, execution = Mock(), Mock()
    run = Mock(id=uuid.uuid4())
    runtime_runs.create_run.return_value = run
    execution.execute.return_value = Mock(
        results=[{
            "test_case_id": "TC-500",
            "runtime_status": "Failed",
            "expected_result": {"status_code": 404},
            "actual_result": {"status_code": 500},
            "assertion_failure": "Expected HTTP 404, got 500",
            "logs": "Internal Server Error",
            "execution_time_ms": 1,
        }],
        summary={"passed": 0, "failed": 1, "total": 1, "pass_rate": 0},
        duration_ms=1,
    )
    service = RuntimeValidationService(
        Mock(), Mock(), runtime_runs, Mock(), execution
    )
    lease = SUTBackendLease({}, output=deque([
        "ERROR: Exception in ASGI application",
        "Traceback (most recent call last):",
        "RuntimeError: persisted SUT failure",
    ]))

    service._run_against_backend(
        project_id=uuid.uuid4(),
        project_directory=tmp_path,
        source_run=Mock(id=uuid.uuid4()),
        result={
            "quality_optimization": {
                "optimized_test_suite": [_case().model_dump(mode="json")]
            }
        },
        openapi_document={},
        sut_lease=lease,
        base_url=SUT_BASE_URL,
        test_case_ids=None,
        timeout_seconds=30,
    )

    persisted = runtime_runs.complete.call_args.kwargs["results"][0]
    assert "RuntimeError: persisted SUT failure" in persisted["logs"]
    assert "RuntimeError: persisted SUT failure" in (
        persisted["assertion_failure"]
    )


def test_sut_backend_lease_preserves_empty_process_output_buffer() -> None:
    output = deque(maxlen=400)

    lease = SUTBackendLease({}, output=output)
    output.append("Traceback (most recent call last):")

    assert lease.output is output
    assert list(lease.output) == ["Traceback (most recent call last):"]


def test_sut_backend_lease_waits_for_delayed_diagnostics() -> None:
    output = deque(maxlen=400)
    activity = __import__("threading").Event()
    process = Mock()
    process.poll.return_value = None
    lease = SUTBackendLease(
        {}, process=process, output=output, output_activity=activity
    )

    def emit_traceback() -> None:
        __import__("time").sleep(0.05)
        output.extend([
            "ERROR: Exception in ASGI application",
            "Traceback (most recent call last):",
            "RuntimeError: delayed failure",
        ])
        activity.set()

    thread = __import__("threading").Thread(target=emit_traceback)
    thread.start()
    captured = lease.captured_output(wait_for_diagnostics=True)
    thread.join()

    assert captured[-1] == "RuntimeError: delayed failure"


def _obsolete_runtime_validation_uses_plan_and_reports_preparation_issues(
    tmp_path,
) -> None:
    project_id, source_run_id = uuid.uuid4(), uuid.uuid4()
    project = Mock(id=project_id, storage_path=str(tmp_path / "project"))
    issue = RuntimePreparationIssue(
        test_case_id="TC-SKIP",
        code="request_payload_unresolved",
        message="No supported request payload was found",
    )
    plan = RuntimeExecutionPlan(
        targets=[
            RuntimeExecutionTarget(
                test_case_id="TC-RUN",
                route="/health",
                http_method="GET",
                expected_http_status=200,
                executable=True,
            ),
            RuntimeExecutionTarget(
                test_case_id="TC-SKIP",
                route="/projects",
                http_method="POST",
                expected_http_status=201,
                executable=False,
                issues=[issue],
            ),
        ],
        issues=[issue],
        total_tests=2,
        prepared_tests=1,
        unresolved_tests=1,
    )
    source_run = Mock(
        id=source_run_id,
        project_id=project_id,
        status="completed",
        result={
            "runtime_execution_plan": plan.model_dump(mode="json"),
            # Deliberately unusable: the plan must be the only source.
            "quality_optimization": {"optimized_test_suite": []},
        },
    )
    projects, code_runs, runtime_runs, storage, execution = (
        Mock(), Mock(), Mock(), Mock(), Mock()
    )
    projects.get_by_id.return_value = project
    code_runs.get_by_id.return_value = source_run
    run = Mock(id=uuid.uuid4(), status=RuntimeValidationStatus.PENDING)
    runtime_runs.create_run.return_value = run
    storage.resolve_project_directory.return_value = tmp_path / "project"
    execution.execute.return_value = Mock(
        results=[],
        summary={
            "passed": 0, "failed": 0, "skipped": 0,
            "not_executable": 1, "total": 1, "pass_rate": 0,
        },
        duration_ms=1,
    )
    openapi = Mock()
    openapi.load_document.return_value = ({}, None)
    openapi.complete.side_effect = (
        lambda targets, **_: (targets, None)
    )
    sut = Mock()
    sut.ensure_running.return_value = SUTBackendLease({})
    service = RuntimeValidationService(
        projects, code_runs, runtime_runs, storage, execution, openapi, sut
    )

    service.run(
        project_id=project_id,
        code_understanding_run_id=source_run_id,
        base_url="http://127.0.0.1:8001",
        test_case_ids=None,
        timeout_seconds=30,
    )

    arguments = execution.execute.call_args.kwargs
    assert [item.test_case_id for item in arguments["test_cases"]] == [
        "TC-RUN"
    ]
    assert arguments["preparation_failures"][0]["test_case_id"] == "TC-SKIP"
    assert arguments["preparation_failures"][0]["expected_result"][
        "source"
    ] == "Runtime Preparation"
    assert "payload" in arguments["preparation_failures"][0][
        "assertion_failure"
    ]


def _obsolete_runtime_plan_filters_mixed_targets_by_requested_ids(tmp_path) -> None:
    issue = RuntimePreparationIssue(
        test_case_id="TC-SKIP", code="route_unresolved",
        message="No route",
    )
    plan = RuntimeExecutionPlan(
        targets=[
            RuntimeExecutionTarget(
                test_case_id="TC-RUN", route="/health", http_method="GET",
                expected_http_status=200, executable=True,
            ),
            RuntimeExecutionTarget(
                test_case_id="TC-SKIP", executable=False, issues=[issue],
            ),
        ],
        issues=[issue], total_tests=2, prepared_tests=1,
        unresolved_tests=1,
    )

    executable, failures = RuntimeValidationService._from_runtime_plan(plan)

    assert [target.test_case_id for target in executable] == ["TC-RUN"]
    assert [failure["test_case_id"] for failure in failures] == ["TC-SKIP"]


def _obsolete_runtime_report_preserves_non_http_preparation_reason() -> None:
    message = "Internal helper function (HTTP validation not applicable)"
    issue = RuntimePreparationIssue(
        test_case_id="TC-UNIT",
        code="non_http_test",
        message=message,
    )
    plan = RuntimeExecutionPlan(
        targets=[RuntimeExecutionTarget(
            test_case_id="TC-UNIT",
            classification="UNIT",
            executable=False,
            issues=[issue],
        )],
        issues=[issue],
        total_tests=1,
        prepared_tests=0,
        unresolved_tests=1,
    )

    executable, failures = RuntimeValidationService._from_runtime_plan(plan)

    assert executable == []
    assert failures[0]["expected_result"]["classification"] == "UNIT"
    assert failures[0]["expected_result"]["issues"] == [{
        "code": "non_http_test",
        "message": message,
    }]
    assert failures[0]["assertion_failure"] == message


def _obsolete_completed_openapi_target_ignores_stale_global_preparation_issue() -> None:
    stale = RuntimePreparationIssue(
        test_case_id="TC-RUN",
        code="request_payload_unresolved",
        message="Old preparation issue",
    )
    plan = RuntimeExecutionPlan(
        targets=[RuntimeExecutionTarget(
            test_case_id="TC-RUN",
            classification="HTTP",
            route="/users",
            http_method="POST",
            expected_http_status=201,
            request_payload={"email": "user@example.com"},
            executable=True,
        )],
        issues=[stale],
        total_tests=1,
        prepared_tests=0,
        unresolved_tests=1,
    )

    executable, failures = RuntimeValidationService._from_runtime_plan(plan)

    assert [target.test_case_id for target in executable] == ["TC-RUN"]
    assert failures == []


def _obsolete_runtime_selection_includes_resource_creation_prerequisite() -> None:
    targets = [
        RuntimeExecutionTarget(
            test_case_id="TC-CREATE",
            route="/users",
            http_method="POST",
            expected_http_status=201,
            executable=True,
        ),
        RuntimeExecutionTarget(
            test_case_id="TC-DEPENDENT",
            route="/users/{user_id}",
            http_method="GET",
            expected_http_status=200,
            path_parameters={"user_id": 1},
            executable=True,
        ),
        RuntimeExecutionTarget(
            test_case_id="TC-UNRELATED",
            route="/health",
            http_method="GET",
            expected_http_status=200,
            executable=True,
        ),
    ]

    selected = RuntimeValidationService._include_runtime_prerequisites(
        targets, {"TC-DEPENDENT"}
    )

    assert selected == {"TC-CREATE", "TC-DEPENDENT"}


def test_report_generator_counts_all_runtime_outcomes() -> None:
    summary = ReportGenerator.summary([
        {"runtime_status": "Passed"},
        {"runtime_status": "Failed"},
        {"runtime_status": "Skipped"},
        {"runtime_status": "NotExecutable"},
    ])
    assert summary == {
        "passed": 1, "failed": 1, "skipped": 1, "not_executable": 1,
        "total": 4, "executed": 2, "pass_rate": 50.0,
    }


def test_runtime_inputs_fall_back_to_completed_stage_four_generation() -> None:
    generated = _case().model_dump(mode="json")

    tests, failures, available_ids = RuntimeValidationService._runtime_inputs({
        "test_generation": {"generated_test_cases": [generated]},
    })

    assert [item.id for item in tests] == [generated["id"]]
    assert failures == []
    assert available_ids == {generated["id"]}


def test_runtime_inputs_use_generation_when_optimization_suite_is_empty() -> None:
    generated = _case().model_dump(mode="json")

    tests, _, _ = RuntimeValidationService._runtime_inputs({
        "quality_optimization": {"optimized_test_suite": []},
        "test_generation": {"generated_test_cases": [generated]},
    })

    assert [item.id for item in tests] == [generated["id"]]


def _obsolete_runtime_validation_retry_reuses_previous_execution_inputs() -> None:
    source = Mock(
        id=uuid.uuid4(), project_id=uuid.uuid4(), status="failed",
        failed_stage="runtime_validation", result={"runtime_execution_plan": {}},
    )
    previous = Mock(status="failed", base_url="http://127.0.0.1:8000")
    code_runs = Mock()
    code_runs.get_by_id.return_value = source
    runtime_runs = Mock()
    runtime_runs.get_latest_by_source_run_id.return_value = previous
    service = RuntimeValidationService(
        Mock(), code_runs, runtime_runs, Mock(), Mock()
    )
    retried = Mock()
    service.run = Mock(return_value=retried)

    assert service.retry_pipeline(source.id, timeout_seconds=45) is retried
    code_runs.prepare_retry.assert_called_once_with(source)
    service.run.assert_called_once_with(
        project_id=source.project_id,
        code_understanding_run_id=source.id,
        base_url="http://127.0.0.1:8001",
        test_case_ids=None,
        timeout_seconds=45,
    )
    code_runs.complete.assert_called_once_with(source, source.result)


def _obsolete_runtime_validation_rejects_accelerator_backend_target() -> None:
    service = RuntimeValidationService(
        Mock(), Mock(), Mock(), Mock(), Mock(), Mock()
    )

    with pytest.raises(
        RuntimeArtifactNotReadyError,
        match="fixed at http://127.0.0.1:8001",
    ):
        service.run(
            project_id=uuid.uuid4(),
            code_understanding_run_id=None,
            base_url="http://127.0.0.1:8000",
            test_case_ids=None,
            timeout_seconds=30,
        )


def _obsolete_runtime_validation_reports_automatic_startup_failure(tmp_path) -> None:
    project_id, source_run_id = uuid.uuid4(), uuid.uuid4()
    projects, code_runs, runtime_runs, sut = (
        Mock(), Mock(), Mock(), Mock()
    )
    projects.get_by_id.return_value = Mock(
        id=project_id, storage_path="unused"
    )
    code_runs.get_by_id.return_value = Mock(
        id=source_run_id,
        project_id=project_id,
        status="completed",
        result={},
    )
    storage = Mock()
    storage.resolve_project_directory.return_value = tmp_path
    message = (
        "Uploaded backend startup failed.\n"
        "Detected entry point: main:app\n"
        "Startup command: python -m uvicorn main:app\n"
        "Reason: uvicorn exited with code 1\n"
        "stdout/stderr:\nImportError"
    )
    sut.ensure_running.side_effect = SUTBackendStartupError(message)
    service = RuntimeValidationService(
        projects, code_runs, runtime_runs, storage, Mock(), Mock(), sut
    )

    with pytest.raises(
        RuntimeArtifactNotReadyError,
        match="Uploaded backend startup failed",
    ) as captured:
        service.run(
            project_id=project_id,
            code_understanding_run_id=source_run_id,
            base_url=SUT_BASE_URL,
            test_case_ids=None,
            timeout_seconds=30,
        )

    assert str(captured.value) == message
    runtime_runs.create_run.assert_not_called()
