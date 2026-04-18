"""CRUD операции для бронирования."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models import Booking, BookingTableSlot
from app.schemas.booking import BookingStatus

logger = get_logger()


class BookingCRUD(CRUDBase):
    """CRUD операции для бронирования."""

    async def get_bookings(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = True,
        cafe_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> list[Booking]:
        """Получает бронирования."""
        stmt = select(Booking)
        if show_active is not None:
            stmt = stmt.where(Booking.is_active == show_active)
        if cafe_id is not None:
            stmt = stmt.where(Booking.cafe_id == cafe_id)
        if user_id is not None:
            stmt = stmt.where(Booking.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class BookingTableSlotCRUD(CRUDBase):
    """CRUD операции для слотов бронирования."""

    async def is_available(
        self,
        slots: list[dict[str, int]],
        session: AsyncSession,
    ) -> bool:
        """Проверяет доступность запрошенных слотов."""
        for slot in slots:
            stmt = select(BookingTableSlot).where(
                BookingTableSlot.table_id == slot.table_id,
                BookingTableSlot.slot_id == slot.slot_id,
                BookingTableSlot.booking.status.in_(
                    BookingStatus.BOOKING, BookingStatus.ACTIVE,
                ),
                BookingTableSlot.is_active,
            ).exists()
            result = await session.execute(select(stmt))
            if result.scalar():
                logger.warning(Constants.SLOT_ALREADY_BOOKED.format(
                    slot.slot_id, slot.table_id),
                )
                return False
        return True


booking_crud = BookingCRUD(Booking)
booking_table_slot_crud = BookingTableSlotCRUD(BookingTableSlot)
