# src/app/core/middleware.py
"""Middleware для логирования и трассировки запросов.

Обеспечивает генерацию trace_id, установку контекста пользователя
и логирование жизненного цикла каждого HTTP-запроса.
"""

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.constants import LoggingConstants
from app.core.logging import (
    get_logger,
    trace_id_ctx,
    user_id_ctx,
    username_ctx,
)

CallNext = Callable[[Request], Awaitable[Response]]


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для сквозного логирования запросов.

    Выполняет следующие функции:
    1. Генерирует или принимает из заголовков уникальный trace_id.
    2. Инициализирует контекст пользователя значениями по умолчанию (SYSTEM).
    3. Логирует начало и завершение обработки запроса с метаданными.
    4. Возвращает trace_id в заголовках ответа для отладки на клиенте.

    Все логи автоматически обогащаются контекстными переменными.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: CallNext,
    ) -> Response:
        """Обработка входящего запроса: логирование и управление контекстом.

        1. Извлекает или генерирует trace_id для идентификации запроса.
        2. Сбрасывает контекст пользователя на значения по умолчанию (SYSTEM).
        3. Логирует старт запроса: метод, путь.
        4. Вызывает следующую обработку в цепочке.
        5. Добавляет trace_id в заголовки ответа.
        6. Логирует завершение запроса со статус кодом.

        Args:
            request: Входящий объект Request от FastAPI.
            call_next: Функция для передачи управления следующему обработчику.

        Returns:
            Response: Объект ответа, который будет отправлен клиенту.

        """
        if request.url.path in LoggingConstants.NOISE_ENDPOINTS:
            return await call_next(request)

        trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
        trace_id_ctx.set(trace_id)

        user_id_ctx.set('SYSTEM')
        username_ctx.set('SYSTEM')

        logger = get_logger()
        logger.info(
            f'Отправлен запрос: {request.method} {request.url.path}',
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers['X-Trace-ID'] = trace_id

        logger.info(
            f'Запрос выполнен: {response.status_code}'
            + f' ({duration_ms}ms) | {request.method} {request.url.path}',
        )
        if duration_ms > 1000:
            logger.warning(
                'Медленный запрос: '
                + f'{duration_ms}ms | {request.method} {request.url.path}',
            )
        return response
