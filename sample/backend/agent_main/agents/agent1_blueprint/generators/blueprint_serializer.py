"""Blueprint Serializer — persists all Agent-1 artifacts to the outputs/ folder."""

import json
import os
from typing import Any, Dict

from app.utils.logger import get_logger

logger = get_logger(__name__)


class BlueprintSerializer:
    """Write Agent-1 JSON artifacts to the outputs directory."""

    def write_json_artifacts(
        self,
        output_dir: str,
        project_manifest: Dict[str, Any],
        master_blueprint: Dict[str, Any],
        implementation_plan: Dict[str, Any],
    ) -> Dict[str, str]:
        """Persist the three core artifacts to disk.

        Args:
            output_dir:          Target directory (created if it does not exist).
            project_manifest:    ProjectManifest payload.
            master_blueprint:    MasterBlueprint payload.
            implementation_plan: ImplementationPlan payload.

        Returns:
            Dict mapping artifact names to their absolute file paths.
        """
        os.makedirs(output_dir, exist_ok=True)

        paths = {
            "project_manifest":    os.path.join(output_dir, "ProjectManifest.json"),
            "master_blueprint":    os.path.join(output_dir, "MasterBlueprint.json"),
            "implementation_plan": os.path.join(output_dir, "ImplementationPlan.json"),
        }

        payloads = {
            "project_manifest":    project_manifest,
            "master_blueprint":    master_blueprint,
            "implementation_plan": implementation_plan,
        }

        for key, path in paths.items():
            self._write_json(path, payloads[key])
            logger.info("BlueprintSerializer: wrote %s", path)

        return paths

    def write_additional_artifacts(
        self, output_dir: str, artifacts: Dict[str, tuple[str, Any]]
    ) -> Dict[str, str]:
        """Persist additional JSON or text artifacts produced by Agent-1."""
        os.makedirs(output_dir, exist_ok=True)
        paths: Dict[str, str] = {}
        for key, (filename, payload) in artifacts.items():
            path = os.path.join(output_dir, filename)
            if filename.endswith(".json"):
                self._write_json(path, payload)
            else:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(str(payload))
            paths[key] = path
            logger.info("BlueprintSerializer: wrote %s", path)
        return paths

    @staticmethod
    def _write_json(path: str, payload: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
