from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ManagerDep, SessionDep, UserDep
from app.api.validators.cafe import get_cafe_or_404
from app.api.validators.slot import (
    check_slots_intersections,
    validate_slot,
    validate_slot_times,
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
    await get_cafe_or_404(session, cafe_id, is_exist=True)
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
    slot: TimeSlotCreate,
    session: SessionDep,
    user: ManagerDep,
) -> TimeSlotInfo:
    """Создание нового слота в кафе."""
    cafe = await get_cafe_or_404(session, cafe_id)
    await validate_slot_times(
        start_time=slot.start_time,
        end_time=slot.end_time,
    )
    await check_slots_intersections(
        start_time=slot.start_time,
        end_time=slot.end_time,
        cafe_id=cafe_id,
        session=session,
    )
    slot_data = slot.model_dump()
    slot_data['cafe_id'] = cafe_id
    slot_new = await slot_crud.create(slot_data, session)

    from app.schemas.cafe import CafeShortInfo

    return TimeSlotInfo(
        id=slot_new.id,
        start_time=slot_new.start_time,
        end_time=slot_new.end_time,
        description=slot_new.description,
        is_active=slot_new.is_active,
        cafe=CafeShortInfo.model_validate(cafe, from_attributes=True),
        created_at=slot_new.created_at,
        updated_at=slot_new.updated_at,
    )


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
    user: ManagerDep,
) -> TimeSlotInfo:
    """Обновление информации о слоте в кафе."""
    await get_cafe_or_404(session, cafe_id, is_exist=True)
    slot_db = await slot_crud.get_slot_or_404(session=session, slot_id=slot_id)
    slot_data = slot_in.model_dump(exclude_unset=True)
    start_time = slot_data.get('start_time', slot_db.start_time)
    end_time = slot_data.get('end_time', slot_db.end_time)
    await validate_slot_times(
        start_time=start_time,
        end_time=end_time,
    )
    await check_slots_intersections(
        start_time=start_time,
        end_time=end_time,
        cafe_id=cafe_id,
        session=session,
        slot_id=slot_id,
    )
    slot_upd = await slot_crud.update(
        obj_in=slot_in,
        db_obj=slot_db,
        session=session,
    )
    await session.refresh(slot_db)
    return TimeSlotInfo.model_validate(slot_upd, from_attributes=True)
