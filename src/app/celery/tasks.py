import smtplib
from email.mime.text import MIMEText
import logging
import os
from dotenv import load_dotenv

from app.core.constants import NotificationConstants
from .celery_app import celery_app

# Настройка логирования для задач
logger = logging.getLogger(__name__)

load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

@celery_app.task(name='tasks.notify_admin', bind=True, max_retries=3)
def notify_admin(self, data: dict | None = None):
    if data:
        print(f"[ADMIN NOTIFY] Отправляю письмо админу о столе {data['table_id']}")

        client = data.get('user', 'Неизвестно')
        client_email = client.get('email', 'Неизвестно')
        client_name = client.get('username', 'Неизвестно')

        subject = f"🚨 НОВАЯ БРОНЬ! Стол №{data['table_id']}"
        body = f"""
        Поступила новая бронь:
        
        👤 Клиент: {client_name}
        📞 Телефон: {data['phone']}
        📧 Email клиента: {client_email}
        📅 Дата и время: {data['booking_date']}
        💬 Комментарий: {data.get('comment', 'Нет')}
        """
    else:
        subject = f"Тестоовое сообщение"
        body = f"Фото сформировано"

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = ADMIN_EMAIL
    msg['To'] = SMTP_USER

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            print("✅ Подключено!")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ Логин успешен!")
            server.send_message(msg)
            print(f"✅ Письмо отправлено! Проверьте ящик {SMTP_USER}")
    except Exception as e:
        print(f"[ADMIN NOTIFY] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='tasks.notify_client', bind=True, max_retries=3)
def notify_client(self, data: dict | None = None):
    """
    Отправка напоминания КЛИЕНТУ о брони.
    Выполняется ПО РАСПИСАНИЮ (отложенная задача).
    """
    client_email = None

    if data:
        client = data.get('user', 'Неизвестно')
        client_email = client.get('email', 'Неизвестно')
        client_name = client.get('username', 'Неизвестно')
        print(f"[CLIENT REMINDER] Отправляю напоминание клиенту {client_name}")

        subject = "⏰ Напоминание о брони стола в ресторане"
        body = f"""
        {client_name}, здравствуйте!
        
        Напоминаем, что вы забронировали стол на {data.get('booking_date'), 'Неизвестно'}.
        
        Будем рады вас видеть!
        
        С уважением,
        Ресторан "Каффетерий"
        """
    else:
        subject = "Отложенное напоминание"
        body = "Фотография загружена на сервер 5 минут назад"

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = ADMIN_EMAIL
    msg['To'] = client_email if client_email else SMTP_USER

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            print("✅ Подключено!")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ Логин успешен!")
            server.send_message(msg)
            print(f"✅ Письмо отправлено! Проверьте ящик {SMTP_USER}")
    except Exception as e:
        print(f"[ADMIN NOTIFY] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=60)