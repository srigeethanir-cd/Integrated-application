from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection, Engine


class DatabaseSchemaError(RuntimeError):
    """Raised when the database revision is incompatible with this application."""


class DatabaseSchemaOutdatedError(DatabaseSchemaError):
    def __init__(
        self, *, current_revision: str | None, expected_revision: str,
        required_revisions: tuple[str, ...],
    ) -> None:
        self.current_revision = current_revision
        self.expected_revision = expected_revision
        self.required_revisions = required_revisions
        current = current_revision or "<none>"
        required = " -> ".join(required_revisions) or expected_revision
        super().__init__(
            "Database schema is outdated. "
            f"Current Alembic revision: {current}. "
            f"Expected Alembic revision: {expected_revision}. "
            f"Required migration: {required}. Run 'alembic upgrade head'."
        )


@lru_cache
def _migration_script() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[2]
    config_path = backend_root / "alembic.ini"
    if not config_path.is_file():
        raise DatabaseSchemaError(
            f"Alembic configuration was not found at {config_path}."
        )
    config = Config(str(config_path))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


def expected_schema_revision() -> str:
    heads = _migration_script().get_heads()
    if len(heads) != 1:
        rendered = ", ".join(heads) or "<none>"
        raise DatabaseSchemaError(
            f"Expected one Alembic head, but discovered: {rendered}."
        )
    return heads[0]


def _required_revisions(current: str | None, expected: str) -> tuple[str, ...]:
    script = _migration_script()
    try:
        revisions = list(script.iterate_revisions(expected, current))
    except Exception as error:  # Alembic raises several graph-specific errors.
        raise DatabaseSchemaError(
            f"Database revision {current or '<none>'} is not connected to "
            f"application head {expected}."
        ) from error
    return tuple(revision.revision for revision in reversed(revisions))


def validate_database_schema(bind: Engine | Connection) -> None:
    expected = expected_schema_revision()
    if isinstance(bind, Engine):
        with bind.connect() as connection:
            current_heads = MigrationContext.configure(connection).get_current_heads()
    else:
        current_heads = MigrationContext.configure(bind).get_current_heads()

    if current_heads == (expected,):
        return
    if len(current_heads) > 1:
        current = ", ".join(current_heads)
        raise DatabaseSchemaError(
            f"Database has multiple Alembic heads ({current}); expected {expected}."
        )
    current = current_heads[0] if current_heads else None
    raise DatabaseSchemaOutdatedError(
        current_revision=current,
        expected_revision=expected,
        required_revisions=_required_revisions(current, expected),
    )
