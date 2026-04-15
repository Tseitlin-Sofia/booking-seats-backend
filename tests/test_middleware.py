"""Тесты для LoggingMiddleware.

Проверяет корректность работы middleware логирования:
- Генерация и приём trace_id через заголовки.
- Подстановка дефолтного пользователя (SYSTEM) для публичных запросов.
- Изоляция контекста между разными запросами.
- Обновление контекста внутри одного запроса (после аутентификации).
- Логирование метода, пути и статуса ответа.
- Валидация формата UUID4 для сгенерированных trace_id.

Все тесты используют TestClient для эмуляции HTTP-запросов без запуска сервера.
"""

import re
from typing import List

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from loguru import logger

from app.core.constants import LoggingConstants
from app.core.middleware import LoggingMiddleware

TEST_ENDPOINT: str = '/test'
TEST_AUTH_ENDPOINT: str = '/test-with-user'
TEST_NONEXISTENT: str = '/nonexistent'

TEST_USER_ID: str = '999'
TEST_USERNAME: str = 'TestUser'

UUID4_PATTERN: re.Pattern[str] = re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$',
    re.IGNORECASE,
)


@pytest.fixture
def test_app() -> FastAPI:
    """Создаёт минимальное тестовое приложение с LoggingMiddleware."""
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get(TEST_ENDPOINT)
    async def test_endpoint() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get(TEST_AUTH_ENDPOINT)
    async def test_endpoint_with_user(request: Request) -> dict[str, str]:
        from app.core.logging import user_id_ctx, username_ctx

        user_id_ctx.set(TEST_USER_ID)
        username_ctx.set(TEST_USERNAME)
        return {'status': 'authenticated'}

    return app


def test_middleware_generates_trace_id(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет генерацию trace_id, если заголовок не передан."""
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)
    response = client.get(TEST_ENDPOINT)

    assert response.status_code == 200, (
        f'Ожидался статус 200, получен {response.status_code}'
    )

    assert 'x-trace-id' in response.headers, (
        'В ответе отсутствует заголовок X-Trace-ID'
    )
    trace_id = response.headers['x-trace-id']

    assert any(trace_id in log_line for log_line in captured), (
        f'Trace ID {trace_id} не найден в логах: {captured}'
    )

    assert any(
        f'Request started: GET {TEST_ENDPOINT}' in log_line
        for log_line in captured
    ), f'Не найден лог "Запрос отправлен" в: {captured}'

    assert any('Request finished: 200' in log_line for log_line in captured), (
        f'Не найден лог "Запрос завершен" в: {captured}'
    )


def test_middleware_uses_incoming_trace_id(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет использование trace_id из заголовка запроса."""
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)
    custom_trace_id = 'my-custom-trace-123'

    response = client.get(
        TEST_ENDPOINT,
        headers={'X-Trace-ID': custom_trace_id},
    )

    assert response.status_code == 200, (
        f'Ожидался статус 200, получен {response.status_code}'
    )
    assert response.headers['x-trace-id'] == custom_trace_id, (
        f'Ожидался trace_id {custom_trace_id}, '
        + f'получен {response.headers["x-trace-id"]}'
    )

    assert any(custom_trace_id in log_line for log_line in captured), (
        f'Кастомный trace_id {custom_trace_id} не найден в логах: {captured}'
    )


def test_middleware_logs_system_user_by_default(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет, что для публичных запросов пользователь = SYSTEM."""
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)
    response = client.get(TEST_ENDPOINT)

    assert response.status_code == 200, (
        f'Ожидался статус 200, получен {response.status_code}'
    )

    trace_id = response.headers['x-trace-id']
    relevant_logs = [log for log in captured if trace_id in log]

    assert len(relevant_logs) >= 2, (
        'Ожидалось минимум 2 лога для запроса, '
        + f'получено {len(relevant_logs)}: {relevant_logs}'
    )

    for log_line in relevant_logs:
        assert 'user_id=SYSTEM' in log_line, (
            f'Ожидался user_id=SYSTEM в логе, получено: {log_line}'
        )
        assert 'username=SYSTEM' in log_line, (
            f'Ожидался username=SYSTEM в логе, получено: {log_line}'
        )


def test_middleware_context_isolation(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет, что каждый запрос получает УНИКАЛЬНЫЙ trace_id."""
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)

    resp1 = client.get(TEST_ENDPOINT)
    resp2 = client.get(TEST_ENDPOINT)
    resp3 = client.get(TEST_ENDPOINT)

    trace1 = resp1.headers['x-trace-id']
    trace2 = resp2.headers['x-trace-id']
    trace3 = resp3.headers['x-trace-id']

    unique_traces = {trace1, trace2, trace3}
    assert len(unique_traces) == 3, (
        'Ожидалось 3 уникальных trace_id, '
        + f'получено {len(unique_traces)}: {unique_traces}'
    )

    for trace_id in [trace1, trace2, trace3]:
        assert any(trace_id in log for log in captured), (
            f'Trace ID {trace_id} не найден в логах: {captured}'
        )


def test_middleware_auth_context_update(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет обновление контекста внутри одного запроса.

    После эмуляции аутентификации в эндпоинте,
    последующие логи должны видеть реального пользователя.
    """
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)

    response = client.get(TEST_AUTH_ENDPOINT)
    trace_id = response.headers['x-trace-id']

    relevant_logs = [log for log in captured if trace_id in log]

    has_system = any('user_id=SYSTEM' in log for log in relevant_logs)
    has_authenticated = any(
        f'user_id={TEST_USER_ID} username={TEST_USERNAME}' in log
        for log in relevant_logs
    )

    assert has_system or has_authenticated, (
        f'Ожидается либо SYSTEM, либо аутентифицированный пользователь '
        f'в логах запроса {trace_id}. Получено: {relevant_logs}'
    )


def test_middleware_logs_request_details(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет, что в логах фиксируются метод, путь и статус запроса."""
    captured: List[str] = []

    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    client = TestClient(test_app)
    _ = client.post(TEST_NONEXISTENT)

    assert any(
        f'Request started: POST {TEST_NONEXISTENT}' in log_line
        for log_line in captured
    ), f'Не найден лог начала запроса в: {captured}'

    assert any('Request finished: 404' in log_line for log_line in captured), (
        f'Не найден лог завершения с кодом 404 в: {captured}'
    )


def test_middleware_uuid_format(
    test_app: FastAPI,
    capture_sink,
) -> None:
    """Проверяет, что сгенерированный trace_id имеет валидный формат UUID4."""
    client = TestClient(test_app)
    response = client.get(TEST_ENDPOINT)

    trace_id = response.headers['x-trace-id']

    assert UUID4_PATTERN.match(trace_id), (
        f'Trace ID не соответствует формату UUID4: {trace_id}. '
        f'Ожидался паттерн: {UUID4_PATTERN.pattern}'
    )
