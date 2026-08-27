"""Create dependency discovery tables.

Revision ID: 20260720_0002
Revises: 20260717_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dependency_status = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="dependency_status",
        create_type=False,
    )
    step_status = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="step_status",
        create_type=False,
    )
    bind = op.get_bind()
    dependency_status.create(bind, checkfirst=True)
    step_status.create(bind, checkfirst=True)

    op.create_table(
        "dependency_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_path", sa.String(), nullable=False),
        sa.Column("status", dependency_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_dependency_runs_project_id"),
        "dependency_runs",
        ["project_id"],
    )
    op.create_table(
        "discovered_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=2048), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("is_entry_point", sa.Boolean(), nullable=False),
        sa.Column("imports", sa.JSON(), nullable=True),
        sa.Column("classes", sa.JSON(), nullable=True),
        sa.Column("functions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["dependency_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "analysis_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("status", step_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["dependency_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("analysis_status")
    op.drop_table("discovered_files")
    op.drop_index(op.f("ix_dependency_runs_project_id"), table_name="dependency_runs")
    op.drop_table("dependency_runs")
    postgresql.ENUM(name="step_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="dependency_status").drop(bind, checkfirst=True)
