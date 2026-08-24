"""Exceptions for the Knowledge Service module."""


class KnowledgeServiceError(Exception):
    """Base exception for all Knowledge Service errors."""

    pass


class StoryNotFoundError(KnowledgeServiceError):
    """Raised when a requested user story cannot be found by ID or Key."""

    def __init__(self, story_id: str) -> None:
        self.story_id = story_id
        super().__init__(f"Story not found for ID/Key: '{story_id}'")


class BlueprintNotFoundError(KnowledgeServiceError):
    """Raised when a blueprint for a story or project cannot be located."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Blueprint not found for project ID: '{project_id}'")


class ContextBuilderError(KnowledgeServiceError):
    """Raised when context aggregation fails."""

    pass


class SemanticAnalyzerError(KnowledgeServiceError):
    """Raised when semantic analysis fails or invalid arguments are provided."""

    pass


class RetrievalEngineError(KnowledgeServiceError):
    """Raised when retrieval engine orchestration fails."""

    pass


