import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from story_orchestration.dependency_resolver import StoryDependencyResolver
from story_orchestration.execution_scheduler import StoryExecutionScheduler
from story_shared.artifact_registry import SharedArtifactRegistry
from story_database.migration_planner import DatabaseMigrationPlanner
from validators.cross_story_validator import CrossStoryValidator
from merger.merge_queue import DependencyAwareMergeQueue

logger = logging.getLogger(__name__)
settings = get_settings()

class ProjectOrchestrator:
    """Central orchestration controller coordinating project workflows, agents, database tables, and queues."""

    def __init__(self, project_id: str, db: Optional[Session] = None):
        self.project_id = project_id
        self.workspace_root = Path(settings.workspace_root) / project_id
        
        if db is None:
            from app.database.session import SessionLocal
            self.db = SessionLocal()
            self._own_session = True
        else:
            self.db = db
            self._own_session = False

        self.resolver = StoryDependencyResolver(db=self.db, project_id=project_id)
        self.scheduler = StoryExecutionScheduler(db=self.db, project_id=project_id)
        self.registry = SharedArtifactRegistry(db=self.db, project_id=project_id)
        self.migration_planner = DatabaseMigrationPlanner(db=self.db, project_id=project_id)
        self.cross_story_validator = CrossStoryValidator(workspace_root=Path(settings.workspace_root) / project_id)
        
        self.integrated_project_root = Path(f"{Path(settings.outputs_root).parent}/generated_projects/{project_id}")
        self.merge_queue = DependencyAwareMergeQueue(
            db=self.db,
            project_id=project_id,
            workspace_root=Path(settings.workspace_root) / project_id,
            integrated_project_root=self.integrated_project_root
        )

    def close(self):
        """Close DB session if owned by orchestrator."""
        if self._own_session and self.db:
            self.db.close()

    def run_dependency_analysis(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs the dependency resolver stage and writes reports to DB."""
        logger.info("Orchestrator: Resolving dependencies for project %s", self.project_id)
        return self.resolver.resolve_dependencies(stories)

    def execute_story_generation_queue(
        self,
        stories: List[Dict[str, Any]],
        run_story_fn: Any
    ) -> Dict[str, Any]:
        """Runs the execution scheduler queue in parallel based on PostgreSQL dependency order."""
        logger.info("Orchestrator: Executing generation queue for project %s", self.project_id)
        
        from app.models import DependencyGraphRecord
        record = self.db.query(DependencyGraphRecord).filter_by(project_id=self.project_id).first()
        
        if not record:
            self.run_dependency_analysis(stories)
            record = self.db.query(DependencyGraphRecord).filter_by(project_id=self.project_id).first()
            
        execution_order = record.execution_order_json
        dependency_graph = record.dependency_graph_json.get("dependencies", {})
        if not dependency_graph:
            # Reconstruct map from links
            dependency_graph = {s_key: [] for s_key in execution_order}
            for link in record.dependency_graph_json.get("links", []):
                src = link["source"]
                tgt = link["target"]
                if tgt in dependency_graph:
                    dependency_graph[tgt].append(src)
        
        return self.scheduler.execute_queue(
            stories=stories,
            execution_order=execution_order,
            dependency_graph=dependency_graph,
            run_story_fn=run_story_fn
        )

    def plan_project_migrations(self, migrations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Plans all database migrations dynamically and stores them in database."""
        logger.info("Orchestrator: Planning database migrations for project %s", self.project_id)
        return self.migration_planner.plan_migrations(migrations)

    def validate_cross_stories_pre_merge(self, approved_stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Performs pre-merge validations across multiple approved stories."""
        logger.info("Orchestrator: Running pre-merge validation checks for project %s", self.project_id)
        return self.cross_story_validator.validate_cross_stories(approved_stories)

    def execute_dependency_aware_merge(
        self,
        approved_stories: List[Dict[str, Any]],
        run_merge_fn: Any
    ) -> Dict[str, Any]:
        """Merges approved stories into staging according to dependency order using DB MergeQueue state."""
        logger.info("Orchestrator: Processing staging merge queue for project %s", self.project_id)
        
        from app.models import DependencyGraphRecord
        record = self.db.query(DependencyGraphRecord).filter_by(project_id=self.project_id).first()
        
        execution_order = record.execution_order_json
        dependency_graph = record.dependency_graph_json.get("dependencies", {})
        if not dependency_graph:
            dependency_graph = {s_key: [] for s_key in execution_order}
            for link in record.dependency_graph_json.get("links", []):
                src = link["source"]
                tgt = link["target"]
                if tgt in dependency_graph:
                    dependency_graph[tgt].append(src)
        
        return self.merge_queue.execute_merges(
            approved_stories=approved_stories,
            execution_order=execution_order,
            dependency_graph=dependency_graph,
            run_merge_fn=run_merge_fn
        )
