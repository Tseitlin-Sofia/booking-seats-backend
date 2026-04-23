"""Валидаторы для аутентификации."""


def validate_login_not_empty(v: str) -> str:
    """Проверяет, что логин не пустой."""
    if not v or not v.strip():
        raise ValueError('Login is required')
    return v.strip()
