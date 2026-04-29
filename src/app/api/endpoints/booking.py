"""Эндпоинты бронирования."""

# from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, status
from fastapi.param_functions import Query

from app.api.dependencies import SessionDep, UserDep
from app.api.validators.booking import (
    validate_booking_exists,
    validate_booking_slots,
    validate_cafe_slot_table,
    validate_table_slots_exists,
    validate_user_rights,
)
from app.crud.booking import booking_crud, booking_table_slot_crud
from app.schemas.booking import (
    BookingCreate,
    BookingInfo,
    BookingStatus,
    BookingTableSlotCreate,
    BookingUpdate,
)

# from app.celery.tasks import notify_admin, notify_client

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
        bool, Query(description="Показывать активные бронирования?"),
    ] = True,
    cafe_id: Annotated[
        Optional[int], Query(description="ID кафе"),
    ] = None,
    user_id: Annotated[
        Optional[int], Query(description="ID пользователя"),
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
        slots=booking.table_slots,
        booking_date=booking.booking_date,
        session=session,
    )
    await validate_cafe_slot_table(
        cafe_id=booking.cafe_id,
        slots=booking.table_slots,
        session=session,
    )
    booking_data = booking.model_dump()
    booking_data['status'] = BookingStatus.BOOKING
    booking_data['user_id'] = current_user.id

    new_booking = await booking_crud.create(
        session=session,
        obj_in=booking_data,
    )
    # TODO код для создания задачи на отправку напоминания клиенту
    # и уведомления админа
    # booking_for_celery = BookingInfo.model_validate(new_booking).model_dump()
    # notify_admin.delay(booking_for_celery)
    # booking_date = booking_for_celery.get('booking_date', None)
    # notify_client.apply_async(
    #     args=[booking_for_celery],
    #     eta=booking_date - timedelta(hours=2)
    # )

    for table_slot in booking_data.tables_slots:
        await booking_table_slot_crud.create(
            session=session,
            obj_in=BookingTableSlotCreate(**{
                'booking_id': new_booking.id,
                'table_id': table_slot.table_id,
                'slot_id': table_slot.slot_id,
            }),
        )
    await session.refresh(new_booking)
    return new_booking


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
        session=session,
    )
    booking_data = booking.model_dump(exclude_unset=True)
    booking_db = await validate_booking_exists(booking_id, session)
    await validate_user_rights(current_user, booking_db.user_id)
    await validate_booking_slots(
        slots=booking_data.table_slots,
        booking_date=booking_data.get('booking_date', booking_db.booking_date),
        session=session,
    )
    await validate_cafe_slot_table(
        cafe_id=booking_db.cafe_id,
        slots=booking_data.table_slots,
        session=session,
    )
    booking_table_slots_db = (
        await booking_table_slot_crud.get_by_attribute_multi(
            session=session,
            attr_name='booking_id',
            attr_value=booking_id,
        )
    )
    await booking_table_slot_crud.deactivate_multi(
        session=session,
        db_objs=booking_table_slots_db,
    )

    for table_slot in booking_data.pop('table_slots'):
        await booking_table_slot_crud.create(
            session=session,
            obj_in=BookingTableSlotCreate(**{
                'booking_id': booking_id,
                'table_id': table_slot.table_id,
                'slot_id': table_slot.slot_id,
            }),
        )
    booking_upd = await booking_crud.update(
        session=session,
        db_obj=booking_db,
        obj_in=booking_data,
    )
    await session.refresh(booking_upd)
    return booking_upd
