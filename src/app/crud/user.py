from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models.user import User

logger = get_logger()


class CRUDUser(CRUDBase):
    """Круд для работы с пользователями."""

    async def create(
        self,
        session: AsyncSession,
        user_data: dict,
    ) -> User:
        """Создаёт пользователя предварительно хешируя пароль."""
        user = self.model(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(
            f'Создан пользователь! user_id={user.id},'
            + f'username={user.username}, role={user.role}',
        )
        return user

    async def update(
        self,
        session: AsyncSession,
        db_user: User,
        user_update_data: dict,
    ) -> User:
        """Обновление данных пользователя."""
        for field in user_update_data:
            if hasattr(db_user, field):
                setattr(db_user, field, user_update_data[field])

        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        logger.info(
            f'Обновлён пользователь! user_id={db_user.id},'
            + f' username={db_user.username},'
            + f' updated_fields={list(user_update_data.keys())}',
        )
        return db_user


user_crud = CRUDUser(User)
