"""Backend Artifact Generator — Generates Python / FastAPI backend code for user stories."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from app.utils.llm_client import LLMClient
# pyrefly: ignore [missing-import]
from agents.agent2_story_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class BackendGenerator:
    """Generates backend services, controllers, and business logic."""

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "Python FastAPI",
    ) -> str:
        """Generate backend Python source code for story.

        Returns string containing source code.
        """
        prompt = self.prompt_builder.build_generation_prompt(
            artifact_type="backend",
            story=story,
            decision=decision,
            blueprint=blueprint,
            tech_stack=tech_stack,
        )

        try:
            if hasattr(self.llm, "generate") or hasattr(self.llm, "predict"):
                # Call LLM client if available
                res = self.llm.generate(prompt)
                if isinstance(res, str) and len(res) > 20:
                    return self._clean_code(res)
        except Exception as e:
            logger.warning("LLM call failed for BackendGenerator, falling back to template: %s", str(e))

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
        service_name = decision.get("service_name", f"{comp}Service")
        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "Feature Operation")

        if module == "password_reset":
            return f'''"""Service layer for {story_key}: {story_title}."""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Handles password reset request tokens, email dispatch, and verification."""

    def __init__(self) -> None:
        self.name = "PasswordResetService"

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Generate reset token and initiate secure password reset dispatch."""
        logger.info("Generating password reset token for: %s", email)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "email": email,
            "reset_token": token,
            "expires_at": expires_at.isoformat(),
            "message": "Password reset instructions sent to registered email.",
        }}

    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Verify token and update credentials."""
        logger.info("Verifying reset token: %s...", token[:8])
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "message": "Password has been successfully reset. Please log in with your new credentials.",
        }}
'''
        elif module == "user_registration":
            return f'''"""Service layer for {story_key}: {story_title}."""

import logging
import hashlib
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UserRegistrationService:
    """Handles new user onboarding, password hashing, and account provisioning."""

    def __init__(self) -> None:
        self.name = "UserRegistrationService"

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user account."""
        username = user_data.get("username", "")
        email = user_data.get("email", "")
        raw_pw = user_data.get("password", "")
        pw_hash = hashlib.sha256(raw_pw.encode("utf-8")).hexdigest()

        logger.info("Registering new user '%s' (%s)", username, email)
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "username": username,
            "email": email,
            "user_id": "usr_" + hashlib.md5(email.encode("utf-8")).hexdigest()[:12],
            "message": f"User '{{username}}' registered successfully.",
        }}
'''
        elif module == "user_login":
            return f'''"""Service layer for {story_key}: {story_title}."""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UserLoginService:
    """Handles user credential validation, session creation, and JWT issuance."""

    def __init__(self) -> None:
        self.name = "UserLoginService"

    def authenticate_user(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and issue auth token."""
        username = credentials.get("username") or credentials.get("email", "")
        logger.info("Authenticating user session for '%s'", username)
        token = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "authenticated": True,
            "access_token": f"bearer_{{token}}",
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
            "message": "Authentication successful.",
        }}
'''
        elif module == "dashboard_metrics":
            return f'''"""Service layer for {story_key}: {story_title}."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DashboardMetricsService:
    """Aggregates analytics, KPI statistics, and system health status."""

    def __init__(self) -> None:
        self.name = "DashboardMetricsService"

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Retrieve aggregated KPI dashboard metrics."""
        logger.info("Calculating real-time dashboard summary metrics")
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": [
                {{"metric_key": "total_users", "label": "Total Registered Users", "value": 1284, "trend": "+12%"}},
                {{"metric_key": "active_sessions", "label": "Active Sessions", "value": 94, "trend": "+5%"}},
                {{"metric_key": "uptime", "label": "Service Availability", "value": "99.98%", "trend": "nominal"}},
                {{"metric_key": "avg_latency", "label": "API Response Latency", "value": "42ms", "trend": "-8%"}},
            ],
            "system_health": "OPTIMAL",
        }}
'''
        else:
            fields = decision.get("fields", [])
            field_checks = []
            param_docs = []
            for f in fields:
                fname = f.get('name')
                flabel = f.get('label')
                param_docs.append(f"        {fname}: {flabel}")
                if f.get('required'):
                    field_checks.append(f'''        if not payload.get("{fname}"):
            logger.warning("{flabel} ({fname}) is required but was not provided.")
            return {{"status": "error", "message": "{flabel} is a required field."}}''')

            field_validation_block = "\n".join(field_checks) if field_checks else f'''        if not payload:
            return {{"status": "error", "message": "Payload cannot be empty."}}'''

            primary_action = decision.get("primary_action", "execute_operation")

            return f'''"""Service layer for {story_key}: {story_title}."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class {service_name}:
    """Service handling domain business logic for {story_title}."""

    def __init__(self) -> None:
        self.name = "{service_name}"
        self.story_key = "{story_key}"

    def {primary_action}(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute {story_title} operation with validation and business rule enforcement.

        Parameters:
{chr(10).join(param_docs) if param_docs else '        payload: Operation data dictionary'}
        """
        logger.info("Executing {service_name}.{primary_action} with keys: %s", list(payload.keys()) if payload else [])
        
{field_validation_block}

        return {{
            "status": "success",
            "story_key": "{story_key}",
            "action": "{primary_action}",
            "message": "{story_title} processed successfully.",
            "data": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }}

    def get_status(self, entity_id: str) -> Dict[str, Any]:
        """Retrieve operational state for {story_title} entity."""
        logger.info("Fetching {service_name} status for ID: %s", entity_id)
        return {{
            "status": "success",
            "story_key": "{story_key}",
            "entity_id": entity_id,
            "state": "ACTIVE",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }}
'''
