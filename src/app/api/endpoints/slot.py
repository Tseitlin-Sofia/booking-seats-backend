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
    return CRUDBase.get_by_attribute_multi(slots)


@router.post(
    '/', response_model=SlotBase,
    summary='Создание нового слота для бронирования столика',
)
async def create_slot(
    slot_data: SlotCreate,
    session: SessionDep,
) -> SlotBase:
    """Создание нового слота для бронирования столика."""
    await get_cafe_or_404(session, slot_data.cafe_id, True)
    await check_slots_intersections(
        **slot_data.model_dump(), session=session,
    )
    return await slot_crud.create(slot_data, session)
