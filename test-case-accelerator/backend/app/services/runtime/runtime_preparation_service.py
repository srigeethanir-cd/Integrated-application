"""Prepare optimized tests for the later runtime-validation stage."""

from __future__ import annotations

import ast
from copy import deepcopy
import re
from typing import Any

from app.schemas.runtime_preparation import (
    RuntimeExecutionPlan,
    RuntimeExecutionTarget,
    RuntimePreparationIssue,
    RuntimeTestClassification,
)
from app.schemas.test_case import TestCase


class RuntimePreparationService:
    """Convert an optimized suite into a non-mutating runtime execution plan."""

    def prepare(
        self,
        optimized_test_suite: list[TestCase | dict[str, Any]],
        code_understanding: dict[str, Any],
    ) -> RuntimeExecutionPlan:
        endpoints = code_understanding.get("api_endpoints", [])
        models = code_understanding.get("data_models", [])
        pydantic_schemas = code_understanding.get("pydantic_schemas", [])
        targets = [
            self._prepare_test(
                TestCase.model_validate(item),
                endpoints,
                models,
                pydantic_schemas,
            )
            for item in optimized_test_suite
        ]
        targets = self._plan_http_dependencies(targets)
        issues = [
            issue for target in targets for issue in target.issues
        ]
        prepared = sum(target.executable for target in targets)
        return RuntimeExecutionPlan(
            targets=targets,
            issues=issues,
            total_tests=len(targets),
            prepared_tests=prepared,
            unresolved_tests=len(targets) - prepared,
        )

    @classmethod
    def _plan_http_dependencies(
        cls,
        targets: list[RuntimeExecutionTarget],
    ) -> list[RuntimeExecutionTarget]:
        """Order CRUD targets and replace guessed IDs with capture references."""
        creators = [
            target for target in targets
            if target.classification == RuntimeTestClassification.HTTP
            and target.executable
            and target.http_method == "POST"
            and target.route
        ]
        prerequisites: list[RuntimeExecutionTarget] = []
        independent: list[RuntimeExecutionTarget] = []
        dependent: list[RuntimeExecutionTarget] = []
        creator_fields: dict[str, set[str]] = {}
        for target in targets:
            if target in creators:
                prerequisites.append(target)
                continue
            placeholders = re.findall(
                r"\{([^{}:]+)(?::[^{}]+)?\}", target.route or ""
            )
            creator = next(
                (
                    item for item in creators
                    if cls._resource_root(item.route or "")
                    == cls._resource_root(target.route or "")
                ),
                None,
            )
            if not placeholders or creator is None or target.http_method not in {
                "GET", "PUT", "PATCH", "DELETE"
            }:
                independent.append(target)
                continue
            trace = deepcopy(target.traceability)
            trace["depends_on"] = {
                "test_case_id": creator.test_case_id,
                "method": creator.http_method,
                "route": creator.route,
                "identifier_fields": placeholders,
            }
            path_parameters = dict(target.path_parameters)
            for name in placeholders:
                path_parameters[name] = f"captured:{name}"
            creator_fields.setdefault(creator.test_case_id, set()).update(
                placeholders
            )
            dependent.append(target.model_copy(update={
                "path_parameters": path_parameters,
                "traceability": trace,
            }))
        updated_creators = []
        for creator in prerequisites:
            trace = deepcopy(creator.traceability)
            fields = sorted(creator_fields.get(creator.test_case_id, set()))
            if fields:
                trace["identifier_fields"] = fields
            updated_creators.append(creator.model_copy(update={"traceability": trace}))
        return [*updated_creators, *independent, *dependent]

    @staticmethod
    def _resource_root(route: str) -> str:
        prefix = route.split("{", 1)[0].rstrip("/")
        return prefix or "/"

    def _prepare_test(
        self,
        case: TestCase,
        endpoints: list[dict[str, Any]],
        models: list[dict[str, Any]],
        pydantic_schemas: list[dict[str, Any]],
    ) -> RuntimeExecutionTarget:
        trace = deepcopy(case.traceability or {})
        if case.unit_test is not None:
            return RuntimeExecutionTarget(
                test_case_id=case.id,
                classification=RuntimeTestClassification.UNIT,
                executable=True,
                traceability=trace,
                module=case.unit_test.module,
                symbol=case.unit_test.symbol,
                generated_code=case.unit_test.generated_code,
            )

        references = [
            item for item in trace.get("api_routes", [])
            if isinstance(item, dict)
        ]
        reference = references[0] if references else {}
        endpoint = self._exact_endpoint(trace, endpoints)
        if endpoint is not None and not self._targets_http_endpoint(
            trace, endpoint
        ):
            endpoint = None
        if endpoint is None:
            if self._has_unresolved_http_method(trace, endpoints):
                route = self._text(trace.get("route")) or self._text(
                    reference.get("route")
                )
                issue = RuntimePreparationIssue(
                    test_case_id=case.id,
                    code="http_method_unresolved",
                    message="No exact HTTP method reference could be resolved",
                )
                return RuntimeExecutionTarget(
                    test_case_id=case.id,
                    classification=RuntimeTestClassification.HTTP,
                    route=route,
                    http_method=None,
                    executable=False,
                    traceability=trace,
                    issues=[issue],
                )
            classification = (
                RuntimeTestClassification.INTEGRATION
                if case.category.value == "exception/integration"
                else RuntimeTestClassification.UNIT
            )
            issue = RuntimePreparationIssue(
                test_case_id=case.id,
                code="non_http_test",
                message=(
                    "Internal helper function (HTTP validation not applicable)"
                ),
            )
            return RuntimeExecutionTarget(
                test_case_id=case.id,
                classification=classification,
                executable=False,
                traceability=trace,
                issues=[issue],
            )
        source = endpoint or {}

        # Stage 3 endpoint metadata is authoritative; traceability is fallback.
        route = self._text(source.get("route")) or self._text(
            trace.get("route")
        ) or self._text(reference.get("route"))
        method = self._text(source.get("method")) or self._text(
            trace.get("method")
        ) or self._text(reference.get("method"))
        if method:
            method = method.upper()

        status = self._resolve_status(case, source, trace, reference)
        path_parameters, _ = self._parameters(
            self._first(
                source, trace, reference, keys=("path_parameters",)
            )
        )
        query_parameters, unresolved_query = self._parameters(
            self._first(
                source, trace, reference, keys=("query_parameters",)
            )
        )
        required_headers, unresolved_headers = self._parameters(
            self._first(
                trace, source, reference,
                keys=("required_headers", "headers"),
            )
        )
        required_headers = {
            str(name): str(value)
            for name, value in required_headers.items()
        }
        authentication_value = self._first(
            trace, source, reference,
            keys=("authentication_required", "requires_auth", "authenticated"),
        )
        authentication_required = (
            bool(authentication_value)
            if authentication_value is not None else None
        )
        authentication_schemes = self._strings(self._first(
            trace, source, reference,
            keys=("authentication_schemes", "security_schemes"),
        ))

        request_model = (
            self._text(source.get("request_model"))
            or self._text(source.get("request_type"))
            or self._text(trace.get("request_model"))
        )
        response_model = (
            self._text(source.get("response_model"))
            or self._text(source.get("response_type"))
            or self._text(trace.get("response_model"))
        )
        payload = self._first(
            trace,
            source,
            reference,
            keys=("request_payload", "request_example", "body"),
        )
        if payload is None:
            payload = self._structured_model_value(
                pydantic_schemas, request_model
            )
        if payload is None:
            payload = self._model_example(models, request_model)
        expected_response = self._first(
            source,
            trace,
            reference,
            keys=("expected_response", "response_example"),
        )
        if expected_response is None:
            expected_response = self._structured_model_value(
                pydantic_schemas, response_model
            )
        if expected_response is None:
            expected_response = self._model_example(models, response_model)
        expected_response_fields = self._strings(self._first(
            trace, source, reference,
            keys=("expected_response_fields", "response_fields"),
        ))
        if not expected_response_fields and isinstance(expected_response, dict):
            expected_response_fields = sorted(expected_response)

        issues = []
        if route is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="route_unresolved",
                message="No exact route reference could be resolved",
            ))
        if method is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="http_method_unresolved",
                message="No exact HTTP method reference could be resolved",
            ))
        if status is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="expected_status_unresolved",
                message="No supported expected HTTP status was found",
            ))

        placeholders = set()
        if route:
            placeholders = {
                value.split(":", 1)[0]
                for value in re.findall(r"\{([^{}]+)\}", route)
            }
        missing_path = sorted(placeholders - path_parameters.keys())
        if missing_path:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="path_parameters_unresolved",
                message=(
                    "No supported value was found for path parameter(s): "
                    + ", ".join(missing_path)
                ),
            ))
        if unresolved_query:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="query_parameters_unresolved",
                message=(
                    "No supported value was found for query parameter(s): "
                    + ", ".join(sorted(unresolved_query))
                ),
            ))
        if unresolved_headers:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="missing_required_headers",
                message=(
                    "Missing required headers: "
                    + ", ".join(sorted(unresolved_headers))
                ),
            ))
        if authentication_required is True and not self._has_authentication(
            required_headers
        ):
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="missing_authentication",
                message="Missing authentication",
            ))

        payload_required = (
            method in {"POST", "PUT", "PATCH"}
            or request_model is not None
            or any(key in source for key in ("request_payload", "request_type"))
        )
        if payload_required and payload is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=case.id,
                code="request_payload_unresolved",
                message="No supported request payload or model example was found",
            ))

        executable = not issues
        return RuntimeExecutionTarget(
            test_case_id=case.id,
            classification=RuntimeTestClassification.HTTP,
            route=route,
            http_method=method,
            expected_http_status=status,
            path_parameters=path_parameters,
            query_parameters=query_parameters,
            required_headers=required_headers,
            authentication_required=authentication_required,
            authentication_schemes=authentication_schemes,
            request_payload=deepcopy(payload),
            expected_response=deepcopy(expected_response),
            expected_response_fields=expected_response_fields,
            executable=executable,
            traceability=trace,
            issues=issues,
        )

    @staticmethod
    def _targets_http_endpoint(
        trace: dict[str, Any],
        endpoint: dict[str, Any],
    ) -> bool:
        explicit_symbol = RuntimePreparationService._text(
            trace.get("symbol")
        )
        if explicit_symbol is not None:
            return endpoint.get("handler") == explicit_symbol
        explicit_method = RuntimePreparationService._text(trace.get("method"))
        if trace.get("route") and explicit_method:
            return (
                endpoint.get("route") == trace.get("route")
                and RuntimePreparationService._method_matches(
                    endpoint, explicit_method
                )
            )
        return any(
            isinstance(reference, dict)
            and RuntimePreparationService._text(reference.get("method"))
            and reference.get("route") == endpoint.get("route")
            and RuntimePreparationService._method_matches(
                endpoint, reference["method"]
            )
            and (
                reference.get("handler") is not None
                and reference.get("handler") == endpoint.get("handler")
            )
            for reference in (
                trace.get("api_routes", [])
                if isinstance(trace.get("api_routes"), list)
                else []
            )
        )

    @staticmethod
    def _exact_endpoint(
        trace: dict[str, Any], endpoints: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        references = trace.get("api_routes", [])
        references = references if isinstance(references, list) else []
        explicit_symbol = RuntimePreparationService._text(trace.get("symbol"))
        if explicit_symbol:
            candidates = [
                endpoint for endpoint in endpoints
                if endpoint.get("handler") == explicit_symbol
            ]
            if not candidates:
                return None
            method = RuntimePreparationService._text(trace.get("method"))
            if method is None:
                method = next(
                    (
                        RuntimePreparationService._text(item.get("method"))
                        for item in references
                        if isinstance(item, dict)
                        and item.get("handler") == explicit_symbol
                        and RuntimePreparationService._text(item.get("method"))
                    ),
                    None,
                )
            if method is not None:
                candidates = [
                    endpoint for endpoint in candidates
                    if RuntimePreparationService._method_matches(endpoint, method)
                ]
                if not candidates:
                    return None
            elif len(candidates) != 1:
                return None

            route = RuntimePreparationService._text(trace.get("route"))
            if route is not None:
                candidates = [
                    endpoint for endpoint in candidates
                    if endpoint.get("route") == route
                ]
            return candidates[0] if len(candidates) == 1 else None

        for reference in references:
            if not isinstance(reference, dict):
                continue
            route = reference.get("route")
            method = RuntimePreparationService._text(reference.get("method"))
            handler = reference.get("handler")
            if not route or method is None:
                continue
            matches = [
                endpoint for endpoint in endpoints
                if (handler is None or endpoint.get("handler") == handler)
                and RuntimePreparationService._method_matches(endpoint, method)
                and endpoint.get("route") == route
            ]
            if len(matches) == 1:
                return matches[0]

        route = RuntimePreparationService._text(trace.get("route"))
        method = RuntimePreparationService._text(trace.get("method"))
        if route and method:
            matches = [
                endpoint for endpoint in endpoints
                if endpoint.get("route") == route
                and RuntimePreparationService._method_matches(endpoint, method)
            ]
            return matches[0] if len(matches) == 1 else None
        return None

    @staticmethod
    def _method_matches(endpoint: dict[str, Any], method: str) -> bool:
        endpoint_method = RuntimePreparationService._text(endpoint.get("method"))
        return bool(endpoint_method and endpoint_method.upper() == method.upper())

    @staticmethod
    def _has_unresolved_http_method(
        trace: dict[str, Any], endpoints: list[dict[str, Any]]
    ) -> bool:
        symbol = RuntimePreparationService._text(trace.get("symbol"))
        if symbol:
            handler_matches = [
                endpoint for endpoint in endpoints
                if endpoint.get("handler") == symbol
            ]
            if not handler_matches:
                return False
            method = RuntimePreparationService._text(trace.get("method"))
            if method is not None:
                return not any(
                    RuntimePreparationService._method_matches(endpoint, method)
                    for endpoint in handler_matches
                )
            return len(handler_matches) != 1

        route = RuntimePreparationService._text(trace.get("route"))
        if route and any(endpoint.get("route") == route for endpoint in endpoints):
            return RuntimePreparationService._text(trace.get("method")) is None
        return False

    @staticmethod
    def _first(
        *sources: dict[str, Any], keys: tuple[str, ...]
    ) -> Any:
        for source in sources:
            for key in keys:
                if key in source and source[key] is not None:
                    return deepcopy(source[key])
        return None

    @staticmethod
    def _status(value: Any) -> int | None:
        if isinstance(value, list):
            values = sorted({
                RuntimePreparationService._status(item) for item in value
            } - {None})
            return values[0] if values else None
        if isinstance(value, bool):
            return None
        if isinstance(value, int) and 100 <= value <= 599:
            return value
        if isinstance(value, str) and value.isdigit():
            parsed = int(value)
            return parsed if 100 <= parsed <= 599 else None
        return None

    @classmethod
    def _statuses(cls, value: Any) -> list[int]:
        values = value if isinstance(value, list) else [value]
        return sorted({
            status
            for item in values
            if (status := cls._status(item)) is not None
        })

    @classmethod
    def _status_candidates(
        cls,
        sources: tuple[dict[str, Any], ...],
        keys: tuple[str, ...],
    ) -> list[int]:
        for source in sources:
            for key in keys:
                statuses = cls._statuses(source.get(key))
                if statuses:
                    return statuses
        return []

    @staticmethod
    def _select_status(
        statuses: list[int],
        preferred: tuple[int, ...],
        ranges: tuple[tuple[int, int], ...],
    ) -> int | None:
        for status in preferred:
            if status in statuses:
                return status
        for minimum, maximum in ranges:
            ranged = [
                status for status in statuses
                if minimum <= status <= maximum
            ]
            if ranged:
                return min(ranged)
        return None

    @classmethod
    def _resolve_status(
        cls,
        case: TestCase,
        endpoint: dict[str, Any],
        trace: dict[str, Any],
        reference: dict[str, Any],
    ) -> int | None:
        explicit = cls._status(cls._first(
            trace,
            reference,
            endpoint,
            keys=(
                "expected_http_status",
                "expected_status",
                "status_code",
            ),
        ))
        if explicit is not None:
            return explicit

        case_text = " ".join([
            case.title,
            case.description,
            *case.steps,
            *case.expected_results,
        ])
        mapped_statuses = {
            cls._status(item.get("status_code"))
            for item in endpoint.get("exception_status_mappings", [])
            if isinstance(item, dict)
            and isinstance(item.get("exception"), str)
            and re.search(
                rf"\b{re.escape(item['exception'])}\b", case_text
            )
        } - {None}
        if len(mapped_statuses) == 1:
            return mapped_statuses.pop()

        category = case.category.value
        sources = (endpoint, trace, reference)
        if category in {"positive", "boundary"}:
            candidates = cls._status_candidates(
                sources,
                ("success_status_code", "success_status_codes"),
            )
            selected = cls._select_status(
                candidates,
                preferred=(200, 201),
                ranges=((200, 299),),
            )
            return selected or cls._default_http_status(endpoint)
        if category in {"negative", "security", "exception/integration"}:
            candidates = cls._status_candidates(
                sources,
                ("error_status_code", "error_status_codes"),
            )
            selected = cls._select_status(
                candidates,
                preferred=(400, 401, 403, 404),
                ranges=((400, 499), (500, 599)),
            )
            return selected or cls._default_http_status(endpoint)
        candidates = cls._status_candidates(
            sources,
            ("status_code", "status_codes"),
        )
        return cls._status(candidates) or cls._default_http_status(endpoint)

    @staticmethod
    def _default_http_status(endpoint: dict[str, Any]) -> int | None:
        method = RuntimePreparationService._text(endpoint.get("method"))
        if method and method.upper() in {
            "GET", "POST", "PUT", "PATCH", "DELETE"
        }:
            return 200
        return None

    @staticmethod
    def _parameters(value: Any) -> tuple[dict[str, Any], set[str]]:
        if value is None:
            return {}, set()
        if isinstance(value, list):
            names = {item for item in value if isinstance(item, str)}
            return {}, names
        if not isinstance(value, dict):
            return {}, set()

        resolved: dict[str, Any] = {}
        unresolved: set[str] = set()
        for name, specification in value.items():
            if isinstance(specification, dict):
                found = False
                for key in ("value", "default", "example"):
                    if key in specification and specification[key] is not None:
                        resolved[name] = deepcopy(specification[key])
                        found = True
                        break
                if not found:
                    unresolved.add(name)
            elif specification is not None:
                resolved[name] = deepcopy(specification)
            else:
                unresolved.add(name)
        return resolved, unresolved

    @staticmethod
    def _model_example(
        models: list[dict[str, Any]], model_name: str | None
    ) -> Any:
        if model_name is None:
            return None
        model = next(
            (
                item for item in models
                if isinstance(item, dict)
                and item.get("name") == model_name
            ),
            None,
        )
        if model is None:
            return None
        for key in ("example", "request_example", "response_example",
                    "defaults", "field_defaults"):
            if key in model and model[key] is not None:
                return deepcopy(model[key])
        fields = model.get("fields")
        if not isinstance(fields, dict):
            return None
        values, unresolved = RuntimePreparationService._parameters(fields)
        return values if values and not unresolved else None

    @staticmethod
    def _structured_model_value(
        schemas: list[dict[str, Any]], model_name: str | None
    ) -> Any:
        if model_name is None:
            return None
        schema = next(
            (
                item for item in schemas
                if isinstance(item, dict)
                and item.get("name") == model_name
            ),
            None,
        )
        if schema is None:
            return None

        examples = schema.get("examples", [])
        if isinstance(examples, list) and examples:
            return deepcopy(examples[0])

        fields = schema.get("fields")
        if not isinstance(fields, list):
            return None
        result: dict[str, Any] = {}
        for field in fields:
            if not isinstance(field, dict) or not isinstance(
                field.get("name"), str
            ):
                return None
            field_examples = field.get("examples", [])
            if isinstance(field_examples, list) and field_examples:
                result[field["name"]] = deepcopy(field_examples[0])
            elif field.get("has_default") is True:
                result[field["name"]] = deepcopy(field.get("default"))
            elif field.get("required", True):
                synthesized = RuntimePreparationService._synthesized_value(
                    field.get("type")
                )
                if synthesized is _UNRESOLVED:
                    return None
                result[field["name"]] = synthesized
        return result

    @staticmethod
    def _synthesized_value(field_type: Any) -> Any:
        if not isinstance(field_type, str) or not field_type.strip():
            return _UNRESOLVED
        value = field_type.strip()
        normalized = value.casefold().replace("typing.", "")

        literal = re.search(r"\bliteral\s*\[(.*)\]\s*$", value, re.I)
        if literal:
            try:
                members = ast.literal_eval(f"[{literal.group(1)}]")
            except (SyntaxError, ValueError):
                return _UNRESOLVED
            return deepcopy(members[0]) if members else _UNRESOLVED

        if re.search(r"\bemailstr\b", normalized):
            return "user@example.com"
        if re.search(r"\buuid\b", normalized):
            return "00000000-0000-0000-0000-000000000001"
        if re.search(r"\bdatetime\b", normalized):
            return "2026-01-01T00:00:00Z"
        if re.search(r"\bdate\b", normalized):
            return "2026-01-01"
        if re.search(r"\b(?:list|sequence|set|tuple)\s*(?:\[|$)", normalized):
            return []
        if re.search(r"\b(?:dict|mapping)\s*(?:\[|$)", normalized):
            return {}
        if re.search(r"\bbool\b", normalized):
            return True
        if re.search(r"\bfloat\b", normalized):
            return 1.0
        if re.search(r"\bint\b", normalized):
            return 1
        if re.search(r"\bstr\b", normalized):
            return "example"
        return _UNRESOLVED

    @staticmethod
    def _text(value: Any) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        if isinstance(value, (list, tuple, set)):
            return [
                item.strip() for item in value
                if isinstance(item, str) and item.strip()
            ]
        if isinstance(value, dict):
            return [str(item) for item in value]
        return []

    @staticmethod
    def _has_authentication(headers: dict[str, str]) -> bool:
        return any(
            name.casefold() in {"authorization", "x-api-key", "api-key"}
            and bool(value)
            for name, value in headers.items()
        )


_UNRESOLVED = object()
