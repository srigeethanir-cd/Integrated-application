"""Complete persisted HTTP execution metadata from a FastAPI OpenAPI document."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from app.schemas.runtime_preparation import (
    RuntimeExecutionTarget,
    RuntimePreparationIssue,
    RuntimeTestClassification,
)


class OpenAPIMetadataService:
    """Resolve incomplete HTTP targets before they reach the executor."""

    def load_document(
        self, *, base_url: str, timeout_seconds: int = 15
    ) -> tuple[dict[str, Any] | None, str | None]:
        try:
            with urlopen(
                base_url.rstrip("/") + "/openapi.json",
                timeout=min(timeout_seconds, 15),
            ) as response:
                document = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError) as error:
            return None, str(error)
        if not isinstance(document, dict):
            return None, "OpenAPI response is not a JSON object"
        return document, None

    def complete(
        self,
        targets: list[RuntimeExecutionTarget],
        *,
        base_url: str,
        timeout_seconds: int = 15,
        document: dict[str, Any] | None = None,
    ) -> tuple[list[RuntimeExecutionTarget], str | None]:
        candidates = [
            target for target in targets
            if self._is_incomplete_http(target)
        ]
        if not candidates:
            return targets, None
        if document is None:
            document, error = self.load_document(
                base_url=base_url, timeout_seconds=timeout_seconds
            )
            if document is None:
                return targets, (
                    "Backend unavailable: could not load /openapi.json "
                    f"({error})"
                )
        return [
            self._complete_target(target, document)
            if self._is_incomplete_http(target)
            else target.model_copy(deep=True)
            for target in targets
        ], None

    @staticmethod
    def _is_incomplete_http(target: RuntimeExecutionTarget) -> bool:
        classification = target.classification
        is_http = (
            classification == RuntimeTestClassification.HTTP
            or classification is None and bool(target.route or target.http_method)
        )
        return is_http and (
            not target.executable
            or bool(target.issues)
            or target.authentication_required is None
        )

    @classmethod
    def _find_path_item(
        cls, route: str, document: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Match target route against OpenAPI paths using normalization."""
        paths = document.get("paths", {})
        if not isinstance(paths, dict) or not route:
            return None, None

        # 1. Exact match
        if route in paths and isinstance(paths[route], dict):
            return paths[route], route

        normalized_route = route.rstrip("/")

        # 2. Trailing slash normalized match
        for path_key, item in paths.items():
            if isinstance(item, dict) and path_key.rstrip("/") == normalized_route:
                return item, path_key

        # 3. Canonical placeholder match e.g. /users/{user_id} vs /users/{id}
        def _canonical(p: str) -> str:
            return re.sub(r"\{[^{}]+\}", "{}", p.rstrip("/"))

        canonical_target = _canonical(route)
        for path_key, item in paths.items():
            if isinstance(item, dict) and _canonical(path_key) == canonical_target:
                return item, path_key

        # 4. Match concrete path parameters e.g. /users/123 against /users/{id}
        for path_key, item in paths.items():
            if not isinstance(item, dict):
                continue
            pattern = "^" + re.sub(r"\{[^{}]+\}", r"[^/]+", path_key.rstrip("/")) + "$"
            if re.match(pattern, normalized_route):
                return item, path_key

        # 5. Handle route base path prefixes (e.g. /api/v1/users vs /users)
        prefix_match = re.search(r"/(?:api(?:/v\d+)?|v\d+)(/.*)", normalized_route, re.I)
        if prefix_match:
            stripped = prefix_match.group(1).rstrip("/")
            for path_key, item in paths.items():
                if isinstance(item, dict):
                    if (
                        path_key.rstrip("/") == stripped
                        or _canonical(path_key) == _canonical(stripped)
                    ):
                        return item, path_key

        return None, None

    def _complete_target(
        self, target: RuntimeExecutionTarget, document: dict[str, Any]
    ) -> RuntimeExecutionTarget:
        if (
            target.classification is not None
            and target.classification != RuntimeTestClassification.HTTP
        ):
            return target.model_copy(deep=True)
        updated = target.model_copy(deep=True)
        updated.classification = RuntimeTestClassification.HTTP

        was_originally_executable = target.executable and not target.issues

        if not updated.route:
            if was_originally_executable:
                updated.executable = True
                updated.issues = []
                return updated
            return self._with_issue(updated, "missing_endpoint", "Missing endpoint")

        path_item, _ = self._find_path_item(updated.route, document)
        if not isinstance(path_item, dict):
            if was_originally_executable:
                updated.executable = True
                updated.issues = []
                return updated
            return self._with_issue(updated, "missing_endpoint", "Missing endpoint")

        method = (updated.http_method or "").lower()
        operation = path_item.get(method) if isinstance(path_item, dict) else None
        if not isinstance(operation, dict):
            return self._with_issue(
                updated,
                "http_method_unresolved",
                "No exact HTTP method reference could be resolved",
            )

        updated.http_method = method.upper()
        parameters = [
            self._resolve_ref(item, document)
            for item in [*path_item.get("parameters", []), *operation.get("parameters", [])]
            if isinstance(item, dict)
        ]
        missing_parameters: list[str] = []
        for parameter in parameters:
            name, location = parameter.get("name"), parameter.get("in")
            if not isinstance(name, str):
                continue
            value = self._schema_value(
                parameter.get("schema", {}), document,
                example=parameter.get("example"),
            )
            destination = (
                updated.path_parameters if location == "path"
                else updated.query_parameters if location == "query"
                else updated.required_headers if location == "header"
                else None
            )
            if destination is not None and name not in destination:
                if value is not _UNRESOLVED:
                    destination[name] = str(value) if location == "header" else value
                elif parameter.get("required"):
                    missing_parameters.append(name)

        request_body = self._resolve_ref(operation.get("requestBody", {}), document)
        if updated.request_payload is None and request_body:
            content = request_body.get("content", {})
            media = content.get("application/json") or next(
                (value for value in content.values() if isinstance(value, dict)),
                {},
            )
            updated.request_payload = self._media_value(media, document)
            if updated.request_payload is _UNRESOLVED:
                updated.request_payload = None

        responses = operation.get("responses", {})
        if updated.expected_http_status is None:
            success = sorted(
                int(code) for code in responses
                if str(code).isdigit() and 200 <= int(code) <= 299
            )
            updated.expected_http_status = success[0] if success else None

        status_key = str(updated.expected_http_status) if updated.expected_http_status is not None else ""
        response = self._resolve_ref(
            responses.get(status_key, {}), document
        )
        content = response.get("content", {}) if isinstance(response, dict) else {}
        media = content.get("application/json") or next(
            (value for value in content.values() if isinstance(value, dict)), {}
        )
        response_schema = self._resolve_ref(media.get("schema", {}), document)
        if not updated.expected_response_fields:
            updated.expected_response_fields = sorted(
                response_schema.get("properties", {}).keys()
            )

        security = operation.get("security", document.get("security", []))
        security = (
            security if isinstance(security, list) else []
        )
        updated.authentication_required = bool(security) and not any(
            requirement == {} for requirement in security
        )
        updated.authentication_schemes = sorted({
            name for requirement in security if isinstance(requirement, dict)
            for name in requirement
        })
        auth_headers = self._authentication_headers(
            updated.authentication_schemes, document
        )
        auth_missing = updated.authentication_required and not any(
            name.casefold() in {
                header.casefold() for header in auth_headers
            }
            and bool(value)
            for name, value in updated.required_headers.items()
        )

        issues: list[RuntimePreparationIssue] = []
        if missing_parameters:
            issues.append(RuntimePreparationIssue(
                test_case_id=updated.test_case_id,
                code="missing_required_parameters",
                message="Missing required parameters: " + ", ".join(missing_parameters),
            ))
        if request_body.get("required") and updated.request_payload is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=updated.test_case_id,
                code="missing_request_schema",
                message="Missing request schema",
            ))
        if auth_missing:
            issues.append(RuntimePreparationIssue(
                test_case_id=updated.test_case_id,
                code="missing_authentication",
                message="Missing authentication",
            ))
        if updated.expected_http_status is None:
            issues.append(RuntimePreparationIssue(
                test_case_id=updated.test_case_id,
                code="missing_expected_status",
                message="Missing expected HTTP status",
            ))

        if was_originally_executable:
            updated.executable = True
            updated.issues = []
        else:
            updated.issues = issues
            updated.executable = not issues

        return updated

    @classmethod
    def _authentication_headers(
        cls, schemes: list[str], document: dict[str, Any]
    ) -> set[str]:
        definitions = document.get("components", {}).get(
            "securitySchemes", {}
        )
        headers: set[str] = set()
        for name in schemes:
            definition = cls._resolve_ref(definitions.get(name, {}), document)
            if definition.get("type") == "apiKey" and definition.get("in") == "header":
                header = definition.get("name")
                if isinstance(header, str):
                    headers.add(header)
            elif definition.get("type") in {"http", "oauth2", "openIdConnect"}:
                headers.add("Authorization")
        return headers or {"Authorization", "X-API-Key", "API-Key"}

    @staticmethod
    def _with_issue(
        target: RuntimeExecutionTarget, code: str, message: str
    ) -> RuntimeExecutionTarget:
        target.issues = [RuntimePreparationIssue(
            test_case_id=target.test_case_id, code=code, message=message
        )]
        target.executable = False
        return target

    @classmethod
    def _resolve_ref(
        cls, value: Any, document: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        reference = value.get("$ref")
        if not isinstance(reference, str) or not reference.startswith("#/"):
            return value
        resolved: Any = document
        for component in reference[2:].split("/"):
            resolved = resolved.get(component, {}) if isinstance(resolved, dict) else {}
        return resolved if isinstance(resolved, dict) else {}

    @classmethod
    def _media_value(cls, media: dict[str, Any], document: dict[str, Any]) -> Any:
        if "example" in media:
            return deepcopy(media["example"])
        examples = media.get("examples", {})
        if isinstance(examples, dict) and examples:
            example = cls._resolve_ref(next(iter(examples.values())), document)
            if "value" in example:
                return deepcopy(example["value"])
        return cls._schema_value(media.get("schema", {}), document)

    @classmethod
    def _schema_value(
        cls, schema: Any, document: dict[str, Any], *, example: Any = None
    ) -> Any:
        if example is not None:
            return deepcopy(example)
        schema = cls._resolve_ref(schema, document)
        for key in ("example", "default", "const"):
            if key in schema:
                return deepcopy(schema[key])
        if isinstance(schema.get("enum"), list) and schema["enum"]:
            return deepcopy(schema["enum"][0])
        for combinator in ("oneOf", "anyOf", "allOf"):
            values = schema.get(combinator)
            if isinstance(values, list) and values:
                if combinator == "allOf":
                    result = {}
                    for value in values:
                        item = cls._schema_value(value, document)
                        if isinstance(item, dict):
                            result.update(item)
                    return result or _UNRESOLVED
                return cls._schema_value(values[0], document)
        schema_type = schema.get("type")
        if schema_type == "object" or isinstance(schema.get("properties"), dict):
            result = {}
            required = set(schema.get("required", []))
            for name, field in schema.get("properties", {}).items():
                value = cls._schema_value(field, document)
                if value is not _UNRESOLVED and (
                    name in required or any(
                        key in field for key in ("example", "default", "const")
                    )
                ):
                    result[name] = value
                elif name in required:
                    return _UNRESOLVED
            return result
        if schema_type == "array":
            return []
        if schema_type == "string":
            fmt = schema.get("format")
            return {
                "email": "user@example.com",
                "uuid": "00000000-0000-0000-0000-000000000001",
                "date": "2026-01-01",
                "date-time": "2026-01-01T00:00:00Z",
            }.get(fmt, "example")
        if schema_type == "integer":
            return schema.get("minimum", 1)
        if schema_type == "number":
            return schema.get("minimum", 1.0)
        if schema_type == "boolean":
            return True
        return _UNRESOLVED


_UNRESOLVED = object()
