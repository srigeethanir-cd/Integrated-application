from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services.security_scan.security_scan_service import (
    SecurityScanError,
    SemgrepRunner,
)


def test_resolved_semgrep_is_used_for_version_and_scan(
    monkeypatch, tmp_path: Path
) -> None:
    executable = tmp_path / "semgrep"
    executable.write_text("binary", encoding="utf-8")
    responses = [
        Mock(stdout="1.150.0\n", stderr="", returncode=0),
        Mock(
            stdout='{"results": [], "errors": [], "paths": {"scanned": []}}',
            stderr="",
            returncode=0,
        ),
    ]
    run = Mock(side_effect=responses)
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.shutil.which",
        lambda _name: str(executable),
    )
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.subprocess.run", run
    )

    payload = SemgrepRunner(config="p/default").scan(tmp_path)

    assert payload["results"] == []
    assert run.call_args_list[0].args[0] == [str(executable.resolve()), "--version"]
    assert run.call_args_list[1].args[0][0] == str(executable.resolve())
    assert run.call_args_list[1].args[0][1] == "scan"
    assert run.call_args_list[1].kwargs["cwd"] == tmp_path.resolve()


def test_missing_semgrep_fails_before_process_execution(
    monkeypatch, tmp_path: Path
) -> None:
    run = Mock()
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
    monkeypatch.setattr(
        "app.services.security_scan.security_scan_service.subprocess.run", run
    )

    with pytest.raises(SecurityScanError, match="Semgrep executable not found"):
        SemgrepRunner(executable="missing-semgrep").scan(tmp_path)

    run.assert_not_called()
