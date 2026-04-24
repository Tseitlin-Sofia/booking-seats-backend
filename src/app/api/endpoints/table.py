"""Эндпоинты для управления столами в кафе."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import SessionDep
from app.api.validators.table import (
    check_cafe_exists,
    check_table_exists_in_cafe,
)
from app.core.user import get_current_user, get_manager_user
from app.crud.table import table_crud
# from app.models.cafe import cafe_managers
from app.models.user import User
from app.schemas.table import (
    TableCreate,
    TableInfo,
    TableUpdate,
)

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
ManagerDep = Annotated[User, Depends(get_manager_user)]


async def check_manager_cafe_access(
    user: User,
    cafe_id: int,
    session: AsyncSession,
) -> None:
    """Менеджер может управлять только столами кафе из связи cafe_managers."""
    if user.is_admin:
        return
    if not user.is_manager:
        return
    # result = await session.execute(
    #     select(cafe_managers.c.cafe_id).where(
    #         cafe_managers.c.user_id == user.id,
    #         cafe_managers.c.cafe_id == cafe_id,
    #     ),
    # )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Менеджер имеет доступ только к своему кафе.',
        )


@router.get(
    '/',
    response_model=list[TableInfo],
    summary='Получение списка столов в кафе',
)
async def get_tables(
    cafe_id: int,
    session: SessionDep,
    user: UserDep,
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
    user: ManagerDep,
) -> TableInfo:
    """Создаёт новый стол в указанном кафе."""
    await check_manager_cafe_access(user, cafe_id, session)
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
    user: UserDep,
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
    user: ManagerDep,
) -> TableInfo:
    """Обновляет данные стола в указанном кафе."""
    await check_manager_cafe_access(user, cafe_id, session)
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
