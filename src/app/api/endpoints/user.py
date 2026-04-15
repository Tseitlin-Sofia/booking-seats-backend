from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserInfo, UserUpdate

router = APIRouter()

SessionDep = Annotated[
    AsyncSession,
    Depends(get_async_session),
]
# UserDep = Annotated[User, Depends(current_user)]


@router.get(
    '/',
    response_model=list[UserInfo],
    description=(
        'Возвращает информацию о всех пользователях.'
        'Только для администраторов или менеджеров'
    ),
)
async def get_users(
    session: SessionDep,
    # TODO добавить пермишены
) -> list[UserInfo]:
    """Возвращает список всех пользователей."""
    return await user_crud.get_multi(session=session)


@router.post(
    '/',
    response_model=UserInfo,
    description=(
        'Создает нового пользователя с указанными данными.'
        'Регистрировать пользователя может или не авторизированный '
        'пользователь или менеджер или администратор.'
    ),
)
async def create_user(
    session: SessionDep,
    user_in: UserCreate,
) -> UserInfo:
    """Создает нового пользователя."""
    try:
        user = await user_crud.create(session=session, user_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return user


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    description=(
        'Возвращает информацию о пользователе по его ID. '
        'Только для администраторов или менеджеров'
    ),
)
async def get_user(
    user_id: int,
    session: SessionDep,
    # TODO добавить пермишены
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
    description=(
        'Возвращает обновленную информацию о пользователе по его ID. '
        'Только для администраторов или менеджеров'
    ),
)
async def update_user(
    # user_id: int,
    user_in: UserUpdate,
    session: SessionDep,
    # TODO добавить пермишены
) -> UserInfo:
    """Изменяет данные конкретного ползователя."""
    return await user_crud.update(user_in=user_in, session=session)


# @router.get(
#     '/me',
#     response_model=UserInfo,
#     description=(
#         'Возвращает информацию о текущем пользователе.'
#         ' Только для авторизированных пользователей'
#     ),
# )
# async def get_me_info(
#     user: UserDep,
# ) -> UserInfo:
#     """Возвращает данные текущего авторизованного пользователя."""
#     return UserInfo.model_validate(user)
