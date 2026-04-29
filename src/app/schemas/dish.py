from pydantic import BaseModel, ConfigDict, Field


class DishShortInfo(BaseModel):
    """Краткая информация о блюде для вложенных ответов."""

    id: int = Field(..., title='Id')
    name: str = Field(..., title='Name')
    price: float = Field(..., title='Price')
    description: str | None = Field(None, title='Description')
    is_available: bool = Field(..., title='Is Available')

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
