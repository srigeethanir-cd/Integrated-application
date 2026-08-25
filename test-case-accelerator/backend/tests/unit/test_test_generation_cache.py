from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from redis.exceptions import ConnectionError

from app.infrastructure.redis.cache_manager import CacheManager
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)
from app.services.ingestion.storage_service import StorageService


def _generation_service(generation: dict) -> tuple[CodeUnderstandingService, MagicMock, MagicMock, object]:
    project_id = uuid4()
    run = SimpleNamespace(
        id=uuid4(), project_id=project_id, dependency_run_id=uuid4(),
        prompt_version="stage3-v1", status="completed",
        result={"project_summary": "Example"},
    )
    service = object.__new__(CodeUnderstandingService)
    service._code_understanding_repository = MagicMock()
    service._code_understanding_repository.get_by_id.return_value = run
    service._test_generation_agent = MagicMock()
    service._test_generation_agent.generate.return_value = generation
    service._test_generation_agent.is_current_output.return_value = True
    service._cache_manager = MagicMock()
    service._generation_cache_key = MagicMock(return_value="test-generation:key")
    return service, service._cache_manager, service._test_generation_agent, run


def test_generation_cache_miss_persists_and_stores_completed_suite() -> None:
    generation = {
        "generated_test_cases": [{"id": "TC-1"}],
        "generation_status": "complete",
    }
    service, cache, agent, run = _generation_service(generation)
    cache.get.return_value = None
    cache.set.return_value = True

    result = service.generate_test_cases(run.project_id, run.id)

    assert result == generation
    agent.generate.assert_called_once_with({"project_summary": "Example"})
    service._code_understanding_repository.save_test_generation.assert_called_once_with(
        run, generation
    )
    cache.set.assert_called_once()


def test_generation_cache_hit_skips_llm_and_persists_cached_suite() -> None:
    cached = {
        "generated_test_cases": [{"id": "TC-cached"}],
        "generation_status": "complete",
    }
    service, cache, agent, run = _generation_service({})
    cache.get.return_value = cached

    result = service.generate_test_cases(run.project_id, run.id)

    assert result == cached
    agent.generate.assert_not_called()
    service._code_understanding_repository.save_test_generation.assert_called_once_with(
        run, cached
    )
    cache.set.assert_not_called()


def test_stale_generation_cache_is_regenerated() -> None:
    fresh = {
        "generated_test_cases": [{"id": "TC-fresh"}],
        "generation_status": "complete",
    }
    stale = {
        "generated_test_cases": [{"id": "TC-stale"}],
        "generation_status": "complete",
    }
    service, cache, agent, run = _generation_service(fresh)
    cache.get.return_value = stale
    cache.set.return_value = True
    agent.is_current_output.return_value = False

    result = service.generate_test_cases(run.project_id, run.id)

    assert result == fresh
    agent.generate.assert_called_once()
    service._code_understanding_repository.save_test_generation.assert_called_once_with(
        run, fresh
    )
    cache.set.assert_called_once()


def test_partial_generation_is_not_cached() -> None:
    partial = {
        "generated_test_cases": [{"id": "TC-partial"}],
        "generation_status": "partial_coverage_incomplete",
    }
    service, cache, _, run = _generation_service(partial)
    cache.get.return_value = None

    assert service.generate_test_cases(run.project_id, run.id) == partial
    cache.set.assert_not_called()


def test_redis_unavailable_falls_back_to_normal_generation() -> None:
    generation = {"generated_test_cases": [], "generation_status": "complete"}
    service, _, agent, run = _generation_service(generation)
    redis_client = MagicMock()
    redis_client.get.side_effect = ConnectionError("unavailable")
    service._cache_manager = CacheManager(redis_client)

    assert service.generate_test_cases(run.project_id, run.id) == generation
    agent.generate.assert_called_once()


def test_generation_hash_is_deterministic_and_invalidates_changed_inputs(tmp_path) -> None:
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    run_id = UUID("87654321-4321-8765-4321-876543218765")
    source = tmp_path / str(project_id) / "source"
    source.mkdir(parents=True)
    source_file = source / "app.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    discovered = SimpleNamespace(path=f"{project_id}/source/app.py")
    dependency = SimpleNamespace(files=[discovered])
    run = SimpleNamespace(dependency_run_id=uuid4(), prompt_version="stage3-v1")
    service = object.__new__(CodeUnderstandingService)
    service._storage_service = StorageService(tmp_path)
    service._project_repository = MagicMock()
    service._project_repository.get_by_id.return_value = SimpleNamespace(
        storage_path=str(project_id)
    )
    service._dependency_repository = MagicMock()
    service._dependency_repository.get_by_id.return_value = dependency
    service._test_generation_agent = MagicMock()
    service._test_generation_agent.cache_fingerprint.return_value = {
        "prompt_hash": "prompt-v1", "max_batch_functions": 4
    }

    first = service._generation_cache_key(project_id, run_id, run, {"summary": "v1"})
    repeated = service._generation_cache_key(project_id, run_id, run, {"summary": "v1"})
    changed_stage3 = service._generation_cache_key(
        project_id, run_id, run, {"summary": "v2"}
    )
    source_file.write_text("VALUE = 2\n", encoding="utf-8")
    changed_source = service._generation_cache_key(
        project_id, run_id, run, {"summary": "v1"}
    )
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    run.prompt_version = "stage3-v2"
    changed_stage3_prompt = service._generation_cache_key(
        project_id, run_id, run, {"summary": "v1"}
    )
    run.prompt_version = "stage3-v1"
    service._test_generation_agent.cache_fingerprint.return_value = {
        "prompt_hash": "prompt-v2", "max_batch_functions": 2
    }
    changed_generation_parameters = service._generation_cache_key(
        project_id, run_id, run, {"summary": "v1"}
    )

    assert first == repeated
    assert first != changed_stage3
    assert first != changed_source
    assert first != changed_stage3_prompt
    assert first != changed_generation_parameters
    assert first is not None and first.startswith(
        f"test-generation:{project_id}:{run_id}:"
    )
