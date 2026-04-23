# src/app/celery/test_tasks.py
import smtplib
from email.mime.text import MIMEText

# Локальный SMTP-сервер (без авторизации)
SMTP_HOST = "localhost"
SMTP_PORT = 1025
SMTP_USER = ""        # Не нужен
SMTP_PASSWORD = ""    # Не нужен

msg = MIMEText(
    """
    Поступила новая бронь:
    
    👤 Клиент: Тестовый Клиент
    📞 Телефон: +79991234567
    📅 Дата и время: 2026-04-20 19:00
    💬 Комментарий: Тестовая бронь
    """,
    "plain", "utf-8"
)
msg['Subject'] = "🚨 НОВАЯ БРОНЬ! Стол №5"
msg['From'] = "restaurant@test.local"
msg['To'] = "admin@test.local"

print("Подключаюсь к локальному SMTP-серверу (localhost:1025)...")
try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
        # Никакого starttls() и login() — локальному серверу это не нужно
        server.send_message(msg)
        print("✅ Письмо отправлено!")
        print("📧 Проверьте первый терминал — там должно появиться содержимое письма.")
except Exception as e:
    print(f"❌ Ошибка: {e}")