from pathlib import Path
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.test_generation.deterministic_unit_generator import (
    DeterministicUnitTestGenerator,
)
from app.agents.code_understanding.agent import (
    CodeUnderstandingContext,
    SourceFileContext,
)
from app.agents.semantic_verification import agent as verification_agent
from app.schemas import test_case as test_case_schema
from app.services.code_understanding.static_analyzer import PythonStaticAnalyzer
from app.services.runtime.execution_manager import ExecutionManager, ExecutionOutcome
from app.services.runtime.pytest_runner import PytestRunner
from app.services.runtime.report_generator import ReportGenerator
from app.services.runtime.result_collector import ResultCollector
from app.services.runtime.runtime_preparation_service import RuntimePreparationService
from app.services.runtime.test_file_builder import TestFileBuilder
from app.services.runtime.runtime_validation_service import RuntimeValidationService
from app.database.models.code_understanding import CodeUnderstandingStatus


def _context() -> dict:
    return {
        "functions": [{
            "file": "calculator.py",
            "name": "add",
            "qualified_name": "calculator.add",
            "parameters": ["left", "right"],
            "is_async": False,
        }],
        "test_targets": [{
            "file": "calculator.py",
            "symbol": "add",
            "behavior": "Return the sum of two values",
            "dependencies": [],
        }],
        "api_endpoints": [{"method": "GET", "route": "/ignored"}],
    }


def test_stage4_generates_executable_unit_contract_without_http_metadata():
    result = DeterministicUnitTestGenerator().generate(_context())
    case = test_case_schema.TestCase.model_validate(result["generated_test_cases"][0])

    assert case.unit_test is not None
    assert case.unit_test.module == "calculator"
    assert case.unit_test.symbol == "add"
    assert case.traceability["test_kind"] == "unit"
    assert "route" not in case.traceability
    assert "http" not in case.unit_test.generated_code.casefold()


def test_runtime_preparation_keeps_unit_contract_executable():
    result = DeterministicUnitTestGenerator().generate(_context())
    cases = [test_case_schema.TestCase.model_validate(item) for item in result["generated_test_cases"]]

    plan = RuntimePreparationService().prepare(cases, _context())

    assert plan.prepared_tests == 1
    assert plan.targets[0].classification == "UNIT"
    assert plan.targets[0].executable is True
    assert plan.targets[0].route is None


def test_runtime_executes_generated_pytest_without_network(tmp_path: Path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "calculator.py").write_text(
        "def add(left, right):\n    return left + right\n", encoding="utf-8"
    )
    result = DeterministicUnitTestGenerator().generate(_context())
    cases = [test_case_schema.TestCase.model_validate(item) for item in result["generated_test_cases"]]
    plan = RuntimePreparationService().prepare(cases, _context())

    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="http://unused.invalid",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == 1
    assert outcome.results[0]["runtime_status"] == "Passed"
    assert "urllib" not in (outcome.results[0]["logs"] or "")
    assert outcome.summary["coverage_percent"] > 0


def test_runtime_injects_mock_for_fastapi_depends_default(tmp_path: Path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "route.py").write_text(
        "from fastapi import Depends\n"
        "def get_db():\n    return None\n"
        "def list_items(db=Depends(get_db)):\n    return db.query().all()\n",
        encoding="utf-8",
    )
    context = {
        "functions": [{
            "file": "route.py",
            "name": "list_items",
            "qualified_name": "route.list_items",
            "parameters": ["db"],
            "is_async": False,
        }],
        "test_targets": [{
            "file": "route.py",
            "symbol": "list_items",
            "dependencies": ["db.query"],
        }],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, context)

    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == 1
    assert outcome.summary["failed"] == 0


def test_stage3_repository_behavior_context_is_framework_neutral():
    source = '''
from helpers import notify

class AccountService:
    def __init__(self, repository, audit):
        self.repository = repository
        self.audit = audit

    def transfer(self, amount):
        if amount <= 0:
            raise ValueError("amount")
        self.repository.add(amount)
        self.repository.commit()
        notify(amount)
        return amount
'''.strip()
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="services/accounts.py",
            language="python",
            imports=["helpers"],
            classes=["AccountService"],
            functions=[],
            content=source,
        )],
    )

    result = PythonStaticAnalyzer().analyze(context)
    behavior = result.repository_behavior

    assert behavior is not None
    assert [item.name for item in behavior.modules] == ["services.accounts"]
    service = next(item for item in behavior.classes if item.name == "AccountService")
    assert service.constructor_dependencies == ["repository", "audit"]
    transfer = next(item for item in behavior.functions if item.name == "transfer")
    assert transfer.exceptions == ["ValueError"]
    assert transfer.side_effects == ["database_commit", "database_write"]
    assert behavior.exceptions[transfer.qualified_name] == ["ValueError"]
    assert {item["target"] for item in behavior.dependency_graph} == {"helpers"}
    assert any(
        edge.caller == transfer.qualified_name and edge.callee.endswith("notify")
        for edge in behavior.call_graph
    )


def test_stage4_contract_contains_fixture_mock_patch_docstring_and_aaa(tmp_path):
    context = _context()
    context["test_targets"][0]["dependencies"] = ["dependency.calculate"]
    generated = DeterministicUnitTestGenerator().generate(context)
    case = test_case_schema.TestCase.model_validate(
        generated["generated_test_cases"][0]
    )
    plan = RuntimePreparationService().prepare([case], context)
    build = TestFileBuilder().build(plan.targets, workspace=tmp_path)
    source = build.test_file.read_text(encoding="utf-8")

    assert "@pytest.fixture" in source
    assert "MagicMock" in source
    assert "patch.object" in source
    assert '"""Unit behavior of add."""' in source
    assert "@pytest.mark.parametrize('_unit_iteration', [0])" not in source
    assert "# Arrange" in source
    assert "# Act" in source
    assert "# Assert" in source
    forbidden = ("urllib", "urlopen", "uvicorn", "openapi", "http://", "https://")
    assert not any(item in source.casefold() for item in forbidden)


def test_generated_contract_handles_framework_exceptions_and_mocked_returns():
    generated = DeterministicUnitTestGenerator().generate({
        "functions": [{
            "file": "services.py", "name": "create", "qualified_name": "services.create",
            "parameters": ["repository"], "return_type": "User",
        }],
        "test_targets": [{
            "file": "services.py", "symbol": "create",
            "dependencies": ["repository.add"], "exceptions": ["Conflict"],
            "side_effects": ["database_write"],
        }],
    })

    source = generated["generated_test_cases"][0]["unit_test"]["generated_code"]

    assert "except TypeError:" in source
    assert "hasattr(result, 'status_code')" in source
    assert "not isinstance(result, (MagicMock, AsyncMock))" in source
    assert "Expected at least one declared dependency interaction" not in source


def test_stage4_recommends_professional_test_hierarchy():
    generated = DeterministicUnitTestGenerator().generate({
        "functions": [{
            "file": "app/services/accounts.py",
            "name": "transfer",
            "qualified_name": "app.services.accounts.transfer",
            "parameters": ["amount"],
        }],
        "test_targets": [{
            "file": "app/services/accounts.py",
            "symbol": "transfer",
        }],
    })

    case = test_case_schema.TestCase.model_validate(
        generated["generated_test_cases"][0]
    )

    assert case.traceability["suggested_test_path"] == (
        "tests/services/test_accounts.py"
    )


def test_stage4_classifies_external_dependencies_and_recommends_mocks():
    context = _context()
    context["test_targets"][0]["dependencies"] = [
        "repository.commit",
        "redis.get",
        "http_client.post",
        "os.environ",
        "uuid.uuid4",
        "mailer.send",
        "stripe.charge",
    ]

    generated = DeterministicUnitTestGenerator().generate(context)
    case = test_case_schema.TestCase.model_validate(
        generated["generated_test_cases"][0]
    )

    assert case.unit_test is not None
    assert set(case.unit_test.fixture_names) >= {
        "mock_database",
        "mock_redis",
        "mock_network",
        "mock_environment",
        "mock_uuid",
        "mock_email",
        "mock_payment",
        "monkeypatch",
    }
    recommendations = case.traceability["mock_recommendations"]
    assert {item["kind"] for item in recommendations} >= {
        "database", "redis", "network", "environment", "uuid", "email", "payment"
    }
    assert next(
        item for item in recommendations if item["dependency"] == "http_client.post"
    )["strategy"] == "AsyncMock"
    assert "monkeypatch.setenv" in case.unit_test.generated_code


def test_stage4_variants_have_distinct_executable_assertion_contracts():
    context = _context()
    context["test_targets"][0].update({
        "branches": ["left is zero"],
        "exceptions": ["ValueError"],
        "security_findings": [{"rule_id": "python.lang.security.audit"}],
    })

    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]

    assert {case.category.value for case in cases} == {
        "positive", "negative", "boundary", "exception/integration", "security"
    }
    assert len({case.unit_test.generated_code for case in cases if case.unit_test}) == 5
    for case in cases:
        assert case.unit_test is not None
        source = case.unit_test.generated_code
        assert "# Arrange" in source
        assert "# Act" in source
        assert "# Assert" in source
        assert "assert result is not None" not in source
        assert "assert not isinstance(result, BaseException)" in source
        expected = (
            ["ValueError"]
            if case.category.value in {"negative", "exception/integration"}
            else []
        )
        assert f"expected_exceptions = {expected!r}" in source
        assert case.traceability["expected_exceptions"] == expected
        assert case.traceability["exceptions"] == ["ValueError"]


def test_boundary_only_expects_exception_with_explicit_throw_evidence():
    context = _context()
    context["test_targets"][0].update({
        "edge_cases": ["minimum value raises ValueError"],
        "exceptions": ["ValueError"],
    })

    generated = DeterministicUnitTestGenerator().generate(context)
    boundary = next(
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
        if item["category"] == "boundary"
    )

    assert "expected_exceptions = ['ValueError']" in (
        boundary.unit_test.generated_code
    )
    assert boundary.traceability["expected_exceptions"] == ["ValueError"]


def test_stage4_derives_assertions_from_semantic_behavior():
    context = {
        "functions": [
            {"file": "users.py", "name": "create_user", "return_type": "User"},
            {"file": "auth.py", "name": "authenticate", "return_type": "bool"},
            {
                "file": "validation.py", "name": "validate_email",
                "return_type": "str", "exceptions": ["HTTPException"],
            },
            {"file": "users.py", "name": "list_users", "return_type": "list[User]"},
            {"file": "events.py", "name": "notify_user"},
        ],
        "test_targets": [
            {
                "file": "users.py", "symbol": "create_user",
                "dependencies": ["repository.save"],
                "side_effects": ["database_write"],
            },
            {
                "file": "auth.py", "symbol": "authenticate",
                "dependencies": ["verify_password", "issue_token"],
            },
            {
                "file": "validation.py", "symbol": "validate_email",
                "exceptions": ["HTTPException"],
            },
            {"file": "users.py", "symbol": "list_users"},
            {
                "file": "events.py", "symbol": "notify_user",
                "dependencies": ["publisher.send"], "side_effects": ["send"],
            },
        ],
    }

    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    positive = {
        case.traceability["symbol"]: case
        for case in cases if case.category.value == "positive"
    }

    assert positive["create_user"].expected_results == [
        "The repository or database persistence operation is invoked",
        "The created or persisted object is returned",
    ]
    assert positive["authenticate"].expected_results == [
        "The callable returns exactly True",
        "Password verification or authentication is performed",
        "The authentication result or generated token is returned",
    ]
    assert "assert result is expected_boolean" in (
        positive["authenticate"].unit_test.generated_code
    )
    assert positive["validate_email"].expected_results == [
        "The valid input is accepted and returned unchanged"
    ]
    assert positive["list_users"].expected_results == [
        "The returned collection has the expected type and contents"
    ]
    assert positive["notify_user"].expected_results == [
        "The declared collaborator interaction is invoked"
    ]

    exception = next(
        case for case in cases
        if case.traceability["symbol"] == "validate_email"
        and case.category.value == "exception/integration"
    )
    assert exception.expected_results == [
        "HTTPException is raised with the expected status_code",
        "HTTPException detail describes the rejected request",
    ]
    assert "assert isinstance(result.status_code, int)" in (
        exception.unit_test.generated_code
    )
    exception_code = exception.unit_test.generated_code
    assert "assert result.detail not in (None, '')" in exception_code
    assert "if result.headers is not None:" in exception_code
    assert (
        "else:\n        assert result.args and result.args[0] == str(result)"
        in exception_code
    )


def test_stage5_verifies_unit_syntax_import_contract_and_duplicates():
    generated = DeterministicUnitTestGenerator().generate(_context())
    case = test_case_schema.TestCase.model_validate(
        generated["generated_test_cases"][0]
    )
    sources = [{
        "path": "calculator.py",
        "content": "def add(left, right):\n    return left + right\n",
    }]

    verified = verification_agent.TestVerificationAgent(client=None).verify(
        [case], _context(), sources
    )
    findings = {
        item["check"]: item["status"]
        for item in verified["results"][0]["findings"]
    }
    assert findings["unit_test_syntax"] == "Verified"
    assert findings["unit_import_contract"] == "Verified"
    assert verified["results"][0]["status"] == "Verified"

    duplicates = verification_agent.TestVerificationAgent(client=None).verify(
        [case, case.model_copy(deep=True)], _context(), sources
    )
    assert all(
        any(
            item["check"] == "duplicate" and item["status"] == "Failed"
            for item in result["findings"]
        )
        for result in duplicates["results"]
    )


def test_stage5_uses_explicit_file_for_ambiguous_unit_symbol():
    context = {
        "functions": [{
            "file": "services/items.py",
            "name": "create_item",
            "qualified_name": "services.items.create_item",
            "parameters": [],
            "is_async": False,
        }],
        "test_targets": [{
            "file": "services/items.py",
            "symbol": "create_item",
            "behavior": "Create an item",
            "dependencies": [],
        }],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    case = test_case_schema.TestCase.model_validate(
        generated["generated_test_cases"][0]
    )
    sources = [
        {"path": "repositories/items.py", "content": "def create_item():\n    return 1\n"},
        {"path": "services/items.py", "content": "def create_item():\n    return 2\n"},
    ]

    verified = verification_agent.TestVerificationAgent(client=None).verify(
        [case], context, sources
    )

    assert verified["results"][0]["status"] == "Verified"
    assert {
        evidence["file"] for evidence in verified["results"][0]["evidence"]
    } == {"services/items.py"}


def test_stage5_cache_fingerprint_tracks_unit_rule_contract():
    fingerprint = verification_agent.TestVerificationAgent(
        client=None
    ).cache_fingerprint()

    assert fingerprint["rule_engine_version"] == "unit-contract-v3"


def test_stage4_variants_are_not_stage5_duplicates():
    context = _context()
    context["test_targets"][0]["branches"] = ["left is zero"]
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    verified = verification_agent.TestVerificationAgent(client=None).verify(
        cases,
        context,
        [{
            "path": "calculator.py",
            "content": "def add(left, right):\n    return left + right\n",
        }],
    )

    assert len(cases) == 2
    assert all(result["status"] == "Verified" for result in verified["results"])
    assert all(
        finding["check"] != "duplicate"
        for result in verified["results"]
        for finding in result["findings"]
    )


def test_stage4_preserves_exception_classes_and_accepts_declared_exception(tmp_path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "guard.py").write_text(
        "class DomainError(Exception):\n    pass\n"
        "def validate(value):\n    raise DomainError('invalid')\n",
        encoding="utf-8",
    )
    context = {
        "functions": [{
            "file": "guard.py",
            "name": "validate",
            "qualified_name": "guard.validate",
            "parameters": ["value"],
            "exceptions": ["DomainError"],
            "is_async": False,
        }],
        "test_targets": [{
            "file": "guard.py",
            "symbol": "validate",
            "dependencies": ["DomainError"],
            "exceptions": ["DomainError"],
        }],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, context)

    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["failed"] == 1
    assert outcome.summary["passed"] == len(cases) - 1


def test_stage4_does_not_generate_targets_for_repository_test_sources():
    context = {
        "functions": [
            {
                "file": "services/items.py",
                "name": "create_item",
                "qualified_name": "services.items.create_item",
            },
            {
                "file": "tests/test_items.py",
                "name": "test_create_item",
                "qualified_name": "tests.test_items.test_create_item",
            },
        ],
        "test_targets": [
            {"file": "services/items.py", "symbol": "create_item"},
            {"file": "tests/test_items.py", "symbol": "test_create_item"},
        ],
    }

    generated = DeterministicUnitTestGenerator().generate(context)

    assert generated["total_generated"] == 1
    assert generated["generated_test_cases"][0]["unit_test"]["file"] == (
        "services/items.py"
    )


def test_stage4_excludes_properties_and_runtime_constructs_pydantic_validator(
    tmp_path: Path,
):
    source = tmp_path / "project"
    source.mkdir()
    (source / "profile.py").write_text(
        "from datetime import date\n"
        "from pydantic import BaseModel, model_validator\n"
        "class Profile(BaseModel):\n"
        "    age: int\n"
        "    birth_date: date\n"
        "    @property\n"
        "    def label(self):\n"
        "        return str(self.age)\n"
        "    @model_validator(mode='after')\n"
        "    def validate_age(self):\n"
        "        if date.today().year - self.birth_date.year < self.age:\n"
        "            raise ValueError('age mismatch')\n"
        "        return self\n",
        encoding="utf-8",
    )
    context = {
        "functions": [
            {
                "file": "profile.py",
                "name": "label",
                "qualified_name": "profile.Profile.label",
                "decorators": ["property"],
            },
            {
                "file": "profile.py",
                "name": "validate_age",
                "qualified_name": "profile.Profile.validate_age",
                "decorators": ["model_validator(mode='after')"],
                "exceptions": ["ValueError"],
            },
        ],
        "test_targets": [
            {"file": "profile.py", "symbol": "label"},
            {
                "file": "profile.py",
                "symbol": "validate_age",
                "exceptions": ["ValueError"],
            },
        ],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, context)
    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert {case.unit_test.symbol for case in cases} == {"Profile.validate_age"}
    assert outcome.summary["passed"] == len(cases) - 1
    assert outcome.summary["failed"] == 1


def test_runtime_supplies_async_upload_and_patches_async_dependency(tmp_path: Path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "uploads.py").write_text(
        "from fastapi import File, UploadFile\n"
        "async def store(upload):\n"
        "    return await upload.read()\n"
        "async def receive(upload: UploadFile = File(...)):\n"
        "    return await store(upload)\n",
        encoding="utf-8",
    )
    context = {
        "functions": [{
            "file": "uploads.py",
            "name": "receive",
            "qualified_name": "uploads.receive",
            "parameters": ["upload"],
            "is_async": True,
        }],
        "test_targets": [{
            "file": "uploads.py",
            "symbol": "receive",
            "dependencies": ["store"],
        }],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, context)
    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == len(cases)


def test_runtime_supports_tuple_helper_and_encoded_hash_inputs(tmp_path: Path):
    source = tmp_path / "project"
    source.mkdir()
    (source / "auth.py").write_text(
        "import hmac\n"
        "def issue_pair():\n    return ('access', 'refresh')\n"
        "def hash_password(value, salt):\n    return '00:' + '00' * 32\n"
        "def login():\n    access, refresh = issue_pair()\n    return access\n"
        "def verify(encoded: str):\n"
        "    salt, digest = encoded.split(':', 1)\n"
        "    bytes.fromhex(salt)\n"
        "    bytes.fromhex(digest)\n"
        "    actual = hash_password('password', b'0').split(':', 1)[1]\n"
        "    return hmac.compare_digest(actual, digest)\n",
        encoding="utf-8",
    )
    context = {
        "functions": [
            {
                "file": "auth.py", "name": "login",
                "qualified_name": "auth.login", "parameters": [],
            },
            {
                "file": "auth.py", "name": "verify",
                "qualified_name": "auth.verify", "parameters": ["encoded"],
            },
        ],
        "test_targets": [
            {"file": "auth.py", "symbol": "login", "dependencies": ["issue_pair"]},
            {
                "file": "auth.py",
                "symbol": "verify",
                "dependencies": ["hash_password"],
            },
        ],
    }
    generated = DeterministicUnitTestGenerator().generate(context)
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, context)
    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == len(cases)


def test_runtime_project_app_shadows_accelerator_app(monkeypatch, tmp_path: Path):
    source = tmp_path / "project"
    app_directory = source / "app"
    app_directory.mkdir(parents=True)
    (app_directory / "__init__.py").write_text("", encoding="utf-8")
    (app_directory / "worker.py").write_text(
        "def execute():\n    return __file__\n", encoding="utf-8"
    )
    context = {
        "functions": [{
            "file": "app/worker.py",
            "name": "execute",
            "qualified_name": "app.worker.execute",
            "parameters": [],
        }],
        "test_targets": [{"file": "app/worker.py", "symbol": "execute"}],
    }
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in DeterministicUnitTestGenerator().generate(context)[
            "generated_test_cases"
        ]
    ]
    plan = RuntimePreparationService().prepare(cases, context)
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).parents[2]))

    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == 1
    logs = outcome.results[0]["logs"]
    assert "TESTFORGE_IMPORT_DIAGNOSTIC" in logs
    assert '"module": "app.worker"' in logs
    assert str(source.resolve()) not in logs  # Runtime uses only the isolated copy.
    assert "backend\\app" not in logs and "backend/app" not in logs


def test_runtime_sanitizes_space_and_hyphen_module_paths(tmp_path: Path):
    source = tmp_path / "project"
    target_directory = source / "feature modules"
    target_directory.mkdir(parents=True)
    (target_directory / "order-service.py").write_text(
        "def execute():\n    return 'ok'\n", encoding="utf-8"
    )
    context = {
        "functions": [{
            "file": "feature modules/order-service.py",
            "name": "execute",
            "qualified_name": "execute",
            "parameters": [],
        }],
        "test_targets": [{
            "file": "feature modules/order-service.py",
            "symbol": "execute",
        }],
    }
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in DeterministicUnitTestGenerator().generate(context)[
            "generated_test_cases"
        ]
    ]
    plan = RuntimePreparationService().prepare(cases, context)

    outcome = ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    ).execute(
        source_directory=source,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=30,
    )

    assert outcome.summary["passed"] == 1
    assert '"module": "feature_modules.order_service"' in (
        outcome.results[0]["logs"] or ""
    )


def test_runtime_service_executes_only_unit_plan_and_persists_results(tmp_path):
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    source = tmp_path / "source"
    source.mkdir()
    (source / "calculator.py").write_text(
        "def add(left, right):\n    return left + right\n", encoding="utf-8"
    )
    generated = DeterministicUnitTestGenerator().generate(_context())
    cases = [
        test_case_schema.TestCase.model_validate(item)
        for item in generated["generated_test_cases"]
    ]
    plan = RuntimePreparationService().prepare(cases, _context())
    project = SimpleNamespace(storage_path="stored")
    stage_run = SimpleNamespace(
        id=run_id,
        project_id=project_id,
        status=CodeUnderstandingStatus.COMPLETED,
        failed_stage=None,
        result={"runtime_execution_plan": plan.model_dump(mode="json")},
    )
    persisted_run = SimpleNamespace(id=uuid.uuid4())
    projects = Mock()
    projects.get_by_id.return_value = project
    code_runs = Mock()
    code_runs.get_by_id.return_value = stage_run
    runtime_runs = Mock()
    runtime_runs.create_run.return_value = persisted_run
    storage = Mock()
    storage.resolve_project_directory.return_value = tmp_path
    execution = Mock()
    execution.execute.return_value = ExecutionOutcome(
        results=[{
            "test_case_id": cases[0].id,
            "runtime_status": "Passed",
            "expected_result": {"kind": "unit"},
            "actual_result": {"return_value": "2"},
            "assertion_failure": None,
            "logs": "1 passed",
            "execution_time_ms": 1.0,
        }],
        summary={"passed": 1, "failed": 0, "coverage_percent": 100.0},
        duration_ms=2.0,
    )
    service = RuntimeValidationService(
        projects, code_runs, runtime_runs, storage, execution
    )

    result = service.run(
        project_id=project_id,
        code_understanding_run_id=run_id,
        base_url="http://legacy-value-is-not-contacted",
        test_case_ids=None,
        timeout_seconds=30,
    )

    assert result is persisted_run
    executed = execution.execute.call_args.kwargs["test_cases"]
    assert executed and all(item.classification == "UNIT" for item in executed)
    assert execution.execute.call_args.kwargs["base_url"] == ""
    runtime_runs.complete.assert_called_once()
