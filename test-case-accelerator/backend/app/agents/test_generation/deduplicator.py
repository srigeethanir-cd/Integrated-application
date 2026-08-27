import logging
import re
from typing import List, Tuple

from ...schemas.test_case import TestCase

logger = logging.getLogger(__name__)


class Deduplicator:
    """Remove duplicate test cases.

    Duplicates are identified by matching any of the following fields:
    - ``id``
    - ``title``
    - ``steps`` (exact sequence)
    The first occurrence is kept.
    """

    def deduplicate(self, test_cases: List[TestCase]) -> List[TestCase]:
        seen_ids: set[str] = set()
        seen_titles: set[str] = set()
        seen_steps: set[Tuple[str, ...]] = set()
        seen_behaviors: set[tuple[str, str, str, str]] = set()
        seen_scenarios: set[tuple[str, str, str]] = set()
        unique_cases: List[TestCase] = []
        for case in test_cases:
            dup_id = case.id in seen_ids
            normalized_title = " ".join(case.title.casefold().split())
            normalized_steps = tuple(" ".join(step.casefold().split()) for step in case.steps)
            dup_title = normalized_title in seen_titles
            dup_steps = normalized_steps in seen_steps
            behavior_key = self._behavior_key(case)
            scenario_key = self._scenario_key(case)
            dup_behavior = bool(behavior_key[0]) and behavior_key in seen_behaviors
            dup_scenario = bool(scenario_key[0]) and scenario_key in seen_scenarios
            if dup_id or (dup_title and dup_steps) or dup_behavior or dup_scenario:
                logger.debug("Deduplicator removed duplicate test case %s", case.id)
                continue
            seen_ids.add(case.id)
            seen_titles.add(normalized_title)
            seen_steps.add(normalized_steps)
            seen_behaviors.add(behavior_key)
            seen_scenarios.add(scenario_key)
            unique_cases.append(case)
        return unique_cases

    @staticmethod
    def _behavior_key(case: TestCase) -> tuple[str, str, str, str]:
        identity, polarity, branch = Deduplicator._scenario_key(case)
        expected = Deduplicator._canonical_expected(
            " ".join(case.expected_results)
        )
        return identity, polarity, branch, expected

    @staticmethod
    def _scenario_key(case: TestCase) -> tuple[str, str, str]:
        trace = case.traceability or {}
        symbols = trace.get("symbols", [])
        symbol = trace.get("symbol") or (
            symbols[0] if isinstance(symbols, list) and symbols else ""
        )
        route = trace.get("route") or trace.get("endpoint") or ""
        method = str(trace.get("method") or "").upper()
        identity = (
            f"{method} {route}".strip()
            if route else str(symbol)
        )
        requirements = trace.get("coverage_requirements", [])
        text = " ".join([case.title, case.description, *case.steps])
        branch = Deduplicator._canonical_branch(text)
        if not branch and requirements:
            branch = "|".join(
                sorted(str(item).split("|", 2)[-1] for item in requirements)
            )
        if not branch:
            branch = re.sub(r"[\w.+-]+@[\w.-]+", "<email>", text.casefold())
            branch = re.sub(r"['\"][^'\"]*['\"]", "<value>", branch)
            branch = re.sub(
                r"\b(?:test|verify|check|ensure|call|invoke|endpoint|request|"
                r"response|should|must|using|with|when|given|then)\b",
                " ",
                branch,
            )
            branch = " ".join(branch.split())
        polarity = Deduplicator._polarity(case)
        return identity, polarity, branch

    @staticmethod
    def _polarity(case: TestCase) -> str:
        value = case.category.value.casefold()
        if value in {"negative", "security", "exception/integration"}:
            return "negative"
        text = " ".join(
            [case.title, case.description, *case.steps]
        ).casefold()
        return (
            "negative"
            if re.search(
                r"\b(?:reject|fail|invalid|missing|unknown|unauthori[sz]ed|"
                r"forbidden|exception|error|false)\b",
                text,
            )
            else "positive"
        )

    @staticmethod
    def _canonical_branch(text: str) -> str:
        value = text.casefold().replace("recipient", "receiver")
        patterns = (
            ("negative_balance", ("negative balance", "balance below zero", "balance < 0")),
            ("missing_receiver", ("missing receiver", "receiver does not exist", "unknown receiver", "nonexistent receiver")),
            ("missing_sender", ("missing sender", "sender does not exist", "unknown sender", "nonexistent sender")),
            ("insufficient_funds", ("insufficient funds", "not enough funds", "balance too low")),
            ("duplicate_account", ("duplicate account", "account already exists", "existing account")),
            ("invalid_credentials", ("invalid credentials", "incorrect password", "wrong password", "bad credentials")),
            ("valid_credentials", ("valid credentials", "correct password", "matching credentials")),
            ("unauthorized", ("unauthorized", "unauthenticated", "without authentication", "without authorization")),
        )
        return next(
            (name for name, aliases in patterns if any(alias in value for alias in aliases)),
            "",
        )

    @staticmethod
    def _canonical_expected(text: str) -> str:
        value = text.casefold()
        exception = re.search(r"\b([a-z_]*(?:error|exception))\b", value)
        if exception:
            return exception.group(1)
        if re.search(r"\b(?:returns?|is)\s+false\b|\bfails?\b|\breject", value):
            return "failure"
        if re.search(r"\b(?:returns?|is)\s+true\b|\bsucceeds?\b|\bcreated\b", value):
            return "success"
        value = re.sub(r"['\"][^'\"]*['\"]", "<value>", value)
        return " ".join(value.split())
