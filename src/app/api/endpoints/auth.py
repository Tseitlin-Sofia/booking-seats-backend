"""Эндпоинты аутентификации."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import auth_service
from app.schemas.auth import AuthData, AuthToken

router = APIRouter()

SessionDep = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.post(
    '/login',
    response_model=AuthToken,
    summary='Получение токена авторизации',
    description=(
        'Возвращает токен для последующей '
        'авторизации пользователя.'
    ),
)
async def login(
    auth_data: AuthData,
    session: SessionDep,
) -> AuthToken:
    """Аутентификация пользователя по email/phone/username и паролю."""
    user = await auth_service.authenticate_user(
        session=session,
        login=auth_data.login,
        password=auth_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Неверные имя пользователя или пароль',
        )

    token = auth_service.create_token(user.id, user.role)
    return AuthToken(access_token=token, token_type='bearer')
