from datetime import datetime
from typing import Self

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.slot import Slot


class CRUDSlot(CRUDBase):
    """CRUD операции для модели Slot."""

    def __init__(self, model: type[Self]) -> None:
        """Инициализатор класса."""
        self.model = model

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
        slot_data: datetime,
        session: AsyncSession,
    ) -> Slot:
        """Создает новый слот для бронирования столика."""
        new_slot = self.model(**slot_data.model_dump())
        session.add(new_slot)
        await session.commit()
        await session.refresh(new_slot)
        return new_slot

    async def get_slots_at_the_same_time(
        self,
        *,
        from_reserve: datetime,
        to_reserve: datetime,
        table_id: int,
        session: AsyncSession,
    ) -> list[Slot]:
        """Возвращает слоты, пересекающиеся с заданным интервалом."""
        statement = select(Slot).where(
            Slot.table_id == table_id,
            and_(
                from_reserve <= Slot.to_reserve,
                to_reserve >= Slot.from_reserve,
            ),
        )
        reservations = await session.execute(statement)
        return reservations.scalars().all()


slot_crud = CRUDSlot(Slot)
