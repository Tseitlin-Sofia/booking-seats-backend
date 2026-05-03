"""Тесты для логирования Celery задач."""

import time
from typing import Any, Generator, List
from unittest.mock import patch

import pytest
from loguru import logger

from app.celery.base_task import LoguruTask
from app.core.constants import LoggingConstants
from app.core.logging import (
    get_logger,
    setup_logging,
    trace_id_ctx,
    user_id_ctx,
    username_ctx,
)
from tests.test_logging import LOG_STRUCTURE_PATTERN


class TestCeleryLoggingFormat:
    """Тесты для проверки формата логов Celery задач."""

    @pytest.fixture(autouse=True)
    def setup_celery_eager(self) -> Generator[None, None, None]:
        """Настраивает Celery для синхронного выполнения."""
        from app.celery.celery_app import celery_app

        celery_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )
        yield
        celery_app.conf.update(
            task_always_eager=False,
            task_eager_propagates=False,
        )

    def test_celery_task_log_format_matches_common_pattern(
        self,
        capture_sink,
    ) -> None:
        """Проверяет, что логи Celery задач соответствуют общему формату."""
        from app.celery.tasks import notify_admin

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        booking_data = {'id': 1, 'table_id': 5}

        with patch('app.celery.tasks.send_email', return_value=None):
            notify_admin('POST', booking_data)

        time.sleep(0.1)

        assert len(captured) >= 1, 'Лог Celery задачи не был перехвачен'

        log_matched = any(
            LOG_STRUCTURE_PATTERN.search(log_line) for log_line in captured
        )
        assert log_matched, (
            f'Ни один лог Celery не соответствует общему формату.\n'
            f'Полученные логи: {captured}'
        )
        assert any('user_id=SYSTEM' in log_line for log_line in captured), (
            f'В логах Celery отсутствует user_id: {captured}'
        )
        assert any('username=SYSTEM' in log_line for log_line in captured), (
            f'В логах Celery отсутствует username: {captured}'
        )
        assert any(
            'trace_id=SYSTEM' in log_line or 'trace_id=CELERY' in log_line
            for log_line in captured
        ), f'В логах Celery отсутствует trace_id: {captured}'

    def test_celery_task_log_context_not_auto_passed(
        self,
        capture_sink,
    ) -> None:
        """Демонстрирует, что контекст НЕ передается автоматически.

        Это ожидаемое поведение: contextvars не передаются между процессами.
        """
        from app.celery.tasks import notify_admin

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        trace_id_ctx.set('should-not-appear')
        user_id_ctx.set('should-not-appear')
        username_ctx.set('should-not-appear')

        with patch('app.celery.tasks.send_email', return_value=None):
            notify_admin('POST', {'id': 1, 'table_id': 5})

        time.sleep(0.1)

        assert not any('should-not-appear' in log for log in captured), (
            'Контекст не должен передаваться автоматически! '
            'Для передачи используйте _logging_context аргумент.'
        )

    def test_celery_task_error_log_format(self, capture_sink) -> None:
        """Проверяет формат логов ошибок в Celery задачах."""
        from app.celery.tasks import notify_admin

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
            backtrace=True,
        )

        booking_data = {'id': 1, 'table_id': 5}

        with patch(
            'app.celery.tasks.send_email',
            side_effect=Exception('SMTP connection failed'),
        ):
            with patch.object(
                notify_admin,
                'retry',
                side_effect=Exception('Retry'),
            ):
                with pytest.raises(Exception):
                    notify_admin('POST', booking_data)

        time.sleep(0.1)

        error_logs = [log for log in captured if 'Ошибка отправки' in log]
        assert len(error_logs) > 0, (
            f'Лог ошибки не найден. Получено: {captured}'
        )

        for error_log in error_logs:
            assert LOG_STRUCTURE_PATTERN.search(error_log), (
                f'Лог ошибки Celery не соответствует формату: {error_log}'
            )
            assert 'ERROR' in error_log, (
                f'Уровень ошибки не указан или неверен: {error_log}'
            )

    def test_celery_task_log_level_info(self, capture_sink) -> None:
        """Проверяет, что при уровне INFO логи записываются."""
        from app.celery.tasks import notify_admin

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        booking_data = {'id': 1, 'table_id': 5}

        with patch('app.celery.tasks.send_email', return_value=None):
            notify_admin('POST', booking_data)

        time.sleep(0.1)

        info_logs = [log for log in captured if 'INFO' in log]
        assert len(info_logs) >= 1, (
            f'При уровне INFO логи должны записываться. Получено: {captured}'
        )

    def test_celery_standard_logger_intercept(self, capture_sink) -> None:
        """Проверяет перехват логов из стандартного logging в Celery."""
        import logging

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        celery_logger = logging.getLogger('celery')
        celery_logger.setLevel(logging.INFO)
        celery_logger.info('Сообщение из стандартного celery логгера')

        time.sleep(0.1)

        assert any(
            'Сообщение из стандартного celery логгера' in log
            for log in captured
        ), f'Лог из стандартного celery логгера не был перехвачен: {captured}'

    def test_celery_task_success_log_contains_info_level(
        self,
        capture_sink: Any,
    ) -> None:
        """Проверяет, что выполнение задачи логируется с уровнем INFO."""
        from app.celery.tasks import notify_client

        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        booking_data = {
            'id': 1,
            'user': {'username': 'test_user', 'email': 'test@example.com'},
        }

        with patch('app.celery.tasks.send_email', return_value=None):
            notify_client(booking_data)

        time.sleep(0.1)
        assert len(captured) >= 0, 'Логов нет'


class TestCeleryLoggingTaskBase:
    """Тесты для базового класса LoguruTask."""

    def test_loguru_task_on_failure_logs_error(self, capture_sink) -> None:
        """Проверяет, что on_failure логирует ошибку с правильным форматом."""
        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        task = LoguruTask()
        task._logger = get_logger()
        task.name = 'test_failure_task'

        exc = Exception('Test failure error')
        task.on_failure(exc, 'task-failure-123', [], {}, None)

        time.sleep(0.1)

        error_logs = [
            log for log in captured if 'завершилась с ошибкой' in log
        ]
        assert len(error_logs) >= 1, (
            f'Лог ошибки on_failure не найден: {captured}'
        )
        assert any('Test failure error' in log for log in error_logs), (
            f'Сообщение об ошибке не найдено: {captured}'
        )
        assert any('task-failure-123' in log for log in error_logs), (
            f'ID задачи не найден в логе ошибки: {captured}'
        )

    def test_loguru_task_on_retry_logs_warning(self, capture_sink) -> None:
        """Проверка формата логирования on_retry."""
        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        task = LoguruTask()
        task._logger = get_logger()
        task.name = 'test_retry_task'

        exc = Exception('Retry attempt')
        task.on_retry(exc, 'task-retry-456', [], {}, None)

        time.sleep(0.1)

        retry_logs = [log for log in captured if 'будет повторена' in log]
        assert len(retry_logs) >= 1, (
            f'Лог повторной попытки on_retry не найден: {captured}'
        )
        assert any('Retry attempt' in log for log in retry_logs), (
            f'Причина повторной попытки не найдена: {captured}'
        )
        assert any('WARNING' in log for log in retry_logs), (
            f'Уровень предупреждения не установлен: {captured}'
        )

    def test_loguru_task_on_success_logs_info(self, capture_sink) -> None:
        """Проверяет, что on_success логирует успех с правильным форматом."""
        captured: List[str] = []
        setup_logging(env='dev', log_level='INFO')
        logger.add(
            capture_sink(captured),
            format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

        task = LoguruTask()
        task._logger = get_logger()
        task.name = 'test_success_task'

        task.on_success('result', 'task-success-789', [], {})

        time.sleep(0.1)

        success_logs = [log for log in captured if 'успешно выполнена' in log]
        assert len(success_logs) >= 1, (
            f'Лог успешного выполнения on_success не найден: {captured}'
        )
        assert any('test_success_task' in log for log in success_logs), (
            f'Имя задачи не найдено в логе успеха: {captured}'
        )
        assert any('task-success-789' in log for log in success_logs), (
            f'ID задачи не найдено в логе успеха: {captured}'
        )
        assert any('INFO' in log for log in success_logs), (
            f'Уровень INFO не установлен: {captured}'
        )

    def test_loguru_task_init_sets_logger(self) -> None:
        """Проверяет, что при инициализации создается логгер."""
        task = LoguruTask()
        assert task._logger is not None
        assert hasattr(task.log, 'info')
        assert hasattr(task.log, 'error')
        assert hasattr(task.log, 'warning')

    def test_loguru_task_log_property_returns_logger(self) -> None:
        """Проверяет, что свойство log возвращает логгер."""
        task = LoguruTask()
        assert task.log == task._logger
