from unittest.mock import MagicMock, patch

import pytest

from app.database.schema_validation import (
    DatabaseSchemaOutdatedError,
    validate_database_schema,
)


def _connection_with_heads(*heads: str) -> MagicMock:
    connection = MagicMock()
    context = MagicMock()
    context.get_current_heads.return_value = heads
    return connection, context


def test_schema_validation_accepts_current_head() -> None:
    connection, context = _connection_with_heads("20260722_0005")
    with (
        patch("app.database.schema_validation.expected_schema_revision", return_value="20260722_0005"),
        patch("app.database.schema_validation.MigrationContext.configure", return_value=context),
    ):
        validate_database_schema(connection)


def test_schema_validation_reports_current_expected_and_required_revisions() -> None:
    connection, context = _connection_with_heads("20260720_0003")
    with (
        patch("app.database.schema_validation.expected_schema_revision", return_value="20260722_0005"),
        patch("app.database.schema_validation._required_revisions", return_value=("20260722_0004", "20260722_0005")),
        patch("app.database.schema_validation.MigrationContext.configure", return_value=context),
    ):
        with pytest.raises(DatabaseSchemaOutdatedError) as captured:
            validate_database_schema(connection)

    message = str(captured.value)
    assert "Current Alembic revision: 20260720_0003" in message
    assert "Expected Alembic revision: 20260722_0005" in message
    assert "20260722_0004 -> 20260722_0005" in message
