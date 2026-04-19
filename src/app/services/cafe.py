from typing import Optional
import re

from app.core.constants import CafeConstants


def is_correct_phone(value: str) -> Optional[str]:
    if not re.match(value, CafeConstants.PHONE_FORMAT):
        raise ValueError(CafeConstants.ERROR_PHONE)
    return value
