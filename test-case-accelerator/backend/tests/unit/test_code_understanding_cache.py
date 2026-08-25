from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from app.database.models.code_understanding import CodeUnderstandingStatus
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)
from app.services.ingestion.storage_service import StorageService
import pytest


def _service_fixture(tmp_path):
    project_id = UUID("12345678-1234-5678-1234-567812345678")
    dependency_run_id = UUID("87654321-4321-8765-4321-876543218765")
    source_directory = tmp_path / str(project_id) / "source"
    source_directory.mkdir(parents=True)
    source_file = source_directory / "app.py"
    source_file.write_text("def hello():\n    return 'hello'\n", encoding="utf-8")

    project_repository = MagicMock()
    project_repository.get_by_id.return_value = SimpleNamespace(
        id=project_id, storage_path=str(project_id)
    )
    dependency_repository = MagicMock()
    dependency_repository.get_by_id.return_value = SimpleNamespace(
        id=dependency_run_id,
        project_id=project_id,
        status="completed",
        files=[SimpleNamespace(
            path=f"{project_id}/source/app.py",
            language="python",
            is_entry_point=True,
            imports=[],
            classes=[],
            functions=["hello"],
        )],
    )
    repository = MagicMock()
    pending_run = SimpleNamespace(id=uuid4(), status="pending", result=None)
    completed_run = SimpleNamespace(
        id=pending_run.id,
        status=CodeUnderstandingStatus.COMPLETED,
        result={"project_summary": "A greeting service"},
    )
    repository.create_run.return_value = pending_run
    repository.complete.return_value = completed_run
    agent = MagicMock()
    agent.analyze.return_value.model_dump.return_value = completed_run.result
    cache = MagicMock()
    service = CodeUnderstandingService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        code_understanding_repository=repository,
        storage_service=StorageService(tmp_path),
        agent=agent,
        model_name="test-model",
        cache_manager=cache,
    )
    return service, cache, agent, repository, source_file, project_id, dependency_run_id


def test_code_understanding_cache_miss_executes_and_stores(tmp_path) -> None:
    service, cache, agent, repository, _, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    cache.get.return_value = None
    cache.set.return_value = True

    result = service.understand(project_id, dependency_run_id)

    assert result is repository.complete.return_value
    agent.analyze.assert_called_once()
    key = cache.get.call_args_list[0].args[0]
    assert key.startswith(f"code-understanding:{project_id}:")
    assert cache.set.call_count == 2


def test_code_understanding_cache_hit_skips_agent_and_new_run(tmp_path) -> None:
    service, cache, agent, repository, _, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    cached_run = SimpleNamespace(
        id=uuid4(), status=CodeUnderstandingStatus.COMPLETED,
        result={
            "project_summary": "Cached",
            "_artifact_version": service._artifact_version_manifest(
                include_pipeline=False
            ),
        },
    )
    cache.get.return_value = {
        "run_id": str(cached_run.id), "status": "completed", "result": cached_run.result
    }
    repository.get_by_id.return_value = cached_run

    result = service.understand(project_id, dependency_run_id)

    assert result is cached_run
    agent.analyze.assert_not_called()
    repository.create_run.assert_not_called()
    cache.set.assert_not_called()


def test_source_change_uses_a_new_content_addressed_key(tmp_path) -> None:
    service, cache, _, _, source_file, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    cache.get.return_value = None
    cache.set.return_value = True

    service.understand(project_id, dependency_run_id)
    first_key = cache.get.call_args.args[0]
    source_file.write_text("def hello():\n    return 'changed'\n", encoding="utf-8")
    service.understand(project_id, dependency_run_id)
    second_key = cache.get.call_args.args[0]

    assert first_key != second_key


def test_failed_stage3_response_is_never_cached(tmp_path) -> None:
    service, cache, agent, _, _, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    cache.get.return_value = None
    agent.analyze.side_effect = RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        service.understand(project_id, dependency_run_id)

    cache.set.assert_not_called()


def test_completed_pipeline_is_reused_only_with_current_artifact_version(
    tmp_path, caplog
) -> None:
    service, cache, agent, repository, _, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    active = service._artifact_version_manifest(include_pipeline=False)
    completed = SimpleNamespace(
        id=uuid4(),
        status=CodeUnderstandingStatus.COMPLETED,
        result={"_artifact_version": active, "project_summary": "Current"},
    )
    repository.get_by_dependency_run_id.return_value = [completed]

    result = service.understand(project_id, dependency_run_id)

    assert result is completed
    agent.analyze.assert_not_called()
    assert "CACHE HIT artifact=pipeline" in caplog.text


def test_version_mismatch_invalidates_redis_and_regenerates(
    tmp_path, caplog
) -> None:
    service, cache, agent, repository, _, project_id, dependency_run_id = (
        _service_fixture(tmp_path)
    )
    stale = SimpleNamespace(
        id=uuid4(),
        status=CodeUnderstandingStatus.COMPLETED,
        result={
            "_artifact_version": {
                "semantic": "old", "generator": "old",
                "verification": "old", "composite": "old",
            },
            "project_summary": "Stale",
            "test_generation": {"generated_test_cases": []},
        },
    )
    repository.get_by_dependency_run_id.return_value = [stale]
    repository.prepare_artifact_regeneration.side_effect = lambda run: setattr(
        run, "result", None
    )
    cache.get.return_value = None

    service.understand(project_id, dependency_run_id)

    cache.clear_project.assert_called_once_with(str(project_id))
    repository.prepare_artifact_regeneration.assert_called_once_with(stale)
    agent.analyze.assert_called_once()
    assert "ARTIFACT VERSION MISMATCH" in caplog.text
    assert "CACHE INVALIDATED" in caplog.text
    assert "REGENERATING" in caplog.text


def test_generator_fingerprint_changes_composite_artifact_version(tmp_path) -> None:
    service, _, _, _, _, _, _ = _service_fixture(tmp_path)
    generator = MagicMock()
    service._test_generation_agent = generator
    generator.cache_fingerprint.return_value = {"unit_generator_version": "v1"}
    first = service._artifact_version_manifest(include_pipeline=True)
    generator.cache_fingerprint.return_value = {"unit_generator_version": "v2"}
    second = service._artifact_version_manifest(include_pipeline=True)

    assert first["generator"] != second["generator"]
    assert first["composite"] != second["composite"]


def test_failed_pipeline_does_not_publish_partial_artifacts(tmp_path) -> None:
    service, _, _, repository, _, project_id, _ = _service_fixture(tmp_path)
    repository.get_latest_by_project_id.return_value = SimpleNamespace(
        id=uuid4(),
        status=CodeUnderstandingStatus.FAILED,
        result={
            "test_generation": {"generated_test_cases": ["partial"]},
            "test_verification": {"results": ["partial"]},
        },
    )

    state = service.get_latest_pipeline_state(project_id)

    assert state["artifacts_publishable"] is False
    assert state["test_generation"] is None
    assert state["test_verification"] is None
    assert state["quality_optimization"] is None
    assert state["runtime_execution_plan"] is None


def test_secondary_failure_while_marking_failed_does_not_mask_original(
    tmp_path, caplog
) -> None:
    service, _, _, repository, _, _, _ = _service_fixture(tmp_path)
    repository.fail.side_effect = RuntimeError("database still unavailable")

    service._safe_fail_run(
        SimpleNamespace(id=uuid4()),
        RuntimeError("original pipeline failure"),
        failed_stage="stage_5",
    )

    assert "Failed to persist pipeline failure locally" in caplog.text
