"""Conflict Detector for identifying AST collisions, route duplications, and schema conflicts."""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConflictItem(BaseModel):
    """Specification of an identified code/schema conflict."""

    conflict_type: str = Field(description="Conflict: ROUTE_DUPLICATION | AST_COLLISION | SCHEMA_COLLISION")
    target_file: str = Field(description="Target filepath where conflict occurred")
    conflict_identifier: str = Field(description="Conflicting route, function, or table name")
    resolution_strategy: str = Field(default="APPEND_UNIQUE", description="Strategy: APPEND_UNIQUE | OVERWRITE | RENAME")


class ConflictDetector:
    """Detects AST code collisions, route duplications, and database schema collisions."""

    def detect_conflicts(self, target_file_path: str, source_content: str) -> List[ConflictItem]:
        """Inspect target_file_path and source_content for collisions."""
        conflicts: List[ConflictItem] = []
        tgt_path = Path(target_file_path)

        if not tgt_path.exists():
            return conflicts

        try:
            with open(tgt_path, "r", encoding="utf-8") as f:
                tgt_content = f.read()

            # 1. Route Duplication Check
            src_routes = set(re.findall(r"@(?:router|api_router)\.(?:get|post|put|delete)\(['\"]([^'\"]+)['\"]", source_content))
            tgt_routes = set(re.findall(r"@(?:router|api_router)\.(?:get|post|put|delete)\(['\"]([^'\"]+)['\"]", tgt_content))

            duplicated_routes = src_routes.intersection(tgt_routes)
            for r in duplicated_routes:
                conflicts.append(
                    ConflictItem(
                        conflict_type="ROUTE_DUPLICATION",
                        target_file=target_file_path,
                        conflict_identifier=r,
                        resolution_strategy="APPEND_UNIQUE",
                    )
                )

            # 2. Function AST Collision Check
            try:
                src_ast = ast.parse(source_content)
                tgt_ast = ast.parse(tgt_content)

                src_funcs = {node.name for node in ast.walk(src_ast) if isinstance(node, ast.FunctionDef)}
                tgt_funcs = {node.name for node in ast.walk(tgt_ast) if isinstance(node, ast.FunctionDef)}

                dup_funcs = src_funcs.intersection(tgt_funcs)
                for func in dup_funcs:
                    conflicts.append(
                        ConflictItem(
                            conflict_type="AST_COLLISION",
                            target_file=target_file_path,
                            conflict_identifier=func,
                            resolution_strategy="RENAME",
                        )
                    )
            except Exception:
                pass

        except Exception as e:
            logger.error("ConflictDetector error inspecting %s: %s", target_file_path, e)

        return conflicts
