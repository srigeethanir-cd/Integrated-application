from __future__ import annotations

import os
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PytestRunResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    junit_path: Path
    timed_out: bool = False
    coverage_percent: float | None = None


class PytestRunner:
    def run(
        self, test_file: Path, *, timeout_seconds: int,
        python_path: Path | None = None,
        dependency_path: Path | None = None,
    ) -> PytestRunResult:
        junit_path = test_file.parent / "runtime-results.xml"
        command = [
            sys.executable, "-m", "pytest", str(test_file.name), "-q", "-s",
            f"--junitxml={junit_path}",
        ]
        environment = {
            key: value for key, value in os.environ.items()
            if key.upper() in {
                "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
                "GROQ_API_KEY", "GROQ_MODEL", "PRIMARY_LLM_PROVIDER",
                "CEREBRAS_API_KEY", "CEREBRAS_MODEL"
            } or key.startswith("TESTFORGE_") or key.startswith("APP_")
        }
        if python_path is not None:
            runtime_root = str(python_path.resolve())
            paths = [runtime_root]
            if dependency_path is not None:
                paths.append(str(dependency_path.resolve()))
            environment["PYTHONPATH"] = os.pathsep.join(paths)
            environment["TESTFORGE_RUNTIME_SOURCE_ROOT"] = runtime_root
            environment["PYTHONNOUSERSITE"] = "1"
        if self._has_pytest_cov(environment):
            command.extend(["--cov", "--cov-report=json:coverage.json"])
        logger.info(
            "Runtime pytest launch cwd=%s pythonpath=%s command=%s",
            test_file.parent.resolve(),
            environment.get("PYTHONPATH", ""),
            subprocess.list2cmdline(command),
        )
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=test_file.parent,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            for line in (completed.stdout or "").splitlines():
                if line.startswith("TESTFORGE_IMPORT_DIAGNOSTIC"):
                    logger.info("%s", line)
            return PytestRunResult(
                completed.returncode,
                completed.stdout[-100_000:],
                completed.stderr[-100_000:],
                (time.perf_counter() - started) * 1000,
                junit_path,
                coverage_percent=self._coverage(test_file.parent / "coverage.json"),
            )
        except subprocess.TimeoutExpired as error:
            return PytestRunResult(
                124,
                (error.stdout or "")[-100_000:] if isinstance(error.stdout, str) else "",
                (error.stderr or "")[-100_000:] if isinstance(error.stderr, str) else "",
                (time.perf_counter() - started) * 1000,
                junit_path,
                timed_out=True,
            )

    @staticmethod
    def _coverage(path: Path) -> float | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return float(payload["totals"]["percent_covered"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _has_pytest_cov(environment: dict[str, str]) -> bool:
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "--help"],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            return "--cov" in (res.stdout or "")
        except Exception:
            return False
