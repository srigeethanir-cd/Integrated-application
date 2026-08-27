import logging
from typing import List, Dict

from ...schemas.enums import Category, Priority, Severity
from ...schemas.test_case import TestCase

logger = logging.getLogger(__name__)


class PriorityEngine:
    """Assign priority and severity to test cases based on simple heuristics.

    This deterministic implementation uses keyword matching on the test case title
    and description. It can be replaced with a more sophisticated model without
    breaking the public interface.
    """

    _risk_keywords = ("data loss", "payment", "authorization", "authentication", "credential", "privacy")

    _severity_map: Dict[Severity, List[str]] = {
        Severity.BLOCKER: ["crash", "data loss", "security breach"],
        Severity.CRITICAL: ["error", "exception", "failure"],
        Severity.MAJOR: ["incorrect", "misbehave"],
        Severity.MINOR: ["typo", "ui misalignment"],
        Severity.TRIVIAL: ["cosmetic", "performance hint"],
    }

    def assign(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Return a new list of TestCase objects with updated priority and severity.

        The original TestCase instances are immutable (Pydantic models are by default
        mutable, but we treat them as immutable here). We create shallow copies with
        the updated enum values.
        """
        updated_cases: List[TestCase] = []
        for case in test_cases:
            title_desc = f"{case.title} {case.description}".lower()
            try:
                priority = Priority(getattr(case, "priority", None))
                priority_rule = None
            except (TypeError, ValueError):
                priority, priority_rule = self._fallback_priority(
                    case, title_desc
                )
            try:
                severity = Severity(getattr(case, "severity", None))
            except (TypeError, ValueError):
                severity = self._select_enum(
                    title_desc, self._severity_map, Severity.MINOR
                )
            traceability = dict(case.traceability or {})
            if priority_rule is not None:
                traceability["priority_rule"] = priority_rule
            updated_case = case.model_copy(
                update={
                    "priority": priority,
                    "severity": severity,
                    "traceability": traceability,
                }
            )
            logger.debug(
                "Assigned priority %s and severity %s to test case %s",
                priority.name,
                severity.name,
                case.id,
            )
            updated_cases.append(updated_case)
        return updated_cases

    def _fallback_priority(
        self, case: TestCase, title_desc: str
    ) -> tuple[Priority, str]:
        if any(keyword in title_desc for keyword in self._risk_keywords):
            return (
                Priority.CRITICAL,
                "business-risk: critical data/security operation",
            )
        if case.category == Category.SECURITY:
            return Priority.CRITICAL, "category: security"
        if case.category in {
            Category.NEGATIVE, Category.EXCEPTION_INTEGRATION
        }:
            return Priority.HIGH, f"category: {case.category.value}"
        if case.category == Category.BOUNDARY:
            return Priority.MEDIUM, "category: boundary"
        return Priority.MEDIUM, "category: positive"

    @staticmethod
    def _select_enum(text: str, mapping: Dict[object, List[str]], default) -> object:
        for enum_val, keywords in mapping.items():
            if any(keyword in text for keyword in keywords):
                return enum_val
        return default
