"""Add telemetry and resume columns to analysis_status.

Revision ID: 20260723_0006
Revises: 20260722_0005
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0006"
down_revision: str | None = "20260722_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analysis_status", sa.Column("stage_number", sa.Integer(), nullable=True))
    op.add_column("analysis_status", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("analysis_status", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("analysis_status", sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.add_column("analysis_status", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_status", "error_message")
    op.drop_column("analysis_status", "completed_at")
    op.drop_column("analysis_status", "started_at")
    op.drop_column("analysis_status", "retry_count")
    op.drop_column("analysis_status", "stage_number")
