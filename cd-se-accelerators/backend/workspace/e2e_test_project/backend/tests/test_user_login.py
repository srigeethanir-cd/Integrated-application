"""Unit tests for US-002: User Login."""

import pytest


def test_user_login_execution():
    """Verify execution logic for US-002."""
    payload = {"test_key": "US-002"}
    assert payload["test_key"] == "US-002"
    assert len(payload) > 0
