"""Валидаторы для бронирования."""

from typing import Self

from pydantic import model_validator
from sqlalchemy import func

from app.core.constants import BookingConstants as Constants


class BookingValidatorMixin:
    """Валидаторы для бронирования."""

    @model_validator(mode='after')
    def check_future_date(self) -> Self:
        """Проверяет, что дата бронирования находится в будущем."""
        if self.booking_date < func.current_date().execute().scalar():
            raise ValueError(Constants.DATE_ERROR)
        return self

    @model_validator(mode='after')
    def check_list_slotst_is_not_empty(
        self,
    ) -> Self:
        """Проверяет, что список слотов не пуст."""
        if len(self.table_slots) == 0:
            raise ValueError(Constants.LIST_SLOTS_ERROR)
        return self

    @model_validator(mode='after')
    def check_guest_number_is_positive(self) -> Self:
        """Проверяет, количество гостей."""
        if (
            self.guest_number > Constants.MAX_GUESTS
            or self.guest_number < Constants.MIN_GUESTS
        ):
            raise ValueError(Constants.GUEST_NUMBER_ERROR)
        return self
