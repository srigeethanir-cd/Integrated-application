"""Update database schema with new tables, PKs, FKs, JSONB columns, and indexes.

Revision ID: a1b2c3d4e5f6
Revises: 6fa3061d758d
Create Date: 2026-07-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6fa3061d758d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Update projects table ───────────────────────────────────────
    op.alter_column("projects", "id", new_column_name="project_id")
    op.alter_column("projects", "name", new_column_name="project_name")
    
    # Drop old index if exists and create index for project_name
    try:
        op.drop_index("ix_projects_name", table_name="projects")
    except Exception:
        pass
    op.create_index("ix_projects_project_name", "projects", ["project_name"])
    
    op.add_column("projects", sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False))
    
    # Convert tech_stack string/column to jsonb
    op.execute(
        "ALTER TABLE projects ALTER COLUMN tech_stack TYPE JSONB USING "
        "CASE WHEN tech_stack IS NULL THEN NULL "
        "WHEN tech_stack LIKE '{%' OR tech_stack LIKE '[%' THEN tech_stack::jsonb "
        "ELSE to_jsonb(tech_stack) END"
    )

    # ── 2. Update blueprints table ─────────────────────────────────────
    op.alter_column("blueprints", "id", new_column_name="blueprint_id")
    op.add_column("blueprints", sa.Column("api_design", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("blueprints", sa.Column("database_design", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # Copy api_blueprint data to api_design if present
    op.execute("UPDATE blueprints SET api_design = api_blueprint WHERE api_blueprint IS NOT NULL")

    # ── 3. Rename stories to user_stories and update columns ─────────
    op.rename_table("stories", "user_stories")
    op.alter_column("user_stories", "id", new_column_name="story_id")
    op.alter_column("user_stories", "title", new_column_name="story_title")
    op.alter_column("user_stories", "description", new_column_name="story_description")
    op.alter_column("user_stories", "status", new_column_name="approval_status")
    
    # Make epic_id nullable
    op.alter_column("user_stories", "epic_id", nullable=True)

    # Add project_id column to user_stories
    op.add_column("user_stories", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    
    # Backfill user_stories.project_id from epics if possible
    op.execute(
        "UPDATE user_stories SET project_id = epics.project_id "
        "FROM epics WHERE user_stories.epic_id = epics.id"
    )
    
    op.add_column("user_stories", sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False))

    op.create_foreign_key(
        "fk_user_stories_project_id_projects",
        "user_stories",
        "projects",
        ["project_id"],
        ["project_id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_user_stories_project_id", "user_stories", ["project_id"])
    op.create_index("ix_user_stories_story_id", "user_stories", ["story_id"])
    op.create_index("ix_user_stories_approval_status", "user_stories", ["approval_status"])

    # ── 4. Create traceability table ───────────────────────────────────
    op.create_table(
        "traceability",
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_agent", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("trace_id"),
    )
    op.create_index("ix_traceability_project_id", "traceability", ["project_id"])
    op.create_index("ix_traceability_source_id", "traceability", ["source_id"])
    op.create_index("ix_traceability_target_id", "traceability", ["target_id"])

    # ── 5. Create artifacts table ──────────────────────────────────────
    op.create_table(
        "artifacts",
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_name", sa.String(255), nullable=False),
        sa.Column("artifact_type", sa.String(100), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["user_stories.story_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("artifact_id"),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("ix_artifacts_story_id", "artifacts", ["story_id"])

    # ── 6. Create artifact_contents table ──────────────────────────────
    op.create_table(
        "artifact_contents",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.artifact_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("content_id"),
    )
    op.create_index("ix_artifact_contents_artifact_id", "artifact_contents", ["artifact_id"])


def downgrade() -> None:
    op.drop_table("artifact_contents")
    op.drop_table("artifacts")
    op.drop_table("traceability")

    op.drop_constraint("fk_user_stories_project_id_projects", "user_stories", type_="foreignkey")
    op.drop_index("ix_user_stories_approval_status", table_name="user_stories")
    op.drop_index("ix_user_stories_story_id", table_name="user_stories")
    op.drop_index("ix_user_stories_project_id", table_name="user_stories")
    op.drop_column("user_stories", "version")
    op.drop_column("user_stories", "project_id")
    op.alter_column("user_stories", "epic_id", nullable=False)
    op.alter_column("user_stories", "approval_status", new_column_name="status")
    op.alter_column("user_stories", "story_description", new_column_name="description")
    op.alter_column("user_stories", "story_title", new_column_name="title")
    op.alter_column("user_stories", "story_id", new_column_name="id")
    op.rename_table("user_stories", "stories")

    op.drop_column("blueprints", "database_design")
    op.drop_column("blueprints", "api_design")
    op.alter_column("blueprints", "blueprint_id", new_column_name="id")

    op.drop_column("projects", "version")
    op.drop_index("ix_projects_project_name", table_name="projects")
    op.create_index("ix_projects_name", "projects", ["name"])
    op.alter_column("projects", "project_name", new_column_name="name")
    op.alter_column("projects", "project_id", new_column_name="id")
