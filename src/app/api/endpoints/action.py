from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ManagerDep, SessionDep, UserDep
from app.api.validators.action import (
    can_manager_change_action,
    get_action_or_404,
    is_action_already_exists,
    is_cafes_exists
)
from app.crud.action import action_crud, CRUDAction
from app.models import Action
from app.schemas.action import ActionCreate, ActionInfo, ActionUpdate

router = APIRouter()


@router.get(
    '/',
    response_model=List[ActionInfo],
    response_model_exclude_none=True,
    summary='Получение списка акций',
    description=(
        'Получение списка акций. '
        'Для администраторов и менеджеров - все акции (с возможностью выбора) '
        ', для пользователей - только активные.'
    ),
    response_description='Подробный вывод всех акций',
)
async def get_all_actions(
    session: SessionDep,
    user: UserDep,
    show_active: Optional[bool] = None,
) -> List[Action]:
    """Ручка multi-get."""
    if not (user.is_admin or user.is_manager):
        return await action_crud.get_multi(session, True)
    return await action_crud.get_multi(session, show_active)


@router.get(
    '/{action_id}',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Получение информации об акции по ее ID',
    description=(
        'Получение информации об акции по ее ID. '
        'Для администраторов и менеджеров - все акции, '
        'для пользователей - только активные.'
    ),
    response_description='Подробный вывод одной акции',
)
async def get_action(
    session: SessionDep,
    action_id: int,
    user: UserDep,
) -> Action:
    """Ручка id-get."""
    action = await get_action_or_404(session, action_id)
    if not (user.is_admin or user.is_manager) and not action.is_active:
        raise HTTPException(HTTPStatus.FORBIDDEN, detail='Доступ запрещен!')
    return action


@router.post(
    '/',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Создание новой акции',
    description=(
        'Создает новую акцию. '
        'Только для администраторов и менеджеров.'
    ),
    response_description='Подробный вывод созданной акции',
)
async def create_new_action(
    session: SessionDep,
    new_action: ActionCreate,
    user: ManagerDep,
) -> CRUDAction:
    """Ручка post."""
    if user.is_manager:
        await can_manager_change_action(new_action, user)
    await is_action_already_exists(session, new_action)
    cafes = await is_cafes_exists(session, new_action)
    return await action_crud.create_new_action(session, new_action, cafes,)


@router.patch(
    '/{cafe_id}',
    response_model=ActionInfo,
    response_model_exclude_none=True,
    summary='Обновление информации об акции по ее ID',
    description=(
        'Обновление информации об акции по ее ID. '
        'Только для администраторов и менеджеров.'
    ),
    response_description='Подробный вывод измененной акции',
)
async def update_cafe(
    action_id: int,
    new_action: ActionUpdate,
    user: ManagerDep,
    session: SessionDep,
) -> CRUDAction:
    """Ручка patch."""
    if user.is_manager:
        await can_manager_change_action(new_action, user)
    await is_action_already_exists(session, new_action)
    db_action = await get_action_or_404(session, action_id)
    cafes = await is_cafes_exists(session, new_action)
    return await action_crud.update_db_action(
        session, db_action, new_action,  cafes,
    )
