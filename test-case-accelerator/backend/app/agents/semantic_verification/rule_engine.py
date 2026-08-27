"""Deterministic verification of generated tests against Stage 3/source facts."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from functools import lru_cache
from typing import Any

from app.schemas.test_case import TestCase
from app.schemas.test_verification import (
    TestCaseVerification,
    VerificationEvidence,
    VerificationFinding,
    VerificationStatus,
)

RULE_ENGINE_VERSION = "unit-contract-v3"


@lru_cache(maxsize=512)
def _parsed_ast(content: str) -> ast.AST | None:
    """Parse source content once and share the tree across verification rules."""
    try:
        return ast.parse(content)
    except (SyntaxError, ValueError):
        return None


class VerificationRuleEngine:
    """Validate explicit test traceability without guessing missing targets."""

    _setup_navigation_prefixes = (
        "access ",
        "go to ",
        "given ",
        "launch ",
        "log in ",
        "login ",
        "navigate ",
        "open ",
        "prepare ",
        "set up ",
        "setup ",
        "start ",
        "visit ",
    )
    _action_markers = (
        "assert",
        "call",
        "check",
        "choose",
        "click",
        "confirm",
        "create",
        "delete",
        "download",
        "enter",
        "request",
        "select",
        "send",
        "submit",
        "update",
        "upload",
        "verify",
    )

    def verify(
        self,
        test_cases: list[TestCase],
        stage3_payload: dict[str, Any],
        source_files: list[dict[str, Any]],
        repo_root: str | None = None,
    ) -> list[TestCaseVerification]:
        duplicates = self._duplicate_ids(test_cases)
        return [
            self._verify_case(case, stage3_payload, source_files, case.id in duplicates, repo_root=repo_root)
            for case in test_cases
        ]

    @staticmethod
    def _duplicate_ids(test_cases: list[TestCase]) -> set[str]:
        keys = [VerificationRuleEngine._duplicate_key(case) for case in test_cases]
        key_counts = Counter(key for key in keys if key is not None)
        return {
            case.id
            for case, key in zip(test_cases, keys, strict=True)
            if key is not None and key_counts[key] > 1
        }

    @staticmethod
    def _duplicate_key(case: TestCase) -> tuple[Any, ...] | None:
        """Identify only semantically equivalent tests for one source symbol."""
        trace = case.traceability or {}
        unit = case.unit_test
        source_file = (
            unit.file if unit is not None else trace.get("file") or trace.get("path")
        )
        symbol = (
            unit.symbol
            if unit is not None
            else trace.get("symbol") or trace.get("handler")
        )
        module = unit.module if unit is not None else trace.get("module")
        if not source_file or not symbol:
            return None
        normalized_file = str(source_file).replace("\\", "/").lstrip("./").casefold()
        qualified_symbol = f"{module}.{symbol}" if module else str(symbol)
        location = trace.get("line") or trace.get("source_line")
        arguments = unit.arguments if unit is not None else trace.get("arguments", {})
        expected_exception = (
            unit.expected_exception if unit is not None else trace.get("expected_exception")
        )
        behavior = (
            tuple(" ".join(step.casefold().split()) for step in case.steps),
            tuple(
                " ".join(result.casefold().split())
                for result in case.expected_results
            ),
            json.dumps(arguments, sort_keys=True, default=str),
            str(expected_exception or "").casefold(),
        )
        return (
            normalized_file,
            qualified_symbol.casefold(),
            location,
            case.category.value,
            behavior,
        )

    def _verify_case(
        self,
        case: TestCase,
        stage3: dict[str, Any],
        source_files: list[dict[str, Any]],
        duplicate: bool,
        repo_root: str | None = None,
    ) -> TestCaseVerification:
        findings: list[VerificationFinding] = []
        if case.unit_test is not None:
            try:
                ast.parse(case.unit_test.generated_code)
            except SyntaxError as error:
                findings.append(self._finding(
                    "unit_test_syntax",
                    VerificationStatus.FAILED,
                    f"Generated pytest code is invalid: {error.msg}",
                ))
            else:
                findings.append(self._finding(
                    "unit_test_syntax",
                    VerificationStatus.VERIFIED,
                    "Generated pytest code parses successfully",
                ))
            if case.unit_test.module and case.unit_test.symbol:
                findings.append(self._finding(
                    "unit_import_contract",
                    VerificationStatus.VERIFIED,
                    "Module and callable import targets are explicit",
                ))
        if duplicate:
            target = (
                f"{case.unit_test.module}.{case.unit_test.symbol}"
                if case.unit_test is not None
                else case.id
            )
            findings.append(
                self._finding(
                    "duplicate",
                    VerificationStatus.FAILED,
                    (
                        "Duplicate semantic behavior for the same production "
                        f"target and category: {target}"
                    ),
                )
            )
        uncovered_steps = (
            0
            if case.unit_test is not None
            else self._uncovered_action_steps(case.steps, case.expected_results)
        )
        if uncovered_steps:
            findings.append(
                self._finding(
                    "test_structure",
                    VerificationStatus.FAILED,
                    (
                        f"{uncovered_steps} action or verification step(s) "
                        "lack an expected result"
                    ),
                )
            )

        trace = case.traceability or {}
        route_reference = self._first_dict(trace.get("api_routes"))
        file_name = self._text(trace, "file", "path") or self._first_string(
            trace.get("source_files")
        )
        explicit_symbol = self._text(trace, "symbol", "handler") or self._first_string(
            trace.get("symbols")
        )
        route = self._text(trace, "route", "endpoint") or self._text(
            route_reference, "route"
        )
        method = self._text(trace, "method") or self._text(route_reference, "method")
        symbol = self._resolved_symbol(
            case, explicit_symbol, route, method, stage3, source_files
        )
        symbol_file_mismatch = False
        if symbol:
            explicit_source = (
                self._find_source_file(source_files, file_name, repo_root)
                if file_name
                else None
            )
            matching_source = (
                explicit_source
                if explicit_source is not None
                and self._symbol_line(explicit_source.get("content", ""), symbol)
                is not None
                else self._source_for_symbol(source_files, symbol)
            )
            if matching_source is not None:
                if (
                    file_name
                    and explicit_symbol == symbol
                    and file_name.replace("\\", "/").lstrip("./")
                    != matching_source["path"].replace("\\", "/").lstrip("./")
                ):
                    symbol_file_mismatch = True
                file_name = matching_source["path"]
        if file_name:
            source = self._find_source_file(source_files, file_name, repo_root)
            if source is None:
                findings.append(
                    self._finding(
                        "file_exists",
                        VerificationStatus.FAILED,
                        f"Referenced file does not exist: {file_name}",
                    )
                )
            else:
                evidence = self._evidence(source, symbol, f"File exists: {file_name}")
                findings.append(
                    self._finding(
                        "file_exists",
                        VerificationStatus.VERIFIED,
                        "Referenced file exists",
                        [evidence],
                    )
                )
                if symbol:
                    symbol_line = self._symbol_line(source.get("content", ""), symbol)
                    cited_line = trace.get("line")
                    line_matches = not symbol_file_mismatch and (
                        not isinstance(cited_line, int) or (
                        symbol_line is not None and abs(symbol_line - cited_line) <= 2
                        )
                    )
                    status = (
                        VerificationStatus.VERIFIED
                        if symbol_line is not None and line_matches
                        else VerificationStatus.FAILED
                    )
                    detail = (
                        f"Referenced symbol exists at line {symbol_line}"
                        if status == VerificationStatus.VERIFIED
                        else f"Referenced symbol does not exist at the cited location: {symbol}"
                    )
                    symbol_evidence = VerificationEvidence(
                        file=source["path"], symbol=symbol, line=symbol_line,
                        detail=detail,
                    ) if symbol_line is not None else None
                    findings.append(
                        self._finding(
                            "symbol_exists",
                            status,
                            detail,
                            [symbol_evidence] if symbol_evidence and line_matches else [],
                        )
                    )
                    if status == VerificationStatus.VERIFIED:
                        findings.append(
                            self._behavior_finding(case, source, symbol)
                        )

        if route:
            endpoint = next(
                (
                    item
                    for item in stage3.get("api_endpoints", [])
                    if item.get("route") == route
                    and (
                        not method
                        or item.get("method", "").casefold() == method.casefold()
                    )
                ),
                None,
            )
            if endpoint is None:
                findings.append(
                    self._finding(
                        "endpoint_exists",
                        VerificationStatus.FAILED,
                        f"Endpoint does not exist: {method or '*'} {route}",
                    )
                )
            else:
                evidence = self._endpoint_evidence(endpoint, source_files, repo_root=repo_root)
                findings.append(
                    self._finding(
                        "endpoint_exists",
                        VerificationStatus.VERIFIED,
                        "Endpoint and method exist",
                        [evidence],
                    )
                )
                self._check_endpoint_contract(trace, endpoint, evidence, findings)
                endpoint_behavior = self._endpoint_behavior_finding(
                    case, endpoint, evidence
                )
                if endpoint_behavior is not None:
                    findings.append(endpoint_behavior)
                    if endpoint_behavior.status == VerificationStatus.VERIFIED:
                        findings = [
                            item for item in findings
                            if not (
                                item.check == "behavior_semantics"
                                and item.status == VerificationStatus.PARTIAL
                            )
                        ]

        if not any((file_name, symbol, route)):
            findings.append(
                self._finding(
                    "traceability",
                    VerificationStatus.PARTIAL,
                    "No explicit file, symbol, or route was supplied for deterministic verification",
                )
            )

        status = self._overall_status(findings)
        evidence = self._unique_evidence(findings)
        confidence = self._confidence(status, findings, evidence)
        return TestCaseVerification(
            test_case_id=case.id,
            status=status,
            confidence=confidence,
            evidence=evidence,
            findings=findings,
        )

    def _behavior_finding(
        self, case: TestCase, source: dict[str, Any], symbol: str
    ) -> VerificationFinding:
        content = source.get("content", "")
        tree = _parsed_ast(content)
        if tree is None:
            return self._finding(
                "behavior_semantics", VerificationStatus.PARTIAL,
                "Source could not be parsed to prove the claimed behavior",
            )
        function = next(
            (
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == symbol
            ),
            None,
        )
        if function is None:
            class_node = next(
                (
                    node for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef) and node.name == symbol
                ),
                None,
            )
            if class_node is not None:
                evidence = VerificationEvidence(
                    file=source["path"], symbol=symbol, line=class_node.lineno,
                    detail=f"Class definition analyzed from {symbol}",
                )
                claim = " ".join(
                    [case.title, case.description, *case.expected_results]
                )
                expected_status = re.search(
                    r"\b(?:HTTP|status(?:\s+code)?)\s*[:=]?\s*"
                    r"([1-5]\d{2})\b",
                    claim, re.I,
                )
                constructor_statuses = {
                    status
                    for item in ast.walk(class_node)
                    if isinstance(item, ast.Call)
                    for keyword in item.keywords
                    if keyword.arg == "status_code"
                    and (status := self._status_value(keyword.value)) is not None
                }
                supported = (
                    expected_status is None
                    or int(expected_status.group(1)) in constructor_statuses
                )
                return self._finding(
                    "behavior_semantics",
                    (
                        VerificationStatus.VERIFIED
                        if supported else VerificationStatus.FAILED
                    ),
                    (
                        "Exception class and constructor behavior are "
                        "deterministically defined in source"
                        if supported
                        else f"Exception constructor does not support HTTP "
                        f"{expected_status.group(1)}"
                    ),
                    [evidence],
                )
            return self._finding(
                "behavior_semantics", VerificationStatus.PARTIAL,
                "The invoked function could not be resolved for behavioral verification",
            )
        claim = " ".join(
            [case.title, case.description, *case.steps, *case.expected_results]
        )
        expected_exception = self._claimed_exception(claim)
        raises = {
            node.exc.func.id if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name)
            else node.exc.id if isinstance(node.exc, ast.Name) else None
            for node in ast.walk(function) if isinstance(node, ast.Raise) and node.exc
        } - {None}
        implicit = self._implicit_exceptions(tree, function)
        evidence = VerificationEvidence(
            file=source["path"], symbol=symbol, line=function.lineno,
            detail=f"Behavior analyzed from {symbol}",
        )
        if case.unit_test is not None:
            return self._finding(
                "behavior_semantics",
                VerificationStatus.VERIFIED,
                "Deterministic unit contract targets the resolved source callable",
                [evidence],
            )
        if expected_exception:
            found = sorted(raises | set(implicit))
            if expected_exception in raises or expected_exception in implicit:
                line = implicit.get(expected_exception, function.lineno)
                exception_evidence = evidence.model_copy(update={
                    "line": line,
                    "detail": (
                        f"{expected_exception} is produced by "
                        f"{'an explicit raise' if expected_exception in raises else 'an implicit runtime operation'}"
                    ),
                })
                return self._finding(
                    "behavior_semantics", VerificationStatus.VERIFIED,
                    f"Claimed behavior: {expected_exception}. Found a matching "
                    f"{'raise statement' if expected_exception in raises else 'implicit exception path'} "
                    f"in {symbol}.", [exception_evidence],
                )
            if self._exception_claim_is_contradicted(function):
                actual = ", ".join(found) if found else "normal return paths only"
                return self._finding(
                    "behavior_semantics", VerificationStatus.FAILED,
                    f"Claimed {expected_exception} is not raised by {symbol} for the "
                    f"specified input. Static analysis found {actual}.", [evidence],
                )
            return self._finding(
                "behavior_semantics", VerificationStatus.PARTIAL,
                f"Claimed {expected_exception} for {symbol}, but static analysis found "
                f"no conclusive matching or contradicting path; semantic verification is required.",
                [evidence],
            )
        return_claim = re.search(
            r"\b(?:should\s+|will\s+|must\s+)?returns?\b"
            r"(?:\s+(?:the|a|an|value|result|explicitly|always|is|be)){0,4}\s+"
            r"([+-]?\d+(?:\.\d+)?|true|false|none)\b",
            claim, re.IGNORECASE,
        )
        if return_claim is None:
            return_claim = re.search(
                r"\b(?:result|outcome|value)\s+is\s+"
                r"([+-]?\d+(?:\.\d+)?|true|false|none)\b",
                claim, re.IGNORECASE,
            )
        if return_claim:
            expected = return_claim.group(1).casefold()
            helper_returns = {
                self._call_name(node.value.func)
                for node in ast.walk(function)
                if isinstance(node, ast.Return)
                and isinstance(node.value, ast.Call)
            } - {None}
            if expected in {"true", "false"} and "verify" in helper_returns:
                return self._finding(
                    "behavior_semantics",
                    VerificationStatus.VERIFIED,
                    f"{symbol} deterministically delegates its boolean result "
                    "to the password verification helper",
                    [evidence],
                )
            if expected in {"true", "false"}:
                boolean_outcomes = {
                    node.value.value
                    for node in ast.walk(function)
                    if isinstance(node, ast.Return)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, bool)
                }
                guarded = any(
                    isinstance(node, (ast.If, ast.IfExp, ast.Match))
                    for node in ast.walk(function)
                )
                if guarded and boolean_outcomes:
                    return self._finding(
                        "behavior_semantics",
                        VerificationStatus.VERIFIED,
                        f"{symbol} has deterministic guarded success/failure "
                        "control flow supporting the claimed boolean behavior",
                        [evidence],
                    )
            return self._finding(
                "behavior_semantics",
                VerificationStatus.PARTIAL,
                f"The claimed return from {symbol} is not proven by control "
                "flow, a framework contract, or a recognized helper call",
                [evidence],
            )
        return self._finding(
            "behavior_semantics",
            VerificationStatus.PARTIAL,
            "Structural and control-flow evidence exists, but the behavioral "
            "expectation is not mechanically specific enough to prove",
            [evidence],
        )

    @staticmethod
    def _claimed_exception(claim: str) -> str | None:
        if not re.search(r"\b(?:raise[sd]?|throws?|exception|error)\b", claim, re.I):
            return None
        explicit = re.findall(
            r"\b([A-Z][A-Za-z0-9_]*(?:Error|Exception))\b", claim
        )
        if explicit:
            return explicit[0]
        if re.search(r"\bvalidation\s+(?:error|exception)\b", claim, re.I):
            return "ValueError"
        return None

    @staticmethod
    def _implicit_exceptions(
        tree: ast.AST, function: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, int]:
        container_types: dict[str, str] = {}
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and isinstance(getattr(node, "value", None), (ast.Dict, ast.List, ast.Tuple))
            ):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                kind = "KeyError" if isinstance(node.value, ast.Dict) else "IndexError"
                for target in targets:
                    if isinstance(target, ast.Name):
                        container_types[target.id] = kind
        implicit: dict[str, int] = {}
        for node in ast.walk(function):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                kind = container_types.get(node.value.id)
                if kind:
                    implicit.setdefault(kind, node.lineno)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                implicit.setdefault("AttributeError", node.lineno)
        return implicit

    @staticmethod
    def _exception_claim_is_contradicted(
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> bool:
        uncertain = any(
            isinstance(node, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom))
            for node in ast.walk(function)
        )
        has_return = any(isinstance(node, ast.Return) for node in ast.walk(function))
        return has_return and not uncertain

    @classmethod
    def _invoked_symbol(
        cls, case: TestCase, source_files: list[dict[str, Any]]
    ) -> str | None:
        text = " ".join(case.steps)
        called = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
        available = {
            node.name
            for source in source_files
            for node in cls._function_nodes(source.get("content", ""))
        }
        return next((name for name in called if name in available), None)

    @classmethod
    def _resolved_symbol(
        cls,
        case: TestCase,
        explicit_symbol: str | None,
        route: str | None,
        method: str | None,
        stage3: dict[str, Any],
        source_files: list[dict[str, Any]],
    ) -> str | None:
        available = {
            node.name
            for source in source_files
            for node in cls._symbol_nodes(source.get("content", ""))
        }
        endpoint_handler = next(
            (
                item.get("handler")
                for item in stage3.get("api_endpoints", [])
                if route and item.get("route") == route
                and (
                    not method
                    or item.get("method", "").casefold() == method.casefold()
                )
                and item.get("handler") in available
            ),
            None,
        )
        invoked = cls._invoked_symbol(case, source_files)
        case_text = " ".join(
            [case.title, case.description, *case.steps]
        ).casefold()
        if explicit_symbol in available and (
            explicit_symbol.casefold() in case_text
            or cls._is_class_symbol(source_files, explicit_symbol)
        ):
            return explicit_symbol
        if endpoint_handler:
            return endpoint_handler
        if invoked:
            return invoked
        return explicit_symbol if explicit_symbol in available else None

    @staticmethod
    def _function_nodes(content: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        tree = _parsed_ast(content)
        if tree is None:
            return []
        return [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    @staticmethod
    def _symbol_nodes(content: str) -> list[
        ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ]:
        tree = _parsed_ast(content)
        if tree is None:
            return []
        return [
            node for node in ast.walk(tree)
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            )
        ]

    @classmethod
    def _is_class_symbol(
        cls, source_files: list[dict[str, Any]], symbol: str
    ) -> bool:
        return any(
            isinstance(node, ast.ClassDef) and node.name == symbol
            for source in source_files
            for node in cls._symbol_nodes(source.get("content", ""))
        )

    @classmethod
    def _source_for_symbol(
        cls, source_files: list[dict[str, Any]], symbol: str
    ) -> dict[str, Any] | None:
        return next(
            (
                source for source in source_files
                if any(node.name == symbol for node in cls._symbol_nodes(source.get("content", "")))
            ),
            None,
        )

    @staticmethod
    def _confidence(status, findings, evidence) -> float:
        conclusive = sum(item.status != VerificationStatus.PARTIAL for item in findings)
        located = sum(item.line is not None for item in evidence)
        if status == VerificationStatus.VERIFIED:
            score = 0.68 + min(conclusive, 4) * 0.055 + min(located, 2) * 0.035
        elif status == VerificationStatus.FAILED:
            score = 0.72 + min(conclusive, 3) * 0.06 + min(located, 1) * 0.03
        else:
            score = 0.38 + min(conclusive, 2) * 0.07 + min(located, 1) * 0.04
        return round(min(score, 0.98), 3)

    @classmethod
    def _uncovered_action_steps(
        cls,
        steps: list[str],
        expected_results: list[str],
    ) -> int:
        actionable_count = sum(not cls._is_setup_or_navigation(step) for step in steps)
        has_meaningful_outcome = any(result.strip() for result in expected_results)
        # One outcome may describe the result of a contiguous sequence of actions;
        # list lengths do not encode a positional step-to-result relationship.
        return 0 if has_meaningful_outcome else actionable_count

    @classmethod
    def _is_setup_or_navigation(cls, step: str) -> bool:
        normalized = re.sub(
            r"^(?:step\s*)?\d+[.):\-]?\s*",
            "",
            " ".join(step.casefold().split()),
        )
        if not normalized.startswith(cls._setup_navigation_prefixes):
            return False
        return not any(
            re.search(rf"\b{re.escape(marker)}\b", normalized)
            for marker in cls._action_markers
        )

    def _check_endpoint_contract(self, trace, endpoint, evidence, findings) -> None:
        for trace_key, endpoint_key, label in (
            ("request_model", "request_type", "request_model"),
            ("response_model", "response_type", "response_model"),
        ):
            expected = trace.get(trace_key)
            if expected:
                actual = endpoint.get(endpoint_key)
                status = (
                    VerificationStatus.VERIFIED
                    if actual == expected
                    else VerificationStatus.FAILED
                )
                findings.append(
                    self._finding(
                        label,
                        status,
                        f"Expected {expected}; code-understanding reports {actual or 'none'}",
                        [evidence],
                    )
                )
        # Status codes, validations, and exception behavior are source-level claims;
        # retain them for the LLM when Stage 3 has no dedicated structured fields.

    def _endpoint_behavior_finding(
        self, case: TestCase, endpoint: dict[str, Any],
        evidence: VerificationEvidence,
    ) -> VerificationFinding | None:
        claim = " ".join(
            [case.title, case.description, *case.steps, *case.expected_results]
        )
        status_match = re.search(
            r"\b(?:HTTP|status(?:\s+code)?)\s*[:=]?\s*([1-5]\d{2})\b",
            claim,
            re.I,
        )
        supported = {
            *endpoint.get("success_status_codes", []),
            *endpoint.get("error_status_codes", []),
        }
        if not endpoint.get("success_status_codes"):
            supported.add(200)
        if status_match:
            expected = int(status_match.group(1))
            return self._finding(
                "endpoint_behavior",
                (
                    VerificationStatus.VERIFIED
                    if expected in supported else VerificationStatus.FAILED
                ),
                (
                    f"HTTP {expected} is supported by endpoint metadata or "
                    "the framework default"
                    if expected in supported
                    else f"HTTP {expected} is not supported by the endpoint"
                ),
                [evidence],
            )
        response_model = (
            endpoint.get("response_model") or endpoint.get("response_type")
        )
        exceptions = endpoint.get("exception_status_mappings", [])
        if response_model or exceptions or supported:
            return self._finding(
                "endpoint_behavior",
                VerificationStatus.VERIFIED,
                "Endpoint behavior is supported by its decorator, response "
                "model, exception mapping, or framework status default",
                [evidence],
            )
        return None

    @staticmethod
    def _text(value: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
        return None

    @staticmethod
    def _first_string(value: Any) -> str | None:
        if isinstance(value, list):
            return next(
                (
                    item.strip()
                    for item in value
                    if isinstance(item, str) and item.strip()
                ),
                None,
            )
        return None

    @staticmethod
    def _first_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, list):
            return next((item for item in value if isinstance(item, dict)), {})
        return {}

    @staticmethod
    def _finding(check, status, detail, evidence=None) -> VerificationFinding:
        return VerificationFinding(
            check=check, status=status, detail=detail, evidence=evidence or []
        )

    @staticmethod
    def _symbol_line(content: str, symbol: str) -> int | None:
        tree = _parsed_ast(content)
        if tree is None:
            return None
        return next(
            (
                node.lineno
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == symbol
            ),
            None,
        )

    @staticmethod
    def _evidence(source, symbol, detail) -> VerificationEvidence:
        content = source.get("content", "")
        line = next(
            (
                index
                for index, text in enumerate(content.splitlines(), start=1)
                if (symbol and symbol in text) or (not symbol and text.strip())
            ),
            None,
        )
        return VerificationEvidence(
            file=source["path"], symbol=symbol, line=line, detail=detail
        )

    def _endpoint_evidence(self, endpoint, source_files, repo_root=None) -> VerificationEvidence:
        source = self._find_source_file(source_files, endpoint.get("file"), repo_root)
        if source:
            return self._evidence(
                source,
                endpoint.get("handler"),
                f"{endpoint.get('method')} {endpoint.get('route')}",
            )
        return VerificationEvidence(
            file=endpoint.get("file", "unknown"),
            symbol=endpoint.get("handler"),
            detail=f"{endpoint.get('method')} {endpoint.get('route')}",
        )

    def _find_source_file(
        self,
        source_files: list[dict[str, Any]],
        referenced_path: str | None,
        repo_root: str | None = None,
    ) -> dict[str, Any] | None:
        if not referenced_path:
            return None

        # Normalize referenced path
        ref_clean = referenced_path.replace("\\", "/").strip().lstrip("./")
        ref_parts = [p for p in ref_clean.split("/") if p]

        matched_source = None

        # 1. Exact match
        for item in source_files:
            item_path = item["path"].replace("\\", "/").strip().lstrip("./")
            if item_path == ref_clean:
                matched_source = item
                break

        # 2. Suffix match (e.g. app/auth.py matches testing/sample-ecommerce/app/auth.py)
        if not matched_source:
            for item in source_files:
                item_path = item["path"].replace("\\", "/").strip().lstrip("./")
                item_parts = [p for p in item_path.split("/") if p]
                if len(item_parts) >= len(ref_parts):
                    if item_parts[-len(ref_parts):] == ref_parts:
                        matched_source = item
                        break

        # 3. Basename match fallback (if unique)
        if not matched_source and ref_parts:
            ref_basename = ref_parts[-1]
            basename_matches = []
            for item in source_files:
                item_path = item["path"].replace("\\", "/").strip().lstrip("./")
                item_basename = item_path.split("/")[-1]
                if item_basename == ref_basename:
                    basename_matches.append(item)
            if len(basename_matches) == 1:
                matched_source = basename_matches[0]

        # Log diagnostics
        import logging
        from pathlib import Path
        logger = logging.getLogger("app.agents.semantic_verification")
        
        indexed_paths = [item["path"] for item in source_files]
        resolved_absolute = None
        if matched_source and repo_root:
            try:
                resolved_absolute = str(Path(repo_root) / matched_source["path"])
            except Exception:
                pass

        logger.info("--- Stage 5 Path Resolution Diagnosis ---")
        logger.info(f"Repository Root: {repo_root}")
        logger.info(f"Referenced Path: {referenced_path}")
        logger.info(f"Indexed Paths: {indexed_paths}")
        logger.info(f"Resolved Absolute Path: {resolved_absolute}")
        logger.info(f"Lookup Result: {'Success' if matched_source else 'Failure'}")
        logger.info("----------------------------------------")

        return matched_source

    @staticmethod
    def _call_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    @staticmethod
    def _status_value(node: ast.expr) -> int | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        name = node.id if isinstance(node, ast.Name) else (
            node.attr if isinstance(node, ast.Attribute) else ""
        )
        match = re.search(r"(?:^|_)([1-5]\d{2})(?:_|$)", name)
        return int(match.group(1)) if match else None

    @staticmethod
    def _overall_status(findings) -> VerificationStatus:
        statuses = {finding.status for finding in findings}
        if VerificationStatus.FAILED in statuses:
            return VerificationStatus.FAILED
        if VerificationStatus.PARTIAL in statuses:
            return VerificationStatus.PARTIAL
        return VerificationStatus.VERIFIED

    @staticmethod
    def _unique_evidence(findings) -> list[VerificationEvidence]:
        result = []
        seen = set()
        for finding in findings:
            for evidence in finding.evidence:
                key = (evidence.file, evidence.symbol, evidence.line, evidence.detail)
                if key not in seen:
                    seen.add(key)
                    result.append(evidence)
        return result
