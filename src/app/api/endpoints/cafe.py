from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import ManagerDep, SessionDep, UserDep
from app.api.validators.cafe import (
    check_name_address,
    get_cafe_or_404,
    is_manager_from_cafe,
    is_managers_id,
)
from app.core.user import get_admin_user
from app.crud.cafe import CRUDCafe, cafe_crud
from app.models import Cafe
from app.schemas.cafe import CafeCreate, CafeInfo, CafeUpdate

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
)
async def get_all_cafes(
    session: SessionDep,
    user: UserDep,
    show_active: Optional[bool] = None,
) -> List[Cafe]:
    """Ручка multi-get."""
    if not (user.is_admin or user.is_manager):
        return await cafe_crud.get_multi(session, True)
    return await cafe_crud.get_multi(session, show_active)


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
)
async def get_cafe(
    session: SessionDep,
    cafe_id: int,
    user: UserDep,
) -> Cafe:
    """Ручка id-get."""
    cafe = await get_cafe_or_404(session, cafe_id)
    if not (user.is_admin or user.is_manager) and not cafe.is_active:
        raise HTTPException(HTTPStatus.FORBIDDEN, detail='Доступ запрещен!')
    return cafe


@router.post(
    '/',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Создание нового кафе',
    description=(
        'Создает новое кафе. '
        'Только для администраторов.'
    ),
    response_description='Подробный вывод созданного кафе',
    dependencies=[Depends(get_admin_user)],
)
async def create_new_cafe(
    new_cafe: CafeCreate,
    session: SessionDep,
) -> CRUDCafe:
    """Ручка post."""
    await check_name_address(session, new_cafe)
    managers = await is_managers_id(session, new_cafe)
    return await cafe_crud.create_new_cafe(session, new_cafe, managers)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    response_model_exclude_none=True,
    summary='Обновление информации о кафе по его ID',
    description=(
        'Обновление информации о кафе по его ID. '
        'Только для администраторов и менеджеров.'
    ),
    response_description='Подробный вывод измененного кафе',
)
async def update_cafe(
    cafe_id: int,
    new_cafe: CafeUpdate,
    user: ManagerDep,
    session: SessionDep,
) -> CRUDCafe:
    """Ручка patch."""
    await is_manager_from_cafe(cafe_id, user)
    db_cafe = await get_cafe_or_404(session, cafe_id)
    await check_name_address(session, new_cafe, db_cafe)
    managers = await is_managers_id(session, new_cafe, cafe_id)
    return await cafe_crud.update_db_cafe(
        session, db_cafe, new_cafe,  managers,
    )
