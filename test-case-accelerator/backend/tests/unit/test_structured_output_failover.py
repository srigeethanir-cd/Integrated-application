from unittest.mock import Mock

import httpx
import pytest
from openai import APIConnectionError, BadRequestError, RateLimitError

from app.agents.code_understanding.agent import CodeUnderstandingResult
from app.agents.code_understanding.client import (
    AllProvidersExhaustedError,
    MalformedStructuredResponseError,
    ResilientStructuredOutputClient,
    ProviderCooldownRegistry,
)


def _result() -> CodeUnderstandingResult:
    return CodeUnderstandingResult(project_summary="ok", architecture="layered")


def _connection_error() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "https://provider"))


def _bad_request() -> BadRequestError:
    request = httpx.Request("POST", "https://provider")
    return BadRequestError(
        "invalid schema",
        response=httpx.Response(400, request=request),
        body={"error": "json_validate_failed"},
    )


def _call(client: ResilientStructuredOutputClient):
    return client.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=CodeUnderstandingResult,
    )


def test_groq_success_returns_without_fallback() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(groq, cerebras, sleep=Mock())

    assert _call(client) == _result()
    cerebras.generate_structured.assert_not_called()


def test_groq_retry_then_success() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.side_effect = [_connection_error(), _result()]
    client = ResilientStructuredOutputClient(groq, cerebras, sleep=Mock())

    assert _call(client) == _result()
    assert groq.generate_structured.call_count == 2
    cerebras.generate_structured.assert_not_called()


def test_groq_retries_then_cerebras_succeeds_with_identical_request() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.side_effect = _connection_error()
    cerebras.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(
        groq, cerebras, max_attempts=2, sleep=Mock()
    )

    assert _call(client) == _result()
    assert groq.generate_structured.call_count == 2
    assert cerebras.generate_structured.call_count == 1
    assert groq.generate_structured.call_args.kwargs == (
        cerebras.generate_structured.call_args.kwargs
    )


def test_both_providers_failing_reports_provider_exhaustion() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.side_effect = _connection_error()
    cerebras.generate_structured.side_effect = _connection_error()
    client = ResilientStructuredOutputClient(
        groq, cerebras, max_attempts=2, sleep=Mock()
    )

    with pytest.raises(AllProvidersExhaustedError) as captured:
        _call(client)
    assert captured.value.reason == "all_providers_unavailable"
    assert {item["provider"] for item in captured.value.attempts} == {
        "groq", "cerebras"
    }
    assert "groq attempt" in str(captured.value)
    assert "cerebras attempt" in str(captured.value)


def test_http_400_falls_back_without_retry() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.side_effect = _bad_request()
    cerebras.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(groq, cerebras, sleep=Mock())

    assert _call(client) == _result()
    groq.generate_structured.assert_called_once()
    cerebras.generate_structured.assert_called_once()


def test_schema_validation_failure_falls_back() -> None:
    groq, cerebras = Mock(), Mock()
    groq.generate_structured.side_effect = MalformedStructuredResponseError(
        "invalid structured result"
    )
    cerebras.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(groq, cerebras, sleep=Mock())

    assert _call(client) == _result()
    groq.generate_structured.assert_called_once()
    cerebras.generate_structured.assert_called_once()


def test_payload_rate_limit_failure_falls_back_to_cerebras() -> None:
    groq, cerebras = Mock(), Mock()
    request = httpx.Request("POST", "https://api.groq.com/openai/v1")
    groq.generate_structured.side_effect = BadRequestError(
        "rate_limit_exceeded",
        response=httpx.Response(413, request=request),
        body={"error": {"type": "tokens_per_minute", "limit": 8000}},
    )
    cerebras.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(groq, cerebras, sleep=Mock())

    assert _call(client) == _result()
    assert groq.generate_structured.call_count == 1
    cerebras.generate_structured.assert_called_once()


def test_repeated_429_honors_retry_after_before_failover() -> None:
    now = [0.0]
    delays = []
    def sleep(delay: float) -> None:
        delays.append(delay)
        now[0] += delay
    request = httpx.Request("POST", "https://provider")
    rate_limit = RateLimitError(
        "rate limited",
        response=httpx.Response(429, request=request, headers={"Retry-After": "3"}),
        body={"error": {"type": "rate_limit_exceeded"}},
    )
    primary, fallback = Mock(), Mock()
    primary.generate_structured.side_effect = rate_limit
    fallback.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(
        primary, fallback, max_attempts=2, sleep=sleep,
        cooldown_registry=ProviderCooldownRegistry(clock=lambda: now[0]),
    )

    assert _call(client) == _result()
    assert primary.generate_structured.call_count == 2
    fallback.generate_structured.assert_called_once()
    assert delays == [3.0]


def test_long_retry_after_fails_over_without_waiting() -> None:
    request = httpx.Request("POST", "https://provider")
    rate_limit = RateLimitError(
        "rate limited",
        response=httpx.Response(
            429, request=request, headers={"Retry-After": "45"}
        ),
        body={"error": {"type": "rate_limit_exceeded"}},
    )
    primary, fallback, sleep = Mock(), Mock(), Mock()
    primary.generate_structured.side_effect = rate_limit
    fallback.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(
        primary, fallback, max_attempts=3, sleep=sleep,
        failover_threshold_seconds=30,
        cooldown_registry=ProviderCooldownRegistry(clock=lambda: 0),
    )

    assert _call(client) == _result()
    primary.generate_structured.assert_called_once()
    fallback.generate_structured.assert_called_once()
    sleep.assert_not_called()


def test_failover_preserves_structured_output_contract() -> None:
    primary, fallback = Mock(), Mock()
    primary.generate_structured.side_effect = _connection_error()
    fallback.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(
        primary, fallback, max_attempts=1, sleep=Mock()
    )

    result = _call(client)

    assert isinstance(result, CodeUnderstandingResult)
    assert (
        fallback.generate_structured.call_args.kwargs["response_model"]
        is CodeUnderstandingResult
    )


def test_capacity_aware_routing_bypasses_undersized_primary() -> None:
    primary, fallback = Mock(), Mock()
    primary.can_fit_structured_request.return_value = False
    fallback.can_fit_structured_request.return_value = True
    fallback.generate_structured.return_value = _result()
    client = ResilientStructuredOutputClient(
        primary,
        fallback,
        max_attempts=1,
        sleep=Mock(),
        cooldown_registry=ProviderCooldownRegistry(clock=lambda: 0),
    )

    result = client.generate_structured_capacity_aware(
        system_prompt="system",
        user_prompt="large-stage-6-prompt",
        response_model=CodeUnderstandingResult,
    )

    assert result == _result()
    primary.generate_structured.assert_not_called()
    fallback.generate_structured.assert_called_once()
