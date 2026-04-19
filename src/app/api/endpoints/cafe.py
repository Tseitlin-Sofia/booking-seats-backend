from typing import List, Self

from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.api.validators.cafe import is_managers_id
from app.crud.cafe import cafe_crud
from app.schemas.cafe import (
    CafeCreate,
    CafeDB,
    CafeInfo,
    CafeUpdate,
)

router = APIRouter()


@router.get(
    '/',
    response_model=List[CafeInfo],
    response_model_exclude_none=True,
    summary='Получение списка кафе',
    description=(
        'Получение списка кафе. '
        'Для администраторов и менеджеров - все кафе (с возможностью выбора), '
        'для пользователей - только активные.'
    ),
    response_description='Подробный вывод всех кафе',
    # TODO: добавить потом пермишены
)
async def get_all_cafes(session: SessionDep) -> Self:
    """Ручка multi-get."""
    return await cafe_crud.get_by_attribute_multi(
        attr_name='is_active',
        attr_value=True,
        session=session,
    )


@router.post(
    '/',
    response_model=CafeDB,
    response_model_exclude_none=True,
    summary='Создание нового кафе',
    description=(
        'Создает новое кафе. '
        'Только для администраторов и менеджеров.'
    ),
    response_description='Подробный вывод созданного кафе',
    # TODO: добавить потом пермишены
)
async def create_new_cafe(
    new_cafe: CafeCreate,
    session: SessionDep,
) -> Self:
    """Ручка post."""
    managers = None  # await is_managers_id(new_cafe, session)
    return await cafe_crud.create_new_cafe(new_cafe, managers, session)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Получение информации о кафе по его ID',
    description=(
        'Получение информации о кафе по его ID. '
        'Для администраторов и менеджеров - все кафе, '
        'для пользователей - только активные.'
    ),
    response_description='Подробный вывод одного кафе',
    # TODO: добавить потом пермишены
)
async def get_cafe_by_id(cafe_id: int, session: SessionDep) -> Self:
    """Ручка id-get."""
    return await cafe_crud.get(cafe_id, session)


@router.patch(
    '/{cafe_id}',
    response_model=CafeDB,
    response_model_exclude_none=True,
    summary='Обновление информации о кафе по его ID',
    description=(
        'Обновление информации о кафе по его ID. '
        'Только для администраторов и менеджеров.'
    ),
    response_description='Подробный вывод измененного кафе',
    # TODO: добавить потом пермишены
)
async def update_charity_project(
    cafe_id: int,
    cafe_changed: CafeUpdate,
    session: SessionDep,
) -> Self:
    """Ручка patch."""
    db_cafe = await cafe_crud.get(cafe_id, session)
    managers = None
    if 'managers_id' in cafe_changed.model_dump(exclude_unset=True):
        managers = await is_managers_id(cafe_changed, session)
    return await cafe_crud.update_db_cafe(
        db_cafe,
        cafe_changed,
        managers,
        session,
    )
