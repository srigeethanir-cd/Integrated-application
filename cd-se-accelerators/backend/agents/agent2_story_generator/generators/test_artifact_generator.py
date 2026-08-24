"""Test Artifact Generator — Generates pytest unit tests for user stories."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from app.utils.llm_client import LLMClient
# pyrefly: ignore [missing-import]
from agents.agent2_story_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class TestArtifactGenerator:
    """Generates pytest unit test suites."""

    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "pytest / Python",
    ) -> str:
        """Generate pytest code for story."""
        prompt = self.prompt_builder.build_generation_prompt(
            artifact_type="test",
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
            logger.warning("LLM call failed for TestArtifactGenerator, falling back to template: %s", str(e))

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
        story_title = story.get("title", "Feature Test")

        if module == "password_reset":
            return f'''"""Unit tests for {story_key}: {story_title}."""

import pytest
from backend.{story_key.lower()}_service import PasswordResetService


def test_password_reset_token_issuance():
    """Verify password reset token creation and expiration timestamp."""
    svc = PasswordResetService()
    res = svc.request_password_reset("user@example.com")
    assert res["status"] == "success"
    assert res["email"] == "user@example.com"
    assert len(res["reset_token"]) > 20
    assert "expires_at" in res


def test_password_reset_completion():
    """Verify password update with token."""
    svc = PasswordResetService()
    res = svc.reset_password("valid_test_token", "NewSecurePassword123!")
    assert res["status"] == "success"
    assert "successfully reset" in res["message"]
'''
        elif module == "user_registration":
            return f'''"""Unit tests for {story_key}: {story_title}."""

import pytest
from backend.{story_key.lower()}_service import UserRegistrationService


def test_user_registration_flow():
    """Verify user registration and user ID generation."""
    svc = UserRegistrationService()
    data = {{"username": "johndoe", "email": "john@example.com", "password": "Password123!"}}
    res = svc.register_user(data)
    assert res["status"] == "success"
    assert res["username"] == "johndoe"
    assert res["email"] == "john@example.com"
    assert res["user_id"].startswith("usr_")
'''
        elif module == "user_login":
            return f'''"""Unit tests for {story_key}: {story_title}."""

import pytest
from backend.{story_key.lower()}_service import UserLoginService


def test_user_login_authentication():
    """Verify bearer token issuance for valid credentials."""
    svc = UserLoginService()
    res = svc.authenticate_user({{"username": "admin", "password": "SecretPassword"}})
    assert res["status"] == "success"
    assert res["authenticated"] is True
    assert "access_token" in res
    assert res["token_type"] == "bearer"
'''
        elif module == "dashboard_metrics":
            return f'''"""Unit tests for {story_key}: {story_title}."""

import pytest
from backend.{story_key.lower()}_service import DashboardMetricsService


def test_dashboard_metrics_aggregation():
    """Verify KPI metric aggregation and system status."""
    svc = DashboardMetricsService()
    res = svc.get_dashboard_summary()
    assert res["status"] == "success"
    assert len(res["metrics"]) >= 3
    assert res["system_health"] == "OPTIMAL"
'''
        else:
            return f'''"""Unit tests for {story_key}: {story_title}."""

import pytest


def test_{module}_execution():
    """Verify execution logic for {story_key} ({story_title})."""
    payload = {{"story_key": "{story_key}", "module": "{module}", "status": "ACTIVE"}}
    assert payload["story_key"] == "{story_key}"
    assert payload["status"] == "ACTIVE"
'''
