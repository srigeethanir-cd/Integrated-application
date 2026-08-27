import uuid
from unittest.mock import Mock

import pytest

from app.agents.code_understanding.agent import (
    CodeUnderstandingAgent,
    CodeUnderstandingContext,
    CodeUnderstandingResult,
    PydanticFieldDescription,
    PydanticSchemaDescription,
    ProviderCodeUnderstandingResult,
    SourceFileContext,
)


def test_code_understanding_removes_endpoints_without_source_decorators(
    caplog,
) -> None:
    caplog.set_level("INFO")
    provider = Mock()
    provider.generate_structured.return_value = CodeUnderstandingResult.model_validate({
        "project_summary": "Minimal API",
        "architecture": "Single FastAPI module",
        "api_endpoints": [
            {"method": "GET", "route": "/", "handler": "root", "file": "main.py"},
            {"method": "POST", "route": "/", "handler": None, "file": "main.py"},
            {"method": "PUT", "route": "/", "handler": "update_root", "file": "main.py"},
            {"method": "DELETE", "route": "/", "handler": "delete_root", "file": "main.py"},
        ],
    })
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="main.py", language="python", functions=["root"],
            content='from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"ok": True}\n',
        )],
    )

    result = CodeUnderstandingAgent(provider).analyze(context)

    assert [(item.method, item.route, item.handler) for item in result.api_endpoints] == [
        ("GET", "/", "root")
    ]
    provider.generate_structured.assert_not_called()


def test_provider_contract_excludes_deterministic_metadata() -> None:
    schema = ProviderCodeUnderstandingResult.model_json_schema()
    assert set(schema["properties"]) == {
        "project_summary",
        "architecture",
        "business_rules",
        "execution_flows",
        "ambiguities",
    }
    serialized = str(schema)
    for field in (
        "analyzed_files", "pydantic_schemas", "request_model",
        "response_model", "success_status_codes", "error_status_codes",
        "exception_status_mappings", "branches", "edge_cases",
        "api_endpoints", "test_targets",
    ):
        assert field not in serialized


def test_enrichment_preserves_external_stage3_contract() -> None:
    provider = Mock()
    provider.generate_structured.return_value = ProviderCodeUnderstandingResult(
        project_summary="Service",
        architecture="Layered",
        business_rules=["Only active accounts can log in"],
    )
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="account.py",
            language="python",
            is_entry_point=True,
            content=(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.get('/accounts/{account_id}', status_code=204)\n"
                "def get_account(account_id: int):\n"
                "    if account_id < 1:\n"
                "        raise ValueError('invalid')\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent(provider).analyze(context)

    assert set(result.model_dump()) == set(CodeUnderstandingResult.model_fields)
    assert result.api_endpoints[0].route == "/accounts/{account_id}"
    assert result.api_endpoints[0].success_status_codes == [204]
    assert result.analyzed_files[0].path == "account.py"
    assert result.test_targets[0].symbol == "get_account"
    assert result.test_targets[0].branches


def test_code_understanding_extracts_explicit_http_and_pydantic_metadata() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CodeUnderstandingResult.model_validate({
        "project_summary": "Account API",
        "architecture": "FastAPI",
        "api_endpoints": [{
            "method": "POST",
            "route": "/login",
            "handler": "login",
            "file": "account.py",
        }],
    })
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="account.py",
            language="python",
            content=(
                "from fastapi import FastAPI, HTTPException, status\n"
                "from pydantic import BaseModel, Field\n"
                "app = FastAPI()\n"
                "class LoginRequest(BaseModel):\n"
                "    email: str = Field(example='user@example.com')\n"
                "    password: str\n"
                "    remember_me: bool = False\n"
                "class TokenResponse(BaseModel):\n"
                "    access_token: str\n"
                "    token_type: str = 'bearer'\n"
                "    model_config = {'json_schema_extra': {'example': "
                "{'access_token': 'documented', 'token_type': 'bearer'}}}\n"
                "class InvalidCredentials(HTTPException):\n"
                "    def __init__(self):\n"
                "        super().__init__(status_code=401, detail='invalid')\n"
                "def authenticate(request: LoginRequest):\n"
                "    raise InvalidCredentials()\n"
                "@app.post('/login', response_model=TokenResponse, "
                "status_code=status.HTTP_201_CREATED, responses={409: {}})\n"
                "def login(request: LoginRequest):\n"
                "    return authenticate(request)\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent(provider).analyze(context)

    endpoint = result.api_endpoints[0]
    assert endpoint.request_type == "LoginRequest"
    assert endpoint.request_model == "LoginRequest"
    assert endpoint.response_type == "TokenResponse"
    assert endpoint.response_model == "TokenResponse"
    assert endpoint.success_status_codes == [201]
    assert endpoint.error_status_codes == [401, 409]
    assert [
        item.model_dump() for item in endpoint.exception_status_mappings
    ] == [{"exception": "InvalidCredentials", "status_code": 401}]

    schemas = {item.name: item for item in result.pydantic_schemas}
    request_fields = {
        item.name: item for item in schemas["LoginRequest"].fields
    }
    assert request_fields["email"].type == "str"
    assert request_fields["email"].required is True
    assert request_fields["email"].examples == ["user@example.com"]
    assert request_fields["password"].required is True
    assert request_fields["remember_me"].has_default is True
    assert request_fields["remember_me"].default is False
    assert request_fields["remember_me"].required is False
    assert schemas["TokenResponse"].examples == [{
        "access_token": "documented",
        "token_type": "bearer",
    }]


def test_code_understanding_does_not_infer_runtime_values() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CodeUnderstandingResult.model_validate({
        "project_summary": "Minimal API",
        "architecture": "FastAPI",
        "api_endpoints": [{
            "method": "POST",
            "route": "/items",
            "handler": "create_item",
            "file": "main.py",
        }],
    })
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="main.py",
            language="python",
            content=(
                "from fastapi import FastAPI\n"
                "from pydantic import BaseModel\n"
                "app = FastAPI()\n"
                "class ItemRequest(BaseModel):\n"
                "    name: str\n"
                "@app.post('/items')\n"
                "def create_item(request: ItemRequest):\n"
                "    return {'name': request.name}\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent(provider).analyze(context)

    endpoint = result.api_endpoints[0]
    assert endpoint.success_status_codes == [200]
    assert endpoint.error_status_codes == []
    assert endpoint.exception_status_mappings == []
    field = result.pydantic_schemas[0].fields[0]
    assert field.required is True
    assert field.has_default is False
    assert field.default is None
    assert field.examples == []


def test_stage3a_composes_router_prefixes_and_extracts_endpoint_metadata() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[
            SourceFileContext(
                path="app/main.py",
                language="python",
                content=(
                    "from fastapi import FastAPI\n"
                    "from .routers import items\n"
                    "app = FastAPI()\n"
                    "app.include_router(items.router, prefix='/api')\n"
                ),
            ),
            SourceFileContext(
                path="app/routers/items.py",
                language="python",
                content=(
                    "from typing import Annotated\n"
                    "from fastapi import APIRouter, Depends, HTTPException\n"
                    "router = APIRouter(prefix='/items')\n"
                    "def get_db(): pass\n"
                    "@router.get('/{item_id}')\n"
                    "def get_item(item_id: int, db=Depends(get_db)):\n"
                    "    raise HTTPException(status_code=404)\n"
                    "@router.put('/{item_id}')\n"
                    "def update_item(item_id: int, db: Annotated[str, Depends(get_db)]):\n"
                    "    raise HTTPException(status_code=404)\n"
                    "@router.delete('/{item_id}')\n"
                    "def delete_item(item_id: int, db=Depends(get_db)):\n"
                    "    raise HTTPException(status_code=404)\n"
                    "@router.post('/', status_code=201)\n"
                    "def create_item(db=Depends(get_db)): pass\n"
                ),
            ),
        ],
    )

    result = CodeUnderstandingAgent().analyze(context)
    endpoints = {
        (item.method, item.route): item for item in result.api_endpoints
    }

    for method in ("GET", "PUT", "DELETE"):
        endpoint = endpoints[(method, "/api/items/{item_id}")]
        assert endpoint.dependencies == ["get_db"]
        assert endpoint.success_status_codes == [200]
        assert endpoint.error_status_codes == [404]
        assert [
            item.model_dump() for item in endpoint.exception_status_mappings
        ] == [{"exception": "HTTPException", "status_code": 404}]
    assert endpoints[("POST", "/api/items/")].success_status_codes == [201]
    assert "Depends" not in next(
        item for item in result.functions if item.name == "get_item"
    ).calls
    assert all(edge.callee != "Depends" for edge in result.call_graph)


def test_stage3a_preserves_function_class_and_pydantic_metadata() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="app/models.py",
            language="python",
            content=(
                "from typing import Annotated\n"
                "from pydantic import BaseModel, Field, field_validator, "
                "model_validator\n"
                "class Parent:\n"
                "    inherited: str\n"
                "class Payload(Parent, BaseModel):\n"
                "    name: Annotated[str, Field(min_length=2, max_length=40, "
                "pattern='^[a-z]+$', description='Display name', "
                "title='Name')] = Field(..., regex='^[a-z]+$', "
                "examples=['alpha'])\n"
                "    score: int = Field(default_factory=int, gt=0, lt=100, "
                "ge=1, le=99)\n"
                "    @field_validator('name', mode='before')\n"
                "    @classmethod\n"
                "    def normalize_name(cls, value):\n"
                "        return value.strip()\n"
                "    @model_validator(mode='after')\n"
                "    def validate_model(self):\n"
                "        return self\n"
                "async def load_payload():\n"
                "    return Payload(name='alpha')\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent().analyze(context)

    function = next(
        item for item in result.functions if item.name == "load_payload"
    )
    assert function.is_async is True
    payload_class = next(
        item for item in result.classes if item.name == "Payload"
    )
    assert payload_class.fields == ["name", "score"]
    assert payload_class.methods == ["normalize_name", "validate_model"]
    assert payload_class.bases == ["Parent", "BaseModel"]
    assert payload_class.inheritance == ["Parent", "BaseModel"]

    schema = next(
        item for item in result.pydantic_schemas if item.name == "Payload"
    )
    fields = {item.name: item for item in schema.fields}
    assert fields["name"].min_length == 2
    assert fields["name"].max_length == 40
    assert fields["name"].pattern == "^[a-z]+$"
    assert fields["name"].regex == "^[a-z]+$"
    assert fields["name"].description == "Display name"
    assert fields["name"].title == "Name"
    assert fields["name"].examples == ["alpha"]
    assert fields["score"].gt == 0
    assert fields["score"].lt == 100
    assert fields["score"].ge == 1
    assert fields["score"].le == 99
    assert fields["score"].default_factory == "int"
    assert fields["score"].required is False
    validators = {item.name: item for item in schema.validators}
    assert validators["normalize_name"].fields == ["name"]
    assert validators["normalize_name"].mode == "before"
    assert validators["validate_model"].fields == []
    assert validators["validate_model"].mode == "after"
    result.model_dump(mode="json")


def test_stage3a_extracts_sqlalchemy_metadata_without_router_false_positives() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="app/database.py",
            language="python",
            content=(
                "from sqlalchemy import Column, Integer, String, ForeignKey, "
                "Index, UniqueConstraint, CheckConstraint\n"
                "from sqlalchemy.orm import Session, relationship, sessionmaker\n"
                "SessionLocal = sessionmaker(bind=engine)\n"
                "class User(Base):\n"
                "    __table_args__ = (UniqueConstraint('email'), "
                "CheckConstraint('age >= 0'), "
                "Index('ix_user_email', 'email'))\n"
                "    id = Column(Integer, primary_key=True, index=True)\n"
                "    organization_id = Column(Integer, "
                "ForeignKey('organizations.id'), nullable=False)\n"
                "    email = Column(String(255), nullable=False, unique=True, "
                "default='unknown')\n"
                "    age = Column(Integer, CheckConstraint('age >= 0'), "
                "default=0)\n"
                "    organization = relationship('Organization')\n"
                "def get_db():\n"
                "    db = SessionLocal()\n"
                "    try:\n"
                "        yield db\n"
                "    except Exception:\n"
                "        db.rollback()\n"
                "        raise\n"
                "    finally:\n"
                "        db.close()\n"
                "def save_user(database: Session, user: User):\n"
                "    database.add(user)\n"
                "    database.commit()\n"
                "    database.refresh(user)\n"
                "def configure_routes(router):\n"
                "    router.get('/users')\n"
                "    router.post('/users')\n"
                "    router.delete('/users/{user_id}')\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent().analyze(context)

    assert [
        item.model_dump() for item in result.sqlalchemy_session_factories
    ] == [{
        "name": "SessionLocal",
        "file": "app/database.py",
        "factory": "sessionmaker",
        "bind": "engine",
    }]
    model = next(item for item in result.data_models if item.name == "User")
    columns = {item.name: item for item in model.columns}
    assert columns["id"].type == "Integer"
    assert columns["id"].primary_key is True
    assert columns["id"].nullable is False
    assert columns["id"].index is True
    assert columns["organization_id"].foreign_keys == ["organizations.id"]
    assert columns["organization_id"].nullable is False
    assert columns["email"].type == "String(255)"
    assert columns["email"].unique is True
    assert columns["email"].default == "unknown"
    assert columns["age"].default == 0
    assert model.primary_keys == ["id"]
    assert model.foreign_keys == [
        "organization_id -> organizations.id"
    ]
    assert model.relationships == [
        "organization = relationship('Organization')"
    ]
    assert "id" in model.indexes
    assert "Index('ix_user_email', 'email')" in model.indexes
    assert "email" in model.unique_constraints
    assert "UniqueConstraint('email')" in model.unique_constraints
    assert "CheckConstraint('age >= 0')" in model.check_constraints

    get_db = next(item for item in result.functions if item.name == "get_db")
    assert set(get_db.sqlalchemy_model_usage) == {
        "SessionLocal()", "db.close", "db.rollback", "yield db"
    }
    save = next(item for item in result.functions if item.name == "save_user")
    assert set(save.sqlalchemy_model_usage) >= {
        "database.add", "database.commit", "database.refresh"
    }
    routes = next(
        item for item in result.functions if item.name == "configure_routes"
    )
    assert routes.sqlalchemy_model_usage == []


def test_stage3a_builds_precise_qualified_runtime_call_graph_and_targets() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[
            SourceFileContext(
                path="app/helpers.py",
                language="python",
                content=(
                    "def execute():\n"
                    "    return 1\n"
                    "class Worker:\n"
                    "    def __init__(self):\n"
                    "        pass\n"
                    "    def run(self):\n"
                    "        return execute()\n"
                ),
            ),
            SourceFileContext(
                path="app/main.py",
                language="python",
                content=(
                    "from typing import Dict, List, Optional, overload\n"
                    "from fastapi import APIRouter, Depends, FastAPI\n"
                    "from app.helpers import execute as run_helper\n"
                    "import app.helpers as helpers\n"
                    "app = FastAPI()\n"
                    "router = APIRouter()\n"
                    "app.include_router(router)\n"
                    "def provider():\n"
                    "    return 1\n"
                    "@router.get('/')\n"
                    "def endpoint(values: Optional[List[str]] = "
                    "Depends(provider)):\n"
                    "    typed: Dict[str, int] = {}\n"
                    "    payload = {'id': 1}\n"
                    "    run_helper()\n"
                    "    helpers.execute()\n"
                    "    return payload['id']\n"
                    "@overload\n"
                    "def contract(value: int): ...\n"
                    "def outer():\n"
                    "    def nested():\n"
                    "        return helpers.execute()\n"
                    "    return 1\n"
                ),
            ),
        ],
    )

    result = CodeUnderstandingAgent().analyze(context)

    edges = {(item.caller, item.callee) for item in result.call_graph}
    assert edges == {
        ("app.helpers.Worker.run", "app.helpers.execute"),
        ("app.main", "fastapi.FastAPI"),
        ("app.main", "fastapi.APIRouter"),
        ("app.main", "app.include_router"),
        ("app.main.endpoint", "app.helpers.execute"),
    }
    assert all(
        item.callee not in {
            "Depends", "router.get", "router.post",
            "router.put", "router.delete",
        }
        for item in result.call_graph
    )
    endpoint = next(
        item for item in result.functions if item.name == "endpoint"
    )
    assert endpoint.calls == ["app.helpers.execute"]

    targets = {
        (item.file, item.symbol): item for item in result.test_targets
    }
    assert set(targets) == {
        ("app/helpers.py", "execute"),
        ("app/helpers.py", "run"),
        ("app/main.py", "provider"),
        ("app/main.py", "endpoint"),
        ("app/main.py", "outer"),
    }
    assert targets[("app/main.py", "endpoint")].edge_cases == [
        "missing key access may raise KeyError: payload['id']"
    ]
    assert all(
        "List[" not in edge and "Optional[" not in edge and "Dict[" not in edge
        for target in targets.values() for edge in target.edge_cases
    )


def test_target_discovery_uses_runtime_modules_and_prefers_business_services() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[
            SourceFileContext(
                path="backend/app/services/auth.py",
                language="python",
                content=(
                    "def authenticate_user(username: str) -> bool:\n"
                    "    return username == 'known'\n"
                ),
            ),
            SourceFileContext(
                path="backend/app/routes/auth.py",
                language="python",
                is_entry_point=True,
                content=(
                    "from fastapi import APIRouter\n"
                    "from app.services.auth import authenticate_user as service_auth\n"
                    "router = APIRouter()\n"
                    "@router.post('/login')\n"
                    "def authenticate_user(username: str):\n"
                    "    return service_auth(username)\n"
                ),
            ),
        ],
    )

    result = CodeUnderstandingAgent().analyze(context)

    assert {module.name for module in result.modules} == {
        "app.routes.auth", "app.services.auth",
    }
    functions = {item.qualified_name: item for item in result.functions}
    assert functions[
        "app.routes.auth.authenticate_user"
    ].target_classification == "router_wrapper"
    assert functions[
        "app.services.auth.authenticate_user"
    ].target_classification == "business_service"
    assert [item.qualified_name for item in result.test_targets] == [
        "app.services.auth.authenticate_user"
    ]
    assert result.test_targets[0].target_priority == "high"
    assert result.test_targets[0].runtime_resolvable is True
    assert any(
        edge.caller == "app.routes.auth.authenticate_user"
        and edge.callee == "app.services.auth.authenticate_user"
        for edge in result.call_graph
    )
    assert {
        (edge["source"], edge["target"])
        for edge in result.repository_behavior.dependency_graph
    } >= {("app.routes.auth", "app.services.auth")}


def test_target_dependencies_only_include_real_collaborators() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="app/users.py",
            language="python",
            content=(
                "import json\n"
                "from datetime import datetime\n"
                "from fastapi import HTTPException\n"
                "from app.models import User\n"
                "def create_user(db, hasher, payload: dict):\n"
                "    names = []\n"
                "    names.append(str(payload.get('name', '')).strip())\n"
                "    created_at = datetime.utcnow()\n"
                "    json.dumps(payload)\n"
                "    if not names:\n"
                "        raise HTTPException(status_code=400)\n"
                "    user = User(name=names.pop(), created_at=created_at)\n"
                "    user.password = hasher.hash(payload['password'])\n"
                "    db.add(user)\n"
                "    db.commit()\n"
                "    return user\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent().analyze(context)

    target = next(item for item in result.test_targets if item.symbol == "create_user")
    assert target.dependencies == ["HTTPException", "User", "add", "commit", "hash"]


def test_target_discovery_preserves_same_named_methods_by_owner() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=[SourceFileContext(
            path="services/workers.py",
            language="python",
            content=(
                "class ImportService:\n"
                "    def run(self):\n"
                "        return 'imported'\n"
                "class ExportService:\n"
                "    def run(self):\n"
                "        return 'exported'\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent().analyze(context)

    assert {item.qualified_name for item in result.test_targets} == {
        "services.workers.ExportService.run",
        "services.workers.ImportService.run",
    }
    assert {item.owner_class for item in result.test_targets} == {
        "services.workers.ExportService",
        "services.workers.ImportService",
    }


def test_stage3a_extracts_symbols_calls_sqlalchemy_and_security() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        security_findings=[{
            "id": "finding-1",
            "rule_id": "python.lang.security.audit",
            "severity": "ERROR",
            "file": "app/api.py",
            "line": 15,
            "message": "Review authentication",
            "cwe": ["CWE-287"],
            "owasp": ["A07"],
            "metadata": {"category": "security"},
        }],
        files=[SourceFileContext(
            path="app/api.py",
            language="python",
            content=(
                "from fastapi import FastAPI\n"
                "from sqlalchemy.orm import DeclarativeBase\n"
                "app = FastAPI()\n"
                "class Base(DeclarativeBase):\n"
                "    pass\n"
                "class User(Base):\n"
                "    id: int\n"
                "    def active(self) -> bool:\n"
                "        return True\n"
                "def load_user(session, user_id: int):\n"
                "    return session.query(User).get(user_id)\n"
                "@app.get('/users/{user_id}', response_model=User)\n"
                "def get_user(user_id: int, session):\n"
                "    user = load_user(session, user_id)\n"
                "    if not user:\n"
                "        raise ValueError('missing')\n"
                "    return user\n"
            ),
        )],
    )

    result = CodeUnderstandingAgent().analyze(context)

    assert result.modules[0].name == "app.api"
    assert {item.kind for item in result.symbol_table} >= {
        "class", "function", "method"
    }
    function = next(item for item in result.functions if item.name == "get_user")
    assert function.decorators == ["app.get('/users/{user_id}', response_model=User)"]
    assert function.exceptions == ["ValueError"]
    assert function.security_findings[0].rule_id == "python.lang.security.audit"
    assert any(
        edge.caller == "app.api.get_user"
        and edge.callee == "app.api.load_user"
        for edge in result.call_graph
    )
    loader = next(item for item in result.functions if item.name == "load_user")
    assert "session.query" in loader.sqlalchemy_model_usage
    endpoint = result.api_endpoints[0]
    assert endpoint.security_findings[0].id == "finding-1"
    user_class = next(item for item in result.classes if item.name == "User")
    assert user_class.methods == ["active"]


def test_complete_stage3_response_with_required_field_is_json_serializable() -> None:
    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        security_findings=[{
            "id": "finding-1",
            "rule_id": "python.security.example",
            "severity": "WARNING",
            "file": "main.py",
            "line": 8,
            "message": "Example finding",
            "cwe": [],
            "owasp": [],
            "metadata": {"example": None},
        }],
        files=[SourceFileContext(
            path="main.py",
            language="python",
            is_entry_point=True,
            content=(
                "from fastapi import FastAPI\n"
                "from pydantic import BaseModel, Field\n"
                "app = FastAPI()\n"
                "class Request(BaseModel):\n"
                "    required_value: str = Field(...)\n"
                "class Response(BaseModel):\n"
                "    value: str\n"
                "@app.post('/items', response_model=Response)\n"
                "def create_item(request: Request):\n"
                "    if not request.required_value:\n"
                "        raise ValueError('required')\n"
                "    return Response(value=request.required_value)\n"
            ),
        )],
    )

    enriched = CodeUnderstandingAgent().analyze(context)
    serialized = enriched.model_dump(mode="json")

    field = enriched.pydantic_schemas[0].fields[0]
    assert field.required is True
    assert field.has_default is False
    assert field.default is None
    assert serialized["pydantic_schemas"][0]["fields"][0]["default"] is None
    assert serialized["security_findings"][0]["id"] == "finding-1"


def test_stage3_ellipsis_guard_reports_nested_field_and_model() -> None:
    enriched = CodeUnderstandingResult(
        project_summary="Example",
        architecture="Python",
        pydantic_schemas=[PydanticSchemaDescription(
            name="Request",
            file="main.py",
            fields=[PydanticFieldDescription(
                name="value",
                type="str",
                required=True,
                default=...,
            )],
        )],
    )

    with pytest.raises(
        ValueError,
        match=(
            "field='default'.*"
            r"path='CodeUnderstandingResult\.pydantic_schemas\[0\]"
            r"\.fields\[0\]\.default'.*"
            "offending_model='PydanticFieldDescription'"
        ),
    ):
        enriched.assert_no_ellipsis()
