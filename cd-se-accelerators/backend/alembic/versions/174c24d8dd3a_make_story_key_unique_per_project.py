"""make_story_key_unique_per_project

Revision ID: 174c24d8dd3a
Revises: 7c2b8b858e2f
Create Date: 2026-07-29 12:50:45.443056+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
# pyrefly: ignore [missing-module-attribute]
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '174c24d8dd3a'
down_revision: Union[str, None] = '7c2b8b858e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop global unique index on user_stories(story_key)
    op.drop_index('ix_user_stories_story_key', table_name='user_stories')
    
    # Re-create as non-unique index for lookups
    op.create_index(op.f('ix_user_stories_story_key'), 'user_stories', ['story_key'], unique=False)
    
    # Create composite unique constraint on (project_id, story_key)
    op.create_unique_constraint('uq_user_stories_project_story_key', 'user_stories', ['project_id', 'story_key'])


def downgrade() -> None:
    # Drop composite unique constraint
    op.drop_constraint('uq_user_stories_project_story_key', 'user_stories', type_='unique')
    
    # Drop non-unique index
    op.drop_index(op.f('ix_user_stories_story_key'), table_name='user_stories')
    
    # Re-create global unique index
    op.create_index('ix_user_stories_story_key', 'user_stories', ['story_key'], unique=True)
