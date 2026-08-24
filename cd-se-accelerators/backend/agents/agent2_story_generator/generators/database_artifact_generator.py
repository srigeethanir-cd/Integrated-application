"""Database Artifact Generator — Generates SQL migration & schema scripts for user stories."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from app.utils.llm_client import LLMClient
# pyrefly: ignore [missing-import]
from agents.agent2_story_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class DatabaseArtifactGenerator:
    """Generates database schema DDL & migration scripts."""

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "PostgreSQL",
    ) -> str:
        """Generate SQL schema script for story."""
        prompt = self.prompt_builder.build_generation_prompt(
            artifact_type="database",
            story=story,
            decision=decision,
            blueprint=blueprint,
            tech_stack=tech_stack,
        )

        try:
            if hasattr(self.llm, "generate") or hasattr(self.llm, "predict"):
                res = self.llm.generate(prompt)
                if isinstance(res, str) and len(res) > 20:
                    return self._clean_code(res)
        except Exception as e:
            logger.warning("LLM call failed for DatabaseArtifactGenerator, falling back to template: %s", str(e))

        return self._generate_fallback(story, decision)

    @staticmethod
    def _clean_code(raw: str) -> str:
        if "```sql" in raw:
            return raw.split("```sql")[1].split("```")[0].strip()
        elif "```" in raw:
            return raw.split("```")[1].split("```")[0].strip()
        return raw.strip()

    @staticmethod
    def _generate_fallback(story: Dict[str, Any], decision: Dict[str, Any]) -> str:
        module = decision.get("module_name", "feature")
        table_name = decision.get("table_name", f"tbl_{module}")
        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "Feature Table")

        if module == "password_reset":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    email VARCHAR(255) NOT NULL,
    reset_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_email ON {table_name}(email);
CREATE INDEX IF NOT EXISTS idx_{table_name}_token ON {table_name}(reset_token);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        elif module == "user_registration":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_username ON {table_name}(username);
CREATE INDEX IF NOT EXISTS idx_{table_name}_email ON {table_name}(email);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        elif module == "user_login":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id);
CREATE INDEX IF NOT EXISTS idx_{table_name}_token_hash ON {table_name}(token_hash);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        elif module == "dashboard_metrics":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    metric_key VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    category VARCHAR(100) NOT NULL,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_metric_key ON {table_name}(metric_key);
CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(category);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        elif module == "user_profile":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    user_id UUID UNIQUE NOT NULL,
    full_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    phone_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        elif module == "order_management":
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    customer_id UUID NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    order_status VARCHAR(50) DEFAULT 'PENDING',
    items_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_customer_id ON {table_name}(customer_id);
CREATE INDEX IF NOT EXISTS idx_{table_name}_order_status ON {table_name}(order_status);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
        else:
            return f'''-- Database Migration for {story_key}: {story_title}

CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_key VARCHAR(50) NOT NULL DEFAULT '{story_key}',
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status);
CREATE INDEX IF NOT EXISTS idx_{table_name}_story_key ON {table_name}(story_key);
'''
