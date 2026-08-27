import stat
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile

from app.core.config import settings
from app.database.models.project import ProjectSourceType, ProjectStatus
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.storage_service import StorageService
from app.services.ingestion.upload_service import (
    UploadService,
    UploadSizeLimitError,
    ZipCompressionRatioLimitError,
    ZipEntryCountLimitError,
    ZipFileSizeLimitError,
    ZipTotalSizeLimitError,
)


def _zip_upload(
    files: dict[str, bytes],
    compression: int = zipfile.ZIP_STORED,
) -> UploadFile:
    content = BytesIO()
    with zipfile.ZipFile(content, "w", compression=compression) as archive:
        for filename, data in files.items():
            archive.writestr(filename, data)
    content.seek(0)
    return UploadFile(filename="project.zip", file=content)


def _service(tmp_path: Path) -> tuple[UploadService, MagicMock, StorageService]:
    repository = MagicMock(spec=ProjectRepository)
    repository.create.side_effect = lambda project: project
    storage = StorageService(tmp_path)
    return UploadService(repository, storage), repository, storage


def test_valid_zip_upload(tmp_path: Path) -> None:
    service, repository, storage = _service(tmp_path)

    project = service.upload_project(_zip_upload({"main.py": b"print('ok')"}), "demo")

    assert project.source_type is ProjectSourceType.ZIP
    assert project.status is ProjectStatus.UPLOADED
    assert project.storage_path == str(project.id)
    project_directory = storage.resolve_project_directory(
        project.id,
        project.storage_path,
    )
    assert (project_directory / "archive.zip").is_file()
    assert (project_directory / "source" / "main.py").is_file()
    repository.create.assert_called_once_with(project)


def test_invalid_zip_file(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)
    upload = UploadFile(filename="invalid.zip", file=BytesIO(b"not a zip"))

    with pytest.raises(zipfile.BadZipFile):
        service.upload_project(upload, "demo")


def test_upload_size_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, _ = _service(tmp_path)
    upload = _zip_upload({"file.txt": b"data"})
    monkeypatch.setattr(settings, "max_upload_size_bytes", 1)

    with pytest.raises(UploadSizeLimitError):
        service.upload_project(upload, "demo")


def test_zip_entry_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, _ = _service(tmp_path)
    monkeypatch.setattr(settings, "max_zip_entries", 1)

    with pytest.raises(ZipEntryCountLimitError):
        service.upload_project(_zip_upload({"a": b"a", "b": b"b"}), "demo")


def test_total_uncompressed_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, _ = _service(tmp_path)
    monkeypatch.setattr(settings, "max_zip_total_uncompressed_size_bytes", 3)

    with pytest.raises(ZipTotalSizeLimitError):
        service.upload_project(_zip_upload({"a": b"aa", "b": b"bb"}), "demo")


def test_individual_file_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, _ = _service(tmp_path)
    monkeypatch.setattr(settings, "max_zip_file_uncompressed_size_bytes", 3)

    with pytest.raises(ZipFileSizeLimitError):
        service.upload_project(_zip_upload({"large": b"data"}), "demo")


def test_compression_ratio_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, _ = _service(tmp_path)
    monkeypatch.setattr(settings, "max_zip_compression_ratio", 2.0)
    upload = _zip_upload({"compressed": b"0" * 10_000}, zipfile.ZIP_DEFLATED)

    with pytest.raises(ZipCompressionRatioLimitError):
        service.upload_project(upload, "demo")


def test_zip_slip_rejection(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)

    with pytest.raises(zipfile.BadZipFile, match="escapes"):
        service.upload_project(_zip_upload({"../outside.py": b"unsafe"}), "demo")

    assert not (tmp_path / "outside.py").exists()


def test_zip_symlink_rejection(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)
    content = BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "target")
    content.seek(0)

    with pytest.raises(zipfile.BadZipFile, match="symbolic link"):
        service.upload_project(
            UploadFile(filename="project.zip", file=content),
            "demo",
        )


def test_cleanup_on_repository_failure(tmp_path: Path) -> None:
    service, repository, storage = _service(tmp_path)
    repository.create.side_effect = RuntimeError("database failure")

    with pytest.raises(RuntimeError, match="database failure"):
        service.upload_project(_zip_upload({"file.py": b"content"}), "demo")

    created_project = repository.create.call_args.args[0]
    assert isinstance(created_project.id, uuid.UUID)
    assert not storage.project_directory_exists(created_project.id)
