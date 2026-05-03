"""Эндпоинты бронирования."""

from datetime import timedelta
from typing import Annotated, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, status
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
from app.celery.celery_app import celery_app
from app.celery.tasks import notify_admin, notify_client
from app.core.db import Base
from app.core.logging import get_logger
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingStatus,
    BookingTableSlotCreate,
    BookingUpdate,
    BookingUpdateWithoutTablesSlots,
)
from app.services.task import get_reminder_id

logger = get_logger()
router = APIRouter()


def _make_notification_tasks_for_celery(
    booking_obj: Base,
    method: str,
) -> None:
    """Создание задачи в celery.

    Созадется задача на отправку уведомления админинистратору и напоминания
    клиенту о брони.
    """
    booking_for_celery = BookingInfo.model_validate(booking_obj).model_dump()
    task_id = get_reminder_id(booking_for_celery.get('id'))
    if method == 'PATCH':
        AsyncResult(task_id, app=celery_app).revoke()
    notify_admin.delay(method, booking_for_celery)
    booking_date = booking_for_celery.get('booking_date')
    if not booking_date:
        logger.warning(
            'Дата бронирования не указана для booking_id={}',
            booking_for_celery.get('id'),
        )
        return

    notify_client.apply_async(
        args=[booking_for_celery],
        eta=booking_date - timedelta(hours=2),
        task_id=task_id,
    )


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
    booking_data.update({
        'status': BookingStatus.BOOKING,
        'user_id': current_user.id,
    })

    new_booking = await booking_crud.create(
        session=session,
        obj_in=booking_data,
    )
    # Код для создания задачи на отправку напоминания клиенту
    # и уведомления админа
    # _make_notification_tasks_for_celery(new_booking, method='POST')

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
    await validate_table_slots_exists(
        booking=booking,
    )
    booking_data = booking.model_dump(exclude_unset=True)
    booking_db = await validate_booking_exists(booking_id, session)
    await validate_user_rights(current_user, booking_db.user_id)
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
    session.expire(booking_db, ['tables_slots'])
    await session.refresh(booking_db)
    await session.commit()
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
    booking_upd = await booking_crud.update(
        session=session,
        db_obj=booking_db,
        obj_in=BookingUpdateWithoutTablesSlots(**booking_data),
    )
    await session.refresh(booking_upd)
    # _make_notification_tasks_for_celery(booking_upd, method='PATCH')
    return BookingInfo.model_validate(booking_upd, from_attributes=True)
