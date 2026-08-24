-- Database Migration for US-003: User Profile View

CREATE TABLE IF NOT EXISTS tbl_user_profile_view (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US-003',
    name VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_user_profile_view_story_key ON tbl_user_profile_view(story_key);
