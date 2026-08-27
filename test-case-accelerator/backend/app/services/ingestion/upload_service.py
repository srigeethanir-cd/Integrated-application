import shutil
import stat
import uuid
import zipfile
import time
from io import SEEK_END, SEEK_SET
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.database.models.project import Project, ProjectSourceType, ProjectStatus
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.storage_service import StorageService


class ZipUploadLimitError(zipfile.BadZipFile):
    """Base exception for ZIP uploads that exceed configured safety limits."""


class UploadSizeLimitError(ZipUploadLimitError):
    """Raised when the uploaded archive is too large."""


class ZipEntryCountLimitError(ZipUploadLimitError):
    """Raised when an archive contains too many entries."""


class ZipTotalSizeLimitError(ZipUploadLimitError):
    """Raised when an archive's total uncompressed size is too large."""


class ZipFileSizeLimitError(ZipUploadLimitError):
    """Raised when an individual archived file is too large."""


class ZipCompressionRatioLimitError(ZipUploadLimitError):
    """Raised when an archived file has an unsafe compression ratio."""


class UploadService:
    """Coordinates persistence and extraction of uploaded ZIP projects."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        storage_service: StorageService,
    ) -> None:
        self._project_repository = project_repository
        self._storage_service = storage_service

    def upload_project(
        self,
        uploaded_file: UploadFile,
        name: str,
        description: str | None = None,
    ) -> Project:
        started_at = time.perf_counter()
        uploaded_file.file.seek(0, SEEK_END)
        archive_size = uploaded_file.file.tell()
        uploaded_file.file.seek(0, SEEK_SET)
        self._validate_upload_size(uploaded_file)
        self._validate_zip(uploaded_file)

        project_id = uuid.uuid4()
        project_directory = self._storage_service.create_project_directory(project_id)

        try:
            archive_path = project_directory / "archive.zip"
            source_directory = project_directory / "source"

            self._persist_archive(uploaded_file, archive_path)
            self._extract_archive(archive_path, source_directory)

            from app.services.ingestion.ingestion_metadata import collect_ingestion_metadata
            collect_ingestion_metadata(
                project_id=project_id,
                project_directory=project_directory,
                source_directory=source_directory,
                source_type="ZIP",
                started_at=started_at,
                archive_name=uploaded_file.filename,
                archive_size=archive_size,
            )

            project = Project(
                id=project_id,
                name=name,
                description=description,
                source_type=ProjectSourceType.ZIP,
                github_url=None,
                storage_path=self._storage_service.to_relative_path(
                    project_directory
                ),
                status=ProjectStatus.UPLOADED,
            )
            return self._project_repository.create(project)
        except Exception as error:
            self._cleanup_project_directory(project_id, error)
            raise

    @staticmethod
    def _validate_upload_size(uploaded_file: UploadFile) -> None:
        uploaded_file.file.seek(0, SEEK_END)
        upload_size = uploaded_file.file.tell()
        uploaded_file.file.seek(0, SEEK_SET)

        if upload_size > settings.max_upload_size_bytes:
            raise UploadSizeLimitError(
                "Uploaded archive size "
                f"({upload_size} bytes) exceeds the configured limit "
                f"({settings.max_upload_size_bytes} bytes)"
            )

    @staticmethod
    def _validate_zip(uploaded_file: UploadFile) -> None:
        uploaded_file.file.seek(0)
        is_zip_archive = zipfile.is_zipfile(uploaded_file.file)
        uploaded_file.file.seek(0)

        if not is_zip_archive:
            raise zipfile.BadZipFile("Uploaded file is not a valid ZIP archive")

    @staticmethod
    def _persist_archive(uploaded_file: UploadFile, archive_path: Path) -> None:
        uploaded_file.file.seek(0)
        with archive_path.open("wb") as destination:
            shutil.copyfileobj(uploaded_file.file, destination)

    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        destination.mkdir(parents=False, exist_ok=False)

        with zipfile.ZipFile(archive_path) as archive:
            self._validate_archive_members(archive, destination)
            archive.extractall(destination)

    @staticmethod
    def _validate_archive_members(
        archive: zipfile.ZipFile,
        destination: Path,
    ) -> None:
        resolved_destination = destination.resolve()
        members = archive.infolist()

        if len(members) > settings.max_zip_entries:
            raise ZipEntryCountLimitError(
                f"Archive entry count ({len(members)}) exceeds the configured limit "
                f"({settings.max_zip_entries})"
            )

        total_uncompressed_size = 0

        for member in members:
            total_uncompressed_size += member.file_size
            if (
                total_uncompressed_size
                > settings.max_zip_total_uncompressed_size_bytes
            ):
                raise ZipTotalSizeLimitError(
                    "Archive total uncompressed size "
                    f"({total_uncompressed_size} bytes) exceeds the configured limit "
                    f"({settings.max_zip_total_uncompressed_size_bytes} bytes)"
                )

            if member.file_size > settings.max_zip_file_uncompressed_size_bytes:
                raise ZipFileSizeLimitError(
                    f"Archive member {member.filename!r} uncompressed size "
                    f"({member.file_size} bytes) exceeds the configured limit "
                    f"({settings.max_zip_file_uncompressed_size_bytes} bytes)"
                )

            if member.file_size > 0:
                if member.compress_size == 0:
                    raise ZipCompressionRatioLimitError(
                        f"Archive member {member.filename!r} has an invalid "
                        "compression ratio"
                    )

                compression_ratio = member.file_size / member.compress_size
                if compression_ratio > settings.max_zip_compression_ratio:
                    raise ZipCompressionRatioLimitError(
                        f"Archive member {member.filename!r} compression ratio "
                        f"({compression_ratio:.2f}) exceeds the configured limit "
                        f"({settings.max_zip_compression_ratio:.2f})"
                    )

            normalized_name = member.filename.replace("\\", "/")
            member_path = Path(normalized_name)
            resolved_member = (resolved_destination / member_path).resolve()

            if member_path.is_absolute() or not resolved_member.is_relative_to(
                resolved_destination
            ):
                raise zipfile.BadZipFile(
                    f"Archive member escapes the project directory: {member.filename}"
                )

            unix_mode = member.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise zipfile.BadZipFile(
                    f"Archive contains a symbolic link: {member.filename}"
                )

    def _cleanup_project_directory(
        self,
        project_id: uuid.UUID,
        original_error: Exception,
    ) -> None:
        try:
            self._storage_service.delete_project_directory(project_id)
        except Exception as cleanup_error:
            original_error.add_note(f"Project storage cleanup failed: {cleanup_error}")
