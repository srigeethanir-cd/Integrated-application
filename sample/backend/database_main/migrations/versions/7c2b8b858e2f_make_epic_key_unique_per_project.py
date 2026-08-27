"""make_epic_key_unique_per_project

Revision ID: 7c2b8b858e2f
Revises: 6f688358ebe7
Create Date: 2026-07-29 11:42:53.046522+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7c2b8b858e2f'
down_revision: Union[str, None] = '6f688358ebe7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop global unique index/constraint on epic_key
    op.drop_index('ix_epics_epic_key', table_name='epics')
    
    # Re-create as non-unique index on epic_key for lookups
    op.create_index(op.f('ix_epics_epic_key'), 'epics', ['epic_key'], unique=False)
    
    # Create composite unique constraint on (project_id, epic_key)
    op.create_unique_constraint('uq_epics_project_epic_key', 'epics', ['project_id', 'epic_key'])


def downgrade() -> None:
    # Remove composite constraint
    op.drop_constraint('uq_epics_project_epic_key', 'epics', type_='unique')
    
    # Drop non-unique index
    op.drop_index(op.f('ix_epics_epic_key'), table_name='epics')
    
    # Re-create global unique index
    op.create_index('ix_epics_epic_key', 'epics', ['epic_key'], unique=True)
