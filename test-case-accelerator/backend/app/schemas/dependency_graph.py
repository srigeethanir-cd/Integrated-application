# backend/app/schemas/dependency_graph.py
"""Pydantic schema for representing a dependency graph.

The schema provides a serialisable representation of the adjacency list.
Business fields will be added in later commits.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, List


class DependencyGraphSchema(BaseModel):
    """Adjacency‑list representation of the project's dependency graph.

    Keys are source file paths, values are lists of target file paths that the
    source imports.
    """

    adjacency: Dict[str, List[str]] = Field(..., description="Mapping of source file to imported target files")

    class Config:
        json_encoders = {str: str}
