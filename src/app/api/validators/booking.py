"""Валидаторы для эндпоинтов бронирования."""

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.crud.cafe import cafe_crud
from app.crud.slot import slot_crud
from app.crud.table import table_crud
from app.models import Dish, User
from app.models.booking import Booking
from app.schemas.booking import BookingTableSlot as BookingTableSlotSchema
from app.schemas.dish import PreOrderItemCreate

logger = get_logger()


async def validate_booking_slots(
    slots: list[BookingTableSlotSchema],
    booking_date: date,
    session: AsyncSession,
) -> None:
    """Валидация слотов бронирования (проверка доступности)."""
    is_available = await booking_table_slot_crud.is_available(
        slots=slots,
        date=booking_date,
        session=session,
    )

    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=Constants.SLOTS_UNAVAILABLE,
        )


async def validate_cafe_slot_table(
    cafe_id: int,
    slots: list[BookingTableSlotSchema],
    session: AsyncSession,
) -> None:
    """Валидация того что запрашиваемый слот и стол принадлежат одному кафе."""
    cafe_db = await cafe_crud.get(session=session, obj_id=cafe_id)
    if not cafe_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.CAFE_DOES_NOT_EXIST.format(cafe_id),
        )

    for slot in slots:
        slot_db = await slot_crud.get(session=session, obj_id=slot.slot_id)
        if not slot_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Constants.SLOT_DOES_NOT_EXIST.format(slot.slot_id),
            )
        table_db = await table_crud.get(session=session, obj_id=slot.table_id)
        if not table_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Constants.TABLE_DOES_NOT_EXIST.format(slot.table_id),
            )

        if slot_db.cafe_id != table_db.cafe_id or slot_db.cafe_id != cafe_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Constants.SLOT_CAFE_MISMATCH,
            )

        if not slot_db.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Constants.SLOT_INACTIVE.format(slot.slot_id),
            )

        if not table_db.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Constants.TABLE_INACTIVE.format(slot.table_id),
            )


async def validate_user_rights(
    user: Optional[User],
    requested_user_id: int,
) -> None:
    """Валидация прав пользователя на доступ к бронированию."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Constants.USER_NOT_AUTHENTICATED,
        )

    if user.is_admin or user.is_manager:
        return

    if user.id == requested_user_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=Constants.USER_RIGHTS_ERROR,
    )


async def validate_booking_exists(
    booking_id: int,
    session: AsyncSession,
) -> Booking:
    """Проверка существования бронирования."""
    booking = await booking_crud.get(session=session, obj_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.BOOKING_NOT_FOUND.format(booking_id),
        )
    return booking


async def validate_pre_order_items(
    items: list[PreOrderItemCreate],
    cafe_id: int,
    session: AsyncSession,
) -> dict[int, Dish]:
    """Проверяет доступность блюд и их принадлежность к кафе."""
    dish_ids = [item.dish_id for item in items]
    result = await session.execute(select(Dish).where(Dish.id.in_(dish_ids)))
    dishes = {d.id: d for d in result.scalars().all()}

    missing = set(dish_ids) - set(dishes.keys())
    if missing:
        logger.warning(
            f'В предзаказ добавлены несуществующие блюда: {list(missing)}',
        )
        raise HTTPException(status_code=422, detail=Constants.DISH_NOT_FOUND)

    unavailable = [d_id for d_id, d in dishes.items() if not d.is_available]
    if unavailable:
        logger.warning(
            f'Попытка заказать недоступные блюда: {unavailable}',
        )
        raise HTTPException(status_code=422, detail=Constants.DISH_UNAVAILABLE)

    wrong_cafe = [d_id for d_id, d in dishes.items() if d.cafe_id != cafe_id]
    if wrong_cafe:
        logger.warning(
            f'Блюда из предзаказа принадлежат другому кафе, id: {wrong_cafe}',
        )
        raise HTTPException(
            status_code=422,
            detail=Constants.DISH_CAFE_MISMATCH,
        )

    return dishes
