from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    ManagerDep,
    OptionalUserDep,
    SessionDep,
    UserDep,
)
from app.api.validators.user import (
    validate_admin_or_manager_cannot_deactivate_self,
    validate_cannot_deactivate_last_manager,
    validate_manager_can_only_edit_users,
)
from app.core.user import get_current_user, get_manager_user
from app.crud.user import user_crud
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserInfo, UserUpdate
from app.services.user import user_service

router = APIRouter()


@router.get(
    '/',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
    description=(
        'Возвращает информацию о всех пользователях.'
        'Только для администраторов или менеджеров'
    ),
    dependencies=(Depends(get_manager_user),),
)
async def get_users(
    session: SessionDep,
) -> list[UserInfo]:
    """Возвращает список всех пользователей."""
    return await user_crud.get_multi(session=session)


@router.post(
    '/',
    response_model=UserInfo,
    summary='Регистрация нового пользователя',
    description=(
        'Создает нового пользователя с указанными данными.'
        'Регистрировать пользователя может или не авторизированный '
        'пользователь или менеджер или администратор.'
    ),
)
async def create_user(
    session: SessionDep,
    user_in: UserCreate,
    current_user: OptionalUserDep,
) -> UserInfo:
    """Создает нового пользователя."""
    if current_user and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                'Авторизированный пользователь не'
                'может создать нового пользователя'
            ),
        )
    try:
        user = await user_service.create_user(session=session, user_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return user


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получение информации о текущем пользователе',
    description=(
        'Возвращает информацию о текущем пользователе.'
        ' Только для авторизированных пользователей'
    ),
    dependencies=(Depends(get_current_user),),
)
async def get_me_info(
    user: UserDep,
) -> UserInfo:
    """Возвращает данные текущего авторизованного пользователя."""
    return UserInfo.model_validate(user)


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновление информации о текущем пользователе',
    description=(
        'Возвращает обновленную информацию о пользователе. '
        'Только для авторизированных пользователей'
    ),
)
async def patch_me(
    user_in: UserUpdate,
    session: SessionDep,
    current_user: UserDep,
) -> UserInfo:
    """Возвращает обновленные даные текущего пользователя."""
    if user_in.role is not None or user_in.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не можете поменять поля role и is_active самому себе.',
        )
    try:
        return await user_service.update_user(
            session=session, user=current_user, user_in=user_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получение информации о пользователе по его ID',
    description=(
        'Возвращает информацию о пользователе по его ID. '
        'Только для администраторов или менеджеров'
    ),
    dependencies=(Depends(get_manager_user),),
)
async def get_user(
    user_id: int,
    session: SessionDep,
) -> UserInfo:
    """Возвращает сведения о конкретном пользователе."""
    user = await user_crud.get(obj_id=user_id, session=session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь с таким id не найден.',
        )
    return user


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновление информации о пользователе по его ID',
    description=(
        'Возвращает обновленную информацию о пользователе по его ID. '
        'Только для администраторов или менеджеров'
    ),
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: SessionDep,
    current_user: ManagerDep,
) -> UserInfo:
    """Изменяет данные конкретного ползователя."""
    target_user = await user_crud.get(
        obj_id=user_id, session=session, is_active=None,
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь с таким id не найден',
        )

    try:
        validate_admin_or_manager_cannot_deactivate_self(
            current_user=current_user,
            target_user=target_user,
            is_active=user_in.is_active,
        )
        validate_manager_can_only_edit_users(
            current_user=current_user,
            target_user=target_user,
        )
        await validate_cannot_deactivate_last_manager(
            session=session,
            user=target_user,
            is_active=user_in.is_active,
        )
        return await user_service.update_user(
            session=session, user=target_user, user_in=user_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
