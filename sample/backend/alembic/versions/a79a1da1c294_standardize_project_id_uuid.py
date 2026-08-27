"""standardize_project_id_uuid

Revision ID: a79a1da1c294
Revises: 174c24d8dd3a
Create Date: 2026-07-30 09:58:50.721404+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a79a1da1c294'
down_revision: Union[str, None] = '174c24d8dd3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.dialects import postgresql
    
    tables_to_clean = [
        'generated_files',
        'story_dependencies',
        'execution_logs',
        'project_validations',
        'final_governance_audits',
        'rollback_history_records',
        'prompt_execution_logs',
        'workflow_execution_sessions',
        'artifacts'
    ]
    
    # 1. Delete legacy rows with invalid UUID format
    for table in tables_to_clean:
        op.execute(
            f"DELETE FROM {table} WHERE project_id IS NOT NULL AND "
            f"project_id !~ '^[a-fA-F0-9]{{8}}-[a-fA-F0-9]{{4}}-[a-fA-F0-9]{{4}}-[a-fA-F0-9]{{4}}-[a-fA-F0-9]{{12}}$'"
        )
    
    # 2. Alter column types to UUID
    op.alter_column('generated_files', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
    
    op.alter_column('story_dependencies', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('execution_logs', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('project_validations', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('final_governance_audits', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('rollback_history_records', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('prompt_execution_logs', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('workflow_execution_sessions', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    op.alter_column('artifacts', 'project_id',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='project_id::uuid')
                    
    # 3. Delete orphaned rows (referencing deleted projects)
    for table in tables_to_clean:
        op.execute(
            f"DELETE FROM {table} WHERE project_id IS NOT NULL AND "
            f"project_id NOT IN (SELECT project_id FROM projects)"
        )
                    
    # 4. Add foreign key constraints to projects.project_id
    op.create_foreign_key('fk_generated_files_project_id', 'generated_files', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_story_dependencies_project_id', 'story_dependencies', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_execution_logs_project_id', 'execution_logs', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_project_validations_project_id', 'project_validations', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_final_governance_audits_project_id', 'final_governance_audits', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_rollback_history_records_project_id', 'rollback_history_records', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_prompt_execution_logs_project_id', 'prompt_execution_logs', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workflow_execution_sessions_project_id', 'workflow_execution_sessions', 'projects', ['project_id'], ['project_id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('fk_workflow_execution_sessions_project_id', 'workflow_execution_sessions', type_='foreignkey')
    op.drop_constraint('fk_prompt_execution_logs_project_id', 'prompt_execution_logs', type_='foreignkey')
    op.drop_constraint('fk_rollback_history_records_project_id', 'rollback_history_records', type_='foreignkey')
    op.drop_constraint('fk_final_governance_audits_project_id', 'final_governance_audits', type_='foreignkey')
    op.drop_constraint('fk_project_validations_project_id', 'project_validations', type_='foreignkey')
    op.drop_constraint('fk_execution_logs_project_id', 'execution_logs', type_='foreignkey')
    op.drop_constraint('fk_story_dependencies_project_id', 'story_dependencies', type_='foreignkey')
    op.drop_constraint('fk_generated_files_project_id', 'generated_files', type_='foreignkey')

    # Convert project_id back to String/VARCHAR
    op.alter_column('artifacts', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('workflow_execution_sessions', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('prompt_execution_logs', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('rollback_history_records', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('final_governance_audits', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('project_validations', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('execution_logs', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('story_dependencies', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
                    
    op.alter_column('generated_files', 'project_id',
                    type_=sa.String(255),
                    postgresql_using='project_id::varchar')
