"""Centralized export of all SQLAlchemy ORM models."""

from database_main.models.authentication import AuthenticationRecord
from database_main.models.project import Project
from database_main.models.blueprint import Blueprint
from database_main.models.epic import Epic
from database_main.models.story import Story
from database_main.models.component import Component
from database_main.models.story_component_map import StoryComponentMap
from database_main.models.generation_history import GenerationHistory
from database_main.models.traceability import Traceability

# Import consolidated models
from database_main.models.consolidated_models import (
    StoryLifecycle,
    StoryHistory,
    GeneratedFile,
    Artifact as ConsolidatedArtifact,
    StoryDependency,
    ExecutionLog,
    ExecutionTimelineRecord,
    AgentExecutionMetric,
    ProjectValidation,
    StoryRefinement
)

from database_main.models.orchestration_metadata import (
    RollbackHistoryRecord
)

from database_main.models.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
    PromptExecutionLog,
    PromptApproval,
    PromptPerformance
)

from database_main.models.workflow_execution import WorkflowExecutionSession
from database_main.models.final_governance_audit import FinalGovernanceAudit
from database_main.models.request_change import RequestChange

# Class Aliases for consolidated tables (100% Backward Compatibility)
File = GeneratedFile
FileHistory = GeneratedFile
GeneratedFileRegistry = GeneratedFile
FileVersionHistory = GeneratedFile

StoryExecution = StoryLifecycle
StoryValidation = StoryLifecycle
StoryApproval = StoryLifecycle
StoryMerge = StoryLifecycle

StoryVersion = StoryHistory
StoryAudit = StoryHistory
StoryFeedback = StoryHistory
StoryRevision = StoryHistory

Artifact = ConsolidatedArtifact
ArtifactContent = ConsolidatedArtifact
SharedArtifactRegistryRecord = ConsolidatedArtifact

Dependency = StoryDependency
DependencyGraphRecord = StoryDependency

ValidationResult = ProjectValidation
ProjectHealthRecord = ProjectValidation

__all__ = [
    "AuthenticationRecord",
    "Project",
    "Blueprint",
    "Epic",
    "Story",
    "Component",
    "StoryComponentMap",
    "Dependency",
    "File",
    "FileHistory",
    "GenerationHistory",
    "ValidationResult",
    "Traceability",
    "Artifact",
    "ArtifactContent",
    "StoryExecution",
    "StoryValidation",
    "StoryApproval",
    "StoryMerge",
    "StoryVersion",
    "StoryAudit",
    "GeneratedFileRegistry",
    "FileVersionHistory",
    "StoryFeedback",
    "StoryRevision",
    "SharedArtifactRegistryRecord",
    "DependencyGraphRecord",
    "ExecutionTimelineRecord",
    "RollbackHistoryRecord",
    "ProjectHealthRecord",
    "AgentExecutionMetric",
    "PromptTemplate",
    "PromptTemplateVersion",
    "PromptExecutionLog",
    "PromptApproval",
    "PromptPerformance",
    "StoryLifecycle",
    "StoryHistory",
    "GeneratedFile",
    "StoryDependency",
    "ExecutionLog",
    "ProjectValidation",
    "WorkflowExecutionSession",
    "FinalGovernanceAudit",
    "RequestChange",
]
