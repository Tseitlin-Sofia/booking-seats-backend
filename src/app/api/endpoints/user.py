"""Эндпоинты для управления пользователями."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import SessionDep
from app.core.user import (
    get_admin_user,
    get_current_user,
    get_current_user_optional,
    get_manager_user,
)
from app.crud.user import user_crud
from app.models.user import User, UserRole
from app.schemas.users import UserCreate, UserInfo, UserUpdate

router = APIRouter()


@router.get(
    '/',
    response_model=List[UserInfo],
    summary='Получить список пользователей',
    description=(
        'Возвращает список всех пользователей. '
        'Доступно только для администраторов и менеджеров.'
    ),
)
async def get_users(
    session: SessionDep,
    current_user: User = Depends(get_manager_user),
) -> List[UserInfo]:
    """Получить список пользователей."""
    return await user_crud.get_multi(session)


@router.post(
    '/',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Зарегистрировать нового пользователя',
    description=(
        'Регистрация нового пользователя. '
        'Доступно без авторизации или для '
        'менеджеров/администраторов.'
    ),
)
async def create_user(
    user_in: UserCreate,
    session: SessionDep,
    current_user: Optional[User] = Depends(
        get_current_user_optional,
    ),
) -> UserInfo:
    """Создать нового пользователя."""
    is_authenticated = current_user is not None
    is_manager_or_admin = is_authenticated and current_user.role in (
        UserRole.MANAGER,
        UserRole.ADMIN,
    )

    if is_authenticated and not is_manager_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав для создания пользователей',
        )

    role = UserRole.USER
    if is_manager_or_admin and user_in.role is not None:
        role = user_in.role

    if user_in.email:
        existing = await user_crud.get_by_email(
            user_in.email, session,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пользователь с таким email уже существует',
            )
    if user_in.phone:
        existing = await user_crud.get_by_phone(
            user_in.phone, session,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    'Пользователь с таким телефоном'
                    ' уже существует'
                ),
            )
    existing = await user_crud.get_by_username(
        user_in.username, session,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким именем уже существует',
        )

    return await user_crud.create_user(user_in, session, role=role)


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получить информацию о текущем пользователе',
    description=(
        'Доступно только для авторизованных пользователей.'
    ),
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserInfo:
    """Получить информацию о текущем пользователе."""
    return current_user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновить информацию о текущем пользователе',
    description=(
        'Доступно только для авторизованных пользователей.'
    ),
)
async def update_current_user(
    user_in: UserUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> UserInfo:
    """Обновить информацию о текущем пользователе."""
    if user_in.role is not None and user_in.role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нельзя изменить свою роль',
        )
    return await user_crud.update_user(
        current_user, user_in, session,
    )


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получить информацию о пользователе по ID',
    description=(
        'Доступно только для администраторов и менеджеров.'
    ),
)
async def get_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: User = Depends(get_manager_user),
) -> UserInfo:
    """Получить информацию о пользователе по ID."""
    user = await user_crud.get(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )
    return user


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновить информацию о пользователе по ID',
    description=(
        'Доступно только для администраторов и менеджеров.'
    ),
)
async def update_user_by_id(
    user_id: int,
    user_in: UserUpdate,
    session: SessionDep,
    current_user: User = Depends(get_manager_user),
) -> UserInfo:
    """Обновить информацию о пользователе по ID."""
    user = await user_crud.get(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )
    if current_user.role == UserRole.MANAGER:
        if user_in.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    'Менеджер не может назначать'
                    ' роль администратора'
                ),
            )
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    'Менеджер не может изменять'
                    ' администратора'
                ),
            )
    return await user_crud.update_user(user, user_in, session)


@router.delete(
    '/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Деактивировать пользователя по ID',
    description=(
        'Блокировка пользователя.'
        ' Доступно только для администраторов.'
    ),
)
async def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: User = Depends(get_admin_user),
) -> None:
    """Деактивировать (заблокировать) пользователя."""
    user = await user_crud.get(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Нельзя деактивировать самого себя',
        )
    user.is_active = False
    session.add(user)
    await session.commit()
