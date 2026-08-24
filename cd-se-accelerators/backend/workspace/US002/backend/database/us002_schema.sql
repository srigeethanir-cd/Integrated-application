-- Database Migration for US002: Remember Me

CREATE TABLE IF NOT EXISTS tbl_remember_me (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US002',
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_remember_me_status ON tbl_remember_me(status);
CREATE INDEX IF NOT EXISTS idx_tbl_remember_me_story_key ON tbl_remember_me(story_key);
