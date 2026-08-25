"""
Angular Parser – Python wrapper that delegates to the Node.js TypeScript /
Angular Compiler parser.

All Node.js interaction is **completely isolated** inside this class.  The
rest of the Python backend only sees ``BaseParser.parse()`` returning a dict.
If the underlying parsing mechanism changes, only this file needs to change.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from app.services.project_analyzer.base_parser import BaseParser

logger = logging.getLogger(__name__)

# Resolve the Node.js script path relative to *this* file.
_PARSERS_DIR = Path(__file__).resolve().parent / "parsers"
_ANGULAR_SCRIPT = _PARSERS_DIR / "angular_parser.js"


class AngularParser(BaseParser):
    """Parses Angular projects using the TypeScript Compiler API +
    ``@angular/compiler`` for HTML template analysis."""

    @property
    def framework_name(self) -> str:
        return "Angular"

    def parse(self, project_path: Path) -> Dict[str, Any]:
        """Run the Node.js Angular parser against *project_path*.

        Args:
            project_path: Absolute path to the project source directory.

        Returns:
            A dict matching the ``AngularAnalysisResult`` Pydantic schema.

        Raises:
            RuntimeError: If Node.js is unavailable, the script is missing,
                or the parser exits with a non-zero status.
        """
        logger.info("AngularParser: starting parse for %s", project_path)
        raw_json = self._run_node_script(project_path)

        try:
            result = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("AngularParser: invalid JSON from Node.js script: %s", exc)
            raise RuntimeError(
                f"Angular parser produced invalid JSON: {exc}"
            ) from exc

        logger.info(
            "AngularParser: completed – %d component(s), %d service(s) found",
            len(result.get("components", [])),
            len(result.get("services", [])),
        )
        return result

    # ------------------------------------------------------------------
    # Private – Node.js invocation (isolated)
    # ------------------------------------------------------------------

    def _run_node_script(self, project_path: Path) -> str:
        """Execute the Node.js Angular parser script and return its stdout.

        Args:
            project_path: Project root to pass to the script.

        Returns:
            Raw JSON string from stdout.

        Raises:
            RuntimeError: On any failure (missing runtime, non-zero exit).
        """
        if not _ANGULAR_SCRIPT.is_file():
            raise RuntimeError(
                f"Angular parser script not found: {_ANGULAR_SCRIPT}. "
                "Ensure the Node.js parsers are set up."
            )

        cmd = ["node", str(_ANGULAR_SCRIPT), str(project_path)]
        logger.debug("AngularParser: running %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(_PARSERS_DIR),
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js runtime not found. Please install Node.js "
                "(https://nodejs.org/) and ensure 'node' is on PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Angular parser timed out after 180 seconds. "
                "The project may be too large or the parser is stuck."
            )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "(no stderr output)"
            logger.error("AngularParser: Node.js script failed:\n%s", stderr)
            raise RuntimeError(f"Angular parser failed: {stderr}")

        return result.stdout
