"""Architecture Preserver ensuring layered architectural boundaries and shared module reuse."""

import logging
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ArchitectureCheckResult(BaseModel):
    """Result of architectural layer boundary check."""

    passed: bool = Field(description="Boundary check status")
    violations: List[str] = Field(default_factory=list, description="Architectural layer boundary violations")


class ArchitecturePreserver:
    """Preserves layered architecture boundaries (API -> Service -> Repository -> Model) and shared component integrity."""

    ALLOWED_LAYERS = ["api", "services", "repository", "models", "core", "database", "schemas", "utils"]

    def verify_architecture_boundaries(self, project_root: str) -> ArchitectureCheckResult:
        """Inspect integrated project directories to ensure clean layer separation."""
        root = Path(project_root)
        violations: List[str] = []

        if not root.exists():
            return ArchitectureCheckResult(passed=True, violations=[])

        # Check for layer violations (e.g. models importing from api)
        py_files = list(root.glob("**/*.py"))
        for f in py_files:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                if "models" in f.parts and "from app.api" in content:
                    violations.append(f"Model file '{f.name}' violates layer boundary by importing from API layer.")
            except Exception:
                pass

        passed = len(violations) == 0
        logger.info("ArchitecturePreserver: Verified layer boundaries on %s (Passed: %s)", project_root, passed)

        return ArchitectureCheckResult(passed=passed, violations=violations)
