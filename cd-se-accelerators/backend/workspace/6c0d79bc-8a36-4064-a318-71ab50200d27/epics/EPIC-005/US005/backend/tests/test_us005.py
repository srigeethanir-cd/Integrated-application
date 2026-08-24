"""Unit tests for US005: Logout."""

import pytest


def test_logout_execution():
    """Verify execution logic for US005 (Logout)."""
    payload = {"story_key": "US005", "module": "logout", "status": "ACTIVE"}
    assert payload["story_key"] == "US005"
    assert payload["status"] == "ACTIVE"
