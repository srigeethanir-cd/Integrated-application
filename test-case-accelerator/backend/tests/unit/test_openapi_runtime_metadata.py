import json
from unittest.mock import Mock, patch

from app.schemas.runtime_preparation import RuntimeExecutionTarget
from app.services.runtime.openapi_metadata_service import OpenAPIMetadataService
from app.services.runtime.test_file_builder import TestFileBuilder


def _openapi_response(document: dict) -> Mock:
    response = Mock()
    response.read.return_value = json.dumps(document).encode()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


def test_openapi_completes_request_parameters_and_response_metadata() -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-HTTP",
        classification="HTTP",
        route="/users/{user_id}",
        http_method="PATCH",
        executable=False,
        issues=[{
            "test_case_id": "TC-HTTP",
            "code": "request_payload_unresolved",
            "message": "Missing request schema",
        }],
    )
    document = {
        "paths": {"/users/{user_id}": {"patch": {
            "parameters": [
                {
                    "name": "user_id", "in": "path", "required": True,
                    "schema": {"type": "integer", "example": 7},
                },
                {
                    "name": "notify", "in": "query", "required": True,
                    "schema": {"type": "boolean", "default": True},
                },
            ],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {
                    "type": "object", "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                }}},
            },
            "responses": {"200": {"content": {"application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                },
            }}}},
        }}},
    }

    with patch(
        "app.services.runtime.openapi_metadata_service.urlopen",
        return_value=_openapi_response(document),
    ):
        completed, error = OpenAPIMetadataService().complete(
            [target], base_url="http://backend"
        )

    assert error is None
    assert completed[0].executable is True
    assert completed[0].path_parameters == {"user_id": 7}
    assert completed[0].query_parameters == {"notify": True}
    assert completed[0].request_payload == {"name": "example"}
    assert completed[0].expected_http_status == 200
    assert completed[0].expected_response_fields == ["id", "name"]


def _obsolete_generated_http_request_uses_persisted_headers_and_response_fields(
    tmp_path,
) -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-AUTH",
        classification="HTTP",
        route="/me",
        http_method="GET",
        expected_http_status=200,
        required_headers={"Authorization": "Bearer persisted-token"},
        authentication_required=True,
        authentication_schemes=["OAuth2PasswordBearer"],
        expected_response_fields=["id"],
        executable=True,
    )

    result = TestFileBuilder().build(
        [target], workspace=tmp_path, base_url="http://backend"
    )
    generated = result.test_file.read_text(encoding="utf-8")

    assert "Bearer persisted-token" in generated
    assert "Expected response fields missing" in generated


def test_openapi_preserves_originally_executable_status_when_endpoint_absent() -> None:
    # Target marked executable by Runtime Preparation
    target = RuntimeExecutionTarget(
        test_case_id="TC-PREPARED-EXEC",
        classification="HTTP",
        route="/business/orders",
        http_method="POST",
        expected_http_status=201,
        request_payload={"item": "Widget"},
        executable=True,
        issues=[],
    )

    # OpenAPI document from backend (e.g. Accelerator backend) without business endpoints
    document = {
        "info": {"title": "Test Case Accelerator"},
        "paths": {
            "/projects/upload": {"post": {}},
            "/projects/pipeline": {"get": {}},
        },
    }

    with patch(
        "app.services.runtime.openapi_metadata_service.urlopen",
        return_value=_openapi_response(document),
    ):
        completed, error = OpenAPIMetadataService().complete(
            [target], base_url="http://127.0.0.1:8000"
        )

    assert error is None
    assert completed[0].executable is True
    assert completed[0].issues == []
    assert completed[0].route == "/business/orders"


def test_openapi_route_normalization_matches_placeholders_and_prefixes() -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-NORM",
        classification="HTTP",
        route="/api/v1/users/{user_id}/",
        http_method="GET",
        executable=False,
        issues=[{
            "test_case_id": "TC-NORM",
            "code": "missing_expected_status",
            "message": "Missing expected HTTP status",
        }],
    )

    document = {
        "paths": {
            "/users/{id}": {
                "get": {
                    "responses": {"200": {"description": "OK"}},
                }
            }
        }
    }

    with patch(
        "app.services.runtime.openapi_metadata_service.urlopen",
        return_value=_openapi_response(document),
    ):
        completed, error = OpenAPIMetadataService().complete(
            [target], base_url="http://backend"
        )

    assert error is None
    assert completed[0].executable is True
    assert completed[0].expected_http_status == 200


def test_openapi_does_not_substitute_get_for_missing_http_method() -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-METHOD-MISSING",
        classification="HTTP",
        route="/items/{item_id}",
        http_method=None,
        executable=False,
        issues=[{
            "test_case_id": "TC-METHOD-MISSING",
            "code": "http_method_unresolved",
            "message": "No exact HTTP method reference could be resolved",
        }],
    )
    document = {
        "paths": {
            "/items/{item_id}": {
                "get": {"responses": {"200": {"description": "OK"}}},
            }
        }
    }

    completed, error = OpenAPIMetadataService().complete(
        [target], base_url="http://backend", document=document
    )

    assert error is None
    assert completed[0].http_method is None
    assert completed[0].executable is False
    assert [issue.code for issue in completed[0].issues] == [
        "http_method_unresolved"
    ]


def test_openapi_preserves_non_http_classification_and_issue() -> None:
    target = RuntimeExecutionTarget(
        test_case_id="TC-UNIT",
        classification="UNIT",
        executable=False,
        issues=[{
            "test_case_id": "TC-UNIT",
            "code": "non_http_test",
            "message": "Internal helper function (HTTP validation not applicable)",
        }],
    )

    completed, error = OpenAPIMetadataService().complete(
        [target],
        base_url="http://backend",
        document={"paths": {"/items": {"get": {}}}},
    )

    assert error is None
    assert completed[0].classification == "UNIT"
    assert completed[0].executable is False
    assert completed[0].issues[0].code == "non_http_test"
    assert completed[0].issues[0].message == (
        "Internal helper function (HTTP validation not applicable)"
    )
