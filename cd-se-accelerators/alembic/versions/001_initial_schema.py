"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_name', sa.String(length=255), nullable=False),
        sa.Column('framework', sa.String(length=64), nullable=True),
        sa.Column('project_path', sa.String(length=1024), nullable=False),
        sa.Column('workspace_path', sa.String(length=1024), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('source_file_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. pipeline_runs
    op.create_table(
        'pipeline_runs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('current_stage', sa.String(length=128), nullable=False),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pipeline_runs_project_id', 'pipeline_runs', ['project_id'], unique=False)

    # 3. source_files
    op.create_table(
        'source_files',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_hash', sa.String(length=128), nullable=True),
        sa.Column('file_type', sa.String(length=64), nullable=True),
        sa.Column('analyzed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. components
    op.create_table(
        'components',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_file_id', sa.String(length=64), nullable=True),
        sa.Column('component_type', sa.String(length=128), nullable=True),
        sa.Column('framework', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_file_id'], ['source_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. test_cases
    op.create_table(
        'test_cases',
        sa.Column('id', sa.String(length=128), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('component_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('specification', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=128), nullable=True),
        sa.Column('priority', sa.String(length=64), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('expected_result', sa.Text(), nullable=True),
        sa.Column('source_function', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['components.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. test_files
    op.create_table(
        'test_files',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('component_id', sa.String(length=64), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('framework', sa.String(length=64), nullable=True),
        sa.Column('test_case_ids', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['components.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. test_executions
    op.create_table(
        'test_executions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('test_file_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('total_tests', sa.Integer(), nullable=True),
        sa.Column('passed', sa.Integer(), nullable=True),
        sa.Column('failed', sa.Integer(), nullable=True),
        sa.Column('skipped', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('pass_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_file_id'], ['test_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. test_results
    op.create_table(
        'test_results',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('execution_id', sa.String(length=64), nullable=False),
        sa.Column('test_case_id', sa.String(length=128), nullable=True),
        sa.Column('test_name', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('expected', sa.Text(), nullable=True),
        sa.Column('actual', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['test_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. coverage_reports
    op.create_table(
        'coverage_reports',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('statements', sa.Float(), nullable=True),
        sa.Column('branches', sa.Float(), nullable=True),
        sa.Column('functions', sa.Float(), nullable=True),
        sa.Column('lines', sa.Float(), nullable=True),
        sa.Column('coverage_status', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=False),
        sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
        sa.Column('total_tests', sa.Integer(), nullable=True),
        sa.Column('passed', sa.Integer(), nullable=True),
        sa.Column('failed', sa.Integer(), nullable=True),
        sa.Column('skipped', sa.Integer(), nullable=True),
        sa.Column('pass_rate', sa.Float(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('report_data', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('coverage_reports')
    op.drop_table('test_results')
    op.drop_table('test_executions')
    op.drop_table('test_files')
    op.drop_table('test_cases')
    op.drop_table('components')
    op.drop_table('source_files')
    op.drop_table('pipeline_runs')
    op.drop_table('projects')
