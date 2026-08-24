-- Database Migration for US001: User Registration

CREATE TABLE IF NOT EXISTS tbl_user_registration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US001',
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_user_registration_story_key ON tbl_user_registration(story_key);
