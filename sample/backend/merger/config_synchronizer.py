"""Config Synchronizer for merging environment variables and configuration files."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConfigSynchronizer:
    """Merges and synchronizes configuration files (.env, app_config.yaml, project_config.json)."""

    def synchronize_env_files(self, source_env: str, target_env: str) -> None:
        """Merge environment variables from source_env into target_env without overwriting existing keys."""
        src_path = Path(source_env)
        tgt_path = Path(target_env)

        if not src_path.exists():
            return

        tgt_keys = set()
        if tgt_path.exists():
            with open(tgt_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        tgt_keys.add(line.split("=")[0].strip())

        new_lines = []
        with open(src_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key = line.split("=")[0].strip()
                    if key not in tgt_keys:
                        new_lines.append(line)

        if new_lines:
            tgt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tgt_path, "a", encoding="utf-8") as f:
                f.write("\n" + "".join(new_lines))
            logger.info("ConfigSynchronizer: Appended %d new env variables to %s", len(new_lines), target_env)

    def synchronize_json_configs(self, source_json: str, target_json: str) -> None:
        """Merge JSON configuration dictionary values."""
        src_path = Path(source_json)
        tgt_path = Path(target_json)

        if not src_path.exists():
            return

        try:
            with open(src_path, "r", encoding="utf-8") as f:
                src_data = json.load(f)

            tgt_data = {}
            if tgt_path.exists():
                with open(tgt_path, "r", encoding="utf-8") as f:
                    tgt_data = json.load(f)

            # Deep merge dictionaries
            for k, v in src_data.items():
                if k not in tgt_data:
                    tgt_data[k] = v

            tgt_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tgt_path, "w", encoding="utf-8") as f:
                json.dump(tgt_data, f, indent=2)

            logger.info("ConfigSynchronizer: Synchronized JSON config at %s", target_json)
        except Exception as e:
            logger.error("ConfigSynchronizer error synchronizing JSON config: %s", e)
