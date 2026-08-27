import uuid
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.security_scan.security_scan_service import (
    SecurityScanError,
    SecurityScanService,
    SemgrepRunner,
)


def test_security_scan_persists_normalized_semgrep_json_findings() -> None:
    project_id = uuid.uuid4()
    project = Mock(id=project_id, storage_path="projects/example")
    run = Mock(status="running")
    repository = Mock()
    repository.get_latest_by_project_id.return_value = None
    repository.create.return_value = run
    storage = Mock()
    storage.resolve_project_directory.return_value = Path("/tmp/project")
    runner = Mock()
    runner.scan.return_value = {
        "results": [{
            "check_id": "python.lang.security.audit.eval-detected",
            "path": "/tmp/project/source/app.py",
            "start": {"line": 12},
            "extra": {
                "severity": "ERROR",
                "message": "Avoid eval",
                "metadata": {"cwe": ["CWE-95"], "owasp": ["A03:2021"]},
            },
        }],
        "paths": {"scanned": ["app.py"]},
        "errors": [],
    }
    service = SecurityScanService(
        Mock(get_by_id=Mock(return_value=project)), repository, storage, runner
    )

    assert service.run(project_id) is run
    runner.scan.assert_called_once_with(Path("/tmp/project/source").resolve())
    findings = repository.complete.call_args.args[1]
    summary = repository.complete.call_args.args[2]
    assert findings[0]["rule_id"] == "python.lang.security.audit.eval-detected"
    assert findings[0]["severity"] == "HIGH"
    assert findings[0]["cwe"] == ["CWE-95"]
    assert findings[0]["owasp"] == ["A03:2021"]
    assert findings[0]["file"] == "app.py"
    assert findings[0]["line"] == 12
    assert findings[0]["metadata"]["_testforge_end_line"] == 12
    assert summary["total_findings"] == 1
    assert summary["by_severity"] == {"HIGH": 1}
    assert summary["security_score"] == 85
    assert isinstance(summary["duration_ms"], int)
    assert summary["rules_executed"] is None


def test_security_summary_uses_explicit_semgrep_rule_timing_count() -> None:
    payload = {"results": [], "time": {"rules": [{"id": "one"}, {"id": "two"}]}}

    summary = SecurityScanService._summary(payload, [])

    assert summary["rules_executed"] == 2


def test_security_finding_preserves_native_semgrep_remediation(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("secret = 'value'", encoding="utf-8")
    payload = {"results": [{
        "check_id": "jwt-hardcoded-secret",
        "path": "app.py",
        "start": {"line": 1},
        "extra": {
            "severity": "ERROR",
            "message": "Hardcoded secret",
            "fix": "Read the JWT secret from an environment variable.",
            "metadata": {"technology": ["jwt"]},
        },
    }]}

    finding = SecurityScanService(Mock(), Mock(), Mock(), Mock())._findings(
        payload, source
    )[0]

    assert finding["metadata"]["_testforge_native_remediation"] == (
        "Read the JWT secret from an environment variable."
    )
    assert payload["results"][0]["extra"]["metadata"] == {"technology": ["jwt"]}


def test_security_findings_are_normalized_enriched_and_deduplicated(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "auth.py").write_text(
        "import os\nJWT_SECRET = 'unsafe'\nprint(JWT_SECRET)\n",
        encoding="utf-8",
    )
    result = {
        "check_id": "python.jwt.hardcoded-secret",
        "path": "auth.py",
        "start": {"line": 2},
        "end": {"line": 2},
        "extra": {
            "severity": "ERROR",
            "message": "Hardcoded JWT secret",
            "metadata": {
                "confidence": "HIGH",
                "category": "security",
                "cwe": "CWE-798",
                "owasp": "A07:2021",
                "references": ["https://example.test/rule"],
            },
        },
    }

    findings = SecurityScanService(Mock(), Mock(), Mock(), Mock())._findings(
        {"results": [result, dict(result)]}, source
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding["severity"] == "HIGH"
    assert finding["metadata"]["_testforge_confidence"] == "HIGH"
    assert finding["metadata"]["_testforge_category"] == "security"
    assert finding["metadata"]["_testforge_end_line"] == 2
    assert "2: JWT_SECRET = 'unsafe'" in finding["metadata"][
        "_testforge_code_snippet"
    ]
    assert finding["metadata"]["_testforge_recommendation"].startswith(
        "Move the JWT secret"
    )
    assert finding["metadata"]["_testforge_references"] == [
        "https://example.test/rule"
    ]
    assert finding["metadata"]["_testforge_duplicate_count"] == 2


def test_semgrep_runner_rejects_non_json_output(monkeypatch) -> None:
    source_directory = Path(".").resolve()
    run = Mock(return_value=Mock(stdout="plain text", stderr="", returncode=2))
    parse = Mock(side_effect=AssertionError("non-JSON output must not be parsed"))
    monkeypatch.setattr(
        "subprocess.run",
        run,
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.json.loads",
        parse,
    )
    with pytest.raises(SecurityScanError, match="before producing a JSON report"):
        SemgrepRunner(config="p/security-audit").scan(source_directory)

    command = run.call_args.args[0]
    assert "--no-git-ignore" in command
    assert command[-1] == str(source_directory)
    assert run.call_args.kwargs["encoding"] == "utf-8"
    assert run.call_args.kwargs["errors"] == "replace"
    parse.assert_not_called()


def test_semgrep_runner_resolves_configured_executable(tmp_path) -> None:
    executable = tmp_path / "custom-semgrep"
    executable.write_text("binary", encoding="utf-8")

    assert SemgrepRunner(executable=str(executable)).resolve_executable() == executable.resolve()


def test_semgrep_runner_resolves_executable_from_path(monkeypatch, tmp_path) -> None:
    executable = tmp_path / "semgrep"
    executable.write_text("binary", encoding="utf-8")
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.shutil.which",
        lambda name: str(executable) if name == "semgrep" else None,
    )

    assert SemgrepRunner().resolve_executable() == executable.resolve()


def test_semgrep_runner_resolves_windows_virtual_environment_executable(
    monkeypatch, tmp_path
) -> None:
    scripts = tmp_path / "Scripts"
    scripts.mkdir()
    python = scripts / "python.exe"
    python.write_text("binary", encoding="utf-8")
    executable = scripts / "semgrep.exe"
    executable.write_text("binary", encoding="utf-8")
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.platform.system",
        lambda: "Windows",
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.shutil.which",
        lambda _name: None,
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.executable",
        str(python),
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.prefix",
        str(tmp_path),
    )

    assert SemgrepRunner().resolve_executable() == executable.resolve()


@pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
def test_semgrep_runner_resolves_posix_virtual_environment_executable(
    monkeypatch, tmp_path, system_name
) -> None:
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    python = bin_directory / "python"
    python.write_text("binary", encoding="utf-8")
    executable = bin_directory / "semgrep"
    executable.write_text("binary", encoding="utf-8")
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.platform.system",
        lambda: system_name,
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.shutil.which",
        lambda _name: None,
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.executable",
        str(python),
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.prefix",
        str(tmp_path),
    )

    assert SemgrepRunner().resolve_executable() == executable.resolve()


def test_semgrep_runner_missing_executable_has_actionable_diagnostics(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("PATH", "example-path")
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.shutil.which",
        lambda _name: None,
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.executable",
        str(tmp_path / "python"),
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.sys.prefix",
        str(tmp_path),
    )

    with pytest.raises(SecurityScanError) as captured:
        SemgrepRunner(executable="missing-semgrep").resolve_executable()

    message = str(captured.value)
    assert "Semgrep executable not found" in message
    assert "Checked:" in message
    assert "PATH:\nexample-path" in message
    assert "Configured executable:\nmissing-semgrep" in message


def test_auto_config_with_metrics_disabled_fails_before_subprocess(
    monkeypatch,
) -> None:
    run = Mock()
    monkeypatch.setattr("subprocess.run", run)

    with pytest.raises(
        SecurityScanError,
        match=r"SEMGREP_CONFIG=auto cannot be used while metrics are disabled",
    ):
        SemgrepRunner(config="auto", metrics_enabled=False).scan(Path("."))

    run.assert_not_called()


def test_auto_config_uses_explicit_fallback_when_metrics_are_disabled(
    monkeypatch,
) -> None:
    run = Mock(
        return_value=Mock(
            stdout='{"results": [], "errors": [], "paths": {"scanned": []}}',
            stderr="",
            returncode=0,
        )
    )
    monkeypatch.setattr("subprocess.run", run)

    SemgrepRunner(
        config="auto",
        explicit_config="p/security-audit",
        metrics_enabled=False,
    ).scan(Path("."))

    command = run.call_args.args[0]
    assert command[command.index("--config") + 1] == "p/security-audit"
    assert command[command.index("--metrics") + 1] == "off"


def test_semgrep_runner_default_uses_default_ruleset(monkeypatch) -> None:
    run = Mock(
        return_value=Mock(
            stdout='{"results": [], "errors": [], "paths": {"scanned": []}}',
            stderr="",
            returncode=0,
        )
    )
    monkeypatch.setattr("subprocess.run", run)

    SemgrepRunner().scan(Path("."))

    command = run.call_args.args[0]
    assert command[command.index("--config") + 1] == "p/default"


def test_auto_config_is_allowed_when_metrics_are_enabled(monkeypatch) -> None:
    run = Mock(
        return_value=Mock(
            stdout='{"results": [], "errors": [], "paths": {"scanned": []}}',
            stderr="",
            returncode=0,
        )
    )
    monkeypatch.setattr("subprocess.run", run)

    SemgrepRunner(config="auto", metrics_enabled=True).scan(Path("."))

    command = run.call_args.args[0]
    assert command[command.index("--config") + 1] == "auto"
    assert command[command.index("--metrics") + 1] == "on"


def test_missing_local_ruleset_fails_before_subprocess(monkeypatch) -> None:
    run = Mock()
    monkeypatch.setattr("subprocess.run", run)

    with pytest.raises(SecurityScanError, match="local ruleset does not exist"):
        SemgrepRunner(config="./missing-semgrep-rules").scan(Path("."))

    run.assert_not_called()


def test_semgrep_runner_captures_unicode_stderr_safely(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "subprocess.run",
        Mock(
            return_value=Mock(
                stdout='{"results": [], "errors": [], "paths": {"scanned": []}}',
                stderr="scanner warning: café \ufffd",
                returncode=2,
            )
        ),
    )

    with pytest.raises(SecurityScanError, match="café"):
        SemgrepRunner(config="p/security-audit").scan(Path("."))


def test_summary_deduplicates_scanned_paths_and_counts_severities() -> None:
    payload = {
        "paths": {"scanned": ["src/app.py", "src/app.py", "src/utils.py"]},
        "results": [],
        "errors": [{"message": "one parse warning"}],
    }
    findings = [
        {"severity": "ERROR"},
        {"severity": "ERROR"},
        {"severity": "WARNING"},
    ]

    summary = SecurityScanService._summary(payload, findings)

    assert summary["files_scanned"] == 2
    assert summary["total_findings"] == 3
    assert summary["by_severity"] == {"ERROR": 2, "WARNING": 1}
    assert summary["errors"] == 1
    assert summary["warnings"] == 0
    assert summary["diagnostics"][0]["category"] == "scanner_failure"


def test_summary_uses_finding_paths_when_semgrep_omits_paths() -> None:
    payload = {
        "results": [
            {"path": "src/app.py"},
            {"path": "src/app.py"},
            {"path": "src/utils.py"},
        ],
        "errors": [],
    }

    summary = SecurityScanService._summary(payload, [])

    assert summary["files_scanned"] == 2


def test_summary_classifies_diagnostics_and_expected_exclusions() -> None:
    payload = {
        "version": "1.171.0",
        "results": [],
        "errors": [
            {
                "level": "warn",
                "type": "Parse error",
                "message": "Could not parse file",
                "path": "src/broken.py",
            },
            {
                "level": "info",
                "type": "Unknown language",
                "message": "No parser",
                "path": "src/example.xyz",
            },
            {
                "level": "error",
                "type": "Timeout",
                "message": "Rule timed out",
                "path": "src/large.py",
            },
        ],
        "paths": {
            "scanned": ["src/clean.py"],
            "skipped": [
                {"path": "node_modules", "reason": "cli_exclude_flags_match"},
                {"path": "src/no-access.py", "reason": "insufficient_permissions"},
                {"path": "src/example.xyz", "reason": "wrong_language"},
            ],
        },
    }

    summary = SecurityScanService._summary(payload, [])

    assert summary["errors"] == 2
    assert summary["warnings"] == 0
    assert summary["informational"] == 0
    assert summary["parser_errors"] == 1
    assert summary["unsupported_files"] == 2
    assert summary["skipped_files"] == 3
    assert summary["skipped_by_reason"] == {
        "cli_exclude_flags_match": 1,
        "insufficient_permissions": 1,
        "wrong_language": 1,
    }
    assert summary["engine_version"] == "1.171.0"
    diagnostic_categories = Counter(
        diagnostic["category"] for diagnostic in summary["diagnostics"]
    )
    assert diagnostic_categories == {
        "parser_error": 1,
        "unsupported": 1,
        "scanner_failure": 1,
    }
    assert (
        summary["errors"]
        - 1  # The insufficient-permissions skipped target is also a failure.
        + summary["warnings"]
        + summary["informational"]
        + summary["parser_errors"]
        + sum(
            diagnostic["category"] == "unsupported"
            for diagnostic in summary["diagnostics"]
        )
        == len(summary["diagnostics"])
    )


def test_partial_parsing_is_counted_only_as_a_parser_issue() -> None:
    payload = {
        "results": [],
        "errors": [
            {
                "level": "warn",
                "type": "PartialParsing",
                "message": "Part of the file could not be parsed",
                "path": "src/generated.py",
            }
        ],
        "paths": {"scanned": ["src/generated.py"]},
    }

    summary = SecurityScanService._summary(payload, [])

    assert summary["diagnostics"][0]["category"] == "parser_error"
    assert summary["errors"] == 0
    assert summary["warnings"] == 0
    assert summary["informational"] == 0
    assert summary["parser_errors"] == 1


def test_security_scan_failure_persists_duration_and_error_summary() -> None:
    project_id = uuid.uuid4()
    run = Mock(status="running")
    repository = Mock()
    repository.get_latest_by_project_id.return_value = None
    repository.create.return_value = run
    runner = Mock()
    runner.scan.side_effect = SecurityScanError("scanner unavailable")
    service = SecurityScanService(
        Mock(
            get_by_id=Mock(
                return_value=Mock(id=project_id, storage_path="projects/example")
            )
        ),
        repository,
        Mock(
            resolve_project_directory=Mock(return_value=Path("/tmp/project"))
        ),
        runner,
    )

    with pytest.raises(SecurityScanError, match="scanner unavailable"):
        service.run(project_id)

    failure_summary = repository.fail.call_args.kwargs["summary"]
    assert failure_summary["errors"] == 1
    assert isinstance(failure_summary["duration_ms"], int)


def test_retry_locks_and_reuses_failed_run() -> None:
    run_id = uuid.uuid4()
    project_id = uuid.uuid4()
    failed = Mock(id=run_id, project_id=project_id, status="failed")
    repository = Mock()
    repository.get_by_id_for_update.return_value = failed
    service = SecurityScanService(Mock(), repository, Mock(), Mock())
    retried = Mock()
    service.run = Mock(return_value=retried)

    assert service.retry(run_id) is retried
    repository.get_by_id_for_update.assert_called_once_with(run_id)
    service.run.assert_called_once_with(project_id, resume_failed=True)


def test_concurrent_scan_reuses_running_project_run() -> None:
    project_id = uuid.uuid4()
    running = Mock(status="running")
    repository = Mock()
    repository.get_latest_by_project_id.side_effect = [None, running]
    repository.create.side_effect = IntegrityError(
        "insert", {}, Exception("duplicate running scan")
    )
    service = SecurityScanService(
        Mock(
            get_by_id=Mock(
                return_value=Mock(id=project_id, storage_path="project")
            )
        ),
        repository,
        Mock(),
        Mock(),
    )

    assert service.run(project_id) is running


def test_finding_outside_project_source_fails_validation() -> None:
    service = SecurityScanService(Mock(), Mock(), Mock(), Mock())
    payload = {
        "results": [
            {
                "check_id": "rule.id",
                "path": str(Path("outside.py").resolve()),
                "start": {"line": 1},
                "extra": {"severity": "ERROR", "metadata": {}},
            }
        ]
    }

    with pytest.raises(SecurityScanError, match="outside the project source"):
        service._findings(payload, Path("project/source").resolve())


def test_completed_security_scan_is_reused_on_resume() -> None:
    completed = Mock(status="completed")
    repository = Mock()
    repository.get_latest_by_project_id.return_value = completed
    service = SecurityScanService(Mock(), repository, Mock(), Mock())

    assert service.run(uuid.uuid4(), resume_failed=True) is completed
    repository.create.assert_not_called()


def _semgrep_executable() -> Path:
    executable = Path(sys.executable).with_name(
        "semgrep.exe" if sys.platform == "win32" else "semgrep"
    )
    if not executable.is_file():
        pytest.skip("Semgrep executable is not installed")
    return executable


def _scan_or_skip_restricted_windows_store(
    runner: SemgrepRunner, source_directory: Path
) -> dict:
    try:
        return runner.scan(source_directory)
    except SecurityScanError as error:
        if "CertOpenSystemStore returned NULL" in str(error):
            pytest.skip("Test sandbox cannot access the Windows certificate store")
        raise


def test_real_semgrep_json_matches_findings_counts_and_exclusions() -> None:
    fixture_root = Path(__file__).parents[1] / "fixtures" / "security_scan"
    source_directory = (fixture_root / "source").resolve()
    runner = SemgrepRunner(
        executable=str(_semgrep_executable()),
        config=str((fixture_root / "rules.yml").resolve()),
        timeout_seconds=60,
    )
    payload = _scan_or_skip_restricted_windows_store(runner, source_directory)
    service = SecurityScanService(Mock(), Mock(), Mock(), Mock())
    findings = service._findings(payload, source_directory)
    summary = service._summary(payload, findings)

    assert len(payload["paths"]["scanned"]) == 3
    assert summary["files_scanned"] == 3
    assert summary["total_findings"] == 1
    assert summary["by_severity"] == {"HIGH": 1}
    assert summary["errors"] == 0
    assert summary["skipped_by_reason"]["cli_exclude_flags_match"] == 4
    assert findings[0]["rule_id"].endswith("audit.python.eval")
    assert findings[0]["file"] == "nested/vulnerable.py"
    assert findings[0]["line"] == 2
    assert findings[0]["severity"] == "HIGH"
    assert findings[0]["metadata"]["_testforge_code_snippet"]
    assert findings[0]["cwe"] == ["CWE-95"]
    assert findings[0]["owasp"] == ["A03:2021"]


def test_real_semgrep_clean_and_unsupported_only_projects() -> None:
    fixture_root = Path(__file__).parents[1] / "fixtures" / "security_scan"
    runner = SemgrepRunner(
        executable=str(_semgrep_executable()),
        config=str((fixture_root / "rules.yml").resolve()),
        timeout_seconds=60,
    )

    clean_payload = _scan_or_skip_restricted_windows_store(
        runner, (fixture_root / "clean_source").resolve()
    )
    empty_payload = _scan_or_skip_restricted_windows_store(
        runner, (fixture_root / "empty_source").resolve()
    )

    assert len(clean_payload["paths"]["scanned"]) == 1
    assert clean_payload["results"] == []
    assert empty_payload["paths"]["scanned"] == []
    empty_summary = SecurityScanService._summary(
        empty_payload,
        [],
        source_directory=(fixture_root / "empty_source").resolve(),
    )
    assert empty_summary["unsupported_files"] == 1


def test_summary_handles_large_target_lists_without_overcounting() -> None:
    paths = [f"src/module_{index}.py" for index in range(10_000)]
    summary = SecurityScanService._summary(
        {"paths": {"scanned": paths}, "results": [], "errors": []},
        [],
    )

    assert summary["files_scanned"] == 10_000
