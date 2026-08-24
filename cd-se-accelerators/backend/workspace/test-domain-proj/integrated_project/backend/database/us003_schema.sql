-- Database Migration for US003: Forgot Password

CREATE TABLE IF NOT EXISTS tbl_password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US003',
    email VARCHAR(255) NOT NULL,
    reset_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_password_resets_email ON tbl_password_resets(email);
CREATE INDEX IF NOT EXISTS idx_tbl_password_resets_token ON tbl_password_resets(reset_token);
CREATE INDEX IF NOT EXISTS idx_tbl_password_resets_story_key ON tbl_password_resets(story_key);
