import json
from unittest.mock import Mock

import pytest
import httpx
from openai import RateLimitError

from app.agents.test_generation.test_generation_agent import (
    TestGenerationAgent as GenerationAgent,
    TestGenerationError as GenerationError,
)
from app.agents.test_generation.traceability_mapper import TraceabilityMapper
from app.schemas.test_case import TestCaseBatch as CaseBatch
from app.agents.semantic_verification.agent import (
    TestVerificationAgent as VerificationAgent,
)
from app.agents.code_understanding.client import (
    AllProvidersExhaustedError,
    ResilientStructuredOutputClient,
    TruncatedStructuredResponseError,
)
from app.agents.test_generation.scenario_planner import ExecutableScenarioPlanner


def _case(**overrides):
    value = {
        "id": "TC-1",
        "title": "Create a record",
        "description": "A normal path",
        "category": "integration",
        "priority": "high",
        "severity": "major",
        "steps": ["Submit request"],
        "expected_results": ["Record is created"],
    }
    value.update(overrides)
    return value


def _plan() -> dict:
    return {
        "current_score": 70,
        "threshold": 80,
        "missing_categories": ["security"],
        "weak_test_cases": ["TC-2"],
        "failed_test_cases": ["TC-3"],
        "actions": [
            {"action": "ADD", "category": "security", "test_case_id": None},
            {"action": "UPDATE", "test_case_id": "TC-2", "category": None},
            {"action": "UPDATE", "test_case_id": "TC-3", "category": None},
        ],
        "rationale": ["Address deterministic coverage gaps"],
    }


def test_prompt_builder_loads_packaged_template() -> None:
    agent = GenerationAgent(client=Mock())
    prompt = agent._prompt_builder.build_prompt(
        {"project_summary": "Example"}, ["functional"]
    )

    assert '"test_cases"' in prompt
    assert "Example" in prompt


def test_generation_uses_json_object_and_preserves_valid_classification() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case()]}
    )

    result = GenerationAgent(client=provider).generate({"architecture": "API"})

    request = provider.generate_structured.call_args.kwargs
    assert request["response_model"] is CaseBatch
    assert "Application lifecycle behavior was detected" not in request["user_prompt"]
    assert result["generated_test_cases"][0]["category"] == "exception/integration"
    assert result["generated_test_cases"][0]["priority"] == "high"
    assert result["generated_test_cases"][0]["severity"] == "major"
    assert result["generated_test_cases"][0]["traceability"] == {
        "api_routes": [],
        "business_rules": [],
        "execution_flows": [],
        "source_files": [],
        "symbols": [],
    }


@pytest.mark.parametrize(
    ("category", "priority", "severity"),
    [(None, None, None), ("unsupported", "urgent", "unknown")],
)
def test_post_processing_falls_back_for_missing_or_invalid_classification(
    category, priority, severity,
) -> None:
    case = CaseBatch.model_validate(
        {"test_cases": [_case(category="positive", priority="low", severity="major")]}
    ).test_cases[0].model_copy(
        update={
            "category": category,
            "priority": priority,
            "severity": severity,
        }
    )

    result = GenerationAgent(client=Mock())._post_process([case], {})

    assert result[0].category.value == "positive"
    assert result[0].priority.value == "medium"
    assert result[0].severity.value == "minor"
    assert result[0].traceability["priority_rule"] == "category: positive"


def test_parser_accepts_legacy_array_and_rejects_malformed_object() -> None:
    agent = GenerationAgent(client=Mock())

    assert agent._parse_llm_output(json.dumps([_case()]))[0].id == "TC-1"
    with pytest.raises(GenerationError):
        agent._parse_llm_output('{"unexpected": []}')


def test_deduplication_normalizes_title_and_steps() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {
            "test_cases": [
                _case(),
                _case(
                    id="TC-2",
                    title="  CREATE   A RECORD ",
                    steps=[" submit REQUEST "],
                ),
            ]
        }
    )

    result = GenerationAgent(client=provider).generate({})

    assert result["total_generated"] == 2
    assert result["total_after_deduplication"] == 1


def test_post_processing_emits_one_metadata_consistent_canonical_scenario() -> None:
    provider_cases = CaseBatch.model_validate({"test_cases": [
        _case(
            id="LOGIN-201", title="Login with matching credentials",
            description="POST /login using valid credentials",
            steps=["POST /login with the correct password"],
            expected_results=["HTTP 201 is returned"],
            traceability={"route": "/login", "method": "POST"},
        ),
        _case(
            id="LOGIN-200", title="Successful login",
            description="POST /login using correct password",
            steps=["POST /login with matching credentials"],
            expected_results=["HTTP 200 is returned"],
            traceability={"route": "/login", "method": "POST"},
        ),
        _case(
            id="LOGIN-DUP", title="Valid credentials are accepted",
            description="POST /login with matching credentials",
            steps=["Call login with the correct password"],
            expected_results=["HTTP 200 is returned"],
            traceability={"route": "/login", "method": "POST"},
        ),
    ]}).test_cases
    stage3 = {
        "api_endpoints": [{
            "route": "/login", "method": "POST", "handler": "login",
            "file": "auth.py", "success_status_codes": [200],
            "error_status_codes": [401],
        }],
        "test_targets": [{
            "symbol": "login", "file": "auth.py",
            "signature": "login(username, password)",
        }],
    }

    result = GenerationAgent(client=Mock())._post_process(provider_cases, stage3)

    assert [item.id for item in result] == ["LOGIN-200"]
    assert result[0].traceability["route"] == "/login"


def test_generation_maps_stage_three_traceability_consumed_by_stage_five() -> None:
    stage3 = {
        "api_endpoints": [
            {
                "method": "POST",
                "route": "/projects",
                "handler": "create_project",
                "file": "app/api/projects.py",
                "request_type": "ProjectCreate",
                "response_type": "ProjectResponse",
            }
        ],
        "business_rules": [
            {
                "description": "Project creation requires a valid name",
                "files": ["app/api/projects.py"],
                "symbols": ["create_project"],
            }
        ],
        "execution_flows": [
            {
                "name": "Create project",
                "entrypoint": "create_project",
                "steps": ["Validate project name", "Persist project"],
                "files": ["app/api/projects.py"],
            }
        ],
        "test_targets": [
            {
                "symbol": "create_project",
                "file": "app/api/projects.py",
                "behavior": "Create and return a project",
            }
        ],
    }
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {
            "test_cases": [
                _case(
                    title="Create a project",
                    description="POST /projects with a valid project name",
                    steps=["Submit POST /projects"],
                    expected_results=["ProjectResponse is returned"],
                )
            ]
        }
    )

    generation = GenerationAgent(client=provider).generate(stage3)
    generated_case = generation["generated_test_cases"][0]
    trace = generated_case["traceability"]

    assert trace["file"] == "app/api/projects.py"
    assert trace["symbol"] == "create_project"
    assert trace["route"] == "/projects"
    assert trace["source_files"] == ["app/api/projects.py"]
    assert trace["business_rules"][0]["description"].startswith("Project creation")
    assert trace["execution_flows"][0]["name"] == "Create project"

    verification = VerificationAgent().verify(
        [generated_case],
        stage3,
        [
            {
                "path": "app/api/projects.py",
                "functions": ["create_project"],
                "classes": [],
                "content": "@router.post('/projects')\ndef create_project():\n    pass",
            }
        ],
    )

    checks = {
        finding["check"]: finding["status"]
        for finding in verification["results"][0]["findings"]
    }
    assert checks["file_exists"] == "Verified"
    assert checks["symbol_exists"] == "Verified"
    assert checks["endpoint_exists"] == "Verified"


def test_traceability_primary_fields_require_exact_or_confident_match() -> None:
    stage3 = {
        "test_targets": [{
            "symbol": "create_project",
            "signature": "create_project(data: ProjectCreate)",
            "file": "app/projects.py",
            "behavior": "Persist a new project",
        }],
        "analyzed_files": [{
            "path": "app/projects.py",
            "purpose": "Project persistence",
            "key_symbols": ["create_project"],
        }],
        "api_endpoints": [{
            "method": "POST", "route": "/projects",
            "handler": "create_project", "file": "app/projects.py",
        }],
    }
    unrelated = CaseBatch.model_validate({
        "test_cases": [_case(
            title="Validate a record",
            description="Persist an ordinary record",
            steps=["Submit a record"],
        )]
    }).test_cases[0]

    conservative = TraceabilityMapper(confidence_threshold=0.6).map(
        [unrelated], stage3
    )[0].traceability
    permissive = TraceabilityMapper(confidence_threshold=0.1).map(
        [unrelated], stage3
    )[0].traceability

    assert not {"file", "symbol", "route"}.intersection(conservative)
    assert permissive["file"] == "app/projects.py"


def test_traceability_precedence_and_valid_explicit_metadata() -> None:
    stage3 = {
        "test_targets": [
            {
                "symbol": "create_project",
                "signature": "create_project(data: ProjectCreate)",
                "file": "app/projects.py",
            },
            {
                "symbol": "archive_project",
                "signature": "archive_project(project_id: int)",
                "file": "app/archive.py",
            },
        ],
        "analyzed_files": [{
            "path": "app/archive.py",
            "purpose": "Archival",
            "key_symbols": ["archive_project"],
        }],
        "api_endpoints": [{
            "method": "POST", "route": "/projects",
            "handler": "create_project", "file": "app/projects.py",
        }],
    }
    explicit_target = CaseBatch.model_validate({
        "test_cases": [_case(
            title="Create project",
            description="Call create_project through POST /projects",
            steps=["Invoke create_project"],
        )]
    }).test_cases[0]
    explicit_file = CaseBatch.model_validate({
        "test_cases": [_case(
            id="TC-2", title="Archive project",
            description="Exercise app/archive.py",
            steps=["Use the analyzed file"],
        )]
    }).test_cases[0]
    valid_existing = CaseBatch.model_validate({
        "test_cases": [_case(
            id="TC-3", title="Existing trace",
            traceability={
                "file": "app/projects.py",
                "symbol": "create_project",
                "route": "/projects",
            },
        )]
    }).test_cases[0]

    target_trace, file_trace, existing_trace = [
        item.traceability
        for item in TraceabilityMapper().map(
            [explicit_target, explicit_file, valid_existing], stage3
        )
    ]

    assert target_trace["symbol"] == "create_project"
    assert target_trace["file"] == "app/projects.py"
    assert target_trace["route"] == "/projects"
    assert file_trace["file"] == "app/archive.py"
    assert "symbol" not in file_trace
    assert {
        key: existing_trace[key] for key in ("file", "symbol", "route")
    } == {
        key: valid_existing.traceability[key]
        for key in ("file", "symbol", "route")
    }


def test_traceability_discards_invalid_primary_without_guessing() -> None:
    stage3 = {
        "test_targets": [{
            "symbol": "create_project", "file": "app/projects.py",
            "behavior": "Persist a new project",
        }],
        "api_endpoints": [{
            "method": "POST", "route": "/projects",
            "handler": "create_project", "file": "app/projects.py",
        }],
    }
    case = CaseBatch.model_validate({
        "test_cases": [_case(
            title="Unrelated operation",
            description="No matching implementation details",
            traceability={
                "file": "guessed.py",
                "symbol": "guessed_symbol",
                "route": "/guessed",
            },
        )]
    }).test_cases[0]

    trace = TraceabilityMapper().map([case], stage3)[0].traceability

    assert not {"file", "symbol", "route"}.intersection(trace)


def test_generation_runs_completion_pass_for_uncovered_branch() -> None:
    positive = _case(
        title="Valid balance below 1000",
        description="calculate_interest balance below 1000",
        category="positive",
    )
    boundary = _case(
        id="TC-2",
        title="Boundary balance below 1000",
        description="calculate_interest balance below 1000 boundary",
        category="boundary",
        steps=["Submit a balance of 999"],
        expected_results=["The below 1000 tier is used"],
    )
    provider = Mock()
    provider.generate_structured.side_effect = [
        CaseBatch.model_validate({"test_cases": [positive]}),
        CaseBatch.model_validate({"test_cases": [boundary]}),
    ]
    stage3 = {
        "test_targets": [{
            "symbol": "calculate_interest", "file": "utils.py",
            "behavior": "Calculate tiered interest", "branches": ["balance below 1000"],
        }]
    }

    result = GenerationAgent(client=provider).generate(stage3)

    assert provider.generate_structured.call_count == 2
    assert result["coverage_summary"]["function_coverage"] == 100
    assert result["coverage_summary"]["branch_coverage"] == 100
    assert result["total_after_deduplication"] == 2


def test_large_target_set_is_preemptively_split_into_batches() -> None:
    targets = [
        {"symbol": f"function_{index}", "file": "large_module.py", "behavior": f"Behavior {index}"}
        for index in range(10)
    ]
    provider = Mock()
    provider.generate_structured.side_effect = [
        CaseBatch.model_validate({
            "test_cases": [
                _case(
                    id=f"TC-{index}", title=f"Call function_{index}",
                    description=f"Exercise function_{index}",
                    steps=[f"Invoke function_{index}"],
                    traceability={"symbol": f"function_{index}", "symbols": [f"function_{index}"]},
                )
                for index in indices
            ]
        })
        for indices in (range(4), range(4, 8), range(8, 10))
    ]

    result = GenerationAgent(
        client=provider, max_batch_functions=4,
        estimated_tokens_per_case=650, safe_output_tokens=12_000,
    ).generate({"test_targets": targets})

    assert provider.generate_structured.call_count == 3
    assert result["coverage_summary"]["function_coverage"] == 100
    assert result["total_after_deduplication"] == 10
    prompts = [call.kwargs["user_prompt"] for call in provider.generate_structured.call_args_list]
    assert all(prompt.count('"symbol": "function_') <= 4 for prompt in prompts)


def test_completion_budget_scales_with_estimated_batch_size() -> None:
    agent = GenerationAgent(client=Mock(), estimated_tokens_per_case=650, safe_output_tokens=12_000)

    assert agent._completion_budget(2) == 1_560
    assert agent._completion_budget(14) == 10_920
    assert agent._completion_budget(90) == 12_000


def test_truncated_batch_is_retried_as_smaller_scopes() -> None:
    targets = [
        {"symbol": "first", "file": "module.py", "behavior": "First"},
        {"symbol": "second", "file": "module.py", "behavior": "Second"},
    ]
    provider = Mock()
    provider.generate_structured.side_effect = [
        TruncatedStructuredResponseError("response truncated due to token limit"),
        CaseBatch.model_validate({"test_cases": [_case(title="Call first", description="first", steps=["Invoke first"], traceability={"symbol": "first", "symbols": ["first"]})]}),
        CaseBatch.model_validate({"test_cases": [_case(id="TC-2", title="Call second", description="second", steps=["Invoke second"], traceability={"symbol": "second", "symbols": ["second"]})]}),
    ]

    result = GenerationAgent(client=provider, max_batch_functions=4).generate(
        {"test_targets": targets}
    )

    assert provider.generate_structured.call_count == 3
    assert result["coverage_summary"]["function_coverage"] == 100


def test_non_converging_completion_returns_partial_result() -> None:
    target = {
        "symbol": "calculate_interest", "file": "utils.py",
        "behavior": "Calculate interest", "branches": ["balance exactly 5000"],
    }
    provider = Mock()
    provider.generate_structured.side_effect = [
        CaseBatch.model_validate({"test_cases": [
            _case(title="Calculate interest", description="calculate_interest", traceability={"symbol": "calculate_interest"})
        ]}),
        CaseBatch.model_validate({"test_cases": [
            _case(id="TC-2", title="Unrelated tier", description="calculate_interest other tier", steps=["Use another tier"], traceability={"symbol": "calculate_interest"})
        ]}),
        CaseBatch.model_validate({"test_cases": [
            _case(id="TC-3", title="Still unrelated", description="calculate_interest default", steps=["Use default"], traceability={"symbol": "calculate_interest"})
        ]}),
    ]

    result = GenerationAgent(client=provider).generate({"test_targets": [target]})

    assert provider.generate_structured.call_count == 3
    assert result["generation_status"] == "partial_coverage_incomplete"
    assert result["generated_test_cases"]
    assert len(result["uncovered_requirements"]) == 2


def test_single_target_truncation_returns_partial_result() -> None:
    provider = Mock()
    provider.generate_structured.side_effect = TruncatedStructuredResponseError(
        "response truncated due to token limit"
    )
    target = {
        "symbol": "tiny_function", "file": "tiny.py", "behavior": "Return a value"
    }

    result = GenerationAgent(client=provider).generate({"test_targets": [target]})

    assert provider.generate_structured.call_count == 1
    assert result["generation_status"] == "partial_coverage_incomplete"
    assert result["generated_test_cases"] == []
    assert result["uncovered_requirements"][0]["symbol"] == "tiny_function"


def test_all_providers_rate_limited_returns_partial_result() -> None:
    request = httpx.Request("POST", "https://provider")
    error = RateLimitError(
        "rate limited",
        response=httpx.Response(429, request=request),
        body={"error": {"type": "rate_limit_exceeded"}},
    )
    primary, fallback = Mock(), Mock()
    primary.generate_structured.side_effect = error
    fallback.generate_structured.side_effect = error
    client = ResilientStructuredOutputClient(
        primary, fallback, max_attempts=1, sleep=Mock()
    )
    target = {"symbol": "tiny_function", "file": "tiny.py", "behavior": "Return"}

    result = GenerationAgent(client=client).generate({"test_targets": [target]})

    assert result["generation_status"] == "partial_coverage_incomplete"
    assert result["generation_reason"] == "all_providers_rate_limited"
    assert result["generated_test_cases"] == []
    primary.generate_structured.assert_called_once()
    fallback.generate_structured.assert_called_once()


def test_generation_requests_only_detected_application_lifecycle_tests() -> None:
    stage3 = {
        "entrypoints": [
            {
                "path": "app/main.py",
                "symbol": "create_app",
                "purpose": "FastAPI application factory",
            }
        ],
        "execution_flows": [
            {
                "name": "Application startup",
                "entrypoint": "lifespan",
                "steps": [
                    "Run the startup handler",
                    "Register API routers with include_router",
                    "Initialize dependencies",
                    "Connect to database",
                ],
                "files": ["app/main.py"],
            }
        ],
    }
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case()]}
    )

    GenerationAgent(client=provider).generate(stage3)

    prompt = provider.generate_structured.call_args.kwargs["user_prompt"]
    assert "application_initialization" in prompt
    assert "startup_event" in prompt
    assert "router_registration" in prompt
    assert "dependency_initialization" in prompt
    assert "database_service_startup" in prompt
    assert '"execution_flows"' not in prompt
    assert '"entrypoints"' not in prompt


def _obsolete_generation_prompt_scopes_regeneration_plan_to_actions() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case(id="TC-2", title="Improved partial case")]}
    )
    payload = {
        "regeneration_plan": _plan(),
        "test_cases_to_improve": [
            _case(id="TC-2", title="Partial case"),
            _case(id="TC-3", title="Failed case"),
        ],
    }

    GenerationAgent(client=provider).generate(payload)

    prompt = provider.generate_structured.call_args.kwargs["user_prompt"]
    assert "TC-2" in prompt and "TC-3" in prompt
    assert "Do not reproduce the existing suite" in prompt
    request = provider.generate_structured.call_args.kwargs
    assert request["response_model"] is CaseBatch
    assert "only one valid JSON object" in request["system_prompt"]
    assert '"test_cases"' in prompt
    assert "Valid category values" not in prompt
    assert "Do not add markdown" not in prompt


def test_standard_and_regeneration_use_identical_structured_contract() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case()]}
    )
    agent = GenerationAgent(client=provider)

    agent.generate({})
    standard = provider.generate_structured.call_args.kwargs
    agent.generate(
        {
            "regeneration_plan": {
                **_plan(),
                "actions": [
                    {"action": "UPDATE", "test_case_id": "TC-1", "category": None}
                ],
            },
        }
    )
    regeneration = provider.generate_structured.call_args.kwargs

    assert regeneration["response_model"] is standard["response_model"] is CaseBatch
    assert regeneration["system_prompt"] == standard["system_prompt"]


def test_optimization_regeneration_uses_minimal_context_and_valid_batch(
    caplog,
) -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case(id="TC-2", category="security")]}
    )
    payload = {
        "project_summary": "Relevant project context",
        "api_endpoints": [{"method": "POST", "route": "/projects"}],
        "test_generation": {"generated_test_cases": ["FULL_SUITE_SENTINEL"]},
        "test_verification": {"results": ["VERIFICATION_SENTINEL"]},
        "quality_optimization": {"history": ["HISTORY_SENTINEL"]},
        "regeneration_plan": {
            **_plan(),
            "failed_test_cases": [],
            "actions": [
                {"action": "ADD", "category": "security", "test_case_id": None},
                {"action": "UPDATE", "test_case_id": "TC-2", "category": None},
            ],
        },
        "test_cases_to_improve": [_case(id="TC-2")],
    }

    result = GenerationAgent(client=provider).generate(payload)

    request = provider.generate_structured.call_args.kwargs
    prompt = request["user_prompt"]
    assert request["response_model"] is CaseBatch
    assert result["generated_test_cases"][0]["id"] == "TC-2"
    assert "TC-2" in prompt and "security" in prompt
    assert "Relevant project context" not in prompt
    assert "FULL_SUITE_SENTINEL" not in prompt
    assert "VERIFICATION_SENTINEL" not in prompt
    assert "HISTORY_SENTINEL" not in prompt
    assert "Submit request" not in prompt
    assert len(prompt) < 3_000
    assert "prompt_length=" in caplog.text
    assert "existing_test_cases=0" in caplog.text
    assert "requested_regenerated_cases=2" in caplog.text
    assert "generated_cases=1" in caplog.text


def _obsolete_regeneration_prompt_preserves_target_grounding_and_stage5_feedback(
    caplog,
) -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case(id="TC-2")]}
    )
    payload = {
        "project_summary": "OMIT_REPOSITORY_SUMMARY",
        "test_targets": [
            {
                "symbol": "create_project",
                "file": "projects.py",
                "signature": "create_project(data: ProjectCreate) -> Project",
                "branches": ["duplicate name"],
                "edge_cases": ["empty name"],
            },
            {
                "symbol": "list_users",
                "file": "users.py",
                "signature": "list_users()",
            },
        ],
        "api_endpoints": [
            {
                "method": "POST", "route": "/projects",
                "handler": "create_project", "file": "projects.py",
                "request_type": "ProjectCreate", "response_type": "Project",
            },
            {
                "method": "GET", "route": "/users",
                "handler": "list_users", "file": "users.py",
            },
        ],
        "data_models": [
            {"name": "ProjectCreate", "file": "models.py", "fields": ["name"]},
            {"name": "User", "file": "users.py", "fields": ["email"]},
        ],
        "analyzed_files": [
            {
                "path": "projects.py", "purpose": "project API",
                "key_symbols": ["create_project"],
            },
            {
                "path": "users.py", "purpose": "OMIT_UNRELATED_FILE",
                "key_symbols": ["list_users"],
            },
        ],
        "regeneration_plan": {
            **_plan(),
            "actions": [{
                "action": "UPDATE", "test_case_id": "TC-2",
                "target_symbol": "create_project",
                "coverage_requirement": "duplicate name",
            }],
        },
        "test_cases_to_improve": [
            _case(
                id="TC-2",
                title="OMIT_FAILED_TEST_BODY",
                traceability={
                    "source_files": ["projects.py"],
                    "symbols": ["create_project"],
                },
            )
        ],
        "regeneration_verification": {
            "results": [{
                "test_case_id": "TC-2",
                "status": "Failed",
                "evidence": [{
                    "file": "projects.py", "symbol": "create_project",
                    "line": 12, "detail": "duplicate guard",
                }],
                "findings": [{
                    "check": "behavior_semantics", "status": "Failed",
                    "detail": "Expected conflict was not asserted",
                    "evidence": [],
                }],
            }]
        },
    }

    GenerationAgent(client=provider).generate(payload)

    prompt = provider.generate_structured.call_args.kwargs["user_prompt"]
    for expected in (
        "Repair each failed or partially verified test",
        "TC-2", "Failed", "Expected conflict was not asserted",
        "duplicate name", "create_project",
        "create_project(data: ProjectCreate)", "empty name",
        "ProjectCreate", "/projects", "projects.py",
    ):
        assert expected in prompt
    for omitted in (
        "OMIT_REPOSITORY_SUMMARY", "OMIT_FAILED_TEST_BODY",
        "OMIT_UNRELATED_FILE", "list_users", "/users",
        "verification_evidence", "duplicate guard",
    ):
        assert omitted not in prompt
    assert len(prompt) < 3_000
    assert "Regeneration feedback reduction" in caplog.text
    assert "before_bytes=" in caplog.text
    assert "after_bytes=" in caplog.text
    assert "bytes_saved=" in caplog.text
    assert "estimated_tokens_saved=" in caplog.text


def test_regeneration_context_removes_evidence_and_keeps_required_feedback() -> None:
    payload = {
        "regeneration_plan": {
            "actions": [{
                "action": "UPDATE",
                "test_case_id": "TC-7",
                "target_symbol": "create_project",
                "coverage_requirement": "duplicate name",
            }],
        },
        "test_cases_to_improve": [_case(id="TC-7")],
        "regeneration_verification": {
            "results": [{
                "test_case_id": "TC-7",
                "status": "Failed",
                "evidence": [{
                    "file": "projects.py",
                    "symbol": "create_project",
                    "detail": "large raw evidence object",
                }],
                "findings": [{
                    "status": "Failed",
                    "detail": "Expected conflict was not asserted",
                }],
            }],
        },
    }

    context = GenerationAgent._regeneration_context(payload)

    assert context["feedback"] == [{
        "failed_test_id": "TC-7",
        "verification_status": "Failed",
        "failure_reason": ["Expected conflict was not asserted"],
        "missing_coverage": "duplicate name",
        "target_symbol": "create_project",
    }]
    assert "verification_evidence" not in context["feedback"][0]


def test_stage6_provider_exhaustion_returns_recoverable_partial_result() -> None:
    class ExhaustedProvider:
        def generate_structured_capacity_aware(self, **kwargs):
            error = RuntimeError("cooldown")
            raise AllProvidersExhaustedError(
                "all_providers_rate_limited", last_error=error
            )

        def generate_structured(self, **kwargs):
            raise AssertionError("Stage 6 must use capacity-aware routing")

    result = GenerationAgent(client=ExhaustedProvider()).generate({
        "regeneration_plan": {
            **_plan(),
            "actions": [{
                "action": "UPDATE",
                "test_case_id": "TC-2",
                "category": None,
            }],
        },
        "test_cases_to_improve": [_case(id="TC-2")],
    })

    assert result["generated_test_cases"] == []
    assert result["generation_status"] == "partial_coverage_incomplete"
    assert result["generation_reason"] == "all_providers_rate_limited"


def _obsolete_generation_prompt_selects_only_related_grounding() -> None:
    provider = Mock()
    provider.generate_structured.return_value = CaseBatch.model_validate(
        {"test_cases": [_case()]}
    )
    payload = {
        "project_summary": "OMIT_SUMMARY",
        "architecture": "OMIT_ARCHITECTURE",
        "test_targets": [{
            "symbol": "create_project",
            "file": "projects.py",
            "signature": "create_project(data: ProjectCreate) -> Project",
            "behavior": "OMIT_BEHAVIOR",
            "branches": ["duplicate name"],
            "edge_cases": ["empty name"],
            "dependencies": ["OMIT_DEPENDENCY"],
        }],
        "api_endpoints": [
            {
                "method": "POST", "route": "/projects",
                "handler": "create_project", "file": "projects.py",
                "request_type": "ProjectCreate", "response_type": "Project",
            },
            {
                "method": "GET", "route": "/users",
                "handler": "list_users", "file": "users.py",
            },
        ],
        "business_rules": [
            {
                "description": "Project names are unique",
                "files": ["projects.py"], "symbols": ["create_project"],
            },
            {
                "description": "OMIT_UNRELATED_RULE",
                "files": ["users.py"], "symbols": ["list_users"],
            },
        ],
        "data_models": [
            {"name": "ProjectCreate", "file": "models.py", "fields": ["name"]},
            {"name": "User", "file": "users.py", "fields": ["email"]},
        ],
    }

    GenerationAgent(client=provider).generate(payload)

    prompt = provider.generate_structured.call_args.kwargs["user_prompt"]
    for expected in (
        "create_project(data: ProjectCreate)",
        "duplicate name", "empty name", "/projects",
        "Project names are unique", "ProjectCreate",
    ):
        assert expected in prompt
    for omitted in (
        "OMIT_SUMMARY", "OMIT_ARCHITECTURE", "OMIT_BEHAVIOR",
        "OMIT_DEPENDENCY", "/users", "OMIT_UNRELATED_RULE",
    ):
        assert omitted not in prompt


def _obsolete_executable_scenario_planner_creates_and_reuses_resource_identifier() -> None:
    stage3 = {
        "api_endpoints": [
            {
                "method": "POST", "route": "/items",
                "handler": "create_item", "request_model": "ItemCreate",
                "response_model": "ItemOut", "success_status_codes": [201],
            },
            {
                "method": "GET", "route": "/items/{item_id}",
                "handler": "read_item", "response_model": "ItemOut",
                "success_status_codes": [200], "error_status_codes": [404],
            },
            {
                "method": "PUT", "route": "/items/{item_id}",
                "handler": "update_item", "request_model": "ItemUpdate",
                "response_model": "ItemOut", "success_status_codes": [200],
            },
            {
                "method": "DELETE", "route": "/items/{item_id}",
                "handler": "delete_item", "success_status_codes": [204],
            },
        ],
        "pydantic_schemas": [
            {
                "name": "ItemCreate",
                "fields": [
                    {
                        "name": "name", "type": "str", "required": True,
                        "has_default": False, "default": None,
                        "min_length": 3, "max_length": 30, "examples": [],
                    },
                    {
                        "name": "description", "type": "str | None",
                        "required": False, "has_default": True,
                        "default": None, "examples": [],
                    },
                ],
            },
            {
                "name": "ItemUpdate",
                "fields": [{
                    "name": "name", "type": "str | None", "required": False,
                    "has_default": True, "default": None, "examples": [],
                }],
            },
            {
                "name": "ItemOut",
                "fields": [
                    {"name": "id", "type": "int", "required": True},
                    {"name": "name", "type": "str", "required": True},
                ],
            },
        ],
    }
    cases = [
        CaseBatch.model_validate({"test_cases": [_case(
            id="TC-GET", title="Get existing item",
            description="GET /items/{item_id} returns the existing item",
            category="positive",
            steps=["GET /items/{item_id}"],
            expected_results=["HTTP 200"],
            traceability={
                "route": "/items/{item_id}", "method": "GET",
                "symbol": "read_item",
            },
        )]}).test_cases[0],
        CaseBatch.model_validate({"test_cases": [_case(
            id="TC-PUT", title="Update existing item",
            description="PUT /items/{item_id} updates the existing item",
            category="positive",
            steps=["PUT /items/{item_id}"],
            expected_results=["HTTP 200"],
            traceability={
                "route": "/items/{item_id}", "method": "PUT",
                "symbol": "update_item",
            },
        )]}).test_cases[0],
    ]

    planned = ExecutableScenarioPlanner().plan(cases, stage3)

    assert [case.traceability["method"] for case in planned] == [
        "POST", "GET", "PUT", "DELETE",
    ]
    setup, get_case, put_case, cleanup = planned
    assert setup.traceability["request_payload"] == {"name": "test-name"}
    assert setup.traceability["identifier_fields"] == ["id"]
    assert get_case.traceability["path_parameters"]["item_id"]["source"] == (
        "captured_identifier"
    )
    assert put_case.traceability["request_payload"] == {"name": "test-name"}
    assert put_case.traceability["expected_http_status"] == 200
    assert None not in put_case.traceability["request_payload"].values()
    assert cleanup.traceability["cleanup"] is True
    assert cleanup.traceability["path_parameters"]["item_id"]["source"] == (
        "captured_identifier"
    )
    output = {
        "generated_test_cases": [
            case.model_dump(mode="json") for case in planned
        ]
    }
    assert GenerationAgent.is_current_output(output, stage3) is True
    stale = {
        "generated_test_cases": [{
            **output["generated_test_cases"][0],
            "traceability": {"route": "/items", "method": "POST"},
        }]
    }
    assert GenerationAgent.is_current_output(stale, stage3) is False
