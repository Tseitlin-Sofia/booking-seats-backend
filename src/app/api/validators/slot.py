from datetime import time

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.slot import slot_crud
from app.models.slot import Slot

logger = get_logger()


async def validate_slot(
    cafe_id: int,
    session: AsyncSession,
    slot_id: int,
    is_active: bool = True,
) -> Slot:
    """Получает слот по id или возвращает 404 ошибку."""
    from app.api.validators.cafe import get_cafe_or_404

    await get_cafe_or_404(session, cafe_id, is_active)
    return await slot_crud.get_slot_or_404(session, slot_id, is_active)


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


async def validate_slot_times(
    start_time: time,
    end_time: time,
) -> None:
    """Проверяет корректность временного интервала слота."""
    if start_time >= end_time:
        raise HTTPException(
            status_code=422,
            detail='Время начала слота должно быть меньше времени окончания.',
        )
