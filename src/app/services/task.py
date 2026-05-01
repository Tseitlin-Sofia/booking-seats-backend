"""Сервисные функции для работы с задачами в Celery."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.logging import get_logger

logger = get_logger()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
CLIENT_EMAIL = os.getenv('CLIENT_EMAIL', 'test@mail.com')


def send_email(
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
) -> None:
    """Отправка email через SMTP-сервер с текстовой и HTML-версией."""
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(text_body, "plain", "utf-8")

    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        logger.info("Подключено к {}:{}", SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        logger.info("Письмо отправлено на {}", to)


def build_admin_notification(data: dict, method: str) -> tuple[str, str]:
    """Формирует тему и тело письма для админа."""
    user = data.get('user', {})
    booking_id = data.get('id')
    basic_body = f"""
        👤 Клиент: {user.get('username', 'Неизвестно')}
        📞 Телефон: {data.get('phone', 'Не указан')}
        📧 Email клиента: {user.get('email', 'Неизвестно')}
        📅 Дата и время: {data.get('booking_date', 'Неизвестно')}
    """
    if method == 'POST':
        subject = f"🚨 НОВАЯ БРОНЬ №{booking_id}! Стол №{data['table_id']}"
        body = f"Поступила новая бронь №{booking_id}:\n" + basic_body
    elif method == 'PATCH':
        subject = f"🚨 ИЗМЕНЕНИЕ БРОНИ №{data.get('id')}!"
        body = f"Бронь № {booking_id} изменена:\n" + basic_body
    return subject, body


def build_client_reminder(data: dict) -> tuple[str, str]:
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


def get_reminder_id(booking_id: int) -> str:
    """Генерирует уникальный ID задачи на основе ID брони."""
    return f"reminder-booking-{booking_id}"


def get_html_for_admin(data: dict, method: str) -> str:
    """Генерирует HTML для уведомления администратора."""
    user = data.get('user', {})
    booking_id = data.get('id')
    table_id = data.get('table_id', '—')
    client_name = user.get('username', 'Неизвестно')
    client_phone = data.get('phone', 'Не указан')
    client_email = user.get('email', 'Неизвестно')
    booking_date = data.get('booking_date', 'Неизвестно')

    if method == 'POST':
        title = f'🚨 Новая бронь №{booking_id}'
        action = 'поступила'
    else:
        title = f'✏️ Изменение брони №{booking_id}'
        action = 'изменена'

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #4a3f35, #6b5c4b);
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 22px;
            }}
            .content {{
                padding: 30px;
            }}
            .info-block {{
                background: #faf7f2;
                border-left: 4px solid #c9a96e;
                padding: 20px;
                border-radius: 0 8px 8px 0;
            }}
            .info-row {{
                display: flex;
                align-items: center;
                margin-bottom: 12px;
                font-size: 16px;
            }}
            .info-row:last-child {{
                margin-bottom: 0;
            }}
            .emoji {{
                font-size: 20px;
                margin-right: 12px;
                min-width: 28px;
            }}
            .label {{
                color: #8b7355;
                font-weight: 600;
                min-width: 150px;
            }}
            .value {{
                color: #3d3226;
            }}
            .footer {{
                background: #faf7f2;
                text-align: center;
                padding: 20px;
                color: #8b7355;
                font-size: 14px;
                border-top: 1px solid #e8dcc8;
            }}
            .restaurant-name {{
                font-weight: 700;
                color: #6b5c4b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{title}</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.85;">
                    {action.capitalize()} новая бронь в ресторане
                </p>
            </div>
            <div class="content">
                <div class="info-block">
                    <div class="info-row">
                        <span class="emoji">👤</span>
                        <span class="label">Клиент:</span>
                        <span class="value">{client_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="emoji">📞</span>
                        <span class="label">Телефон:</span>
                        <span class="value">{client_phone}</span>
                    </div>
                    <div class="info-row">
                        <span class="emoji">📧</span>
                        <span class="label">Email:</span>
                        <span class="value">{client_email}</span>
                    </div>
                    <div class="info-row">
                        <span class="emoji">📅</span>
                        <span class="label">Дата и время:</span>
                        <span class="value">{booking_date}</span>
                    </div>
                    <div class="info-row">
                        <span class="emoji">🪑</span>
                        <span class="label">Стол №:</span>
                        <span class="value">{table_id}</span>
                    </div>
                </div>
            </div>
            <div class="footer">
                С уважением,<br>
                <span class="restaurant-name">Ресторан «Каффетерий»</span>
            </div>
        </div>
    </body>
    </html>
    """


def get_html_for_client(data: dict) -> str:
    """Генерирует HTML для напоминания клиенту."""
    user = data.get('user', {})
    client_name = user.get('username', 'Гость').capitalize()
    booking_date = data.get('booking_date', 'Неизвестно')
    table_id = data.get('table_id', '—')
    comment = data.get('comment', '')

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #fdf8f4;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 550px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            }}
            .header {{
                background: linear-gradient(135deg, #c9a96e, #e0c78a);
                color: #ffffff;
                padding: 35px 30px 25px;
                text-align: center;
            }}
            .header .icon {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .header .subtitle {{
                margin: 6px 0 0 0;
                opacity: 0.9;
                font-size: 15px;
            }}
            .content {{
                padding: 30px 25px;
            }}
            .greeting {{
                font-size: 18px;
                color: #3d3226;
                margin-bottom: 20px;
                line-height: 1.5;
            }}
            .info-card {{
                background: #fdf8f4;
                border: 1px solid #f0e3d0;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .info-row {{
                display: flex;
                align-items: center;
                margin-bottom: 14px;
                font-size: 15px;
            }}
            .info-row:last-child {{
                margin-bottom: 0;
            }}
            .emoji {{
                font-size: 18px;
                margin-right: 10px;
                min-width: 24px;
                text-align: center;
            }}
            .label {{
                color: #8b7355;
                font-weight: 600;
                min-width: 120px;
            }}
            .value {{
                color: #3d3226;
                font-weight: 500;
            }}
            .reminder-text {{
                text-align: center;
                color: #8b7355;
                font-size: 15px;
                line-height: 1.6;
                margin-top: 20px;
            }}
            .footer {{
                background: #fdf8f4;
                text-align: center;
                padding: 20px;
                color: #8b7355;
                font-size: 13px;
                border-top: 1px solid #f0e3d0;
                line-height: 1.6;
            }}
            .restaurant-name {{
                font-weight: 700;
                color: #6b5c4b;
                font-size: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="icon">⏰</div>
                <h1>Ждём вас!</h1>
                <p class="subtitle">Напоминание о бронировании</p>
            </div>
            <div class="content">
                <div class="greeting">
                    {client_name}, здравствуйте!
                </div>
                <div class="info-card">
                    <div class="info-row">
                        <span class="emoji">📅</span>
                        <span class="label">Дата и время:</span>
                        <span class="value">{booking_date}</span>
                    </div>
                    <div class="info-row">
                        <span class="emoji">🪑</span>
                        <span class="label">Стол №:</span>
                        <span class="value">{table_id}</span>
                    </div>
                    {f'''<div class="info-row">
                        <span class="emoji">💬</span>
                        <span class="label">Комментарий:</span>
                        <span class="value">{comment}</span>
                    </div>''' if comment else ''}
                </div>
                <div class="reminder-text">
                    Будем рады видеть вас!<br>
                    Мы подготовили для вас лучший стол.
                </div>
            </div>
            <div class="footer">
                С уважением,<br>
                <span class="restaurant-name">Ресторан «Каффетерий»</span>
            </div>
        </div>
    </body>
    </html>
    """
