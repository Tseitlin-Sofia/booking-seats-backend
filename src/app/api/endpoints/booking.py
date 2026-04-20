"""Эндпоинты бронирования."""

from typing import Annotated, Optional

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Query

from app.api.dependencies import SessionDep
from app.api.validators.booking import (
    validate_booking_slots,
    validate_cafe_slot_table,
    validate_user_rights,
)
from app.core.constants import BookingConstants as Constants
from app.models.booking import Booking, BookingTableSlot
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingUpdate,
)

from app.crud.booking import booking_crud, booking_table_slot_crud

router = APIRouter()

current_user_mock = None


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
    session: SessionDep,
    show_active: Annotated[bool, Query()] = True,
    cafe_id: Annotated[Optional[int], Query()] = None,
    user_id: Annotated[Optional[int], Query()] = None,
) -> list[BookingInfo]:
    """Получение списка бронирований."""
    user = await current_user_mock(session)
    if user.is_user:
        await validate_user_rights(user, user_id)
        user_id = user.id
    return await booking_crud.get_bookings(
        session=session,
        show_active=show_active,
        cafe_id=cafe_id,
        user_id=user_id,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Получение бронирования',
    description=(
        'Получение бронирования по его ID. '
        'Пользователь может получить информацию о своем бронировании.'
    ),
    response_description='Подробный вывод бронирования',
)
async def get_booking(
    session: SessionDep,
    booking_id: int,
) -> BookingInfo:
    """Получение бронирования по его ID."""
    booking_db = await booking_crud.get(
        session=session,
        obj_id=booking_id,
    )
    if not booking_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.BOOKING_NOT_FOUND.format(booking_id),
        )
    user = current_user_mock
    await validate_user_rights(user, booking_db.user_id)
    return booking_db


# TODO: Перенести в круд методы.
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
    session: SessionDep,
    booking: BookingCreate,
) -> BookingInfo:
    """Создание бронирования."""
    slots = BookingTableSlot(**booking.table_slots.model_dump())
    booking_obj = Booking(**booking.model_dump())
    user = current_user_mock
    await validate_booking_slots(
        slots=slots,
        date=booking_obj.date,
        session=session,
    )
    await booking_table_slot_crud.create(
        session=session,
        obj_in=slots,
    )
    await validate_cafe_slot_table(
        cafe_id=booking_obj.cafe_id,
        slots=slots,
        session=session,
    )
    await booking_crud.create(
        session=session,
        obj_in=booking_obj,
        user=user,
    )
    return booking_obj


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновление бронирования',
    description=(
        'Обновление бронирования. '
        'Пользователь может обновить свое бронирование.'
        'Амдминстратор или менеджер - любое'
    ),
    response_description='Подробный вывод обновленного бронирования',
)
async def update_booking(
    session: SessionDep,
    booking_id: int,
    booking: BookingUpdate,
) -> BookingInfo:
    """Обновление бронирования."""
    booking_db = await booking_crud.get(
        session=session,
        obj_id=booking_id,
    )
    if not booking_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Constants.BOOKING_NOT_FOUND.format(booking_id),
        )
    user = current_user_mock
    await validate_user_rights(user, booking_db.user_id)
    slots = BookingTableSlot(**booking.table_slots.model_dump())
    await validate_booking_slots(
        slots=slots,
        date=booking_db.date,
        session=session,
    )
    await booking_table_slot_crud.update(
        session=session,
        db_obj=booking_db.table_slots,
        obj_in=slots,
    )
    await validate_cafe_slot_table(
        cafe_id=booking_db.cafe_id,
        slots=slots,
        session=session,
    )
    await booking_crud.update(
        session=session,
        db_obj=booking_db,
        obj_in=booking,
    )
    return booking_db
