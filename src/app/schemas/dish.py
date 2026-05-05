import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import DishConstants


class DishShortInfo(BaseModel):
    """Краткая информация о блюде для вложенных ответов."""

    id: int = Field(..., title='Id')
    name: str = Field(..., title='Name')
    price: float = Field(..., title='Price')
    description: str | None = Field(None, title='Description')
    is_available: bool = Field(..., title='Is Available')

    model_config = ConfigDict(from_attributes=True)


class DishCreate(BaseModel):
    """Схема создания блюда."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=DishConstants.MAX_NAME_LENGTH,
    )
    description: Optional[str] = Field(
        None,
        max_length=DishConstants.MAX_DESCRIPTION_LENGTH,
    )
    price: float = Field(..., gt=0)
    is_available: bool = True

    model_config = ConfigDict(extra='forbid')


class DishUpdate(BaseModel):
    """Схема обновления блюда (все поля опциональны)."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=DishConstants.MAX_NAME_LENGTH,
    )
    description: Optional[str] = Field(
        None,
        max_length=DishConstants.MAX_DESCRIPTION_LENGTH,
    )
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def prevent_null_required_fields(self) -> Self:
        """Запрещает явную передачу null для обязательных полей."""
        not_nullable = {'name', 'price', 'is_available', 'is_active'}
        for field_name in not_nullable:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                msg = f'Поле {field_name} не может быть null'
                raise ValueError(msg)
        return self


class DishInfo(BaseModel):
    """Полная информация о блюде."""

    id: int
    cafe_id: int
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PreOrderItemCreate(BaseModel):
    """Схема передачи данных о позиции предзаказа при создании бронирования."""

    dish_id: int
    quantity: int = Field(
        ge=1,
        le=100,
        description='Количество порций (от 1 до 100)',
    )


class PreOrderItemInfo(BaseModel):
    """Схема возврата информации о позиции предзаказа в ответе API."""

    dish: DishShortInfo
    quantity: int = Field(..., ge=1, description='Количество порций')
    price_at_order: float = Field(..., description='Цена на момент заказа')

    model_config = ConfigDict(from_attributes=True)
