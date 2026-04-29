from typing import Any, Callable, Generator, List

import pytest
from loguru import logger

from app.core.logging import (
    setup_logging,
    trace_id_ctx,
    user_id_ctx,
    username_ctx,
)

SinkCallback = Callable[[Any], None]
SinkType = Callable[[List[str]], SinkCallback]


@pytest.fixture
def capture_sink() -> SinkType:
    """Возвращает фабрику для создания хендлера, перехватывающего логи."""

    def _create(captured: List[str]) -> SinkCallback:
        def sink(message: Any) -> None:
            captured.append(str(message).rstrip())

        return sink

    return _create


@pytest.fixture(autouse=True)
def setup_test_logging() -> Generator[None, None, None]:
    """Настраивает логирование для тестов и восстанавливает после."""
    default_trace = trace_id_ctx.get()
    default_user = user_id_ctx.get()
    default_username = username_ctx.get()

    logger.remove()
    setup_logging(env='dev', log_level='INFO')

    yield

    logger.remove()
    trace_id_ctx.set(default_trace)
    user_id_ctx.set(default_user)
    username_ctx.set(default_username)
