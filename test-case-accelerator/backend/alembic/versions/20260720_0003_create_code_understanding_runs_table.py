"""Create code-understanding runs table.

Revision ID: 20260720_0003
Revises: 20260720_0002
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0003"
down_revision: str | None = "20260720_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

code_understanding_status = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    name="code_understanding_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    code_understanding_status.create(bind, checkfirst=True)

    op.create_table(
        "code_understanding_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "dependency_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            code_understanding_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["dependency_run_id"],
            ["dependency_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_code_understanding_runs_dependency_run_id",
        "code_understanding_runs",
        ["dependency_run_id"],
    )
    op.create_index(
        "ix_code_understanding_runs_project_id",
        "code_understanding_runs",
        ["project_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index(
        "ix_code_understanding_runs_project_id",
        table_name="code_understanding_runs",
    )
    op.drop_index(
        "ix_code_understanding_runs_dependency_run_id",
        table_name="code_understanding_runs",
    )
    op.drop_table("code_understanding_runs")
    code_understanding_status.drop(bind, checkfirst=True)
