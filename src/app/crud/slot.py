from datetime import time
from typing import Self

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.slot import Slot


class CRUDSlot(CRUDBase):
    """CRUD операции для модели Slot."""

    def __init__(self, model: type[Self]) -> None:
        """Инициализатор класса."""
        self.model = model

    async def get_slot_or_404(
        self,
        session: AsyncSession,
        slot_id: int,
        is_active: bool = True,
    ) -> Slot:
        """Получает слот по id или возвращает 404 ошибку."""
        slot = await session.execute(
            select(self.model).where(
                and_(
                    self.model.id == slot_id,
                    self.model.is_active == is_active,
                ),
            ),
        )
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
    ) -> list[Slot]:
        """Получает все слоты для заданного кафе."""
        db_slots = await session.execute(
            select(self.model).where(self.model.cafe_id == cafe_id),
        )
        return db_slots.scalars().all()

    async def create(
        self,
        slot_data: dict,
        session: AsyncSession,
    ) -> Slot:
        """Создает новый слот для бронирования столика."""
        new_slot = self.model(**slot_data)
        session.add(new_slot)
        await session.commit()
        await session.refresh(new_slot)
        return new_slot

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
        statement = select(Slot).where(
            Slot.cafe_id == cafe_id,
            start_time < Slot.end_time,
            end_time > Slot.start_time,
        )
        if slot_id is not None:
            statement = statement.where(Slot.id != slot_id)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self,
        slot_id: int,
        slot_data: dict,
        session: AsyncSession,
    ) -> Slot:
        """Обновляет существующий слот для бронирования столика."""
        slot = await self.get_slot_or_404(session, slot_id)
        for key, value in slot_data.items():
            setattr(slot, key, value)
        session.add(slot)
        await session.commit()
        await session.refresh(slot)
        return slot


slot_crud = CRUDSlot(Slot)
