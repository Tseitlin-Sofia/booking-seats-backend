from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase
from app.services.user import get_password_hash

class CRUDUser(CRUDBase):
    """Круд для работы с пользователями."""

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        """Получить пользователя по email."""
        db_user = await session.execute(select(User).where(User.email == email))
        return db_user.scalars().first()
    
    async def get_by_phone(
        self,
        session: AsyncSession,
        phone: str,
    ) -> User | None:
        """Получить пользователя по phone."""
        db_user = await session.execute(select(User).where(User.phone == phone))
        return db_user.scalars().first()
    
    async def get_by_username(
        self,
        session: AsyncSession,
        username: str,
    ) -> User | None:
        """Получить пользователя по username."""
        db_user = await session.execute(
            select(User).where(User.username == username)
        )
        return db_user.scalars().first()

    async def check_unique_fields(
        self,
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        username: str | None = None
    ) -> None:
        """Проверяет поля email, phone и username на уникальность."""
        if email:
            if await self.get_by_email(session, email):
                raise ValueError('Пользователь с таким email уже существует.')
        if phone:
            if await self.get_by_phone(session, phone):
                raise ValueError('Пользователь с таким phone уже существует')
        if username:
            if await self.get_by_username(session, username):
                raise ValueError(
                    'Пользоваетль с таким username уже существует.'
                )

    @staticmethod        
    def check_email_or_phone_required(
        user_in: UserCreate
    ) -> None:
        """Метод для проверки наличия хотя бы одного из полей email, phone."""
        if not user_in.email and not user_in.phone:
            # TODO лог о некоректном предоставлении полей
            raise ValueError(
                'Хотя бы одно из полей email или phone должно быть заполено'
            )
        
    async def create(
        self,
        session: AsyncSession,
        user_in: UserCreate
    ):
        """Создаёт пользователя предварительно хешируя пароль."""
        await self.check_unique_fields(
            session,
            email=user_in.email,
            phone=user_in.phone,
            username=user_in.username
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
                username=user_in.username
            )
        
        if user_in.password:
            user_update_data = user_in.model_dump(
                exclude={'password'},
                exclude_unset=True
            )
            user_update_data['password_hash'] = get_password_hash(user_in.password)
        else:
            user_update_data = user_in.model_dump(exclude_unset=True)
        
        for field in user_update_data:
            if hasattr(db_user, field):
                setattr(db_user, field, user_update_data[field])
        
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user

    async def deactivate_or_activate_user(
        self,
        session: AsyncSession,
        user_id: int,
        activate_flag: bool
    ) -> User:
        user = await self.get(
            obj_id=user_id,
            session=session,
        )
        if not user:
            # TODO логи
            raise ValueError('Пользователь с таким id не найден')
        user.is_activate = activate_flag
        await session.commit()
        await session.refresh(user)
        # TODO можно бовить лог о деактивации пользователя
        return user
    

user_crud = CRUDUser(User)
