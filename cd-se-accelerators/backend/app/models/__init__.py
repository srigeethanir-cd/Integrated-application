"""Centralized export of all SQLAlchemy ORM models."""

from app.models.authentication import AuthenticationRecord
from app.models.project import Project
from app.models.blueprint import Blueprint
from app.models.epic import Epic
from app.models.story import Story
from app.models.component import Component
from app.models.story_component_map import StoryComponentMap
from app.models.generation_history import GenerationHistory
from app.models.traceability import Traceability

# Import consolidated models
from app.models.consolidated_models import (
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

from app.models.orchestration_metadata import (
    RollbackHistoryRecord
)

from app.models.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
    PromptExecutionLog,
    PromptApproval,
    PromptPerformance
)

from app.models.workflow_execution import WorkflowExecutionSession
from app.models.final_governance_audit import FinalGovernanceAudit
from app.models.request_change import RequestChange

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
