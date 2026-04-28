import smtplib
from email.mime.text import MIMEText
import logging
import os

from .celery_app import celery_app

# Настройка логирования для задач
logger = logging.getLogger(__name__)


ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
CLIENT_EMAIL = os.getenv('CLIENT_EMAIL', 'test@mail.com')

def send_message_to_smtp_server(message: MIMEText) -> None:
    """Отправка сообщения на почту через smtp-сервер"""
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        print("✅ Подключено!")
        server.login(ADMIN_EMAIL, SMTP_PASSWORD)
        print("✅ Логин успешен!")
        server.send_message(message)
        print(f"✅ Письмо отправлено! Проверьте ящик {message['To']}")


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
    msg['From'] = SMTP_USER
    msg['To'] = ADMIN_EMAIL

    try:
        send_message_to_smtp_server(msg)
    except Exception as e:
        print(f"[NOTIFY] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='tasks.notify_client', bind=True, max_retries=4)
def notify_client(self, data: dict | None = None):
    """
    Отправка напоминания КЛИЕНТУ о брони.
    Выполняется ПО РАСПИСАНИЮ (отложенная задача).
    """
    client_email: str = CLIENT_EMAIL
    if data:
        client: dict = data.get('user', 'Неизвестно')
        client_email: str = client.get('email', CLIENT_EMAIL)
        client_name: str = client.get('username', 'Неизвестно')
        print(f"[CLIENT REMINDER] Отправляю напоминание клиенту {client_name}")

        subject = "⏰ Напоминание о брони стола в ресторане"
        body = f"""
        {client_name.capitalize()}, здравствуйте!
        
        Напоминаем, что вы забронировали стол на
         {data.get('booking_date', 'Неизвестно')}.
        
        Будем рады вас видеть!
        
        С уважением,
        Ресторан "Каффетерий"
        """
    else:
        subject = "Отложенное напоминание"
        body = "Фотография загружена на сервер 5 минут назад"

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = client_email

    try:
        send_message_to_smtp_server(msg)
    except Exception as e:
        print(f"[NOTIFY] ❌ Ошибка: {e}")
        raise self.retry(exc=e, countdown=30)
