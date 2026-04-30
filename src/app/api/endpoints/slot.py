from typing import Optional

from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.api.validators.cafe import get_cafe_or_404
from app.api.validators.slot import check_slots_intersections
from app.crud.base import CRUDBase
from app.crud.slot import slot_crud
from app.schemas.slot import SlotBase, SlotCreate

router = APIRouter()


@router.get(
    '/',
    response_model=list[SlotBase],
    summary='Получение списка слотов для бронирования столиков в кафе',
)
async def get_slots(
    cafe_id: int,
    session: SessionDep,
    active: Optional[bool] = True,
) -> list[SlotBase]:
    """Возвращает все слоты для бронирования столиков в заданном кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    slots = await slot_crud.get_slots_by_cafe(cafe_id, session)
    if not active:
        return slots
    return await CRUDBase.get_by_attribute_multi(
        self=slot_crud,
        attr_name='cafe_id',
        attr_value=cafe_id,
        session=session,
        is_active=True,
    )


@router.post(
    '/', response_model=SlotBase,
    summary='Создание нового слота для бронирования столика',
)
async def create_slot(
    cafe_id: int,
    slot_data: SlotCreate,
    session: SessionDep,
) -> SlotBase:
    """Создание нового слота для бронирования столика."""
    slot_data_dict = slot_data.model_dump()
    slot_data_dict['cafe_id'] = cafe_id
    await get_cafe_or_404(session, cafe_id, True)
    await check_slots_intersections(
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        cafe_id=cafe_id,
        table_id=slot_data.table_id,
        session=session,
    )
    return await slot_crud.create(slot_data_dict, session)


@router.patch(
    '/{slot_id}',
    response_model=SlotBase,
    summary='Обновление информации о слоте для бронирования столика',
)
async def update_slot(
    cafe_id: int,
    slot_id: int,
    slot_data: SlotCreate,
    session: SessionDep,
) -> SlotBase:
    """Обновление информации о слоте для бронирования столика."""
    slot_data_dict = slot_data.model_dump()
    slot_data_dict['cafe_id'] = cafe_id
    await get_cafe_or_404(session, cafe_id, True)
    await check_slots_intersections(
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        cafe_id=cafe_id,
        table_id=slot_data.table_id,
        session=session,
        slot_id=slot_id,
    )
    return await slot_crud.update(slot_id, slot_data_dict, session)
