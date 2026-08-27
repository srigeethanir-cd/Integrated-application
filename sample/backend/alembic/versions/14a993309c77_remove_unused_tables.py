"""remove_unused_tables

Revision ID: 14a993309c77
Revises: a79a1da1c294
Create Date: 2026-07-30 12:59:48.667350+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
# pyrefly: ignore [missing-module-attribute]
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '14a993309c77'
down_revision: Union[str, None] = 'a79a1da1c294'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unused/dead tables
    op.drop_table('merge_queue_records')
    op.drop_table('migration_plans')
    op.drop_table('releases')
    op.drop_table('visualizations')
    op.drop_table('workspace_registries')
    op.drop_table('traceability_nodes')
    op.drop_table('traceability_edges')
    op.drop_table('traceability_audit_logs')


def downgrade() -> None:
    # Recreate the dropped tables
    op.create_table('traceability_audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('story_key', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('impacted_nodes_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('traceability_edges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_node_key', sa.String(length=100), nullable=False),
        sa.Column('target_node_key', sa.String(length=100), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('traceability_nodes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('node_key', sa.String(length=100), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workspace_registries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=False),
        sa.Column('workspace_root', sa.String(length=500), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('visualizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=False),
        sa.Column('story_key', sa.String(length=50), nullable=True),
        sa.Column('visualization_type', sa.String(length=100), nullable=False),
        sa.Column('preview_url', sa.String(length=500), nullable=True),
        sa.Column('project_tree_json', sa.JSON(), nullable=True),
        sa.Column('er_diagram_json', sa.JSON(), nullable=True),
        sa.Column('component_graph_json', sa.JSON(), nullable=True),
        sa.Column('api_graph_json', sa.JSON(), nullable=True),
        sa.Column('viz_json', sa.JSON(), nullable=True),
        sa.Column('preview_assets_json', sa.JSON(), nullable=True),
        sa.Column('url_map_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('releases',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('archive_path', sa.String(length=500), nullable=False),
        sa.Column('checksum', sa.String(length=255), nullable=False),
        sa.Column('export_status', sa.String(length=50), nullable=True),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('manifest_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('migration_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=False),
        sa.Column('migration_plan_json', sa.JSON(), nullable=True),
        sa.Column('execution_order_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('merge_queue_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=False),
        sa.Column('story_key', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_log', sa.String(length=2000), nullable=True),
        sa.Column('rollback_checkpoint_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
