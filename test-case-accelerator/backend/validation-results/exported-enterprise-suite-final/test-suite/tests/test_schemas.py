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

RESULT_DIRECTORY = Path('.testforge-results')
BASE_URL = ''.rstrip("/")
CAPTURED_IDENTIFIERS = {}
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
        + json.dumps({
            "phase": "before_import",
            "cwd": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "sys_path": list(sys.path),
            "module": module_name,
            "module_file": None,
            "app_file": getattr(app_module, "__file__", None),
        }, default=str),
        flush=True,
    )

def _import_unit_module(module_name, source_file):
    _prepare_import_environment(module_name)
    source_path = (PROJECT_ROOT / source_file).resolve()
    if not _inside_project(source_path):
        raise ImportError(f"Runtime target escapes uploaded project: {source_file}")
    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
        module_name,
    ):
        raise ImportError(f"Invalid sanitized runtime module path: {module_name}")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        spec = importlib.util.spec_from_file_location(module_name, source_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load runtime target: {source_file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    module_file = getattr(module, "__file__", None)
    if not module_file or not _inside_project(module_file):
        raise ImportError(
            f"Runtime module resolved outside uploaded project: {module_name} -> {module_file}"
        )
    app_module = sys.modules.get("app")
    app_file = getattr(app_module, "__file__", None)
    if app_file and not _inside_project(app_file):
        raise ImportError(f"Shadowed app package resolved outside uploaded project: {app_file}")
    print(
        "TESTFORGE_IMPORT_DIAGNOSTIC "
        + json.dumps({
            "phase": "after_import",
            "cwd": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "sys_path": list(sys.path),
            "module": module_name,
            "module_file": module_file,
            "app_file": app_file,
        }, default=str),
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

def _unit_value(annotation, name, variant="positive", metadata=None):
    origin = get_origin(annotation)
    arguments = [item for item in get_args(annotation) if item is not type(None)]
    if origin is not None and arguments:
        annotation = origin if origin in {list, dict, set, tuple} else arguments[0]
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
    elif any(token in lowered for token in ("encoded", "hash", "digest")):
        string_value = "invalid" if negative else "00:" + "00" * 32
    elif any(token in lowered for token in ("password", "secret")):
        string_value = "" if negative else "ValidPass123!"
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
    values = {
        str: string_value,
        int: int(numeric_value),
        float: float(numeric_value),
        bool: not negative,
        bytes: string_value.encode("utf-8"),
        date: date.today(),
        datetime: datetime.now(),
        UUID: UUID(int=1),
        list: [],
        dict: {},
        set: set(),
        tuple: (),
    }
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
        payload = {
            field_name: _unit_value(
                field.annotation, field_name, variant, field
            )
            for field_name, field in model_fields.items()
            if getattr(field, "is_required", lambda: True)()
        }
        if negative and callable(getattr(annotation, "model_construct", None)):
            return annotation.model_construct(**payload)
        try:
            return annotation(**payload)
        except Exception:
            if callable(getattr(annotation, "model_construct", None)):
                return annotation.model_construct(**payload)
    if annotation_name in {"str", "string"}:
        return string_value
    if annotation_name in {"int", "integer"}:
        return int(numeric_value)
    if annotation_name in {"float", "number"}:
        return float(numeric_value)
    if annotation_name in {"bool", "boolean"}:
        return not negative
    if any(token in lowered for token in (
        "email", "phone", "mobile", "telephone", "url", "uri", "website",
        "password", "secret", "username", "user_name", "login", "name",
    )):
        return string_value
    return values.get(annotation, MagicMock(name=name))

def _resolve_unit_target(module, symbol):
    parts = symbol.split(".")
    value = module
    if not parts or not hasattr(module, parts[0]):
        raise LookupError(
            f"Validated runtime symbol is unavailable: {module.__name__}.{symbol}"
        )
    if len(parts) > 1:
        owner = getattr(module, parts[0])
        if not hasattr(owner, parts[1]):
            raise LookupError(
                f"Validated owner method is unavailable: {symbol}"
            )
        model_fields = getattr(owner, "model_fields", None)
        legacy_fields = getattr(owner, "__fields__", None)
        if callable(getattr(owner, "model_construct", None)) and isinstance(model_fields, dict):
            instance = owner.model_construct(**{
                name: _unit_value(field.annotation, name)
                for name, field in model_fields.items()
            })
        elif callable(getattr(owner, "construct", None)) and isinstance(legacy_fields, dict):
            instance = owner.construct(**{
                name: _unit_value(
                    getattr(field, "outer_type_", None), name
                )
                for name, field in legacy_fields.items()
            })
        else:
            try:
                constructor_parameters = [
                    parameter
                    for parameter in inspect.signature(owner).parameters.values()
                    if parameter.name not in {"self", "cls"}
                ]
                if all(
                    parameter.default is not parameter.empty
                    or parameter.kind in {
                        parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD
                    }
                    for parameter in constructor_parameters
                ):
                    instance = owner()
                else:
                    instance = owner.__new__(owner)
            except TypeError:
                instance = MagicMock(spec=owner)
        try:
            for parameter in inspect.signature(owner.__init__).parameters.values():
                if parameter.name not in {"self", "cls"}:
                    setattr(instance, parameter.name, MagicMock(name=parameter.name))
        except (TypeError, ValueError):
            pass
        value = instance
        parts = parts[1:]
    for part in parts:
        if not hasattr(value, part):
            raise LookupError(f"Validated runtime symbol is unavailable: {symbol}")
        value = getattr(value, part)
    return value

def _unit_arguments(target, dependency_mock, variant="positive"):
    args = []
    kwargs = {}
    for parameter in inspect.signature(target).parameters.values():
        if parameter.name in {"self", "cls"}:
            continue
        if parameter.kind in {parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD}:
            continue
        semantic_name = parameter.name
        semantic_metadata = (
            parameter.default if parameter.default is not parameter.empty else None
        )
        owner = getattr(target, "__self__", None)
        owner_type = owner if inspect.isclass(owner) else type(owner)
        owner_fields = getattr(owner_type, "model_fields", None)
        if (
            semantic_name.casefold() in {"v", "value"}
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
                and default_type.__name__ in {
                    "Body", "Cookie", "Depends", "File", "Form", "Header",
                    "Path", "Query", "Security",
                }
            )
            if not is_dependency_marker:
                continue
        if parameter.kind is parameter.POSITIONAL_ONLY:
            args.append(value)
        else:
            kwargs[parameter.name] = value
    return args, kwargs

def _record(case_id, value):
    path = RESULT_DIRECTORY / f"{case_id}.json"
    path.write_text(json.dumps({"actual_result": {"return_value": repr(value)}}), encoding="utf-8")

def test_ut_app_schemas_usercreate_normalize_email(dependency_mock, monkeypatch):
    import asyncio
    import builtins
    import hashlib
    import importlib
    import inspect
    from contextlib import ExitStack
    from unittest.mock import AsyncMock, MagicMock, patch
    module = _import_unit_module('app.schemas', 'app/schemas.py')
    dependencies = ['lower']
    test_variant = 'positive'
    expected_exceptions = []
    semantic_assertions = {'authentication': False, 'boolean': False, 'collection': False, 'crud': False, 'exception_details': False, 'interaction_dependencies': [], 'validation': False, 'expectations': ['The declared collaborator interaction is invoked']}
    if any((any((token in dependency.casefold() for token in ('env', 'environ', 'settings', 'config'))) for dependency in dependencies)):
        monkeypatch.setenv('TESTFORGE_UNIT_TEST', '1')
    patches = ExitStack()
    dependency_mocks = {}
    for dependency in dependencies:
        name = dependency.rsplit('.', 1)[-1]
        if not hasattr(module, name):
            name = dependency.split('.', 1)[0]
        if hasattr(module, name):
            original = getattr(module, name)
            if inspect.isclass(original) and issubclass(original, BaseException):
                continue
            replacement = AsyncMock(name=name) if inspect.iscoroutinefunction(original) else MagicMock(name=name)
            if any((token in name.casefold() for token in ('hash', 'encode', 'digest'))):
                replacement.return_value = '00:' + '00' * 32
            elif any((token in name.casefold() for token in ('issue', 'pair', 'rotate'))):
                replacement.return_value = (MagicMock(name=f'{name}_first'), MagicMock(name=f'{name}_second'))
            else:
                replacement.return_value.__iter__.return_value = [MagicMock(name=f'{name}_first'), MagicMock(name=f'{name}_second')]
            if test_variant == 'exception' and expected_exceptions:
                exception_type = getattr(module, expected_exceptions[0], None)
                exception_type = exception_type or getattr(builtins, expected_exceptions[0], None)
                if isinstance(exception_type, type) and issubclass(exception_type, BaseException):
                    try:
                        replacement.side_effect = exception_type('forced dependency failure')
                    except TypeError:
                        replacement.side_effect = exception_type()
            dependency_mocks[dependency] = replacement
            patches.enter_context(patch.object(module, name, replacement))
    target = _resolve_unit_target(module, 'UserCreate.normalize_email')
    owner = getattr(target, '__self__', None)
    repository = getattr(owner, 'repository', None)
    if isinstance(repository, MagicMock):
        entity = MagicMock(name='repository_entity')
        entity.id = 1
        entity.is_active = True
        entity.hashed_password = hashlib.sha256(b'ValidPass123!').hexdigest()
        repository.get_by_email.return_value = None if target.__name__.startswith('create_') else entity
        repository.get_by_id.return_value = entity
        repository.add.side_effect = lambda value: value
        repository.search.return_value = []
    args, kwargs = _unit_arguments(target, dependency_mock, test_variant)
    for dependency in dependencies:
        parameter_name = dependency.split('.', 1)[0]
        parameter_mock = kwargs.get(parameter_name)
        if isinstance(parameter_mock, MagicMock):
            dependency_mocks.setdefault(dependency, parameter_mock)
    bound = inspect.signature(target).bind(*args, **kwargs)
    with patches:
        try:
            result = target(*args, **kwargs)
            if inspect.isawaitable(result):
                result = asyncio.run(result)
            if inspect.isgenerator(result):
                result = list(result)
        except Exception as error:
            if type(error).__name__ not in expected_exceptions:
                raise
            result = error
    assert callable(target)
    assert set(bound.arguments).issubset(inspect.signature(target).parameters)
    if isinstance(result, BaseException):
        assert type(result).__name__ in expected_exceptions
        assert str(result), 'Expected exception must carry a diagnostic message'
        if semantic_assertions['exception_details'] or (hasattr(result, 'status_code') and hasattr(result, 'detail')):
            assert isinstance(result.status_code, int)
            assert result.detail not in (None, '')
            if result.headers is not None:
                assert isinstance(result.headers, dict)
        else:
            assert result.args and result.args[0] == str(result)
    else:
        assert not isinstance(result, BaseException)
        return_annotation = inspect.signature(target).return_annotation
        if not isinstance(result, (MagicMock, AsyncMock)) and return_annotation is not inspect.Signature.empty and isinstance(return_annotation, type) and (return_annotation is not type(None)):
            assert isinstance(result, return_annotation)
        if semantic_assertions['boolean']:
            expected_boolean = True if semantic_assertions['crud'] else test_variant != 'negative'
            assert result is expected_boolean
        if semantic_assertions['collection'] and (not isinstance(result, (MagicMock, AsyncMock))):
            assert isinstance(result, (dict, list, set, tuple))
    for dependency, mock in dependency_mocks.items():
        assert isinstance(mock, (MagicMock, AsyncMock)), dependency
    interaction_mocks = [dependency_mocks[name] for name in semantic_assertions['interaction_dependencies'] if name in dependency_mocks]
    if interaction_mocks and (not isinstance(result, BaseException)):
        assert any((mock.mock_calls for mock in interaction_mocks)), 'Expected the semantic collaborator interaction to occur'
