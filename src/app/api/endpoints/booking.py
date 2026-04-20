"""Эндпоинты бронирования."""

from typing import Annotated, Optional
from fastapi import APIRouter
from fastapi.param_functions import Query

from app.api.dependencies import SessionDep
from app.api.validators.booking import (
    validate_user_rights,
    validate_booking_slots,
    validate_cafe_slot_table,
)
from app.models import Booking, BookingTableSlot
from app.schemas.booking import (
    BookingInfo,
    BookingTableSlotShortInfo,
    BookingCreate,
    BookingUpdate,
)

router = APIRouter()


@router.get(
    '/',
    response_model=list[BookingInfo],
    response_model_exclude_none=True,
    summary='Получение списка бронирований',
    description=(
        'Получение списка бронирований. '
        'Для администраторов и менеджеров - все бронирования '
        '(с возможностью выбора), '
        'для пользователей - только свои.'
    ),
    response_description='Подробный вывод всех бронирований',
)
async def get_bookings(
    show_active: Annotated[bool, Query()] = True,
    cafe_id: Annotated[Optional[int], Query()] = None,
    user_id: Annotated[Optional[int], Query()] = None,
    session: SessionDep,
) -> list[BookingInfo]:
    """Получение списка бронирований."""
    user = await current_user_MOCK(session)
    if user.is_user:
        await validate_user_rights(user, user_id)
        user_id = user.id



@router.post(
    '/',
    response_model=BookingInfo,
    summary='Создание бронирования',
    description=(
        'Создание бронирования. '
        'Пользователь может забронировать свободный слот в кафе.'
    ),
    response_description='Подробный вывод созданного бронирования',
)
async def create_booking(
    booking: BookingCreate,
    session: SessionDep,
) -> BookingInfo:
    """Создание бронирования."""
    slots = BookingTableSlot(**booking.table_slots.model_dump())
    booking_obj = Booking(**booking.model_dump())
    user = await current_user_MOCK(session)
    await validate_booking_slots(..., session)
    await validate_cafe_slot_table(..., session)
