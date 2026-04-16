from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.crud.slot import slot_crud
from app.api.validators.table import (
    check_cafe_exists
)
from app.schemas.slot import SlotCreate, SlotDB


router = APIRouter()


@router.get(
    '/',
    response_model=list[SlotDB],
    summary='Получение списка слотов для бронирования столиков в кафе',
)
async def get_slots(
    cafe_id: int,
    session: SessionDep,
) -> list[SlotDB]:
    """Возвращает все слоты для бронирования столиков в заданном кафе."""
    await check_cafe_exists(cafe_id, session)
    return await SlotDB.from_slots_by_cafe(
        cafe_id=cafe_id,
        session=session,
    )