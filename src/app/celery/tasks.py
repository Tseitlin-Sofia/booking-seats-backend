import time

import smtplib
from email.mime.text import MIMEText
import logging

from typing import Dict, Any
from datetime import datetime

from .celery_app import celery_app

# Настройка логирования для задач
logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.notify_admin', bind=True, max_retries=3)
def notify_admin(self, booking_data: dict):
    print(f"[ADMIN NOTIFY] Отправляю письмо админу о столе {booking_data['table_id']}")

    # --- ВРЕМЕННЫЕ НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОГО ТЕСТА ---
    SMTP_HOST = "localhost"
    SMTP_PORT = 1025
    SMTP_USER = ""           # Пусто для локального сервера
    SMTP_PASSWORD = ""       # Пусто для локального сервера
    ADMIN_EMAIL = "admin@test.local"

    subject = f"🚨 НОВАЯ БРОНЬ! Стол №{booking_data['table_id']}"
    body = f"""
    Поступила новая бронь:
    
    👤 Клиент: {booking_data['client_name']}
    📞 Телефон: {booking_data['phone']}
    📧 Email клиента: {booking_data['client_email']}
    📅 Дата и время: {booking_data['date_time']}
    💬 Комментарий: {booking_data.get('comment', 'Нет')}
    """

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = SMTP_USER or "noreply@test.local"
    msg['To'] = ADMIN_EMAIL

    try:
        # Подключение БЕЗ starttls() и БЕЗ login()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
        print(f"[ADMIN NOTIFY] ✅ Письмо админу отправлено")
        return {"status": "sent", "to": "admin"}
    except Exception as e:
        print(f"[ADMIN NOTIFY] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='tasks.notify_client', bind=True, max_retries=3)
def notify_client(self, booking_data: dict):
    """
    Отправка напоминания КЛИЕНТУ о брони.
    Выполняется по расписанию (например, за 2 часа до визита).
    """
    print(f"[CLIENT REMINDER] Отправляю напоминание клиенту {booking_data['client_email']}")

    # SMTP_HOST = "smtp.yandex.ru"
    # SMTP_PORT = 587
    # SMTP_USER = "vash-restoran@yandex.ru"
    # SMTP_PASSWORD = "ваш_пароль_приложений"

    # Временно для локального теста
    SMTP_HOST = "localhost"
    SMTP_PORT = 1025
    SMTP_USER = ""
    SMTP_PASSWORD = ""
    ADMIN_EMAIL = "admin@test.local"

    subject = f"⏰ Напоминание о брони стола в ресторане"
    body = f"""
    {booking_data['client_name']}, здравствуйте!
    
    Напоминаем, что вы забронировали стол №{booking_data['table_id']}
    на {booking_data['date_time']}.
    
    Будем рады вас видеть!
    
    С уважением,
    Ресторан "Вкусно"
    """

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = booking_data['client_email']

    try:
        # with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USER, SMTP_PASSWORD)
        #     server.send_message(msg)
        # В блоке отправки (внутри notify_admin):
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            # Без server.starttls() и без server.login()
            server.send_message(msg)
        print(f"[CLIENT REMINDER] ✅ Напоминание клиенту отправлено")
        return {"status": "sent", "to": booking_data['client_email']}
    except Exception as e:
        print(f"[CLIENT REMINDER] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=60)