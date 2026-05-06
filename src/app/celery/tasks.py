from app.celery.base_task import LoguruTask
from app.celery.celery_app import celery_app
from app.services.task import (
    ADMIN_EMAIL,
    CLIENT_EMAIL,
    build_admin_notification,
    build_client_reminder,
    get_html_for_admin,
    get_html_for_client,
    is_canceled,
    send_email,
    is_completed
)


@celery_app.task(
    name='tasks.notify_admin',
    bind=True,
    base=LoguruTask,
    max_retries=3,
)
def notify_admin(
    self: LoguruTask,
    method: str,
    data: dict | None = None,
    changed_by_role: str = 'user',
) -> None:
    """Мгновенное уведомление админу о новой брони."""
    if data:
        if is_canceled(data) or is_completed(data):
            self.log.info(
                'Бронь отменена/выполнена, уведомление админу не придёт'
            )
            return

        if method == 'PATCH' and changed_by_role in ('admin', 'manager'):
            self.log.info('Изменение внёс админ/менеджер, уведомление не нужно')
            return

        self.log.info(
            'Отправляю уведомление админу о столе {}',
            data.get('table_id'),
        )
        subject, text_body = build_admin_notification(data, method)
        html_body = get_html_for_admin(data, method)

    else:
        subject = 'Тестовое сообщение'
        text_body = 'Фото сформировано'
        html_body = None

    try:
        send_email(
            to=ADMIN_EMAIL,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
    except Exception as e:
        self.log.error('Ошибка отправки админу: {}', e)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    name='tasks.notify_client',
    bind=True,
    base=LoguruTask,
    max_retries=4,
)
def notify_client(self: LoguruTask, data: dict | None = None) -> None:
    """Отложенное напоминание клиенту о брони."""
    if data:
        user = data.get('user', {})
        client_email = user.get('email', CLIENT_EMAIL)
        self.log.info('Отправляю напоминание клиенту {}', user.get('username'))
        subject, text_body = build_client_reminder(data)
        html_body = get_html_for_client(data)
    else:
        client_email = CLIENT_EMAIL
        subject = 'Отложенное напоминание'
        text_body = 'Фотография загружена на сервер 5 минут назад'
        html_body = None

    try:
        send_email(
            to=client_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
    except Exception as e:
        self.log.error('Ошибка отправки клиенту: {}', e)
        raise self.retry(exc=e, countdown=30)
