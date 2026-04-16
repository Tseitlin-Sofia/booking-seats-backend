"""Модуль аутентификации приложения.

Один JWT-токен (PyJWT), без refresh.
В токене: sub, role, last_used, exp.
Проверка: токен валиден, если с момента последнего запроса
прошло не более TOKEN_INACTIVITY_MINUTES.
Обновление токена через заголовок X-New-Token.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl='/auth/login', auto_error=False,
)


class AuthService:
    """Сервис аутентификации и работы с JWT-токенами."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса аутентификации."""
        self.session = session

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Проверяет соответствие пароля хэшу."""
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def hash_password(password: str) -> str:
        """Хэширует пароль."""
        return pwd_context.hash(password)

    @staticmethod
    def create_token(user_id: int, role: str) -> str:
        """Создаёт JWT-токен с payload: sub, role, iat, exp."""
        now = datetime.now(timezone.utc)
        inactivity = settings.jwt_token_inactivity_minutes
        payload = {
            'sub': str(user_id),
            'role': role,
            'iat': now,
            'exp': now + timedelta(minutes=inactivity),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> dict:
        """Декодирует и валидирует JWT-токен."""
        try:
            return jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401, detail='Token expired',
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=401, detail='Invalid token',
            )

    async def authenticate_user(
        self,
        login: str,
        password: str,
    ) -> Optional[User]:
        """Аутентифицирует пользователя по логину и паролю."""
        if '@' in login:
            query = select(User).where(User.email == login)
        elif login.startswith('+'):
            query = select(User).where(User.phone == login)
        else:
            query = select(User).where(User.username == login)

        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user


async def get_current_user(
    response: Response,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Возвращает текущего авторизованного пользователя."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    auth = AuthService(session)
    payload = auth.decode_token(token)

    user_id = payload.get('sub')
    if not user_id:
        raise credentials_exc

    result = await session.execute(
        select(User).where(User.id == int(user_id)),
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exc

    new_token = auth.create_token(user.id, user.role)
    response.headers['X-New-Token'] = new_token

    return user


async def get_current_user_optional(
    response: Response,
    token: Optional[str] = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """Возвращает пользователя или None, если токен не передан."""
    if not token:
        return None

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    auth = AuthService(session)
    payload = auth.decode_token(token)

    user_id = payload.get('sub')
    if not user_id:
        raise credentials_exc

    result = await session.execute(
        select(User).where(User.id == int(user_id)),
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exc

    new_token = auth.create_token(user.id, user.role)
    response.headers['X-New-Token'] = new_token

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяет, что пользователь — администратор."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав (требуется роль администратора)',
        )
    return current_user


async def get_manager_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяет, что пользователь — менеджер или администратор."""
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                'Недостаточно прав'
                ' (требуется роль менеджера или администратора)'
            ),
        )
    return current_user
