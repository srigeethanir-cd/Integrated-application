import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import SharedArtifactRegistryRecord

logger = logging.getLogger(__name__)

class SharedArtifactRegistry:
    """Tracks and registers shared components, services, and schemas across stories in PostgreSQL to avoid duplicates."""

    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id

    def find_reusable_artifact(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Checks if a matching reusable artifact has already been registered in the database."""
        record = self.db.query(SharedArtifactRegistryRecord).filter_by(
            project_id=self.project_id,
            category=category,
            name=name
        ).first()

        if record:
            return {
                "name": record.name,
                "category": record.category,
                "path": record.file_path,
                "owner_story": record.owner_story,
                "usage_references": record.usage_references_json
            }
        return None

    def register_artifact(self, category: str, name: str, file_path: str, story_key: str) -> Dict[str, Any]:
        """Registers a newly generated file as a shared reusable artifact in PostgreSQL."""
        # Check if already registered to avoid duplicates
        record = self.db.query(SharedArtifactRegistryRecord).filter_by(
            project_id=self.project_id,
            category=category,
            name=name
        ).first()

        if not record:
            record = SharedArtifactRegistryRecord(
                project_id=self.project_id,
                name=name,
                category=category,
                file_path=file_path,
                owner_story=story_key,
                usage_references_json=[story_key]
            )
            self.db.add(record)
        else:
            if story_key not in record.usage_references_json:
                refs = list(record.usage_references_json)
                refs.append(story_key)
                record.usage_references_json = refs
                
        self.db.commit()
        logger.info("ArtifactRegistry: Registered shared %s '%s' from story %s in DB", category, name, story_key)
        
        return {
            "name": record.name,
            "category": record.category,
            "path": record.file_path,
            "owner_story": record.owner_story,
            "usage_references": record.usage_references_json
        }

    def record_usage(self, artifact_name: str, story_key: str):
        """Records that another story is reusing a registered shared artifact."""
        record = self.db.query(SharedArtifactRegistryRecord).filter_by(
            project_id=self.project_id,
            name=artifact_name
        ).first()

        if record:
            if story_key not in record.usage_references_json:
                refs = list(record.usage_references_json)
                refs.append(story_key)
                record.usage_references_json = refs
                self.db.commit()
                logger.info("ArtifactRegistry: Recorded usage of '%s' by story %s in DB", artifact_name, story_key)
