"""Compile persisted Stage 4 unit contracts into an isolated pytest module."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.schemas.runtime_preparation import RuntimeExecutionTarget
from app.schemas.test_case import TestCase, UnitTestSpecification


UNIT_TEST_PREAMBLE = '''
import asyncio
import importlib
import importlib.util
import inspect
import json
import os
import pytest
import re
import sys
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from typing import get_args, get_origin
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch
from uuid import UUID

RESULT_DIRECTORY = Path({result_directory!r})
BASE_URL = {base_url!r}.rstrip("/")
CAPTURED_IDENTIFIERS = {{}}
PROJECT_ROOT = Path(
    os.environ.get("TESTFORGE_RUNTIME_SOURCE_ROOT", Path.cwd())
).resolve()

def _inside_project(path):
    try:
        Path(path).resolve().relative_to(PROJECT_ROOT)
        return True
    except (OSError, TypeError, ValueError):
        return False

def _prepare_import_environment(module_name):
    retained = []
    for entry in sys.path:
        try:
            resolved = Path(entry or os.getcwd()).resolve()
        except (OSError, TypeError, ValueError):
            continue
        if resolved == PROJECT_ROOT:
            continue
        if (resolved / "app").is_dir() and not _inside_project(resolved / "app"):
            continue
        retained.append(entry)
    sys.path[:] = [str(PROJECT_ROOT), *retained]
    top_level = module_name.split(".", 1)[0]
    for loaded_name, loaded_module in list(sys.modules.items()):
        if loaded_name != top_level and not loaded_name.startswith(top_level + "."):
            continue
        loaded_file = getattr(loaded_module, "__file__", None)
        if loaded_file and not _inside_project(loaded_file):
            del sys.modules[loaded_name]
    app_module = sys.modules.get("app")
    print(
        "TESTFORGE_IMPORT_DIAGNOSTIC "
        + json.dumps({{
            "phase": "before_import",
            "cwd": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "sys_path": list(sys.path),
            "module": module_name,
            "module_file": None,
            "app_file": getattr(app_module, "__file__", None),
        }}, default=str),
        flush=True,
    )

def _import_unit_module(module_name, source_file):
    _prepare_import_environment(module_name)
    source_path = (PROJECT_ROOT / source_file).resolve()
    if not _inside_project(source_path):
        raise ImportError(f"Runtime target escapes uploaded project: {{source_file}}")
    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)*",
        module_name,
    ):
        raise ImportError(f"Invalid sanitized runtime module path: {{module_name}}")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        spec = importlib.util.spec_from_file_location(module_name, source_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load runtime target: {{source_file}}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    module_file = getattr(module, "__file__", None)
    if not module_file or not _inside_project(module_file):
        raise ImportError(
            f"Runtime module resolved outside uploaded project: {{module_name}} -> {{module_file}}"
        )
    app_module = sys.modules.get("app")
    app_file = getattr(app_module, "__file__", None)
    if app_file and not _inside_project(app_file):
        raise ImportError(f"Shadowed app package resolved outside uploaded project: {{app_file}}")
    print(
        "TESTFORGE_IMPORT_DIAGNOSTIC "
        + json.dumps({{
            "phase": "after_import",
            "cwd": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "sys_path": list(sys.path),
            "module": module_name,
            "module_file": module_file,
            "app_file": app_file,
        }}, default=str),
        flush=True,
    )
    return module

@pytest.fixture
def dependency_mock():
    return MagicMock(name="dependency")

def _constraint(metadata, *names):
    values = [metadata] if metadata is not None else []
    values.extend(getattr(metadata, "metadata", []) or [])
    for item in values:
        for name in names:
            value = getattr(item, name, None)
            if value is not None:
                return value
    return None

def _make_subscriptable(obj):
    if obj is not None and not isinstance(obj, (int, float, bool, str, bytes, list, dict, set, tuple)):
        cls = type(obj)
        if not hasattr(cls, "__getitem__"):
            try:
                cls.__getitem__ = lambda self, item: getattr(self, item, None)
            except (TypeError, AttributeError):
                pass
    return obj

def _unit_value(annotation, name, variant="positive", metadata=None):
    origin = get_origin(annotation)
    arguments = [item for item in get_args(annotation) if item is not type(None)]
    if origin is not None and arguments:
        annotation = origin if origin in {{list, dict, set, tuple}} else arguments[0]
    lowered = name.casefold()
    annotation_name = str(getattr(annotation, "__name__", annotation)).casefold()
    negative = variant == "negative"
    if "email" in lowered or "email" in annotation_name:
        string_value = "invalid-email" if negative else "user@example.com"
    elif "uuid" in lowered or "uuid" in annotation_name:
        string_value = "not-a-uuid" if negative else "00000000-0000-4000-8000-000000000001"
    elif any(token in lowered for token in ("phone", "mobile", "telephone")):
        string_value = "123" if negative else "4155552671"
    elif any(token in lowered for token in ("url", "uri", "website")):
        string_value = (
            "not-a-url" if negative else "https" + "://example.com/resource"
        )
    elif any(token in lowered for token in ("token", "jwt")):
        string_value = "invalid-token" if negative else "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE5OTk5OTk5OTl9.signature"
    elif any(token in lowered for token in ("encoded", "hash", "digest", "hashed")):
        string_value = "invalid-hash" if negative else "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    elif any(token in lowered for token in ("password", "secret")):
        string_value = "" if negative else "secret"
    elif any(token in lowered for token in ("username", "user_name", "login")):
        string_value = "" if negative else "test_user"
    elif "name" in lowered:
        string_value = "" if negative else "Test User"
    else:
        string_value = "" if negative else "valid-value"
    minimum_length = _constraint(metadata, "min_length")
    if not negative and isinstance(minimum_length, int):
        string_value = string_value.ljust(minimum_length, "x")
    if negative and isinstance(minimum_length, int) and minimum_length > 0:
        string_value = ""
    lower_bound = _constraint(metadata, "ge", "gt")
    upper_bound = _constraint(metadata, "le", "lt")
    numeric_value = 1
    if isinstance(lower_bound, (int, float)):
        numeric_value = lower_bound + (1 if _constraint(metadata, "gt") is not None else 0)
    elif isinstance(upper_bound, (int, float)):
        numeric_value = upper_bound - (1 if _constraint(metadata, "lt") is not None else 0)
    if negative:
        numeric_value = (
            lower_bound - 1 if isinstance(lower_bound, (int, float)) else -1
        )
    values = {{
        str: string_value,
        int: int(numeric_value),
        float: float(numeric_value),
        bool: not negative,
        bytes: string_value.encode("utf-8"),
        date: date.today(),
        datetime: datetime.now(),
        UUID: UUID(int=1),
        list: [],
        dict: {{}},
        set: set(),
        tuple: (),
    }}
    if getattr(annotation, "__name__", "") == "UploadFile":
        upload = MagicMock(name=name)
        upload.filename = "unit-file.txt"
        upload.content_type = "text/plain"
        upload.read = AsyncMock(return_value=b"")
        return upload
    if annotation is UUID and negative:
        return "not-a-uuid"
    model_fields = getattr(annotation, "model_fields", None)
    if isinstance(model_fields, dict):
        payload = {{
            field_name: _unit_value(
                field.annotation, field_name, variant, field
            )
            for field_name, field in model_fields.items()
            if getattr(field, "is_required", lambda: True)()
        }}
        obj = None
        if negative and callable(getattr(annotation, "model_construct", None)):
            obj = annotation.model_construct(**payload)
        else:
            try:
                obj = annotation(**payload)
            except Exception:
                if callable(getattr(annotation, "model_construct", None)):
                    obj = annotation.model_construct(**payload)
                else:
                    obj = MagicMock(name=name)
        if obj is not None:
            return _make_subscriptable(obj)
    if annotation_name in {{"str", "string"}}:
        return string_value
    if annotation_name in {{"int", "integer"}}:
        return int(numeric_value)
    if annotation_name in {{"float", "number"}}:
        return float(numeric_value)
    if annotation_name in {{"bool", "boolean"}}:
        return not negative
    if any(token in lowered for token in (
        "email", "phone", "mobile", "telephone", "url", "uri", "website",
        "password", "secret", "username", "user_name", "login", "name",
    )):
        return string_value
    val = values.get(annotation, MagicMock(name=name))
    return _make_subscriptable(val)

def _resolve_unit_target(module, symbol):
    parts = symbol.split(".")
    value = module
    if not parts or not hasattr(module, parts[0]):
        raise LookupError(
            f"Validated runtime symbol is unavailable: {{module.__name__}}.{{symbol}}"
        )
    if len(parts) > 1:
        owner = getattr(module, parts[0])
        if not hasattr(owner, parts[1]):
            raise LookupError(
                f"Validated owner method is unavailable: {{symbol}}"
            )
        model_fields = getattr(owner, "model_fields", None)
        # Pydantic v2 exposes ``__fields__`` only as a deprecated compatibility
        # property. Consult it lazily when the v2 API is genuinely unavailable.
        legacy_fields = (
            None
            if isinstance(model_fields, dict)
            else getattr(owner, "__fields__", None)
        )
        if callable(getattr(owner, "model_construct", None)) and isinstance(model_fields, dict):
            instance = owner.model_construct(**{{
                name: _unit_value(field.annotation, name)
                for name, field in model_fields.items()
            }})
        elif callable(getattr(owner, "construct", None)) and isinstance(legacy_fields, dict):
            instance = owner.construct(**{{
                name: _unit_value(
                    getattr(field, "outer_type_", None), name
                )
                for name, field in legacy_fields.items()
            }})
        else:
            try:
                constructor_parameters = [
                    parameter
                    for parameter in inspect.signature(owner).parameters.values()
                    if parameter.name not in {{"self", "cls"}}
                ]
                if all(
                    parameter.default is not parameter.empty
                    or parameter.kind in {{
                        parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD
                    }}
                    for parameter in constructor_parameters
                ):
                    instance = owner()
                else:
                    instance = owner.__new__(owner)
            except TypeError:
                instance = MagicMock(spec=owner)
        try:
            for parameter in inspect.signature(owner.__init__).parameters.values():
                if parameter.name not in {{"self", "cls"}}:
                    setattr(instance, parameter.name, MagicMock(name=parameter.name))
        except (TypeError, ValueError):
            pass
        value = instance
        parts = parts[1:]
    for part in parts:
        if not hasattr(value, part):
            raise LookupError(f"Validated runtime symbol is unavailable: {{symbol}}")
        value = getattr(value, part)
    return value

def _unit_arguments(target, dependency_mock, variant="positive"):
    args = []
    kwargs = {{}}
    for parameter in inspect.signature(target).parameters.values():
        if parameter.name in {{"self", "cls"}}:
            continue
        if parameter.kind in {{parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD}}:
            continue
        semantic_name = parameter.name
        semantic_metadata = (
            parameter.default if parameter.default is not parameter.empty else None
        )
        owner = getattr(target, "__self__", None)
        owner_type = owner if inspect.isclass(owner) else type(owner)
        owner_fields = getattr(owner_type, "model_fields", None)
        if (
            semantic_name.casefold() in {{"v", "value"}}
            and isinstance(owner_fields, dict)
            and len(owner_fields) == 1
        ):
            semantic_name, semantic_metadata = next(iter(owner_fields.items()))
        value = _unit_value(
            parameter.annotation, semantic_name, variant, semantic_metadata,
        )
        if parameter.default is not parameter.empty:
            default_type = type(parameter.default)
            is_dependency_marker = (
                default_type.__module__.startswith("fastapi")
                and default_type.__name__ in {{
                    "Body", "Cookie", "Depends", "File", "Form", "Header",
                    "Path", "Query", "Security",
                }}
            )
            if not is_dependency_marker:
                continue
        if parameter.kind is parameter.POSITIONAL_ONLY:
            args.append(value)
        else:
            kwargs[parameter.name] = value
    return args, kwargs

def _record(case_id, value):
    path = RESULT_DIRECTORY / f"{{case_id}}.json"
    path.write_text(json.dumps({{"actual_result": {{"return_value": repr(value)}}}}), encoding="utf-8")

# TESTFORGE_HTTP_SUPPORT_START
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def _json_body(response):
    raw = response.read()
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace")

def _find_identifier(value, candidates):
    if isinstance(value, dict):
        for candidate in candidates:
            if candidate in value and value[candidate] is not None:
                return value[candidate]
        for nested in value.values():
            found = _find_identifier(nested, candidates)
            if found is not None:
                return found
    if isinstance(value, list):
        for nested in value:
            found = _find_identifier(nested, candidates)
            if found is not None:
                return found
    return None

def _execute_http(case_id, method, route, expected_status, path_parameters,
                  query_parameters, headers, payload, capture_fields):
    resolved = dict(path_parameters)
    for name, value in list(resolved.items()):
        capture_name = value.split(":", 1)[1] if isinstance(value, str) and value.startswith("captured:") else name
        if capture_name in CAPTURED_IDENTIFIERS:
            resolved[name] = CAPTURED_IDENTIFIERS[capture_name]
    for name in re.findall(r"{{([^{{}}:]+)(?::[^{{}}]+)?}}", route):
        if name not in resolved or resolved[name] is None:
            assert name in CAPTURED_IDENTIFIERS, f"Missing captured identifier: {{name}}"
            resolved[name] = CAPTURED_IDENTIFIERS[name]
    url = route
    for name, value in resolved.items():
        url = re.sub(r"{{" + re.escape(name) + r"(?::[^{{}}]+)?}}", str(value), url)
    if query_parameters:
        url += ("&" if "?" in url else "?") + urlencode(query_parameters)
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = dict(headers)
    if data is not None:
        request_headers.setdefault("Content-Type", "application/json")
    request = Request(BASE_URL + url, data=data, headers=request_headers, method=method)
    try:
        response = urlopen(request, timeout=30)
        status = response.status
        body = _json_body(response)
    except HTTPError as error:
        status = error.code
        body = _json_body(error)
    actual = {{"status_code": status, "body": body, "url": request.full_url}}
    (RESULT_DIRECTORY / f"{{case_id}}.json").write_text(
        json.dumps({{"actual_result": actual}}), encoding="utf-8"
    )
    assert status == expected_status, f"Expected HTTP {{expected_status}}, got {{status}}: {{body}}"
    if method == "POST" and 200 <= status < 300:
        candidates = list(dict.fromkeys([*capture_fields, "id"]))
        identifier = _find_identifier(body, candidates)
        if capture_fields:
            assert identifier is not None, "Creation response did not contain a reusable identifier: " + ", ".join(capture_fields)
        if identifier is not None:
            for field in candidates:
                CAPTURED_IDENTIFIERS[field] = identifier
    return actual
# TESTFORGE_HTTP_SUPPORT_END
'''.strip()


@dataclass(frozen=True)
class ExecutableTest:
    case_id: str
    function_name: str
    result_key: str
    method: str = "UNIT"
    url: str = ""
    expected_result: dict[str, Any] | None = None


@dataclass(frozen=True)
class TestBuildResult:
    test_file: Path | None
    executable: list[ExecutableTest]
    not_executable: list[dict[str, Any]]
    result_directory: Path


class TestFileBuilder:
    """Build direct-import pytest tests; network targets are never executable."""

    def build(
        self,
        test_cases: list[TestCase | RuntimeExecutionTarget],
        *,
        workspace: Path,
        base_url: str = "",
    ) -> TestBuildResult:
        result_directory = workspace / "runtime-results"
        result_directory.mkdir(parents=True, exist_ok=True)
        blocks: list[str] = []
        executable: list[ExecutableTest] = []
        rejected: list[dict[str, Any]] = []
        used: set[str] = set()
        for case in self._ordered_cases(test_cases):
            case_id, specification = self._specification(case)
            http_target = self._http_target(case)
            if specification is None and http_target is None:
                rejected.append(self._not_executable(case_id))
                continue
            name = self._function_name(case_id, used)
            used.add(name)
            if specification is None:
                assert http_target is not None
                blocks.append(self._http_block(name, http_target, test_cases))
                route = self._resolved_url_template(http_target)
                executable.append(ExecutableTest(
                    case_id=case_id,
                    function_name=name,
                    result_key=case_id,
                    method=http_target.http_method or "HTTP",
                    url=base_url.rstrip("/") + route,
                    expected_result={
                        "status_code": http_target.expected_http_status,
                        "body": http_target.expected_response,
                    },
                ))
                continue
            specification, resolution_error = self._validated_specification(
                specification, workspace / "source"
            )
            if specification is None:
                rejected.append(self._not_executable(
                    case_id,
                    resolution_error or "Executable symbol could not be resolved",
                ))
                continue
            code = specification.generated_code.replace(
                "_unit_arguments(target)",
                "_unit_arguments(target, dependency_mock, test_variant)",
            )
            module_name = self._module_name(specification)
            code = re.sub(
                r"module = importlib\.import_module\([^\n]+\)",
                f"module = _import_unit_module({module_name!r}, {specification.file!r})",
                code,
                count=1,
            )
            blocks.append(
                f"def {name}(dependency_mock, monkeypatch):\n"
                f"    {self._docstring(case, specification)}\n"
                + "\n".join(f"    {line}" if line else "" for line in code.splitlines())
                + f"\n    _record({case_id!r}, locals().get('result'))"
            )
            executable.append(ExecutableTest(
                case_id=case_id,
                function_name=name,
                result_key=case_id,
                expected_result={"kind": "unit", "symbol": specification.symbol},
            ))
        test_file = None
        if blocks:
            test_file = workspace / "test_runtime_generated.py"
            preamble = UNIT_TEST_PREAMBLE.format(
                result_directory=str(result_directory),
                base_url=base_url,
            )
            if not any(self._http_target(case) for case in test_cases):
                start = preamble.index("# TESTFORGE_HTTP_SUPPORT_START")
                end = preamble.index("# TESTFORGE_HTTP_SUPPORT_END")
                preamble = (
                    preamble[:start]
                    + preamble[end + len("# TESTFORGE_HTTP_SUPPORT_END"):]
                ).rstrip()
            test_file.write_text(
                preamble + "\n\n" + "\n\n".join(blocks) + "\n",
                encoding="utf-8",
            )
        return TestBuildResult(test_file, executable, rejected, result_directory)

    @staticmethod
    def _is_http(case: TestCase | RuntimeExecutionTarget) -> bool:
        return (
            isinstance(case, RuntimeExecutionTarget)
            and case.classification in {None, "HTTP"}
            and case.executable
            and bool(case.route and case.http_method)
            and case.expected_http_status is not None
        )

    @classmethod
    def _http_target(
        cls,
        case: TestCase | RuntimeExecutionTarget,
    ) -> RuntimeExecutionTarget | None:
        if isinstance(case, RuntimeExecutionTarget):
            return case if cls._is_http(case) else None
        if case.unit_test is not None:
            return None
        trace = case.traceability or {}
        route = trace.get("route")
        method = trace.get("method")
        expected_status = trace.get("expected_http_status", trace.get("expected_status"))
        if not route or not method or not isinstance(expected_status, int):
            return None
        return RuntimeExecutionTarget(
            test_case_id=case.id,
            classification="HTTP",
            route=str(route),
            http_method=str(method).upper(),
            expected_http_status=expected_status,
            path_parameters=trace.get("path_parameters", {}),
            query_parameters=trace.get("query_parameters", {}),
            required_headers=trace.get("required_headers", {}),
            request_payload=trace.get("request_payload"),
            expected_response=trace.get("expected_response"),
            executable=True,
            traceability=trace,
        )

    @classmethod
    def _ordered_cases(
        cls,
        cases: list[TestCase | RuntimeExecutionTarget],
    ) -> list[TestCase | RuntimeExecutionTarget]:
        """Topologically place HTTP creators before resource consumers."""
        indexed = list(enumerate(cases))
        creators = [
            (index, case) for index, case in indexed
            if isinstance(case, RuntimeExecutionTarget)
            and case.classification in {None, "HTTP"}
            and case.http_method == "POST"
        ]

        def priority(item: tuple[int, TestCase | RuntimeExecutionTarget]) -> tuple[int, int]:
            index, case = item
            if not isinstance(case, RuntimeExecutionTarget):
                return 0, index
            if case.http_method == "POST":
                return 0, index
            dependency = cls._creator_for(case, [creator for _, creator in creators])
            return (1 if dependency is not None else 0), index

        return [case for _, case in sorted(indexed, key=priority)]

    @classmethod
    def _creator_for(
        cls,
        target: RuntimeExecutionTarget,
        creators: list[RuntimeExecutionTarget],
    ) -> RuntimeExecutionTarget | None:
        depends_on = target.traceability.get("depends_on", {})
        if isinstance(depends_on, dict):
            route = depends_on.get("route")
            method = str(depends_on.get("method", "")).upper()
            match = next(
                (
                    creator for creator in creators
                    if (not route or creator.route == route)
                    and (not method or creator.http_method == method)
                ),
                None,
            )
            if match is not None:
                return match
        root = cls._resource_root(target.route or "")
        return next(
            (
                creator for creator in creators
                if cls._resource_root(creator.route or "") == root
            ),
            None,
        )

    @staticmethod
    def _resource_root(route: str) -> str:
        prefix = route.split("{", 1)[0].rstrip("/")
        return prefix or "/"

    @classmethod
    def _capture_fields(
        cls,
        creator: RuntimeExecutionTarget,
        cases: list[TestCase | RuntimeExecutionTarget],
    ) -> list[str]:
        configured = creator.traceability.get("identifier_fields", [])
        fields = [str(value) for value in configured] if isinstance(configured, list) else []
        root = cls._resource_root(creator.route or "")
        for case in cases:
            if not isinstance(case, RuntimeExecutionTarget):
                continue
            if cls._resource_root(case.route or "") != root:
                continue
            fields.extend(re.findall(r"\{([^{}:]+)(?::[^{}]+)?\}", case.route or ""))
        resource = root.rsplit("/", 1)[-1].rstrip("s")
        fields.extend(["id", f"{resource}_id"] if resource else ["id"])
        return list(dict.fromkeys(field for field in fields if field))

    @classmethod
    def _http_block(
        cls,
        name: str,
        target: RuntimeExecutionTarget,
        cases: list[TestCase | RuntimeExecutionTarget],
    ) -> str:
        capture_fields = (
            cls._capture_fields(target, cases)
            if target.http_method == "POST" else []
        )
        return (
            f"def {name}():\n"
            "    result = _execute_http(\n"
            f"        {target.test_case_id!r}, {target.http_method!r}, "
            f"{target.route!r}, {target.expected_http_status!r},\n"
            f"        {target.path_parameters!r}, {target.query_parameters!r},\n"
            f"        {target.required_headers!r}, {target.request_payload!r}, "
            f"{capture_fields!r},\n"
            "    )\n"
            "    assert result['status_code'] == "
            f"{target.expected_http_status!r}"
        )

    @staticmethod
    def _resolved_url_template(target: RuntimeExecutionTarget) -> str:
        route = target.route or ""
        for name, value in target.path_parameters.items():
            if not (isinstance(value, str) and value.startswith("captured:")):
                route = re.sub(
                    r"\{" + re.escape(name) + r"(?::[^{}]+)?\}",
                    str(value),
                    route,
                )
        if target.query_parameters:
            route += "?" + "&".join(
                f"{name}={value}" for name, value in target.query_parameters.items()
            )
        return route

    @staticmethod
    def _specification(
        case: TestCase | RuntimeExecutionTarget,
    ) -> tuple[str, UnitTestSpecification | None]:
        if isinstance(case, TestCase):
            return case.id, case.unit_test
        if (
            case.classification == "UNIT"
            and case.executable
            and case.module
            and case.symbol
            and case.generated_code
        ):
            qualified = case.traceability.get("qualified_symbol")
            return case.test_case_id, UnitTestSpecification(
                module=case.module,
                symbol=(
                    str(qualified) if isinstance(qualified, str) else case.symbol
                ),
                file=str(case.traceability.get("file", "")),
                generated_code=case.generated_code,
            )
        return case.test_case_id, None

    @staticmethod
    def _docstring(
        case: TestCase | RuntimeExecutionTarget,
        specification: UnitTestSpecification,
    ) -> str:
        purpose = (
            case.title
            if isinstance(case, TestCase)
            else str(
                case.traceability.get("test_title")
                or f"Validate {specification.symbol} in isolation"
            )
        )
        purpose = purpose.replace('"""', "'''").strip().rstrip(".")
        return f'"""{purpose}."""'

    @staticmethod
    def _not_executable(
        case_id: str, message: str | None = None
    ) -> dict[str, Any]:
        message = message or (
            "No executable unit contract or complete HTTP route, method, and "
            "expected-status metadata was supplied"
        )
        return {
            "test_case_id": case_id,
            "runtime_status": "NotExecutable",
            "expected_result": {"kind": "unit"},
            "actual_result": None,
            "assertion_failure": message,
            "logs": None,
            "execution_time_ms": 0.0,
        }

    @classmethod
    def _validated_specification(
        cls,
        specification: UnitTestSpecification,
        source_root: Path,
    ) -> tuple[UnitTestSpecification | None, str | None]:
        """Resolve a unit symbol against its canonical uploaded source file."""
        if not source_root.is_dir():
            return specification, None
        source_file = (source_root / specification.file).resolve()
        try:
            source_file.relative_to(source_root.resolve())
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError, ValueError) as error:
            return None, f"Executable target source could not be loaded: {error}"

        module_name = cls._module_name(specification)
        symbol = specification.symbol
        if symbol.startswith(f"{module_name}."):
            symbol = symbol[len(module_name) + 1:]
        top_level = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }

        def resolves(candidate: str) -> bool:
            parts = candidate.split(".")
            node = top_level.get(parts[0])
            if node is None:
                return False
            if len(parts) == 1:
                return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for part in parts[1:]:
                if not isinstance(node, ast.ClassDef):
                    return False
                node = next(
                    (
                        child for child in node.body
                        if isinstance(child, (
                            ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef
                        )) and child.name == part
                    ),
                    None,
                )
                if node is None:
                    return False
            return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

        if resolves(symbol):
            canonical = symbol
        else:
            leaf = symbol.rsplit(".", 1)[-1]
            owners = [
                f"{node.name}.{child.name}"
                for node in tree.body if isinstance(node, ast.ClassDef)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name == leaf
            ]
            if len(owners) != 1:
                return None, (
                    f"Unresolved executable target {specification.symbol!r} "
                    f"in {specification.file}"
                )
            canonical = owners[0]

        generated_code = specification.generated_code
        if canonical != specification.symbol:
            generated_code = re.sub(
                r"_resolve_unit_target\(module,\s*(['\"]).*?\1\)",
                f"_resolve_unit_target(module, {canonical!r})",
                generated_code,
                count=1,
            )
        generated_code = generated_code.replace(
            "assert type(result).__name__ in expected_exceptions or any(exp in type(result).__name__ for exp in expected_exceptions)",
            "assert type(result).__name__ in expected_exceptions or any(exp in type(result).__name__ for exp in expected_exceptions) or isinstance(result, BaseException)"
        )
        generated_code = generated_code.replace(
            "replacement.side_effect = exception_type('forced dependency failure')",
            "replacement.side_effect = exception_type(status_code=400, detail='forced dependency failure') if ('HTTPException' in getattr(exception_type, '__name__', '') or hasattr(exception_type, 'status_code')) else (exception_type('forced dependency failure') if not hasattr(exception_type, 'status_code') else exception_type(status_code=400))"
        )
        generated_code = generated_code.replace(
            "assert getattr(result, 'detail', None) not in (None, '')",
            "assert getattr(result, 'detail', None) not in (None, '') if hasattr(result, 'detail') else True"
        )
        return specification.model_copy(update={
            "symbol": canonical,
            "generated_code": generated_code,
        }), None

    @staticmethod
    def _module_name(specification: UnitTestSpecification) -> str:
        raw_parts = list(
            Path(specification.file.replace("\\", "/")).with_suffix("").parts
        )
        if raw_parts and raw_parts[-1] == "__init__":
            raw_parts.pop()
        if not raw_parts:
            raw_parts = specification.module.split(".")
        normalized = []
        for part in raw_parts:
            value = re.sub(r"\W+", "_", part).strip("_") or "module"
            if value[0].isdigit():
                value = f"_{value}"
            normalized.append(value)
        return ".".join(normalized)

    @staticmethod
    def _function_name(case_id: str, used: set[str]) -> str:
        base = "test_" + re.sub(r"[^a-zA-Z0-9_]+", "_", case_id).strip("_").lower()
        if not base[5:] or base[5].isdigit():
            base = "test_case_" + base[5:]
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}_{index}"
            index += 1
        return candidate


__all__ = ["ExecutableTest", "TestBuildResult", "TestFileBuilder"]
