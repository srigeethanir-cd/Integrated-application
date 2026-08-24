"""Shared Core Manager for Agent 2.

Manages shared dependencies under workspace/core/ (auth, middleware, utilities, common models, hooks, API clients), ensuring module reuse without duplication.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SharedModule(BaseModel):
    """Specification of a shared core module under workspace/core/."""

    module_id: str = Field(description="Module ID (e.g. CORE_AUTH)")
    category: str = Field(description="Category: auth | middleware | utils | models | hooks | client")
    relative_path: str = Field(description="Path relative to workspace/core/")
    description: str = Field(description="Module capability")


class SharedCoreManager:
    """Manages workspace/core/ shared modules, preventing duplicated code across stories."""

    def __init__(self, workspace_root: str = "./workspace"):
        self.workspace_root = Path(workspace_root)
        self.core_dir = self.workspace_root / "core"
        self.core_dir.mkdir(parents=True, exist_ok=True)

    def list_existing_shared_modules(self) -> List[SharedModule]:
        """Inspect workspace/core/ and return existing shared modules."""
        modules = []

        if not self.core_dir.exists():
            return modules

        for root, _, files in os.walk(self.core_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js")):
                    rel_path = os.path.relpath(os.path.join(root, file), self.core_dir)
                    category = "utils"
                    if "auth" in rel_path.lower():
                        category = "auth"
                    elif "middleware" in rel_path.lower():
                        category = "middleware"
                    elif "model" in rel_path.lower():
                        category = "models"
                    elif "hook" in rel_path.lower():
                        category = "hooks"

                    modules.append(
                        SharedModule(
                            module_id=f"CORE_{file.upper().replace('.', '_')}",
                            category=category,
                            relative_path=rel_path,
                            description=f"Shared {category} module ({file})",
                        )
                    )

        return modules

    def ensure_shared_module(
        self,
        category: str,
        filename: str,
        content: str,
    ) -> str:
        """Reuse existing shared module if present, or write new shared module under workspace/core/."""
        cat_dir = self.core_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        target_file = cat_dir / filename
        if target_file.exists():
            logger.info("SharedCoreManager: Reusing existing shared module at %s", target_file)
            return str(target_file)

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("SharedCoreManager: Created new shared module under workspace/core/%s/%s", category, filename)
        return str(target_file)
