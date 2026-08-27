import json
import zipfile
from pathlib import Path

import pytest

from app.services.export import ExportArtifactError, ExportValidationError
from app.services.export.pytest_export_service import PytestExportService


def _case(
    *,
    test_id: str = "UT-1",
    path: str = "tests/services/test_auth.py",
    code: str | None = None,
) -> dict:
    return {
        "id": test_id,
        "title": "authenticates a user",
        "description": "Verifies the authentication service result.",
        "category": "positive",
        "traceability": {"suggested_test_path": path},
        "unit_test": {
            "generated_code": code
            or """from app.services.auth import authenticate

def test_authenticate_returns_user():
    result = authenticate("user@example.com")
    assert result.email == "user@example.com"
""",
        },
    }


def _state(cases: list[dict]) -> dict:
    return {
        "test_generation": {"generated_test_cases": cases},
        "test_verification": {
            "summary": {"verified": len(cases), "partial": 0, "failed": 0}
        },
        "quality_optimization": {"final_score": 96.5},
        "runtime_execution_plan": {"status": "ready"},
    }


def test_export_contains_executable_pytest_project() -> None:
    service = PytestExportService(generator_version="1.2.3")
    archive_path = service.create_archive(
        project_name="Accounts API",
        pipeline_state=_state([_case()]),
    )
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            assert "test-suite/README.md" in names
            assert "test-suite/pytest.ini" in names
            assert "test-suite/requirements-test.txt" in names
            assert "test-suite/manifest.json" in names
            assert "test-suite/conftest.py" in names
            assert "test-suite/tests/services/test_auth.py" in names
            assert "test-suite/tests/repositories/" in names
            assert "assert result.email == 'user@example.com'" in archive.read(
                "test-suite/tests/services/test_auth.py"
            ).decode()
            manifest = json.loads(archive.read("test-suite/manifest.json"))
            assert manifest["generator_version"] == "1.2.3"
            assert manifest["generated_tests"] == 1
            assert manifest["verification_status"] == "verified"
            assert manifest["runtime_validation_status"] == "ready"
            assert manifest["quality_score"] == 96.5
    finally:
        Path(archive_path).unlink(missing_ok=True)


def test_export_wraps_deterministic_body_with_runtime_support() -> None:
    case = _case(code="""import importlib
module = importlib.import_module('app.services.auth')
target = _resolve_unit_target(module, 'authenticate')
args, kwargs = _unit_arguments(target)
result = target(*args, **kwargs)
assert result is not None
""")
    case["unit_test"].update({
        "module": "app.services.auth",
        "file": "app/services/auth.py",
        "symbol": "authenticate",
    })
    service = PytestExportService(generator_version="1.0")
    archive_path = service.create_archive(
        project_name="Runtime export", pipeline_state=_state([case]),
    )
    try:
        with zipfile.ZipFile(archive_path) as archive:
            module = archive.read("test-suite/tests/services/test_auth.py").decode()
            assert "def _resolve_unit_target" in module
            assert "def test_ut_1(dependency_mock, monkeypatch):" in module
            assert "_import_unit_module('app.services.auth', 'app/services/auth.py')" in module
    finally:
        Path(archive_path).unlink(missing_ok=True)


def test_export_consolidates_shared_fixtures_and_testing_dependencies() -> None:
    code = """import pytest
from unittest.mock import MagicMock

@pytest.fixture
def repository():
    return MagicMock()

@pytest.mark.asyncio
async def test_service(repository, mocker):
    assert repository is not None
"""
    service = PytestExportService(generator_version="1.0")
    archive_path = service.create_archive(
        project_name="Async API",
        pipeline_state=_state(
            [
                _case(test_id="UT-1", code=code),
                _case(test_id="UT-2", code=code),
            ]
        ),
    )
    try:
        with zipfile.ZipFile(archive_path) as archive:
            conftest = archive.read("test-suite/conftest.py").decode()
            test_module = archive.read("test-suite/tests/services/test_auth.py").decode()
            requirements = archive.read("test-suite/requirements-test.txt").decode()
            assert conftest.count("def repository") == 1
            assert "from unittest.mock import MagicMock" in conftest
            assert "def repository" not in test_module
            assert "pytest-asyncio" in requirements
            assert "pytest-mock" in requirements
    finally:
        Path(archive_path).unlink(missing_ok=True)


@pytest.mark.parametrize(
    "unsafe_path",
    ["../test_escape.py", "/tests/test_escape.py", "tests/not-a-test.py"],
)
def test_export_rejects_unsafe_or_invalid_paths(unsafe_path: str) -> None:
    service = PytestExportService(generator_version="1.0")
    with pytest.raises(ExportArtifactError):
        service.create_archive(
            project_name="Unsafe",
            pipeline_state=_state([_case(path=unsafe_path)]),
        )


def test_export_requires_generated_tests() -> None:
    service = PytestExportService(generator_version="1.0")
    with pytest.raises(ExportValidationError, match="No generated tests"):
        service.create_archive(
            project_name="Empty",
            pipeline_state=_state([]),
        )


def test_export_rejects_corrupted_python() -> None:
    service = PytestExportService(generator_version="1.0")
    with pytest.raises(ExportArtifactError, match="invalid Python"):
        service.create_archive(
            project_name="Corrupted",
            pipeline_state=_state([_case(code="def test_broken(:\n    pass")]),
        )
