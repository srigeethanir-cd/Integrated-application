"""
Project Scanner Models – Fast Indexing & Caching.

Defines Pydantic schemas for project indexing, file hashing, and scan statistics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileHashEntry(BaseModel):
    """File content hash entry for caching."""

    file_path: str = Field(..., description="POSIX relative path of the file.")
    file_hash: str = Field(..., description="SHA-256 content hash.")
    file_size_bytes: int = Field(0, description="Size of file in bytes.")
    is_component: bool = Field(False, description="Whether file contains a frontend component.")
    is_service: bool = Field(False, description="Whether file contains a service/API layer.")
    is_test: bool = Field(False, description="Whether file is a unit test.")


class ScanStats(BaseModel):
    """Statistics for project scanning."""

    total_files_scanned: int = Field(0, description="Total files encountered during walk.")
    relevant_files: int = Field(0, description="Files included in project index.")
    ignored_files: int = Field(0, description="Files skipped due to ignore patterns.")
    component_files: int = Field(0, description="Number of potential component source files.")
    hook_files: int = Field(0, description="Number of hook files discovered.")
    page_files: int = Field(0, description="Number of page-level files discovered.")
    service_files: int = Field(0, description="Number of service/API files discovered.")
    utility_files: int = Field(0, description="Number of utility/helper files discovered.")


class ProjectIndex(BaseModel):
    """Reusable index of a project workspace created during fast scan."""

    project_root: str = Field(..., description="Absolute path of project root.")
    project_id: str = Field(..., description="Unique project identifier.")
    pipeline_run_id: str = Field(..., description="Associated pipeline run ID.")
    project_hash: str = Field(..., description="Composite SHA-256 hash of all relevant source files.")
    framework: str = Field("Unknown", description="Deterministically detected framework.")
    framework_version: Optional[str] = Field(None, description="Framework version if available.")
    source_files: List[str] = Field(default_factory=list, description="Relative paths of source files.")
    components: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted component metadata summaries.")
    services: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted service metadata summaries.")
    routes: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted route metadata summaries.")
    hooks: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted hook file metadata summaries.")
    pages: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted page-level file metadata summaries.")
    utilities: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted utility file metadata summaries.")
    styles: List[str] = Field(default_factory=list, description="Relative paths of style files associated with components.")
    existing_tests: List[str] = Field(default_factory=list, description="Relative paths of unit test files.")
    configuration_files: List[str] = Field(default_factory=list, description="Relative paths of configuration files.")
    relevant_dependencies: Dict[str, str] = Field(default_factory=dict, description="Key frontend dependencies from package.json.")
    file_hashes: Dict[str, str] = Field(default_factory=dict, description="Map of relative file path -> SHA-256 hash.")
    stats: ScanStats = Field(default_factory=ScanStats, description="Scan file counts breakdown.")
