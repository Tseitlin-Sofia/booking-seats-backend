from datetime import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.slot import Slot


class CRUDSlot(CRUDBase):
    """CRUD операции для модели Slot."""

    async def get_slot_or_404(
        self,
        session: AsyncSession,
        slot_id: int,
        is_active: bool = True,
    ) -> Slot:
        """Получает слот по id или возвращает 404 ошибку."""
        stmt = select(self.model).where(self.model.id == slot_id)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)
        slot = await session.execute(stmt)
        slot = slot.scalars().first()
        if not slot:
            raise HTTPException(
                status_code=404,
                detail='Слот для бронирования столика не найден.',
            )
        return slot

    async def get_slots_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        is_active: bool | None = True,
    ) -> list[Slot]:
        """Получает все слоты для заданного кафе."""
        stmt = select(self.model).where(self.model.cafe_id == cafe_id)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)
        db_slots = await session.execute(stmt)
        return db_slots.scalars().all()

    async def get_slots_at_the_same_time(
            self,
            *,
            slot_id: int | None = None,
            start_time: time,
            end_time: time,
            cafe_id: int,
            session: AsyncSession,
    ) -> list[Slot]:
        """Возвращает слоты в этом кафе, пересекающиеся с заданным интервалом.

        Занятость конкретного стола в слоте (на конкретную дату)
        проверяется отдельно через BookingTableSlotCRUD.is_available.
        """
        stmt = select(self.model).where(
            self.model.cafe_id == cafe_id,
            start_time < self.model.end_time,
            end_time > self.model.start_time,
            self.model.is_active,
        )
        if slot_id is not None:
            stmt = stmt.where(self.model.id != slot_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())


slot_crud = CRUDSlot(Slot)
