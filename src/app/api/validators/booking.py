"""Валидаторы для эндпоинтов бронирования."""

from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.crud.cafe import cafe_crud
from app.models import Dish, Slot, Table, User
from app.models.booking import Booking
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
)
from app.schemas.dish import PreOrderItemCreate

logger = get_logger()


async def validate_booking_slots(
    slots: list[dict[str, int]],
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=Constants.SLOTS_UNAVAILABLE,
        )


async def validate_cafe_slot_table(
    cafe_id: int,
    slots: list[dict[str, int]],
    session: AsyncSession,
) -> None:
    """Валидация того слот и стол существуют и принадлежат правильному кафе."""
    cafe_db = await cafe_crud.get(session=session, obj_id=cafe_id)
    if not cafe_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.CAFE_DOES_NOT_EXIST,
        )
    slot_ids = [slot['slot_id'] for slot in slots]
    table_ids = [slot['table_id'] for slot in slots]

    slots_db = await booking_table_slot_crud.get_by_id_list_bts(
        session=session,
        cafe_id=cafe_id,
        model=Slot,
        id_list=slot_ids,
    )
    tables_db = await booking_table_slot_crud.get_by_id_list_bts(
        session=session,
        cafe_id=cafe_id,
        model=Table,
        id_list=table_ids,
    )
    unique_set = set()
    for table_slot in slots:
        slot_tuple = tuple(sorted(table_slot.items()))
        if slot_tuple in unique_set:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=Constants.DUBLICATE_SLOTS,
            )
        unique_set.add(slot_tuple)
    if (
        len(set(table_ids)) != len(tables_db)
        or len(set(slot_ids)) != len(slots_db)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=Constants.SLOTS_OR_TABLES_NOT_IN_CAFE,
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

    if user.is_admin or user.is_manager or user.id == requested_user_id:
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
    booking = await booking_crud.get(
        session=session,
        obj_id=booking_id,
        eager_options=booking_crud.booking_full_load_options(),
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.BOOKING_NOT_FOUND,
        )
    return booking


async def validate_table_slots_exists(
    booking: BookingUpdate | BookingCreate,
) -> None:
    """Проверка передачи списка слотов."""
    booking_data = booking.model_dump()
    if (
        booking_data.get('tables_slots') is None
        or len(
            booking_data['tables_slots'],
        )
        == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Constants.LIST_SLOTS_ERROR,
        )


async def validate_start_time(
    session: AsyncSession,
    tables_slots: list[dict[str, int]],
    booking_date: date,
) -> None:
    """Проверка времени начала бронирования."""
    if await booking_crud.get_start_datetime_by_slots_and_date(
        tables_slots=tables_slots,
        booking_date=booking_date,
        session=session,
    ) < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=Constants.INVALID_START_TIME_ERROR,
        )


async def validate_guest_number(
    guest_number: int,
    tables_slots: list[dict[str, int]],
    session: AsyncSession,
) -> None:
    """Проверяет количество гостей на основе вместимости столов."""
    max_guests = await booking_table_slot_crud.get_capacity(
        tables_slots=tables_slots, session=session,
    )
    if guest_number > max_guests or guest_number < Constants.MIN_GUESTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=Constants.GUEST_NUMBER_ERROR.format(
                Constants.MIN_GUESTS, max_guests,
            ),
        )


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
