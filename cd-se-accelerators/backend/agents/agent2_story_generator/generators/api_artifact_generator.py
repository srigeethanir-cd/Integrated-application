"""API Artifact Generator — Generates FastAPI router and API endpoints for user stories."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from app.utils.llm_client import LLMClient
# pyrefly: ignore [missing-import]
from agents.agent2_story_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class APIArtifactGenerator:
    """Generates FastAPI router endpoints for user stories."""

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "FastAPI / Python",
    ) -> str:
        """Generate FastAPI route definitions."""
        prompt = self.prompt_builder.build_generation_prompt(
            artifact_type="api",
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
            logger.warning("LLM call failed for APIArtifactGenerator, falling back to template: %s", str(e))

        return self._generate_fallback(story, decision)

    @staticmethod
    def _clean_code(raw: str) -> str:
        if "```python" in raw:
            return raw.split("```python")[1].split("```")[0].strip()
        elif "```" in raw:
            return raw.split("```")[1].split("```")[0].strip()
        return raw.strip()

    @staticmethod
    def _generate_fallback(story: Dict[str, Any], decision: Dict[str, Any]) -> str:
        module = decision.get("module_name", "feature")
        comp = decision.get("component_name", "Feature")
        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "Feature Endpoint")

        if module == "password_reset":
            return f'''"""FastAPI Router for {story_key}: {story_title}."""

from pydantic import BaseModel, EmailStr, Field
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Registered user email address")


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="Password reset verification token")
    new_password: str = Field(..., min_length=8, description="New secure password")


@router.post("/request", status_code=status.HTTP_200_OK)
def request_password_reset(payload: ForgotPasswordRequest) -> Dict[str, Any]:
    """Initiate password recovery by sending a reset link/token."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "email": payload.email,
        "message": f"Password reset instructions have been dispatched to {{payload.email}}.",
    }}


@router.post("/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(payload: ResetPasswordRequest) -> Dict[str, Any]:
    """Verify reset token and update account password."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "message": "Password updated successfully. You can now log in.",
    }}
'''
        elif module == "user_registration":
            return f'''"""FastAPI Router for {story_key}: {story_title}."""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/users", tags=["User Registration"])


class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Valid user email")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user_endpoint(payload: UserRegistrationRequest) -> Dict[str, Any]:
    """Register a new user account."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "username": payload.username,
        "email": payload.email,
        "message": f"User account '{{payload.username}}' created successfully.",
    }}
'''
        elif module == "user_login":
            return f'''"""FastAPI Router for {story_key}: {story_title}."""

from pydantic import BaseModel, Field
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or Email")
    password: str = Field(..., description="Account password")


@router.post("/login", status_code=status.HTTP_200_OK)
def login_endpoint(payload: UserLoginRequest) -> Dict[str, Any]:
    """Authenticate user credentials and return access session."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "authenticated": True,
        "token_type": "bearer",
        "message": f"User '{{payload.username}}' authenticated successfully.",
    }}
'''
        elif module == "dashboard_metrics":
            return f'''"""FastAPI Router for {story_key}: {story_title}."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/dashboard", tags=["Dashboard Metrics"])


@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_dashboard_metrics() -> Dict[str, Any]:
    """Retrieve system KPIs and metric summaries."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "metrics": [
            {{"key": "users", "label": "Total Users", "value": 1284}},
            {{"key": "active", "label": "Active Sessions", "value": 94}},
            {{"key": "health", "label": "System Health", "value": "99.98%"}},
        ],
    }}
'''
        else:
            return f'''"""FastAPI Router for {story_key}: {story_title}."""

from typing import Any, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/{module}", tags=["{comp}"])


class {comp}Request(BaseModel):
    action: str = Field(default="execute", description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)


@router.post("/execute", status_code=status.HTTP_200_OK)
def execute_{module}_endpoint(payload: {comp}Request) -> Dict[str, Any]:
    """Execute API endpoint for {story_title}."""
    return {{
        "status": "success",
        "story_key": "{story_key}",
        "action": payload.action,
        "received": payload.parameters,
        "message": "{story_title} executed successfully.",
    }}
'''
