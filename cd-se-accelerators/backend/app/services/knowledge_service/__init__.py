"""Knowledge Service module.

Exposes context building, semantic requirement analysis, retrieval engine facade,
blueprint management, traceability, component registration, and dependency graph interfaces.
"""

from app.services.knowledge_service.context_builder import ContextBuilder
from app.services.knowledge_service.exceptions import (
    BlueprintNotFoundError,
    ContextBuilderError,
    KnowledgeServiceError,
    RetrievalEngineError,
    SemanticAnalyzerError,
    StoryNotFoundError,
)
from app.services.knowledge_service.retrieval_engine import RetrievalEngine
from app.services.knowledge_service.semantic_analyzer import SemanticAnalyzer

__all__ = [
    "ContextBuilder",
    "SemanticAnalyzer",
    "RetrievalEngine",
    "KnowledgeServiceError",
    "StoryNotFoundError",
    "BlueprintNotFoundError",
    "ContextBuilderError",
    "SemanticAnalyzerError",
    "RetrievalEngineError",
]
