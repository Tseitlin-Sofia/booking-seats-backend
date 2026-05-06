"""Эндпоинты бронирования."""

from typing import Annotated, Optional

from fastapi import APIRouter, status
from fastapi.param_functions import Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import SessionDep, UserDep
from app.api.validators.booking import (
    validate_booking_exists,
    validate_booking_slots,
    validate_cafe_slot_table,
    validate_guest_number,
    validate_pre_order_items,
    validate_start_time,
    validate_table_slots_exists,
    validate_user_rights,
)
from app.core.logging import get_logger
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.models.booking import Booking, BookingDish, BookingTableSlot
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingStatus,
    BookingTableSlotCreate,
    BookingUpdate,
    BookingUpdateWithoutTablesSlots,
)
from app.services.booking import booking_service

logger = get_logger()
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
    return [
        BookingInfo.model_validate(booking, from_attributes=True)
        for booking in result
    ]


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
    return BookingInfo.model_validate(booking_db, from_attributes=True)


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
    await validate_table_slots_exists(
        booking=booking,
    )
    tables_slots = [slot.model_dump() for slot in booking.tables_slots]
    await validate_booking_slots(
        slots=tables_slots,
        booking_date=booking.booking_date,
        session=session,
    )
    await validate_cafe_slot_table(
        cafe_id=booking.cafe_id,
        slots=tables_slots,
        session=session,
    )
    booking_data = booking.model_dump(
        exclude={'tables_slots', 'pre_order_items'},
    )
    await validate_start_time(
        session=session,
        tables_slots=tables_slots,
        booking_date=booking.booking_date,
    )
    await validate_guest_number(
        guest_number=booking.guest_number,
        tables_slots=tables_slots,
        session=session,
    )
    if booking.pre_order_items:
        dishes_map = await validate_pre_order_items(
            booking.pre_order_items,
            booking.cafe_id,
            session,
        )
    booking_data.update({
        'status': BookingStatus.BOOKING,
        'user_id': current_user.id,
    })

    new_booking = await booking_crud.create(
        session=session,
        obj_in=booking_data,
    )

    for table_slot in tables_slots:
        await booking_table_slot_crud.create(
            session=session,
            obj_in={
                'booking_id': new_booking.id,
                'table_id': table_slot['table_id'],
                'slot_id': table_slot['slot_id'],
            },
        )

    if booking.pre_order_items:
        await booking_crud.add_pre_order_items(
            new_booking.id,
            booking.pre_order_items,
            dishes_map,
            session,
        )

    await session.refresh(new_booking)
    booking_response = BookingInfo.model_validate(
        new_booking, from_attributes=True,
    )
    await booking_service.make_notification_tasks_for_celery(
        booking_response,
        method='POST',
        session=session,
        changed_by_role=current_user.role
    )
    return booking_response


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
#     await validate_table_slots_exists(
#         booking=booking,
#     )
#     booking_data = booking.model_dump(exclude_unset=True)
#     booking_db = await validate_booking_exists(booking_id, session)
#     await validate_user_rights(current_user, booking_db.user_id)
#     booking_table_slots_db = (
#         await booking_table_slot_crud.get_by_attribute_multi(
#             session=session,
#             attr_name='booking_id',
#             attr_value=booking_id,
#             is_active=None,
#         )
#     )
#     await booking_table_slot_crud.delete_multi(
#         session=session,
#         objs=booking_table_slots_db,
#     )
#     await session.flush()
#     session.expire(booking_db, ['tables_slots'])
#     await session.refresh(booking_db)
#     await session.commit()
#     tables_slots = booking_data.pop('tables_slots')
#     await validate_booking_slots(
#         slots=tables_slots,
#         booking_date=booking_data.get(
#             'booking_date', booking_db.booking_date
#         ),
#         session=session,
#     )
#     await validate_cafe_slot_table(
#         cafe_id=booking_db.cafe_id,
#         slots=tables_slots,
#         session=session,
#     )
#     await validate_start_time(
#         session=session,
#         tables_slots=tables_slots,
#         booking_date=booking_data.get(
#             'booking_date', booking_db.booking_date
#         ),
#     )
#     await validate_guest_number(
#         guest_number=booking_data.get(
#             'guest_number', booking_db.guest_number
#         ),
#         tables_slots=tables_slots,
#         session=session,
#     )
#     if booking.pre_order_items:
#         await booking_crud.delete_multi(
#             session=session,
#             objs=booking_db.pre_order_items,
#         )
#         await session.flush()
#         session.expire(booking_db, ['pre_order_items'])
#         await session.refresh(booking_db)
#         await session.commit()
#         dishes_map = await validate_pre_order_items(
#             booking.pre_order_items,
#             booking_db.cafe_id,
#             session,
#         )
#         await booking_crud.add_pre_order_items(
#             booking_db.id,
#             booking.pre_order_items,
#             dishes_map,
#             session,
#         )
#     for table_slot in tables_slots:
#         await booking_table_slot_crud.create(
#             session=session,
#             obj_in=BookingTableSlotCreate(**{
#                 'booking_id': booking_id,
#                 'table_id': table_slot['table_id'],
#                 'slot_id': table_slot['slot_id'],
#                 'is_active': booking_data.get('is_active', True),
#             }),
#         )
#     booking_upd = await booking_crud.update(
#         session=session,
#         db_obj=booking_db,
#         obj_in=BookingUpdateWithoutTablesSlots(**booking_data),
#     )
#     await session.refresh(booking_upd, attribute_names=[
#         "tables_slots",
#         "tables_slots.slot",
#         "tables_slots.table",
#         "pre_order_items",
#         "pre_order_items.dish",
#     ])
#     booking_response = BookingInfo.model_validate(
#         booking_upd, from_attributes=True,
#     )
#     await booking_service.make_notification_tasks_for_celery(
#         booking_response, method='PATCH', session=session,
#     )
#     return booking_response

@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновление информации о бронировании по его ID',
    description=(
        'Обновление информации о бронировании по его ID. '
        'Для администраторов и менеджеров - все бронирования, '
        'для пользователей - только свои.'
    ),
    response_description='Подробный вывод обновленного бронирования',
)
async def update_booking(
    session: SessionDep,
    booking_id: int,
    booking: BookingUpdate,
    current_user: UserDep,
) -> BookingInfo:
    """Обновление бронирования."""
    await validate_table_slots_exists(booking=booking)
    booking_data = booking.model_dump(exclude_unset=True)
    booking_db = await validate_booking_exists(booking_id, session)
    await validate_user_rights(current_user, booking_db.user_id)

    # Удаляем старые tables_slots
    booking_table_slots_db = (
        await booking_table_slot_crud.get_by_attribute_multi(
            session=session,
            attr_name='booking_id',
            attr_value=booking_id,
            is_active=None,
        )
    )
    await booking_table_slot_crud.delete_multi(
        session=session,
        objs=booking_table_slots_db,
    )
    await session.flush()
    session.expunge_all()

    # Заново загружаем booking_db
    booking_db = await validate_booking_exists(booking_id, session)

    tables_slots = booking_data.pop('tables_slots')
    await validate_booking_slots(
        slots=tables_slots,
        booking_date=booking_data.get('booking_date', booking_db.booking_date),
        session=session,
    )
    await validate_cafe_slot_table(
        cafe_id=booking_db.cafe_id,
        slots=tables_slots,
        session=session,
    )
    await validate_start_time(
        session=session,
        tables_slots=tables_slots,
        booking_date=booking_data.get('booking_date', booking_db.booking_date),
    )
    await validate_guest_number(
        guest_number=booking_data.get('guest_number', booking_db.guest_number),
        tables_slots=tables_slots,
        session=session,
    )

    # Удаляем старые pre_order_items, если есть новые
    if booking.pre_order_items:
        pre_order_items_db = booking_db.pre_order_items
        await booking_crud.delete_multi(
            session=session,
            objs=pre_order_items_db,
        )
        await session.flush()
        session.expunge_all()
        booking_db = await validate_booking_exists(booking_id, session)

    # Обновляем основные поля бронирования
    booking_upd = await booking_crud.update(
        session=session,
        db_obj=booking_db,
        obj_in=BookingUpdateWithoutTablesSlots(**booking_data),
    )

    # Создаём новые tables_slots
    for table_slot in tables_slots:
        await booking_table_slot_crud.create(
            session=session,
            obj_in=BookingTableSlotCreate(**{
                'booking_id': booking_id,
                'table_id': table_slot['table_id'],
                'slot_id': table_slot['slot_id'],
                'is_active': booking_data.get('is_active', True),
            }),
        )

    # Создаём новые pre_order_items
    if booking.pre_order_items:
        dishes_map = await validate_pre_order_items(
            booking.pre_order_items,
            booking_db.cafe_id,
            session,
        )
        await booking_crud.add_pre_order_items(
            booking_id,
            booking.pre_order_items,
            dishes_map,
            session,
        )

    # Коммитим все изменения
    await session.commit()

    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            joinedload(Booking.tables_slots).joinedload(BookingTableSlot.slot),
            joinedload(Booking.tables_slots).joinedload(BookingTableSlot.table),
            joinedload(Booking.pre_order_items).joinedload(BookingDish.dish),
            joinedload(Booking.user),
            joinedload(Booking.cafe),
        )
    )
    result = await session.execute(stmt)
    booking_upd = result.unique().scalar_one()

    # Формируем ответ и задачи Celery
    booking_response = BookingInfo.model_validate(
        booking_upd, from_attributes=True,
    )
    await booking_service.make_notification_tasks_for_celery(
        booking_response,
        method='PATCH',
        session=session,
        changed_by_role=current_user.role
    )
    return booking_response