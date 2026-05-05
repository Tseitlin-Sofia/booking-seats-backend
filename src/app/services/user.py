import re

from pwdlib import PasswordHash
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserDuplicateError, UserValidationError
from app.crud.user import user_crud
from app.models import User
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserUpdate

ph = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Хеширует пароль для последующего хранения в БД."""
    return ph.hash(password)


class UserService:
    """Сервис работы с пользователями."""

    async def is_first_user(self, session: AsyncSession) -> bool:
        """Проверяет, есть ли уже пользователи в системе."""
        result = await session.execute(
            select(func.count()).select_from(User),
        )
        count = result.scalar()
        return count == 0

    def normalize_phone(self, phone: str | None) -> str | None:
        """Приводит телефон к единому формату: +7XXXXXXXXXX."""
        if not phone:
            return None
        cleaned = re.sub(r'[^\d+]', '', phone)
        if cleaned.startswith('8') and len(cleaned) == 11:
            cleaned = '+7' + cleaned[1:]
        return cleaned

    def raise_duplicate_error(
        self,
        email: str | None,
        phone: str | None,
        username: str | None,
        tg_id: str | None,
        conflicting_user: User,
    ) -> None:
        """Выбрасывает исключение с указанием конфликтующего поля."""
        if email and conflicting_user.email == email:
            raise UserDuplicateError(
                'Пользователь с такими учетными данными уже существует.',
            )
        if phone and conflicting_user.phone == phone:
            raise UserDuplicateError(
                'Пользователь с такими учетными данными уже существует.',
            )
        if username and conflicting_user.username == username:
            raise UserDuplicateError(
                'Пользователь с такими учетными данными уже существует.',
            )
        if tg_id and conflicting_user.tg_id == tg_id:
            raise UserDuplicateError(
                'Пользователь с такими учетными данными уже существует.',
            )

    async def check_unique_fields(
        self,
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        username: str | None = None,
        tg_id: str | None = None,
    ) -> None:
        """Проверяет поля email, phone и username на уникальность."""
        conditions = []
        normalized_phone = self.normalize_phone(phone) if phone else None

        if email:
            conditions.append(User.email == email)
        if normalized_phone:
            conditions.append(User.phone == normalized_phone)
        if username:
            conditions.append(User.username == username)
        if tg_id:
            conditions.append(User.tg_id == tg_id)

        if not conditions:
            return

        stmt = select(User).where(
            User.is_active,
            or_(*conditions),
        )

        result = await session.execute(stmt)
        conflicting_user = result.scalars().first()

        if conflicting_user:
            self.raise_duplicate_error(
                email, normalized_phone, username, tg_id, conflicting_user,
            )

    @staticmethod
    def check_email_or_phone_required(
        email: str | None,
        phone: str | None,
    ) -> None:
        """Метод для проверки наличия хотя бы одного из полей email, phone."""
        if not email and not phone:
            raise UserValidationError(
                'Хотя бы одно из полей email '
                'или телефон должно быть заполено',
            )

    async def create_user(
        self,
        session: AsyncSession,
        user_in: UserCreate,
    ) -> User:
        """Создаёт нового пользователя и проводит необходимые проверки."""
        self.check_email_or_phone_required(user_in.email, user_in.phone)
        await self.check_unique_fields(
            session=session,
            email=user_in.email,
            phone=user_in.phone,
            username=user_in.username,
            tg_id=user_in.tg_id,
        )

        user_data = user_in.model_dump(exclude={'password'})
        user_data['password_hash'] = get_password_hash(user_in.password)
        if user_in.phone:
            user_data['phone'] = self.normalize_phone(user_in.phone)

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
                phone=user_in.phone if user_in.phone != user.phone else None,
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

        if user_in.phone:
            user_update_data['phone'] = self.normalize_phone(user_in.phone)

        updated_email = user_update_data.get('email', user.email)
        updated_phone = user_update_data.get('phone', user.phone)
        self.check_email_or_phone_required(updated_email, updated_phone)

        return await user_crud.update(
            session=session,
            db_user=user,
            user_update_data=user_update_data,
        )


user_service = UserService()
