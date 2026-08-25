from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.database.models.code_understanding import CodeUnderstandingRun
from app.database.retry import is_transient_database_error
from app.database.repositories.code_understanding_repository import (
    CodeUnderstandingRepository,
)
from app.database.session import engine


def _run() -> CodeUnderstandingRun:
    return CodeUnderstandingRun(
        id=uuid4(),
        project_id=uuid4(),
        dependency_run_id=uuid4(),
        model_name="model",
        prompt_version="prompt",
    )


def test_neon_pool_configuration_avoids_stale_connections() -> None:
    assert engine.pool._recycle == 300
    assert engine.pool._timeout == 30
    assert engine.pool.size() == 5
    assert engine.pool._max_overflow == 5


def test_transient_operational_error_rolls_back_disposes_and_retries() -> None:
    session = MagicMock(spec=Session)
    session.commit.side_effect = [
        OperationalError("commit", {}, ConnectionResetError()),
        None,
    ]
    bind = MagicMock()
    bind.engine = bind
    session.get_bind.return_value = bind
    run = _run()

    with patch(
        "app.database.repositories.code_understanding_repository.time.sleep"
    ) as sleep:
        CodeUnderstandingRepository(session).mark_running(run)

    assert session.commit.call_count == 2
    session.rollback.assert_called_once_with()
    bind.dispose.assert_called_once_with(close=False)
    sleep.assert_called_once_with(0.1)


def test_integrity_error_is_not_retried() -> None:
    session = MagicMock(spec=Session)
    error = IntegrityError("commit", {}, ValueError("duplicate"))
    session.commit.side_effect = error

    with pytest.raises(IntegrityError):
        CodeUnderstandingRepository(session).mark_running(_run())

    session.commit.assert_called_once_with()
    session.rollback.assert_called_once_with()
    session.get_bind.assert_not_called()


def test_retry_is_bounded_to_three_attempts() -> None:
    session = MagicMock(spec=Session)
    session.commit.side_effect = OperationalError(
        "commit", {}, ConnectionResetError()
    )
    bind = MagicMock()
    bind.engine = bind
    session.get_bind.return_value = bind

    with patch(
        "app.database.repositories.code_understanding_repository.time.sleep"
    ), pytest.raises(OperationalError):
        CodeUnderstandingRepository(session).mark_running(_run())

    assert session.commit.call_count == 4
    assert session.rollback.call_count == 4
    assert bind.dispose.call_count == 3


def test_dns_and_network_interruptions_are_transient() -> None:
    assert is_transient_database_error(
        OSError("temporary failure in name resolution")
    )
