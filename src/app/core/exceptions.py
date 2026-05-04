"""Кастомные исключения."""


class UserValidationError(ValueError):
    """Ошибка валидации данных пользователя (422)."""

    pass


class UserDuplicateError(ValueError):
    """Ошибка дублирования данных пользователя (400)."""

    pass


class PermissionDeniedError(ValueError):
    """Ошибка прав доступа (403)."""

    pass
