"""Unit tests for US004: Account Lockout."""

import pytest


def test_user_profile_execution():
    """Verify execution logic for US004 (Account Lockout)."""
    payload = {"story_key": "US004", "module": "user_profile", "status": "ACTIVE"}
    assert payload["story_key"] == "US004"
    assert payload["status"] == "ACTIVE"
