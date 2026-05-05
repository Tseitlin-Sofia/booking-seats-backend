"""Эндпоинты для управления столами в кафе."""
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import SessionDep
from app.api.validators.cafe import get_cafe_or_404, is_manager_from_cafe
from app.api.validators.table import check_table_exists_in_cafe
from app.core.user import get_current_user, get_manager_user
from app.crud.table import table_crud
from app.models.user import User
from app.schemas.table import (
    TableCreate,
    TableInfo,
    TableUpdate,
)

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
ManagerDep = Annotated[User, Depends(get_manager_user)]


@router.get(
    '/',
    response_model=list[TableInfo],
    summary='Получение списка столов в кафе',
)
async def get_tables(
    cafe_id: int,
    session: SessionDep,
    user: UserDep,
    show_active: bool = None,
) -> list[TableInfo]:
    """Возвращает все столы заданного кафе."""
    await get_cafe_or_404(session, cafe_id, is_exist=True)
    if not (user.is_admin or user.is_manager):
        return await table_crud.get_tables_by_cafe(cafe_id, session, True)
    return await table_crud.get_tables_by_cafe(cafe_id, session, show_active)


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
    user: ManagerDep,
) -> TableInfo:
    """Создаёт новый стол в указанном кафе."""
    if user.is_manager:
        await is_manager_from_cafe(cafe_id, user)
    await get_cafe_or_404(session, cafe_id, is_exist=True)
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
    user: UserDep,
) -> TableInfo:
    """Возвращает информацию о конкретном столе в кафе."""
    await get_cafe_or_404(session, cafe_id, is_exist=True)
    await check_table_exists_in_cafe(
        cafe_id,
        table_id,
        session,
    )
    table = await table_crud.get_with_cafe(table_id, session)
    if not (user.is_admin or user.is_manager) and not table.is_active:
        raise HTTPException(HTTPStatus.FORBIDDEN, detail='Доступ запрещен!')
    return table


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
    user: ManagerDep,
) -> TableInfo:
    """Обновляет данные стола в указанном кафе."""
    if user.is_manager:
        await is_manager_from_cafe(cafe_id, user)
    await get_cafe_or_404(session, cafe_id, is_exist=True)
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
    return await table_crud.get_with_cafe(table_id, session)
