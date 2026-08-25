"""Harden security scan timestamps and concurrent run tracking.

Revision ID: 20260727_0009
Revises: 20260727_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0009"
down_revision: str | None = "20260727_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preserve the newest active run if historical races created more than one.
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY project_id
                       ORDER BY created_at DESC, id DESC
                   ) AS position
            FROM security_scan_runs
            WHERE status = 'running'
        )
        UPDATE security_scan_runs
        SET status = 'failed',
            error_message = COALESCE(
                error_message,
                'Superseded by a concurrent security scan'
            ),
            finished_at = CURRENT_TIMESTAMP
        WHERE id IN (SELECT id FROM ranked WHERE position > 1)
        """
    )
    op.alter_column(
        "security_scan_runs",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    for column in ("started_at", "finished_at"):
        op.alter_column(
            "security_scan_runs",
            column,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            existing_nullable=True,
        )
    op.create_index(
        "uq_security_scan_runs_running_project",
        "security_scan_runs",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_security_scan_runs_running_project",
        table_name="security_scan_runs",
    )
    op.alter_column(
        "security_scan_runs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    for column in ("started_at", "finished_at"):
        op.alter_column(
            "security_scan_runs",
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            existing_nullable=True,
        )
