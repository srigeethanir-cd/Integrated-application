"""Deterministic executable-scenario planning for Stage 4 output."""

from __future__ import annotations

import re
import logging
from copy import deepcopy
from typing import Any

from app.schemas.test_case import TestCase

logger = logging.getLogger(__name__)
PLANNER_VERSION = "lifecycle-v1"


class ExecutableScenarioPlanner:
    """Ground HTTP cases with payloads and resource lifecycle dependencies."""

    _HTTP_METHOD = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b", re.I)
    _PLACEHOLDER = re.compile(r"\{([^{}:]+)(?::[^{}]+)?\}")

    def plan(
        self, cases: list[TestCase], stage3: dict[str, Any]
    ) -> list[TestCase]:
        endpoints = [
            item for item in stage3.get("api_endpoints", [])
            if isinstance(item, dict) and item.get("route") and item.get("method")
        ]
        schemas = {
            item.get("name"): item
            for item in stage3.get("pydantic_schemas", [])
            if isinstance(item, dict) and item.get("name")
        }
        enriched = [
            self._enrich(case, self._endpoint(case, endpoints), schemas)
            for case in cases
        ]
        existing_positive = {
            self._case_key(case)
            for case in enriched
            if self._is_success_case(case)
        }
        if "regeneration_plan" not in stage3:
            for endpoint in endpoints:
                key = (str(endpoint["method"]).upper(), endpoint["route"])
                if key not in existing_positive:
                    enriched.append(self._endpoint_case(endpoint, schemas))
                    existing_positive.add(key)
        prerequisites: list[TestCase] = []
        prerequisite_keys: set[tuple[str, str]] = set()
        for case in enriched:
            endpoint = self._endpoint(case, endpoints)
            if endpoint is None or not self._requires_existing_entity(case, endpoint):
                continue
            creator = self._creator(endpoint, endpoints)
            if creator is None:
                continue
            key = (str(creator["method"]).upper(), creator["route"])
            existing = next(
                (
                    item for item in enriched
                    if self._case_key(item) == key
                    and item.category.value in {"positive", "boundary"}
                ),
                None,
            )
            if existing is None and key not in prerequisite_keys:
                prerequisites.append(self._prerequisite(creator, schemas, case.id))
                prerequisite_keys.add(key)
            trace = dict(case.traceability or {})
            parameters = self._PLACEHOLDER.findall(endpoint["route"])
            trace["depends_on"] = {
                "method": creator["method"],
                "route": creator["route"],
                "identifier_fields": parameters,
            }
            trace["path_parameters"] = {
                name: {
                    "value": f"captured:{name}",
                    "source": "captured_identifier",
                }
                for name in parameters
            }
            case_index = enriched.index(case)
            enriched[case_index] = case.model_copy(
                update={
                    "traceability": trace,
                    "preconditions": self._unique([
                        *case.preconditions,
                        "Create the required resource and capture its returned identifier",
                    ]),
                }
            )

        cleanup: list[TestCase] = []
        for prerequisite in prerequisites:
            creator_route = str((prerequisite.traceability or {}).get("route", ""))
            deleter = next(
                (
                    item for item in endpoints
                    if str(item.get("method")).upper() == "DELETE"
                    and self._PLACEHOLDER.search(item["route"])
                    and (item["route"].split("{", 1)[0].rstrip("/") or "/")
                    == (creator_route.rstrip("/") or "/")
                ),
                None,
            )
            has_cleanup = any(
                self._case_key(item)
                == ("DELETE", deleter["route"] if deleter else "")
                and item.category.value in {"positive", "boundary"}
                for item in enriched
            )
            if deleter is not None and not has_cleanup:
                cleanup.append(self._cleanup(deleter, prerequisite.id))

        combined = [*prerequisites, *enriched, *cleanup]
        ordered = sorted(
            combined, key=lambda case: self._order_key(case, endpoints)
        )
        logger.info(
            "Stage 4 lifecycle plan version=%s execution_order=%s",
            PLANNER_VERSION,
            [
                {
                    "test_case_id": case.id,
                    "method": (case.traceability or {}).get("method"),
                    "route": (case.traceability or {}).get("route"),
                    "path_parameters": (case.traceability or {}).get(
                        "path_parameters"
                    ),
                    "depends_on": (case.traceability or {}).get("depends_on"),
                    "identifier_fields": (case.traceability or {}).get(
                        "identifier_fields"
                    ),
                    "payload": (case.traceability or {}).get("request_payload"),
                }
                for case in ordered
                if (case.traceability or {}).get("method")
            ],
        )
        return ordered

    def _enrich(
        self, case: TestCase, endpoint: dict[str, Any] | None,
        schemas: dict[str, dict[str, Any]],
    ) -> TestCase:
        if endpoint is None:
            return case
        trace = dict(case.traceability or {})
        method = str(endpoint["method"]).upper()
        trace.update({
            "route": endpoint["route"],
            "method": method,
            "symbol": endpoint.get("handler"),
            "request_model": endpoint.get("request_model")
            or endpoint.get("request_type"),
            "response_model": endpoint.get("response_model")
            or endpoint.get("response_type"),
            "stage4_planner_version": PLANNER_VERSION,
        })
        if case.category.value in {"positive", "boundary"}:
            trace["expected_http_status"] = self._success_status(endpoint)
            request_model = self._model_name(trace.get("request_model"))
            if method in {"POST", "PUT", "PATCH"} and not isinstance(
                trace.get("request_payload"), dict
            ):
                payload = self._payload(schemas.get(request_model))
                if payload:
                    trace["request_payload"] = payload
            response_model = self._model_name(trace.get("response_model"))
            response = schemas.get(response_model)
            fields = self._field_names(response)
            if fields:
                trace["expected_response_fields"] = fields
            identifiers = [
                name for name in fields
                if name == "id" or name.endswith("_id")
            ]
            if identifiers:
                trace["identifier_fields"] = identifiers
        return case.model_copy(update={"traceability": trace})

    def _endpoint(
        self, case: TestCase, endpoints: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        trace = case.traceability or {}
        symbol = trace.get("symbol")
        route = trace.get("route")
        method = str(trace.get("method") or "").upper()
        exact = [
            item for item in endpoints
            if (not symbol or item.get("handler") == symbol)
            and (not route or item.get("route") == route)
            and (not method or str(item.get("method")).upper() == method)
        ]
        if len(exact) == 1 and (symbol or (route and method)):
            return exact[0]
        text = " ".join([case.title, case.description, *case.steps])
        method_match = self._HTTP_METHOD.search(text)
        if method_match:
            requested_method = method_match.group(1).upper()
            route_matches = [
                item for item in endpoints
                if str(item.get("method")).upper() == requested_method
                and item["route"] in text
            ]
            if len(route_matches) == 1:
                return route_matches[0]
        return None

    def _requires_existing_entity(
        self, case: TestCase, endpoint: dict[str, Any]
    ) -> bool:
        return bool(
            self._PLACEHOLDER.search(endpoint["route"])
            and str(endpoint["method"]).upper() in {"GET", "PUT", "PATCH", "DELETE"}
            and case.category.value in {"positive", "boundary"}
            and 200 <= self._success_status(endpoint) < 300
        )

    @staticmethod
    def _creator(
        endpoint: dict[str, Any], endpoints: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        collection = endpoint["route"].split("{", 1)[0].rstrip("/") or "/"
        return next(
            (
                item for item in endpoints
                if str(item.get("method")).upper() == "POST"
                and (item.get("route", "").rstrip("/") or "/") == collection
            ),
            None,
        )

    def _prerequisite(
        self, endpoint: dict[str, Any], schemas: dict[str, dict[str, Any]],
        dependent_id: str,
    ) -> TestCase:
        request_model = self._model_name(
            endpoint.get("request_model") or endpoint.get("request_type")
        )
        response_model = self._model_name(
            endpoint.get("response_model") or endpoint.get("response_type")
        )
        response_fields = self._field_names(schemas.get(response_model))
        identifiers = [
            name for name in response_fields
            if name == "id" or name.endswith("_id")
        ] or ["id"]
        route = endpoint["route"]
        return TestCase(
            id=f"SETUP-{dependent_id}",
            title=f"Create prerequisite resource for {dependent_id}",
            description="Create a real resource and capture its returned identifier.",
            category="positive",
            priority="high",
            severity="major",
            preconditions=[],
            steps=[f"POST {route} with a schema-valid request payload"],
            expected_results=[
                f"HTTP {self._success_status(endpoint)} is returned",
                "The response contains a reusable resource identifier",
            ],
            traceability={
                "route": route,
                "method": "POST",
                "symbol": endpoint.get("handler"),
                "request_model": request_model,
                "response_model": response_model,
                "request_payload": self._payload(schemas.get(request_model)),
                "expected_http_status": self._success_status(endpoint),
                "expected_response_fields": response_fields,
                "identifier_fields": identifiers,
                "prerequisite_for": [dependent_id],
            },
        )

    def _endpoint_case(
        self, endpoint: dict[str, Any], schemas: dict[str, dict[str, Any]]
    ) -> TestCase:
        method = str(endpoint["method"]).upper()
        route = endpoint["route"]
        handler = endpoint.get("handler") or route
        case = TestCase(
            id=f"HTTP-{method}-{re.sub(r'[^A-Za-z0-9]+', '-', str(handler)).strip('-')}",
            title=f"{method} {route} succeeds with valid input",
            description=f"Execute the grounded {handler} endpoint successfully.",
            category="positive",
            priority="high",
            severity="major",
            preconditions=[],
            steps=[f"Send {method} {route} with valid grounded input"],
            expected_results=[
                f"HTTP {self._success_status(endpoint)} is returned"
            ],
            traceability={
                "route": route,
                "method": method,
                "symbol": endpoint.get("handler"),
                "cleanup": method == "DELETE" and bool(
                    self._PLACEHOLDER.search(route)
                ),
            },
        )
        return self._enrich(case, endpoint, schemas)

    def _payload(self, schema: dict[str, Any] | None) -> dict[str, Any]:
        if not schema:
            return {}
        fields = schema.get("fields", [])
        if not isinstance(fields, list):
            return {}
        payload: dict[str, Any] = {}
        for field in fields:
            if not isinstance(field, dict) or not field.get("name"):
                continue
            default = field.get("default")
            if field.get("has_default") and default is not None:
                payload[field["name"]] = deepcopy(default)
                continue
            examples = field.get("examples") or []
            if examples:
                payload[field["name"]] = deepcopy(examples[0])
                continue
            if field.get("required") or not payload:
                payload[field["name"]] = self._field_value(field)
        return payload

    def _cleanup(self, endpoint: dict[str, Any], prerequisite_id: str) -> TestCase:
        parameters = self._PLACEHOLDER.findall(endpoint["route"])
        return TestCase(
            id=f"CLEANUP-{prerequisite_id}",
            title=f"Clean up resource created by {prerequisite_id}",
            description="Delete the created resource using its captured identifier.",
            category="positive",
            priority="medium",
            severity="minor",
            preconditions=["A prerequisite resource identifier was captured"],
            steps=[f"DELETE {endpoint['route']} using the captured identifier"],
            expected_results=[
                f"HTTP {self._success_status(endpoint)} is returned",
                "The created resource is removed",
            ],
            traceability={
                "route": endpoint["route"],
                "method": "DELETE",
                "symbol": endpoint.get("handler"),
                "expected_http_status": self._success_status(endpoint),
                "path_parameters": {
                    name: {
                        "value": f"captured:{name}",
                        "source": "captured_identifier",
                    }
                    for name in parameters
                },
                "depends_on": {
                    "test_case_id": prerequisite_id,
                    "identifier_fields": parameters,
                },
                "cleanup": True,
            },
        )

    @staticmethod
    def _field_value(field: dict[str, Any]) -> Any:
        name = str(field.get("name", "value")).casefold()
        type_name = str(field.get("type", "str")).casefold()
        minimum = field.get("min_length") or 1
        if "email" in name:
            return "test@example.com"
        if "uuid" in type_name:
            return "00000000-0000-4000-8000-000000000001"
        if "bool" in type_name:
            return True
        if any(item in type_name for item in ("int", "float", "decimal")):
            if field.get("ge") is not None:
                return field["ge"]
            if field.get("gt") is not None:
                return field["gt"] + 1
            if field.get("le") is not None:
                return field["le"]
            if field.get("lt") is not None:
                return field["lt"] - 1
            return 1
        if any(item in type_name for item in ("list", "set", "tuple")):
            return ["example"] if minimum else []
        if "dict" in type_name:
            return {"key": "value"}
        value = f"test-{name.replace('_', '-')}"
        if len(value) < minimum:
            value += "x" * (minimum - len(value))
        maximum = field.get("max_length")
        return value[:maximum] if isinstance(maximum, int) else value

    @staticmethod
    def _success_status(endpoint: dict[str, Any]) -> int:
        statuses = endpoint.get("success_status_codes") or []
        if statuses:
            return int(statuses[0])
        return 200

    @staticmethod
    def _model_name(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        value = re.sub(r"^(?:List|list)\[(.*)]$", r"\1", value)
        return value.rsplit(".", 1)[-1]

    @staticmethod
    def _field_names(schema: dict[str, Any] | None) -> list[str]:
        if not schema or not isinstance(schema.get("fields"), list):
            return []
        return [
            field["name"] for field in schema["fields"]
            if isinstance(field, dict) and field.get("name")
        ]

    @staticmethod
    def _case_key(case: TestCase) -> tuple[str, str]:
        trace = case.traceability or {}
        return str(trace.get("method") or "").upper(), str(trace.get("route") or "")

    @staticmethod
    def _is_success_case(case: TestCase) -> bool:
        text = " ".join(
            [case.title, case.description, *case.steps, *case.expected_results]
        )
        status = re.search(r"\b(?:HTTP|status(?: code)?)\s*(\d{3})\b", text, re.I)
        if status:
            return 200 <= int(status.group(1)) < 300
        return not re.search(
            r"\b(?:invalid|missing|required field|unauthoriz|forbidden|"
            r"not found|non.?existent|error|failure|rejected)\b",
            text,
            re.I,
        )

    def _order_key(
        self, case: TestCase, endpoints: list[dict[str, Any]]
    ) -> tuple[int, str]:
        endpoint = self._endpoint(case, endpoints)
        method = str(endpoint.get("method") if endpoint else "").upper()
        rank = {"POST": 0, "GET": 1, "PUT": 2, "PATCH": 2, "DELETE": 3}.get(
            method, 1
        )
        return rank, case.id

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
