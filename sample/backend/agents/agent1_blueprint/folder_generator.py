"""Folder Generator module for Agent 1.

Scaffolds production project folder structure under outputs/ or specified target directories.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FolderGenerator:
    """Scaffolds output target project folders."""

    DEFAULT_FOLDERS = [
        "backend/app/api/v1",
        "backend/app/core",
        "backend/app/database",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/repository",
        "backend/app/utils",
        "backend/alembic/versions",
        "backend/tests",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/routes",
        "frontend/src/layouts",
        "docs",
    ]

    def scaffold_folders(self, target_root: str) -> List[str]:
        """Scaffold directories under target_root path."""
        root = Path(target_root)
        created = []
        for f in self.DEFAULT_FOLDERS:
            folder_path = root / f
            folder_path.mkdir(parents=True, exist_ok=True)
            created.append(str(folder_path))
        logger.info("FolderGenerator: Scaffolded %d project directories under %s", len(created), target_root)
        return created
