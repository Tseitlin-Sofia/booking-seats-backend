"""Общие валидаторы для схем."""

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat


def validate_phone_number(v: str | None) -> str | None:
    """Валидация и форматирование номера телефона в E.164."""
    if v is None:
        return v
    try:
        parsed = phonenumbers.parse(v, 'RU')
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError('Invalid phone number')
        return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        raise ValueError('Invalid phone format')
