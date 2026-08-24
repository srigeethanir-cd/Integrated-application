"""Unit tests for US003: Forgot Password."""

import pytest
from backend.us003_service import PasswordResetService


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
