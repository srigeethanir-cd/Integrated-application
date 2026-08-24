-- Database Migration for US004: Account Lockout

CREATE TABLE IF NOT EXISTS tbl_user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT 'US004',
    user_id UUID UNIQUE NOT NULL,
    full_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    phone_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_user_profiles_user_id ON tbl_user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_tbl_user_profiles_story_key ON tbl_user_profiles(story_key);
