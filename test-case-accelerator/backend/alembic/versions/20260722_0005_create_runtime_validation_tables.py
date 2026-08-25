"""Create Stage 7 runtime validation tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260722_0005"
down_revision: str | None = "20260722_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    validation_status = postgresql.ENUM(
        "pending", "running", "completed", "partial", "failed",
        name="runtime_validation_status",
        create_type=False,
    )
    test_status = postgresql.ENUM(
        "Passed", "Failed", "Skipped", "NotExecutable",
        name="runtime_test_status",
        create_type=False,
    )
    validation_status.create(op.get_bind(), checkfirst=True)
    test_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "runtime_validation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_stage_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", validation_status, nullable=False, server_default="pending"),
        sa.Column("execution_mode", sa.String(50), nullable=False, server_default="managed"),
        sa.Column("base_url", sa.String(2048), nullable=False),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("summary", postgresql.JSONB()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_stage_run_id"], ["code_understanding_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_runtime_validation_runs_project_id", "runtime_validation_runs", ["project_id"])
    op.create_index("ix_runtime_validation_runs_source_stage_run_id", "runtime_validation_runs", ["source_stage_run_id"])
    op.create_table(
        "runtime_execution_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_case_id", sa.String(255), nullable=False),
        sa.Column("runtime_status", test_status, nullable=False),
        sa.Column("expected_result", postgresql.JSONB()),
        sa.Column("actual_result", postgresql.JSONB()),
        sa.Column("assertion_failure", sa.Text()),
        sa.Column("logs", sa.Text()),
        sa.Column("execution_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["run_id"], ["runtime_validation_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_runtime_execution_results_run_id", "runtime_execution_results", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_runtime_execution_results_run_id", table_name="runtime_execution_results")
    op.drop_table("runtime_execution_results")
    op.drop_index("ix_runtime_validation_runs_source_stage_run_id", table_name="runtime_validation_runs")
    op.drop_index("ix_runtime_validation_runs_project_id", table_name="runtime_validation_runs")
    op.drop_table("runtime_validation_runs")
    postgresql.ENUM(name="runtime_test_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="runtime_validation_status").drop(op.get_bind(), checkfirst=True)
