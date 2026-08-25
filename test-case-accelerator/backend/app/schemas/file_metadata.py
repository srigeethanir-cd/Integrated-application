# backend/app/schemas/file_metadata.py
"""Pydantic schema for file metadata produced by the discovery stage.

Only fields required for later stages are defined. Additional attributes can be
added in future commits.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class FileMetadata(BaseModel):
    """Metadata information for a single source file.

    Attributes:
        path: Portable path relative to the configured storage root.
        language: Detected programming language.
        is_entry_point: ``True`` if the file is an entry point.
        imports: List of import strings found in the file.
        classes: List of class names defined in the file.
        functions: List of function names defined in the file.
    """

    path: str = Field(..., description="Storage-root-relative file path")
    language: str = Field(..., description="Detected programming language")
    is_entry_point: bool = Field(False, description="Whether the file is an entry point")
    imports: List[str] = Field(default_factory=list, description="Import statements found in the file")
    classes: List[str] = Field(default_factory=list, description="Class names defined in the file")
    functions: List[str] = Field(default_factory=list, description="Function names defined in the file")

    model_config = {"from_attributes": True}
