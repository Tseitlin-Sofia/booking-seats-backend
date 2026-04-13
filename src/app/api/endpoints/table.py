"""Эндпоинты для управления столами в кафе."""

from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.api.validators.table import (
    check_cafe_exists,
    check_table_exists_in_cafe,
)
from app.crud.table import table_crud
from app.schemas.table import (
    TableCreate,
    TableInfo,
    TableUpdate,
)
from app.api.dependencies import SessionDep

router = APIRouter()


@router.get(
    '/',
    response_model=list[TableInfo],
    summary='Получение списка столов в кафе',
)
async def get_tables(
    cafe_id: int,
    session: SessionDep,
    show_active: bool = True,
) -> list[TableInfo]:
    """Возвращает все столы заданного кафе."""
    await check_cafe_exists(cafe_id, session)
    return await table_crud.get_tables_by_cafe(
        cafe_id=cafe_id,
        session=session,
        show_active=show_active,
    )


@router.post(
    '/',
    response_model=TableInfo,
    status_code=201,
    summary='Создание нового стола',
)
async def create_table(
    cafe_id: int,
    table_in: TableCreate,
    session: SessionDep,
) -> TableInfo:
    """Создаёт новый стол в указанном кафе."""
    await check_cafe_exists(cafe_id, session)
    return await table_crud.create_for_cafe(
        cafe_id=cafe_id,
        obj_in=table_in,
        session=session,
    )


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Получение стола по ID',
)
async def get_table(
    cafe_id: int,
    table_id: int,
    session: SessionDep,
) -> TableInfo:
    """Возвращает информацию о конкретном столе в кафе."""
    await check_cafe_exists(cafe_id, session)
    await check_table_exists_in_cafe(
        cafe_id,
        table_id,
        session,
    )
    return await table_crud.get_with_cafe(
        table_id,
        session,
    )


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    summary='Обновление стола',
)
async def update_table(
    cafe_id: int,
    table_id: int,
    table_in: TableUpdate,
    session: SessionDep,
) -> TableInfo:
    """Обновляет данные стола в указанном кафе."""
    await check_cafe_exists(cafe_id, session)
    table = await check_table_exists_in_cafe(
        cafe_id,
        table_id,
        session,
    )
    await table_crud.update(
        db_obj=table,
        obj_in=table_in,
        session=session,
    )
    return await table_crud.get_with_cafe(
        table_id,
        session,
    )
