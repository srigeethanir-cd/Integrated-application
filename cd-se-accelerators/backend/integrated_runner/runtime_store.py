"""Runtime State persistence for integrated application runner."""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

RUNTIME_FILE_NAME = "runtime.json"

def get_runtime_file_path(project_root: str) -> str:
    return os.path.join(project_root, RUNTIME_FILE_NAME)

def save_runtime_info(project_root: str, data: Dict[str, Any]) -> str:
    os.makedirs(project_root, exist_ok=True)
    file_path = get_runtime_file_path(project_root)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save runtime.json to {file_path}: {e}")
    return file_path

def load_runtime_info(project_root: str) -> Optional[Dict[str, Any]]:
    file_path = get_runtime_file_path(project_root)
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load runtime.json from {file_path}: {e}")
        return None
