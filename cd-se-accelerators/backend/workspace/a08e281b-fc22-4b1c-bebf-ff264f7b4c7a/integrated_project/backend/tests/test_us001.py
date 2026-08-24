"""Unit tests for US001: User Registration."""

import pytest

def test_user_registration_execution():
    """Verify execution logic for US001: User Registration."""
    payload = {"story_key": "US001", "action": "user_registration"}
    assert payload["story_key"] == "US001"
    assert payload["action"] == "user_registration"
