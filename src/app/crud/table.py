"""CRUD операции для столов."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models.table import Table
from app.schemas.table import TableCreate

logger = get_logger()


class CRUDTable(CRUDBase):
    """CRUD операции для модели Table."""

    async def get_with_cafe(
        self,
        table_id: int,
        session: AsyncSession,
    ) -> Optional[Table]:
        """Получает стол по ID с подгрузкой связанного кафе."""
        result = await session.execute(
            select(Table)
            .where(Table.id == table_id)
            .options(selectinload(Table.cafe)),
        )
        return result.scalars().first()

    async def get_tables_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        show_active: bool = True,
    ) -> list[Table]:
        """Получает все столы заданного кафе."""
        stmt = (
            select(Table)
            .where(Table.cafe_id == cafe_id)
            .options(selectinload(Table.cafe))
        )
        if show_active is not None:
            stmt = stmt.where(
                Table.is_active == show_active,  # noqa: E712
            )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_for_cafe(
        self,
        cafe_id: int,
        obj_in: TableCreate,
        session: AsyncSession,
    ) -> Table:
        """Создаёт стол, привязанный к кафе."""
        obj_data = obj_in.model_dump()
        obj_data['cafe_id'] = cafe_id
        db_obj = self.model(**obj_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.info(
            'Стол успешно создан!'
            + f'table_id: {db_obj.id}| cafe_id: {cafe_id}'
            + f' Номер стола:{getattr(db_obj, "number", None)}',
        )
        return await self.get_with_cafe(db_obj.id, session)

    async def get_table_in_cafe(
        self,
        cafe_id: int,
        table_id: int,
        session: AsyncSession,
    ) -> Optional[Table]:
        """Получает стол по ID внутри конкретного кафе."""
        result = await session.execute(
            select(Table)
            .where(
                Table.id == table_id,
                Table.cafe_id == cafe_id,
            )
            .options(selectinload(Table.cafe)),
        )
        return result.scalars().first()


table_crud = CRUDTable(Table)
