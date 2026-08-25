import pytest
from pydantic import ValidationError

from app.schemas.enums import Category
from app.schemas.test_case import TestCase as CaseSchema
from app.schemas.test_quality import QualityFeedback


def _case(category: str) -> dict:
    return {
        "id": "TC-1", "title": "Scenario", "description": "Scenario",
        "category": category, "priority": "medium", "severity": "major",
        "steps": ["Act"], "expected_results": ["Result"],
    }


def test_generation_schema_remaps_known_legacy_categories() -> None:
    assert CaseSchema.model_validate(_case("functional")).category == Category.POSITIVE
    assert CaseSchema.model_validate(_case("performance")).category == Category.BOUNDARY
    assert CaseSchema.model_validate(_case("integration")).category == Category.EXCEPTION_INTEGRATION


def test_generation_schema_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        CaseSchema.model_validate(_case("accessibility"))


def test_quality_feedback_rejects_performance_gap() -> None:
    with pytest.raises(ValidationError):
        QualityFeedback(missing_categories=["performance"])
