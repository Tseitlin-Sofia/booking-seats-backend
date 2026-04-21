from pwdlib import PasswordHash

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserUpdate
from app.crud.user import user_crud
from app.models import User
from app.models.user import UserRole

ph = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Хеширует пароль для последующего хранения в БД."""
    return ph.hash(password)


class UserService:
    """Сервис работы с пользователями."""

    async def is_first_user(self, session: AsyncSession) -> bool:
        """Проверяет, есть ли уже пользователи в системе."""
        result = await session.execute(
            select(func.count()).select_from(User)
        )
        count = result.scalar()
        return count == 0

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
            if await user_crud.get_by_attribute(
                attr_name='email', attr_value=email, session=session,
            ):
                raise ValueError('Пользователь с таким email уже существует.')
        if phone:
            if await user_crud.get_by_attribute(
                attr_name='phone', attr_value=phone, session=session,
            ):
                raise ValueError('Пользователь с таким phone уже существует')
        if username:
            if await user_crud.get_by_attribute(
                attr_name='username', attr_value=username, session=session,
            ):
                raise ValueError(
                    'Пользоваетль с таким username уже существует.',
                )
        if tg_id:
            if await user_crud.get_by_attribute(
                attr_name='tg_id', attr_value=tg_id, session=session,
            ):
                raise ValueError(
                    'Пользоваетль с таким tg_id уже существует.',
                )

    @staticmethod
    def check_email_or_phone_required(
        email: str | None,
        phone: str | None,
    ) -> None:
        """Метод для проверки наличия хотя бы одного из полей email, phone."""
        if not email and not phone:
            # TODO лог о некоректном предоставлении полей
            raise ValueError(
                'Хотя бы одно из полей email или phone должно быть заполено',
            )

    async def create_user(
        self,
        session: AsyncSession,
        user_in: UserCreate
    ) -> User:
        """Создаёт нового пользователя и проводит необходимые проверки."""
        await self.check_unique_fields(
            session=session,
            email=user_in.email,
            phone=user_in.phone,
            username=user_in.username,
            tg_id=user_in.tg_id,
        )
        self.check_email_or_phone_required(user_in.email, user_in.phone)

        user_data = user_in.model_dump(exclude={'password'})
        user_data['password_hash'] = get_password_hash(user_in.password)

        if await self.is_first_user(session=session):
            user_data['role'] = UserRole.ADMIN

        return await user_crud.create(session=session, user_data=user_data)
    
    async def update_user(
        self,
        session: AsyncSession,
        user: User,
        user_in: UserUpdate,
    ) -> User:
        """Обновляет пользователя и проводит необходимые проверки."""
        if user_in.email or user_in.phone or user_in.username or user_in.tg_id:
            await self.check_unique_fields(
                session=session,
                email=user_in.email if user_in.email != user.email else None,
                phone=user_in.phone if user_in.phone != user_in.phone else None,
                username=(
                    user_in.username
                    if user_in.username != user.username else None
                ),
                tg_id=user_in.tg_id if user_in.tg_id != user.tg_id else None,
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

        return await user_crud.update(
            session=session,
            db_user=user,
            user_update_data=user_update_data,
        )

user_service = UserService()
