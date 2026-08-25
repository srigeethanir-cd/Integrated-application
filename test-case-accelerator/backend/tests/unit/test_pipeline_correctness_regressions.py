from unittest.mock import Mock
import logging

from pydantic import ValidationError
import pytest

from app.agents.code_understanding.agent import (
    CodeUnderstandingAgent,
    CodeUnderstandingContext,
    CodeUnderstandingResult,
)
from app.agents.semantic_verification.agent import TestVerificationAgent as VerificationAgent
from app.agents.semantic_verification.rule_engine import VerificationRuleEngine
from app.agents.test_generation.deduplicator import Deduplicator
from app.agents.test_generation.test_generation_agent import TestGenerationAgent as GenerationAgent
from app.schemas.test_case import TestCase as Case, TestCaseBatch as CaseBatch
from app.schemas.test_verification import LLMVerificationBatch, TestCaseVerification as CaseVerification


def case(**values) -> Case:
    payload = {
        "id": "TC-1", "title": "Call calculate_interest",
        "description": "Exercise calculate_interest(-100)",
        "category": "negative", "priority": "high", "severity": "major",
        "steps": ["Call calculate_interest(-100)"],
        "expected_results": ["The correct interest tier is returned"],
        "traceability": {"file": "bank.py", "symbol": "calculate_interest"},
    }
    payload.update(values)
    return Case.model_validate(payload)


def test_ambiguous_behavior_escalates_to_semantic_verification() -> None:
    provider = Mock()
    provider.generate_structured.return_value = LLMVerificationBatch(
        verifications=[CaseVerification(
            test_case_id="TC-1", status="Verified", confidence=.85,
            evidence=[{"file": "bank.py", "symbol": "calculate_interest", "line": 1, "detail": "Confirmed"}],
            findings=[],
        )]
    )
    sources = [{"path": "bank.py", "content": "def calculate_interest(balance):\n    if balance < 1000:\n        return 2\n    return 4"}]

    result = VerificationAgent(client=provider).verify([case()], {}, sources)

    provider.generate_structured.assert_called_once()
    assert result["results"][0]["verification_path"] == "Rule+LLM"


def test_claimed_raise_absent_from_function_is_failed() -> None:
    sources = [{"path": "bank.py", "content": "def calculate_interest(balance):\n    if balance < 1000:\n        return 2\n    return 4"}]
    result = VerificationAgent().verify([
        case(expected_results=["Raises ValueError"])
    ], {}, sources)
    assert result["results"][0]["status"] == "Failed"


def test_evidence_resolves_invoked_create_account_not_traced_get_balance() -> None:
    sources = [{"path": "account.py", "content": "def create_account(name):\n    return name\n\ndef get_balance(name):\n    return 0"}]
    tested = case(
        title="Create account", description="create_account('A')",
        steps=["Call create_account('A')"], expected_results=["Returns the account"],
        traceability={"file": "account.py", "symbol": "get_balance"},
    )
    result = VerificationAgent(rule_confidence_threshold=0).verify([tested], {}, sources)
    evidence = result["results"][0]["evidence"]
    assert any(item["symbol"] == "create_account" and item["line"] == 1 for item in evidence)
    assert not any(item["symbol"] == "get_balance" for item in evidence)


def test_symbol_resolution_does_not_map_verify_password_to_hash_password() -> None:
    sources = [{
        "path": "auth.py",
        "content": (
            "def hash_password(value):\n    return 'hash'\n\n"
            "def verify_password(value, hashed):\n"
            "    return value == hashed\n"
        ),
    }]
    target = case(
        title="Verify password",
        steps=["Call verify_password('secret', 'hash')"],
        expected_results=["Returns false"],
        traceability={"file": "auth.py", "symbol": "verify_password"},
    )

    result = VerificationRuleEngine().verify([target], {}, sources)[0]

    assert result.evidence
    assert {item.symbol for item in result.evidence} == {"verify_password"}


def test_exception_class_resolution_does_not_map_to_endpoint_handler() -> None:
    sources = [{
        "path": "account.py",
        "content": (
            "class AccountNotFoundException(Exception):\n    pass\n\n"
            "def register():\n    return True\n"
        ),
    }]
    target = case(
        title="AccountNotFoundException is defined",
        steps=["Inspect AccountNotFoundException"],
        expected_results=["Exception class exists"],
        traceability={
            "file": "account.py",
            "symbol": "AccountNotFoundException",
        },
    )

    result = VerificationRuleEngine().verify([target], {}, sources)[0]

    assert result.status == "Verified"
    assert {item.symbol for item in result.evidence} == {
        "AccountNotFoundException"
    }


def test_endpoint_metadata_promotes_framework_default_behavior() -> None:
    sources = [{
        "path": "api.py",
        "content": (
            "def get_account():\n"
            "    return {'active': True}\n"
        ),
    }]
    stage3 = {"api_endpoints": [{
        "method": "GET", "route": "/accounts", "handler": "get_account",
        "file": "api.py", "response_model": "AccountResponse",
        "success_status_codes": [], "error_status_codes": [],
        "exception_status_mappings": [],
    }]}
    target = case(
        title="Get account returns HTTP 200",
        steps=["Send GET /accounts"],
        expected_results=["HTTP 200 is returned"],
        traceability={
            "file": "api.py", "symbol": "get_account",
            "route": "/accounts", "method": "GET",
        },
    )

    result = VerificationRuleEngine().verify([target], stage3, sources)[0]

    assert result.status == "Verified"
    assert any(
        item.check == "endpoint_behavior" and item.status == "Verified"
        for item in result.findings
    )


def test_password_helper_call_proves_boolean_behavior() -> None:
    sources = [{
        "path": "auth.py",
        "content": (
            "def verify_password(plain, hashed):\n"
            "    return pwd_context.verify(plain, hashed)\n"
        ),
    }]
    target = case(
        title="Verify matching password",
        steps=["Call verify_password('secret', 'hash')"],
        expected_results=["Returns true"],
        traceability={"file": "auth.py", "symbol": "verify_password"},
    )

    result = VerificationRuleEngine().verify([target], {}, sources)[0]

    assert result.status == "Verified"
    assert "password verification helper" in next(
        item.detail for item in result.findings
        if item.check == "behavior_semantics"
    )


def test_exception_constructor_status_is_verified_directly() -> None:
    sources = [{
        "path": "errors.py",
        "content": (
            "class AccountNotFoundException(HTTPException):\n"
            "    def __init__(self):\n"
            "        super().__init__(status_code=404, detail='missing')\n"
        ),
    }]
    target = case(
        title="AccountNotFoundException returns HTTP 404",
        steps=["Inspect AccountNotFoundException"],
        expected_results=["HTTP 404 is returned"],
        traceability={
            "file": "errors.py", "symbol": "AccountNotFoundException",
        },
    )

    result = VerificationRuleEngine().verify([target], {}, sources)[0]

    assert result.status == "Verified"
    assert {item.symbol for item in result.evidence} == {
        "AccountNotFoundException"
    }


def test_non_web_project_discards_hallucinated_http_tests() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch(test_cases=[
        case(title="Account endpoint returns HTTP 400", steps=["POST /accounts"], expected_results=["HTTP 400 is returned"])
    ])
    result = GenerationAgent(client=provider).generate({
        "api_endpoints": [],
        "test_targets": [{"symbol": "create_account", "file": "account.py", "behavior": "Create"}],
    })
    assert result["generated_test_cases"] == []


def test_semantic_email_duplicates_are_removed_without_collapsing_phone_values() -> None:
    email_one = case(id="E1", title="Reject user@examplecom", description="validate_email user@examplecom", steps=["Call validate_email('user@examplecom')"], expected_results=["Returns false"], traceability={"symbol": "validate_email"})
    email_two = case(id="E2", title="Reject user@example", description="validate_email user@example", steps=["Call validate_email('user@example')"], expected_results=["Returns false"], traceability={"symbol": "validate_email"})
    phone_one = case(id="P1", title="Accept phone 1234567890", description="validate_phone 1234567890", steps=["Call validate_phone('1234567890')"], expected_results=["Returns true"], traceability={"symbol": "validate_phone"})
    phone_two = case(id="P2", title="Accept phone 9876543210", description="validate_phone 9876543210", steps=["Call validate_phone('9876543210')"], expected_results=["Returns true"], traceability={"symbol": "validate_phone"})
    unique = Deduplicator().deduplicate([email_one, email_two, phone_one, phone_two])
    assert [item.id for item in unique] == ["E1", "P1", "P2"]


def test_verified_record_requires_content_and_evidence() -> None:
    with pytest.raises(ValidationError):
        case(steps=[])
    rule = Mock()
    rule.verify.return_value = [CaseVerification(
        test_case_id="TC-1", status="Verified", confidence=.95,
        evidence=[], findings=[],
    )]
    result = VerificationAgent(rule_engine=rule, rule_confidence_threshold=0).verify([case()], {}, [])
    assert result["results"][0]["status"] == "Partial"


def test_ast_enrichment_enumerates_numeric_partitions_guards_and_missing_keys() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CodeUnderstandingResult.model_validate({
        "project_summary": "Bank", "architecture": "Functions",
        "test_targets": [
            {"symbol": "transfer", "file": "bank.py", "behavior": "Transfer"},
            {"symbol": "create_account", "file": "bank.py", "behavior": "Create"},
            {"symbol": "get_balance", "file": "bank.py", "behavior": "Balance"},
        ],
    })
    context = CodeUnderstandingContext.model_validate({
        "project_id": "00000000-0000-0000-0000-000000000001",
        "dependency_run_id": "00000000-0000-0000-0000-000000000002",
        "files": [{"path": "bank.py", "language": "python", "content": (
            "accounts = {}\n"
            "def transfer(amount):\n    if amount == 0:\n        return False\n    return True\n"
            "def create_account(name):\n    if name in accounts:\n        return False\n    accounts[name] = 0\n"
            "def get_balance(name):\n    return accounts[name]\n"
        )}],
    })
    result = CodeUnderstandingAgent(provider).analyze(context)
    targets = {item.symbol: item for item in result.test_targets}
    assert {"amount < 0", "amount == 0", "amount > 0"}.issubset(targets["transfer"].branches)
    assert any("name in accounts" in item for item in targets["create_account"].branches)
    assert any("KeyError" in item for item in targets["get_balance"].edge_cases)


@pytest.mark.parametrize(
    "expected",
    [
        "login() returns False for an unknown user",
        "login() should return false for an incorrect password",
        "The result is False because credentials are incorrect",
        "Returns the value False",
        "login() always returns False for invalid credentials",
    ],
)
def test_login_explicit_false_returns_are_detected(expected: str) -> None:
    source = [{"path": "auth.py", "content": (
        "USERS = {'alice': 'secret'}\n"
        "def login(username, password):\n"
        "    if username not in USERS:\n        return False\n"
        "    if USERS[username] != password:\n        return False\n"
        "    return True\n"
    )}]
    tested = case(
        title="Incorrect login", description="login('alice', 'wrong')",
        steps=["Call login('alice', 'wrong')"], expected_results=[expected],
        traceability={"file": "auth.py", "symbol": "login"},
    )
    result = VerificationAgent(rule_confidence_threshold=0).verify([tested], {}, source)
    finding = next(
        item for item in result["results"][0]["findings"]
        if item["check"] == "behavior_semantics"
    )
    assert finding["status"] == "Verified"
    assert "guarded success/failure control flow" in finding["detail"]


def test_implicit_key_error_and_explicit_value_error_are_proven() -> None:
    source = [{"path": "account.py", "content": (
        "accounts = {}\n"
        "def get_balance(name):\n    return accounts[name]\n"
        "def create_account(balance):\n"
        "    if balance < 0:\n        raise ValueError('negative balance')\n"
        "    return balance\n"
    )}]
    key_case = case(
        id="KEY", title="Missing account", description="get_balance('missing')",
        steps=["Call get_balance('missing')"], expected_results=["Raises KeyError"],
        traceability={"file": "account.py", "symbol": "get_balance"},
    )
    value_case = case(
        id="VALUE", title="Negative balance", description="create_account(-1)",
        steps=["Call create_account(-1)"], expected_results=["Raises a validation exception"],
        traceability={"file": "account.py", "symbol": "create_account"},
    )
    result = VerificationAgent(rule_confidence_threshold=0).verify(
        [key_case, value_case], {}, source
    )
    assert [item["status"] for item in result["results"]] == ["Verified", "Verified"]
    assert "implicit exception path" in result["results"][0]["findings"][-1]["detail"]
    assert "ValueError" in result["results"][1]["findings"][-1]["detail"]


def test_disproven_exception_remains_failed_with_specific_message() -> None:
    source = [{"path": "bank.py", "content": "def calculate_interest(balance):\n    return 2"}]
    tested = case(expected_results=["Raises ValueError"])
    result = VerificationAgent(rule_confidence_threshold=0).verify([tested], {}, source)
    finding = next(
        item for item in result["results"][0]["findings"]
        if item["check"] == "behavior_semantics"
    )
    assert finding["status"] == "Failed"
    assert finding["detail"] == (
        "Claimed ValueError is not raised by calculate_interest for the specified "
        "input. Static analysis found normal return paths only."
    )


def test_cross_batch_business_scenario_duplicates_are_collapsed() -> None:
    scenarios = [
        case(id="TC-002", title="Negative initial balance", description="create_account with negative balance", steps=["Call create_account(-1)"], traceability={"symbol": "create_account"}, expected_results=["Raises ValueError"]),
        case(id="TC-102", title="Reject balance below zero", description="create_account balance below zero", steps=["Create account using a below-zero balance"], traceability={"symbol": "create_account"}, expected_results=["Raises ValueError"]),
        case(id="TC-011", title="Receiver absent", description="transfer to missing receiver", steps=["Transfer to a missing receiver"], traceability={"symbol": "transfer"}, expected_results=["Raises KeyError"]),
        case(id="TC-112", title="Unknown recipient", description="transfer when recipient does not exist", steps=["Transfer to an unknown recipient"], traceability={"symbol": "transfer"}, expected_results=["Raises KeyError"]),
        case(id="TC-012", title="Sender absent", description="transfer from missing sender", steps=["Transfer from a missing sender"], traceability={"symbol": "transfer"}, expected_results=["Raises KeyError"]),
        case(id="TC-205", title="Unknown sender", description="transfer when sender does not exist", steps=["Transfer from an unknown sender"], traceability={"symbol": "transfer"}, expected_results=["Raises KeyError"]),
        case(id="TC-006", title="Low funds", description="transfer with insufficient funds", steps=["Transfer more than available funds"], traceability={"symbol": "transfer"}, expected_results=["Returns false"]),
        case(id="TC-015", title="Balance too low", description="transfer when balance too low", steps=["Transfer when balance is too low"], traceability={"symbol": "transfer"}, expected_results=["Fails"]),
    ]
    unique = Deduplicator().deduplicate(scenarios)
    assert [item.id for item in unique] == ["TC-002", "TC-011", "TC-012", "TC-006"]


def test_deduplication_preserves_numeric_boundaries_and_test_categories() -> None:
    scenarios = [
        case(
            id="B-0", title="Minimum balance 0",
            description="transfer at minimum balance 0",
            steps=["Call transfer(0)"], category="boundary",
            traceability={"symbol": "transfer"},
            expected_results=["Returns true"],
        ),
        case(
            id="B-100", title="Maximum balance 100",
            description="transfer at maximum balance 100",
            steps=["Call transfer(100)"], category="boundary",
            traceability={"symbol": "transfer"},
            expected_results=["Returns true"],
        ),
        case(
            id="N-1", title="Reject negative transfer",
            description="transfer rejects -1",
            steps=["Call transfer(-1)"], category="negative",
            traceability={"symbol": "transfer"},
            expected_results=["Returns false"],
        ),
        case(
            id="S-1", title="Block unauthorized transfer",
            description="transfer rejects unauthorized input",
            steps=["Call transfer(-1) without authorization"], category="security",
            traceability={"symbol": "transfer"},
            expected_results=["Returns false"],
        ),
        case(
            id="E-1", title="Missing account exception",
            description="transfer from missing account",
            steps=["Call transfer(-1) for missing account"],
            category="exception/integration",
            traceability={"symbol": "transfer"},
            expected_results=["Raises KeyError"],
        ),
    ]

    unique = Deduplicator().deduplicate(scenarios)

    assert [item.id for item in unique] == [
        "B-0", "B-100", "N-1", "S-1", "E-1"
    ]


def test_deduplication_still_removes_true_duplicate_behavior() -> None:
    first = case(
        id="D-1", title="Reject missing receiver",
        description="transfer to missing receiver",
        steps=["Transfer to an unknown receiver"], category="negative",
        traceability={"symbol": "transfer"},
        expected_results=["Raises KeyError"],
    )
    duplicate = case(
        id="D-2", title="Unknown recipient",
        description="transfer when recipient does not exist",
        steps=["Call transfer for a nonexistent recipient"], category="negative",
        traceability={"symbol": "transfer"},
        expected_results=["Raises KeyError"],
    )

    assert Deduplicator().deduplicate([first, duplicate]) == [first]


def test_semantic_fallback_majority_emits_structured_warning(caplog) -> None:
    provider = Mock()
    provider.generate_structured.side_effect = RuntimeError("provider offline")
    source = [{"path": "bank.py", "content": "def calculate_interest(balance):\n    return balance"}]
    cases = [case(id=f"TC-{index}") for index in range(3)]

    with caplog.at_level(logging.WARNING):
        VerificationAgent(
            client=provider, max_provider_attempts=1,
            rule_confidence_threshold=1,
        ).verify(cases, {}, source)

    assert "fallback_percentage=100.00" in caplog.text
    assert "provider_failure_reason=RuntimeError" in caplog.text
    assert "affected_tests=3" in caplog.text
