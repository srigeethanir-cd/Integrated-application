"""
React Parser – Python wrapper that delegates to the Node.js Babel parser.

All Node.js interaction is **completely isolated** inside this class.  The
rest of the Python backend only sees ``BaseParser.parse()`` returning a dict.
If the underlying parsing mechanism changes (e.g. switch to a Python-based
parser or a gRPC call), only this file needs to be updated.
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
_REACT_SCRIPT = _PARSERS_DIR / "react_parser.js"


class ReactParser(BaseParser):
    """Parses React / Next.js projects using ``@babel/parser`` + ``@babel/traverse``."""

    @property
    def framework_name(self) -> str:
        return "React"

    def parse(self, project_path: Path) -> Dict[str, Any]:
        """Run the Node.js React parser against *project_path*.

        Args:
            project_path: Absolute path to the project source directory.

        Returns:
            A dict matching the ``ReactAnalysisResult`` Pydantic schema.

        Raises:
            RuntimeError: If Node.js is unavailable, the script is missing,
                or the parser exits with a non-zero status.
        """
        logger.info("ReactParser: starting parse for %s", project_path)
        raw_json = self._run_node_script(project_path)

        try:
            result = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("ReactParser: invalid JSON from Node.js script: %s", exc)
            raise RuntimeError(
                f"React parser produced invalid JSON: {exc}"
            ) from exc

        logger.info(
            "ReactParser: completed – %d component(s) found",
            len(result.get("components", [])),
        )
        return result

    # ------------------------------------------------------------------
    # Private – Node.js invocation (isolated)
    # ------------------------------------------------------------------

    def _run_node_script(self, project_path: Path) -> str:
        """Execute the Node.js React parser script and return its stdout.

        Args:
            project_path: Project root to pass to the script.

        Returns:
            Raw JSON string from stdout.

        Raises:
            RuntimeError: On any failure (missing runtime, non-zero exit).
        """
        if not _REACT_SCRIPT.is_file():
            raise RuntimeError(
                f"React parser script not found: {_REACT_SCRIPT}. "
                "Ensure the Node.js parsers are set up."
            )

        cmd = ["node", str(_REACT_SCRIPT), str(project_path)]
        logger.debug("ReactParser: running %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(_PARSERS_DIR),
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js runtime not found. Please install Node.js "
                "(https://nodejs.org/) and ensure 'node' is on PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "React parser timed out after 120 seconds. "
                "The project may be too large or the parser is stuck."
            )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "(no stderr output)"
            logger.error("ReactParser: Node.js script failed:\n%s", stderr)
            raise RuntimeError(f"React parser failed: {stderr}")

        return result.stdout
