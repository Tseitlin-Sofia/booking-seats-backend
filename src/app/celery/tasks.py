import os
import smtplib
from email.mime.text import MIMEText

from celery import Task

from app.core.logging import get_logger

from .celery_app import celery_app

# Настройка логирования для задач
logger = get_logger()


ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
CLIENT_EMAIL = os.getenv('CLIENT_EMAIL', 'test@mail.com')


def send_email(to: str, subject: str, body: str) -> None:
    """Отправка email через SMTP-сервер."""
    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        logger.info("Подключено к {}:{}", SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        logger.info("Письмо отправлено на {}", to)


def _build_admin_notification(data: dict) -> tuple[str, str]:
    """Формирует тему и тело письма для админа."""
    user = data.get('user', {})
    subject = f"🚨 НОВАЯ БРОНЬ! Стол №{data['table_id']}"
    body = f"""
    Поступила новая бронь:

    👤 Клиент: {user.get('username', 'Неизвестно')}
    📞 Телефон: {data.get('phone', 'Не указан')}
    📧 Email клиента: {user.get('email', 'Неизвестно')}
    📅 Дата и время: {data.get('booking_date', 'Неизвестно')}
    💬 Комментарий: {data.get('comment', 'Нет')}
    """
    return subject, body


def _build_client_reminder(data: dict) -> tuple[str, str]:
    """Формирует тему и тело письма для клиента."""
    user = data.get('user', {})
    name = user.get('username', 'Неизвестно').capitalize()
    subject = "⏰ Напоминание о брони стола в ресторане"
    body = f"""
    {name}, здравствуйте!

    Напоминаем, что вы забронировали стол на \
    {data.get('booking_date', 'Неизвестно')}.

    Будем рады вас видеть!

    С уважением,
    Ресторан "Каффетерий"
    """
    return subject, body


@celery_app.task(name='tasks.notify_admin', bind=True, max_retries=3)
def notify_admin(self: Task, data: dict | None = None) -> None:
    """Мгновенное уведомление админу о новой брони."""
    if data:
        logger.info(
            "Отправляю уведомление админу о столе {}",
            data.get('table_id'),
        )
        subject, body = _build_admin_notification(data)
    else:
        subject, body = "Тестовое сообщение", "Фото сформировано"

    try:
        send_email(to=ADMIN_EMAIL, subject=subject, body=body)
    except Exception as e:
        logger.error("Ошибка отправки админу: {}", e)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='tasks.notify_client', bind=True, max_retries=4)
def notify_client(self: Task, data: dict | None = None) -> None:
    """Отложенное напоминание клиенту о брони."""
    if data:
        user = data.get('user', {})
        client_email = user.get('email', CLIENT_EMAIL)
        logger.info("Отправляю напоминание клиенту {}", user.get('username'))
        subject, body = _build_client_reminder(data)
    else:
        client_email = CLIENT_EMAIL
        subject, body = (
            "Отложенное напоминание",
            "Фотография загружена на сервер 5 минут назад",
        )

    try:
        send_email(to=client_email, subject=subject, body=body)
    except Exception as e:
        logger.error("Ошибка отправки клиенту: {}", e)
        raise self.retry(exc=e, countdown=30)
