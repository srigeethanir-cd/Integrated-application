"""Build a safe, executable pytest project from persisted TestForge artifacts."""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sys
import tempfile
import textwrap
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.runtime.test_file_builder import UNIT_TEST_PREAMBLE

logger = logging.getLogger(__name__)

EXPORT_VERSION = "1.0"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")


class ExportValidationError(ValueError):
    """The persisted pipeline state cannot produce a valid export."""


class ExportArtifactError(ExportValidationError):
    """A generated test artifact is missing or corrupted."""


class ExportCreationError(RuntimeError):
    """The archive could not be written."""


class PytestExportService:
    """Create a temporary ZIP archive without mutating project source files."""

    def __init__(self, *, generator_version: str) -> None:
        self._generator_version = generator_version

    def create_archive(self, *, project_name: str, pipeline_state: dict[str, Any]) -> Path:
        generation, quality = self._select_generation(pipeline_state)
        cases = generation.get("generated_test_cases")
        if not isinstance(cases, list) or not cases:
            raise ExportValidationError("No generated tests are available for export")

        grouped: dict[PurePosixPath, list[str]] = defaultdict(list)
        shared_fixtures: dict[str, str] = {}
        fixture_imports: set[str] = set()
        requires_asyncio = False
        requires_mock = False
        categories: set[str] = set()

        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                raise ExportArtifactError(f"Generated test at index {index} is not an object")
            code = self._exportable_code(case, index)
            path = self._safe_test_path(case, index)
            module_code, fixtures, imports = self._split_fixtures(
                code, case_index=index
            )
            if module_code.strip() and module_code not in grouped[path]:
                grouped[path].append(module_code)
            for name, fixture_code in fixtures.items():
                previous = shared_fixtures.get(name)
                if previous is not None and previous != fixture_code:
                    raise ExportArtifactError(
                        f"Fixture {name!r} has conflicting definitions"
                    )
                shared_fixtures[name] = fixture_code
            if fixtures:
                fixture_imports.update(imports)
            requires_asyncio = requires_asyncio or "pytest.mark.asyncio" in code or "async def test_" in code
            requires_mock = requires_mock or "mocker" in code or "pytest_mock" in code
            category = case.get("category")
            if isinstance(category, str) and category.strip():
                categories.add(category.strip())

        if not grouped:
            raise ExportArtifactError("Generated artifacts contain no executable test code")

        generation_time = datetime.now(UTC)
        manifest = self._manifest(
            project_name=project_name,
            generation_time=generation_time,
            generated_tests=len(cases),
            pipeline_state=pipeline_state,
            quality=quality,
        )
        fd, archive_name = tempfile.mkstemp(prefix="testforge-export-", suffix=".zip")
        os.close(fd)
        archive_path = Path(archive_name)
        try:
            with zipfile.ZipFile(
                archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
            ) as archive:
                root = PurePosixPath("test-suite")
                self._write(archive, root / "README.md", self._readme(project_name, generation_time, len(cases), manifest))
                self._write(archive, root / "pytest.ini", self._pytest_ini(categories, requires_asyncio))
                self._write(archive, root / "requirements-test.txt", self._requirements(requires_asyncio, requires_mock))
                self._write(archive, root / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
                self._write(
                    archive,
                    root / "conftest.py",
                    self._conftest(shared_fixtures, fixture_imports),
                )
                for directory in ("tests/", "tests/services/", "tests/repositories/", "tests/api/", "tests/utils/"):
                    archive.writestr(f"{root}/{directory}", b"")
                for test_path, modules in sorted(grouped.items(), key=lambda item: str(item[0])):
                    self._write(archive, root / test_path, self._merge_modules(modules, test_path))
        except ExportValidationError:
            archive_path.unlink(missing_ok=True)
            raise
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            archive_path.unlink(missing_ok=True)
            logger.exception("Unable to create pytest export archive")
            raise ExportCreationError("Unable to create the test-suite ZIP archive") from error
        return archive_path

    @staticmethod
    def _select_generation(pipeline_state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        quality = pipeline_state.get("quality_optimization")
        if isinstance(quality, dict):
            optimized = quality.get("optimized_test_suite")
            if isinstance(optimized, list) and optimized:
                base = pipeline_state.get("test_generation")
                generation = dict(base) if isinstance(base, dict) else {}
                generation["generated_test_cases"] = optimized
                return generation, quality
            nested = quality.get("test_generation")
            if isinstance(nested, dict) and nested.get("generated_test_cases"):
                return nested, quality
        generation = pipeline_state.get("test_generation")
        if not isinstance(generation, dict):
            raise ExportValidationError("The generated test artifact is missing or corrupted")
        return generation, quality if isinstance(quality, dict) else None

    @staticmethod
    def _generated_code(case: dict[str, Any], index: int) -> str:
        unit_test = case.get("unit_test")
        if not isinstance(unit_test, dict):
            raise ExportArtifactError(f"Generated test at index {index} has no unit_test metadata")
        code = unit_test.get("generated_code")
        if not isinstance(code, str) or not code.strip():
            raise ExportArtifactError(f"Generated test at index {index} has no executable Python code")
        return code.strip() + "\n"

    @classmethod
    def _exportable_code(cls, case: dict[str, Any], index: int) -> str:
        """Wrap Stage 4 body fragments with the Stage 6 runtime contract."""
        code = cls._generated_code(case, index)
        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            raise ExportArtifactError(
                f"Generated test at index {index} contains invalid Python"
            ) from error
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in tree.body
        ):
            return code
        unit_test = case.get("unit_test") or {}
        module = str(unit_test.get("module") or "")
        source_file = str(unit_test.get("file") or (case.get("traceability") or {}).get("file") or "")
        if not module or not source_file:
            raise ExportArtifactError(
                f"Generated test at index {index} lacks module or source-file metadata"
            )
        code = code.replace(
            f"module = importlib.import_module({module!r})",
            f"module = _import_unit_module({module!r}, {source_file!r})",
            1,
        ).replace(
            "_unit_arguments(target)",
            "_unit_arguments(target, dependency_mock, test_variant)",
        )
        identifier = re.sub(r"[^a-zA-Z0-9_]+", "_", str(case.get("id") or index)).strip("_").casefold()
        return (
            f"def test_{identifier}(dependency_mock, monkeypatch):\n"
            + textwrap.indent(code.rstrip(), "    ")
            + "\n"
        )

    @staticmethod
    def _safe_test_path(case: dict[str, Any], index: int) -> PurePosixPath:
        traceability = case.get("traceability")
        raw = traceability.get("suggested_test_path") if isinstance(traceability, dict) else None
        if not isinstance(raw, str) or not raw.strip():
            raise ExportArtifactError(
                f"Generated test at index {index} is missing suggested_test_path metadata"
            )
        normalized = raw.strip().replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ExportArtifactError(f"Unsafe suggested_test_path: {raw!r}")
        parts = list(path.parts)
        if parts[0] != "tests":
            parts.insert(0, "tests")
        if any(not _SAFE_SEGMENT.fullmatch(part) for part in parts):
            raise ExportArtifactError(f"Invalid suggested_test_path: {raw!r}")
        if not parts[-1].startswith("test_") or not parts[-1].endswith(".py"):
            raise ExportArtifactError(f"Suggested test path must name a test_*.py file: {raw!r}")
        return PurePosixPath(*parts)

    @staticmethod
    def _split_fixtures(
        code: str, *, case_index: int
    ) -> tuple[str, dict[str, str], set[str]]:
        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            raise ExportArtifactError(
                f"Generated test at index {case_index} contains invalid Python: {error.msg}"
            ) from error
        fixtures: dict[str, str] = {}
        imports: set[str] = set()
        retained: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.add(ast.unparse(node))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                PytestExportService._is_fixture_decorator(item) for item in node.decorator_list
            ):
                fixtures[node.name] = ast.get_source_segment(code, node) or ast.unparse(node)
            else:
                retained.append(node)
        module = ast.Module(body=retained, type_ignores=[])
        return (
            ast.unparse(ast.fix_missing_locations(module)).strip() + "\n",
            fixtures,
            imports,
        )

    @staticmethod
    def _is_fixture_decorator(node: ast.expr) -> bool:
        target = node.func if isinstance(node, ast.Call) else node
        return (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "pytest"
            and target.attr == "fixture"
        ) or isinstance(target, ast.Name) and target.id == "fixture"

    @staticmethod
    def _merge_modules(modules: list[str], path: PurePosixPath) -> str:
        unique: dict[str, ast.stmt] = {}
        for code in modules:
            tree = ast.parse(code)
            for node in tree.body:
                key = ast.dump(node, include_attributes=False)
                unique.setdefault(key, node)
        merged = ast.Module(body=list(unique.values()), type_ignores=[])
        result = ast.unparse(ast.fix_missing_locations(merged)).strip()
        if not result:
            raise ExportArtifactError(f"No executable content remains for {path}")
        preamble = UNIT_TEST_PREAMBLE.format(
            result_directory=".testforge-results",
            base_url="",
        )
        start = preamble.index("# TESTFORGE_HTTP_SUPPORT_START")
        end = preamble.index("# TESTFORGE_HTTP_SUPPORT_END")
        preamble = (
            preamble[:start]
            + preamble[end + len("# TESTFORGE_HTTP_SUPPORT_END"):]
        ).rstrip()
        return preamble + "\n\n" + result + "\n"

    @staticmethod
    def _conftest(fixtures: dict[str, str], imports: set[str]) -> str:
        import_lines = sorted(imports | {"import pytest"})
        header = (
            '"""Shared fixtures generated by TestForge."""\n\n'
            + "\n".join(import_lines)
            + "\n"
        )
        if not fixtures:
            return header
        return header + "\n\n" + "\n\n".join(fixtures[name] for name in sorted(fixtures)) + "\n"

    @staticmethod
    def _requirements(asyncio: bool, mock: bool) -> str:
        dependencies = ["pytest>=8.3,<9.0"]
        if asyncio:
            dependencies.append("pytest-asyncio>=0.24,<1.0")
        if mock:
            dependencies.append("pytest-mock>=3.14,<4.0")
        return "\n".join(dependencies) + "\n"

    @staticmethod
    def _pytest_ini(categories: set[str], asyncio: bool) -> str:
        markers = sorted({re.sub(r"[^a-z0-9_]+", "_", item.casefold()).strip("_") for item in categories})
        lines = ["[pytest]", "testpaths = tests", "python_files = test_*.py", "python_classes = Test*", "python_functions = test_*", "addopts = -ra --strict-markers"]
        if asyncio:
            lines.append("asyncio_mode = auto")
        if markers:
            lines.append("markers =")
            lines.extend(f"    {marker}: TestForge generated {marker.replace('_', ' ')} tests" for marker in markers if marker)
        return "\n".join(lines) + "\n"

    def _manifest(self, *, project_name: str, generation_time: datetime, generated_tests: int, pipeline_state: dict[str, Any], quality: dict[str, Any] | None) -> dict[str, Any]:
        verification = pipeline_state.get("test_verification")
        verification_status: str | None = None
        if isinstance(verification, dict) and isinstance(verification.get("summary"), dict):
            summary = verification["summary"]
            verification_status = "failed" if summary.get("failed", 0) else "needs_review" if summary.get("partial", 0) else "verified"
        runtime = pipeline_state.get("runtime_execution_plan")
        runtime_status = runtime.get("status") if isinstance(runtime, dict) else None
        quality_score = quality.get("final_score") if quality else None
        return {
            "export_version": EXPORT_VERSION,
            "generated_tests": generated_tests,
            "generation_time": generation_time.isoformat(),
            "generator_version": self._generator_version,
            "project_name": project_name,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "quality_score": quality_score,
            "runtime_validation_status": runtime_status,
            "verification_status": verification_status,
        }

    def _readme(self, project_name: str, generated_at: datetime, count: int, manifest: dict[str, Any]) -> str:
        runtime = manifest["runtime_validation_status"] or "Not recorded"
        return f"""# {project_name} — TestForge pytest suite

Production-ready unit tests generated by TestForge.

## Export information

- Generated: {generated_at.isoformat()}
- Generator version: {self._generator_version}
- Export version: {EXPORT_VERSION}
- Generated tests: {count}
- Python: {manifest['python_version']}+
- Verification: {manifest['verification_status'] or 'Not recorded'}
- Runtime validation: {runtime}

## Install

Run these commands from the application repository so its source package is importable:

```bash
python -m venv .venv
python -m pip install -r test-suite/requirements-test.txt
python -m pip install -e .
```

## Run

```bash
pytest -c test-suite/pytest.ini test-suite/tests
```

## Known limitations

- Application dependencies are owned by the source project and are intentionally not duplicated here.
- Runtime validation status is included only when it was persisted with the generation run.
- Generated mocks and fixtures reflect the repository state at generation time.
"""

    @staticmethod
    def _write(archive: zipfile.ZipFile, path: PurePosixPath, content: str) -> None:
        if path.is_absolute() or ".." in path.parts:
            raise ExportCreationError(f"Refusing unsafe archive path: {path}")
        archive.writestr(str(path), content.encode("utf-8"))
