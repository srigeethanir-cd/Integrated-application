import logging
from typing import List

from ...schemas.enums import Category
from ...schemas.test_case import TestCase

logger = logging.getLogger(__name__)


class CategoryEngine:
    """Derive the supported category taxonomy from asserted behavior."""

    def assign(self, test_cases: List[TestCase]) -> List[TestCase]:
        assigned = []
        for case in test_cases:
            try:
                category = Category(getattr(case, "category", None))
            except (TypeError, ValueError):
                category = self.classify([case])[0]
            assigned.append(case.model_copy(update={"category": category}))
        return assigned

    def classify(self, test_cases: List[TestCase]) -> List[Category]:
        categories = []
        for case in test_cases:
            outcome = " ".join(case.expected_results).casefold()
            scenario = (
                f"{case.title} {case.description} {' '.join(case.steps)}"
            ).casefold()
            if any(
                word in scenario
                for word in (
                    "boundary", "exactly", "minimum", "maximum", "empty", "zero",
                )
            ):
                category = Category.BOUNDARY
            elif any(
                word in outcome
                for word in (
                    "raise", "error", "exception", "invalid", "reject", "fail",
                    "false", "keyerror",
                )
            ):
                category = Category.NEGATIVE
            elif any(
                word in scenario
                for word in (
                    "auth", "permission", "unauthorized", "token", "injection",
                )
            ):
                category = Category.SECURITY
            elif any(
                word in scenario
                for word in ("external", "integration", "dependency", "service")
            ):
                category = Category.EXCEPTION_INTEGRATION
            else:
                category = Category.POSITIVE
            categories.append(category)
            logger.debug("Classified test case %s as %s", case.id, category.value)
        return categories
