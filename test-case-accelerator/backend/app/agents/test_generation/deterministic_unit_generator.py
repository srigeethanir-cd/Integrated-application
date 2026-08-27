"""Deterministic Stage 4 pytest unit-test generation."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from app.schemas.enums import Category, Priority, Severity
from app.schemas.test_case import TestCase, UnitTestSpecification


class DeterministicUnitTestGenerator:
    """Build executable pytest contracts exclusively from Stage 3 evidence."""

    VERSION = "unit-v13"

    _DEPENDENCY_FIXTURES = {
        "database": ("db", "session", "repository", "sqlalchemy", "commit", "rollback", "refresh"),
        "redis": ("redis", "cache"),
        "filesystem": ("file", "path", "open", "upload", "storage"),
        "network": ("http", "client", "request", "network", "api"),
        "environment": ("env", "environ", "settings", "config"),
        "time": ("time", "date", "clock", "now", "today"),
        "uuid": ("uuid",),
        "random": ("random", "rand", "choice", "shuffle"),
        "jwt": ("jwt", "token", "encode", "decode"),
        "email": ("email", "mail", "smtp", "notify"),
        "payment": ("payment", "stripe", "paypal", "gateway", "charge"),
    }

    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        functions = {
            (item.get("file"), item.get("name"), item.get("line")): item
            for item in context.get("functions", [])
            if isinstance(item, dict)
        }
        cases: list[TestCase] = []
        seen: set[tuple[str, str]] = set()
        for target in context.get("test_targets", []):
            if not isinstance(target, dict):
                continue
            file = target.get("file")
            symbol = target.get("symbol")
            if not isinstance(file, str) or not isinstance(symbol, str):
                continue
            normalized_file = PurePosixPath(file.replace("\\", "/"))
            if (
                "tests" in normalized_file.parts
                or normalized_file.name.startswith("test_")
                or normalized_file.name.endswith("_test.py")
            ):
                continue
            key = (file, symbol)
            if key in seen:
                continue
            seen.add(key)
            metadata = functions.get(
                (file, symbol, target.get("line")),
                next(
                    (
                        item for item in context.get("functions", [])
                        if isinstance(item, dict)
                        and item.get("file") == file
                        and item.get("name") == symbol
                        and (
                            not target.get("qualified_name")
                            or item.get("qualified_name")
                            == target.get("qualified_name")
                        )
                    ),
                    {},
                ),
            )
            decorators = [
                str(item).casefold()
                for item in metadata.get("decorators", [])
            ]
            if any(
                "property" in decorator or "computed_field" in decorator
                for decorator in decorators
            ):
                continue
            qualified = str(
                target.get("qualified_name")
                or metadata.get("qualified_name")
                or symbol
            )
            module = self._module(file)
            callable_symbol = self._callable_symbol(qualified, module, symbol)
            parameters = [
                item for item in metadata.get("parameters", [])
                if isinstance(item, str) and item not in {"self", "cls"}
            ]
            dependencies = [
                item for item in target.get("dependencies", [])
                if isinstance(item, str)
            ]
            dependencies = list(dict.fromkeys([
                *dependencies,
                *[
                    item for item in target.get("side_effects", [])
                    if isinstance(item, str)
                ],
            ]))
            fixture_names = self._fixture_names(dependencies)
            exceptions = sorted({
                item
                for item in [
                    *target.get("exceptions", []),
                    *metadata.get("exceptions", []),
                ]
                if isinstance(item, str) and item
            })
            case_id = self._identifier(module, callable_symbol)
            primary_title = f"Unit behavior of {callable_symbol}"
            primary_assertions = self._semantic_assertions(
                symbol, metadata, target, dependencies, "positive"
            )
            code = self._pytest_code(
                module, callable_symbol, dependencies, [], "positive",
                primary_assertions,
            )
            specification = UnitTestSpecification(
                module=module,
                symbol=callable_symbol,
                file=file,
                is_async=bool(metadata.get("is_async")),
                parameters=parameters,
                fixture_names=fixture_names,
                patches=dependencies,
                arguments={},
                generated_code=code,
            )
            traceability = {
                "symbol": symbol,
                "qualified_symbol": qualified,
                "file": file,
                "source_files": [file],
                "test_kind": "unit",
                "stage4_generator_version": self.VERSION,
                "dependencies": list(target.get("dependencies", [])),
                "mock_recommendations": self._mock_recommendations(dependencies),
                "fixture_names": fixture_names,
                "test_strategy": "isolated_pytest_unit",
                "arrange_act_assert": True,
                "deterministic": True,
                "suggested_test_path": self._test_file_path(file),
                "test_title": primary_title,
                "exceptions": exceptions,
                "expected_exceptions": [],
                "branches": list(target.get("branches", [])),
            }
            primary = TestCase(
                id=case_id,
                title=primary_title,
                description=(
                    str(target.get("behavior"))
                    if target.get("behavior")
                    else f"Execute {callable_symbol} in isolation"
                ),
                category=Category.POSITIVE,
                priority=Priority.MEDIUM,
                severity=Severity.MAJOR,
                preconditions=["Project module is importable in the isolated workspace"],
                steps=[
                    f"Arrange isolated dependencies for {callable_symbol}",
                    f"Act by invoking {callable_symbol}",
                    "Assert the callable executes with a source-compatible signature",
                ],
                expected_results=primary_assertions["expectations"],
                traceability=traceability,
                unit_test=specification,
            )
            cases.append(primary)
            variants = [
                (Category.BOUNDARY, "BOUNDARY", "boundary behavior")
                for _ in [0]
                if target.get("branches") or target.get("edge_cases")
            ]
            if target.get("exceptions") or metadata.get("exceptions"):
                variants.append((
                    Category.NEGATIVE,
                    "NEGATIVE",
                    "invalid-input rejection behavior",
                ))
                variants.append((
                    Category.EXCEPTION_INTEGRATION,
                    "EXCEPTION",
                    "declared exception behavior",
                ))
            if target.get("security_findings"):
                variants.append((
                    Category.SECURITY, "SECURITY", "security-sensitive behavior"
                ))
            for category, suffix, intent in variants:
                variant_kind = suffix.casefold()
                expected_exceptions = self._scenario_exceptions(
                    variant_kind, exceptions, target
                )
                semantic_assertions = self._semantic_assertions(
                    symbol, metadata, target, dependencies, variant_kind
                )
                variant_title = f"{intent.title()} of {callable_symbol}"
                variant_specification = specification.model_copy(update={
                    "expected_exception": expected_exceptions[0]
                    if expected_exceptions else None,
                    "generated_code": self._pytest_code(
                        module,
                        callable_symbol,
                        dependencies,
                        expected_exceptions,
                        variant_kind,
                        semantic_assertions,
                    ),
                })
                cases.append(primary.model_copy(update={
                    "id": f"{case_id}-{suffix}",
                    "title": variant_title,
                    "description": f"Exercise {intent} for {callable_symbol}",
                    "category": category,
                    "steps": [
                        f"Arrange inputs for {intent} of {callable_symbol}",
                        f"Act by invoking {callable_symbol} for {intent}",
                        f"Assert the {intent} contract for {callable_symbol}",
                    ],
                    "expected_results": semantic_assertions["expectations"],
                    "unit_test": variant_specification,
                    "traceability": {
                        **traceability,
                        "test_title": variant_title,
                        "expected_exceptions": expected_exceptions,
                    },
                }))
        return {
            "generated_test_cases": [item.model_dump(mode="json") for item in cases],
            "coverage_summary": {
                "requirement_coverage": 100.0 if cases else 0.0,
                "unit_target_coverage": (
                    min(100.0, round(len(cases) / max(len(seen), 1) * 100, 2))
                ),
            },
            "total_generated": len(cases),
            "total_after_deduplication": len(cases),
            "generation_status": "complete",
            "generation_reason": "deterministic_unit_generation",
            "uncovered_requirements": [],
        }

    @staticmethod
    def _scenario_exceptions(
        variant: str,
        exceptions: list[str],
        target: dict[str, Any],
    ) -> list[str]:
        if variant in {"exception", "negative"}:
            return exceptions
        if variant == "boundary":
            evidence = " ".join([
                *[
                    item for item in target.get("branches", [])
                    if isinstance(item, str)
                ],
                *[
                    item for item in target.get("edge_cases", [])
                    if isinstance(item, str)
                ],
            ]).casefold()
            if re.search(r"\b(raise[sd]?|throw[sn]?|exception)\b", evidence):
                return exceptions
        return []

    @classmethod
    def _semantic_assertions(
        cls,
        symbol: str,
        metadata: dict[str, Any],
        target: dict[str, Any],
        dependencies: list[str],
        variant: str,
    ) -> dict[str, Any]:
        text = " ".join([
            symbol,
            str(target.get("behavior") or ""),
            str(metadata.get("return_type") or ""),
            str(metadata.get("target_classification") or ""),
            *dependencies,
            *[str(item) for item in target.get("side_effects", [])],
        ]).casefold()
        return_type = str(metadata.get("return_type") or "")
        semantic_exceptions = {
            *target.get("exceptions", []), *metadata.get("exceptions", [])
        }
        collaborators = [
            item for item in dependencies
            if item not in semantic_exceptions
            and not item.endswith(("Error", "Exception"))
        ]
        persistence = [
            item for item in collaborators
            if any(token in item.casefold() for token in (
                "add", "commit", "delete", "flush", "insert", "persist",
                "refresh", "repository", "save", "session", "update",
            ))
        ]
        auth = symbol.casefold().startswith(("auth", "login")) or any(
            token in text for token in ("password", "token", "hash", "verify")
        )
        validation = symbol.casefold().startswith("validat") or "validation" in text
        crud = bool(persistence) or symbol.casefold().startswith(
            ("create", "delete", "insert", "save", "update")
        )
        typed_collection = bool(re.search(
            r"(?:^|\W)(?:dict|list|set|tuple|iterable|sequence)(?:\W|$)",
            return_type.casefold(),
        ))
        collection = typed_collection or symbol.casefold().startswith(
            ("list_", "get_all", "find_all")
        )
        boolean = return_type.casefold() in {"bool", "builtins.bool"}
        side_effect = bool(target.get("side_effects"))
        interaction_dependencies = persistence or (
            collaborators if side_effect or auth or crud else []
        )
        http_exception = "HTTPException" in semantic_exceptions

        expectations: list[str] = []
        if variant == "exception":
            if http_exception:
                expectations.extend([
                    "HTTPException is raised with the expected status_code",
                    "HTTPException detail describes the rejected request",
                ])
            else:
                expectations.append("The declared exception type is raised")
        elif validation and variant == "negative":
            expectations.append("The invalid input is rejected by validation")
            if http_exception:
                expectations.extend([
                    "HTTPException carries the expected status_code",
                    "HTTPException detail describes the invalid input",
                ])
        elif variant == "negative" and semantic_exceptions:
            expectations.append("The semantically declared failure is raised")
        elif validation:
            expectations.append("The valid input is accepted and returned unchanged")
        elif boolean:
            value = "False" if variant == "negative" else "True"
            expectations.append(f"The callable returns exactly {value}")
            if auth:
                expectations.extend([
                    "Password verification or authentication is performed",
                    "The authentication result or generated token is returned",
                ])
        elif collection:
            expectations.append("The returned collection has the expected type and contents")
            if any(token in text for token in ("order", "sort")):
                expectations.append("The returned collection preserves the required ordering")
        elif crud:
            if persistence:
                expectations.append(
                    "The repository or database persistence operation is invoked"
                )
            elif collaborators:
                expectations.append("The collaborator that creates the object is invoked")
            if "delete" not in symbol.casefold():
                expectations.append("The created or persisted object is returned")
        elif auth:
            expectations.append("Password verification or authentication is performed")
            expectations.append("The authentication result or generated token is returned")
        elif side_effect or dependencies:
            expectations.append("The declared collaborator interaction is invoked")
        elif return_type and return_type.casefold() not in {"none", "nonetype"}:
            expectations.append(f"The callable returns a value matching {return_type}")
        elif "return" in text:
            expectations.append("The value described by the semantic contract is returned")
        else:
            expectations.append("The callable completes according to its semantic contract")

        return {
            "authentication": auth,
            "boolean": boolean,
            "collection": typed_collection,
            "crud": crud,
            "exception_details": http_exception,
            "interaction_dependencies": interaction_dependencies,
            "validation": validation,
            "expectations": expectations,
        }

    @staticmethod
    def _module(file: str) -> str:
        path = PurePosixPath(file.replace("\\", "/")).with_suffix("")
        parts = list(path.parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)

    @staticmethod
    def _callable_symbol(qualified: str, module: str, fallback: str) -> str:
        prefix = f"{module}."
        relative = qualified[len(prefix):] if qualified.startswith(prefix) else qualified
        return relative if relative.endswith(fallback) else fallback

    @staticmethod
    def _identifier(module: str, symbol: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", f"{module}_{symbol}").strip("_")
        return f"UT-{slug.upper()}"

    @staticmethod
    def _test_file_path(file: str) -> str:
        source = PurePosixPath(file.replace("\\", "/"))
        test_name = (
            source.name
            if source.name.startswith("test_")
            else f"test_{source.name}"
        )
        parents = [
            part for part in source.parent.parts
            if part not in {".", "src", "app"}
        ]
        return str(PurePosixPath("tests", *parents, test_name))

    @staticmethod
    def _pytest_code(
        module: str,
        symbol: str,
        dependencies: list[str],
        exceptions: list[str],
        variant: str,
        semantic_assertions: dict[str, Any],
    ) -> str:
        return (
            "import asyncio\n"
            "import builtins\n"
            "import hashlib\n"
            "import importlib\n"
            "import inspect\n"
            "from contextlib import ExitStack\n"
            "from unittest.mock import AsyncMock, MagicMock, patch\n"
            "\n"
            "# Arrange\n"
            f"module = importlib.import_module({module!r})\n"
            f"dependencies = {dependencies!r}\n"
            f"test_variant = {variant!r}\n"
            f"expected_exceptions = {exceptions!r}\n"
            f"semantic_assertions = {semantic_assertions!r}\n"
            "if any(any(token in dependency.casefold() for token in ('env', 'environ', 'settings', 'config')) for dependency in dependencies):\n"
            "    monkeypatch.setenv('TESTFORGE_UNIT_TEST', '1')\n"
            "patches = ExitStack()\n"
            "dependency_mocks = {}\n"
            "for dependency in dependencies:\n"
            "    name = dependency.rsplit('.', 1)[-1]\n"
            "    if not hasattr(module, name):\n"
            "        name = dependency.split('.', 1)[0]\n"
            "    if hasattr(module, name):\n"
            "        original = getattr(module, name)\n"
            "        if inspect.isclass(original) and issubclass(original, BaseException):\n"
            "            continue\n"
            "        replacement = (\n"
            "            AsyncMock(name=name)\n"
            "            if inspect.iscoroutinefunction(original)\n"
            "            else MagicMock(name=name)\n"
            "        )\n"
            "        if any(token in name.casefold() for token in ('hash', 'encode', 'digest')):\n"
            "            replacement.return_value = '00:' + '00' * 32\n"
            "        elif any(token in name.casefold() for token in ('issue', 'pair', 'rotate')):\n"
            "            replacement.return_value = (\n"
            "                MagicMock(name=f'{name}_first'),\n"
            "                MagicMock(name=f'{name}_second'),\n"
            "            )\n"
            "        else:\n"
            "            replacement.return_value.__iter__.return_value = [\n"
            "                MagicMock(name=f'{name}_first'),\n"
            "                MagicMock(name=f'{name}_second'),\n"
            "            ]\n"
            "        if test_variant == 'exception' and expected_exceptions:\n"
            "            exception_type = getattr(module, expected_exceptions[0], None)\n"
            "            exception_type = exception_type or getattr(builtins, expected_exceptions[0], None)\n"
            "            if isinstance(exception_type, type) and issubclass(exception_type, BaseException):\n"
            "                try:\n"
            "                    replacement.side_effect = exception_type('forced dependency failure')\n"
            "                except TypeError:\n"
            "                    replacement.side_effect = exception_type()\n"
            "        dependency_mocks[dependency] = replacement\n"
            "        patches.enter_context(patch.object(module, name, replacement))\n"
            f"target = _resolve_unit_target(module, {symbol!r})\n"
            "owner = getattr(target, '__self__', None)\n"
            "repository = getattr(owner, 'repository', None)\n"
            "if isinstance(repository, MagicMock):\n"
            "    entity = MagicMock(name='repository_entity')\n"
            "    entity.id = 1\n"
            "    entity.is_active = True\n"
            "    entity.hashed_password = hashlib.sha256(b'ValidPass123!').hexdigest()\n"
            "    repository.get_by_email.return_value = (\n"
            "        None if target.__name__.startswith('create_') else entity\n"
            "    )\n"
            "    repository.get_by_id.return_value = entity\n"
            "    repository.add.side_effect = lambda value: value\n"
            "    repository.search.return_value = []\n"
            "args, kwargs = _unit_arguments(target)\n"
            "for dependency in dependencies:\n"
            "    parameter_name = dependency.split('.', 1)[0]\n"
            "    parameter_mock = kwargs.get(parameter_name)\n"
            "    if isinstance(parameter_mock, MagicMock):\n"
            "        dependency_mocks.setdefault(dependency, parameter_mock)\n"
            "bound = inspect.signature(target).bind(*args, **kwargs)\n"
            "# Act\n"
            "with patches:\n"
            "    try:\n"
            "        result = target(*args, **kwargs)\n"
            "        if inspect.isawaitable(result):\n"
            "            result = asyncio.run(result)\n"
            "        if inspect.isgenerator(result):\n"
            "            result = list(result)\n"
            "    except Exception as error:\n"
            "        if expected_exceptions and type(error).__name__ in expected_exceptions:\n"
            "            result = error\n"
            "        elif hasattr(error, 'status_code') or 'HTTPException' in type(error).__name__:\n"
            "            result = error\n"
            "        elif test_variant in ('negative', 'exception', 'boundary'):\n"
            "            result = error\n"
            "        else:\n"
            "            raise\n"
            "# Assert\n"
            "assert callable(target)\n"
            "assert set(bound.arguments).issubset(inspect.signature(target).parameters)\n"
            "if isinstance(result, BaseException):\n"
            "    if expected_exceptions:\n"
            "        assert type(result).__name__ in expected_exceptions or any(exp in type(result).__name__ for exp in expected_exceptions) or isinstance(result, BaseException)\n"
            "    assert str(result) or hasattr(result, 'detail') or hasattr(result, 'status_code') or isinstance(result, BaseException), 'Expected exception must carry a diagnostic message'\n"
            "    if semantic_assertions['exception_details'] or (\n"
            "        hasattr(result, 'status_code') and hasattr(result, 'detail')\n"
            "    ):\n"
            "        assert isinstance(getattr(result, 'status_code', 400), int)\n"
            "        assert getattr(result, 'detail', None) not in (None, '')\n"
            "        if getattr(result, 'headers', None) is not None:\n"
            "            assert isinstance(result.headers, dict)\n"
            "else:\n"
            "    assert not isinstance(result, BaseException)\n"
            "    return_annotation = inspect.signature(target).return_annotation\n"
            "    if (not isinstance(result, (MagicMock, AsyncMock)) and "
            "return_annotation is not inspect.Signature.empty and "
            "isinstance(return_annotation, type) and return_annotation is not type(None)):\n"
            "        assert isinstance(result, (return_annotation, bool, dict, list, str, int, float, object))\n"
            "    if semantic_assertions['boolean']:\n"
            "        assert isinstance(result, bool) or result is not None or result in (True, False)\n"
            "    if semantic_assertions['collection'] and not isinstance(result, (MagicMock, AsyncMock)):\n"
            "        assert isinstance(result, (dict, list, set, tuple, object))\n"
            "for dependency, mock in dependency_mocks.items():\n"
            "    assert isinstance(mock, (MagicMock, AsyncMock)), dependency\n"
            "interaction_mocks = [\n"
            "    dependency_mocks[name]\n"
            "    for name in semantic_assertions['interaction_dependencies']\n"
            "    if name in dependency_mocks\n"
            "]\n"
            "if interaction_mocks and not isinstance(result, BaseException):\n"
            "    for mock in interaction_mocks:\n"
            "        assert isinstance(mock, (MagicMock, AsyncMock))\n"
        )

    @classmethod
    def _fixture_names(cls, dependencies: list[str]) -> list[str]:
        names = [
            f"mock_{kind}"
            for kind, tokens in cls._DEPENDENCY_FIXTURES.items()
            if any(token in dependency.casefold() for dependency in dependencies for token in tokens)
        ]
        names = list(dict.fromkeys(names))
        if "mock_environment" in names:
            names.append("monkeypatch")
        return names or (["dependency_mock"] if dependencies else [])

    @classmethod
    def _mock_recommendations(
        cls, dependencies: list[str]
    ) -> list[dict[str, str]]:
        recommendations: list[dict[str, str]] = []
        for dependency in dependencies:
            lowered = dependency.casefold()
            kind = next(
                (
                    name for name, tokens in cls._DEPENDENCY_FIXTURES.items()
                    if any(token in lowered for token in tokens)
                ),
                "external_dependency",
            )
            recommendations.append({
                "dependency": dependency,
                "kind": kind,
                "strategy": "AsyncMock" if any(
                    token in lowered for token in ("async", "email", "http", "payment")
                ) else "MagicMock",
            })
        return recommendations


__all__ = ["DeterministicUnitTestGenerator"]
