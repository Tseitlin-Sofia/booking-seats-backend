"""Валидаторы для эндпоинтов столов."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cafe import Cafe
from app.models.table import Table


async def check_cafe_exists(
    cafe_id: int,
    session: AsyncSession,
) -> Cafe:
    """Проверяет, что кафе с данным ID существует."""
    result = await session.execute(
        select(Cafe).where(Cafe.id == cafe_id),
    )
    cafe = result.scalars().first()
    if cafe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Кафе с id={cafe_id} не найдено.',
        )
    return cafe


async def check_table_exists_in_cafe(
    cafe_id: int,
    table_id: int,
    session: AsyncSession,
) -> Table:
    """Проверяет, что стол существует в данном кафе."""
    result = await session.execute(
        select(Table).where(
            Table.id == table_id,
            Table.cafe_id == cafe_id,
        ),
    )
    table = result.scalars().first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f'Стол с id={table_id} в кафе с id={cafe_id} не найден.'),
        )
    return table
