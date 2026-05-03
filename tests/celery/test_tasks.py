"""Тесты для Celery задач."""

from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from app.celery.base_task import LoguruTask
from app.celery.tasks import notify_admin, notify_client


class TestCeleryTasks:
    """Тесты для Celery задач."""

    def test_notify_admin_inherits_from_loguru_task(self) -> None:
        """Проверяет, что задача notify_admin наследуется от LoguruTask."""
        assert issubclass(notify_admin.__class__, LoguruTask)

    def test_notify_client_inherits_from_loguru_task(self) -> None:
        """Проверяет, что задача notify_client наследуется от LoguruTask."""
        assert issubclass(notify_client.__class__, LoguruTask)

    @patch('app.celery.tasks.notify_admin.retry')
    def test_notify_admin_success_with_data(
        self,
        mock_retry,
        mock_send_email,
        booking_for_celery,
    ) -> None:
        """Проверяет успешную отправку уведомления администратору с данными."""
        mock_send_email.return_value = None

        result = notify_admin('POST', booking_for_celery)

        mock_send_email.assert_called_once()
        mock_retry.assert_not_called()
        assert result is None

    @patch('app.celery.tasks.notify_admin.retry')
    def test_notify_admin_success_without_data(
        self,
        mock_retry,
        mock_send_email,
    ) -> None:
        """Проверяет отправку тестового уведомления без данных."""
        mock_send_email.return_value = None

        notify_admin('POST')

        mock_send_email.assert_called_once()
        mock_retry.assert_not_called()

        call_args = mock_send_email.call_args[1]
        assert call_args['subject'] == 'Тестовое сообщение'

    @patch('app.celery.tasks.notify_admin.retry')
    def test_notify_admin_failure_retry(
        self,
        mock_retry,
        booking_for_celery,
    ) -> None:
        """Проверяет повторную попытку при ошибке отправки."""
        mock_retry.side_effect = Retry()

        with patch(
            'app.celery.tasks.send_email',
            side_effect=Exception('SMTP error'),
        ):
            with pytest.raises(Retry):
                notify_admin('POST', booking_for_celery)

            mock_retry.assert_called_once()

    @patch('app.celery.tasks.notify_client.retry')
    def test_notify_client_success_with_data(
        self,
        mock_retry,
        mock_send_email,
        booking_for_celery,
    ) -> None:
        """Проверяет успешную отправку напоминания клиенту с данными."""
        mock_send_email.return_value = None

        result = notify_client(booking_for_celery)

        mock_send_email.assert_called_once()
        mock_retry.assert_not_called()
        assert result is None

    @patch('app.celery.tasks.notify_client.retry')
    def test_notify_client_success_without_data(
        self,
        mock_retry,
        mock_send_email,
    ) -> None:
        """Проверяет отправку тестового напоминания без данных."""
        mock_send_email.return_value = None

        notify_client()

        mock_send_email.assert_called_once()
        mock_retry.assert_not_called()

        call_args = mock_send_email.call_args[1]
        assert call_args['subject'] == 'Отложенное напоминание'

    @patch('app.celery.tasks.notify_client.retry')
    def test_notify_client_failure_retry(
        self,
        mock_retry,
        booking_for_celery,
    ) -> None:
        """Проверяет повторную попытку при ошибке отправки клиенту."""
        mock_retry.side_effect = Retry()

        with patch(
            'app.celery.tasks.send_email',
            side_effect=Exception('SMTP error'),
        ):
            with pytest.raises(Retry):
                notify_client(booking_for_celery)

            mock_retry.assert_called_once()
