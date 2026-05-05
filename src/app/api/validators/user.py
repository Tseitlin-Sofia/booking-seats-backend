from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.models.user import User, UserRole


def validate_admin_or_manager_cannot_deactivate_self(
    current_user: User, target_user: User, is_active: bool | None,
) -> None:
    """Админ и менеджер не может деактивировать сам себя."""
    if (
        is_active is not None and current_user.id == target_user.id
    ):
        raise PermissionDeniedError(
            'Нельзя деактивировать свою учетную запись.',
        )


def validate_manager_can_only_edit_users(
    current_user: User, target_user: User,
) -> None:
    """Менеджер может изменять только обычных пользователей."""
    if current_user.is_admin:
        return

    if current_user.id == target_user.id:
        return

    if target_user.is_admin or target_user.is_manager:
        raise PermissionDeniedError(
            'Менеджер может изменять только обычных пользователей',
        )


async def validate_cannot_deactivate_last_manager(
    session: AsyncSession, user: User, is_active: bool | None,
) -> None:
    """Нельзя деактивировать последнего активного менеджера кафе."""
    if is_active is False and user.is_manager and user.cafe_id is not None:
        result = await session.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.cafe_id == user.cafe_id,
                User.role == UserRole.MANAGER,
                User.is_active,
                User.id != user.id,
            ),
        )
        count = result.scalar()
        if count == 0:
            raise ValueError(
                'Нельзя деактивировать последнего активного менеджера кафе',
            )


def validate_manager_cannot_elevate_role(
    current_user: User,
    target_user: User,
    new_role: UserRole | None,
) -> None:
    """Менеджер не может повысить роль пользователя до админа или менеджера."""
    if new_role is None:
        return

    if not current_user.is_admin:
        if new_role in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedError(
                'Менеджер не может изменять роли',
            )

        if target_user.role in (UserRole.ADMIN, UserRole.MANAGER):
            raise PermissionDeniedError(
                'Менеджер не может изменять роль '
                'администратора или другого менеджера.',
            )


def validate_admin_cannot_change_own_role(
    current_user: User,
    target_user: User,
    new_role: UserRole | None,
) -> None:
    """Админ не может изменить свою роль."""
    if (
        new_role is not None
        and current_user.is_admin
        and current_user.id == target_user.id
    ):
        raise PermissionDeniedError(
            'Администратор не может изменить свою роль',
        )
