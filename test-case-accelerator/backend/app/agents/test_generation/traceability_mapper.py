"""Deterministic Stage 3 artifact mapping for generated test cases."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.test_case import TestCase

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "test",
    "case",
}


class TraceabilityMapper:
    """Attach relevant, structured Stage 3 references without changing TestCase."""

    def __init__(self, confidence_threshold: float = 0.6) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self._confidence_threshold = confidence_threshold

    def map(
        self,
        test_cases: list[TestCase],
        stage3_payload: dict[str, Any],
    ) -> list[TestCase]:
        return [self._map_case(case, stage3_payload) for case in test_cases]

    def _map_case(self, case: TestCase, stage3: dict[str, Any]) -> TestCase:
        case_text = " ".join(
            [case.title, case.description, *case.steps, *case.expected_results]
        )
        tokens = self._tokens(case_text)
        endpoints = self._matches(tokens, stage3.get("api_endpoints", []))
        rules = self._matches(tokens, stage3.get("business_rules", []))
        flows = self._matches(tokens, stage3.get("execution_flows", []))
        targets = self._matches(tokens, stage3.get("test_targets", []))
        analyzed_files = self._matches(tokens, stage3.get("analyzed_files", []))

        trace = dict(case.traceability or {})
        explicit_trace = dict(trace)
        trace["api_routes"] = self._merge_items(
            trace.get("api_routes"),
            [self._endpoint_reference(item) for item in endpoints],
        )
        trace["business_rules"] = self._merge_items(trace.get("business_rules"), rules)
        trace["execution_flows"] = self._merge_items(
            trace.get("execution_flows"), flows
        )

        files = self._string_list(trace.get("source_files"))
        symbols = self._string_list(trace.get("symbols"))
        for item in [*endpoints, *rules, *flows, *targets, *analyzed_files]:
            files.extend(self._files(item))
            symbols.extend(self._symbols(item))
        trace["source_files"] = self._unique(files)
        trace["symbols"] = self._unique(symbols)

        # Singular aliases are assigned only from explicit or confident evidence.
        self._remove_invalid_primary(trace, stage3)
        primary = self._primary_match(case_text, explicit_trace, stage3)
        endpoint_primary = (
            primary
            if primary and primary.get("route")
            else self._primary_match(
                case_text,
                explicit_trace,
                {"api_endpoints": stage3.get("api_endpoints", [])},
            )
        )
        if primary:
            self._set_missing(trace, "file", primary.get("file") or primary.get("path"))
            self._set_missing(
                trace, "symbol", primary.get("symbol") or primary.get("handler")
            )
        if endpoint_primary:
            self._set_missing(trace, "route", endpoint_primary.get("route"))
            self._set_missing(trace, "method", endpoint_primary.get("method"))
            self._set_missing(
                trace, "request_model", endpoint_primary.get("request_type")
            )
            self._set_missing(
                trace, "response_model", endpoint_primary.get("response_type")
            )

        # Remove only null aliases; collection keys are always present.
        trace = {key: value for key, value in trace.items() if value is not None}
        return case.model_copy(update={"traceability": trace})

    def _primary_match(
        self,
        case_text: str,
        trace: dict[str, Any],
        stage3: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Choose a primary reference using explicit evidence before token score."""
        targets = stage3.get("test_targets", [])
        analyzed = stage3.get("analyzed_files", [])
        endpoints = stage3.get("api_endpoints", [])

        # 1. Explicit target symbol.
        for target in targets:
            symbol = target.get("symbol")
            if symbol and (
                self._contains_exact(case_text, symbol)
                or trace.get("symbol") == symbol
                or symbol in self._string_list(trace.get("symbols"))
            ):
                return target

        # 2. Function signature.
        for target in targets:
            signature = target.get("signature")
            if signature and (
                signature.casefold() in case_text.casefold()
                or self._confidence(case_text, signature)
                > self._confidence_threshold
            ):
                return target

        # 3. Analyzed file reference.
        for item in analyzed:
            path = item.get("path")
            if path and (
                self._contains_exact(case_text, path)
                or trace.get("file") == path
                or path in self._string_list(trace.get("source_files"))
            ):
                return item

        # 4. API endpoint route or handler.
        for endpoint in endpoints:
            route = endpoint.get("route")
            handler = endpoint.get("handler")
            if (
                route and route.casefold() in case_text.casefold()
            ) or (
                handler and self._contains_exact(case_text, handler)
            ):
                return endpoint

        # 5. Highest-confidence token match, retaining source-order precedence.
        candidates = [*targets, *analyzed, *endpoints]
        scored = [
            (self._confidence(case_text, self._flatten(item)), index, item)
            for index, item in enumerate(candidates)
        ]
        if not scored:
            return None
        confidence, _, candidate = max(
            scored, key=lambda item: (item[0], -item[1])
        )
        return (
            candidate
            if confidence > self._confidence_threshold
            else None
        )

    @classmethod
    def _confidence(cls, case_text: str, candidate_text: str) -> float:
        case_tokens = cls._tokens(case_text)
        candidate_tokens = cls._tokens(candidate_text)
        if not case_tokens or not candidate_tokens:
            return 0.0
        return len(case_tokens & candidate_tokens) / len(candidate_tokens)

    @staticmethod
    def _contains_exact(text: str, value: str) -> bool:
        return re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(value)}(?![A-Za-z0-9_])",
            text,
            re.IGNORECASE,
        ) is not None

    @classmethod
    def _remove_invalid_primary(
        cls, trace: dict[str, Any], stage3: dict[str, Any]
    ) -> None:
        candidates = [
            *stage3.get("test_targets", []),
            *stage3.get("analyzed_files", []),
            *stage3.get("api_endpoints", []),
        ]
        valid = {
            "file": {
                file_name
                for item in candidates
                for file_name in cls._files(item)
            },
            "symbol": {
                symbol
                for item in candidates
                for symbol in cls._symbols(item)
            },
            "route": {
                item.get("route")
                for item in stage3.get("api_endpoints", [])
                if item.get("route")
            },
        }
        for key, allowed in valid.items():
            if allowed and trace.get(key) not in allowed:
                trace.pop(key, None)

    def _matches(
        self, tokens: set[str], candidates: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        scored = [
            (len(tokens & self._tokens(self._flatten(candidate))), index, candidate)
            for index, candidate in enumerate(candidates)
        ]
        return [
            candidate
            for score, _, candidate in sorted(
                scored, key=lambda item: (-item[0], item[1])
            )
            if score > 0
        ][:3]

    @staticmethod
    def _flatten(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(
                TraceabilityMapper._flatten(item) for item in value.values()
            )
        if isinstance(value, list):
            return " ".join(TraceabilityMapper._flatten(item) for item in value)
        return str(value or "")

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token.casefold()
            for token in TOKEN_PATTERN.findall(value.replace("_", " "))
            if token.casefold() not in STOP_WORDS and len(token) > 1
        }

    @staticmethod
    def _endpoint_reference(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: item.get(key)
            for key in (
                "method",
                "route",
                "handler",
                "file",
                "request_type",
                "response_type",
            )
            if item.get(key) is not None
        }

    @staticmethod
    def _files(item: dict[str, Any]) -> list[str]:
        files = item.get("files", [])
        if isinstance(files, str):
            files = [files]
        file_name = item.get("file") or item.get("path")
        return [*files, *([file_name] if isinstance(file_name, str) else [])]

    @staticmethod
    def _symbols(item: dict[str, Any]) -> list[str]:
        symbols = item.get("symbols", [])
        if isinstance(symbols, str):
            symbols = [symbols]
        for key in ("symbol", "handler"):
            if isinstance(item.get(key), str):
                symbols = [*symbols, item[key]]
        return symbols

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        return [item for item in (value or []) if isinstance(item, str)]

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))

    @staticmethod
    def _set_missing(trace: dict[str, Any], key: str, value: Any) -> None:
        if not trace.get(key) and value is not None:
            trace[key] = value

    @staticmethod
    def _merge_items(
        existing: Any, added: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        items = [item for item in (existing or []) if isinstance(item, dict)]
        for item in added:
            if item not in items:
                items.append(item)
        return items
