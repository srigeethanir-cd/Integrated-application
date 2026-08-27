"""
Project Utils – Clean naming, deduplication, and project resolution helpers.
"""

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


def is_hex_string(s: str) -> bool:
    """Return True if string is a raw hexadecimal UUID or hash (e.g. '68F86E429F9407B8EBF7F800553F7C5')."""
    if not s:
        return False
    clean = str(s).replace("-", "").replace("_", "").strip()
    if len(clean) >= 20 and all(c in "0123456789abcdefABCDEF" for c in clean):
        return True
    if clean.lower().startswith("proj") and len(clean) >= 12:
        return True
    return False


def format_title(s: str) -> str:
    """Format string into clean human-readable Title Case."""
    if not s:
        return ""
    clean = str(s).replace("-", " ").replace("_", " ").strip()
    # Split camelCase / PascalCase into spaced words if needed
    split_camel = re.sub(r"([a-z])([A-Z])", r"\1 \2", clean)
    return split_camel.title()


def resolve_clean_project_name(
    project_path: str,
    workspace_path: Optional[str] = None,
    original_filename: Optional[str] = None,
    current_name: Optional[str] = None,
) -> str:
    """Derive a clean, human-readable project title.

    Guarantees that raw hex UUIDs or generic 'source' fallbacks are never returned.
    """
    candidates = []

    # Candidate 0: current_name if clean
    if current_name and not is_hex_string(current_name) and current_name.strip().lower() not in ("source", "source_ingestion", "app", "workspace", "runs", "project"):
        candidates.append(format_title(current_name))

    # Candidate 1: Original Filename
    if original_filename:
        clean_fn = original_filename
        if clean_fn.lower().endswith(".zip"):
            clean_fn = clean_fn[:-4]
        if clean_fn and not is_hex_string(clean_fn):
            candidates.append(format_title(clean_fn))

    paths_to_check = [p for p in [project_path, workspace_path] if p]

    for p_path in paths_to_check:
        if not p_path or not os.path.exists(p_path):
            continue

        # Candidate 2: package.json name field
        pkg_file = os.path.join(p_path, "package.json")
        if os.path.exists(pkg_file):
            try:
                with open(pkg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    name_val = data.get("name")
                    if name_val and not is_hex_string(name_val):
                        candidates.append(format_title(str(name_val)))
            except Exception:
                pass

        # Candidate 3: angular.json project key
        ang_file = os.path.join(p_path, "angular.json")
        if os.path.exists(ang_file):
            try:
                with open(ang_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    projects_dict = data.get("projects", {})
                    if projects_dict:
                        proj_keys = [k for k in projects_dict.keys() if not is_hex_string(k)]
                        if proj_keys:
                            candidates.append(format_title(proj_keys[0]))
            except Exception:
                pass

        # Candidate 4: project_meta.json original filename
        meta_file = os.path.join(p_path, "project_meta.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    fn = meta.get("original_filename")
                    if fn:
                        if fn.lower().endswith(".zip"):
                            fn = fn[:-4]
                        if not is_hex_string(fn):
                            candidates.append(format_title(fn))
            except Exception:
                pass

        # Candidate 5: Directory name if not generic or hex
        b_name = os.path.basename(p_path.rstrip("/\\"))
        if b_name.lower().endswith(".zip"):
            b_name = b_name[:-4]
        if b_name and not is_hex_string(b_name) and b_name.lower() not in ("source", "source_ingestion", "app", "workspace", "runs"):
            candidates.append(format_title(b_name))

    valid_candidates = [
        c for c in candidates
        if c and not is_hex_string(c) and c.strip().lower() not in ("source", "source_ingestion", "project", "app")
    ]

    if valid_candidates:
        return valid_candidates[0]

    return "Frontend Application"
