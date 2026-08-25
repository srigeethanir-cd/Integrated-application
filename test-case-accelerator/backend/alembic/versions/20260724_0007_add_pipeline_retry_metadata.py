"""Add persisted pipeline retry metadata.

Revision ID: 20260724_0007
Revises: 20260723_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0007"
down_revision: str | None = "20260723_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "code_understanding_runs",
        sa.Column("failed_stage", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "code_understanding_runs",
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "code_understanding_runs",
        sa.Column(
            "retry_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "code_understanding_runs",
        sa.Column("last_successful_stage", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("code_understanding_runs", "last_successful_stage")
    op.drop_column("code_understanding_runs", "retry_count")
    op.drop_column("code_understanding_runs", "failure_reason")
    op.drop_column("code_understanding_runs", "failed_stage")
