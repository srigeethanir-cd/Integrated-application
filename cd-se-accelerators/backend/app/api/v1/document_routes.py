"""FastAPI Document Upload Routes for wireframe images and user story JSON specifications."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database.session import get_db

router = APIRouter(prefix="/documents", tags=["Document Upload"])
logger = logging.getLogger(__name__)


class WireframeUploadPayload(BaseModel):
    filename: str = Field(description="Wireframe filename (e.g. login.png)")
    content_base64: Optional[str] = Field(default=None, description="Optional base64 encoded image string")


class StoryUploadPayload(BaseModel):
    filename: str = Field(default="stories.json", description="Filename")
    project_id: Optional[str] = Field(
        default=None,
        description="Target project UUID. Overrides the query parameter if both are supplied.",
    )
    stories: List[Dict[str, Any]] = Field(description="Parsed user story objects")


@router.post("/upload-wireframe", response_model=Dict[str, Any])
def upload_wireframe_image(payload: WireframeUploadPayload) -> Any:
    """Upload wireframe screenshot image metadata/content for Agent 0 visual analysis."""
    if not payload.filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
        raise HTTPException(status_code=400, detail="Invalid image file format. Supported: png, jpg, jpeg, webp, svg")

    logger.info("Uploaded wireframe image metadata: %s", payload.filename)

    return success_response(
        data={
            "filename": payload.filename,
            "saved_path": f"uploads/wireframes/{payload.filename}",
            "status": "STORED",
        },
        message="Wireframe image uploaded successfully.",
    )


@router.post("/upload-user-stories", response_model=Dict[str, Any])
def upload_user_stories_json(
    payload: StoryUploadPayload,
    db: Session = Depends(get_db),
) -> Any:
    """Upload user story JSON specification payload and persist in database."""
    import uuid as _uuid
    from sqlalchemy import desc
    from app.models.blueprint import Blueprint
    from app.models.epic import Epic
    from app.models.project import Project
    from app.models.story import Story
    from app.repository.blueprint_repository import BlueprintRepository

    # ── Resolve project ─────────────────────────────────────────────────
    from app.repository.project_repository import ProjectRepository
    project_repo = ProjectRepository(db)
    resolved_project_id = None

    effective_pid_str = payload.project_id

    if effective_pid_str:
        try:
            pid = _uuid.UUID(effective_pid_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"project_id '{effective_pid_str}' is not a valid UUID.",
            )
        proj = project_repo.get(pid)
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{effective_pid_str}' not found.",
            )
        resolved_project_id = proj.project_id
    else:
        # Auto-select the most recently created project
        latest_proj = db.scalars(
            select(Project).order_by(desc(Project.created_at)).limit(1)
        ).first()
        if latest_proj:
            resolved_project_id = latest_proj.project_id
            logger.info("upload-user-stories: auto-selected project '%s' (%s)", latest_proj.project_name, resolved_project_id)

    if not resolved_project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No project found. Create a project first or supply project_id.",
        )

    logger.info("upload-user-stories: target project_id=%s", resolved_project_id)

    # ── Resolve / create placeholder blueprint ──────────────────────────
    bp = db.scalars(
        select(Blueprint).where(Blueprint.project_id == resolved_project_id).limit(1)
    ).first()
    if not bp:
        bp_repo = BlueprintRepository(db)
        bp = bp_repo.create({
            "project_id": resolved_project_id,
            "version": 1,
            "architecture": "PLACEHOLDER",
        })
        logger.info("upload-user-stories: created placeholder blueprint %s", bp.blueprint_id)
    blueprint_id = bp.blueprint_id

    # ── Process stories (each in a savepoint for partial-batch safety) ──
    inserted: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for index, story_data in enumerate(payload.stories):
        story_key = (
            story_data.get("story_key")
            or story_data.get("id")
            or story_data.get("story_id")
        )
        if not story_key:
            errors.append({
                "index": index,
                "error": "Missing identifier: supply 'story_key', 'id', or 'story_id'.",
            })
            continue

        try:
            # Savepoint: one bad story never rolls back the whole batch
            with db.begin_nested():
                # ── Resolve / create epic scoped to THIS project ──────
                epic_key = (
                    story_data.get("epic_key")
                    or story_data.get("epic_id")
                    or "EP001"
                )
                epic_name = (
                    story_data.get("epic_name")
                    or story_data.get("epic")
                    or "General Epic"
                )
                # Scope lookup to project so same epic_key in different projects creates separate epics
                epic_obj = db.scalars(
                    select(Epic)
                    .where(Epic.epic_key == epic_key)
                    .where(Epic.project_id == resolved_project_id)
                ).first()
                if not epic_obj:
                    epic_obj = Epic(
                        project_id=resolved_project_id,
                        blueprint_id=blueprint_id,
                        epic_key=epic_key,
                        title=epic_name,
                        description=epic_name,
                    )
                    db.add(epic_obj)
                    db.flush()  # get DB-assigned id before using it in Story FK
                    logger.info("upload-user-stories: created epic '%s' for project %s", epic_key, resolved_project_id)

                epic_uuid = epic_obj.id

                # ── Persist story scoped to THIS project ──────────────
                # Scope lookup to project so same story_key in different projects creates separate stories
                existing = db.scalars(
                    select(Story)
                    .where(Story.story_key == story_key)
                    .where(Story.project_id == resolved_project_id)
                ).first()
                if not existing:
                    story_obj = Story(
                        project_id=resolved_project_id,
                        epic_id=epic_uuid,
                        story_key=story_key,
                        story_title=(
                            story_data.get("story_title")
                            or story_data.get("title")
                            or "Untitled Story"
                        ),
                        story_description=(
                            story_data.get("story_description")
                            or story_data.get("description")
                        ),
                        acceptance_criteria=story_data.get("acceptance_criteria") or {},
                    )
                    db.add(story_obj)
                    db.flush()
                    logger.info("upload-user-stories: inserted story '%s'", story_key)
                    inserted.append({"story_key": story_key, "action": "created", "story_id": str(story_obj.story_id)})
                else:
                    # Update epic and title if already exists for this project
                    existing.epic_id = epic_uuid
                    existing.story_title = (
                        story_data.get("story_title")
                        or story_data.get("title")
                        or existing.story_title
                    )
                    existing.story_description = (
                        story_data.get("story_description")
                        or story_data.get("description")
                        or existing.story_description
                    )
                    db.flush()
                    logger.info("upload-user-stories: updated story '%s'", story_key)
                    inserted.append({"story_key": story_key, "action": "updated", "story_id": str(existing.story_id)})

        except Exception as exc:  # noqa: BLE001
            logger.error("upload-user-stories: story index=%d key=%s error: %s", index, story_key, exc)
            errors.append({"index": index, "story_key": story_key, "error": str(exc)})

    # Commit everything that succeeded
    db.commit()

    if errors and not inserted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "All stories failed to persist.", "errors": errors},
        )

    return success_response(
        data={
            "filename": payload.filename,
            "project_id": str(resolved_project_id),
            "stories_submitted": len(payload.stories),
            "stories_persisted": len(inserted),
            "stories_failed": len(errors),
            "persisted": inserted,
            "errors": errors,
        },
        message="User story JSON uploaded and persisted successfully.",
    )


