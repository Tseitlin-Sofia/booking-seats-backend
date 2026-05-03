# src/test_email_service.py
"""Тестирование email-уведомлений с реальными импортами."""

from dotenv import load_dotenv
load_dotenv()

from app.services.task import (
    send_email,
    build_admin_notification,
    build_client_reminder,
    generate_task_id,
    get_html_for_admin,
    get_html_for_client,
    ADMIN_EMAIL,
    CLIENT_EMAIL,
)

test_data = {
    'id': 999,
    'table_id': 5,
    'user': {
        'username': 'Тестовый Гость',
        'email': CLIENT_EMAIL,
        'phone': '+7 999 123 45 67',
    },
    'booking_date': '2026-05-01 19:00',
}

if __name__ == '__main__':
    # Тест 1: Админу (новая бронь)
    print('=' * 60)
    print('ТЕСТ 1: Отправка HTML-письма админу (POST)')
    print('=' * 60)
    subject, text_body = build_admin_notification(test_data, method='POST')
    html_body = get_html_for_admin(test_data, method='POST')
    send_email(to=ADMIN_EMAIL, subject=subject, text_body=text_body, html_body=html_body)
    print(f'Письмо админу отправлено на {ADMIN_EMAIL}\n')

    # Тест 2: Админу (изменение брони)
    print('=' * 60)
    print('ТЕСТ 2: Отправка HTML-письма админу (PATCH)')
    print('=' * 60)
    subject, text_body = build_admin_notification(test_data, method='PATCH')
    html_body = get_html_for_admin(test_data, method='PATCH')
    send_email(to=ADMIN_EMAIL, subject=subject, text_body=text_body, html_body=html_body)
    print(f'Письмо админу отправлено на {ADMIN_EMAIL}\n')

    # Тест 3: Клиенту (напоминание)
    print('=' * 60)
    print('ТЕСТ 3: Отправка HTML-письма клиенту')
    print('=' * 60)
    subject, text_body = build_client_reminder(test_data)
    html_body = get_html_for_client(test_data)
    send_email(to=CLIENT_EMAIL, subject=subject, text_body=text_body, html_body=html_body)
    print(f'Письмо клиенту отправлено на {CLIENT_EMAIL}\n')

    # Тест 4: Генерация task_id
    print('=' * 60)
    print('ТЕСТ 4: Генерация task_id')
    print('=' * 60)
    task_id = generate_task_id(999)
    print(f'task_id: {task_id}')
    assert task_id == 'reminder-booking-999', f'Ожидалось reminder-booking-999, получено {task_id}'
    print('✅ task_id корректен\n')

    print('=' * 60)
    print('✅ Все тесты пройдены!')
    print(f'   Админ: {ADMIN_EMAIL}')
    print(f'   Клиент: {CLIENT_EMAIL}')
    print('=' * 60)