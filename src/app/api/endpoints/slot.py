from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.dependencies import SessionDep, UserDep
from app.api.validators.cafe import get_cafe_or_404
from app.api.validators.slot import (
    check_slots_intersections,
    validate_slot,
)
from app.crud.slot import slot_crud
from app.schemas.slot import (
    TimeSlotCreate,
    TimeSlotInfo,
    TimeSlotUpdate,
)

router = APIRouter()


@router.get(
    '/',
    response_model=list[TimeSlotInfo],
    summary='Получение списка слотов в кафе',
)
async def get_slots(
    cafe_id: int,
    session: SessionDep,
    user: UserDep,
    show_active: Optional[bool] = True,
) -> list[TimeSlotInfo]:
    """Возвращает все слоты для заданного кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    if user.is_user:
        show_active = True
    slots = await slot_crud.get_slots_by_cafe(cafe_id, session, show_active)
    return [
        TimeSlotInfo.model_validate(slot, from_attributes=True)
        for slot in slots
    ]


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Получение слота по ID',
)
async def get_slot(
    cafe_id: int,
    slot_id: int,
    session: SessionDep,
    user: UserDep,
) -> TimeSlotInfo:
    """Возвращает информацию о конкретном слоте в кафе."""
    slot = await validate_slot(
        cafe_id=cafe_id,
        session=session,
        slot_id=slot_id,
    )
    if user.is_user and not slot.is_active:
        raise HTTPException(404, detail='Слот не найден!')
    return TimeSlotInfo.model_validate(slot, from_attributes=True)


@router.post(
    '/',
    response_model=TimeSlotInfo,
    summary='Создание нового слота в кафе',
)
async def create_slot(
    cafe_id: int,
    slot_data: TimeSlotCreate,
    session: SessionDep,
    user: UserDep,
) -> TimeSlotInfo:
    """Создание нового слота в кафе."""
    if not (user.is_admin or user.is_manager):
        raise HTTPException(403, detail='Доступ запрещен!')
    await get_cafe_or_404(session, cafe_id, True)
    await check_slots_intersections(
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        cafe_id=cafe_id,
        session=session,
    )
    slot_data_dict = slot_data.model_dump()
    slot_data_dict['cafe_id'] = cafe_id
    return await slot_crud.create(slot_data_dict, session)


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Обновление информации о слоте',
)
async def update_slot(
    cafe_id: int,
    slot_id: int,
    slot_in: TimeSlotUpdate,
    session: SessionDep,
    user: UserDep,
) -> TimeSlotInfo:
    """Обновление информации о слоте в кафе."""
    if not (user.is_admin or user.is_manager):
        raise HTTPException(403, detail='Доступ запрещен!')
    await get_cafe_or_404(session, cafe_id, True)
    slot_db = await slot_crud.get_slot_or_404(session=session, slot_id=slot_id)
    await check_slots_intersections(
        start_time=slot_in.start_time or slot_db.start_time,
        end_time=slot_in.end_time or slot_db.end_time,
        cafe_id=cafe_id,
        session=session,
        slot_id=slot_id,
    )
    slot_upd = await slot_crud.update(
        obj_in=slot_in,
        db_obj=slot_db,
        session=session,
    )
    return TimeSlotInfo.model_validate(slot_upd, from_attributes=True)
