import os
import uuid
from pathlib import Path

import pytest

from app.services.ingestion.storage_service import StorageService


def test_create_project_directory(tmp_path: Path) -> None:
    service = StorageService(tmp_path)
    project_id = uuid.uuid4()

    directory = service.create_project_directory(project_id)

    assert directory == tmp_path.resolve() / str(project_id)
    assert directory.is_dir()


def test_delete_project_directory(tmp_path: Path) -> None:
    service = StorageService(tmp_path)
    project_id = uuid.uuid4()
    directory = service.create_project_directory(project_id)
    (directory / "file.py").write_text("content", encoding="utf-8")

    assert service.delete_project_directory(project_id) is True
    assert not directory.exists()


def test_stage_project_directory(tmp_path: Path) -> None:
    service = StorageService(tmp_path)
    project_id = uuid.uuid4()
    directory = service.create_project_directory(project_id)

    staged = service.stage_project_directory_for_deletion(project_id)

    assert staged == tmp_path.resolve() / f".deleting-{project_id}"
    assert staged is not None and staged.is_dir()
    assert not directory.exists()


def test_restore_staged_project_directory(tmp_path: Path) -> None:
    service = StorageService(tmp_path)
    project_id = uuid.uuid4()
    directory = service.create_project_directory(project_id)
    staged = service.stage_project_directory_for_deletion(project_id)
    assert staged is not None

    service.restore_staged_project_directory(project_id, staged)

    assert directory.is_dir()
    assert not staged.exists()


def test_rejects_path_outside_storage_root(tmp_path: Path) -> None:
    service = StorageService(tmp_path / "storage")

    with pytest.raises(ValueError, match="outside the storage root"):
        service._validated_storage_directory(tmp_path / "outside")


def test_rejects_symbolic_link_project_directory(tmp_path: Path) -> None:
    service = StorageService(tmp_path / "storage")
    project_id = uuid.uuid4()
    outside = tmp_path / "outside"
    outside.mkdir()
    project_link = service.storage_root / str(project_id)

    try:
        os.symlink(outside, project_link, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symbolic links are unavailable: {error}")

    with pytest.raises(ValueError, match="symbolic link"):
        service.get_project_directory(project_id)


def test_stores_and_resolves_relative_project_paths(tmp_path: Path) -> None:
    service = StorageService(tmp_path / "storage")
    project_id = uuid.uuid4()
    project_directory = service.create_project_directory(project_id)

    stored_path = service.to_relative_path(project_directory)

    assert stored_path == str(project_id)
    assert service.resolve_project_directory(project_id, stored_path) == (
        project_directory
    )


def test_resolves_legacy_absolute_path_after_storage_relocation(
    tmp_path: Path,
) -> None:
    service = StorageService(tmp_path / "new-storage")
    project_id = uuid.uuid4()
    project_directory = service.create_project_directory(project_id)
    source_directory = project_directory / "source"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text("pass\n", encoding="utf-8")
    legacy_path = f"D:\\old-app\\storage\\projects\\{project_id}\\source\\main.py"

    resolved = service.resolve_project_path(project_id, legacy_path)

    assert resolved == source_file


def test_rejects_relative_path_that_escapes_project(tmp_path: Path) -> None:
    service = StorageService(tmp_path / "storage")
    project_id = uuid.uuid4()
    service.create_project_directory(project_id)

    with pytest.raises(ValueError, match="escapes"):
        service.resolve_project_path(
            project_id,
            f"{project_id}/../another-project/source.py",
        )
