import random
import uuid

import pytest
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user import AuthService
from app.models.user import User

ph = PasswordHash.recommended()


@pytest.fixture(scope='function')
async def auth_headers(session: AsyncSession) -> dict:
    """Генерирует JWT-токен для тестового пользователя."""
    unique_suffix = str(uuid.uuid4())[:8]
    test_username = f'test_user_{unique_suffix}'
    phone_postfix = ''.join(random.choices('0123456789', k=7))

    result = await session.execute(
        select(User).where(User.username == test_username),
    )
    user = result.scalars().first()

    if not user:
        user = User(
            username=test_username,
            email=f'test_{unique_suffix}@example.com',
            phone=f'+7999{phone_postfix}',
            password_hash=ph.hash('Test123'),
            role='user',
            is_active=True,
        )
        session.add(user)
        await session.flush()

    token = AuthService.create_token(user.id, user.role)
    return {'Authorization': f'Bearer {token}'}
