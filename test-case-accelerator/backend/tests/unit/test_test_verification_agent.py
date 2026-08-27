from unittest.mock import Mock

import httpx
import pytest
from openai import RateLimitError

from app.agents.semantic_verification.agent import (
    TestVerificationAgent as VerificationAgent,
)
from app.schemas.test_verification import (
    LLMVerificationBatch as VerificationBatch,
    TestCaseVerification as CaseVerification,
    VerificationFinding as Finding,
)


def _case(**overrides):
    value = {
        "id": "TC-1",
        "title": "Create a project",
        "description": "Create through the API",
        "category": "integration",
        "priority": "high",
        "severity": "major",
        "steps": ["POST a project"],
        "expected_results": ["The project is returned"],
        "traceability": {
            "file": "app/api/projects.py",
            "symbol": "create_project",
            "route": "/projects",
            "method": "POST",
            "request_model": "ProjectCreate",
            "response_model": "ProjectResponse",
        },
    }
    value.update(overrides)
    return value


def _stage3():
    return {
        "api_endpoints": [
            {
                "method": "POST",
                "route": "/projects",
                "handler": "create_project",
                "file": "app/api/projects.py",
                "request_type": "ProjectCreate",
                "response_type": "ProjectResponse",
            }
        ]
    }


def _sources():
    return [
        {
            "path": "app/api/projects.py",
            "functions": ["create_project"],
            "classes": [],
            "content": "@router.post('/projects')\ndef create_project():\n    pass",
        }
    ]


def test_rule_verification_confirms_endpoint_file_symbol_and_models() -> None:
    result = VerificationAgent().verify([_case()], _stage3(), _sources())

    verification = result["results"][0]
    assert verification["status"] == "Verified"
    assert verification["confidence"] >= 0.8
    assert verification["verification_path"] == "Rule-Based"
    assert verification["evidence"][0]["file"] == "app/api/projects.py"
    assert any(item["line"] == 2 for item in verification["evidence"])


def test_rule_verification_rejects_real_symbol_cited_from_wrong_file() -> None:
    case = _case(
        title="Validate Minimal Email Format",
        traceability={"file": "utils.py", "symbol": "validate_email", "line": 3},
    )
    sources = [
        {
            "path": "utils.py",
            # Deliberately stale discovery metadata: AST must be authoritative.
            "functions": ["validate_email", "generate_account_number", "calculate_interest"],
            "classes": [],
            "content": "def generate_account_number():\n    return '1'\n\ndef calculate_interest():\n    return 0\n",
        },
        {
            "path": "validator.py",
            "functions": ["validate_email"],
            "classes": [],
            "content": "def validate_email(value):\n    return '@' in value\n",
        },
    ]

    result = VerificationAgent().verify([case], {"api_endpoints": []}, sources)

    verification = result["results"][0]
    assert verification["status"] == "Failed"
    finding = next(item for item in verification["findings"] if item["check"] == "symbol_exists")
    assert finding["status"] == "Failed"
    assert not any(item["symbol"] == "validate_email" for item in finding["evidence"])


def test_rule_verification_allows_one_outcome_for_multiple_actions() -> None:
    case = _case(
        steps=["one", "two"],
        expected_results=["one"],
        traceability={"route": "/missing", "method": "GET"},
    )

    result = VerificationAgent().verify([case], _stage3(), _sources())

    assert result["results"][0]["status"] == "Failed"
    checks = {item["check"] for item in result["results"][0]["findings"]}
    assert "test_structure" not in checks
    assert "endpoint_exists" in checks


@pytest.mark.parametrize(
    ("steps", "expected_results"),
    [
        (
            [
                "Open the application",
                "Navigate to the Projects page",
                "Click Create Project",
            ],
            ["The project form is displayed"],
        ),
        (
            [
                "1. Log in as an administrator",
                "2. Submit a valid project",
                "3. Verify the project appears in the list",
            ],
            ["The project is accepted", "The project appears in the list"],
        ),
        (
            ["Given an authenticated user", "Send POST /projects"],
            ["ProjectResponse is returned"],
        ),
    ],
)
def test_structure_allows_setup_navigation_without_expected_results(
    steps, expected_results
) -> None:
    case = _case(steps=steps, expected_results=expected_results)

    result = VerificationAgent().verify([case], _stage3(), _sources())

    checks = {item["check"] for item in result["results"][0]["findings"]}
    assert "test_structure" not in checks


def test_structure_allows_shared_outcome_for_action_sequence() -> None:
    case = _case(
        steps=[
            "Open the application",
            "Submit a valid project",
            "Verify the project appears in the list",
        ],
        expected_results=["The project is accepted"],
    )

    result = VerificationAgent().verify([case], _stage3(), _sources())

    checks = {item["check"] for item in result["results"][0]["findings"]}
    assert "test_structure" not in checks


def test_structure_rejects_actions_without_a_meaningful_outcome() -> None:
    case = _case(
        steps=[
            "Open the application",
            "Submit a valid project",
            "Verify the project appears in the list",
        ],
        expected_results=["   "],
    )

    result = VerificationAgent().verify([case], _stage3(), _sources())

    finding = next(
        item
        for item in result["results"][0]["findings"]
        if item["check"] == "test_structure"
    )
    assert finding["status"] == "Failed"
    assert finding["detail"].startswith("2 action or verification step")


def test_hybrid_verification_requests_behavioral_contract_checks() -> None:
    provider = Mock()
    provider.generate_structured.return_value = VerificationBatch(
        verifications=[
            CaseVerification(
                test_case_id="TC-1",
                status="Verified",
                confidence=0.8,
                evidence=[],
                findings=[],
            )
        ]
    )

    result = VerificationAgent(client=provider, rule_confidence_threshold=1).verify([_case()], _stage3(), _sources())

    request = provider.generate_structured.call_args.kwargs
    assert request["response_model"] is VerificationBatch
    assert "status codes" in request["system_prompt"]
    assert "exception handling" in request["system_prompt"]
    assert result["results"][0]["status"] == "Verified"


def test_hybrid_verification_falls_back_for_missing_provider_results() -> None:
    provider = Mock()
    provider.generate_structured.return_value = VerificationBatch(verifications=[])

    result = VerificationAgent(client=provider, retry_base_delay=0, rule_confidence_threshold=1).verify(
        [_case()], _stage3(), _sources()
    )

    assert provider.generate_structured.call_count == 3
    assert result["results"][0]["status"] == "Partial"
    assert result["results"][0]["confidence"] == 0.5
    assert result["results"][0]["findings"][-1]["check"] == "provider_verification"


def test_rate_limit_is_retried_and_then_merged() -> None:
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat"),
        headers={"retry-after": "1"},
    )
    rate_limit = RateLimitError("rate limited", response=response, body=None)
    provider = Mock()
    provider.generate_structured.side_effect = [
        rate_limit,
        VerificationBatch(
            verifications=[
                CaseVerification(
                    test_case_id="TC-1",
                    status="Verified",
                    confidence=0.8,
                    evidence=[],
                    findings=[],
                )
            ]
        ),
    ]
    sleep = Mock()

    result = VerificationAgent(client=provider, sleep=sleep, rule_confidence_threshold=1).verify(
        [_case()], _stage3(), _sources()
    )

    assert provider.generate_structured.call_count == 2
    sleep.assert_called_once_with(1.0)
    assert result["results"][0]["status"] == "Verified"


def test_exhausted_rate_limit_returns_partial_rule_results() -> None:
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat"),
    )
    provider = Mock()
    provider.generate_structured.side_effect = RateLimitError(
        "rate limited", response=response, body=None
    )

    result = VerificationAgent(client=provider, retry_base_delay=0, rule_confidence_threshold=1).verify(
        [_case()], _stage3(), _sources()
    )

    assert provider.generate_structured.call_count == 3
    assert result["summary"] == {"verified": 0, "partial": 1, "failed": 0}


def test_malformed_provider_response_returns_partial_rule_results() -> None:
    provider = Mock()
    provider.generate_structured.return_value = {"not_verifications": []}

    result = VerificationAgent(client=provider, max_provider_attempts=1, rule_confidence_threshold=1).verify(
        [_case()], _stage3(), _sources()
    )

    assert result["results"][0]["status"] == "Partial"


def test_same_title_is_not_duplicate_when_behavior_differs() -> None:
    second = _case(
        id="TC-2", steps=["Different step"], expected_results=["Different result"]
    )

    result = VerificationAgent().verify([_case(), second], _stage3(), _sources())

    assert [item["status"] for item in result["results"]] == ["Verified", "Verified"]
    assert all(
        not any(finding["check"] == "duplicate" for finding in item["findings"])
        for item in result["results"]
    )


def test_router_and_service_symbols_are_not_duplicates() -> None:
    router = _case(
        id="TC-ROUTER",
        title="Authenticate user",
        traceability={"file": "app/routers/auth.py", "symbol": "authenticate_user"},
    )
    service = _case(
        id="TC-SERVICE",
        title="Authenticate user",
        traceability={"file": "app/services/auth.py", "symbol": "authenticate_user"},
    )
    sources = [
        {
            "path": "app/routers/auth.py",
            "functions": ["authenticate_user"],
            "classes": [],
            "content": "def authenticate_user():\n    return True\n",
        },
        {
            "path": "app/services/auth.py",
            "functions": ["authenticate_user"],
            "classes": [],
            "content": "def authenticate_user():\n    return True\n",
        },
    ]

    result = VerificationAgent().verify(
        [router, service], {"api_endpoints": []}, sources
    )

    assert all(
        not any(finding["check"] == "duplicate" for finding in item["findings"])
        for item in result["results"]
    )


def test_same_target_behavior_and_category_is_duplicate() -> None:
    duplicate = _case(id="TC-2")

    result = VerificationAgent().verify(
        [_case(), duplicate], _stage3(), _sources()
    )

    assert [item["status"] for item in result["results"]] == ["Failed", "Failed"]
    assert all(
        any(
            finding["check"] == "duplicate"
            and "same production target" in finding["detail"]
            for finding in item["findings"]
        )
        for item in result["results"]
    )


def test_summary_counts_each_status_and_total_verified() -> None:
    rule_engine = Mock()
    rule_engine.verify.return_value = [
        CaseVerification(
            test_case_id="TC-1",
            status="Verified",
            confidence=0.9,
            evidence=[],
            findings=[],
        ),
        CaseVerification(
            test_case_id="TC-2",
            status="Partial",
            confidence=0.5,
            evidence=[],
            findings=[],
        ),
        CaseVerification(
            test_case_id="TC-3",
            status="Failed",
            confidence=0.9,
            evidence=[],
            findings=[],
        ),
    ]
    cases = [
        _case(),
        _case(
            id="TC-2",
            title="Update a project",
            steps=["PATCH a project"],
            expected_results=["The project is updated"],
        ),
        _case(
            id="TC-3",
            title="Delete a project",
            steps=["DELETE a project"],
            expected_results=["The project is deleted"],
        ),
    ]

    result = VerificationAgent(rule_engine=rule_engine).verify(
        cases, _stage3(), _sources()
    )

    assert result["summary"] == {"verified": 0, "partial": 2, "failed": 1}
    assert result["total_verified"] == 0


def test_merge_consolidates_each_check_with_deterministic_precedence() -> None:
    rule_engine = Mock()
    rule_engine.verify.return_value = [
        CaseVerification(
            test_case_id="TC-1",
            status="Partial",
            confidence=0.8,
            evidence=[],
            findings=[
                Finding(
                    check="endpoint_exists",
                    status="Verified",
                    detail="Rule found the endpoint",
                ),
                Finding(
                    check="validation",
                    status="Partial",
                    detail="Rule could not prove every validation",
                ),
            ],
        )
    ]
    provider = Mock()
    provider.generate_structured.return_value = VerificationBatch(
        verifications=[
            CaseVerification(
                test_case_id="TC-1",
                status="Failed",
                confidence=0.9,
                evidence=[],
                findings=[
                    Finding(
                        check="endpoint_exists",
                        status="Partial",
                        detail="Provider was uncertain",
                    ),
                    Finding(
                        check="endpoint_exists",
                        status="Failed",
                        detail="Provider found a route mismatch",
                    ),
                    Finding(
                        check="validation",
                        status="Verified",
                        detail="Provider found validation",
                    ),
                ],
            )
        ]
    )

    result = VerificationAgent(client=provider, rule_engine=rule_engine, rule_confidence_threshold=0.81).verify(
        [_case()], _stage3(), _sources()
    )

    verification = result["results"][0]
    findings = {item["check"]: item for item in verification["findings"]}
    assert len(verification["findings"]) == len(findings) == 2
    assert findings["endpoint_exists"]["status"] == "Failed"
    assert findings["endpoint_exists"]["detail"] == ("Provider found a route mismatch")
    assert findings["validation"]["status"] == "Partial"
    assert verification["status"] == "Failed"
    assert result["summary"] == {"verified": 0, "partial": 0, "failed": 1}
