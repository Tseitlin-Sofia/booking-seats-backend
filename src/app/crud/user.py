from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import get_password_hash


class CRUDUser(CRUDBase):
    """Круд для работы с пользователями."""

    async def check_unique_fields(
        self,
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        username: str | None = None,
        tg_id: str | None = None,
    ) -> None:
        """Проверяет поля email, phone и username на уникальность."""
        if email:
            if await self.get_by_attribute(
                attr_name='email', attr_value=email, session=session,
            ):
                raise ValueError('Пользователь с таким email уже существует.')
        if phone:
            if await self.get_by_attribute(
                attr_name='phone', attr_value=phone, session=session,
            ):
                raise ValueError('Пользователь с таким phone уже существует')
        if username:
            if await self.get_by_attribute(
                attr_name='username', attr_value=username, session=session,
            ):
                raise ValueError(
                    'Пользоваетль с таким username уже существует.',
                )
        if tg_id:
            if await self.get_by_attribute(
                attr_name='tg_id', attr_value=tg_id, session=session,
            ):
                raise ValueError(
                    'Пользоваетль с таким tg_id уже существует.',
                )

    @staticmethod
    def check_email_or_phone_required(
        user_in: UserCreate,
    ) -> None:
        """Метод для проверки наличия хотя бы одного из полей email, phone."""
        if not user_in.email and not user_in.phone:
            # TODO лог о некоректном предоставлении полей
            raise ValueError(
                'Хотя бы одно из полей email или phone должно быть заполено',
            )

    async def create(
        self,
        session: AsyncSession,
        user_in: UserCreate,
    ) -> User:
        """Создаёт пользователя предварительно хешируя пароль."""
        await self.check_unique_fields(
            session,
            email=user_in.email,
            phone=user_in.phone,
            username=user_in.username,
            tg_id=user_in.tg_id,
        )
        self.check_email_or_phone_required(user_in)

        user_data = user_in.model_dump(exclude={'password'})
        user_data['password_hash'] = get_password_hash(user_in.password)

        user = self.model(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # TODO лог о создании пользователя
        return user

    async def update(
        self,
        session: AsyncSession,
        db_user: User,
        user_in: UserUpdate,
    ) -> User:
        """Обновление данных пользователя."""
        if user_in.email or user_in.phone or user_in.username:
            await self.check_unique_fields(
                session,
                email=user_in.email,
                phone=user_in.phone,
                username=user_in.username,
                tg_id=user_in.tg_id,
            )

        if user_in.password:
            user_update_data = user_in.model_dump(
                exclude={'password'},
                exclude_unset=True,
            )
            user_update_data['password_hash'] = get_password_hash(
                user_in.password,
            )
        else:
            user_update_data = user_in.model_dump(exclude_unset=True)

        for field in user_update_data:
            if hasattr(db_user, field):
                setattr(db_user, field, user_update_data[field])

        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user


user_crud = CRUDUser(User)
