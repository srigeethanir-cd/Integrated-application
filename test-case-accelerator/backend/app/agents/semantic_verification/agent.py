"""Hybrid Stage 5 test-case verification agent."""

from __future__ import annotations

import json
import logging
import time
import hashlib
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from app.agents.semantic_verification.rule_engine import (
    RULE_ENGINE_VERSION,
    VerificationRuleEngine,
)
from app.schemas.test_case import TestCase
from app.schemas.test_verification import (
    LLMVerificationBatch,
    TestCaseVerification,
    TestVerificationResult,
    VerificationFinding,
    VerificationPath,
    VerificationStatus,
    VerificationSummary,
)

logger = logging.getLogger(__name__)
SEMANTIC_VERIFICATION_PROMPT_VERSION = "1.0.0"
SEMANTIC_VERIFICATION_SYSTEM_PROMPT = (
    "Verify every test case against only the supplied backend code. "
    "Check routes, request and response models, status codes, input validations, "
    "and exception handling. Cite file, symbol, and line when available. Return "
    "one result per test_case_id. Do not invent evidence."
)


class TestVerificationError(RuntimeError):
    """Raised when Stage 5 cannot produce validated verification output."""


class StructuredVerificationClient(Protocol):
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel: ...


class TestVerificationAgent:
    """Combine code-grounded rules with structured LLM verification."""

    def __init__(
        self,
        *,
        client: StructuredVerificationClient | None = None,
        rule_engine: VerificationRuleEngine | None = None,
        max_provider_attempts: int = 3,
        retry_base_delay: float = 0.25,
        max_retry_delay: float = 2.0,
        rule_confidence_threshold: float = 0.8,
        sleep: Callable[[float], None] = time.sleep,
        model_name: str = "unknown",
    ) -> None:
        if max_provider_attempts < 1:
            raise ValueError("max_provider_attempts must be at least 1")
        if retry_base_delay < 0 or max_retry_delay < 0:
            raise ValueError("Retry delays cannot be negative")
        if not 0 <= rule_confidence_threshold <= 1:
            raise ValueError("rule_confidence_threshold must be between 0 and 1")
        self._client = client
        self._rule_engine = rule_engine or VerificationRuleEngine()
        self._max_provider_attempts = max_provider_attempts
        self._retry_base_delay = retry_base_delay
        self._max_retry_delay = max_retry_delay
        self._rule_confidence_threshold = rule_confidence_threshold
        self._sleep = sleep
        self._last_provider_failure_reason: str | None = None
        self._model_name = model_name

    def cache_fingerprint(self) -> dict[str, Any]:
        """Return stable prompt, model, threshold, and retry configuration.

        Returns:
            JSON-compatible values affecting deterministic verification output.
        """
        return {
            "prompt_version": SEMANTIC_VERIFICATION_PROMPT_VERSION,
            "semantic_prompt_hash": hashlib.sha256(
                SEMANTIC_VERIFICATION_SYSTEM_PROMPT.encode("utf-8")
            ).hexdigest(),
            "model_name": self._model_name,
            "max_provider_attempts": self._max_provider_attempts,
            "retry_base_delay": self._retry_base_delay,
            "max_retry_delay": self._max_retry_delay,
            "rule_confidence_threshold": self._rule_confidence_threshold,
            "rule_engine": type(self._rule_engine).__qualname__,
            "rule_engine_version": RULE_ENGINE_VERSION,
        }

    def verify(
        self,
        test_cases: list[TestCase] | list[dict[str, Any]],
        stage3_payload: dict[str, Any],
        source_files: list[dict[str, Any]],
        repo_root: str | None = None,
    ) -> dict[str, Any]:
        try:
            cases = [TestCase.model_validate(case) for case in test_cases]
        except ValidationError as error:
            raise TestVerificationError(
                "Invalid test case supplied for verification"
            ) from error

        rule_results = self._rule_engine.verify(cases, stage3_payload, source_files, repo_root=repo_root)
        self._last_provider_failure_reason = None
        low_ids = {
            item.test_case_id
            for item in rule_results
            if item.confidence < self._rule_confidence_threshold
        }
        low_cases = [case for case in cases if case.id in low_ids]
        low_rules = [item for item in rule_results if item.test_case_id in low_ids]
        resolved = {item.test_case_id: item for item in rule_results if item.test_case_id not in low_ids}
        for item in rule_results:
            logger.info(
                "Verification routing test_case_id=%s rule_confidence=%.3f "
                "semantic_verification_invoked=%s escalation_reason=%s",
                item.test_case_id, item.confidence, item.test_case_id in low_ids,
                (
                    "rule_confidence_below_threshold"
                    if item.test_case_id in low_ids else "rule_evidence_sufficient"
                ),
            )
        if low_cases:
            llm_results = self._verify_with_llm(
                low_cases, stage3_payload, source_files, low_rules
            )
            reviewed = (
                self._provider_fallback(low_rules)
                if llm_results is None
                else self._merge(low_rules, llm_results)
            )
            if llm_results is None:
                fallback_percentage = len(low_rules) / len(cases) * 100 if cases else 0
                if fallback_percentage > 50:
                    logger.warning(
                        "Semantic verification fallback threshold exceeded "
                        "fallback_percentage=%.2f provider_failure_reason=%s "
                        "affected_tests=%d total_tests=%d",
                        fallback_percentage,
                        self._last_provider_failure_reason or "unknown",
                        len(low_rules), len(cases),
                    )
            resolved.update({item.test_case_id: item for item in reviewed})
        merged = [resolved[case.id] for case in cases]
        merged = [
            self._enforce_verified_completeness(case, result)
            for case, result in zip(cases, merged, strict=True)
        ]
        for item in merged:
            logger.info(
                "Verification completed test_case_id=%s final_status=%s "
                "final_confidence=%.3f verification_path=%s",
                item.test_case_id, item.status.value, item.confidence,
                item.verification_path.value,
            )
        summary = VerificationSummary(
            verified=sum(item.status == VerificationStatus.VERIFIED for item in merged),
            partial=sum(item.status == VerificationStatus.PARTIAL for item in merged),
            failed=sum(item.status == VerificationStatus.FAILED for item in merged),
        )
        return TestVerificationResult(
            results=merged,
            summary=summary,
            total_verified=summary.verified,
        ).model_dump(mode="json")

    @staticmethod
    def _enforce_verified_completeness(
        case: TestCase, result: TestCaseVerification
    ) -> TestCaseVerification:
        if result.status != VerificationStatus.VERIFIED:
            return result
        missing = []
        if not case.title.strip():
            missing.append("title")
        if not any(item.strip() for item in case.steps):
            missing.append("steps")
        if not any(item.strip() for item in case.expected_results):
            missing.append("expected_results")
        if not result.evidence:
            missing.append("evidence")
        if not missing:
            return result
        finding = VerificationFinding(
            check="verified_record_completeness",
            status=VerificationStatus.PARTIAL,
            detail=f"Verified record is missing: {', '.join(missing)}",
        )
        return result.model_copy(update={
            "status": VerificationStatus.PARTIAL,
            "confidence": min(result.confidence, 0.5),
            "findings": [*result.findings, finding],
        })

    def _verify_with_llm(
        self,
        cases: list[TestCase],
        stage3_payload: dict[str, Any],
        source_files: list[dict[str, Any]],
        rule_results: list[TestCaseVerification],
    ) -> list[TestCaseVerification] | None:
        if self._client is None:
            self._last_provider_failure_reason = "provider_not_configured"
            return None
        prompt = json.dumps(
            {
                "test_cases": [case.model_dump(mode="json") for case in cases],
                "code_understanding": stage3_payload,
                "source_files": source_files,
                "rule_results": [item.model_dump(mode="json") for item in rule_results],
            },
            ensure_ascii=False,
        )
        for attempt in range(1, self._max_provider_attempts + 1):
            try:
                response = self._client.generate_structured(
                    system_prompt=SEMANTIC_VERIFICATION_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    response_model=LLMVerificationBatch,
                )
                batch = LLMVerificationBatch.model_validate(response)
                self._validate_result_ids(cases, batch)
                return batch.verifications
            except Exception as error:
                if attempt == self._max_provider_attempts:
                    self._last_provider_failure_reason = type(error).__name__
                    logger.warning(
                        "Test-verification provider unavailable after %d attempt(s): %s",
                        attempt,
                        type(error).__name__,
                    )
                    return None
                delay = self._retry_delay(error, attempt)
                logger.info(
                    "Retrying test-verification provider after %s (attempt %d/%d)",
                    type(error).__name__,
                    attempt + 1,
                    self._max_provider_attempts,
                )
                self._sleep(delay)
        return None  # Defensive; the loop always returns.

    @staticmethod
    def _validate_result_ids(
        cases: list[TestCase], batch: LLMVerificationBatch
    ) -> None:
        expected_ids = [case.id for case in cases]
        actual_ids = [item.test_case_id for item in batch.verifications]
        if len(actual_ids) != len(expected_ids) or sorted(actual_ids) != sorted(
            expected_ids
        ):
            raise ValueError(
                "Test-verification provider did not return one result per test case"
            )

    def _retry_delay(self, error: Exception, attempt: int) -> float:
        delay = self._retry_base_delay * (2 ** (attempt - 1))
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        if headers:
            retry_after = headers.get("retry-after")
            try:
                delay = max(delay, float(retry_after))
            except (TypeError, ValueError):
                pass
        return min(delay, self._max_retry_delay)

    @staticmethod
    def _provider_fallback(
        rule_results: list[TestCaseVerification],
    ) -> list[TestCaseVerification]:
        fallback = []
        for rule in rule_results:
            status = (
                VerificationStatus.FAILED
                if rule.status == VerificationStatus.FAILED
                else VerificationStatus.PARTIAL
            )
            findings = TestVerificationAgent._consolidate_findings(
                [
                    *rule.findings,
                    VerificationFinding(
                        check="provider_verification",
                        status=VerificationStatus.PARTIAL,
                        detail=(
                            "Provider verification was temporarily unavailable; "
                            "rule-based evidence was retained"
                        ),
                    ),
                ]
            )
            fallback.append(
                rule.model_copy(
                    update={
                        "status": TestVerificationAgent._status_from_findings(
                            findings, status
                        ),
                        "confidence": min(rule.confidence, 0.5),
                        "findings": findings,
                        "verification_path": VerificationPath.RULE_AND_LLM,
                    }
                )
            )
        return fallback

    @staticmethod
    def _merge(
        rule_results: list[TestCaseVerification],
        llm_results: list[TestCaseVerification],
    ) -> list[TestCaseVerification]:
        llm_by_id = {item.test_case_id: item for item in llm_results}
        merged = []
        for rule in rule_results:
            llm = llm_by_id.get(rule.test_case_id)
            if llm is None:
                findings = TestVerificationAgent._consolidate_findings(rule.findings)
                merged.append(
                    rule.model_copy(
                        update={
                            "status": TestVerificationAgent._status_from_findings(
                                findings, rule.status
                            ),
                            "findings": findings,
                        }
                    )
                )
                continue
            llm_findings = list(llm.findings)
            if (
                llm.status == VerificationStatus.VERIFIED
                and any(
                    item.check == "behavior_semantics"
                    and item.status == VerificationStatus.PARTIAL
                    for item in rule.findings
                )
                and not any(item.check == "behavior_semantics" for item in llm_findings)
            ):
                llm_findings.append(VerificationFinding(
                    check="behavior_semantics",
                    status=VerificationStatus.VERIFIED,
                    detail="Semantic verification confirmed the behavioral expectation",
                    evidence=llm.evidence,
                ))
            rule_findings = [
                item for item in rule.findings
                if not (
                    llm.status == VerificationStatus.VERIFIED
                    and item.check == "behavior_semantics"
                    and item.status == VerificationStatus.PARTIAL
                )
            ]
            findings = TestVerificationAgent._consolidate_findings(
                [*rule_findings, *llm_findings]
            )
            declared_status = TestVerificationAgent._strongest_status(
                rule.status, llm.status
            )
            status = TestVerificationAgent._status_from_findings(
                findings, declared_status
            )
            evidence = list(rule.evidence)
            known = {
                (item.file, item.symbol, item.line, item.detail) for item in evidence
            }
            for item in llm.evidence:
                key = (item.file, item.symbol, item.line, item.detail)
                if key not in known:
                    known.add(key)
                    evidence.append(item)
            merged.append(
                TestCaseVerification(
                    test_case_id=rule.test_case_id,
                    status=status,
                    confidence=round((rule.confidence + llm.confidence) / 2, 3),
                    verification_path=VerificationPath.RULE_AND_LLM,
                    evidence=evidence,
                    findings=findings,
                )
            )
        return merged

    @staticmethod
    def _consolidate_findings(
        findings: list[VerificationFinding],
    ) -> list[VerificationFinding]:
        grouped: dict[str, list[VerificationFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.check, []).append(finding)

        consolidated = []
        for check, candidates in grouped.items():
            status = TestVerificationAgent._strongest_status(
                *(candidate.status for candidate in candidates)
            )
            winners = [
                candidate for candidate in candidates if candidate.status == status
            ]
            evidence = []
            seen = set()
            for winner in winners:
                for item in winner.evidence:
                    key = (item.file, item.symbol, item.line, item.detail)
                    if key not in seen:
                        seen.add(key)
                        evidence.append(item)
            consolidated.append(
                VerificationFinding(
                    check=check,
                    status=status,
                    detail=winners[0].detail,
                    evidence=evidence,
                )
            )
        return consolidated

    @staticmethod
    def _strongest_status(*statuses: VerificationStatus) -> VerificationStatus:
        rank = {
            VerificationStatus.VERIFIED: 0,
            VerificationStatus.PARTIAL: 1,
            VerificationStatus.FAILED: 2,
        }
        return max(statuses, key=rank.__getitem__)

    @staticmethod
    def _status_from_findings(
        findings: list[VerificationFinding],
        default: VerificationStatus,
    ) -> VerificationStatus:
        if not findings:
            return default
        return TestVerificationAgent._strongest_status(
            *(finding.status for finding in findings)
        )


__all__ = ["TestVerificationAgent", "TestVerificationError"]
