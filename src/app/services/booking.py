from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.celery.tasks import notify_admin, notify_client
from app.core.constants import NotificationConstants
from app.crud.booking import booking_crud
from app.schemas.booking import BookingInfo
from app.services.task import generate_task_id


class BookingService:
    """Сервис для работы с бронированиями."""

    FORMAT = NotificationConstants.DATETIME_FORMAT

    async def make_notification_tasks_for_celery(
        self,
        booking: BookingInfo,
        method: str,
        session: AsyncSession,
        changed_by_role: str = 'user',
    ) -> None:
        """Создание задачи в celery."""
        task_id = generate_task_id(booking.id)
        booking_dict = booking.model_dump()

        booking_datetime = await booking_crud.get_start_datetime_by_booking_id(
            booking.id, session,
        )
        booking_dict['booking_date'] = booking_datetime.strftime(self.FORMAT)
        # prod_reminder_time = booking_datetime - timedelta(hours=2)
        demo_reminder_time = datetime.now() + timedelta(seconds=30)
        notify_admin.delay(method, booking_dict, changed_by_role)
        notify_client.apply_async(
            args=[booking_dict],
            eta=demo_reminder_time,
            task_id=task_id,
        )


booking_service = BookingService()
