"""
Agent one: requirement analysis and extraction.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

# pyrefly: ignore [missing-import]
from designlab_core.utilities.logger import get_logger

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import RequirementAnalysisAgentError
from app.prompts.prompt_manager import PromptManager
from app.shared.llm_client import LLMService, LLMServiceError


_logger = get_logger("agents.requirement_analysis")

# Maximum number of recursive halving passes before hard-failing a subchunk.
# With MAX_SPLIT_DEPTH=10 a 5M-token chunk would be reduced to ~4878 tokens — always safe.
_MAX_SPLIT_DEPTH = int(os.getenv("REQUIREMENT_ANALYSIS_MAX_SPLIT_DEPTH", "10"))
# Minimum meaningful content size in characters to prevent infinite loops on whitespace.
_MIN_CONTENT_CHARS = 10


class ActorRequirementMapping(BaseModel):
    """A source requirement/use case associated with its explicit persona."""

    actor: str
    requirement: str
    chunk_refs: list[str] = Field(default_factory=list)


# pyrefly: ignore [parse-error]
class RequirementAnalysisOutput(BaseModel):
    """
    Structured output produced by the requirement analysis agent.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actors": ["Customer"],
                "functional_requirements": [
                    "Customers can log in using email and OTP.",
                    "The system shall lock the account after 5 failed attempts.",
                ],
                "non_functional_requirements": ["Security"],
                "dependencies": ["OTP Service"],
                "business_goals": ["Increase security."],
                "edge_cases": ["Account locks after 5 failed OTP attempts."],
                "constraints": ["OTP must expire within the configured time limit."],
            }
        }
    )

    actors: list[str] = Field(default_factory=list)
    actor_requirement_mappings: list[ActorRequirementMapping] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    business_goals: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_dict_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ["functional_requirements", "non_functional_requirements", "dependencies", "business_goals", "edge_cases", "constraints"]:
                if key in data and isinstance(data[key], list):
                    new_list = []
                    for item in data[key]:
                        if isinstance(item, dict):
                            # Try to extract a meaningful string
                            desc = item.get("description", "")
                            name = item.get("name", "")
                            val = f"{name}: {desc}" if name and desc else (desc or name or str(item))
                            new_list.append(val)
                        else:
                            new_list.append(item)
                    data[key] = new_list
        return data


class RequirementAnalysisAgent(BaseAgent):
    """
    Extract actors, requirements, dependencies, goals, edge cases, and constraints.
    """

    output_schema = RequirementAnalysisOutput

    def __init__(
        self,
        prompt_manager: PromptManager | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.prompt_manager = prompt_manager or PromptManager()
        self.llm_service = llm_service or LLMService(self.prompt_manager)
        # Cache the template overhead so we only compute it once per instance.
        self._template_overhead_tokens: int | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    async def run(
        self,
        chunks: list[dict[str, Any]] | str,
        *,
        model_name: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> RequirementAnalysisOutput:
        """
        Analyze requirement chunks and return validated structured JSON.
        """
        try:
            system_prompt_str = (
                system_prompt
                or self.prompt_manager.get_requirement_analysis_system_prompt()
            )

            from app.agents.token_budget import TokenBudgetManager
            budget_manager = TokenBudgetManager(
                os.getenv("MODEL_PROVIDER", "openai"),
                os.getenv("MODEL_NAME", "gpt-4o"),
            )
            max_input_tokens = int(
                os.getenv("REQUIREMENT_ANALYSIS_MAX_INPUT_TOKENS", str(budget_manager.ceiling))
            )
            # Groq's llama-3.1-8b-instant has a 6000 TPM limit; cap safely below that.
            safe_limit = min(max_input_tokens, 5000)

            # Resolve max output tokens.
            if max_tokens is None:
                max_tokens = int(os.getenv("REQUIREMENT_ANALYSIS_MAX_OUTPUT_TOKENS", "1500"))

            # Compute and cache the fixed overhead (system + template boilerplate)
            # so every downstream method uses the same value.
            sys_tokens, template_overhead = self._get_fixed_overhead(system_prompt_str)
            available_content_tokens = safe_limit - sys_tokens - template_overhead - max_tokens
            # Ensure we have at least a minimal content window.
            if available_content_tokens < 200:
                available_content_tokens = 200
                _logger.warning(
                    "[REQUIREMENT_ANALYSIS] available_content_tokens capped to 200. "
                    "Consider reducing REQUIREMENT_ANALYSIS_MAX_OUTPUT_TOKENS or increasing "
                    "REQUIREMENT_ANALYSIS_MAX_INPUT_TOKENS."
                )

            _logger.info(
                "[REQUIREMENT_ANALYSIS] Budget: safe_limit=%d sys_tokens=%d "
                "template_overhead=%d reserved_output=%d available_content=%d",
                safe_limit, sys_tokens, template_overhead, max_tokens, available_content_tokens,
            )

            batches = self._build_batches(
                chunks,
                available_content_tokens=available_content_tokens,
                system_prompt=system_prompt_str,
            )

            outputs = []
            # Queue entries: (batch_label, content_tokens_budget, batch_data, split_depth)
            batch_queue = [(i + 1, available_content_tokens, b, 0) for i, b in enumerate(batches)]
            total_batches = len(batches)

            while batch_queue:
                batch_num, content_budget, batch, depth = batch_queue.pop(0)
                _logger.info(
                    "[REQUIREMENT_ANALYSIS] Batch %d/%d RUNNING (split_depth=%d)",
                    batch_num, total_batches, depth,
                )

                try:
                    output = await self._analyze_batch(
                        batch,
                        batch_num=batch_num,
                        total_batches=total_batches,
                        system_prompt=system_prompt_str,
                        model_name=model_name,
                        max_tokens=max_tokens,
                    )
                    outputs.append(output)
                    _logger.info(
                        "[REQUIREMENT_ANALYSIS] Batch %d/%d COMPLETED",
                        batch_num, total_batches,
                    )

                except LLMServiceError as exc:
                    exc_str = str(exc).lower()
                    is_413 = "413" in str(exc) or "payload too large" in exc_str or "request too large" in exc_str
                    is_429 = "429" in str(exc) or "rate limit" in exc_str

                    if is_429:
                        # 429 is already handled by tenacity backoff in llm_client.py — re-raise.
                        raise

                    if is_413:
                        new_budget = content_budget // 2
                        _logger.warning(
                            "[REQUIREMENT_ANALYSIS] Batch %d: 413 Payload Too Large "
                            "(split_depth=%d). Splitting batch with new budget=%d tokens.",
                            batch_num, depth, new_budget,
                        )
                        if depth >= _MAX_SPLIT_DEPTH or new_budget < _MIN_CONTENT_CHARS:
                            chunk_ref = self._get_chunk_ref(batch)
                            raise RequirementAnalysisAgentError(
                                f"Requirement analysis failed: content at chunk_ref={chunk_ref!r} "
                                f"could not be reduced to a safe request size after "
                                f"{_MAX_SPLIT_DEPTH} split passes (min budget {new_budget} tokens). "
                                f"This may indicate corrupted, binary, or non-textual content."
                            ) from exc

                        sub_batches = self._split_batch_by_content(
                            batch, new_budget, system_prompt_str
                        )
                        new_items = [(batch_num, new_budget, sb, depth + 1) for sb in sub_batches]
                        batch_queue = new_items + batch_queue
                        total_batches += len(sub_batches) - 1
                    else:
                        raise

            merged = self._merge_outputs(outputs)
            explicit_use_cases = self._extract_explicit_actor_use_cases(
                chunks,
                actors=merged.actors,
            )

            _logger.info(
                "[REQUIREMENT_ANALYSIS] COMPLETED successfully across %d effective batches.",
                total_batches,
            )
            return self._merge_explicit_use_cases(merged, explicit_use_cases)

        except (ValidationError, json.JSONDecodeError) as exc:
            _logger.error(
                "Requirement analysis response validation failed: %s",
                exc,
                exc_info=True,
            )
            raise RequirementAnalysisAgentError(
                "Requirement analysis returned invalid JSON or schema-incompatible output."
            ) from exc

        except LLMServiceError as exc:
            _logger.error("Requirement analysis LLM call failed: %s", exc, exc_info=True)
            raise RequirementAnalysisAgentError(
                f"Requirement analysis failed while invoking the LLM. "
                f"Underlying cause: {exc.__class__.__name__} - {exc}"
            ) from exc

        except Exception as exc:
            _logger.error("Unexpected requirement analysis failure: %s", exc, exc_info=True)
            raise RequirementAnalysisAgentError(
                f"Requirement analysis failed due to an unexpected backend error: "
                f"{exc.__class__.__name__} - {exc}"
            ) from exc

    # ─────────────────────────────────────────────────────────────────────────
    # Token accounting helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _get_fixed_overhead(self, system_prompt: str) -> tuple[int, int]:
        """
        Returns (sys_tokens, template_overhead_tokens).
        template_overhead is the cost of the prompt template itself with empty chunks.
        Cached after the first call.
        """
        from app.agents.token_budget import count_tokens
        sys_tokens = count_tokens(system_prompt)
        if self._template_overhead_tokens is None:
            empty_prompt = self.prompt_manager.get_requirement_analysis_prompt("")
            self._template_overhead_tokens = count_tokens(empty_prompt)
        return sys_tokens, self._template_overhead_tokens

    def _count_content_tokens(self, content: str) -> int:
        """Count tokens in a content string."""
        from app.agents.token_budget import count_tokens
        return count_tokens(content)

    # ─────────────────────────────────────────────────────────────────────────
    # Batch construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_batches(
        self,
        chunks: list[dict[str, Any]] | str,
        *,
        available_content_tokens: int,
        system_prompt: str = "",
    ) -> list[list[dict[str, Any]] | str]:
        """
        Group chunks into batches whose content fits within available_content_tokens.
        If a single chunk is already too large, split its content recursively.
        """
        if isinstance(chunks, str):
            return self._split_text_into_batches(chunks, available_content_tokens)

        # Filter irrelevant chunks.
        relevant_chunks = [c for c in chunks if c.get("context") != "irrelevant"]
        if not relevant_chunks:
            return [[]]

        batches: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        current_tokens = 0

        for chunk in relevant_chunks:
            chunk_content = str(chunk.get("content", ""))
            chunk_tokens = self._count_content_tokens(chunk_content)
            chunk_ref = self._get_chunk_ref(chunk)

            _logger.info(
                "[REQUIREMENT_ANALYSIS_CHUNK] chunk_ref=%s original_tokens=%d "
                "available_content_tokens=%d split_depth=0",
                chunk_ref, chunk_tokens, available_content_tokens,
            )

            if chunk_tokens <= available_content_tokens:
                # Chunk fits — see if it fits in the current batch.
                if current_tokens + chunk_tokens <= available_content_tokens:
                    current.append(chunk)
                    current_tokens += chunk_tokens
                else:
                    # Flush current batch, start a new one with this chunk.
                    if current:
                        batches.append(current)
                    current = [chunk]
                    current_tokens = chunk_tokens
            else:
                # Chunk is individually too large — recursively split its content.
                _logger.info(
                    "[REQUIREMENT_ANALYSIS] chunk_ref=%s requires splitting "
                    "(chunk_tokens=%d > available=%d)",
                    chunk_ref, chunk_tokens, available_content_tokens,
                )
                if current:
                    batches.append(current)
                    current = []
                    current_tokens = 0

                sub_chunks = self._split_chunk_content_recursively(
                    chunk,
                    target_tokens=available_content_tokens,
                    split_depth=0,
                    chunk_ref=chunk_ref,
                )
                # Each sub-chunk becomes its own batch to be safe.
                for sc in sub_chunks:
                    batches.append([sc])

        if current:
            batches.append(current)

        return batches

    def _split_text_into_batches(self, text: str, available_content_tokens: int) -> list[str]:
        """Split a plain string (not chunk list) into token-safe segments."""
        parts = self._split_text_recursively(text, available_content_tokens, depth=0)
        return parts or [""]

    # ─────────────────────────────────────────────────────────────────────────
    # Recursive content splitting
    # ─────────────────────────────────────────────────────────────────────────

    def _split_chunk_content_recursively(
        self,
        chunk: dict[str, Any],
        *,
        target_tokens: int,
        split_depth: int,
        chunk_ref: str,
    ) -> list[dict[str, Any]]:
        """
        Recursively split a chunk's `content` until every piece fits within target_tokens.
        Preserves original chunk_id in all sub-chunks so traceability is maintained.
        """
        content = str(chunk.get("content", ""))
        content_tokens = self._count_content_tokens(content)

        if content_tokens <= target_tokens:
            return [chunk]

        if split_depth >= _MAX_SPLIT_DEPTH:
            _logger.error(
                "[REQUIREMENT_ANALYSIS] chunk_ref=%s: max split depth %d reached "
                "at content_tokens=%d. Forcing character split.",
                chunk_ref, _MAX_SPLIT_DEPTH, content_tokens,
            )
            # Last resort: hard character split guaranteed to produce safe pieces.
            return self._hard_char_split_chunk(chunk, target_tokens, chunk_ref)

        text_parts = self._split_text_at_best_boundary(content, target_tokens)

        if len(text_parts) <= 1:
            # Boundary splitting didn't help — halve the target and try again.
            return self._hard_char_split_chunk(chunk, target_tokens, chunk_ref)

        result = []
        for part_idx, part_text in enumerate(text_parts):
            part_tokens = self._count_content_tokens(part_text)
            part_chunk = dict(chunk)
            orig_index = chunk.get("chunk_index", chunk.get("chunk_id", "?"))
            part_chunk["content"] = part_text
            part_chunk["chunk_index"] = f"{orig_index}-{split_depth + 1}{chr(65 + part_idx)}"
            # Keep the original chunk_id for traceability (chunk_refs point to this).

            _logger.info(
                "[REQUIREMENT_ANALYSIS_SPLIT] chunk_ref=%s split_depth=%d "
                "part=%s part_tokens=%d",
                chunk_ref, split_depth + 1,
                part_chunk["chunk_index"], part_tokens,
            )

            if part_tokens > target_tokens:
                result.extend(
                    self._split_chunk_content_recursively(
                        part_chunk,
                        target_tokens=target_tokens,
                        split_depth=split_depth + 1,
                        chunk_ref=chunk_ref,
                    )
                )
            else:
                result.append(part_chunk)

        return result

    def _split_text_at_best_boundary(self, text: str, target_tokens: int) -> list[str]:
        """
        Try to split `text` into two roughly equal pieces at the best available boundary.
        Priority order: paragraph → sentence → newline → whitespace → characters.
        Returns a list of parts, or [text] if text is already small enough.
        """
        if self._count_content_tokens(text) <= target_tokens:
            return [text]

        mid_char = len(text) // 2

        # 1. Paragraph boundary (\n\n)
        part = self._split_near_midpoint(text, mid_char, "\n\n")
        if part:
            return part

        # 2. Sentence boundary (". " or ".\n")
        part = self._split_near_midpoint_regex(text, mid_char, r"(?<=[.!?])\s+")
        if part:
            return part

        # 3. Single newline
        part = self._split_near_midpoint(text, mid_char, "\n")
        if part:
            return part

        # 4. Whitespace
        part = self._split_near_midpoint(text, mid_char, " ")
        if part:
            return part

        # 5. Character fallback — always succeeds
        return [text[:mid_char], text[mid_char:]]

    def _split_near_midpoint(self, text: str, mid_char: int, sep: str) -> list[str] | None:
        """
        Find the occurrence of `sep` closest to mid_char and split there.
        Returns None if sep is not found.
        """
        # Search backwards from mid, then forwards.
        left_idx = text.rfind(sep, 0, mid_char)
        right_idx = text.find(sep, mid_char)

        if left_idx == -1 and right_idx == -1:
            return None

        if left_idx == -1:
            split_at = right_idx
        elif right_idx == -1:
            split_at = left_idx
        else:
            # Pick whichever is closer to mid.
            split_at = left_idx if (mid_char - left_idx) <= (right_idx - mid_char) else right_idx

        left = text[:split_at + len(sep)].strip()
        right = text[split_at + len(sep):].strip()

        if not left or not right:
            return None
        return [left, right]

    def _split_near_midpoint_regex(self, text: str, mid_char: int, pattern: str) -> list[str] | None:
        """Regex-based boundary split closest to mid_char."""
        matches = list(re.finditer(pattern, text))
        if not matches:
            return None

        best = min(matches, key=lambda m: abs(m.start() - mid_char))
        left = text[:best.end()].strip()
        right = text[best.end():].strip()
        if not left or not right:
            return None
        return [left, right]

    def _hard_char_split_chunk(
        self, chunk: dict[str, Any], target_tokens: int, chunk_ref: str
    ) -> list[dict[str, Any]]:
        """
        Guaranteed character-level split of a chunk's content.
        Uses tiktoken-aware max_chars so each piece is provably within target_tokens.
        """
        content = str(chunk.get("content", ""))
        # Conservative: assume 3.5 chars/token (tiktoken GPT-4 average is ~4,
        # but LLaMA tokenizers can be slightly more aggressive, so use 3.5 to be safe).
        max_chars = max(_MIN_CONTENT_CHARS, int(target_tokens * 3.5))

        sub_chunks = []
        for i, start in enumerate(range(0, max(len(content), 1), max_chars)):
            piece = content[start:start + max_chars]
            if not piece.strip():
                continue
            part_chunk = dict(chunk)
            orig_index = chunk.get("chunk_index", chunk.get("chunk_id", "?"))
            part_chunk["content"] = piece
            part_chunk["chunk_index"] = f"{orig_index}-HC{i + 1}"
            _logger.info(
                "[REQUIREMENT_ANALYSIS_SPLIT] chunk_ref=%s hard_char_split part=HC%d "
                "part_tokens=%d",
                chunk_ref, i + 1, self._count_content_tokens(piece),
            )
            sub_chunks.append(part_chunk)

        return sub_chunks if sub_chunks else [chunk]

    def _split_text_recursively(self, text: str, target_tokens: int, depth: int) -> list[str]:
        """Recursive plain-text split (used for str-type chunks)."""
        if self._count_content_tokens(text) <= target_tokens or depth >= _MAX_SPLIT_DEPTH:
            return [text]
        parts = self._split_text_at_best_boundary(text, target_tokens)
        if len(parts) <= 1:
            mid = len(text) // 2
            parts = [text[:mid], text[mid:]]
        result = []
        for part in parts:
            result.extend(self._split_text_recursively(part, target_tokens, depth + 1))
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Batch → LLM → output
    # ─────────────────────────────────────────────────────────────────────────

    async def _analyze_batch(
        self,
        chunks: list[dict[str, Any]] | str,
        *,
        batch_num: int = 1,
        total_batches: int = 1,
        system_prompt: str,
        model_name: str | None,
        max_tokens: int | None,
    ) -> RequirementAnalysisOutput:
        from app.agents.token_budget import count_tokens

        serialized_chunks = self._serialize_chunks(chunks)
        prompt = self.prompt_manager.get_requirement_analysis_prompt(serialized_chunks)

        sys_tokens = count_tokens(system_prompt)
        prompt_tokens = count_tokens(prompt)
        input_tokens = sys_tokens + prompt_tokens
        estimated_out = max_tokens or 1500
        total_est = input_tokens + estimated_out
        chunk_count = 1 if isinstance(chunks, str) else len(chunks)

        _logger.info(
            "\n[REQUIREMENT_ANALYSIS]\n"
            "batch_number=%d/%d\n"
            "chunks_in_batch=%d\n"
            "input_tokens=%d\n"
            "estimated_output_tokens=%d\n"
            "total_estimated_tokens=%d\n"
            "model=%s",
            batch_num, total_batches, chunk_count,
            input_tokens, estimated_out, total_est,
            model_name or os.getenv("MODEL_NAME", "gpt-4o"),
        )

        return await self.llm_service.execute(
            prompt=prompt,
            system_prompt=system_prompt,
            response_schema=self.output_schema,
            max_tokens=max_tokens,
            model_name=model_name,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 413 retry helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _split_batch_by_content(
        self,
        batch: list[dict[str, Any]] | str,
        new_budget: int,
        system_prompt: str,
    ) -> list[list[dict[str, Any]] | str]:
        """
        Split a batch that triggered 413 into smaller pieces.
        If the batch has >1 chunks, split the list.
        If batch has exactly 1 chunk, split that chunk's content recursively.
        """
        if isinstance(batch, str):
            parts = self._split_text_recursively(batch, new_budget, depth=0)
            return parts if parts else [batch]

        if len(batch) > 1:
            mid = len(batch) // 2
            return [batch[:mid], batch[mid:]]

        # Single-chunk batch — must split the content.
        chunk = batch[0]
        chunk_ref = self._get_chunk_ref(chunk)
        sub_chunks = self._split_chunk_content_recursively(
            chunk,
            target_tokens=new_budget,
            split_depth=0,
            chunk_ref=chunk_ref,
        )
        if len(sub_chunks) <= 1:
            # Hard character split as absolute last resort.
            sub_chunks = self._hard_char_split_chunk(chunk, new_budget, chunk_ref)
        return [[sc] for sc in sub_chunks]

    # ─────────────────────────────────────────────────────────────────────────
    # Merging
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def _merge_outputs(
        cls,
        outputs: list[RequirementAnalysisOutput],
    ) -> RequirementAnalysisOutput:
        merged: dict[str, list[Any]] = {}
        for field_name in cls.output_schema.model_fields:
            values = [
                item
                for output in outputs
                for item in getattr(output, field_name)
            ]
            unique_values: list[Any] = []
            seen: set[str] = set()
            for value in values:
                if isinstance(value, ActorRequirementMapping):
                    normalized = "|".join(
                        [
                            " ".join(value.actor.casefold().split()),
                            " ".join(value.requirement.casefold().split()).rstrip("."),
                        ]
                    )
                else:
                    normalized = " ".join(value.casefold().split()).rstrip(".")
                if not normalized:
                    continue
                if normalized in seen:
                    if isinstance(value, ActorRequirementMapping):
                        existing = next(
                            item
                            for item in unique_values
                            if isinstance(item, ActorRequirementMapping)
                            and "|".join([
                                " ".join(item.actor.casefold().split()),
                                " ".join(item.requirement.casefold().split()).rstrip("."),
                            ]) == normalized
                        )
                        existing.chunk_refs = list(dict.fromkeys([
                            *existing.chunk_refs,
                            *value.chunk_refs,
                        ]))
                    continue
                seen.add(normalized)
                unique_values.append(value if isinstance(value, ActorRequirementMapping) else value.strip())
            merged[field_name] = unique_values
        return cls.output_schema(**merged)

    # ─────────────────────────────────────────────────────────────────────────
    # Serialization helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_chunks(chunks: list[dict[str, Any]] | str) -> str:
        if isinstance(chunks, str):
            return chunks
        return json.dumps(chunks, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_chunk_ref(chunk: Any) -> str:
        """Extract a human-readable chunk reference from a chunk dict or batch."""
        if isinstance(chunk, dict):
            return str(
                chunk.get("chunk_id") or chunk.get("id") or
                chunk.get("chunk_index") or "unknown"
            )
        if isinstance(chunk, list) and chunk:
            return RequirementAnalysisAgent._get_chunk_ref(chunk[0])
        return "unknown"

    # ─────────────────────────────────────────────────────────────────────────
    # Explicit actor use-case extraction (unchanged)
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def _extract_explicit_actor_use_cases(
        cls,
        chunks: list[dict[str, Any]] | str,
        *,
        actors: list[str],
    ) -> list[ActorRequirementMapping]:
        """Extract numbered entries under explicit '<Actor> Use Cases' headings."""
        if isinstance(chunks, str):
            sources = [("", chunks)]
        else:
            sources = [
                (
                    str(chunk.get("chunk_id") or chunk.get("id") or ""),
                    str(chunk.get("content") or chunk.get("text") or ""),
                )
                for chunk in chunks
            ]
        text_parts: list[str] = []
        spans: list[tuple[int, int, str]] = []
        cursor = 0
        for chunk_id, content in sources:
            if text_parts:
                text_parts.append(" ")
                cursor += 1
            start = cursor
            text_parts.append(content)
            cursor += len(content)
            spans.append((start, cursor, chunk_id))
        text = "".join(text_parts)

        headings: list[tuple[int, int, str]] = []
        for actor in actors:
            for match in re.finditer(
                rf"\b{re.escape(actor)}\s+Use\s+Cases\b",
                text,
                flags=re.IGNORECASE,
            ):
                headings.append((match.start(), match.end(), actor.strip()))
        headings.sort()

        mappings: list[ActorRequirementMapping] = []
        for index, (_, section_start, actor) in enumerate(headings):
            next_heading = headings[index + 1][0] if index + 1 < len(headings) else len(text)
            requirement_heading = re.search(
                r"\bSystem\s+Req\w*ments\b",
                text[section_start:next_heading],
                flags=re.IGNORECASE,
            )
            section_end = (
                section_start + requirement_heading.start()
                if requirement_heading
                else next_heading
            )
            section = text[section_start:section_end]
            markers = list(re.finditer(r"(?:^|\s)(\d+)\.\s+", section))
            for marker_index, marker in enumerate(markers):
                item_start = section_start + marker.start()
                content_start = marker.end()
                content_end = (
                    markers[marker_index + 1].start()
                    if marker_index + 1 < len(markers)
                    else len(section)
                )
                item_text = section[content_start:content_end].strip()
                requirement = re.split(
                    r"\s+(?:○|Input:|Output:)",
                    item_text,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip(" .")
                if not requirement:
                    continue
                item_end = section_start + content_end
                chunk_refs = [
                    chunk_id
                    for chunk_start, chunk_end, chunk_id in spans
                    if chunk_id and chunk_start < item_end and chunk_end > item_start
                ]
                mappings.append(ActorRequirementMapping(
                    actor=actor,
                    requirement=requirement,
                    chunk_refs=list(dict.fromkeys(chunk_refs)),
                ))
        return mappings

    @classmethod
    def _merge_explicit_use_cases(
        cls,
        output: RequirementAnalysisOutput,
        explicit_use_cases: list[ActorRequirementMapping],
    ) -> RequirementAnalysisOutput:
        if not explicit_use_cases:
            return output
        explicit_actors = {
            item.actor.casefold().strip()
            for item in explicit_use_cases
        }
        output.actor_requirement_mappings = [
            item
            for item in output.actor_requirement_mappings
            if item.actor.casefold().strip() not in explicit_actors
        ]
        return cls._merge_outputs([
            output,
            RequirementAnalysisOutput(
                actor_requirement_mappings=explicit_use_cases,
                functional_requirements=[item.requirement for item in explicit_use_cases],
            ),
        ])

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            first_newline = stripped.find("\n")
            if first_newline != -1:
                stripped = stripped[first_newline + 1:]
            if stripped.endswith("```"):
                stripped = stripped[:-3]
            stripped = stripped.strip()
        return stripped
