"""Unit tests for US006: Social Login."""

import pytest
from backend.us006_service import UserLoginService


def test_user_login_authentication():
    """Verify bearer token issuance for valid credentials."""
    svc = UserLoginService()
    res = svc.authenticate_user({"username": "admin", "password": "SecretPassword"})
    assert res["status"] == "success"
    assert res["authenticated"] is True
    assert "access_token" in res
    assert res["token_type"] == "bearer"
