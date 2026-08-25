import pytest
from pydantic import ValidationError

from app.schemas.test_verification import TestVerificationResult as VerificationResult


def test_verification_result_rejects_inconsistent_aggregates() -> None:
    with pytest.raises(ValidationError, match="summary does not match"):
        VerificationResult.model_validate(
            {
                "results": [
                    {
                        "test_case_id": "TC-1",
                        "status": "Verified",
                        "confidence": 0.9,
                        "evidence": [],
                        "findings": [],
                    }
                ],
                "summary": {"verified": 0, "partial": 1, "failed": 0},
                "total_verified": 0,
            }
        )


def test_verification_result_rejects_inconsistent_total_verified() -> None:
    with pytest.raises(ValidationError, match="Verified result count"):
        VerificationResult.model_validate(
            {
                "results": [
                    {
                        "test_case_id": "TC-1",
                        "status": "Verified",
                        "confidence": 0.9,
                        "evidence": [],
                        "findings": [],
                    }
                ],
                "summary": {"verified": 1, "partial": 0, "failed": 0},
                "total_verified": 0,
            }
        )


def test_verification_result_rejects_duplicate_checks() -> None:
    with pytest.raises(ValidationError, match="unique checks"):
        VerificationResult.model_validate(
            {
                "results": [
                    {
                        "test_case_id": "TC-1",
                        "status": "Verified",
                        "confidence": 0.9,
                        "evidence": [],
                        "findings": [
                            {
                                "check": "route",
                                "status": "Verified",
                                "detail": "First",
                            },
                            {
                                "check": "route",
                                "status": "Verified",
                                "detail": "Second",
                            },
                        ],
                    }
                ],
                "summary": {"verified": 1, "partial": 0, "failed": 0},
                "total_verified": 1,
            }
        )
