-- Database Migration for US002: User Login

CREATE TABLE IF NOT EXISTS tbl_user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_user_sessions_user_id ON tbl_user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_tbl_user_sessions_token ON tbl_user_sessions(token_hash);
