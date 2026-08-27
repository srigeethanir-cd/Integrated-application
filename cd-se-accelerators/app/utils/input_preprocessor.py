"""
Input Preprocessor utility.

Provides a unified context manager ``get_project_workspace`` that transparently
handles both local project directories and ZIP archives.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.utils.project_locator import locate_project_root
from app.utils.temp_workspace import TempWorkspace
from app.utils.zip_handler import ZipHandler

logger = logging.getLogger(__name__)


@contextmanager
def get_project_workspace(project_path: str | Path) -> Generator[Path, None, None]:
    """Context manager that prepares and returns a project directory path.

    - If *project_path* is a directory: validates existence/content and yields it directly.
    - If *project_path* is a ZIP archive: extracts it into a temporary workspace,
      locates the project root, logs lifecycle info, yields the project root,
      and cleans up the temporary workspace upon exit.

    Args:
        project_path: String or Path to directory or ZIP archive.

    Yields:
        Path object pointing to the active project root directory.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If file format is unsupported, archive is corrupted, or empty.
    """
    raw_path = Path(project_path)
    logger.info("Processing project input path: %s", raw_path)

    if not raw_path.exists():
        logger.warning("Input path does not exist: %s", raw_path)
        raise FileNotFoundError(f"Project path does not exist: {project_path}")

    if raw_path.is_dir():
        input_type = "directory"
        logger.info("Input type: %s", input_type)

        # Check if empty directory
        if not any(raw_path.iterdir()):
            logger.warning("Directory is empty: %s", raw_path)
            raise ValueError("Project directory is empty.")

        logger.info("Detected project root: %s", raw_path)
        yield raw_path

    elif raw_path.is_file():
        if raw_path.suffix.lower() != ".zip":
            logger.warning("Unsupported file extension for path: %s", raw_path)
            raise ValueError(
                f"Unsupported file format. Expected directory or .zip archive, got: {raw_path.name}"
            )

        input_type = "zip"
        logger.info("Input type: %s", input_type)

        zip_handler = ZipHandler()

        with TempWorkspace() as workspace_dir:
            logger.info("Extraction directory: %s", workspace_dir)

            elapsed_ms = zip_handler.extract(raw_path, workspace_dir)
            logger.info("Elapsed extraction time: %.2f ms", elapsed_ms)

            detected_root = locate_project_root(workspace_dir)
            logger.info("Detected project root: %s", detected_root)

            yield detected_root

    else:
        raise ValueError(f"Invalid path type: {project_path}")
