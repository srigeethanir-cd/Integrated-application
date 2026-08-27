from subprocess import CompletedProcess
from unittest.mock import patch

from app.services.runtime.dependency_preparer import DependencyPreparer


def test_dependency_preparer_installs_requirements_into_isolated_target(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    requirements = source / "requirements.txt"
    requirements.write_text("email-validator==2.2.0\n", encoding="utf-8")

    with patch(
        "app.services.runtime.dependency_preparer.subprocess.run",
        return_value=CompletedProcess([], 0, "installed", ""),
    ) as run:
        result = DependencyPreparer().prepare(
            source, workspace=tmp_path, timeout_seconds=30
        )

    assert result.success is True
    assert result.dependency_path == tmp_path / "project-dependencies"
    command = run.call_args.args[0]
    assert "--target" in command
    assert "-r" in command
    assert str(requirements) in command


def test_dependency_preparer_reports_installation_failure(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text(
        "[project]\nname='broken'\nversion='1.0'\n", encoding="utf-8"
    )

    with patch(
        "app.services.runtime.dependency_preparer.subprocess.run",
        return_value=CompletedProcess([], 1, "", "package unavailable"),
    ):
        result = DependencyPreparer().prepare(
            source, workspace=tmp_path, timeout_seconds=30
        )

    assert result.success is False
    assert result.error is not None
    assert result.error.startswith("Dependency preparation failed:")


def test_dependency_preparer_infers_missing_import_without_manifest(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "users.py").write_text(
        "from email_validator import validate_email\n", encoding="utf-8"
    )

    with patch(
        "app.services.runtime.dependency_preparer.importlib.util.find_spec",
        return_value=None,
    ), patch(
        "app.services.runtime.dependency_preparer.subprocess.run",
        return_value=CompletedProcess([], 0, "installed", ""),
    ) as run:
        result = DependencyPreparer().prepare(
            source, workspace=tmp_path, timeout_seconds=30
        )

    assert result.success is True
    assert "email-validator" in run.call_args.args[0]
