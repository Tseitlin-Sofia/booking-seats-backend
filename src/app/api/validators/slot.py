from datetime import time
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.slot import slot_crud


async def get_slot_or_404(
    session: AsyncSession,
    slot_id: int,
    is_active: bool = True,
) -> Any:
    """Получает слот по id или возвращает 404 ошибку."""
    slot = await slot_crud.get_slot_or_404(session, slot_id, is_active)
    if not slot:
        raise HTTPException(
            status_code=404,
            detail='Слот для бронирования столика не найден.',
        )
    return slot


async def check_slots_intersections(
        *,
        start_time: time,
        end_time: time,
        cafe_id: int,
        session: AsyncSession,
        slot_id: int | None = None,
) -> None:
    """Проверяет пересечение временных слотов в рамках одного кафе."""
    slots = await slot_crud.get_slots_at_the_same_time(
        start_time=start_time,
        end_time=end_time,
        cafe_id=cafe_id,
        session=session,
        slot_id=slot_id,
    )
    if slots:
        raise HTTPException(
            status_code=422,
            detail='Слот пересекается с уже существующим слотом в этом кафе.',
        )
