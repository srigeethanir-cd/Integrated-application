from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, SecretStr

from app.agents.code_understanding.agent import CodeUnderstandingResult
from app.agents.code_understanding.client import (
    GroqStructuredOutputClient,
    MalformedStructuredResponseError,
    ProviderTokenBudgetError,
    ReasoningUsageProfile,
    RollingTokenBudget,
    TruncatedStructuredResponseError,
)
from app.core.config import settings
from app.core.config import (
    LLMProviderConfigurationError,
    validate_llm_provider_configuration,
)
from app.dependencies.code_understanding import (
    get_test_generation_agent,
)
from app.schemas.test_case import TestCaseBatch as CaseBatch


def test_structured_output_client_returns_parsed_response() -> None:
    parsed = CodeUnderstandingResult(
        project_summary="Example",
        architecture="Layered",
    )
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()))]
    )
    client = GroqStructuredOutputClient(sdk_client, "configured-model")

    response = client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CodeUnderstandingResult,
    )

    assert response == parsed
    request = sdk_client.chat.completions.create.call_args.kwargs
    assert request["model"] == "configured-model"
    assert request["messages"][0] == {"role": "system", "content": "system"}
    assert request["messages"][1]["content"].startswith("user")
    assert "Required JSON schema" in request["messages"][1]["content"]
    assert request["response_format"] == {"type": "json_object"}


def test_structured_output_client_rejects_malformed_response(caplog) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="{}"))]
    )
    client = GroqStructuredOutputClient(sdk_client, "configured-model")

    with pytest.raises(MalformedStructuredResponseError):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CodeUnderstandingResult,
        )

    assert "Invalid raw structured provider response: {}" in caplog.text


def test_structured_output_client_rejects_invalid_json() -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="not-json"))]
    )
    client = GroqStructuredOutputClient(sdk_client, "configured-model")

    with pytest.raises(MalformedStructuredResponseError):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CodeUnderstandingResult,
        )


def _valid_structured_test_case(case_id: str) -> dict:
    return {
        "id": case_id,
        "title": f"Case {case_id}",
        "description": "Validate behavior",
        "category": "positive",
        "priority": "high",
        "severity": "major",
        "preconditions": [],
        "steps": ["Invoke target"],
        "expected_results": ["Target succeeds"],
        "requirement_ids": [],
        "business_rule_ids": [],
        "traceability": None,
    }


def _structured_batch_client(test_cases: list[object]):
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(
            message=Mock(content=__import__("json").dumps({
                "test_cases": test_cases,
            })),
            finish_reason="stop",
        )],
    )
    return GroqStructuredOutputClient(
        sdk_client, "configured-model"
    ), sdk_client


def test_test_case_batch_removes_empty_string_padding(caplog) -> None:
    first = _valid_structured_test_case("TC-1")
    second = _valid_structured_test_case("TC-2")
    client, _ = _structured_batch_client([first, "", second])

    result = client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CaseBatch,
    )

    assert [case.model_dump() for case in result.test_cases] == [first, second]
    assert "removed_element_count=1" in caplog.text
    assert "empty_string" in caplog.text


def test_test_case_batch_removes_null_padding(caplog) -> None:
    valid = _valid_structured_test_case("TC-1")
    client, _ = _structured_batch_client([None, valid, None])

    result = client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CaseBatch,
    )

    assert [case.model_dump() for case in result.test_cases] == [valid]
    assert "removed_element_count=2" in caplog.text
    assert "null" in caplog.text


def test_test_case_batch_preserves_valid_dictionaries() -> None:
    valid = _valid_structured_test_case("TC-1")
    client, _ = _structured_batch_client([valid])

    result = client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CaseBatch,
    )

    assert result.test_cases[0].model_dump() == valid


@pytest.mark.parametrize("invalid_item", [7, True, "padding", []])
def test_test_case_batch_rejects_unexpected_element_types(
    invalid_item,
) -> None:
    client, _ = _structured_batch_client([
        _valid_structured_test_case("TC-1"),
        invalid_item,
    ])

    with pytest.raises(MalformedStructuredResponseError):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CaseBatch,
        )


def test_test_case_batch_rejects_malformed_dictionary() -> None:
    client, _ = _structured_batch_client([{"id": "TC-incomplete"}])

    with pytest.raises(MalformedStructuredResponseError):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CaseBatch,
        )


def test_structured_output_client_reports_token_truncation(caplog) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content='{"project_summary":"cut'), finish_reason="length")],
        usage=Mock(completion_tokens=4096),
        id="truncated-response",
    )
    client = GroqStructuredOutputClient(
        sdk_client, "gpt-oss-120b", max_completion_tokens=16_384
    )

    with pytest.raises(TruncatedStructuredResponseError, match="truncated"):
        client.generate_structured(
            system_prompt="system", user_prompt="user",
            response_model=CodeUnderstandingResult,
        )

    assert "response truncated due to token limit" in caplog.text


def test_small_batch_budget_is_capped_below_provider_tpm() -> None:
    parsed = CodeUnderstandingResult(project_summary="Example", architecture="Layered")
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()), finish_reason="stop")]
    )
    client = GroqStructuredOutputClient(
        sdk_client,
        "openai/gpt-oss-20b",
        max_completion_tokens=16_384,
        model_max_output_tokens=65_536,
        tokens_per_minute=8_000,
        token_reserve=256,
    )

    client.generate_structured(
        system_prompt="system", user_prompt="two-function batch",
        response_model=CodeUnderstandingResult,
        max_completion_tokens=10_920,
    )

    requested = sdk_client.chat.completions.create.call_args.kwargs["max_completion_tokens"]
    assert 512 <= requested < 8_000


def _stage3_budget_client(estimated_tokens: int):
    parsed = CodeUnderstandingResult(
        project_summary="Example", architecture="Layered"
    )
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(
            message=Mock(content=parsed.model_dump_json()),
            finish_reason="stop",
        )],
        usage=Mock(completion_tokens=800),
    )
    client = GroqStructuredOutputClient(
        sdk_client, "configured-model", max_completion_tokens=2_000
    )
    client._estimate_expected_completion_tokens = Mock(
        return_value=estimated_tokens
    )
    return client, sdk_client


def test_stage3_output_budget_safe_logs_telemetry(caplog) -> None:
    client, sdk_client = _stage3_budget_client(1_000)

    client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CodeUnderstandingResult,
        context=SimpleNamespace(dependency_run_id="run", files=[]),
    )

    sdk_client.chat.completions.create.assert_called_once()
    assert "estimated_completion_tokens=1000" in caplog.text
    assert "prompt_tokens=" in caplog.text
    assert "schema_tokens=" in caplog.text
    assert "remaining_completion_budget=1000" in caplog.text
    assert "provider_completion_limit=2000" in caplog.text
    assert "actual_completion_tokens=800" in caplog.text
    assert "estimation_error_tokens=200" in caplog.text
    assert "percentage_error=25.00" in caplog.text


def test_stage3_output_budget_warns_above_eighty_percent(caplog) -> None:
    client, sdk_client = _stage3_budget_client(1_601)

    client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CodeUnderstandingResult,
        context=SimpleNamespace(dependency_run_id="run", files=[]),
    )

    sdk_client.chat.completions.create.assert_called_once()
    assert "exceeds 80% of the provider limit" in caplog.text


def test_stage3_output_budget_fails_before_provider_when_exceeded() -> None:
    client, sdk_client = _stage3_budget_client(2_001)

    with pytest.raises(
        ProviderTokenBudgetError,
        match="requires 2001 tokens but only 2000",
    ):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CodeUnderstandingResult,
            context=SimpleNamespace(dependency_run_id="run", files=[]),
        )

    sdk_client.chat.completions.create.assert_not_called()


class _FlatCompletionModel(BaseModel):
    summary: str
    count: int


class _NestedCompletionItem(BaseModel):
    name: str
    details: dict[str, str]


class _NestedCompletionModel(BaseModel):
    summary: str
    groups: list[list[_NestedCompletionItem]]


def _completion_estimate(
    file_count: int,
    *,
    response_model: type[BaseModel] = _FlatCompletionModel,
    prompt_tokens: int = 8_000,
    safety_margin: float = 0.2,
) -> int:
    client = GroqStructuredOutputClient(
        Mock(),
        "configured-model",
        completion_estimation_safety_margin=safety_margin,
    )
    schema = response_model.model_json_schema()
    schema_tokens = client._estimate_tokens(
        "", "", __import__("json").dumps(schema, separators=(",", ":"))
    )
    return client._estimate_expected_completion_tokens(
        response_model=response_model,
        context=SimpleNamespace(files=[object()] * file_count),
        schema_tokens=schema_tokens,
        prompt_tokens=prompt_tokens,
    )


def test_stage3_completion_estimate_scales_for_small_repository() -> None:
    estimate = _completion_estimate(2)

    assert 512 < estimate < 1_500


def test_stage3_completion_estimate_scales_for_medium_repository() -> None:
    small = _completion_estimate(2)
    medium = _completion_estimate(25)

    assert small < medium < 3_500


def test_stage3_completion_estimate_scales_for_large_repository() -> None:
    medium = _completion_estimate(25)
    large = _completion_estimate(100)

    assert medium < large < 10_000


def test_stage3_completion_estimate_accounts_for_nested_response_models() -> None:
    flat = _completion_estimate(5, response_model=_FlatCompletionModel)
    nested = _completion_estimate(5, response_model=_NestedCompletionModel)

    assert nested > flat


def test_stage3_completion_prompt_contribution_is_capped() -> None:
    moderate_prompt = _completion_estimate(5, prompt_tokens=16_384)
    very_large_prompt = _completion_estimate(5, prompt_tokens=1_000_000)

    assert very_large_prompt == moderate_prompt


def test_stage3_completion_estimate_applies_configurable_safety_margin() -> None:
    without_margin = _completion_estimate(10, safety_margin=0)
    with_margin = _completion_estimate(10, safety_margin=0.25)

    assert with_margin == pytest.approx(without_margin * 1.25, abs=1)


def test_rolling_window_exhaustion_routes_to_fallback_without_live_request() -> None:
    now = [0.0]
    budget = RollingTokenBudget(8_000, clock=lambda: now[0])
    parsed = CodeUnderstandingResult(project_summary="Example", architecture="Layered")
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()), finish_reason="stop")],
        usage=Mock(prompt_tokens=2_500, completion_tokens=5_000),
    )
    primary = GroqStructuredOutputClient(
        sdk_client, "openai/gpt-oss-20b", max_completion_tokens=7_000,
        model_max_output_tokens=65_536, tokens_per_minute=8_000,
        token_reserve=0, rolling_token_budget=budget,
    )
    primary.generate_structured(
        system_prompt="system", user_prompt="first request",
        response_model=CodeUnderstandingResult, max_completion_tokens=5_000,
    )
    fallback = Mock()
    fallback.generate_structured.return_value = parsed
    from app.agents.code_understanding.client import ResilientStructuredOutputClient
    resilient = ResilientStructuredOutputClient(primary, fallback, max_attempts=1)

    result = resilient.generate_structured(
        system_prompt="system", user_prompt="next request",
        response_model=CodeUnderstandingResult, max_completion_tokens=1_024,
    )

    assert result == parsed
    assert sdk_client.chat.completions.create.call_count == 1
    fallback.generate_structured.assert_called_once()


def test_reasoning_model_budget_includes_overhead_and_uses_low_effort() -> None:
    parsed = CodeUnderstandingResult(project_summary="Example", architecture="Layered")
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()), finish_reason="stop")],
        usage=Mock(
            prompt_tokens=100,
            completion_tokens=1_200,
            completion_tokens_details=Mock(reasoning_tokens=999),
        ),
    )
    client = GroqStructuredOutputClient(
        sdk_client, "gpt-oss-120b", max_completion_tokens=16_384
    )

    client.generate_structured(
        system_prompt="system", user_prompt="single test",
        response_model=CodeUnderstandingResult, max_completion_tokens=1_024,
    )

    request = sdk_client.chat.completions.create.call_args.kwargs
    assert request["max_completion_tokens"] == 4_096
    assert request["reasoning_effort"] == "low"
    assert client._reasoning_usage_profile.average == 999


def test_measured_reasoning_overhead_uses_proportionate_budget() -> None:
    parsed = CodeUnderstandingResult(project_summary="Example", architecture="Layered")
    profile = ReasoningUsageProfile()
    profile.observe(130)
    profile.observe(131)
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()), finish_reason="stop")],
        usage=Mock(prompt_tokens=100, completion_tokens=323),
    )
    client = GroqStructuredOutputClient(
        sdk_client, "gpt-oss-120b", max_completion_tokens=16_384,
        reasoning_usage_profile=profile,
    )

    client.generate_structured(
        system_prompt="system", user_prompt="batch",
        response_model=CodeUnderstandingResult, max_completion_tokens=6_240,
    )

    requested = sdk_client.chat.completions.create.call_args.kwargs[
        "max_completion_tokens"
    ]
    assert requested == 6_725
    assert requested < 16_384


def test_rpm_exhaustion_routes_to_fallback_with_tokens_available() -> None:
    budget = RollingTokenBudget(100_000, request_limit=1, clock=lambda: 0.0)
    parsed = CodeUnderstandingResult(project_summary="Example", architecture="Layered")
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()), finish_reason="stop")],
        usage=Mock(prompt_tokens=100, completion_tokens=100),
    )
    primary = GroqStructuredOutputClient(
        sdk_client, "configured-model", max_completion_tokens=2_000,
        tokens_per_minute=100_000, requests_per_minute=1,
        rolling_token_budget=budget,
    )
    primary.generate_structured(
        system_prompt="system", user_prompt="first",
        response_model=CodeUnderstandingResult, max_completion_tokens=1_024,
    )
    fallback = Mock()
    fallback.generate_structured.return_value = parsed
    from app.agents.code_understanding.client import ResilientStructuredOutputClient
    resilient = ResilientStructuredOutputClient(primary, fallback, max_attempts=1)

    result = resilient.generate_structured(
        system_prompt="system", user_prompt="second",
        response_model=CodeUnderstandingResult, max_completion_tokens=1_024,
    )

    assert result == parsed
    assert budget.used() == 200
    assert sdk_client.chat.completions.create.call_count == 1
    fallback.generate_structured.assert_called_once()


def _obsolete_generation_provider_uses_configured_token_limits(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    monkeypatch.setattr(settings, "groq_tokens_per_minute", 8_000)
    monkeypatch.setattr(settings, "groq_model_max_output_tokens", 65_536)

    provider = get_test_generation_agent()._client._primary

    assert provider._tokens_per_minute == 8_000
    assert provider._model_max_output_tokens == 65_536


def test_structured_output_client_rejects_missing_choice() -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(choices=[])
    client = GroqStructuredOutputClient(sdk_client, "configured-model")

    with pytest.raises(MalformedStructuredResponseError):
        client.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=CodeUnderstandingResult,
        )


def _obsolete_generation_agent_provider_configures_groq_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    monkeypatch.setattr(settings, "groq_model", "configured-groq-model")

    provider = get_test_generation_agent()._client._primary

    assert provider._model == "configured-groq-model"
    assert str(provider._client.base_url) == "https://api.groq.com/openai/v1/"


def _obsolete_generation_agent_provider_rejects_empty_groq_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", SecretStr(""))

    with pytest.raises(RuntimeError, match="GROQ_API_KEY is required"):
        get_test_generation_agent()


def _obsolete_valid_cerebras_model_configures_distinct_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("groq-key"))
    monkeypatch.setattr(settings, "groq_model", "openai/gpt-oss-20b")
    monkeypatch.setattr(settings, "cerebras_api_key", SecretStr("cerebras-key"))
    monkeypatch.setattr(settings, "cerebras_model", "gpt-oss-120b")

    provider = get_test_generation_agent()._client

    assert provider._primary._model == "openai/gpt-oss-20b"
    assert provider._fallback._model == "gpt-oss-120b"
    assert str(provider._fallback._client.base_url) == "https://api.cerebras.ai/v1/"


def test_invalid_cerebras_model_raises_configuration_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cerebras_model", "llama-3.3-70b")

    with pytest.raises(
        LLMProviderConfigurationError, match="Invalid Cerebras model configuration"
    ):
        validate_llm_provider_configuration(settings)


def _obsolete_structured_output_client_logs_telemetry(caplog) -> None:
    import logging
    parsed = CodeUnderstandingResult(
        project_summary="Example",
        architecture="Layered",
    )
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=parsed.model_dump_json()))]
    )
    client = GroqStructuredOutputClient(sdk_client, "configured-model")

    # Mock context
    class MockFile:
        def __init__(self, path: str, content: str) -> None:
            self.path = path
            self.content = content
            
        def model_dump(self, mode: str = "json") -> dict:
            return {"path": self.path, "content": self.content, "extra": "data"}

    class MockContext:
        def __init__(self) -> None:
            self.project_id = "test-project-id"
            self.dependency_run_id = "test-run-id"
            self.files = [MockFile("app/main.py", "print('hello')")]
            self.omitted_files = []

        def model_dump(self, mode: str = "json") -> dict:
            return {
                "project_id": self.project_id,
                "dependency_run_id": self.dependency_run_id,
                "files": [f.model_dump() for f in self.files],
                "omitted_files": []
            }

    context = MockContext()
    
    with caplog.at_level(logging.INFO):
        client.generate_structured(
            system_prompt="system-prompt",
            user_prompt="user-prompt",
            response_model=CodeUnderstandingResult,
            context=context,
            max_file_characters=2000,
            max_total_characters=5000,
        )

    # Check logs
    assert "Project ID: test-project-id" in caplog.text
    assert "Dependency Run ID: test-run-id" in caplog.text
    assert "Files included/skipped: Included = 1, Skipped = 0" in caplog.text
    assert "Raw source size: 14" in caplog.text
    assert "===== STAGE 3 PROMPT SUMMARY =====" in caplog.text
