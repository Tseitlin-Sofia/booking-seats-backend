"""Сервис для работы с бронированиями."""

from datetime import timedelta

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery.celery_app import celery_app
from app.celery.tasks import notify_admin, notify_client
from app.crud.booking import booking_crud
from app.schemas.booking import BookingInfo
from app.services.task import get_reminder_id


class BookingService:
    """Сервис для работы с бронированиями."""

    async def _make_notification_tasks_for_celery(
        self,
        booking: BookingInfo,
        method: str,
        session: AsyncSession,
    ) -> None:
        """Создание задачи в celery.

        Созадется задача на отправку уведомления админинистратору и напоминания
        клиенту о брони.
        """
        task_id = get_reminder_id(booking.id)
        if method == 'PATCH':
            AsyncResult(task_id, app=celery_app).revoke()
        booking_json = booking.model_dump_json(exclude_unset=False)
        notify_admin.delay(method, booking_json)
        booking_datetime = await booking_crud.get_start_datetime_by_booking_id(
            booking.id, session,
        )
        notify_client.apply_async(
            args=[booking_json],
            eta=booking_datetime - timedelta(hours=2),
            task_id=task_id,
        )


booking_service = BookingService()
