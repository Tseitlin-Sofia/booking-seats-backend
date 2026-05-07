"""Эндпоинты бронирования."""

from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Query

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
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingStatus,
    BookingTableSlotCreate,
    BookingTableSlotShortInfo,
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
        exclude={'tables_slots'},
        exclude_unset=True,
    )
    pre_order_items = booking_data.pop('pre_order_items', None)
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
            pre_order_items,
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
            pre_order_items,
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
        changed_by_role=current_user.role,
    )
    return booking_response


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
    tables_slots = booking_data.pop('tables_slots', None)
    pre_order_items = booking_data.pop('pre_order_items', None)
    booking_db = await validate_booking_exists(booking_id, session)
    pre_order_items_db = booking_db.pre_order_items
    if pre_order_items == []:
        await booking_crud.delete_multi(
            session=session,
            objs=pre_order_items_db,
        )
        del booking_db.pre_order_items
    elif pre_order_items not in (None, []):
        dishes_map = await validate_pre_order_items(
            pre_order_items,
            booking_db.cafe_id,
            session,
        )
        await booking_crud.delete_multi(
            session=session,
            objs=pre_order_items_db,
        )
        del booking_db.pre_order_items
        booking_db = await booking_crud.refresh_booking(
            session=session,
            booking_id=booking_id,
        )
    booking_table_slots_db = (
        await booking_table_slot_crud.get_by_attribute_multi(
            session=session,
            attr_name='booking_id',
            attr_value=booking_id,
            is_active=None,
        )
    )
    booking_table_slots_db_data = [
        {'slot_id': int(slot.slot_id), 'table_id': int(slot.table_id)}
        for slot in booking_table_slots_db
    ]
    await validate_user_rights(current_user, booking_db.user_id)
    if tables_slots:
        await validate_cafe_slot_table(
            cafe_id=booking_db.cafe_id,
            slots=tables_slots,
            session=session,
        )
    await validate_start_time(
        session=session,
        tables_slots=(
            tables_slots if tables_slots else booking_table_slots_db_data
        ),
        booking_date=booking_data.get('booking_date', booking_db.booking_date),
    )
    await validate_guest_number(
        guest_number=booking_data.get('guest_number', booking_db.guest_number),
        tables_slots=(
            tables_slots if tables_slots else booking_table_slots_db_data
        ),
        session=session,
    )
    await booking_table_slot_crud.deactivate_multi(
        session=session,
        db_objs=booking_table_slots_db,
    )
    if pre_order_items not in (None, []):
        await booking_crud.add_pre_order_items(
            booking_id=booking_id,
            items=pre_order_items,
            dishes_map=dishes_map,
            session=session,
        )
    booking_db = await booking_crud.refresh_booking(
        session=session,
        booking_id=booking_id,
    )
    try:
        await validate_booking_slots(
            slots=(
                tables_slots if tables_slots else booking_table_slots_db_data
            ),
            booking_date=booking_data.get(
                'booking_date', booking_db.booking_date,
            ),
            session=session,
        )
        await booking_table_slot_crud.delete_multi(
            session=session,
            objs=booking_table_slots_db,
        )
        await booking_crud.refresh_booking(
            session=session,
            booking_id=booking_id,
        )
        booking_db.tables_slots = []
        await session.flush()
    except HTTPException as exc:
        # Возвращаем деактивированные слоты
        await booking_table_slot_crud.deactivate_multi(
            session=session,
            db_objs=booking_table_slots_db,
            reverse=True,
        )
        raise exc
    booking_db = await booking_crud.refresh_booking(
        session=session,
        booking_id=booking_id,
    )
    # Обновляем основные поля бронирования
    booking_upd = await booking_crud.update(
        session=session,
        db_obj=booking_db,
        obj_in=BookingUpdateWithoutTablesSlots(**booking_data),
    )

    # Создаём новые tables_slots
    for table_slot in (
        tables_slots if tables_slots else booking_table_slots_db_data
    ):
        await booking_table_slot_crud.create(
            session=session,
            obj_in=BookingTableSlotCreate(**{
                'booking_id': booking_id,
                'table_id': table_slot['table_id'],
                'slot_id': table_slot['slot_id'],
                'is_active': True,
            }),
        )

    booking_upd = await booking_crud.refresh_booking(session, booking_id)
    await session.commit()
    booking_upd = await booking_crud.refresh_booking(session, booking_id)
    booking_response = BookingInfo.model_validate(
        booking_upd, from_attributes=True,
    )
    booking_response.tables_slots = [
        BookingTableSlotShortInfo.model_validate(
            table_slot, from_attributes=True,
        )
        for table_slot in await booking_table_slot_crud.get_by_attribute_multi(
            session=session, attr_value=booking_id, attr_name='booking_id',
        )
    ]
    await booking_service.make_notification_tasks_for_celery(
        booking_response,
        method='PATCH',
        session=session,
        changed_by_role=current_user.role,
    )
    return booking_response
