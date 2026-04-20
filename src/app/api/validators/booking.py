"""Валидаторы для эндпоинтов бронирования."""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.booking import booking_table_slot_crud
from app.crud.cafe import cafe_crud
from app.crud.slot import slot_crud
from app.crud.table import table_crud
from app.models import User
from app.schemas.booking import BookingTableSlot as BookingTableSlotSchema

logger = get_logger()


async def validate_booking_slots(
    slots: list[BookingTableSlotSchema],
    date: date,
    session: AsyncSession,
) -> None:
    """Валидация слотов бронирования."""
    if not await booking_table_slot_crud.is_available(
        slots=slots, date=date, session=session,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Constants.SLOTS_UNAVAILABLE,
        )


async def validate_cafe_slot_table(
    slots: list[BookingTableSlotSchema],
    cafe_id: int,
    session: AsyncSession,
) -> None:
    """Валидация того что запрашиваемый слот и стол принадлежат одному кафе."""
    for slot in slots:
        slot_db = await slot_crud.get(slot.slot_id, session)
        table_db = await table_crud.get(slot.table_id, session)
        cafe_db = await cafe_crud.get(cafe_id, session)

        if not slot_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Constants.SLOT_DOES_NOT_EXIST.format(slot.slot_id),
            )

        if not table_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Constants.TABLE_DOES_NOT_EXIST.format(slot.table_id),
            )

        if not cafe_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Constants.CAFE_DOES_NOT_EXIST.format(cafe_id),
            )

        if (idd := slot_db.cafe_id) != table_db.cafe_id or idd != cafe_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Constants.SLOT_CAFE_MISMATCH,
            )


async def validate_user_rights(user: User, requested_user_id: int) -> None:
    """Валидация прав пользователя."""
    if user.is_admin or user.is_manager or user.id == requested_user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=Constants.USER_RIGHTS_ERROR,
    )
