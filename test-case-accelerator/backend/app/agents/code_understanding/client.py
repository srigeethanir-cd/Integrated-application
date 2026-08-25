"""Concrete OpenAI-compatible structured-output client for Stage 3."""

import json
import logging
import math
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import os
import time
import threading
import uuid
from collections import deque
from collections.abc import Callable

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    BadRequestError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError
from openai import OpenAI

logger = logging.getLogger(__name__)


class RollingTokenBudget:
    """Thread-safe trailing-window token ledger shared across API requests."""

    def __init__(
        self, limit: int, *, request_limit: int | None = None,
        window_seconds: float = 60, clock=time.monotonic,
    ):
        self.limit = limit
        self.request_limit = request_limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._entries: deque[tuple[str, float, int]] = deque()
        self._lock = threading.Lock()

    def reserve(self, tokens: int) -> str | None:
        with self._lock:
            self._prune()
            if (
                sum(item[2] for item in self._entries) + tokens > self.limit
                or (
                    self.request_limit is not None
                    and len(self._entries) >= self.request_limit
                )
            ):
                return None
            reservation = uuid.uuid4().hex
            self._entries.append((reservation, self._clock(), tokens))
            return reservation

    def settle(self, reservation: str, actual_tokens: int) -> None:
        with self._lock:
            now = self._clock()
            self._entries = deque(
                (key, timestamp, actual_tokens if key == reservation else tokens)
                for key, timestamp, tokens in self._entries
            )
            self._prune(now)

    def release(self, reservation: str) -> None:
        with self._lock:
            self._entries = deque(
                item for item in self._entries if item[0] != reservation
            )

    def used(self) -> int:
        with self._lock:
            self._prune()
            return sum(item[2] for item in self._entries)

    def request_count(self) -> int:
        with self._lock:
            self._prune()
            return len(self._entries)

    def _prune(self, now: float | None = None) -> None:
        now = self._clock() if now is None else now
        while self._entries and now - self._entries[0][1] >= self._window_seconds:
            self._entries.popleft()


class ReasoningUsageProfile:
    """Running provider/model reasoning overhead used for future budgets."""

    def __init__(self) -> None:
        self._samples = 0
        self._reasoning_tokens = 0
        self._lock = threading.Lock()

    def completion_budget(self, raw_output_tokens: int, *, reasoning_model: bool) -> int:
        if not reasoning_model:
            return raw_output_tokens
        with self._lock:
            if self._samples == 0:
                return raw_output_tokens * 4
            average = self._reasoning_tokens / self._samples
        return math.ceil(raw_output_tokens + average * 1.75 + 256)

    def observe(self, reasoning_tokens: int) -> None:
        if reasoning_tokens < 0:
            return
        with self._lock:
            self._samples += 1
            self._reasoning_tokens += reasoning_tokens

    @property
    def average(self) -> float:
        with self._lock:
            return self._reasoning_tokens / self._samples if self._samples else 0.0


_TOKEN_BUDGETS: dict[tuple[str, str, int, int | None], RollingTokenBudget] = {}
_TOKEN_BUDGETS_LOCK = threading.Lock()
_REASONING_PROFILES: dict[tuple[str, str], ReasoningUsageProfile] = {}


def _shared_token_budget(
    provider: str, model: str, limit: int, request_limit: int | None
) -> RollingTokenBudget:
    key = (provider, model, limit, request_limit)
    with _TOKEN_BUDGETS_LOCK:
        return _TOKEN_BUDGETS.setdefault(
            key, RollingTokenBudget(limit, request_limit=request_limit)
        )


def _shared_reasoning_profile(provider: str, model: str) -> ReasoningUsageProfile:
    with _TOKEN_BUDGETS_LOCK:
        return _REASONING_PROFILES.setdefault(
            (provider, model), ReasoningUsageProfile()
        )


class StructuredOutputClientError(RuntimeError):
    """Base error raised by the Stage 3 LLM provider boundary."""


class MalformedStructuredResponseError(StructuredOutputClientError):
    """Raised when the provider returns no validated structured output."""


class TruncatedStructuredResponseError(MalformedStructuredResponseError):
    """Raised when a provider stops because the completion token limit was hit."""


class ProviderTokenBudgetError(StructuredOutputClientError):
    """Raised before dispatch when a provider cannot fit a useful completion."""


class AllProvidersExhaustedError(StructuredOutputClientError):
    """Raised after every configured structured-output provider has failed."""

    def __init__(
        self, reason: str, *, last_error: Exception,
        attempts: list[dict[str, object]] | None = None,
    ) -> None:
        self.attempts = attempts or []
        summary = "; ".join(
            f"{item['provider']} attempt {item['attempt']}: "
            f"{item['error_type']} ({item['message']})"
            for item in self.attempts
        )
        super().__init__(f"{reason}: {summary}" if summary else reason)
        self.reason = reason
        self.last_error = last_error


class ProviderCooldownRegistry:
    """Process-wide cooldown deadlines for temporarily exhausted providers."""

    def __init__(self, *, clock=time.monotonic) -> None:
        self._clock = clock
        self._deadlines: dict[str, float] = {}
        self._lock = threading.Lock()

    def start(self, provider: str, duration: float) -> None:
        with self._lock:
            self._deadlines[provider] = max(
                self._deadlines.get(provider, 0), self._clock() + duration
            )

    def remaining(self, provider: str) -> float:
        with self._lock:
            return max(0.0, self._deadlines.get(provider, 0) - self._clock())


_PROVIDER_COOLDOWNS = ProviderCooldownRegistry()


class GroqStructuredOutputClient:
    """Generate structured output through Groq's OpenAI-compatible API."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        max_completion_tokens: int | None = None,
        model_max_output_tokens: int | None = None,
        tokens_per_minute: int | None = None,
        token_reserve: int = 256,
        rolling_token_budget: RollingTokenBudget | None = None,
        requests_per_minute: int | None = None,
        reasoning_usage_profile: ReasoningUsageProfile | None = None,
        completion_estimation_safety_margin: float = 0.2,
    ) -> None:
        self._client = client
        self._model = model
        try:
            self._max_completion_tokens = (
                max_completion_tokens
                if max_completion_tokens is not None
                else int(os.getenv("MAX_COMPLETION_TOKENS", "4096"))
            )
        except ValueError as error:
            raise ValueError("MAX_COMPLETION_TOKENS must be an integer") from error
        if self._max_completion_tokens <= 0:
            raise ValueError("MAX_COMPLETION_TOKENS must be greater than zero")
        self._model_max_output_tokens = model_max_output_tokens
        self._tokens_per_minute = tokens_per_minute
        self._token_reserve = token_reserve
        if completion_estimation_safety_margin < 0:
            raise ValueError(
                "completion_estimation_safety_margin must not be negative"
            )
        self._completion_estimation_safety_margin = (
            completion_estimation_safety_margin
        )
        self._rolling_token_budget = rolling_token_budget or (
            _shared_token_budget(
                self._provider_name(), model, tokens_per_minute,
                requests_per_minute,
            )
            if tokens_per_minute is not None
            else None
        )
        self._reasoning_usage_profile = reasoning_usage_profile or (
            _shared_reasoning_profile(self._provider_name(), model)
        )

    def can_fit_structured_request(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        minimum_completion_tokens: int = 512,
    ) -> bool:
        """Return whether this provider can accept the prompt before dispatch."""
        if self._tokens_per_minute is None:
            return True
        schema = json.dumps(
            response_model.model_json_schema(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        prompt_tokens = self._estimate_tokens(
            system_prompt, user_prompt, schema
        )
        return (
            self._tokens_per_minute - prompt_tokens - self._token_reserve
            >= minimum_completion_tokens
        )

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_completion_tokens: int | None = None,
        context: object | None = None,
        max_file_characters: int = 2500,
        max_total_characters: int = 10000,
    ) -> BaseModel:
        schema = json.dumps(
            response_model.model_json_schema(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        provider = self._provider_name()
        prompt_tokens = self._estimate_tokens(system_prompt, user_prompt, "")
        schema_tokens = self._estimate_tokens("", "", schema)
        total_prompt_tokens = prompt_tokens + schema_tokens
        reasoning_model = "gpt-oss" in self._model.casefold()
        raw_output_tokens = max_completion_tokens or (
            max(1, self._max_completion_tokens // 4)
            if reasoning_model
            else self._max_completion_tokens
        )
        requested_tokens = min(
            self._reasoning_usage_profile.completion_budget(
                raw_output_tokens,
                reasoning_model=reasoning_model,
            ),
            self._max_completion_tokens,
            self._model_max_output_tokens or self._max_completion_tokens,
        )
        available_tokens = (
            self._tokens_per_minute - total_prompt_tokens - self._token_reserve
            if self._tokens_per_minute is not None
            else requested_tokens
        )
        effective_tokens = min(requested_tokens, available_tokens)
        if effective_tokens < 512:
            logger.warning(
                "Structured-output preflight rejected provider=%s model=%s "
                "estimated_prompt_tokens=%d requested_completion_tokens=%d "
                "tokens_per_minute=%s available_completion_tokens=%d",
                provider, self._model, total_prompt_tokens, requested_tokens,
                self._tokens_per_minute, effective_tokens,
            )
            raise ProviderTokenBudgetError(
                f"{provider} token budget cannot fit this structured request"
            )
        is_stage3 = (
            context is not None
            and getattr(context, "dependency_run_id", None) is not None
        )
        estimated_completion_tokens: int | None = None
        if is_stage3:
            estimated_completion_tokens = (
                self._estimate_expected_completion_tokens(
                    response_model=response_model,
                    context=context,
                    schema_tokens=schema_tokens,
                    prompt_tokens=prompt_tokens,
                )
            )
            remaining_completion_budget = (
                effective_tokens - estimated_completion_tokens
            )
            logger.info(
                "Stage 3 output budget estimated_completion_tokens=%d "
                "prompt_tokens=%d schema_tokens=%d "
                "remaining_completion_budget=%d "
                "provider_completion_limit=%d",
                estimated_completion_tokens,
                prompt_tokens,
                schema_tokens,
                remaining_completion_budget,
                effective_tokens,
            )
            if estimated_completion_tokens > effective_tokens:
                logger.error(
                    "Stage 3 output budget exceeded "
                    "estimated_completion_tokens=%d "
                    "provider_completion_limit=%d",
                    estimated_completion_tokens,
                    effective_tokens,
                )
                raise ProviderTokenBudgetError(
                    "Stage 3 estimated completion requires "
                    f"{estimated_completion_tokens} tokens but only "
                    f"{effective_tokens} completion tokens are available; "
                    "reduce Stage 3 output scope or increase the configured "
                    "provider completion budget"
                )
            if estimated_completion_tokens > effective_tokens * 0.8:
                logger.warning(
                    "Stage 3 estimated completion exceeds 80%% of the "
                    "provider limit estimated_completion_tokens=%d "
                    "provider_completion_limit=%d utilization=%.2f",
                    estimated_completion_tokens,
                    effective_tokens,
                    estimated_completion_tokens / effective_tokens,
                )

        estimated_total_tokens = total_prompt_tokens + effective_tokens
        reservation = (
            self._rolling_token_budget.reserve(estimated_total_tokens)
            if self._rolling_token_budget is not None
            else "untracked"
        )
        if reservation is None:
            logger.info(
                "Structured-output rolling-window preflight skipped provider=%s "
                "model=%s used_tokens=%d used_requests=%d "
                "requested_total_tokens=%d token_limit=%d request_limit=%s",
                provider, self._model, self._rolling_token_budget.used(),
                self._rolling_token_budget.request_count(), estimated_total_tokens,
                self._rolling_token_budget.limit,
                self._rolling_token_budget.request_limit,
            )
            raise ProviderTokenBudgetError(
                f"{provider} rolling token budget is exhausted"
            )
        logger.info(
            "Structured-output request provider=%s model=%s prompt_length=%d "
            "schema_length=%d estimated_prompt_tokens=%d "
            "raw_output_tokens=%d reasoning_overhead_average=%.2f "
            "requested_completion_tokens=%d effective_completion_tokens=%d "
            "tokens_per_minute=%s",
            provider,
            self._model,
            len(system_prompt) + len(user_prompt),
            len(schema),
            total_prompt_tokens, raw_output_tokens,
            self._reasoning_usage_profile.average,
            requested_tokens, effective_tokens,
            self._tokens_per_minute,
        )

        # Telemetry logging block before LLM request
        if context is not None:
            project_id = getattr(context, "project_id", None)
            dependency_run_id = getattr(context, "dependency_run_id", None)
            files = getattr(context, "files", [])
            omitted_files = getattr(context, "omitted_files", [])
            
            files_included = len(files)
            files_skipped = len(omitted_files)
            
            per_file_chars = {}
            per_file_metadata = {}
            total_metadata_size = 0
            file_contribs = []
            
            for f in files:
                path = getattr(f, "path", "")
                content = getattr(f, "content", "")
                content_len = len(content)
                per_file_chars[path] = content_len
                
                # Serialize each file once, then derive metadata from that dump.
                if hasattr(f, "model_dump"):
                    f_dict = f.model_dump(mode="json")
                elif hasattr(f, "__dict__"):
                    f_dict = dict(f.__dict__)
                else:
                    f_dict = {}
                f_ser_str = json.dumps(
                    f_dict, ensure_ascii=False, separators=(",", ":")
                )
                metadata = dict(f_dict)
                metadata.pop("content", None)
                meta_str = json.dumps(
                    metadata, ensure_ascii=False, separators=(",", ":")
                )
                meta_size = len(meta_str)
                per_file_metadata[path] = meta_size
                total_metadata_size += meta_size
                
                # Serialized size of the file context
                f_ser_size = len(f_ser_str)
                
                file_contribs.append({
                    "path": path,
                    "raw_chars": content_len,
                    "serialized_chars": f_ser_size,
                    "metadata_chars": meta_size
                })
            
            raw_source_chars = sum(per_file_chars.values())
            
            if hasattr(context, "model_dump"):
                repo_context_json = json.dumps(context.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))
            else:
                repo_context_json = ""
            repo_context_size = len(repo_context_json)
            
            # calculate wire request size
            wire_payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_prompt}\n\nRequired JSON schema:\n{schema}"},
                ],
                "response_format": {"type": "json_object"},
                "max_completion_tokens": effective_tokens,
            }
            if "gpt-oss" in self._model.casefold():
                wire_payload["reasoning_effort"] = "low"
            wire_request_size = len(json.dumps(wire_payload, ensure_ascii=False, separators=(",", ":")))
            
            # 10 largest files contributing to the prompt (sorted by serialized_chars descending)
            top_files = sorted(file_contribs, key=lambda x: x["serialized_chars"], reverse=True)[:10]
            
            logger.info("Project ID: %s", project_id)
            logger.info("Dependency Run ID: %s", dependency_run_id)
            logger.info("Files included/skipped: Included = %d, Skipped = %d", files_included, files_skipped)
            logger.info("Per-file source chars: %s", per_file_chars)
            logger.info("Per-file metadata chars: %s", per_file_metadata)
            logger.info("Raw source size: %d", raw_source_chars)
            logger.info("repository_context size: %d", repo_context_size)
            logger.info("System prompt size: %d", len(system_prompt))
            logger.info("User prompt size: %d", len(user_prompt))
            logger.info("Output schema size: %d", len(schema))
            logger.info("Final wire size: %d", wire_request_size)
            logger.info("Estimated prompt tokens: %d", prompt_tokens)
            logger.info("Estimated schema tokens: %d", schema_tokens)
            logger.info("Active prompt limits: Per-file limit = %d, Total source limit = %d", max_file_characters, max_total_characters)
            
            logger.info("10 largest files contributing to the prompt:")
            for idx, item in enumerate(top_files, 1):
                logger.info(
                    "[%d] File: %s | Raw chars: %d | Serialized chars: %d | Metadata chars: %d",
                    idx, item["path"], item["raw_chars"], item["serialized_chars"], item["metadata_chars"]
                )
            
            summary = (
                "\n===== STAGE 3 PROMPT SUMMARY =====\n"
                f"Files included: {files_included}\n"
                f"Files skipped: {files_skipped}\n"
                f"Raw source: {raw_source_chars}\n"
                f"Metadata: {total_metadata_size}\n"
                f"Repository context: {repo_context_size}\n"
                f"Schema: {len(schema)}\n"
                f"Wire size: {wire_request_size}\n"
                f"Estimated prompt tokens: {prompt_tokens}\n"
                f"Estimated schema tokens: {schema_tokens}\n"
                "================================="
            )
            print(summary)
            logger.info(summary)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (f"{user_prompt}\n\nRequired JSON schema:\n{schema}"),
                    },
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=effective_tokens,
                **(
                    {"reasoning_effort": "low"}
                    if "gpt-oss" in self._model.casefold()
                    else {}
                ),
            )
        except BadRequestError as error:
            if self._rolling_token_budget is not None:
                self._rolling_token_budget.release(reservation)
            logger.error(
                "Structured-output provider=%s model=%s rejected response "
                "metadata=%s failed_generation=%s",
                provider,
                self._model,
                getattr(error, "body", None),
                self._raw_error_response(error),
            )
            raise
        except Exception:
            if self._rolling_token_budget is not None:
                self._rolling_token_budget.release(reservation)
            raise
        if self._rolling_token_budget is not None:
            usage = getattr(response, "usage", None)
            prompt_usage = getattr(usage, "prompt_tokens", 0)
            completion_usage = getattr(usage, "completion_tokens", 0)
            actual_tokens = sum(
                item if isinstance(item, int) else 0
                for item in (prompt_usage, completion_usage)
            )
            self._rolling_token_budget.settle(
                reservation, actual_tokens or estimated_total_tokens
            )
        usage = getattr(response, "usage", None)
        completion_usage = getattr(usage, "completion_tokens", 0)
        if (
            is_stage3
            and estimated_completion_tokens is not None
            and isinstance(completion_usage, int)
            and completion_usage > 0
        ):
            estimation_error = estimated_completion_tokens - completion_usage
            percentage_error = estimation_error / completion_usage * 100
            logger.info(
                "Stage 3 completion estimate telemetry "
                "estimated_completion_tokens=%d actual_completion_tokens=%d "
                "estimation_error_tokens=%d percentage_error=%.2f",
                estimated_completion_tokens,
                completion_usage,
                estimation_error,
                percentage_error,
            )
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = getattr(details, "reasoning_tokens", 0)
        if isinstance(details, dict):
            reasoning_tokens = details.get("reasoning_tokens", 0)
        reasoning_reported = isinstance(reasoning_tokens, int)
        if not reasoning_reported:
            reasoning_tokens = 0
        if reasoning_reported:
            self._reasoning_usage_profile.observe(reasoning_tokens)
        logger.info(
            "Structured-output usage provider=%s model=%s reasoning_tokens=%d "
            "average_reasoning_tokens=%.2f usage=%s",
            provider, self._model, reasoning_tokens,
            self._reasoning_usage_profile.average, usage,
        )
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise MalformedStructuredResponseError(
                "The LLM returned no structured result"
            ) from error
        if content is None:
            raise MalformedStructuredResponseError(
                "The LLM returned no structured result"
            )
        choice = response.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            logger.error(
                "Structured response truncated due to token limit provider=%s "
                "model=%s max_completion_tokens=%d usage=%s response_id=%s",
                provider, self._model, effective_tokens,
                getattr(response, "usage", None), getattr(response, "id", None),
            )
            raise TruncatedStructuredResponseError(
                "Structured response truncated due to token limit"
            )
        try:
            parsed_content = json.loads(content)
            from app.schemas.test_case import TestCaseBatch

            if (
                response_model is TestCaseBatch
                and isinstance(parsed_content, dict)
                and isinstance(parsed_content.get("test_cases"), list)
            ):
                sanitized_test_cases = []
                removed_types = []
                for item in parsed_content["test_cases"]:
                    if item is None:
                        removed_types.append("null")
                    elif isinstance(item, str) and item == "":
                        removed_types.append("empty_string")
                    else:
                        sanitized_test_cases.append(item)
                if removed_types:
                    parsed_content = {
                        **parsed_content,
                        "test_cases": sanitized_test_cases,
                    }
                    logger.info(
                        "Structured TestCaseBatch response normalized "
                        "removed_element_count=%d removed_element_types=%s",
                        len(removed_types),
                        sorted(set(removed_types)),
                    )
            return response_model.model_validate(parsed_content)
        except (json.JSONDecodeError, ValidationError) as error:
            logger.error("Invalid raw structured provider response: %s", content)
            logger.error(
                "Structured response validation metadata provider=%s model=%s "
                "finish_reason=%s usage=%s response_id=%s provider_metadata=%s",
                provider,
                self._model,
                getattr(choice, "finish_reason", None),
                getattr(response, "usage", None),
                getattr(response, "id", None),
                {
                    "system_fingerprint": getattr(
                        response, "system_fingerprint", None
                    ),
                    "service_tier": getattr(response, "service_tier", None),
                },
            )
            raise MalformedStructuredResponseError(
                "The LLM returned a malformed structured result"
            ) from error

    def _provider_name(self) -> str:
        base_url = str(getattr(self._client, "base_url", "")).casefold()
        if "cerebras" in base_url:
            return "cerebras"
        if "groq" in base_url:
            return "groq"
        return "openai-compatible"

    @staticmethod
    def _estimate_tokens(system_prompt: str, user_prompt: str, schema: str) -> int:
        # Conservative tokenizer-independent approximation used only for preflight.
        return max(1, (len(system_prompt) + len(user_prompt) + len(schema) + 3) // 4)

    def _estimate_expected_completion_tokens(
        self,
        *,
        response_model: type[BaseModel],
        context: object,
        schema_tokens: int,
        prompt_tokens: int,
    ) -> int:
        """Estimate Stage 3 output from response shape and repository cardinality."""
        files = getattr(context, "files", ()) or ()
        properties, arrays, objects, max_depth = self._response_schema_metrics(
            response_model.model_json_schema()
        )
        response_shape_tokens = max(
            64,
            math.ceil(schema_tokens * 0.25)
            + properties * 6
            + arrays * 12
            + objects * 8
            + max_depth * 12,
        )
        repository_output_tokens = len(files) * 64
        prompt_reasoning_tokens = min(256, max(0, prompt_tokens // 64))
        expected_response_tokens = max(
            512,
            response_shape_tokens
            + repository_output_tokens
            + prompt_reasoning_tokens,
        )
        return math.ceil(
            expected_response_tokens
            * (1 + self._completion_estimation_safety_margin)
        )

    @staticmethod
    def _response_schema_metrics(
        schema: dict[str, object],
    ) -> tuple[int, int, int, int]:
        """Count output-bearing schema structure, including referenced models."""
        definitions = schema.get("$defs", {})
        seen_refs: set[str] = set()

        def visit(node: object, depth: int) -> tuple[int, int, int, int]:
            if not isinstance(node, dict):
                return 0, 0, 0, depth
            reference = node.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                if reference in seen_refs:
                    return 0, 0, 0, depth
                seen_refs.add(reference)
                definition_name = reference.rsplit("/", 1)[-1]
                if isinstance(definitions, dict):
                    return visit(definitions.get(definition_name), depth)

            node_type = node.get("type")
            properties_node = node.get("properties", {})
            property_count = (
                len(properties_node) if isinstance(properties_node, dict) else 0
            )
            array_count = 1 if node_type == "array" else 0
            object_count = (
                1 if node_type == "object" or property_count > 0 else 0
            )
            max_depth = depth
            children: list[object] = []
            if isinstance(properties_node, dict):
                children.extend(properties_node.values())
            if "items" in node:
                children.append(node["items"])
            for keyword in ("anyOf", "oneOf", "allOf"):
                variants = node.get(keyword)
                if isinstance(variants, list):
                    children.extend(variants)
            for child in children:
                child_metrics = visit(child, depth + 1)
                property_count += child_metrics[0]
                array_count += child_metrics[1]
                object_count += child_metrics[2]
                max_depth = max(max_depth, child_metrics[3])
            return property_count, array_count, object_count, max_depth

        return visit(schema, 1)

    @staticmethod
    def _raw_error_response(error: BadRequestError) -> object:
        body = getattr(error, "body", None)
        if body is not None:
            if isinstance(body, dict):
                detail = body.get("error", body)
                if isinstance(detail, dict) and "failed_generation" in detail:
                    return detail["failed_generation"]
            return body
        response = getattr(error, "response", None)
        return getattr(response, "text", None) or str(error)


def is_transient_provider_error(error: Exception) -> bool:
    """Return whether an error represents temporary provider unavailability."""
    if isinstance(error, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True
    return isinstance(error, APIStatusError) and error.status_code >= 500


def is_rate_limit_error(error: Exception) -> bool:
    if isinstance(error, RateLimitError):
        return True
    return isinstance(error, APIStatusError) and error.status_code == 429


class ResilientStructuredOutputClient:
    """Apply deterministic retry and provider failover to structured requests."""

    def __init__(
        self,
        primary: GroqStructuredOutputClient,
        fallback: GroqStructuredOutputClient | None,
        *,
        primary_name: str = "groq",
        fallback_name: str = "cerebras",
        max_attempts: int = 3,
        retry_base_delay: float = 0.25,
        max_retry_delay: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
        cooldown_registry: ProviderCooldownRegistry | None = None,
        failover_threshold_seconds: float = 30.0,
        enable_failover: bool = True,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._primary = primary
        self._fallback = fallback
        # Retain introspection compatibility with the original provider client.
        self._model = primary._model
        self._client = primary._client
        self._primary_name = primary_name
        self._fallback_name = fallback_name
        self._max_attempts = max_attempts
        self._retry_base_delay = retry_base_delay
        self._max_retry_delay = max_retry_delay
        self._sleep = sleep
        self._cooldowns = cooldown_registry or _PROVIDER_COOLDOWNS
        self._failover_threshold_seconds = failover_threshold_seconds
        self._enable_failover = enable_failover

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_completion_tokens: int | None = None,
        context: object | None = None,
        max_file_characters: int = 2500,
        max_total_characters: int = 10000,
    ) -> BaseModel:
        request = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response_model": response_model,
            "max_completion_tokens": max_completion_tokens,
            "context": context,
            "max_file_characters": max_file_characters,
            "max_total_characters": max_total_characters,
        }
        records: list[dict[str, object]] = []
        providers = [(self._primary_name, self._primary)]
        if (
            self._enable_failover
            and self._fallback is not None
            and self._fallback is not self._primary
        ):
            providers.append((self._fallback_name, self._fallback))
        last_error: Exception | None = None
        for index, (provider_name, provider) in enumerate(providers):
            try:
                result = self._attempt_provider(
                    provider, provider_name, request, self._max_attempts, records
                )
                logger.info(
                    "structured_output_complete final_provider=%s "
                    "total_provider_attempts=%d",
                    provider_name, len(records),
                )
                return result
            except Exception as error:
                last_error = error
                if index + 1 < len(providers):
                    logger.warning(
                        "provider_failover from_provider=%s to_provider=%s "
                        "reason=%s total_provider_attempts=%d",
                        provider_name, providers[index + 1][0],
                        type(error).__name__, len(records),
                    )
        assert last_error is not None
        reason = (
            "all_providers_rate_limited"
            if records and all(item["rate_limited"] for item in records)
            else "all_providers_unavailable"
        )
        logger.error(
            "all_providers_exhausted reason=%s total_provider_attempts=%d "
            "attempts=%s",
            reason, len(records), records,
        )
        raise AllProvidersExhaustedError(
            reason, last_error=last_error, attempts=records
        ) from last_error

    def generate_structured_capacity_aware(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_completion_tokens: int | None = None,
    ) -> BaseModel:
        """Route Stage 6 work only to providers that can fit its prompt."""
        request = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response_model": response_model,
            "max_completion_tokens": max_completion_tokens,
            "context": None,
            "max_file_characters": 2500,
            "max_total_characters": 10000,
        }
        providers = [(self._primary_name, self._primary)]
        if (
            self._enable_failover
            and self._fallback is not None
            and self._fallback is not self._primary
        ):
            providers.append((self._fallback_name, self._fallback))
        feasible = []
        records: list[dict[str, object]] = []
        for provider_name, provider in providers:
            can_fit = getattr(provider, "can_fit_structured_request", None)
            if callable(can_fit) and not can_fit(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
            ):
                error = ProviderTokenBudgetError(
                    f"{provider_name} token budget cannot fit this structured request"
                )
                records.append(self._attempt_record(
                    provider_name, 0, error,
                    retry_after=0, rate_limited=False,
                ))
                logger.info(
                    "provider_skipped_before_dispatch provider=%s "
                    "reason=prompt_token_budget",
                    provider_name,
                )
                continue
            feasible.append((provider_name, provider))
        last_error: Exception | None = None
        for provider_name, provider in feasible:
            try:
                return self._attempt_provider(
                    provider, provider_name, request,
                    self._max_attempts, records,
                )
            except Exception as error:
                last_error = error
        if last_error is None:
            last_error = ProviderTokenBudgetError(
                "No configured provider can fit the Stage 6 prompt"
            )
        reason = (
            "all_providers_token_budget_exhausted"
            if not feasible
            else "all_providers_unavailable"
        )
        raise AllProvidersExhaustedError(
            reason, last_error=last_error, attempts=records
        ) from last_error

    def _attempt_provider(
        self,
        provider: GroqStructuredOutputClient,
        provider_name: str,
        request: dict[str, object],
        attempts: int,
        records: list[dict[str, object]],
    ) -> BaseModel:
        logger.info("provider_selected provider=%s", provider_name)
        for attempt in range(1, attempts + 1):
            cooldown = self._cooldowns.remaining(provider_name)
            if cooldown > 0 and attempt == 1:
                if cooldown > self._failover_threshold_seconds:
                    error = ProviderTokenBudgetError(
                        f"{provider_name} cooldown {cooldown:.2f}s exceeds "
                        f"failover threshold {self._failover_threshold_seconds:.2f}s"
                    )
                    records.append(self._attempt_record(
                        provider_name, 0, error, retry_after=cooldown,
                        rate_limited=True,
                    ))
                    logger.warning(
                        "provider_failover_required provider=%s "
                        "retry_after_seconds=%.2f threshold_seconds=%.2f",
                        provider_name, cooldown,
                        self._failover_threshold_seconds,
                    )
                    raise error
                logger.info(
                    "Structured-output provider cooldown provider=%s "
                    "retry_count=%d cooldown_seconds=%.2f",
                    provider_name, attempt - 1, cooldown,
                )
                self._sleep(cooldown)
            try:
                result = provider.generate_structured(**request)
                records.append({
                    "provider": provider_name, "attempt": attempt,
                    "error_type": "none", "message": "success",
                    "rate_limited": False, "retry_after_seconds": 0.0,
                })
                logger.info("Final structured-output provider used: %s", provider_name)
                return result
            except Exception as error:
                rate_limited = is_rate_limit_error(error)
                delay = self._retry_delay(error, attempt)
                records.append(self._attempt_record(
                    provider_name, attempt, error, retry_after=delay,
                    rate_limited=rate_limited,
                ))
                if rate_limited:
                    self._cooldowns.start(provider_name, delay)
                logger.warning(
                    "Structured-output provider failed provider=%s retry_count=%d "
                    "attempt=%d/%d error=%s cooldown_seconds=%.2f",
                    provider_name,
                    attempt - 1,
                    attempt,
                    attempts,
                    type(error).__name__,
                    delay if rate_limited else 0,
                )
                if (
                    rate_limited
                    and delay > self._failover_threshold_seconds
                ):
                    logger.warning(
                        "provider_failover_required provider=%s retry_reason=429 "
                        "retry_after_seconds=%.2f threshold_seconds=%.2f",
                        provider_name, delay, self._failover_threshold_seconds,
                    )
                    raise
                if (
                    not is_transient_provider_error(error)
                    or attempt == attempts
                ):
                    raise
                logger.info(
                    "Retrying structured-output provider provider=%s "
                    "retry_count=%d retry_reason=%s retry_after_seconds=%.2f "
                    "attempt=%d/%d",
                    provider_name, attempt, type(error).__name__, delay,
                    attempt + 1,
                    attempts,
                )
                self._sleep(delay)
        raise AssertionError("Provider attempt loop did not return or raise")

    @staticmethod
    def _attempt_record(
        provider: str, attempt: int, error: Exception, *,
        retry_after: float, rate_limited: bool,
    ) -> dict[str, object]:
        return {
            "provider": provider,
            "attempt": attempt,
            "error_type": type(error).__name__,
            "message": str(error),
            "rate_limited": rate_limited,
            "retry_after_seconds": round(retry_after, 3),
        }

    def _retry_delay(self, error: Exception, attempt: int) -> float:
        backoff = min(
            self._retry_base_delay * (2 ** (attempt - 1)), self._max_retry_delay
        )
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        retry_after = headers.get("retry-after") if headers else None
        if retry_after is None:
            return backoff
        try:
            return max(backoff, float(retry_after))
        except (TypeError, ValueError):
            try:
                deadline = parsedate_to_datetime(str(retry_after))
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                return max(
                    backoff,
                    (deadline - datetime.now(timezone.utc)).total_seconds(),
                )
            except (TypeError, ValueError, OverflowError):
                return backoff
