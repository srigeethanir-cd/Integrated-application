-- Database Migration for US-001: Feature Table

CREATE TABLE IF NOT EXISTS tbl_component (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US-001',
    name VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_component_story_key ON tbl_component(story_key);
