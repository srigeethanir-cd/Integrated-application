import logging
import re
from typing import Any, Dict, List

from ...schemas.enums import Category
from ...schemas.test_case import TestCase

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Calculate coverage statistics for a collection of test cases.

    The implementation is deterministic and based on simple counts of categories
    and requirement IDs. It can be extended with more sophisticated analysis
    without changing the public interface.
    """

    VALID_CATEGORIES = (
        Category.POSITIVE,
        Category.NEGATIVE,
        Category.BOUNDARY,
        Category.SECURITY,
        Category.EXCEPTION_INTEGRATION,
    )

    def analyze(
        self,
        test_cases: List[TestCase],
        stage3_payload: dict[str, Any] | None = None,
    ) -> Dict[str, float]:
        """Return a dictionary with coverage percentages.

        Keys include:
        - ``requirement_coverage`` – % of unique requirement IDs covered.
        - ``category_coverage`` – % of defined categories represented.
        """
        if not test_cases:
            logger.warning("CoverageAnalyzer received empty test case list")
            return {
                "requirement_coverage": 0.0, "category_coverage": 0.0,
                "function_coverage": 0.0, "branch_coverage": 0.0,
                "target_coverage": 0.0, "completeness": 0.0,
            }

        # Requirement coverage
        all_req_ids = {req for case in test_cases for req in case.requirement_ids}
        # In a real system we would compare against the complete requirement set.
        # Here we assume the set of encountered IDs represents 100% of the known
        # requirements for deterministic behaviour.
        requirement_coverage = 100.0 if all_req_ids else 0.0

        # Category coverage
        covered_categories = {case.category for case in test_cases}
        total_categories = len(self.VALID_CATEGORIES)
        category_coverage = (len(covered_categories) / total_categories) * 100.0 if total_categories else 0.0

        targets = (stage3_payload or {}).get("test_targets", [])
        covered_symbols = {
            symbol
            for case in test_cases
            for symbol in self._symbols(case)
        }
        function_coverage = self._ratio(
            sum(target.get("symbol") in covered_symbols for target in targets),
            len(targets),
        ) if targets else 100.0
        branch_requirements = [
            (target.get("symbol"), branch, category)
            for target in targets
            for branch in [*target.get("branches", []), *target.get("edge_cases", [])]
            for category in (Category.POSITIVE, Category.NEGATIVE)
        ]
        covered_branches = sum(
            self._branch_covered(test_cases, symbol, branch, category)
            for symbol, branch, category in branch_requirements
        )
        branch_coverage = self._ratio(covered_branches, len(branch_requirements)) if branch_requirements else 100.0
        covered_functions = sum(
            target.get("symbol") in covered_symbols for target in targets
        )
        target_coverage = self._ratio(
            covered_functions + covered_branches,
            len(targets) + len(branch_requirements),
        )
        branch_units = [
            (target.get("symbol"), branch)
            for target in targets
            for branch in [*target.get("branches", []), *target.get("edge_cases", [])]
        ]
        covered_units = sum(target.get("symbol") in covered_symbols for target in targets)
        covered_units += sum(
            self._branch_has_any(test_cases, symbol, branch)
            for symbol, branch in branch_units
        )
        completeness = self._ratio(covered_units, len(targets) + len(branch_units))

        logger.debug(
            "Coverage calculated: requirement %.2f%%, category %.2f%%",
            requirement_coverage,
            category_coverage,
        )
        return {
            "requirement_coverage": requirement_coverage,
            "category_coverage": category_coverage,
            "function_coverage": function_coverage,
            "branch_coverage": branch_coverage,
            "target_coverage": target_coverage,
            "completeness": completeness,
        }

    def completion_gaps(
        self, test_cases: List[TestCase], stage3_payload: dict[str, Any]
    ) -> list[dict[str, str]]:
        gaps = []
        for target in stage3_payload.get("test_targets", []):
            symbol = target.get("symbol")
            if not symbol:
                continue
            if not any(symbol in self._symbols(case) for case in test_cases):
                gaps.append(self._gap(symbol, "function", Category.POSITIVE))
            for branch in [*target.get("branches", []), *target.get("edge_cases", [])]:
                for category in (Category.POSITIVE, Category.NEGATIVE):
                    if not self._branch_covered(test_cases, symbol, branch, category):
                        gaps.append(self._gap(symbol, branch, category))
        return gaps

    @classmethod
    def _gap(cls, symbol: str, requirement: str, category: Category) -> dict[str, str]:
        return {
            "symbol": symbol,
            "requirement": requirement,
            "category": category.value,
            "requirement_id": cls.requirement_id(symbol, requirement, category),
        }

    @staticmethod
    def requirement_id(symbol: str, requirement: str, category: Category) -> str:
        normalized = "-".join(re.findall(r"[A-Za-z0-9]+", requirement.casefold()))
        return f"{symbol.casefold()}|{category.value}|{normalized}"

    @staticmethod
    def _symbols(case: TestCase) -> set[str]:
        trace = case.traceability or {}
        values = trace.get("symbols", [])
        return {*(values if isinstance(values, list) else []), trace.get("symbol")} - {None}

    @classmethod
    def _branch_covered(cls, cases, symbol, branch, category) -> bool:
        tokens = {item.casefold() for item in re.findall(r"[A-Za-z0-9]+", branch) if len(item) > 2}
        accepted = {category}
        if category == Category.NEGATIVE:
            accepted.add(Category.BOUNDARY)
        requirement_id = cls.requirement_id(symbol, branch, category)
        for case in cases:
            trace = case.traceability or {}
            markers = trace.get("coverage_requirements", [])
            if requirement_id in markers:
                return True
            if symbol not in cls._symbols(case) or case.category not in accepted:
                continue
            case_tokens = {
                item.casefold()
                for item in re.findall(
                    r"[A-Za-z0-9]+",
                    " ".join([case.title, case.description, *case.steps, *case.expected_results]),
                )
                if len(item) > 2
            }
            numeric_tokens = {item for item in tokens if item.isdigit()}
            overlap = len(tokens & case_tokens) / len(tokens) if tokens else 1
            if numeric_tokens.issubset(case_tokens) and overlap >= 0.6:
                return True
        return False

    @classmethod
    def _branch_has_any(cls, cases, symbol, branch) -> bool:
        return any(
            cls._branch_covered(cases, symbol, branch, category)
            for category in cls.VALID_CATEGORIES
        )

    @staticmethod
    def _ratio(value: int, total: int) -> float:
        return round(value / total * 100, 2) if total else 100.0
