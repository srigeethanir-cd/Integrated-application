from copy import deepcopy

import pytest

from app.services.runtime.runtime_preparation_service import (
    RuntimePreparationService,
)


def _case(case_id: str, traceability: dict) -> dict:
    return {
        "id": case_id,
        "title": "Runtime candidate",
        "description": "Prepare without mutation",
        "category": "positive",
        "priority": "high",
        "severity": "major",
        "steps": ["Send request"],
        "expected_results": ["Request succeeds"],
        "traceability": traceability,
    }


def test_preparation_resolves_executable_http_spec_without_mutation() -> None:
    suite = [_case("TC-1", {
        "symbol": "update_project",
        "source_files": ["app/projects.py"],
    })]
    original = deepcopy(suite)
    stage3 = {
        "api_endpoints": [{
            "route": "/projects/{project_id}",
            "method": "PATCH",
            "handler": "update_project",
            "file": "app/projects.py",
            "expected_http_status": 200,
            "path_parameters": {"project_id": {"example": 42}},
            "query_parameters": {"notify": {"default": True}},
            "request_type": "ProjectUpdate",
            "response_type": "ProjectResponse",
        }],
        "data_models": [
            {"name": "ProjectUpdate", "example": {"name": "Updated"}},
            {
                "name": "ProjectResponse",
                "example": {"id": 42, "name": "Updated"},
            },
        ],
    }

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert suite == original
    assert plan.total_tests == 1
    assert plan.prepared_tests == 1
    assert plan.unresolved_tests == 0
    assert plan.targets[0].route == "/projects/{project_id}"
    assert plan.targets[0].classification == "HTTP"
    assert plan.targets[0].http_method == "PATCH"
    assert plan.targets[0].expected_http_status == 200
    assert plan.targets[0].path_parameters == {"project_id": 42}
    assert plan.targets[0].query_parameters == {"notify": True}
    assert plan.targets[0].request_payload == {"name": "Updated"}
    assert plan.targets[0].expected_response == {
        "id": 42, "name": "Updated"
    }
    assert plan.targets[0].executable is True
    assert plan.targets[0].traceability == suite[0]["traceability"]


def test_preparation_classifies_missing_endpoint_as_non_http() -> None:
    suite = [_case("TC-1", {"source_files": ["worker.py"]})]

    plan = RuntimePreparationService().prepare(suite, {"api_endpoints": []})

    assert plan.prepared_tests == 0
    assert plan.unresolved_tests == 1
    assert plan.targets[0].route is None
    assert plan.targets[0].http_method is None
    assert plan.targets[0].classification == "UNIT"
    assert [issue.code for issue in plan.issues] == ["non_http_test"]
    assert plan.issues[0].message == (
        "Internal helper function (HTTP validation not applicable)"
    )


def test_preparation_defaults_empty_get_status_to_200() -> None:
    suite = [_case("TC-1", {"symbol": "list_projects"})]
    stage3 = {"api_endpoints": [{
        "route": "/projects",
        "method": "GET",
        "handler": "list_projects",
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].expected_http_status == 200
    assert plan.issues == []


def test_preparation_orders_crud_creator_and_replaces_hardcoded_identifier() -> None:
    suite = [
        _case("TC-GET", {"symbol": "get_item"}),
        _case("TC-CREATE", {"symbol": "create_item"}),
    ]
    stage3 = {"api_endpoints": [
        {
            "route": "/items/{item_id}",
            "method": "GET",
            "handler": "get_item",
            "expected_http_status": 200,
            "path_parameters": {"item_id": {"example": 1}},
        },
        {
            "route": "/items",
            "method": "POST",
            "handler": "create_item",
            "expected_http_status": 201,
            "request_payload": {"name": "Runtime item"},
        },
    ]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert [target.test_case_id for target in plan.targets] == [
        "TC-CREATE",
        "TC-GET",
    ]
    creator, dependent = plan.targets
    assert creator.traceability["identifier_fields"] == ["item_id"]
    assert dependent.path_parameters == {"item_id": "captured:item_id"}
    assert dependent.traceability["depends_on"] == {
        "test_case_id": "TC-CREATE",
        "method": "POST",
        "route": "/items",
        "identifier_fields": ["item_id"],
    }


def test_preparation_reports_unresolved_payload() -> None:
    suite = [_case("TC-1", {"symbol": "create_project"})]
    stage3 = {
        "api_endpoints": [{
            "route": "/projects",
            "method": "POST",
            "handler": "create_project",
            "expected_http_status": 201,
            "request_type": "ProjectCreate",
        }],
        "data_models": [{"name": "ProjectCreate", "fields": ["name"]}],
    }

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert [issue.code for issue in plan.issues] == [
        "request_payload_unresolved"
    ]


def test_preparation_reports_unresolved_path_parameters() -> None:
    suite = [_case("TC-1", {"symbol": "get_project"})]
    stage3 = {"api_endpoints": [{
        "route": "/projects/{project_id}",
        "method": "GET",
        "handler": "get_project",
        "expected_http_status": 200,
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert [issue.code for issue in plan.issues] == [
        "path_parameters_unresolved"
    ]
    assert "project_id" in plan.issues[0].message


def test_preparation_consumes_enriched_stage3_schema_metadata() -> None:
    suite = [_case("TC-1", {"route": "/projects", "symbol": "create"})]
    stage3 = {
        "api_endpoints": [{
            "route": "/projects",
            "method": "POST",
            "handler": "create",
            "request_model": "ProjectCreate",
            "response_model": "ProjectResponse",
            "success_status_codes": [201],
            "error_status_codes": [],
            "exception_status_mappings": [],
        }],
        "pydantic_schemas": [
            {
                "name": "ProjectCreate",
                "file": "schemas.py",
                "fields": [
                    {
                        "name": "name", "type": "str", "required": True,
                        "optional": False, "has_default": False,
                        "default": None, "examples": ["Documented project"],
                    },
                    {
                        "name": "active", "type": "bool", "required": False,
                        "optional": False, "has_default": True,
                        "default": True, "examples": [],
                    },
                ],
                "examples": [],
            },
            {
                "name": "ProjectResponse",
                "file": "schemas.py",
                "fields": [],
                "examples": [{"name": "Documented project", "active": True}],
            },
        ],
    }

    plan = RuntimePreparationService().prepare(suite, stage3)

    target = plan.targets[0]
    assert target.executable is True
    assert target.expected_http_status == 201
    assert target.request_payload == {
        "name": "Documented project", "active": True
    }
    assert target.expected_response == {
        "name": "Documented project", "active": True
    }
    assert target.issues == []


def test_preparation_uses_matching_exception_status_and_explicit_route() -> None:
    case = _case("TC-1", {
        "route": "/login",
        "symbol": "login",
        "api_routes": [
            {"route": "/register", "method": "POST", "handler": "register"},
            {"route": "/login", "method": "POST", "handler": "login"},
        ],
    })
    case.update({
        "category": "negative",
        "title": "Reject unknown login",
        "expected_results": ["InvalidCredentialsException is raised"],
    })
    stage3 = {
        "api_endpoints": [
            {
                "route": "/register", "method": "POST",
                "handler": "register", "success_status_codes": [201],
            },
            {
                "route": "/login",
                "method": "POST",
                "handler": "login",
                "request_model": "LoginRequest",
                "response_model": "TokenResponse",
                "success_status_codes": [],
                "error_status_codes": [401],
                "exception_status_mappings": [{
                    "exception": "InvalidCredentialsException",
                    "status_code": 401,
                }],
            },
        ],
        "pydantic_schemas": [{
            "name": "LoginRequest",
            "file": "schemas.py",
            "fields": [],
            "examples": [{
                "email": "explicit@example.com",
                "password": "explicit-password",
            }],
        }],
    }

    plan = RuntimePreparationService().prepare([case], stage3)

    target = plan.targets[0]
    assert target.route == "/login"
    assert target.expected_http_status == 401
    assert target.request_payload == {
        "email": "explicit@example.com",
        "password": "explicit-password",
    }
    assert target.expected_response is None
    assert target.executable is True


def test_endpoint_selection_does_not_override_unknown_handler_with_route() -> None:
    trace = {
        "route": "/login",
        "method": "POST",
        "symbol": "login_user",
        "api_routes": [
            {"route": "/register", "method": "POST", "handler": "register"},
            {"route": "/login", "method": "POST", "handler": "login"},
            {
                "route": "/accounts/{user_id}",
                "method": "POST",
                "handler": "create_account",
            },
        ],
    }
    endpoints = [
        {"route": "/register", "method": "POST", "handler": "register"},
        {"route": "/login", "method": "POST", "handler": "login"},
        {
            "route": "/accounts/{user_id}",
            "method": "POST",
            "handler": "create_account",
        },
    ]

    endpoint = RuntimePreparationService._exact_endpoint(trace, endpoints)

    assert endpoint is None


def test_endpoint_selection_uses_exact_symbol_before_candidate_routes() -> None:
    trace = {
        "symbol": "login",
        "api_routes": [
            {"route": "/register", "method": "POST", "handler": "register"},
            {"route": "/login", "method": "POST", "handler": "login"},
        ],
    }
    endpoints = [
        {"route": "/register", "method": "POST", "handler": "register"},
        {"route": "/login", "method": "POST", "handler": "login"},
    ]

    endpoint = RuntimePreparationService._exact_endpoint(trace, endpoints)

    assert endpoint is not None
    assert endpoint["route"] == "/login"


def test_endpoint_selection_preserves_candidate_route_order() -> None:
    trace = {
        "api_routes": [
            {"route": "/login", "method": "POST"},
            {"route": "/register", "method": "POST"},
        ],
    }
    endpoints = [
        {"route": "/register", "method": "POST", "handler": "register"},
        {"route": "/login", "method": "POST", "handler": "login"},
    ]

    endpoint = RuntimePreparationService._exact_endpoint(trace, endpoints)

    assert endpoint is not None
    assert endpoint["route"] == "/login"


@pytest.mark.parametrize("method", ["DELETE", "PUT", "POST"])
def test_endpoint_resolution_preserves_exact_http_method(method: str) -> None:
    handler = f"{method.lower()}_item"
    suite = [_case("TC-METHOD", {
        "symbol": handler,
        "method": method,
        "route": "/items/{item_id}",
        "path_parameters": {"item_id": 1},
        "request_payload": {"name": "example"},
    })]
    stage3 = {"api_endpoints": [
        {
            "route": "/items/{item_id}",
            "method": "GET",
            "handler": "read_item",
            "success_status_codes": [200],
        },
        {
            "route": "/items/{item_id}",
            "method": method,
            "handler": handler,
            "success_status_codes": [200],
        },
    ]}

    target = RuntimePreparationService().prepare(suite, stage3).targets[0]

    assert target.http_method == method
    assert target.http_method != "GET"
    assert target.executable is True


def test_repository_symbol_is_not_promoted_from_call_graph_route() -> None:
    suite = [_case("TC-REPOSITORY", {
        "file": "app/repositories/items.py",
        "symbol": "delete_item_repository",
        "api_routes": [{
            "route": "/items/{item_id}",
            "method": "DELETE",
            "handler": "delete_item",
        }],
    })]
    stage3 = {"api_endpoints": [{
        "route": "/items/{item_id}",
        "method": "DELETE",
        "handler": "delete_item",
        "success_status_codes": [204],
    }]}

    target = RuntimePreparationService().prepare(suite, stage3).targets[0]

    assert target.classification == "UNIT"
    assert target.http_method is None
    assert target.executable is False
    assert [issue.code for issue in target.issues] == ["non_http_test"]


def test_missing_method_is_unresolved_without_get_fallback() -> None:
    suite = [_case("TC-METHOD-MISSING", {
        "route": "/items/{item_id}",
    })]
    stage3 = {"api_endpoints": [
        {
            "route": "/items/{item_id}",
            "method": "GET",
            "handler": "read_item",
        },
        {
            "route": "/items/{item_id}",
            "method": "DELETE",
            "handler": "delete_item",
        },
    ]}

    target = RuntimePreparationService().prepare(suite, stage3).targets[0]

    assert target.classification == "HTTP"
    assert target.route == "/items/{item_id}"
    assert target.http_method is None
    assert target.executable is False
    assert [issue.code for issue in target.issues] == [
        "http_method_unresolved"
    ]


def test_preparation_synthesizes_required_structured_request_field() -> None:
    suite = [_case("TC-1", {"route": "/projects", "symbol": "create"})]
    stage3 = {
        "api_endpoints": [{
            "route": "/projects",
            "method": "POST",
            "handler": "create",
            "request_model": "ProjectCreate",
            "success_status_codes": [201],
        }],
        "pydantic_schemas": [{
            "name": "ProjectCreate",
            "file": "schemas.py",
            "fields": [{
                "name": "name", "type": "str", "required": True,
                "optional": False, "has_default": False,
                "default": None, "examples": [],
            }],
            "examples": [],
        }],
    }

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].request_payload == {"name": "example"}
    assert plan.targets[0].expected_http_status == 201
    assert plan.issues == []


def test_status_resolution_accepts_single_singular_status() -> None:
    suite = [_case("TC-STATUS-1", {"symbol": "list_accounts"})]
    stage3 = {"api_endpoints": [{
        "route": "/accounts",
        "method": "GET",
        "handler": "list_accounts",
        "success_status_code": 204,
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].expected_http_status == 204


def test_status_resolution_selects_from_multiple_success_statuses() -> None:
    suite = [_case("TC-STATUS-2", {"symbol": "create_account"})]
    stage3 = {"api_endpoints": [{
        "route": "/accounts",
        "method": "GET",
        "handler": "create_account",
        "success_status_codes": [204, 201, 200],
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].expected_http_status == 200


def test_status_resolution_selects_from_multiple_error_statuses() -> None:
    case = _case("TC-STATUS-3", {"symbol": "read_account"})
    case["category"] = "negative"
    stage3 = {"api_endpoints": [{
        "route": "/accounts/{account_id}",
        "method": "GET",
        "handler": "read_account",
        "error_status_codes": [500, 422, 404, 401],
    }]}

    plan = RuntimePreparationService().prepare([case], stage3)

    assert plan.targets[0].expected_http_status == 401


def test_boundary_status_resolution_uses_endpoint_success_status() -> None:
    case = _case("TC-STATUS-4", {"symbol": "update_account"})
    case["category"] = "boundary"
    stage3 = {"api_endpoints": [{
        "route": "/accounts",
        "method": "GET",
        "handler": "update_account",
        "success_status_codes": [204, 201],
        "error_status_codes": [400],
    }]}

    plan = RuntimePreparationService().prepare([case], stage3)

    assert plan.targets[0].expected_http_status == 201


def test_explicit_expected_http_status_overrides_inferred_statuses() -> None:
    suite = [_case("TC-STATUS-5", {
        "symbol": "create_account",
        "expected_http_status": 202,
    })]
    stage3 = {"api_endpoints": [{
        "route": "/accounts",
        "method": "GET",
        "handler": "create_account",
        "success_status_codes": [200, 201],
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].expected_http_status == 202


def test_helper_function_is_non_http_even_with_related_route() -> None:
    suite = [_case("TC-NON-HTTP-1", {
        "symbol": "get_db",
        "route": "/accounts/{account_id}",
        "method": "GET",
    })]
    stage3 = {"api_endpoints": [{
        "route": "/accounts/{account_id}",
        "method": "GET",
        "handler": "read_account",
        "success_status_codes": [200],
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    target = plan.targets[0]
    assert target.executable is False
    assert target.expected_http_status is None
    assert [issue.code for issue in target.issues] == ["non_http_test"]


def test_utility_function_is_non_http() -> None:
    suite = [_case("TC-NON-HTTP-2", {
        "file": "app/utils.py",
        "symbol": "calculate_interest",
    })]

    plan = RuntimePreparationService().prepare(
        suite,
        {"api_endpoints": []},
    )

    assert plan.targets[0].expected_http_status is None
    assert [issue.code for issue in plan.issues] == ["non_http_test"]


def test_service_function_is_non_http() -> None:
    suite = [_case("TC-NON-HTTP-3", {
        "file": "app/services/accounts.py",
        "symbol": "create_account_service",
    })]
    stage3 = {"api_endpoints": [{
        "route": "/accounts",
        "method": "POST",
        "handler": "create_account",
        "success_status_codes": [],
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].expected_http_status is None
    assert [issue.code for issue in plan.issues] == ["non_http_test"]


def test_http_endpoint_detection_uses_stage3_route_without_symbol() -> None:
    suite = [_case("TC-HTTP-1", {
        "route": "/health",
        "method": "GET",
    })]
    stage3 = {"api_endpoints": [{
        "route": "/health",
        "method": "GET",
        "handler": "health",
        "success_status_codes": [],
    }]}

    plan = RuntimePreparationService().prepare(suite, stage3)

    target = plan.targets[0]
    assert target.route == "/health"
    assert target.http_method == "GET"
    assert target.expected_http_status == 200
    assert target.executable is True


def _schema_value(
    fields: list[dict],
    examples: list | None = None,
):
    return RuntimePreparationService._structured_model_value(
        [{
            "name": "RequestModel",
            "file": "schemas.py",
            "fields": fields,
            "examples": examples or [],
        }],
        "RequestModel",
    )


def _field(
    name: str,
    field_type: str,
    *,
    required: bool = True,
    optional: bool = False,
    has_default: bool = False,
    default=None,
    examples: list | None = None,
) -> dict:
    return {
        "name": name,
        "type": field_type,
        "required": required,
        "optional": optional,
        "has_default": has_default,
        "default": default,
        "examples": examples or [],
    }


def test_payload_uses_schema_example() -> None:
    assert _schema_value(
        [_field("name", "str")],
        examples=[{"name": "from-schema"}],
    ) == {"name": "from-schema"}


def test_explicit_trace_payload_overrides_schema_example() -> None:
    suite = [_case("TC-PAYLOAD-EXPLICIT", {
        "symbol": "create_project",
        "request_payload": {"name": "from-trace"},
    })]
    stage3 = {
        "api_endpoints": [{
            "route": "/projects",
            "method": "POST",
            "handler": "create_project",
            "request_model": "RequestModel",
            "success_status_codes": [200],
        }],
        "pydantic_schemas": [{
            "name": "RequestModel",
            "file": "schemas.py",
            "fields": [_field("name", "str")],
            "examples": [{"name": "from-schema"}],
        }],
    }

    plan = RuntimePreparationService().prepare(suite, stage3)

    assert plan.targets[0].request_payload == {"name": "from-trace"}


def test_payload_uses_field_example() -> None:
    assert _schema_value([
        _field("name", "str", examples=["from-field"]),
    ]) == {"name": "from-field"}


def test_payload_uses_explicit_default() -> None:
    assert _schema_value([
        _field(
            "retries",
            "int",
            required=False,
            has_default=True,
            default=3,
        ),
    ]) == {"retries": 3}


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        ("str", "example"),
        ("int", 1),
        ("float", 1.0),
        ("bool", True),
        ("UUID", "00000000-0000-0000-0000-000000000001"),
        ("EmailStr", "user@example.com"),
        ("date", "2026-01-01"),
        ("datetime", "2026-01-01T00:00:00Z"),
        ("list[str]", []),
        ("dict[str, int]", {}),
    ],
    ids=[
        "string", "integer", "float", "boolean", "uuid", "email", "date",
        "datetime", "list", "dict",
    ],
)
def test_payload_synthesizes_required_field_types(
    field_type: str,
    expected,
) -> None:
    assert _schema_value([
        _field("value", field_type),
    ]) == {"value": expected}


def test_payload_omits_optional_field_without_example_or_default() -> None:
    assert _schema_value([
        _field("name", "str"),
        _field(
            "nickname",
            "str | None",
            required=False,
            optional=True,
        ),
    ]) == {"name": "example"}


def test_payload_synthesizes_mixed_schema_deterministically() -> None:
    assert _schema_value([
        _field("email", "EmailStr"),
        _field("age", "int"),
        _field("active", "bool", examples=[False]),
        _field(
            "score",
            "float",
            required=False,
            has_default=True,
            default=2.5,
        ),
        _field("tags", "list[str]"),
        _field("metadata", "dict[str, str]"),
        _field("state", "Literal['new', 'active']"),
        _field(
            "nickname",
            "str | None",
            required=False,
            optional=True,
        ),
    ]) == {
        "email": "user@example.com",
        "age": 1,
        "active": False,
        "score": 2.5,
        "tags": [],
        "metadata": {},
        "state": "new",
    }
