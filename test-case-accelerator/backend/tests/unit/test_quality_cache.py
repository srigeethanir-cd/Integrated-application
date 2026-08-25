from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from redis.exceptions import ConnectionError

from app.agents.quality_evaluation.agent import TestQualityEvaluationAgent as QualityAgent
from app.infrastructure.redis.cache_manager import CacheManager
from app.schemas.test_case import TestCase as GeneratedTestCase
from app.schemas.test_quality import QualityLoopResult
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)


def _case(title: str = "Valid request") -> GeneratedTestCase:
    return GeneratedTestCase(
        id="TC-1", title=title, description="Verify behavior", category="positive",
        priority="high", severity="major", preconditions=[], steps=["Send request"],
        expected_results=["Request succeeds"], requirement_ids=[],
        business_rule_ids=[],
    )


def _quality_service(processing_status: str = "completed"):
    project_id, run_id = uuid4(), uuid4()
    run = SimpleNamespace(id=run_id, result={})
    optimized = MagicMock(spec=QualityLoopResult)
    optimized.processing_status = processing_status
    optimized.model_dump.return_value = {
        "processing_status": processing_status, "final_score": 95
    }
    loop = MagicMock()
    loop.run.return_value = optimized
    service = object.__new__(CodeUnderstandingService)
    service._quality_loop_service = loop
    service._code_understanding_repository = MagicMock()
    service._load_stage3_artifact = MagicMock(return_value=({"summary": "stage3"}, run))
    service._load_source_files = MagicMock(return_value=[{"path": "app.py"}])
    service._cache_manager = MagicMock()
    service._quality_cache_key = MagicMock(return_value="quality:key")
    return service, service._cache_manager, loop, optimized, run, project_id


def _verification(verified: int = 1) -> dict:
    return {
        "results": [{"test_case_id": "TC-1", "status": "Verified"}],
        "summary": {"verified": verified, "partial": 0, "failed": 0},
        "total_verified": verified,
    }


def test_quality_cache_miss_persists_and_stores_completed_result() -> None:
    service, cache, loop, optimized, run, project_id = _quality_service()
    cache.get.return_value = None
    cache.set.return_value = True

    result = service.optimize_test_quality(project_id, run.id, [_case()], _verification())

    assert result is optimized
    loop.run.assert_called_once()
    service._code_understanding_repository.save_quality_optimization.assert_called_once()
    assert cache.set.call_count == 2


def test_quality_cache_hit_skips_optimization_and_persists() -> None:
    service, cache, loop, _, run, project_id = _quality_service()
    cached_model = MagicMock(spec=QualityLoopResult)
    cached_model.model_dump.return_value = {"processing_status": "completed"}
    cache.get.return_value = {"processing_status": "completed"}
    service._completed_quality_optimization = MagicMock(return_value=cached_model)

    result = service.optimize_test_quality(project_id, run.id, [_case()], _verification())

    assert result is cached_model
    loop.run.assert_not_called()
    service._code_understanding_repository.save_quality_optimization.assert_called_once_with(
        run, {"processing_status": "completed"}
    )
    assert all(call.args[0] != "quality:key" for call in cache.set.call_args_list)


def test_partial_quality_optimization_is_not_cached() -> None:
    service, cache, _, optimized, run, project_id = _quality_service(
        "partial_success"
    )
    cache.get.return_value = None

    assert service.optimize_test_quality(
        project_id, run.id, [_case()], _verification()
    ) is optimized
    assert all(call.args[0] != "quality:key" for call in cache.set.call_args_list)


def test_redis_unavailable_falls_back_to_quality_optimization() -> None:
    service, _, loop, optimized, run, project_id = _quality_service()
    redis_client = MagicMock()
    redis_client.get.side_effect = ConnectionError("unavailable")
    service._cache_manager = CacheManager(redis_client)

    assert service.optimize_test_quality(
        project_id, run.id, [_case()], _verification()
    ) is optimized
    loop.run.assert_called_once()


def test_quality_hash_is_deterministic_and_invalidates_inputs() -> None:
    project_id, run_id = uuid4(), uuid4()
    service = object.__new__(CodeUnderstandingService)
    service._quality_loop_service = MagicMock()
    service._quality_loop_service.cache_fingerprint.return_value = {
        "threshold": 80, "max_iterations": 3, "prompt_hash": "v1"
    }
    first = service._quality_cache_key(
        project_id, run_id, [_case()], _verification(), {"summary": "stage3"},
        [{"content": "source"}],
    )
    repeated = service._quality_cache_key(
        project_id, run_id, [_case()], _verification(), {"summary": "stage3"},
        [{"content": "source"}],
    )
    changed_verification = service._quality_cache_key(
        project_id, run_id, [_case()], _verification(0), {"summary": "stage3"},
        [{"content": "source"}],
    )
    service._quality_loop_service.cache_fingerprint.return_value = {
        "threshold": 90, "max_iterations": 5, "prompt_hash": "v2"
    }
    changed_configuration = service._quality_cache_key(
        project_id, run_id, [_case()], _verification(), {"summary": "stage3"},
        [{"content": "source"}],
    )

    assert first == repeated
    assert first != changed_verification
    assert first != changed_configuration
    assert first is not None and first.startswith(f"quality:{project_id}:{run_id}:")


def test_quality_agent_fingerprint_contains_prompt_model_and_scoring() -> None:
    fingerprint = QualityAgent(model_name="model-a").cache_fingerprint()

    assert fingerprint["prompt_version"]
    assert fingerprint["prompt_hash"]
    assert fingerprint["model_name"] == "model-a"
    assert fingerprint["scoring_version"]
    assert fingerprint["scored_dimensions"]
