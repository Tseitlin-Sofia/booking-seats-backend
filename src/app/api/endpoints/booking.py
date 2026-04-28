"""Эндпоинты бронирования."""

from typing import Annotated, Optional

from fastapi import APIRouter, status
from fastapi.param_functions import Query

from app.api.dependencies import SessionDep, UserDep
from app.api.validators.booking import (
    validate_booking_exists,
    validate_booking_slots,
    validate_cafe_slot_table,
    validate_pre_order_items,
    validate_user_rights,
)
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.schemas.booking import BookingCreate, BookingInfo, BookingStatus

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
    session: SessionDep,
    current_user: UserDep,
    show_active: Annotated[
        bool,
        Query(description='Показывать активные бронирования?'),
    ] = True,
    cafe_id: Annotated[
        Optional[int],
        Query(description='ID кафе'),
    ] = None,
    user_id: Annotated[
        Optional[int],
        Query(description='ID пользователя'),
    ] = None,
) -> list[BookingInfo]:
    """Получение списка бронирований."""
    if current_user.is_user:
        user_id = current_user.id
    else:
        if user_id:
            await validate_user_rights(current_user, user_id)

    result = await booking_crud.get_bookings(
        session=session,
        show_active=show_active,
        cafe_id=cafe_id,
        user_id=user_id,
    )
    return list(result.scalars().all())


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Получение информации о бронировании по его ID',
    description=(
        'Получение информации о бронировании по его ID. '
        'Для администраторов и менеджеров - все бронирования, '
        'для пользователей - только свои.'
    ),
    response_description='Подробный вывод бронирования',
)
async def get_booking(
    session: SessionDep,
    booking_id: int,
    current_user: UserDep,
) -> BookingInfo:
    """Получение бронирования по его ID."""
    booking_db = await validate_booking_exists(booking_id, session)
    await validate_user_rights(current_user, booking_db.user_id)
    return booking_db


@router.post(
    '/',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового бронирования',
    description=(
        'Создание нового бронирования. '
        'Только для авторизированных пользователей.'
    ),
    response_description='Подробный вывод созданного бронирования',
)
async def create_booking(
    session: SessionDep,
    booking: BookingCreate,
    current_user: UserDep,
) -> BookingInfo:
    """Создание бронирования."""
    await validate_booking_slots(
        slots=booking.tables_slots,
        booking_date=booking.booking_date,
        session=session,
    )
    await validate_cafe_slot_table(
        cafe_id=booking.cafe_id,
        slots=booking.tables_slots,
        session=session,
    )
    booking_data = booking.model_dump(
        exclude={'tables_slots', 'pre_order_items'},
    )
    booking_data.update({
        'status': BookingStatus.BOOKING,
        'user_id': current_user.id,
    })

    new_booking = await booking_crud.create(
        session=session,
        obj_in=booking_data,
    )

    for tables_slot in booking.tables_slots:
        await booking_table_slot_crud.create(
            session=session,
            obj_in={
                'booking_id': new_booking.id,
                'table_id': tables_slot.table_id,
                'slot_id': tables_slot.slot_id,
            },
        )

    if booking.pre_order_items:
        dishes_map = await validate_pre_order_items(
            booking.pre_order_items,
            booking.cafe_id,
            session,
        )
        await booking_crud.add_pre_order_items(
            new_booking.id,
            booking.pre_order_items,
            dishes_map,
            session,
        )

    await session.refresh(new_booking)
    return BookingInfo.model_validate(new_booking, from_attributes=True)


# TODO: Можно удалить слоты и создать заново! cascade inactive
# @router.patch(
#     '/{booking_id}',
#     response_model=BookingInfo,
#     summary='Обновление информации о бронировании по его ID',
#     description=(
#         'Обновление информации о бронировании по его ID. '
#         'Для администраторов и менеджеров - все бронирования, '
#         'для пользователей - только свои.'
#     ),
#     response_description='Подробный вывод обновленного бронирования',
# )
# async def update_booking(
#     session: SessionDep,
#     booking_id: int,
#     booking: BookingUpdate,
#     current_user: UserDep,
# ) -> BookingInfo:
#     """Обновление бронирования."""
#     booking_db = await validate_booking_exists(booking_id, session)
#     booking_table_slots_db = await booking_table_slot_crud.get(
#         session=session,
#         id=booking_id,
#     )
#     await validate_user_rights(current_user, booking_db.user_id)

#     if booking.tables_slots is not None:
#         await validate_booking_slots(
#             slots=booking.tables_slots,
#             booking_date=booking.booking_date or booking_db.booking_date,
#             session=session,
#         )
#         await validate_cafe_slot_table(
#             cafe_id=booking_db.cafe_id,
#             slots=booking.tables_slots,
#             session=session,
#         )
#         await booking_table_slot_crud.update(
#             session=session,
#             db_obj=booking_table_slots_db,
#             obj_in=booking.tables_slots,
#         )
#     return await booking_crud.update(
#         session=session,
#         db_obj=booking_db,
#         obj_in=booking.model_dump(exclude_unset=True),
#     )
