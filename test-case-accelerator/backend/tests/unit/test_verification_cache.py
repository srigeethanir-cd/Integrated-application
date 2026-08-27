from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from redis.exceptions import ConnectionError

from app.agents.semantic_verification.agent import TestVerificationAgent as VerificationAgent
from app.infrastructure.redis.cache_manager import CacheManager
from app.schemas.test_case import TestCase as GeneratedTestCase
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)


def _case(case_id: str = "TC-1", title: str = "Valid request") -> GeneratedTestCase:
    return GeneratedTestCase(
        id=case_id,
        title=title,
        description="Verify behavior",
        category="positive",
        priority="high",
        severity="major",
        preconditions=[],
        steps=["Send request"],
        expected_results=["Request succeeds"],
        requirement_ids=[],
        business_rule_ids=[],
    )


def _completed_verification(test_id: str = "TC-1") -> dict:
    return {
        "results": [{"test_case_id": test_id}],
        "summary": {"verified": 1, "partial": 0, "failed": 0},
        "total_verified": 1,
    }


def _verification_service(result: dict):
    project_id = uuid4()
    run = SimpleNamespace(id=uuid4(), project_id=project_id, dependency_run_id=uuid4())
    service = object.__new__(CodeUnderstandingService)
    service._load_stage3_artifact = MagicMock(return_value=({"summary": "stage3"}, run))
    service._project_repository = MagicMock()
    service._project_repository.get_by_id.return_value = SimpleNamespace(
        storage_path="unused"
    )
    service._dependency_repository = MagicMock()
    service._dependency_repository.get_by_id.return_value = SimpleNamespace(
        status="completed", files=[]
    )
    service._resolve_source_directory = MagicMock()
    service._build_context = MagicMock(return_value=SimpleNamespace(files=[]))
    service._code_understanding_repository = MagicMock()
    service._test_verification_agent = MagicMock()
    service._test_verification_agent.verify.return_value = result
    service._cache_manager = MagicMock()
    service._verification_cache_key = MagicMock(return_value="verification:key")
    return service, service._cache_manager, service._test_verification_agent, run


def test_verification_cache_miss_persists_and_stores_completed_result() -> None:
    verification = _completed_verification()
    service, cache, agent, run = _verification_service(verification)
    cache.get.return_value = None
    cache.set.return_value = True

    result = service.verify_test_cases(run.project_id, run.id, [_case()])

    assert result == verification
    agent.verify.assert_called_once()
    service._code_understanding_repository.save_test_verification.assert_called_once_with(
        run, verification
    )
    cache.set.assert_called_once()


def test_verification_cache_hit_skips_semantic_agent_and_persists() -> None:
    cached = _completed_verification()
    service, cache, agent, run = _verification_service({})
    cache.get.return_value = cached

    result = service.verify_test_cases(run.project_id, run.id, [_case()])

    assert result == cached
    agent.verify.assert_not_called()
    service._code_understanding_repository.save_test_verification.assert_called_once_with(
        run, cached
    )
    cache.set.assert_not_called()


def test_partial_or_failed_verification_is_not_cached() -> None:
    partial = {
        "results": [{"test_case_id": "TC-1"}],
        "summary": {"verified": 0, "partial": 1, "failed": 0},
        "total_verified": 0,
    }
    service, cache, _, run = _verification_service(partial)
    cache.get.return_value = None

    assert service.verify_test_cases(run.project_id, run.id, [_case()]) == partial
    cache.set.assert_not_called()


def test_redis_unavailable_falls_back_to_verification() -> None:
    verification = _completed_verification()
    service, _, agent, run = _verification_service(verification)
    redis_client = MagicMock()
    redis_client.get.side_effect = ConnectionError("unavailable")
    service._cache_manager = CacheManager(redis_client)

    assert service.verify_test_cases(run.project_id, run.id, [_case()]) == verification
    agent.verify.assert_called_once()


def test_verification_hash_is_deterministic_and_invalidates_inputs() -> None:
    project_id = uuid4()
    run_id = uuid4()
    service = object.__new__(CodeUnderstandingService)
    service._test_verification_agent = MagicMock()
    service._test_verification_agent.cache_fingerprint.return_value = {
        "prompt_version": "1.0", "threshold": 0.8
    }
    first = service._verification_cache_key(
        project_id, run_id, [_case()], {"summary": "stage3"}, [{"content": "v1"}]
    )
    repeated = service._verification_cache_key(
        project_id, run_id, [_case()], {"summary": "stage3"}, [{"content": "v1"}]
    )
    changed_suite = service._verification_cache_key(
        project_id, run_id, [_case(title="Changed")], {"summary": "stage3"},
        [{"content": "v1"}],
    )
    service._test_verification_agent.cache_fingerprint.return_value = {
        "prompt_version": "2.0", "threshold": 0.9
    }
    changed_configuration = service._verification_cache_key(
        project_id, run_id, [_case()], {"summary": "stage3"}, [{"content": "v1"}]
    )

    assert first == repeated
    assert first != changed_suite
    assert first != changed_configuration
    assert first is not None and first.startswith(
        f"verification:{project_id}:{run_id}:"
    )


def test_semantic_agent_fingerprint_contains_prompt_model_and_thresholds() -> None:
    fingerprint = VerificationAgent(
        model_name="model-a", rule_confidence_threshold=0.7,
        max_provider_attempts=2,
    ).cache_fingerprint()

    assert fingerprint["prompt_version"]
    assert fingerprint["semantic_prompt_hash"]
    assert fingerprint["model_name"] == "model-a"
    assert fingerprint["rule_confidence_threshold"] == 0.7
    assert fingerprint["max_provider_attempts"] == 2
