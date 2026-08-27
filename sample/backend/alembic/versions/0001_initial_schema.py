"""Initial schema — create all 11 tables.

Revision ID: 0001
Revises: None
Create Date: 2026-07-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
# pyrefly: ignore [missing-module-attribute]
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── projects ────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # ── blueprints ──────────────────────────────────────────────────────
    op.create_table(
        "blueprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("architecture", sa.Text(), nullable=True),
        sa.Column("folder_structure", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("api_blueprint", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("workflow_blueprint", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("shared_components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_blueprints_project_id", "blueprints", ["project_id"])

    # ── epics ───────────────────────────────────────────────────────────
    op.create_table(
        "epics",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("blueprint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("epic_key", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blueprint_id"], ["blueprints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("epic_key"),
    )
    op.create_index("ix_epics_project_id", "epics", ["project_id"])
    op.create_index("ix_epics_blueprint_id", "epics", ["blueprint_id"])
    op.create_index("ix_epics_epic_key", "epics", ["epic_key"])

    # ── stories ─────────────────────────────────────────────────────────
    op.create_table(
        "stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("epic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_key", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["epic_id"], ["epics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("story_key"),
    )
    op.create_index("ix_stories_epic_id", "stories", ["epic_id"])
    op.create_index("ix_stories_story_key", "stories", ["story_key"])
    op.create_index("ix_stories_status", "stories", ["status"])

    # ── components ──────────────────────────────────────────────────────
    op.create_table(
        "components",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_agent", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_components_project_id", "components", ["project_id"])
    op.create_index("ix_components_name", "components", ["name"])
    op.create_index("ix_components_type", "components", ["type"])
    op.create_index("ix_components_created_by_agent", "components", ["created_by_agent"])

    # ── files ───────────────────────────────────────────────────────────
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(1000), nullable=False),
        sa.Column("hash", sa.String(128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_files_component_id", "files", ["component_id"])
    op.create_index("ix_files_story_id", "files", ["story_id"])

    # ── story_component_map ─────────────────────────────────────────────
    op.create_table(
        "story_component_map",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False, comment="One of: CREATE, MODIFY, DELETE, REUSE"),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_component_map_story_id", "story_component_map", ["story_id"])
    op.create_index("ix_story_component_map_component_id", "story_component_map", ["component_id"])
    op.create_index("ix_story_component_map_action", "story_component_map", ["action"])

    # ── dependencies ────────────────────────────────────────────────────
    op.create_table(
        "dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_component_id"], ["components.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dependencies_component_id", "dependencies", ["component_id"])
    op.create_index("ix_dependencies_depends_on_component_id", "dependencies", ["depends_on_component_id"])
    op.create_index("ix_dependencies_dependency_type", "dependencies", ["dependency_type"])

    # ── generation_history ──────────────────────────────────────────────
    op.create_table(
        "generation_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("execution_time", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_history_story_id", "generation_history", ["story_id"])
    op.create_index("ix_generation_history_agent", "generation_history", ["agent"])
    op.create_index("ix_generation_history_status", "generation_history", ["status"])

    # ── validation_results ──────────────────────────────────────────────
    op.create_table(
        "validation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validation_type", sa.String(100), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_validation_results_story_id", "validation_results", ["story_id"])
    op.create_index("ix_validation_results_validation_type", "validation_results", ["validation_type"])

    # ── file_history ────────────────────────────────────────────────────
    op.create_table(
        "file_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("modified_by", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_file_history_file_id", "file_history", ["file_id"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("file_history")
    op.drop_table("validation_results")
    op.drop_table("generation_history")
    op.drop_table("dependencies")
    op.drop_table("story_component_map")
    op.drop_table("files")
    op.drop_table("components")
    op.drop_table("stories")
    op.drop_table("epics")
    op.drop_table("blueprints")
    op.drop_table("projects")
