"""Normalize persisted storage paths to portable relative values.

Revision ID: 20260722_0004
Revises: 20260720_0003
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260722_0004"
down_revision: str | None = "20260720_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE projects
        SET storage_path = id::text
        """
    )
    op.execute(
        """
        UPDATE dependency_runs
        SET project_path = project_id::text || '/source'
        """
    )
    op.execute(
        """
        UPDATE discovered_files AS discovered
        SET path = runs.project_id::text || substring(
            replace(discovered.path, chr(92), '/')
            FROM position(
                runs.project_id::text
                IN replace(discovered.path, chr(92), '/')
            ) + length(runs.project_id::text)
        )
        FROM dependency_runs AS runs
        WHERE discovered.run_id = runs.id
          AND position(
              runs.project_id::text
              IN replace(discovered.path, chr(92), '/')
          ) > 0
        """
    )


def downgrade() -> None:
    # The previous machine-specific root cannot be reconstructed safely.
    pass
