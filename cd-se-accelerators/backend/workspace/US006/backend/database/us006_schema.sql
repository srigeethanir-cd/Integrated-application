-- Database Migration for US006: Social Login

CREATE TABLE IF NOT EXISTS tbl_user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US006',
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_user_sessions_user_id ON tbl_user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_tbl_user_sessions_token_hash ON tbl_user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_tbl_user_sessions_story_key ON tbl_user_sessions(story_key);
