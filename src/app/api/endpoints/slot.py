from typing import Optional

from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.api.validators.cafe import get_cafe_or_404
from app.api.validators.slot import check_slots_intersections
from app.crud.base import CRUDBase
from app.crud.slot import slot_crud
from app.schemas.slot import SlotBase, SlotCreate, SlotUpdate

router = APIRouter()


@router.get(
    '/',
    response_model=list[SlotBase],
    summary='Получение списка слотов в кафе',
)
async def get_slots(
    cafe_id: int,
    session: SessionDep,
    active: Optional[bool] = True,
) -> list[SlotBase]:
    """Возвращает все слоты для заданного кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    if not active:
        return await slot_crud.get_slots_by_cafe(cafe_id, session)
    return await CRUDBase.get_by_attribute_multi(
        self=slot_crud,
        attr_name='cafe_id',
        attr_value=cafe_id,
        session=session,
        is_active=True,
    )


@router.post(
    '/',
    response_model=SlotBase,
    summary='Создание нового слота в кафе',
)
async def create_slot(
    cafe_id: int,
    slot_data: SlotCreate,
    session: SessionDep,
) -> SlotBase:
    """Создание нового слота в кафе."""
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
    response_model=SlotBase,
    summary='Обновление информации о слоте',
)
async def update_slot(
    cafe_id: int,
    slot_id: int,
    slot_data: SlotUpdate,
    session: SessionDep,
) -> SlotBase:
    """Обновление информации о слоте в кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    await check_slots_intersections(
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        cafe_id=cafe_id,
        session=session,
        slot_id=slot_id,
    )
    slot_data_dict = slot_data.model_dump(exclude_unset=True)
    return await slot_crud.update(slot_id, slot_data_dict, session)
