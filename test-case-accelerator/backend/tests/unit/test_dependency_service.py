import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.database.models.project import ProjectStatus
from app.schemas.file_metadata import FileMetadata
from app.services.dependency.dependency_service import (
    DependencyService,
    NoSupportedSourceFilesError,
)
from app.services.ingestion.storage_service import StorageService


def test_run_uses_stage_one_managed_source_directory(tmp_path: Path) -> None:
    project_id = uuid.uuid4()
    storage = StorageService(tmp_path)
    project_directory = storage.create_project_directory(project_id)
    source_directory = project_directory / "source"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text("def main():\n    pass\n", encoding="utf-8")

    project = Mock(id=project_id, storage_path=str(project_directory))
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    dependency_repository = Mock()
    run = Mock()
    dependency_repository.create_run.return_value = run

    service = DependencyService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        storage_service=storage,
        traverser=Mock(scan=Mock(return_value=[source_file])),
        import_resolver=Mock(resolve=Mock(return_value=[])),
        graph_builder=Mock(),
        backend_filter=Mock(filter=Mock(return_value=[source_file])),
        metadata_service=Mock(
            generate=Mock(
                return_value=[
                    FileMetadata(path=str(source_file), language="python")
                ]
            )
        ),
    )

    assert service.run(project_id) is run
    dependency_repository.create_run.assert_called_once_with(
        project_id=project_id,
        project_path=f"{project_id}/source",
    )
    persisted_metadata = dependency_repository.complete.call_args.args[1]
    assert persisted_metadata[0].path == f"{project_id}/source/main.py"
    assert project_repository.update_status.call_args_list[-1].args == (
        project_id,
        ProjectStatus.READY,
    )


def test_run_rejects_storage_path_outside_managed_project(tmp_path: Path) -> None:
    project_id = uuid.uuid4()
    storage = StorageService(tmp_path / "managed")
    project_repository = Mock()
    project_repository.get_by_id.return_value = Mock(
        id=project_id,
        storage_path=str(tmp_path / "unmanaged"),
    )
    service = DependencyService(
        project_repository=project_repository,
        dependency_repository=Mock(),
        storage_service=storage,
        traverser=Mock(),
        import_resolver=Mock(),
        graph_builder=Mock(),
        backend_filter=Mock(),
        metadata_service=Mock(),
    )

    with pytest.raises(ValueError, match="requested project"):
        service.run(project_id)


def test_run_is_failed_when_processing_status_update_fails(tmp_path: Path) -> None:
    project_id = uuid.uuid4()
    storage = StorageService(tmp_path)
    project_directory = storage.create_project_directory(project_id)
    (project_directory / "source").mkdir()
    project_repository = Mock()
    project_repository.get_by_id.return_value = Mock(
        id=project_id,
        storage_path=str(project_directory),
    )
    project_repository.update_status.side_effect = [RuntimeError("database error"), None]
    dependency_repository = Mock()
    run = Mock()
    dependency_repository.create_run.return_value = run
    service = DependencyService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        storage_service=storage,
        traverser=Mock(),
        import_resolver=Mock(),
        graph_builder=Mock(),
        backend_filter=Mock(),
        metadata_service=Mock(),
    )

    with pytest.raises(RuntimeError, match="database error"):
        service.run(project_id)

    dependency_repository.fail.assert_called_once_with(run)
    assert project_repository.update_status.call_args_list[-1].args == (
        project_id,
        ProjectStatus.FAILED,
    )


def test_run_fails_when_no_supported_source_files_are_found(
    tmp_path: Path,
) -> None:
    project_id = uuid.uuid4()
    storage = StorageService(tmp_path)
    project_directory = storage.create_project_directory(project_id)
    source_directory = project_directory / "source"
    source_directory.mkdir()
    readme = source_directory / "README"
    readme.write_text("Hello World!\n", encoding="utf-8")

    project_repository = Mock()
    project_repository.get_by_id.return_value = Mock(
        id=project_id,
        storage_path=str(project_directory),
    )
    dependency_repository = Mock()
    run = Mock()
    dependency_repository.create_run.return_value = run
    metadata_service = Mock()
    service = DependencyService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        storage_service=storage,
        traverser=Mock(scan=Mock(return_value=[readme])),
        import_resolver=Mock(),
        graph_builder=Mock(),
        backend_filter=Mock(filter=Mock(return_value=[])),
        metadata_service=metadata_service,
    )

    with pytest.raises(
        NoSupportedSourceFilesError,
        match="No supported source files",
    ):
        service.run(project_id)

    metadata_service.generate.assert_not_called()
    dependency_repository.complete.assert_not_called()
    dependency_repository.fail.assert_called_once_with(run)
    assert project_repository.update_status.call_args_list[-1].args == (
        project_id,
        ProjectStatus.FAILED,
    )
