"""Discover, start, verify, and stop an uploaded ASGI backend."""

from __future__ import annotations

import ast
from collections import deque
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable

from app.services.runtime.openapi_metadata_service import OpenAPIMetadataService


logger = logging.getLogger(__name__)

SUT_BASE_URL = "http://127.0.0.1:8001"


def find_available_port(preferred_port: int = 8001) -> int:
    """Return an available local TCP port, preferring preferred_port if free."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", preferred_port))
            return preferred_port
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class SUTBackendStartupError(RuntimeError):
    """Raised when the uploaded backend cannot be safely made available."""


@dataclass(frozen=True)
class ASGIEntryPoint:
    framework: str
    file: Path
    module: str
    application: str

    @property
    def import_target(self) -> str:
        return f"{self.module}:{self.application}"


@dataclass(frozen=True)
class _RankedASGICandidate:
    entry_point: ASGIEntryPoint
    score: int
    signals: tuple[str, ...]
    router_count: int
    module_depth: int


@dataclass
class _RuntimeEnvironment:
    temporary_directory: tempfile.TemporaryDirectory[str]
    source_directory: Path
    database_url: str
    environment: dict[str, str]
    strategy: str

    def close(self) -> None:
        self.temporary_directory.cleanup()


class SUTBackendLease:
    """An OpenAPI document and optional child process owned by this run."""

    def __init__(
        self,
        document: dict[str, Any],
        *,
        process: subprocess.Popen[str] | None = None,
        output: deque[str] | None = None,
        output_activity: threading.Event | None = None,
        command: list[str] | None = None,
        entry_point: ASGIEntryPoint | None = None,
        runtime_environment: _RuntimeEnvironment | None = None,
        port: int = 8001,
        base_url: str = "http://127.0.0.1:8001",
    ) -> None:
        self.document = document
        self.process = process
        # Preserve the exact buffer populated by the process reader thread.
        # An empty deque is a valid supplied buffer, but is falsey.
        self.output = output if output is not None else deque(maxlen=400)
        self._output_activity = output_activity or threading.Event()
        self.command = command or []
        self.entry_point = entry_point
        self.runtime_environment = runtime_environment
        self.port = port
        self.base_url = base_url
        self._closed = False

    @property
    def spawned(self) -> bool:
        return self.process is not None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            if self.runtime_environment is not None:
                self.runtime_environment.close()

    def __enter__(self) -> "SUTBackendLease":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def captured_output(self, *, wait_for_diagnostics: bool = False) -> list[str]:
        """Return a stable snapshot of merged process stdout and stderr."""
        if wait_for_diagnostics and self.spawned:
            # An ASGI server sends the HTTP 500 response before its error logger
            # necessarily finishes writing the traceback. Wait for a short quiet
            # period so the reader thread can drain those diagnostic lines.
            quiet_intervals = 0
            while quiet_intervals < 3:
                self._output_activity.clear()
                if self._output_activity.wait(timeout=0.1):
                    quiet_intervals = 0
                else:
                    quiet_intervals += 1
        return list(self.output.copy())


class SUTBackendManager:
    def __init__(
        self,
        openapi: OpenAPIMetadataService,
        *,
        process_factory: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
        command_runner: Callable[
            ..., subprocess.CompletedProcess[str]
        ] = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        port_probe: Callable[[], bool] | None = None,
    ) -> None:
        self._openapi = openapi
        self._process_factory = process_factory
        self._command_runner = command_runner
        self._clock = clock
        self._sleep = sleep
        self._port_probe = port_probe or self._port_8001_in_use

    def ensure_running(
        self,
        source_directory: Path,
        *,
        expected_endpoints: list[dict[str, Any]],
        timeout_seconds: int = 30,
        port: int | None = None,
    ) -> SUTBackendLease:
        source_directory = source_directory.resolve()
        if not source_directory.is_dir():
            raise SUTBackendStartupError(
                f"Uploaded project source directory does not exist: "
                f"{source_directory}"
            )
        allocated_port = port or find_available_port()
        target_base_url = f"http://127.0.0.1:{allocated_port}"
        existing, _ = self._openapi.load_document(
            base_url=target_base_url, timeout_seconds=1
        )
        if existing is not None:
            if self._matches_project(
                existing, expected_endpoints, require_exact=True
            ):
                return SUTBackendLease(
                    existing, port=allocated_port, base_url=target_base_url
                )
            raise SUTBackendStartupError(
                f"Port {allocated_port} is already in use by a different application. "
                "Its OpenAPI document does not match the uploaded project; "
                "the existing process was not modified."
            )

        runtime_environment = self._prepare_runtime_environment(source_directory)
        runtime_source = runtime_environment.source_directory
        try:
            entry = self.detect_entry_point(runtime_source)
            application_root = entry.file.parent
            runtime_environment.environment["PYTHONPATH"] = os.pathsep.join(
                dict.fromkeys([
                    str(application_root),
                    str(runtime_source),
                    runtime_environment.environment.get("PYTHONPATH", ""),
                ])
            ).rstrip(os.pathsep)
            self._initialize_database(runtime_environment, entry)
        except Exception:
            runtime_environment.close()
            raise
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            entry.import_target,
            "--host",
            "127.0.0.1",
            "--port",
            str(allocated_port),
        ]
        output: deque[str] = deque(maxlen=400)
        output_activity = threading.Event()
        environment = runtime_environment.environment.copy()
        options: dict[str, Any] = {
            "cwd": str(application_root),
            "env": environment,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
        }
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            options["start_new_session"] = True
        try:
            process = self._process_factory(command, **options)
        except OSError as error:
            runtime_environment.close()
            raise self._startup_error(
                entry, command, output, f"unable to launch uvicorn: {error}"
            ) from error
        thread = threading.Thread(
            target=self._capture_output,
            args=(process, output, output_activity),
            daemon=True,
        )
        thread.start()
        lease = SUTBackendLease(
            {},
            process=process,
            output=output,
            output_activity=output_activity,
            command=command,
            entry_point=entry,
            runtime_environment=runtime_environment,
            port=allocated_port,
            base_url=target_base_url,
        )
        wait_seconds = min(max(1, timeout_seconds), 30)
        deadline = self._clock() + wait_seconds
        try:
            while self._clock() < deadline:
                document, _ = self._openapi.load_document(
                    base_url=target_base_url, timeout_seconds=1
                )
                if document is not None:
                    if not self._matches_project(
                        document,
                        expected_endpoints,
                        allow_empty=True,
                    ):
                        thread.join(timeout=0.2)
                        raise self._startup_error(
                            entry,
                            command,
                            output,
                            "OpenAPI became reachable but did not match the "
                            "uploaded project",
                        )
                    lease.document = document
                    return lease
                exit_code = process.poll()
                if exit_code is not None:
                    thread.join(timeout=0.2)
                    raise self._startup_error(
                        entry,
                        command,
                        output,
                        f"uvicorn exited with code {exit_code}",
                    )
                self._sleep(0.25)
            raise self._startup_error(
                entry,
                command,
                output,
                f"timed out after {wait_seconds} seconds waiting for "
                "/openapi.json",
            )
        except Exception:
            lease.close()
            thread.join(timeout=1)
            raise

    @staticmethod
    def _prepare_runtime_environment(
        source_directory: Path,
    ) -> _RuntimeEnvironment:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="testforge-runtime-sut-"
        )
        runtime_root = Path(temporary_directory.name)
        runtime_source = runtime_root / "source"
        try:
            shutil.copytree(
                source_directory,
                runtime_source,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", "venv", "__pycache__", "*.pyc",
                    "*.db", "*.sqlite", "*.sqlite3",
                ),
            )
        except Exception:
            temporary_directory.cleanup()
            raise
        database_path = runtime_root / "runtime.db"
        database_url = f"sqlite:///{database_path.as_posix()}"
        environment = os.environ.copy()
        environment.update({
            "DATABASE_URL": database_url,
            "SQLALCHEMY_DATABASE_URL": database_url,
            "TEST_DATABASE_URL": database_url,
            "RUNTIME_VALIDATION": "true",
        })
        environment["PYTHONPATH"] = os.pathsep.join([
            str(runtime_source), environment.get("PYTHONPATH", "")
        ]).rstrip(os.pathsep)
        strategy = (
            "alembic"
            if next(runtime_source.rglob("alembic.ini"), None) is not None
            else "sqlalchemy"
            if SUTBackendManager._sqlalchemy_base(runtime_source) is not None
            else "none"
        )
        logger.info(
            "SUT runtime environment prepared strategy=%s source=%s database=%s",
            strategy,
            runtime_source,
            database_path,
        )
        return _RuntimeEnvironment(
            temporary_directory=temporary_directory,
            source_directory=runtime_source,
            database_url=database_url,
            environment=environment,
            strategy=strategy,
        )

    def _initialize_database(
        self,
        runtime: _RuntimeEnvironment,
        entry: ASGIEntryPoint,
    ) -> None:
        if runtime.strategy == "none":
            logger.info("SUT database initialization skipped strategy=none")
            return
        if runtime.strategy == "alembic":
            config_path = sorted(
                runtime.source_directory.rglob("alembic.ini")
            )[0]
            script = (
                "import os; from alembic import command; "
                "from alembic.config import Config; "
                f"cfg=Config({str(config_path)!r}); "
                "cfg.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL']); "
                "command.upgrade(cfg, 'head')"
            )
            working_directory = config_path.parent
        else:
            base = self._sqlalchemy_base(runtime.source_directory)
            assert base is not None
            module, symbol = base
            model_modules = self._sqlalchemy_model_modules(
                runtime.source_directory
            )
            script = (
                "import importlib, json; "
                "from pathlib import Path; "
                "from sqlalchemy import inspect; "
                f"importlib.import_module({entry.module!r}); "
                f"module=importlib.import_module({module!r}); "
                f"[importlib.import_module(name) for name in {model_modules!r}]; "
                f"base=getattr(module, {symbol!r}); "
                "bind=getattr(module, 'engine', None); "
                "metadata_tables=sorted(base.metadata.tables.keys()); "
                "url=str(bind.url); "
                "database=bind.url.database if bind.url.get_backend_name() == 'sqlite' else None; "
                "database_path=str(Path(database).resolve()) if database and database != ':memory:' else database; "
                "before=set(inspect(bind).get_table_names()); "
                "base.metadata.create_all(bind=bind); "
                "after=sorted(inspect(bind).get_table_names()); "
                "created=len(set(after)-before); "
                "assert not metadata_tables or after, "
                "'SQLAlchemy metadata contains tables but create_all produced zero tables'; "
                "print('SUT_DB_DIAGNOSTICS=' + json.dumps({"
                "'engine_url': url, 'database_path': database_path, "
                "'metadata_tables': metadata_tables, 'database_tables': after, "
                "'tables_created': created}))"
            )
            # Relative SQLite URLs must resolve exactly as they will when the
            # application is launched by Uvicorn.
            working_directory = entry.file.parent
        command = [sys.executable, "-c", script]
        try:
            completed = self._command_runner(
                command,
                cwd=str(working_directory),
                env=runtime.environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SUTBackendStartupError(
                f"Runtime database initialization failed ({runtime.strategy}): "
                f"{error}"
            ) from error
        if completed.returncode != 0:
            output = (completed.stderr or completed.stdout or "").strip()
            raise SUTBackendStartupError(
                f"Runtime database initialization failed ({runtime.strategy})"
                + (f": {output}" if output else "")
            )
        stdout = (completed.stdout or "").strip()
        diagnostics = next(
            (
                line.removeprefix("SUT_DB_DIAGNOSTICS=")
                for line in stdout.splitlines()
                if line.startswith("SUT_DB_DIAGNOSTICS=")
            ),
            None,
        )
        if diagnostics is not None:
            details = json.loads(diagnostics)
            logger.info(
                "SUT SQLAlchemy database paths initialization=%s "
                "runtime_application=%s initialization_cwd=%s "
                "runtime_application_cwd=%s",
                details.get("database_path"),
                details.get("database_path"),
                Path(working_directory).resolve(),
                entry.file.parent.resolve(),
            )
            logger.info(
                "SUT SQLAlchemy metadata_tables=%s database_tables=%s "
                "table_count=%s tables_created=%s",
                details.get("metadata_tables", []),
                details.get("database_tables", []),
                len(details.get("database_tables", [])),
                details.get("tables_created", 0),
            )
        logger.info(
            "SUT database initialization completed strategy=%s "
            "injected_database=%s",
            runtime.strategy,
            Path(runtime.database_url.removeprefix("sqlite:///")).resolve(),
        )

    @staticmethod
    def _sqlalchemy_base(source_directory: Path) -> tuple[str, str] | None:
        for path in sorted(source_directory.rglob("*.py")):
            parsed = SUTBackendManager._parse_python_file(path)
            if parsed is None:
                continue
            tree = parsed[0]
            relative = path.relative_to(source_directory)
            module = relative.with_suffix("").as_posix().replace("/", ".")
            for node in tree.body:
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    value = node.value
                    targets = (
                        node.targets if isinstance(node, ast.Assign)
                        else [node.target]
                    )
                    if (
                        isinstance(value, ast.Call)
                        and SUTBackendManager._is_declarative_base(value)
                    ):
                        target = next(
                            (item for item in targets if isinstance(item, ast.Name)),
                            None,
                        )
                        if target is not None:
                            return module, target.id
                if isinstance(node, ast.ClassDef) and any(
                    (
                        isinstance(base, ast.Name)
                        and base.id == "DeclarativeBase"
                    ) or (
                        isinstance(base, ast.Attribute)
                        and base.attr == "DeclarativeBase"
                    )
                    for base in node.bases
                ):
                    return module, node.name
        return None

    @staticmethod
    def _sqlalchemy_model_modules(source_directory: Path) -> list[str]:
        """Find modules that declare mapped classes or SQLAlchemy tables."""
        modules: list[str] = []
        for path in sorted(source_directory.rglob("*.py")):
            parsed = SUTBackendManager._parse_python_file(path)
            if parsed is None:
                continue
            tree = parsed[0]
            declares_model = any(
                (
                    isinstance(node, ast.ClassDef)
                    and any(
                        (
                            isinstance(base, ast.Name)
                            and base.id in {"Base", "DeclarativeBase"}
                        ) or (
                            isinstance(base, ast.Attribute)
                            and base.attr in {"Base", "DeclarativeBase"}
                        )
                        for base in node.bases
                    )
                ) or (
                    isinstance(node, (ast.Assign, ast.AnnAssign))
                    and isinstance(node.value, ast.Call)
                    and (
                        (
                            isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "Table"
                        ) or (
                            isinstance(node.value.func, ast.Attribute)
                            and node.value.func.attr == "Table"
                        )
                    )
                )
                for node in tree.body
            )
            if not declares_model:
                continue
            relative = path.relative_to(source_directory).with_suffix("")
            parts = list(relative.parts)
            if parts[-1] == "__init__":
                parts.pop()
            if parts:
                modules.append(".".join(parts))
        return modules
    @staticmethod
    def _is_declarative_base(call: ast.Call) -> bool:
        function = call.func
        return (
            isinstance(function, ast.Name) and function.id == "declarative_base"
        ) or (
            isinstance(function, ast.Attribute)
            and function.attr == "declarative_base"
        )

    @staticmethod
    def detect_entry_point(source_directory: Path) -> ASGIEntryPoint:
        source_directory = source_directory.resolve()
        python_files = (
            sorted(source_directory.rglob("*.py"))
            if source_directory.is_dir()
            else []
        )
        logger.warning(
            "SUT discovery diagnostics: source_directory=%s exists=%s "
            "contains_python_files=%s python_file_count=%d",
            source_directory,
            source_directory.is_dir(),
            bool(python_files),
            len(python_files),
        )
        test_references = SUTBackendManager._test_app_references(
            python_files, source_directory
        )
        declared_entrypoints = SUTBackendManager._declared_entrypoints(
            source_directory
        )
        candidates: list[_RankedASGICandidate] = []
        for path in python_files:
            parsed = SUTBackendManager._parse_python_file(path)
            SUTBackendManager._log_file_diagnostics(path, parsed=parsed)
            if parsed is None:
                continue
            tree, imports, framework_imports, assignment_targets = parsed
            assignments = SUTBackendManager._application_assignments(tree)
            if not assignments:
                logger.warning(
                    "SUT Python file rejected: file=%s reason=%s",
                    path,
                    (
                        "no supported FastAPI/Starlette import detected"
                        if not framework_imports
                        else "no supported top-level assignment to an "
                        "imported FastAPI/Starlette constructor"
                    ),
                )
                continue
            relative = path.relative_to(source_directory)
            module = relative.with_suffix("").as_posix().replace("/", ".")
            for framework, application in assignments:
                entry = ASGIEntryPoint(
                    framework=framework,
                    file=path,
                    module=module,
                    application=application,
                )
                candidates.append(SUTBackendManager._rank_candidate(
                    entry,
                    tree=tree,
                    source_directory=source_directory,
                    imports=imports,
                    test_references=test_references,
                    declared_entrypoints=declared_entrypoints,
                ))

        ranked = sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                -candidate.router_count,
                candidate.module_depth,
                len(candidate.entry_point.module),
                candidate.entry_point.import_target,
            ),
        )
        for position, candidate in enumerate(ranked, start=1):
            logger.warning(
                "SUT ASGI candidate ranking: rank=%d target=%s framework=%s "
                "file=%s score=%d router_count=%d module_depth=%d signals=%s",
                position,
                candidate.entry_point.import_target,
                candidate.entry_point.framework,
                candidate.entry_point.file,
                candidate.score,
                candidate.router_count,
                candidate.module_depth,
                list(candidate.signals),
            )

        if ranked:
            selected = ranked[0].entry_point
            logger.warning(
                "SUT ASGI candidate selected: target=%s framework=%s file=%s",
                selected.import_target,
                selected.framework,
                selected.file,
            )
            return selected
        raise SUTBackendStartupError(
            "No supported FastAPI or Starlette application entry point was "
            f"found after recursively scanning {len(python_files)} Python files "
            f"under {source_directory}."
        )

    @staticmethod
    def _parse_python_file(
        path: Path,
    ) -> tuple[ast.Module, list[str], list[str], list[str]] | None:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError):
            return None
        imports: list[str] = []
        framework_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    rendered = name.name + (
                        f" as {name.asname}" if name.asname else ""
                    )
                    imports.append(rendered)
                    if name.name in {"fastapi", "starlette"}:
                        framework_imports.append(rendered)
            elif isinstance(node, ast.ImportFrom):
                rendered_names = [
                    name.name + (f" as {name.asname}" if name.asname else "")
                    for name in node.names
                ]
                rendered = f"from {node.module or ''} import {', '.join(rendered_names)}"
                imports.append(rendered)
                if node.module in {"fastapi", "starlette.applications"} and any(
                    name.name in {"FastAPI", "Starlette"}
                    for name in node.names
                ):
                    framework_imports.append(rendered)

        assignment_targets: list[str] = []
        for node in ast.walk(tree):
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target] if isinstance(node, ast.AnnAssign) else []
            )
            assignment_targets.extend(
                target.id for target in targets if isinstance(target, ast.Name)
            )
        return tree, imports, framework_imports, assignment_targets

    @staticmethod
    def _log_file_diagnostics(
        path: Path,
        *,
        parsed: tuple[ast.Module, list[str], list[str], list[str]] | None,
    ) -> None:
        if parsed is None:
            logger.warning(
                "SUT Python file scan: file=%s ast_parsed=false "
                "imports=[] framework_imports=[] assignment_targets=[] "
                "asgi_app_candidates=[]",
                path,
            )
            return
        tree, imports, framework_imports, assignment_targets = parsed
        detected = SUTBackendManager._application_assignments(tree)
        logger.warning(
            "SUT Python file scan: file=%s ast_parsed=true imports=%s "
            "framework_imports=%s "
            "assignment_targets=%s asgi_app_candidates=%s rejection=%s",
            path,
            imports,
            framework_imports,
            assignment_targets,
            [f"{application}:{framework}" for framework, application in detected],
            "none" if detected else "no ASGI application assignment",
        )

    @staticmethod
    def _application_assignments(tree: ast.Module) -> list[tuple[str, str]]:
        constructors: dict[str, str] = {}
        module_aliases: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module in {
                "fastapi", "starlette.applications"
            }:
                for name in node.names:
                    if name.name in {"FastAPI", "Starlette"}:
                        constructors[name.asname or name.name] = name.name
            elif isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in {"fastapi", "starlette"}:
                        module_aliases[name.asname or name.name] = name.name
        detected: list[tuple[str, str]] = []
        for node in tree.body:
            value = (
                node.value
                if isinstance(node, (ast.Assign, ast.AnnAssign))
                else None
            )
            target = (
                node.targets[0]
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                else node.target if isinstance(node, ast.AnnAssign) else None
            )
            if (
                not isinstance(target, ast.Name)
                or not isinstance(value, ast.Call)
            ):
                continue
            constructor = value.func
            if isinstance(constructor, ast.Name):
                framework = constructors.get(constructor.id)
            elif (
                isinstance(constructor, ast.Attribute)
                and isinstance(constructor.value, ast.Name)
                and constructor.value.id in module_aliases
            ):
                framework = (
                    "FastAPI" if constructor.attr == "FastAPI"
                    else "Starlette" if constructor.attr == "Starlette"
                    else None
                )
            else:
                framework = None
            if framework is not None:
                detected.append((framework, target.id))
        return detected

    @staticmethod
    def _application_assignment(path: Path) -> tuple[str, str] | None:
        parsed = SUTBackendManager._parse_python_file(path)
        if parsed is None:
            return None
        detected = SUTBackendManager._application_assignments(parsed[0])
        return detected[0] if detected else None

    @staticmethod
    def _test_app_references(
        python_files: list[Path], source_directory: Path
    ) -> set[tuple[str, str]]:
        references: set[tuple[str, str]] = set()
        for path in python_files:
            relative_parts = path.relative_to(source_directory).parts
            if not any(part.casefold() in {"test", "tests"} for part in relative_parts):
                continue
            parsed = SUTBackendManager._parse_python_file(path)
            if parsed is None:
                continue
            for node in ast.walk(parsed[0]):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for name in node.names:
                        references.add((node.module, name.name))
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        references.add((name.name, "*"))
        return references

    @staticmethod
    def _declared_entrypoints(source_directory: Path) -> str:
        declarations: list[str] = []
        names = {"dockerfile", "readme", "readme.md", "readme.rst", "pyproject.toml"}
        for path in sorted(source_directory.rglob("*")):
            if not path.is_file() or path.name.casefold() not in names:
                continue
            try:
                declarations.append(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                continue
        return "\n".join(declarations)

    @staticmethod
    def _rank_candidate(
        entry: ASGIEntryPoint,
        *,
        tree: ast.Module,
        source_directory: Path,
        imports: list[str],
        test_references: set[tuple[str, str]],
        declared_entrypoints: str,
    ) -> _RankedASGICandidate:
        relative = entry.file.relative_to(source_directory)
        module_depth = len(relative.parts)
        signals: list[str] = []
        score = 0
        if entry.file.name.casefold() == "main.py":
            score += 100
            signals.append("filename=main.py")
        if entry.file.parent == source_directory or (
            entry.file.parent / "__init__.py"
        ).is_file():
            score += 40
            signals.append("package-root")
        if (
            (entry.module, entry.application) in test_references
            or (entry.module, "*") in test_references
            or (entry.file.stem, entry.application) in test_references
        ):
            score += 35
            signals.append("referenced-by-tests")

        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        has_uvicorn_run = any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "run"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "uvicorn"
            for call in calls
        )
        if has_uvicorn_run:
            score += 30
            signals.append("contains-uvicorn.run")
        imports_routers = any("router" in imported.casefold() for imported in imports)
        if imports_routers:
            score += 25
            signals.append("imports-router")
        router_count = sum(
            1
            for call in calls
            if isinstance(call.func, ast.Attribute)
            and call.func.attr == "include_router"
        )
        if router_count:
            score += min(router_count, 20) * 5
            signals.append(f"router-count={router_count}")
        declaration_tokens = {
            entry.import_target,
            f"{entry.module}.{entry.application}",
        }
        if any(token in declared_entrypoints for token in declaration_tokens):
            score += 20
            signals.append("declared-entrypoint")
        score += max(0, 10 - module_depth)
        signals.append(f"module-depth={module_depth}")
        return _RankedASGICandidate(
            entry_point=entry,
            score=score,
            signals=tuple(signals),
            router_count=router_count,
            module_depth=module_depth,
        )

    @staticmethod
    def _matches_project(
        document: dict[str, Any],
        expected_endpoints: list[dict[str, Any]],
        *,
        require_exact: bool = False,
        allow_empty: bool = False,
    ) -> bool:
        expected = {
            (
                endpoint.get("route"),
                str(endpoint.get("method") or "").casefold(),
            )
            for endpoint in expected_endpoints
            if endpoint.get("route") and endpoint.get("method")
        }
        if not expected:
            return allow_empty
        paths = document.get("paths", {})
        actual = {
            (route, method.casefold())
            for route, operations in paths.items()
            if isinstance(operations, dict)
            for method in operations
            if method.casefold() in {
                "get", "post", "put", "patch", "delete", "head", "options"
            }
        }
        return expected == actual if require_exact else expected.issubset(actual)

    @staticmethod
    def _capture_output(
        process: subprocess.Popen[str], output: deque[str],
        output_activity: threading.Event | None = None,
    ) -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            output.append(line.rstrip())
            if output_activity is not None:
                output_activity.set()

    @staticmethod
    def _port_8001_in_use() -> bool:
        try:
            with socket.create_connection(("127.0.0.1", 8001), timeout=0.25):
                return True
        except OSError:
            return False

    @staticmethod
    def _startup_error(
        entry: ASGIEntryPoint,
        command: list[str],
        output: deque[str],
        reason: str,
    ) -> SUTBackendStartupError:
        logs = "\n".join(output) or "(no process output)"
        return SUTBackendStartupError(
            "Uploaded backend startup failed.\n"
            f"Detected entry point: {entry.import_target} "
            f"({entry.framework}, {entry.file})\n"
            f"Startup command: {subprocess.list2cmdline(command)}\n"
            f"Reason: {reason}\n"
            f"stdout/stderr:\n{logs}"
        )
