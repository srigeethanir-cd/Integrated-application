"""Shared Core Promoter for Agent 3.

Promotes approved shared modules from workspace/core/ to integrated_project/core/.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PromotedModuleSpec(BaseModel):
    """Specification of a promoted shared core module."""

    source_path: str = Field(description="Relative path inside workspace/core/")
    target_path: str = Field(description="Relative path inside integrated_project/core/")
    category: str = Field(description="Category: auth | middleware | utils | models | hooks | client")
    status: str = Field(default="PROMOTED", description="Status: PROMOTED | SKIPPED")


class SharedPromoter:
    """Promotes approved shared core modules from workspace/core/ to integrated_project/core/."""

    def promote_shared_modules(
        self,
        workspace_root: str,
        integrated_project_root: str,
    ) -> List[PromotedModuleSpec]:
        """Inspect workspace/core/ and promote approved shared modules to integrated_project/core/."""
        promoted: List[PromotedModuleSpec] = []
        ws_core = Path(workspace_root) / "core"
        proj_core = Path(integrated_project_root) / "core"
        proj_core.mkdir(parents=True, exist_ok=True)

        if not ws_core.exists():
            logger.info("SharedPromoter: No workspace/core/ directory found to promote.")
            return promoted

        for root, _, files in os.walk(ws_core):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js")):
                    abs_source = Path(root) / file
                    rel_path = os.path.relpath(abs_source, ws_core)
                    abs_target = proj_core / rel_path

                    abs_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(abs_source, abs_target)

                    category = "utils"
                    if "auth" in rel_path.lower():
                        category = "auth"
                    elif "middleware" in rel_path.lower():
                        category = "middleware"
                    elif "model" in rel_path.lower():
                        category = "models"

                    promoted.append(
                        PromotedModuleSpec(
                            source_path=rel_path,
                            target_path=str(Path("core") / rel_path),
                            category=category,
                            status="PROMOTED",
                        )
                    )
                    logger.info("SharedPromoter: Promoted shared module workspace/core/%s -> integrated_project/core/%s", rel_path, rel_path)

        return promoted
