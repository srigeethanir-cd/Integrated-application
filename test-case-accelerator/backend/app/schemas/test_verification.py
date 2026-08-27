"""Transport and provider schemas for Stage 5 test-case verification."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VerificationStatus(StrEnum):
    VERIFIED = "Verified"
    PARTIAL = "Partial"
    FAILED = "Failed"


class VerificationPath(StrEnum):
    RULE_BASED = "Rule-Based"
    RULE_AND_LLM = "Rule+LLM"


class VerificationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    symbol: str | None = None
    line: int | None = Field(default=None, ge=1)
    detail: str


class VerificationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check: str
    status: VerificationStatus
    detail: str
    evidence: list[VerificationEvidence] = Field(default_factory=list)


class TestCaseVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_case_id: str
    status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    verification_path: VerificationPath = VerificationPath.RULE_BASED
    evidence: list[VerificationEvidence] = Field(default_factory=list)
    findings: list[VerificationFinding] = Field(default_factory=list)


class LLMVerificationBatch(BaseModel):
    """Strict JSON object returned by the verification provider."""

    model_config = ConfigDict(extra="forbid")

    verifications: list[TestCaseVerification]


class VerificationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: int = Field(ge=0)
    partial: int = Field(ge=0)
    failed: int = Field(ge=0)


class TestVerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[TestCaseVerification]
    summary: VerificationSummary
    total_verified: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_aggregates(self) -> "TestVerificationResult":
        counts = {
            VerificationStatus.VERIFIED: 0,
            VerificationStatus.PARTIAL: 0,
            VerificationStatus.FAILED: 0,
        }
        for result in self.results:
            checks = [finding.check for finding in result.findings]
            if len(checks) != len(set(checks)):
                raise ValueError("Verification findings must have unique checks")
            if result.findings:
                rank = {
                    VerificationStatus.VERIFIED: 0,
                    VerificationStatus.PARTIAL: 1,
                    VerificationStatus.FAILED: 2,
                }
                expected_status = max(
                    (finding.status for finding in result.findings),
                    key=rank.__getitem__,
                )
                if result.status != expected_status:
                    raise ValueError(
                        "Verification status does not match finding statuses"
                    )
            counts[result.status] += 1
        expected = VerificationSummary(
            verified=counts[VerificationStatus.VERIFIED],
            partial=counts[VerificationStatus.PARTIAL],
            failed=counts[VerificationStatus.FAILED],
        )
        if self.summary != expected:
            raise ValueError("Verification summary does not match result statuses")
        if self.total_verified != expected.verified:
            raise ValueError("total_verified must equal the Verified result count")
        return self
