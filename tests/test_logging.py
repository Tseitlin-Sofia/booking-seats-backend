"""Тесты для модуля централизованного логирования.

Проверяет корректность работы системы логирования на базе loguru:
- Форматирование логов в dev/prod режимах.
- Изоляцию контекстных переменных (trace_id, user_id, username).
- Перехват логов от стандартной библиотеки logging (InterceptHandler).
- Обработку исключений с сохранением трейсбека.
- Создание файлов логов с ротацией в dev-режиме.
- Отсутствие цветов в prod-режиме.

Все тесты используют фикстуры для изоляции состояния loguru и contextvars,
что гарантирует стабильность при параллельном запуске.
"""

import logging
import re
import time
from typing import List

from loguru import logger

from app.core.constants import LoggingConstants
from app.core.logging import (
    get_logger,
    setup_logging,
    trace_id_ctx,
    user_id_ctx,
    username_ctx,
)

from .conftest import SinkType

LOG_WRITE_DELAY_SEC = 0.3

LOG_STRUCTURE_PATTERN: re.Pattern[str] = re.compile(
    r'^'  # Начало строки
    r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| '  # Время
    r'\w+\s+\| '  # Уровень (INFO, ERROR...)
    r'trace_id=\S+ \| '  # trace_id (любое непустое)
    r'user_id=\S+ username=\S+ \| '  # user_id и username
    r'.+'  # Сообщение (любое)
    r'$',  # Конец строки
    re.MULTILINE,
)


def test_trace_id_isolation_and_user_context(
    capture_sink: SinkType,
) -> None:
    """Проверка не смешивания логов двух пользователей.

    1. Запрос от Пользователя А (TraceID-A).
    2. Запрос от Пользователя Б (TraceID-B).
    3. Убедиться, что логи не перемешиваются.
    """
    captured: List[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    trace_id_ctx.set('trace-id-user-A')
    user_id_ctx.set('user_100')
    username_ctx.set('Алиса')

    get_logger().info('Действие Алисы 1')
    get_logger().info('Действие Алисы 2')

    trace_id_ctx.set('trace-id-user-B')
    user_id_ctx.set('user_200')
    username_ctx.set('Боб')

    get_logger().info('Действие Боба 1')

    assert len(captured) == 3, (
        f'Ожидается 3 лога, получено: {len(captured)}: {captured}'
    )

    assert 'trace-id-user-A' in captured[0], (
        f'Несоответствие Trace-ID для лога 0: {captured[0]}'
    )
    assert 'user_id=user_100 username=Алиса' in captured[0], (
        f'Несоответствие пользовательского контекста в логе 0: {captured[0]}'
    )

    assert 'trace-id-user-A' in captured[1], (
        f'есоответствие Trace-ID для лога 1: {captured[1]}'
    )
    assert 'user_id=user_100 username=Алиса' in captured[1], (
        f'Несоответствие пользовательского контекста в логе 1: {captured[1]}'
    )

    assert 'trace-id-user-B' in captured[2], (
        f'есоответствие Trace-ID для лога 2: {captured[2]}'
    )
    assert 'user_id=user_200 username=Боб' in captured[2], (
        f'Несоответствие пользовательского контекста в логе 2: {captured[2]}'
    )


def test_lifecycle_system_to_authenticated(capture_sink: SinkType) -> None:
    """Проверка подстановки данных пользователя.

    1. Запрос начинается как SYSTEM (до аутентификации).
    2. Middleware проверяет токен -> контекст обновляется.
    3. Последующие логи видят реального юзера.
    """
    captured: List[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    get_logger().info('Запрос - проверка авторизации.')
    assert 'user_id=SYSTEM' in captured[-1], (
        f'Ожидается SYSTEM-пользователь до аутентификации: {captured[-1]}'
    )

    user_id_ctx.set('12')
    username_ctx.set('Admin')

    get_logger().info('Настройки обновлены администратором!')
    assert 'user_id=12 username=Admin' in captured[-1], (
        f'Ожидался аутентифицированный пользователь, получено: {captured[-1]}'
    )

    assert 'user_id=SYSTEM' not in captured[-1], (
        f'SYSTEM не должен появляться после аутентификации: {captured[-1]}'
    )


def test_exception_logging_with_traceback(capture_sink: SinkType) -> None:
    """Проверка обработки ошибок.

    Проверяет, что logger.exception корректно записывает ошибку
    и (в dev-режиме) включает стек вызовов.
    """
    captured: List[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
        backtrace=True,
    )

    try:
        1 / 0  # noqa: B018  # Намеренно вызываем ошибку
    except ZeroDivisionError:
        get_logger().exception('Ошибка вычисления')
    assert len(captured) > 0, 'Ни одного лога не получено в рамках теста.'
    log_output = '\n'.join(captured)

    assert 'Ошибка вычисления' in log_output, (
        f'Ожидаемое сообщение не найдено в логах: {log_output}'
    )
    assert 'ZeroDivisionError' in log_output, (
        f'Ожидаемый тип ошибки не обнаружен в логах: {log_output}'
    )
    assert 'user_id=SYSTEM' in log_output, (
        f'Пользовательский контекст не обнаружен в логах: {log_output}'
    )


def test_dev_mode_format(capture_sink: SinkType) -> None:
    """Проверяет структуру лога в dev-режиме."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    get_logger().info('Тестовое сообщение')

    assert len(captured) == 1, (
        f'Ожидается 1 лог, получено: {len(captured)}: {captured}'
    )
    log_line = captured[0]

    assert LOG_STRUCTURE_PATTERN.search(log_line), (
        'Несоответствие формата лога:\n'
        f'Ожидался паттерн: {LOG_STRUCTURE_PATTERN.pattern}\n'
        f'Получено: {log_line}'
    )


def test_context_injection(capture_sink: SinkType) -> None:
    """Проверяет подстановку user_id и username из contextvars."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    user_id_ctx.set('15')
    username_ctx.set('Андрей')

    get_logger().info('Залогированное действие пользователя')

    assert len(captured) == 1, f'Ожидается 1 лог, получено: {len(captured)}'

    assert 'user_id=15' in captured[0], (
        f'Ожидается user_id=15 в логе, получено: {captured[0]}'
    )
    assert 'username=Андрей' in captured[0], (
        f'Ожидается username=Андрей в логе, получено: {captured[0]}'
    )
    assert 'Залогированное действие пользователя' in captured[0], (
        f'Ожидается message в логе, получено: {captured[0]}'
    )


def test_intercept_handler_stdlib(capture_sink: SinkType) -> None:
    """Проверяет перехват логов от стандартной библиотеки logging."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    std_logger = logging.getLogger('test_std_lib')
    std_logger.setLevel(logging.INFO)
    std_logger.info('Тест logging')

    found = any(
        'Тест logging' in line
        and 'user_id=SYSTEM' in line
        and 'username=SYSTEM' in line
        for line in captured
    )
    assert found, (
        f'Логи из logging неправильно перехватываются или форматируются.\n'
        f'Полученные логи: {captured}'
    )


def test_prod_mode_no_ansi_colors(capture_sink: SinkType) -> None:
    """Проверяет, что в prod-режиме нет ANSI-кодов цвета."""
    captured: list[str] = []

    setup_logging(env='prod', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    get_logger().info('Сообщение для прода')

    assert len(captured) == 1, f'Ожидался 1 лог, получено: {len(captured)}'
    log_line = captured[0]

    assert '\x1b[' not in log_line, (
        'В прод-логах не должны фигурировать ANSI коды.'
        f'Получено: {repr(log_line)}'
    )
    assert 'Сообщение для прода' in log_line, (
        f'Ожидалось сообщение в логе, получено: {log_line}'
    )


def test_dev_mode_creates_log_file(tmp_path, monkeypatch) -> None:
    """Проверка создания папки logs и файл логов."""
    fake_log_folder = tmp_path / 'test_logs'
    fake_log_file = fake_log_folder / 'app.log'

    monkeypatch.setattr(LoggingConstants, 'LOGGING_FOLDER', fake_log_folder)
    monkeypatch.setattr(LoggingConstants, 'LOG_FILES_PATH', fake_log_file)

    setup_logging(env='dev', log_level='INFO')

    get_logger().info('Проверка создания файла')

    time.sleep(LOG_WRITE_DELAY_SEC)

    assert fake_log_folder.exists(), (
        'Директория логов не была создана в режиме разработки!'
    )
    assert fake_log_file.exists(), (
        'Лог-файл не был создан в режиме разработки!'
    )

    content = fake_log_file.read_text()
    assert 'Проверка создания файла' in content, (
        f'Сообщение лога не найдено в файле. Содержимое: {content}'
    )


def test_prod_mode_does_create_file(tmp_path, monkeypatch) -> None:
    """Проверяет, что в режиме prod файл логов создаётся."""
    fake_log_folder = tmp_path / 'prod_logs'
    fake_log_file = fake_log_folder / 'app.log'

    monkeypatch.setattr(LoggingConstants, 'LOGGING_FOLDER', fake_log_folder)
    monkeypatch.setattr(LoggingConstants, 'LOG_FILES_PATH', fake_log_file)

    setup_logging(env='prod', log_level='INFO')

    get_logger().info('Проверка создания файла')
    time.sleep(LOG_WRITE_DELAY_SEC)

    assert fake_log_folder.exists(), (
        'Папка логов должна создаваться в режиме продакшена'
    )
    assert fake_log_file.exists(), 'Лог должен создаваться в режиме продакшена'


def test_dev_mode_log_structure(tmp_path, monkeypatch) -> None:
    """Проверяет структуру строки лога именно в созданном файле (dev режим)."""
    fake_log_folder = tmp_path / 'struct_logs'
    fake_log_file = fake_log_folder / 'app.log'

    monkeypatch.setattr(LoggingConstants, 'LOGGING_FOLDER', fake_log_folder)
    monkeypatch.setattr(LoggingConstants, 'LOG_FILES_PATH', fake_log_file)

    setup_logging(env='dev', log_level='INFO')

    user_id_ctx.set('123')
    username_ctx.set('TestUser')
    trace_id_ctx.set('UGJT-1234-GFGF-5342')

    get_logger().info('Проверка структуры')
    time.sleep(LOG_WRITE_DELAY_SEC)

    content = fake_log_file.read_text()

    assert LOG_STRUCTURE_PATTERN.search(content), (
        f'Несовпадение структуры файла логов:\n'
        f'Ожидался паттерн: {LOG_STRUCTURE_PATTERN.pattern}\n'
        f'Получено: {content}'
    )


def test_log_with_special_characters(capture_sink) -> None:
    """Проверяет, что спецсимволы в сообщении не ломают форматирование."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    test_message = 'Сообщение с "кавычками", \n переносом строки, и | символом'
    get_logger().info(test_message)

    assert len(captured) == 1, f'Ожидается 1 лог, получено: {len(captured)}'
    assert 'user_id=SYSTEM' in captured[0], (
        f'Потерян пользовательский контекст: {captured[0]}'
    )
    assert 'Сообщение с' in captured[0], f'Сообщение обрезано: {captured[0]}'


def test_empty_message_does_not_crash(capture_sink) -> None:
    """Проверяет, что пустое сообщение не вызывает ошибку."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    get_logger().info('')

    assert len(captured) == 1, (
        f'Ожидается 1 лог для пустого сообщения, получено: {len(captured)}'
    )
    assert 'user_id=SYSTEM' in captured[0], (
        f'User context missing: {captured[0]}'
    )


def test_very_long_message(capture_sink) -> None:
    """Проверяет обработку очень длинных сообщений."""
    captured: list[str] = []

    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    long_message = 'A' * 10000
    get_logger().info(long_message)

    assert len(captured) == 1, f'Ожидается 1 лог, получено: {len(captured)}'
    assert long_message in captured[0], 'Длинное сообщение было повреждено.'
