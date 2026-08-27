from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from app.database.models.security_scan import SecurityScanRun
from app.database.repositories.project_repository import ProjectRepository
from app.database.repositories.security_scan_repository import SecurityScanRepository
from app.services.ingestion.storage_service import StorageService

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDES = (
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
)
PARSER_ERROR_TYPES = {
    "astbuildererror",
    "lexicalerror",
    "otherparseerror",
    "parseerror",
    "partialparsing",
    "syntaxerror",
}
UNSUPPORTED_ERROR_TYPES = {
    "incompatiblerule",
    "missingplugin",
    "unknownlanguage",
}
SCANNER_FAILURE_SKIP_REASONS = {
    "analysis_failed_parser_or_internal_error",
    "insufficient_permissions",
    "nonexistent_file",
}
UNSUPPORTED_SKIP_REASONS = {"wrong_language"}


class SecurityScanError(RuntimeError):
    """Raised when Semgrep cannot produce a valid scan result."""

    def __init__(self, message: str, *, payload: dict | None = None) -> None:
        super().__init__(message)
        self.payload = payload


class SecurityScanRunNotFoundError(SecurityScanError):
    """Raised when a security scan run does not exist."""


class SecurityScanRetryError(SecurityScanError):
    """Raised when a security scan run cannot be retried."""


class SemgrepRunner:
    def __init__(
        self,
        executable: str = "semgrep",
        config: str = "p/default",
        explicit_config: str | None = None,
        metrics_enabled: bool = False,
        timeout_seconds: int = 300,
    ) -> None:
        self.executable = executable
        self.config = config
        self.explicit_config = explicit_config
        self.metrics_enabled = metrics_enabled
        self.timeout_seconds = timeout_seconds

    def resolve_executable(self) -> Path:
        configured = os.path.expandvars(self.executable.strip())
        path_value = os.environ.get("PATH", "")
        checked: list[str] = []
        if not configured:
            raise self._missing_executable_error(checked, path_value)

        configured_path = Path(configured).expanduser()
        is_path = (
            configured_path.is_absolute()
            or configured_path.parent != Path(".")
            or any(separator in configured for separator in ("/", "\\"))
        )
        if is_path:
            checked.append(str(configured_path))
            if configured_path.is_file():
                return configured_path.resolve()
            raise self._missing_executable_error(checked, path_value)

        executable_names = list(
            dict.fromkeys(
                [configured, "semgrep.exe", "semgrep"]
                if platform.system() == "Windows"
                else [configured, "semgrep"]
            )
        )
        for name in executable_names:
            checked.append(f"PATH lookup: {name}")
            resolved = shutil.which(name)
            if resolved:
                return Path(resolved).resolve()

        environment_directories = list(
            dict.fromkeys(
                [
                    Path(sys.executable).resolve().parent,
                    Path(sys.prefix).resolve() / ("Scripts" if platform.system() == "Windows" else "bin"),
                ]
            )
        )
        for directory in environment_directories:
            for name in executable_names:
                candidate = directory / name
                checked.append(str(candidate))
                if candidate.is_file():
                    return candidate.resolve()

        raise self._missing_executable_error(checked, path_value)

    def _missing_executable_error(
        self, checked: list[str], path_value: str
    ) -> SecurityScanError:
        checked_text = "\n".join(f"- {candidate}" for candidate in checked) or "- none"
        return SecurityScanError(
            "Semgrep executable not found.\n\n"
            f"Checked:\n{checked_text}\n\n"
            f"PATH:\n{path_value or '<empty>'}\n\n"
            f"Configured executable:\n{self.executable or '<empty>'}\n\n"
            "Install Semgrep in the backend virtual environment or set "
            "SEMGREP_EXECUTABLE to the absolute executable path."
        )

    def _version(self, executable: Path, working_directory: Path) -> str:
        try:
            completed = subprocess.run(
                [str(executable), "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=min(self.timeout_seconds, 30),
                check=False,
                cwd=working_directory,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            logger.warning(
                "Semgrep version check failed executable=%s error=%s",
                executable,
                error,
            )
            return f"unavailable ({error})"
        output = (completed.stdout or completed.stderr or "").strip()
        if completed.returncode != 0:
            logger.warning(
                "Semgrep version check failed executable=%s exit_code=%s output=%s",
                executable,
                completed.returncode,
                output or "no output",
            )
            return f"unavailable (exit code {completed.returncode})"
        return output.splitlines()[0] if output else "unknown"

    def scan(self, source_directory: Path) -> dict:
        ruleset = self._resolve_ruleset()
        source_directory = source_directory.resolve()
        if not source_directory.is_dir():
            raise SecurityScanError(
                f"Project source directory does not exist: {source_directory}"
            )
        executable = self.resolve_executable()
        version = self._version(executable, source_directory)
        command = [
            str(executable),
            "scan",
            "--json",
            "--verbose",
            "--metrics",
            "on" if self.metrics_enabled else "off",
            "--no-git-ignore",
            "--semgrepignore-v2",
            "--project-root",
            str(source_directory),
            *(
                argument
                for pattern in DEFAULT_EXCLUDES
                for argument in ("--exclude", pattern)
            ),
            "--config",
            ruleset,
            str(source_directory),
        ]
        logger.info(
            "Semgrep diagnostics resolved_executable=%s path=%s working_directory=%s "
            "version=%s command=%s",
            executable,
            os.environ.get("PATH", ""),
            source_directory,
            version,
            subprocess.list2cmdline(command),
        )
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
                cwd=source_directory,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SecurityScanError(f"Semgrep execution failed: {error}") from error

        stdout = (completed.stdout or "").lstrip("\ufeff").strip()
        stderr = (completed.stderr or "").strip()[:2_000]
        if not stdout.startswith("{"):
            detail = stderr or stdout[:2_000]
            if completed.returncode != 0:
                suffix = f": {detail}" if detail else ""
                raise SecurityScanError(
                    f"Semgrep failed before producing a JSON report{suffix}"
                )
            suffix = f": {detail}" if detail else ""
            raise SecurityScanError(
                f"Semgrep did not return a JSON report{suffix}"
            )
        try:
            payload = json.loads(stdout)
        except (json.JSONDecodeError, TypeError) as error:
            detail = f": {stderr}" if stderr else ""
            raise SecurityScanError(
                f"Semgrep returned a malformed JSON report{detail}"
            ) from error
        if not isinstance(payload, dict):
            raise SecurityScanError("Semgrep JSON output must be an object")
        if not isinstance(payload.get("results", []), list):
            raise SecurityScanError("Semgrep JSON results must be a list")
        if not isinstance(payload.get("errors", []), list):
            raise SecurityScanError("Semgrep JSON errors must be a list")
        if completed.returncode != 0:
            errors = payload.get("errors") or []
            first_error = errors[0] if errors else None
            detail = (
                first_error.get("message")
                if isinstance(first_error, dict)
                else str(first_error or "")
            )
            if not detail:
                detail = stderr
            if not detail:
                detail = "unknown Semgrep error"
            raise SecurityScanError(
                f"Semgrep scan failed: {detail}", payload=payload
            )
        return payload

    def _resolve_ruleset(self) -> str:
        configured = self.config.strip()
        fallback = (self.explicit_config or "").strip()
        if configured.lower() == "auto" and not self.metrics_enabled:
            if fallback and fallback.lower() != "auto":
                return self._validate_explicit_ruleset(fallback)
            raise SecurityScanError(
                "Semgrep configuration error: SEMGREP_CONFIG=auto cannot be used "
                "while metrics are disabled. The auto ruleset requires Semgrep "
                "registry access and metrics. Set SEMGREP_CONFIG to an explicit "
                "ruleset such as p/default or a local rules file/directory, "
                "or set SEMGREP_EXPLICIT_CONFIG as the fallback."
            )
        if not configured:
            raise SecurityScanError(
                "Semgrep configuration error: configure an explicit ruleset such "
                "as p/default or a local rules file/directory."
            )
        return configured if configured.lower() == "auto" else self._validate_explicit_ruleset(configured)

    @staticmethod
    def _validate_explicit_ruleset(ruleset: str) -> str:
        candidate = Path(ruleset).expanduser()
        if candidate.exists():
            return str(candidate.resolve())
        is_path_like = (
            candidate.is_absolute()
            or ruleset.startswith((".", "/", "\\"))
            or "\\" in ruleset
            or candidate.suffix.lower() in {".yml", ".yaml", ".json"}
        )
        if is_path_like:
            raise SecurityScanError(
                f"Semgrep configuration error: local ruleset does not exist: {ruleset}"
            )
        return ruleset


class SecurityScanService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        repository: SecurityScanRepository,
        storage_service: StorageService,
        runner: SemgrepRunner,
    ) -> None:
        self._project_repository = project_repository
        self._repository = repository
        self._storage_service = storage_service
        self._runner = runner

    def run(
        self, project_id: uuid.UUID, *, resume_failed: bool = False
    ) -> SecurityScanRun | None:
        project = self._project_repository.get_by_id(project_id)
        if project is None:
            return None
        previous = self._repository.get_latest_by_project_id(project_id)
        if previous is not None and previous.status == "completed":
            return previous
        if resume_failed and previous is not None and previous.status == "failed":
            run = previous
            self._repository.prepare_retry(run)
        else:
            try:
                run = self._repository.create(project_id)
            except IntegrityError:
                concurrent = self._repository.get_latest_by_project_id(project_id)
                if concurrent is not None and concurrent.status == "running":
                    logger.info(
                        "Reusing concurrent security scan project_id=%s run_id=%s",
                        project_id,
                        concurrent.id,
                    )
                    return concurrent
                raise
        started = time.monotonic()
        logger.info(
            "Security scan started project_id=%s run_id=%s retry_count=%s",
            project_id,
            run.id,
            run.retry_count,
        )
        try:
            project_directory = self._storage_service.resolve_project_directory(
                project.id, project.storage_path
            )
            source_directory = (project_directory / "source").resolve()
            payload = self._runner.scan(source_directory)
            findings = self._findings(payload, source_directory)
            duration_ms = round((time.monotonic() - started) * 1000)
            self._repository.complete(
                run,
                findings,
                self._summary(
                    payload,
                    findings,
                    duration_ms=duration_ms,
                    source_directory=source_directory,
                ),
            )
            logger.info(
                "Security scan completed project_id=%s run_id=%s findings=%s duration_ms=%s",
                project_id,
                run.id,
                len(findings),
                duration_ms,
            )
        except Exception as error:
            duration_ms = round((time.monotonic() - started) * 1000)
            failure_payload = (
                error.payload
                if isinstance(error, SecurityScanError)
                and error.payload is not None
                else {}
            )
            failure_summary = self._summary(
                failure_payload,
                [],
                duration_ms=duration_ms,
                source_directory=locals().get("source_directory"),
            )
            failure_summary["errors"] = max(1, failure_summary["errors"])
            self._repository.fail(run, str(error), summary=failure_summary)
            logger.exception(
                "Security scan failed project_id=%s run_id=%s duration_ms=%s",
                project_id,
                run.id,
                duration_ms,
            )
            raise
        return run

    def retry(self, run_id: uuid.UUID) -> SecurityScanRun:
        run = self._repository.get_by_id_for_update(run_id)
        if run is None:
            raise SecurityScanRunNotFoundError("Security scan run not found")
        if run.status != "failed":
            raise SecurityScanRetryError(
                "Only failed security scans can be retried"
            )
        result = self.run(run.project_id, resume_failed=True)
        assert result is not None
        return result

    def get_run(self, run_id: uuid.UUID) -> SecurityScanRun | None:
        return self._repository.get_by_id(run_id)

    def get_latest_run(self, project_id: uuid.UUID) -> SecurityScanRun | None:
        return self._repository.get_latest_by_project_id(project_id)

    @staticmethod
    def _values(value: object) -> list[str]:
        if value is None:
            return []
        return [str(item) for item in value] if isinstance(value, list) else [str(value)]

    @staticmethod
    def _diagnostics(payload: dict) -> list[dict]:
        diagnostics = []
        for raw in payload.get("errors", []):
            if not isinstance(raw, dict):
                diagnostics.append(
                    {
                        "level": "error",
                        "category": "scanner_failure",
                        "type": "Unknown error",
                        "message": str(raw),
                        "path": None,
                    }
                )
                continue
            level = str(raw.get("level") or "error").lower()
            error_type = str(raw.get("type") or "Unknown error")
            normalized_type = "".join(
                character
                for character in error_type.lower()
                if character.isalnum()
            )
            if normalized_type in PARSER_ERROR_TYPES:
                category = "parser_error"
            elif normalized_type in UNSUPPORTED_ERROR_TYPES:
                category = "unsupported"
            elif level == "error":
                category = "scanner_failure"
            elif level in {"warn", "warning"}:
                category = "warning"
            else:
                category = "information"
            diagnostics.append(
                {
                    "level": "warning" if level == "warn" else level,
                    "category": category,
                    "type": error_type,
                    "message": str(
                        raw.get("message")
                        or raw.get("long_msg")
                        or raw.get("short_msg")
                        or error_type
                    ),
                    "path": (
                        str(raw["path"]).replace("\\", "/")
                        if raw.get("path")
                        else None
                    ),
                }
            )
        return diagnostics

    def _findings(self, payload: dict, source_directory: Path) -> list[dict]:
        findings = []
        for result in payload.get("results", []):
            if not isinstance(result, dict):
                raise SecurityScanError("Semgrep returned an invalid finding")
            rule_id = result.get("check_id")
            result_path = result.get("path")
            start = result.get("start")
            if (
                not isinstance(rule_id, str)
                or not rule_id
                or not isinstance(result_path, str)
                or not result_path
                or not isinstance(start, dict)
                or not isinstance(start.get("line"), int)
                or start["line"] < 1
            ):
                raise SecurityScanError(
                    "Semgrep returned an incomplete finding"
                )
            extra = result.get("extra") or {}
            if not isinstance(extra, dict):
                raise SecurityScanError("Semgrep returned invalid finding metadata")
            metadata = extra.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            else:
                metadata = dict(metadata)
            native_remediation = extra.get("fix") or extra.get("remediation")
            if native_remediation:
                metadata["_testforge_native_remediation"] = str(
                    native_remediation
                )
            end = result.get("end") if isinstance(result.get("end"), dict) else {}
            raw_path = Path(result_path)
            resolved_path = (
                raw_path.resolve()
                if raw_path.is_absolute()
                else (source_directory / raw_path).resolve()
            )
            try:
                file = str(resolved_path.relative_to(source_directory.resolve()))
            except ValueError as error:
                raise SecurityScanError(
                    "Semgrep finding path is outside the project source"
                ) from error
            start_line = start["line"]
            end_line = end.get("line") if isinstance(end.get("line"), int) else start_line
            try:
                source_lines = resolved_path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
                snippet_start = max(1, start_line - 2)
                snippet_end = min(len(source_lines), end_line + 2)
                code_snippet = "\n".join(
                    f"{line_number}: {source_lines[line_number - 1]}"
                    for line_number in range(snippet_start, snippet_end + 1)
                ) or None
            except OSError:
                code_snippet = None
            message = str(extra.get("message", ""))
            recommendation = self._recommendation(
                rule_id, message, metadata, native_remediation
            )
            metadata.update(
                {
                    "_testforge_confidence": self._optional_text(
                        metadata.get("confidence")
                    ),
                    "_testforge_category": self._optional_text(
                        metadata.get("category")
                    ),
                    "_testforge_end_line": end_line,
                    "_testforge_code_snippet": code_snippet,
                    "_testforge_recommendation": recommendation,
                    "_testforge_references": self._values(
                        metadata.get("references") or metadata.get("reference")
                    ),
                    "_testforge_duplicate_count": 1,
                }
            )
            raw_severity = str(extra.get("severity", "UNKNOWN")).upper()
            findings.append(
                {
                    "rule_id": rule_id,
                    "severity": {
                        "ERROR": "HIGH",
                        "WARNING": "MEDIUM",
                        "INFO": "LOW",
                    }.get(raw_severity, raw_severity),
                    "cwe": self._values(metadata.get("cwe")),
                    "owasp": self._values(metadata.get("owasp")),
                    "file": file.replace("\\", "/"),
                    "line": start_line,
                    "message": message,
                    "metadata": metadata,
                }
            )
        unique: dict[tuple[object, ...], dict] = {}
        for finding in findings:
            key = (
                finding["rule_id"], finding["file"], finding["line"],
                finding["metadata"].get("_testforge_end_line"),
                finding["message"],
            )
            if key in unique:
                unique[key]["metadata"]["_testforge_duplicate_count"] += 1
            else:
                unique[key] = finding
        return sorted(
            unique.values(),
            key=lambda item: (item["file"], item["line"], item["rule_id"]),
        )

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if isinstance(value, list):
            value = value[0] if value else None
        return str(value).strip() if value is not None and str(value).strip() else None

    @classmethod
    def _recommendation(
        cls, rule_id: str, message: str, metadata: dict, native: object
    ) -> str | None:
        for value in (
            native,
            metadata.get("recommendation"),
            metadata.get("remediation"),
            metadata.get("fix"),
        ):
            text = cls._optional_text(value)
            if text:
                return text
        consider = message.lower().find("consider ")
        if consider >= 0:
            return message[consider:].strip()
        combined = f"{rule_id} {message}".lower()
        if "jwt" in combined and ("hardcod" in combined or "secret" in combined):
            return (
                "Move the JWT secret into environment variables or another secure "
                "secret-management mechanism instead of hardcoding credentials."
            )
        return None

    @staticmethod
    def _summary(
        payload: dict,
        findings: list[dict],
        *,
        duration_ms: int | None = None,
        source_directory: Path | None = None,
    ) -> dict:
        scanned = (payload.get("paths") or {}).get("scanned") or []
        scanned_files = {
            str(path).replace("\\", "/")
            for path in scanned
            if isinstance(path, (str, Path)) and str(path)
        }
        if not scanned_files:
            scanned_files = {
                str(result.get("path")).replace("\\", "/")
                for result in payload.get("results", [])
                if isinstance(result, dict) and result.get("path")
            }
        diagnostics = SecurityScanService._diagnostics(payload)
        skipped = (payload.get("paths") or {}).get("skipped") or []
        skipped_by_reason = Counter(
            str(item.get("reason") or "unknown")
            for item in skipped
            if isinstance(item, dict)
        )
        skipped_failures = sum(
            count
            for reason, count in skipped_by_reason.items()
            if reason in SCANNER_FAILURE_SKIP_REASONS
        )
        unsupported_files = sum(
            count
            for reason, count in skipped_by_reason.items()
            if reason in UNSUPPORTED_SKIP_REASONS
        )
        unsupported_files += sum(
            item["category"] == "unsupported" for item in diagnostics
        )
        if source_directory is not None:
            source_directory = source_directory.resolve()

            def resolve_reported_path(value: object) -> Path:
                path = Path(str(value))
                return (
                    path.resolve()
                    if path.is_absolute()
                    else (source_directory / path).resolve()
                )

            try:
                source_files = {
                    path.resolve()
                    for path in source_directory.rglob("*")
                    if path.is_file()
                    and not any(
                        part in DEFAULT_EXCLUDES
                        for part in path.relative_to(source_directory).parts[:-1]
                    )
                }
            except OSError:
                source_files = set()
            scanned_targets = {
                resolve_reported_path(path) for path in scanned_files
            }
            skipped_targets = {
                resolve_reported_path(item["path"])
                for item in skipped
                if isinstance(item, dict) and item.get("path")
            }
            unreported_files = {
                path
                for path in source_files
                if path not in scanned_targets
                and not any(
                    path == skipped or path.is_relative_to(skipped)
                    for skipped in skipped_targets
                )
            }
            unsupported_files += len(unreported_files)
        category_counts = Counter(item["category"] for item in diagnostics)
        scanner_errors = category_counts["scanner_failure"] + skipped_failures
        rules_executed = None
        time_payload = payload.get("time")
        if isinstance(time_payload, dict) and "rules" in time_payload:
            rules = time_payload["rules"]
            if isinstance(rules, (list, dict)):
                rules_executed = len(rules)
        elif "rules" in payload and isinstance(payload["rules"], (list, dict)):
            rules_executed = len(payload["rules"])
        else:
            stats = payload.get("stats")
            if isinstance(stats, dict) and "rules" in stats:
                rules = stats["rules"]
                if isinstance(rules, int) and rules >= 0:
                    rules_executed = rules
                elif isinstance(rules, (list, dict)):
                    rules_executed = len(rules)
        severity_counts = Counter(item["severity"] for item in findings)
        security_score = max(
            0,
            100
            - severity_counts["CRITICAL"] * 25
            - (severity_counts["HIGH"] + severity_counts["ERROR"]) * 15
            - (severity_counts["MEDIUM"] + severity_counts["WARNING"]) * 7
            - (severity_counts["LOW"] + severity_counts["INFO"]) * 2,
        )
        searchable = [
            {
                "file": item.get("file"),
                "rule_id": item.get("rule_id"),
                "line": item.get("line"),
                "category": (item.get("metadata") or {}).get(
                    "_testforge_category"
                ),
                "function": (item.get("metadata") or {}).get("function"),
            }
            for item in findings
            if item.get("file") and item.get("rule_id") and item.get("line")
        ]
        facet_terms = {
            "authentication_code": ("auth", "oauth", "login", "credential"),
            "jwt_usage": ("jwt", "json web token"),
            "password_handling": ("password", "passwd", "bcrypt", "argon"),
            "secret_usage": ("secret", "private key", "api key", "credential"),
            "file_upload_handlers": ("upload", "multipart", "filename"),
            "database_access": ("sql", "database", "query", "orm"),
            "external_http_requests": ("http", "request", "url", "ssrf"),
        }
        facets: dict[str, list[dict]] = {name: [] for name in facet_terms}
        for finding, location in zip(findings, searchable, strict=False):
            metadata = finding.get("metadata") or {}
            haystack = " ".join(
                str(value)
                for value in (
                    finding.get("rule_id"), finding.get("message"),
                    finding.get("file"), metadata.get("technology"),
                    metadata.get("category"),
                )
                if value is not None
            ).lower()
            for facet, terms in facet_terms.items():
                if any(term in haystack for term in terms):
                    facets[facet].append(location)
        return {
            "total_findings": len(findings),
            "by_severity": dict(severity_counts),
            "security_score": security_score,
            "security_context": {
                "vulnerable_files": sorted(
                    {item["file"] for item in searchable}
                ),
                "vulnerable_locations": searchable,
                **facets,
            },
            "files_scanned": len(scanned_files),
            "errors": scanner_errors,
            "warnings": category_counts["warning"],
            "informational": category_counts["information"],
            "parser_errors": category_counts["parser_error"],
            "unsupported_files": unsupported_files,
            "skipped_files": sum(skipped_by_reason.values()),
            "skipped_by_reason": dict(skipped_by_reason),
            "diagnostics": diagnostics[:100],
            "engine": "semgrep",
            "engine_version": (
                str(payload["version"]) if payload.get("version") else None
            ),
            "duration_ms": duration_ms,
            "rules_executed": rules_executed,
            "raw_semgrep_json": payload,
        }
